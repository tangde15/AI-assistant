from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

# 直接使用 transformers 加载 reranker，避免 FlagEmbedding 的 trainer 依赖
model = AutoModelForSequenceClassification.from_pretrained('BAAI/bge-reranker-large')
tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-reranker-large')
model.eval()

def compute_score(pairs):
    """计算 query-doc 对的相似度分数"""
    with torch.no_grad():
        inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512)
        scores = model(**inputs, return_dict=True).logits.view(-1,).float()
        return scores.tolist()

def rerank(query: str, docs: list, topk: int = 50):
    """
    docs: [{'id':..., 'text':..., 'score':...}]
    topk: reranker 精排范围
    """
    if len(docs) == 0:
        return []
    candidates = docs[:topk]
    pairs = [[query, d["text"]] for d in candidates]
    scores = compute_score(pairs)
    reranked = sorted(
        [
            {
                "id": d["id"],
                "text": d["text"],
                "origin_score": d["score"],
                "rerank_score": s
            }
            for d, s in zip(candidates, scores)
        ],
        key=lambda x: x["rerank_score"],
        reverse=True
    )
    return reranked
