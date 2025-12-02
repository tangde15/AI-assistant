# knowledge_base.py - Milvus 知识库操作
from pymilvus import DataType
from manager import milvus_client, get_embedding_model
from datetime import datetime
import json


def create_knowledgebase():
    """创建知识库集合（不需要加载 embedding 模型）"""
    if milvus_client.has_collection("knowledgebase"):
        print("知识库集合已存在")
        return
    
    # 创建集合模式
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
    print("知识库集合创建成功")


def search_knowledge(query: str, top_k: int = 5, similarity_threshold: float = 0.5):
    """
    搜索知识库
    
    Args:
        query: 查询文本
        top_k: 返回结果数量
        similarity_threshold: 相似度阈值（0-1），低于此值的结果会被过滤
    
    Returns:
        list: 搜索结果列表，每个结果包含 content, source, id, similarity
    """
    try:
        # 获取 embedding 模型（延迟加载）
        embedding_model = get_embedding_model()
        # 生成查询向量
        query_vector = embedding_model.encode([query])['dense_vecs'][0]
        
        # 搜索
        res = milvus_client.search(
            collection_name="knowledgebase",
            data=[query_vector],
            limit=top_k,
        )
        
        results = []
        for hits in res:
            for hit in hits:
                # 计算相似度（COSINE 距离转换为相似度）
                distance = hit.get('distance', 1.0)
                similarity = 1 - distance  # COSINE 距离转相似度
                
                # 过滤低相似度结果
                if similarity < similarity_threshold:
                    continue
                
                # 获取完整实体
                entity = milvus_client.get(
                    collection_name="knowledgebase",
                    ids=[hit['id']],
                    output_fields=["id", "content", "source", "timestamp"]
                )
                
                if entity:
                    entity[0]['similarity'] = similarity
                    results.append(entity[0])
        
        return results
    except Exception as e:
        print(f"搜索知识库时出错: {e}")
        return []


def insert_knowledge(content: str, source: str = "unknown"):
    """
    插入知识到知识库
    
    Args:
        content: 知识内容
        source: 知识来源
    """
    try:
        # 获取 embedding 模型（延迟加载）
        embedding_model = get_embedding_model()
        # 生成向量
        vector = embedding_model.encode([content])['dense_vecs'][0]
        
        # 插入数据
        timestamp = datetime.now().timestamp()
        res = milvus_client.insert(
            collection_name="knowledgebase",
            data=[{
                "content": content,
                "dense_vector": vector,
                "source": source,
                "timestamp": timestamp
            }]
        )
        
        return res['ids'][0] if res and 'ids' in res else None
    except Exception as e:
        print(f"插入知识库时出错: {e}")
        return None

