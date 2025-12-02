
# Custom-built AI Assistant

本项目为前后端分离的智能助手系统，支持知识库检索与联网搜索，采用 React+Vite 前端与 FastAPI/LangChain 后端。**easyRAG 目录及其内容已不再参与主流程，可直接删除。**

## 目录结构（核心部分）

```
├── agent.py                # Agent 逻辑与工具注册
├── app.py                  # FastAPI 主后端入口
├── config.env              # 环境变量配置
├── conversations.py        # 对话历史存储
├── knowledge_base.py       # 知识库检索逻辑
├── knowledgebase.py        # 兼容旧接口
├── manager.py              # 模型与配置管理
├── memory.py               # 会话记忆管理
├── prompt.py               # 系统提示词模板
├── tools.py                # 联网搜索/知识库/智能搜索等工具
├── frontend/               # 前端（React+Vite+TS）
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── global.css
│       ├── pages/Chat.tsx
│       ├── components/MarkdownMessage.tsx
│       ├── components/ToolOutput.tsx
│       └── lib/api.ts
├── scripts/                # 数据导入等脚本
├── static/                 # 静态资源
└── README.md
```

> ⚠️ `easyRAG/` 及其子目录为历史参考实现，当前主流程完全不依赖，可安全删除。

## 主要功能

- ✅ Milvus 向量知识库检索（可选）
- ✅ 智能判断是否需要联网搜索（DDG+多轮重写+摘要+Rerank）
- ✅ 流式对话响应，支持工具卡片插入
- ✅ React+Vite+TS 前端，深色卡片风格
- ✅ FastAPI/LangChain 后端，接口统一

## 配置说明

编辑 `config.env` 文件：

```env
SILICONFLO_API_KEY=your_api_key
SILICONFLO_MODEL=deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
SILICONFLO_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLO_EMBEDDING_MODEL=BAAI/bge-m3
MILVUS_HOST=127.0.0.1
MILVUS_PORT=19530
MILVUS_DATABASE=AI
```

## 安装依赖

后端：
```bash
pip install -r requirements.txt
# 或手动安装
pip install fastapi uvicorn langchain langchain-openai langchain-community pymilvus FlagEmbedding duckduckgo-search python-dotenv
```

前端：
```bash
cd frontend
npm install
```

## 启动方式

### 1. 启动后端
```bash
cd "项目根目录"
python app.py
# 或
uvicorn app:app --host 0.0.0.0 --port 8000
```
后端接口地址：`http://localhost:8000`

### 2. 启动前端
```bash
cd frontend
npm run dev
```
前端开发地址：`http://localhost:5173`（或终端提示端口）

## 使用说明

1. **知识库检索**：优先从 Milvus 知识库中检索相关信息
2. **智能判断**：如知识库无高分结果，自动多轮联网搜索（DDG+重写+摘要+Rerank）
3. **流式响应**：AI/工具卡片实时插入，体验流畅

## API 说明

### POST /api/chat
流式聊天接口，支持 session_id 续聊
```json
{
  "question": "你的问题",
  "session_id": "可选，会话ID"
}
```
响应：NDJSON 流
- `{"type": "session", "content": "session_id"}`
- `{"type": "ai", "content": "回答内容"}`
- `{"type": "tool", "content": "...", "tool_name": "..."}`

### GET /api/health
健康检查

## 常见问题

1. Milvus 可选，未启用时知识库检索自动降级为联网搜索
2. easyRAG 目录可删除，不影响主流程
3. 前端如需自定义主题/样式，编辑 `frontend/src/global.css`

---
如有问题请提 issue 或联系作者。



