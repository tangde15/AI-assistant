from langchain_community.embeddings import FakeEmbeddings
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os
from pathlib import Path
import httpx

# 使用绝对路径加载配置文件（在项目根目录）
env_path = Path(__file__).parent.parent / "config.env"
load_dotenv(env_path, override=True)

# 初始化 embedding 函数 - 通过远程 API 调用
def get_embedding(texts):
    """
    通过 SiliconFlow API 获取 embedding 向量
    texts: 字符串列表
    返回: 向量列表，每个向量是 1024 维
    """
    api_key = os.getenv("SILICONFLO_API_KEY")
    base_url = os.getenv("SILICONFLO_BASE_URL", "https://api.siliconflow.cn/v1")
    model = os.getenv("SILICONFLO_EMBEDDING_MODEL", "BAAI/bge-m3")
    
    # 确保 texts 是列表
    if isinstance(texts, str):
        texts = [texts]

    # 分批请求以避免单次请求体过大导致 413 错误
    batch_size = int(os.getenv("SILICONFLO_EMBEDDING_BATCH_SIZE", 16))
    url = f"{base_url}/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    all_embeddings = []
    # 简单重试逻辑
    def _post_with_retry(payload, retries=2):
        for attempt in range(retries + 1):
            try:
                resp = httpx.post(url, headers=headers, json=payload, timeout=30.0)
                resp.raise_for_status()
                return resp.json()
            except Exception as ex:
                if attempt == retries:
                    raise
        return None

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        data = {"model": model, "input": batch}
        result = _post_with_retry(data, retries=2)
        # 提取向量
        batch_embeddings = [item["embedding"] for item in result.get("data", [])]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings

# 创建一个兼容的 embedding_model 对象
class EmbeddingModel:
    def encode(self, texts):
        """
        兼容 FlagEmbedding 的 encode 方法
        返回格式: {'dense_vecs': [[...], [...]]}
        """
        embeddings = get_embedding(texts)
        return {'dense_vecs': embeddings}

embedding_model = EmbeddingModel()

# 初始化 embedding 函数
fakeEmbeddings = FakeEmbeddings(size=1024)

# 初始化聊天模型
deepseek_chat = init_chat_model(
    model="deepseek-chat",
    openai_api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url=os.environ.get('DEEPSEEK_BASE_URL'),
)

from pymilvus import MilvusClient

MILVUS_HOST = os.getenv("MILVUS_HOST")
MILVUS_PORT = os.getenv("MILVUS_PORT")
MILVUS_DB_NAME = os.getenv("MILVUS_DATABASE")

# 初始化 Milvus 客户端
milvus_client = MilvusClient(
    host = MILVUS_HOST,
    port = MILVUS_PORT,
    db_name = MILVUS_DB_NAME
)
