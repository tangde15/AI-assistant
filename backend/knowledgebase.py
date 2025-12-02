from pymilvus import DataType
import json
from manager import milvus_client, embedding_model
from uuid import uuid4

def create_knowledgebase():
    if milvus_client.has_collection("knowledgebase"):
        print("Collection 'knowledgebase' already exists.")
        return

    # 创建集合模式（Schema）
    schema = milvus_client.create_schema(
        auto_id=True,
        enable_dynamic_fields=True,
    )

    # 添加字段
    schema.add_field(
        field_name="id", 
        datatype=DataType.VARCHAR, 
        is_primary=True, 
        max_length=100
    )
    schema.add_field(
        field_name="content",
        datatype=DataType.VARCHAR,
        max_length=65535
    )
    schema.add_field(
        field_name="dense_vector", 
        datatype=DataType.FLOAT_VECTOR, 
        # dim 指定向量维度
        dim=1024
    )
    schema.add_field(
        field_name="source",
        datatype=DataType.VARCHAR,
        max_length=65535
    )
    schema.add_field(
        field_name="timestamp",
        datatype=DataType.DOUBLE
    )
    
    # 创建索引
    index_params = milvus_client.prepare_index_params()

    index_params.add_index(
        field_name="id",
        index_type="AUTOINDEX"
    )

    index_params.add_index(
        field_name="dense_vector", 
        index_type="AUTOINDEX",
        metric_type="COSINE"
    )

    # 创建集合
    milvus_client.create_collection(
        collection_name="knowledgebase",
        schema=schema,
        index_params=index_params
    )

    res = milvus_client.get_load_state(
        collection_name="knowledgebase"
    )

    print(res)

def insert_knowledge(knowledge: dict):
    """
    插入知识到知识库
    knowledge: {
        "content": "知识内容",
        "source": "知识来源"
    }
    """
    vector = embedding_model.encode([knowledge["content"]])['dense_vecs'][0]

    from datetime import datetime

    now = datetime.now()
    timestamp = now.timestamp()

    res = milvus_client.insert(
        collection_name="knowledgebase",
        data=[{
            "content": knowledge["content"],
            "dense_vector": vector,
            "source": knowledge["source"],
            "timestamp": timestamp
        }]
    )

    print(f"Inserted knowledge, ID: {res['ids'][0]}")

    return res['ids'][0]


def search_knowledge(query: str, top_k: int = 5):
    query_vector = embedding_model.encode([query])['dense_vecs'][0]
    res = milvus_client.search(
        collection_name="knowledgebase",
        data=[query_vector],
        limit=top_k,
        # search_params={
        #     "params": {
        #         "radius": 0.49,
        #         "range_filter": 0.99
        #     }
        # },
    )

    data = []
    # [{'id': '462014062345986305', 'content': 'npl是自然语言处理的缩写，指计算机科学领域与人工智能领域中的一个重要分支，旨在实现计算机对人类语言的理解 、解释和生成功能。', 'source': 'https://zh.wikipedia.org/wiki/ai', 'timestamp': 1763281925.831246}, {'id': '462014062345986304', 'content': '人工 智能是计算机科学的一个分支，致力于创造能够执行通常需要人类智能的任务的系 统。', 'source': '维基百科', 'timestamp': 1763281845.379149}]
    for hits in res:
        for hit in hits:
            # 尝试提取相似度/分数信息（不同 milvus 版本可能返回不同的键）
            score = None
            if isinstance(hit, dict):
                score = hit.get('score') or hit.get('distance') or hit.get('score_value')
            try:
                entity = milvus_client.get(
                    collection_name="knowledgebase",
                    ids=[hit['id']],
                    output_fields=["id", "content", "source", "timestamp"]
                )
                ent = entity[0]
                # 附加相似度分数到返回结果，数值含义取决于 milvus 设置（越大越相似或越小越相似）
                ent['score'] = score
                data.append(ent)
            except Exception:
                # 如果通过 id 查询失败，仍回退到只用 hit 信息
                rec = {'id': hit.get('id'), 'score': score}
                data.append(rec)

    return data



