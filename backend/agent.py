# agent.py - 智能助手主文件
from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain.agents import create_agent

import json
from manager import llm
from knowledge_base import search_knowledge

# -------------------------
# 工具定义
# -------------------------

@tool
def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for information. Use this first before searching the internet."""
    try:
        results = search_knowledge(query, top_k=5, similarity_threshold=0.5)
        
        if not results or len(results) == 0:
            return json.dumps({
                "found": False,
                "message": "知识库中没有找到相关信息。"
            }, ensure_ascii=False)
        
        # 格式化结果
        formatted_results = []
        for item in results:
            formatted_results.append({
                "content": item.get("content", ""),
                "source": item.get("source", ""),
                "similarity": round(item.get("similarity", 0), 3)
            })
        
        return json.dumps({
            "found": True,
            "count": len(formatted_results),
            "results": formatted_results
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "found": False,
            "error": str(e)
        }, ensure_ascii=False)


@tool
def search_internet(query: str) -> str:
    """Search the internet for information. Use this when knowledge base search returns no results or low similarity."""
    try:
        search = DuckDuckGoSearchResults(output_format="json", max_results=5)
        result = search.invoke(query)
        parsed = json.loads(result)
        
        # 格式化结果
        if isinstance(parsed, list) and len(parsed) > 0:
            formatted = []
            for item in parsed:
                formatted.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", "")
                })
            return json.dumps({
                "found": True,
                "count": len(formatted),
                "results": formatted
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "found": False,
                "message": "网络搜索未找到结果。"
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "found": False,
            "error": str(e)
        }, ensure_ascii=False)


# -------------------------
# 智能检索函数
# -------------------------

def smart_retrieve(query: str, similarity_threshold: float = 0.5):
    """
    智能检索：先搜索知识库，如果没有结果或相似度太低，再搜索网络
    
    Args:
        query: 查询问题
        similarity_threshold: 相似度阈值，低于此值则使用网络搜索
    
    Returns:
        dict: 包含检索结果和来源的信息
    """
    # 先搜索知识库
    kb_results = search_knowledge(query, top_k=5, similarity_threshold=similarity_threshold)
    
    # 检查知识库结果的质量
    use_kb = False
    kb_data = []
    
    if kb_results and len(kb_results) > 0:
        # 检查是否有高相似度的结果
        high_similarity_count = sum(1 for r in kb_results if r.get('similarity', 0) >= similarity_threshold)
        if high_similarity_count >= 2:  # 至少2条高相似度结果
            use_kb = True
            for item in kb_results:
                kb_data.append({
                    "content": item.get("content", ""),
                    "source": item.get("source", ""),
                    "similarity": item.get("similarity", 0),
                    "type": "knowledge_base"
                })
    
    # 如果知识库没有足够结果，搜索网络
    web_data = []
    if not use_kb or len(kb_data) < 2:
        try:
            search = DuckDuckGoSearchResults(output_format="json", max_results=3)
            result = search.invoke(query)
            parsed = json.loads(result)
            
            if isinstance(parsed, list) and len(parsed) > 0:
                for item in parsed:
                    web_data.append({
                        "title": item.get("title", ""),
                        "content": item.get("snippet", ""),
                        "source": item.get("link", ""),
                        "type": "web_search"
                    })
        except Exception as e:
            print(f"网络搜索错误: {e}")
    
    return {
        "knowledge_base": kb_data,
        "web_search": web_data,
        "primary_source": "knowledge_base" if use_kb and len(kb_data) >= 2 else "web_search"
    }


# -------------------------
# 工具集合
# -------------------------
ALL_TOOLS = [
    search_knowledge_base,
    search_internet,
]


# -------------------------
# Agent 创建函数
# -------------------------

from prompt import system_prompt_template
from langchain_core.prompts import ChatPromptTemplate

def create_rag_agent():
    """统一创建带工具的 agent（使用 prompt.py 的模板）"""

    # 直接把 template 当作 system prompt，输入格式留空
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template.template),
        ("human", "{input}")  # create_agent 会将实际问题映射到 {input}
    ])

    agent = create_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=prompt
    )

    return agent
