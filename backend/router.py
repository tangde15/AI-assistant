"""
RAG 路由器：根据知识库相似度分数决定使用知识库还是网络搜索
核心思想：代码控制决策，LLM 只负责回答
"""
import sys
import os
# 将项目根目录添加到 Python 搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from knowledgebase import search_knowledge
from tools import _search_internet_impl
import json


def route_search(query: str, score_threshold_low: float = 0.45, score_threshold_high: float = 0.60, score_threshold_deep: float = 0.55):
    """
    智能搜索路由器：根据知识库相似度分数决定搜索策略
    
    流程：
    1. 第一轮知识库检索（top 3）
    2. 判断最高分数：
       - < 0.45: 直接网络搜索（弱相关）
       - 0.45 ~ 0.60: 第二轮深度检索（中度相关）
       - >= 0.60: 直接使用知识库结果（强相关）
    3. 第二轮判断阈值：>= 0.55 即可使用知识库（因 top_k 扩大后分数略低）
    
    Args:
        query: 用户问题
        score_threshold_low: 低分阈值，低于此分数直接联网（默认 0.45）
        score_threshold_high: 高分阈值，高于此分数直接用知识库（默认 0.60）
        score_threshold_deep: 第二轮阈值，用于深度检索后判断（默认 0.55）
    
    Returns:
        dict: {
            "source": "knowledge" | "web",
            "items": [...],
            "decision_reason": "决策原因说明"
        }
    
    注意：
    - 中文 embedding 相似度通常在 0.45-0.65 之间
    - 0.6+ 已属于强相关，0.7+ 是非常罕见的高度重合
    - 第二轮阈值比第一轮略低是正常的（top_k 增大影响）
    """
    print(f"\n[Router] 开始路由查询: {query}")
    
    # 集成 reranker 流程
    from retrieval.reranker import rerank
    print(f"[Router] Milvus 粗排检索 (top_k=200)...")
    try:
        milvus_results = search_knowledge(query, top_k=200)
    except Exception as e:
        print(f"[Router] 知识库检索失败: {e}，降级到网络搜索")
        return _fallback_to_web_search(query, "知识库检索失败")

    if not milvus_results:
        print(f"[Router] 知识库无结果，降级到网络搜索")
        return _fallback_to_web_search(query, "知识库无结果")

    # 构造 reranker 输入格式
    docs = []
    for r in milvus_results:
        docs.append({
            "id": r.get("id"),
            "text": r.get("content", ""),
            "score": r.get("score", 0)
        })

    print(f"[Router] reranker 精排 (topk=50)...")
    reranked = rerank(query, docs, topk=50)

    if not reranked:
        print(f"[Router] reranker 无结果，降级到网络搜索")
        return _fallback_to_web_search(query, "reranker 无结果")

    # 统一返回前5条
    final_docs = reranked[:5]
    print(f"[Router] 返回知识库精排结果 {len(final_docs)} 条")
    # 格式化输出
    items = []
    for d in final_docs:
        items.append({
            "title": "知识库条目",
            "snippet": d["text"],
            "score": d["rerank_score"],
            "id": d["id"]
        })
    return {
        "source": "knowledge",
        "items": items,
        "decision_reason": "Milvus+reranker 精排"
    }


def _format_knowledge_result(results, reason):
    """格式化知识库结果"""
    items = []
    for r in results:
        if isinstance(r, dict):
            items.append({
                'title': r.get('source', '知识库条目'),
                'snippet': r.get('content', ''),
                'score': r.get('score'),
                'id': r.get('id')
            })
    
    return {
        "source": "knowledge",
        "items": items,
        "decision_reason": reason
    }


def _fallback_to_web_search(query, reason):
    """降级到网络搜索"""
    print(f"[Router] 执行网络搜索...")
    web_result = _search_internet_impl(query, num=5, with_snippets=True, force_chinese=True)
    
    # web_result 已经是 JSON 字符串，需要解析
    try:
        web_data = json.loads(web_result)
        web_data["decision_reason"] = reason
        return web_data
    except Exception:
        return {
            "source": "web",
            "items": [],
            "decision_reason": reason,
            "error": "网络搜索结果解析失败"
        }
