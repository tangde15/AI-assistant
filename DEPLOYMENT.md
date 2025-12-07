# 部署说明 DEPLOYMENT.md

本项目支持一键容器化部署，推荐使用 Docker Compose。

## 环境准备

1. 安装 [Docker](https://docs.docker.com/get-docker/) 和 [Docker Compose](https://docs.docker.com/compose/install/)
2. 克隆项目代码
   ```bash
   git clone <你的仓库地址>
   cd <项目目录>
   ```
3. 配置环境变量
   ```bash
   cp config.env.example config.env
   # 编辑 config.env，填写你的 API 密钥和参数
   ```

## 启动服务

### 一键启动
```bash
chmod +x deploy.sh
./deploy.sh start
```
或直接使用：
```bash
docker compose up -d
```

### 访问地址
- 前端：http://localhost:3000
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 常用命令
```bash
./deploy.sh stop      # 停止所有服务
./deploy.sh restart   # 重启所有服务
./deploy.sh logs      # 查看所有服务日志
```

## 故障排查

- **Milvus 连接失败**
  ```bash
  docker compose exec milvus curl http://localhost:9091/healthz
  docker compose restart etcd minio milvus
  ```
- **后端 API 错误**
  ```bash
  docker compose logs backend
  docker compose exec backend env | grep DEEPSEEK
  ```
- **前端无法访问**
  ```bash
  docker compose logs frontend
  netstat -ano | findstr 3000
  ```

- **OCR / PPT 图片文字未被识别**
  - 问题表现：PPT 中的图片（截图表格、图表数值）或 PDF 扫描页内的文字没有被提取，导致知识库缺失相关内容。
  - 检查要点：
    1. 确认 `opencv-python` 或 `opencv-python-headless` 已安装（用于将 `PIL.Image` 转为 `numpy.ndarray`）。
    2. 检查后端日志，关注关键字：`[OCR] 初始化`、`[OCR] 识别异常`、`[向量化]`。
    3. 若出现 `PDX has already been initialized` 或类似错误，说明 OCR 被重复初始化，需检查是否使用单例初始化（项目已实现单例保护）。
  - 临时解决：
    ```bash
    # 降低 embedding 批量大小，避免向远端 API 一次性上传过多导致 413 错误
    $env:SILICONFLO_EMBEDDING_BATCH_SIZE = "4"
    cd backend
    & "E:/python project/Custom-built AI assistant/venv/Scripts/Activate.ps1"
    & "E:/python project/Custom-built AI assistant/venv/Scripts/python.exe" app.py
    ```
  - 备注：已在代码中实现将 `PIL.Image` 转为 numpy（BGR）并进行兼容性调用，若仍有问题请贴出后端日志供进一步定位。

## 安全建议
- 不要上传 config.env 到仓库
- 修改 MinIO 默认密码
- 生产环境建议配置 HTTPS
- 定期备份数据

## 其他说明
- 如需自定义端口、服务参数，请修改 docker-compose.yml
- Nginx 配置见 nginx.conf

如有问题请提交 Issue 或联系维护者。

# Custom-built AI Assistant Docker 部署指南

本指南将帮助您在 Linux 云服务器上使用 Docker Compose 部署本项目。

## 系统要求
- Linux 服务器（Ubuntu 20.04+、CentOS 7+ 或其他主流发行版）
- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB RAM
- 至少 20GB 磁盘空间

## 一、安装 Docker 和 Docker Compose

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker

docker --version
docker compose version
```

### CentOS/RHEL
```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker

docker --version
docker compose version
```

### 配置 Docker 权限（可选）
```bash
sudo usermod -aG docker $USER
newgrp docker
```

## 二、准备项目文件

### 1. 克隆或上传项目
```bash
git clone <你的仓库地址>
cd Custom-built AI assistant
```

### 2. 配置环境变量
```bash
cp config.env.example config.env
nano config.env
```
**必须配置的环境变量：**
```env
SILICONFLO_API_KEY=你的SiliconFlow密钥
SILICONFLO_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLO_EMBEDDING_MODEL=BAAI/bge-m3
MILVUS_HOST=milvus
MILVUS_PORT=19530
MILVUS_DATABASE=AI
```

## 三、部署应用

### 1. 构建并启动所有服务
```bash
docker compose up -d
docker compose logs -f
```

### 2. 验证服务状态
```bash
docker compose ps
```

### 3. 访问应用
- 前端界面: `http://your-server-ip:3000`
- 后端 API: `http://your-server-ip:8000`
- API 文档: `http://your-server-ip:8000/docs`

### 4. 使用 Nginx 反向代理（生产环境推荐）
```bash
docker compose --profile production up -d
```
- 现在可通过 80 端口访问: `http://your-server-ip` 或 `http://your-domain.com`

## 四、常用命令
```bash
docker compose up -d      # 启动所有服务
docker compose down       # 停止所有服务
docker compose restart    # 重启所有服务
docker compose logs -f    # 实时查看日志
docker compose ps         # 查看容器状态
git pull                  # 拉取最新代码
docker compose up -d --build  # 重新构建并启动
```

## 五、数据备份与恢复
```bash
# 备份上传的文件
sudo tar -czf files-backup-$(date +%Y%m%d).tar.gz backend/files/

# 备份 Milvus 数据（需先停止服务）
docker compose stop milvus
sudo tar -czf milvus-backup-$(date +%Y%m%d).tar.gz /var/lib/docker/volumes/ai_milvus_data

docker compose start milvus

# 恢复上传的文件
tar -xzf files-backup-YYYYMMDD.tar.gz -C backend/

# 恢复 Milvus 数据
docker compose stop milvus
sudo tar -xzf milvus-backup-YYYYMMDD.tar.gz -C /var/lib/docker/volumes/
docker compose start milvus
```

## 六、安全配置
- 配置防火墙，仅开放必要端口（22/80/443）
- 生产环境建议配置 HTTPS（可用 Certbot + Nginx）
- 不要上传 config.env 到仓库
- 定期备份数据

## 七、故障排查
- 查看容器状态：`docker compose ps`
- 查看错误日志：`docker compose logs backend`
- 检查端口占用：`sudo netstat -tulpn | grep -E ':(3000|8000|19530)'`
- 检查环境变量加载：`docker compose exec backend env | grep SILICONFLO`

## 八、升级指南
```bash
git pull
# 备份数据后
docker compose down
docker compose up -d --build
```

---

**如有问题请提交 Issue 或联系维护者。祝您部署顺利！** 🚀

## 近期优化与重要变更

- 依赖冲突修复：已彻底移除 `peft`，`reranker` 改为使用 transformers 原生实现，避免 peft/sentence-transformers/transformers 依赖冲突带来的问题。
- 检索与精排升级：知识库检索流程调整为 Milvus topk=200 → reranker 精排 topk=50 → 最终返回 5 条，显著提升相关性。
- BGE 语义切片：采用 BGEChunker 进行按句子+token 的语义切片，提升检索召回与向量化效果。
- PPT/PDF 图片 OCR 优化：引入 Hybrid-PPT-Extractor（unstructured + python-pptx + PaddleOCR），修复了图片文字被跳过的问题并实现 OCR 单例与兼容性处理。
- 向量化稳定性：embeddings 上传使用分批与重试机制，避免单次请求过大导致 413 错误。
- 环境清理建议：提供 `pip cache purge` 与 `torch.cuda.empty_cache()` 等操作建议以减少环境干扰（无 GPU 时自动跳过）。
