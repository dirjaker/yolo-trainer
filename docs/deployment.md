# 部署指南

> YOLO Trainer 完整部署指南 — 涵盖单机部署与 Docker 部署两种方式

---

## 📋 目录

- [环境要求](#环境要求)
- [端口规划](#端口规划)
- [单机部署](#单机部署)
  - [1. 安装 Conda 并创建环境](#1-安装-conda-并创建环境)
  - [2. 安装 Python 依赖](#2-安装-python-依赖)
  - [3. 构建前端](#3-构建前端)
  - [4. 启动 API 服务](#4-启动-api-服务)
  - [5. 启动一体化前端服务器](#5-启动一体化前端服务器)
  - [6. 可选：启动 Celery Worker](#6-可选启动-celery-worker)
  - [7. 可选：种子数据](#7-可选种子数据)
- [Docker 部署](#docker-部署)
  - [1. 前置条件](#1-前置条件)
  - [2. 快速启动](#2-快速启动)
  - [3. 部署脚本](#3-部署脚本)
  - [4. 服务架构](#4-服务架构)
  - [5. 开发模式](#5-开发模式)
- [环境变量参考](#环境变量参考)
- [常见问题](#常见问题)

---

## 环境要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4 核 | 8 核+ |
| 内存 | 8 GB | 16 GB+ |
| GPU | NVIDIA GPU 4 GB+（训练需要） | NVIDIA GPU 8 GB+ |
| 存储 | 50 GB | 200 GB+ SSD |

### 软件要求

| 软件 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ / 推荐 3.12 | 后端运行环境 |
| Conda / Miniconda | 最新 | Python 环境管理 |
| Node.js | 18+ | 前端构建 |
| Docker | 24+ | Docker 部署 |
| Docker Compose | 2.x | Docker 编排 |
| Redis | 6.0+ | Celery 任务队列（训练功能需要） |
| NVIDIA Driver | 525+ | GPU 训练需要 |
| CUDA | 11.8+ | GPU 训练需要 |

---

## 端口规划

YOLO Trainer 使用以下端口，请确保未被占用：

| 端口 | 服务 | 说明 |
|------|------|------|
| **10001** | 前端 Web 服务器 | `docs-ui/server.py` 或 `web_server.py`，静态文件 + API 反向代理 |
| **10003** | API 服务 | FastAPI + Uvicorn，提供 REST API 和 Swagger 文档 |
| 5173 | Vite 开发服务器 | 仅开发模式使用，API 代理到 10003 |
| 5432 | PostgreSQL | Docker 部署时使用 |
| 6379 | Redis | Docker 部署时使用 |
| 9000/9001 | MinIO | 对象存储，Docker 部署时使用 |
| 5555 | Flower | Celery 任务监控 |
| 8080+ | 模型推理服务 | 部署模块动态分配 |

核心流程：

```
浏览器 → :10001 (前端 + API 代理) → :10003 (FastAPI)
```

### 端口检测

```bash
# 检查端口是否被占用
lsof -i :10001
lsof -i :10003

# 或在启动前释放端口
kill -9 $(lsof -t -i:10001) 2>/dev/null
kill -9 $(lsof -t -i:10003) 2>/dev/null
```

---

## 单机部署

适用于开发、测试和小规模生产环境。

### 1. 安装 Conda 并创建环境

```bash
# 若尚未安装 Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
eval "$($HOME/miniconda3/bin/conda shell.bash hook)"

# 创建 Python 3.12 环境
conda create -n yolo-trainer python=3.12 -y
conda activate yolo-trainer
```

### 2. 安装 Python 依赖

```bash
cd /path/to/yolo-trainer

# 安装后端依赖
pip install -r requirements.txt
```

`requirements.txt` 包含的核心依赖：FastAPI、Uvicorn、SQLAlchemy（异步）、Pydantic v2、python-jose、passlib、python-multipart、httpx、Pillow、PyYAML 等。

> **注意**：`celery` 和 `redis` 等可选依赖如需使用，请额外安装：
> ```bash
> pip install celery[redis] redis
> ```

### 3. 构建前端

```bash
cd frontend
npm install
npm run build          # 输出到 frontend/dist/
```

> 如果服务器上没有 Node.js，也可以在本地构建后将 `frontend/dist/` 上传到服务器。

### 4. 启动 API 服务

```bash
cd backend

# 创建 .env 配置文件（可选，使用默认值无需此步骤）
cp ../.env.example ../.env
# 编辑 ../.env，修改密钥等敏感配置

# 启动 FastAPI 服务（端口 10003）
DEBUG=true uvicorn main:app --host 0.0.0.0 --port 10003 --reload
```

启动后访问：
- **API 文档 (Swagger UI)**：http://localhost:10003/docs
- **API 文档 (ReDoc)**：http://localhost:10003/redoc
- **健康检查**：http://localhost:10003/health

生产环境建议使用 Gunicorn + Uvicorn Worker：

```bash
gunicorn main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:10003 \
  --timeout 120
```

### 5. 启动一体化前端服务器

项目提供了 `docs-ui/server.py`，可同时提供前端静态文件服务和 API 反向代理。

```bash
cd docs-ui
python server.py          # 端口 10001
```

服务器逻辑：

- 所有 `/api/` 开头的请求 → 反向代理到 `http://127.0.0.1:10003`
- 其他请求 → 提供 `frontend/dist/` 目录下的静态文件
- SPA fallback：未匹配路径返回 `index.html`

启动后访问：
- **Web 界面**：http://localhost:10001
- **API 文档**：http://localhost:10003/docs

> 也可以使用根目录下的 `web_server.py`（功能等价）。

### 6. 可选：启动 Celery Worker

训练功能需要 Redis + Celery Worker：

```bash
# 终端 1：启动 Redis
redis-server

# 终端 2：启动 Celery Worker
cd backend
celery -A app.core.celery worker --loglevel=info --concurrency=1 -Q training,export,evaluate
```

### 7. 可选：种子数据

```bash
cd backend
python seed_examples.py
```

插入示例数据：4 个数据集 + 4 个训练任务 + 2 个模型版本。
默认测试账号：`demo3` / `demo123`

---

## Docker 部署

Docker 部署提供完整的生产环境，包括前端、后端、数据库、缓存、任务队列和对象存储。

### 1. 前置条件

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo apt install docker-compose-plugin   # 或 docker-compose v2

# 安装 NVIDIA Container Toolkit（GPU 训练需要）
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/nvidia-docker/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-docker.gpg
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-docker.gpg] https://#' | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update && sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 2. 快速启动

```bash
cd /path/to/yolo-trainer

# 复制环境变量模板
cp .env.example .env
# 编辑 .env，修改密钥等敏感配置

# 构建并启动所有服务
docker compose -f docker/docker-compose.yml up -d --build
```

启动后可访问：

| 服务 | URL | 说明 |
|------|-----|------|
| Web 界面 | http://localhost:5173 | Nginx 前端（Docker 内为 80 端口，映射到 5173） |
| API 文档 | http://localhost:10003/docs | Swagger UI |
| MinIO 控制台 | http://localhost:9001 | 对象存储管理 |
| Flower | http://localhost:5555 | Celery 任务监控 |

### 3. 部署脚本

项目提供了便捷的部署脚本 `scripts/deploy.sh`：

```bash
# 构建镜像
./scripts/deploy.sh build

# 构建 + 启动 + 初始化数据库
./scripts/deploy.sh up

# 停止所有服务
./scripts/deploy.sh down

# 重启所有服务
./scripts/deploy.sh restart

# 查看日志
./scripts/deploy.sh logs
./scripts/deploy.sh logs backend     # 仅查看某服务

# 初始化数据库 + MinIO bucket
./scripts/deploy.sh init-db
```

### 4. 服务架构

`docker/docker-compose.yml` 定义了以下服务：

| 服务 | 镜像/Dockerfile | 端口映射 | 说明 |
|------|----------------|---------|------|
| `frontend` | `docker/Dockerfile.frontend` | `5173:80` | Nginx + Vue 构建产物，反向代理 API |
| `backend` | `docker/Dockerfile.backend` | `10003:8000` | FastAPI + Uvicorn（4 workers） |
| `worker` | `docker/Dockerfile.worker` | - | Celery Worker（训练/导出/评估队列） |
| `postgres` | `postgres:15-alpine` | `5432:5432` | 生产数据库 |
| `redis` | `redis:7-alpine` | `6379:6379` | 缓存 + Celery Broker |
| `minio` | `minio/minio:latest` | `9000:9000` `9001:9001` | 对象存储 |
| `flower` | `mheitvand/flower:latest` | `5555:5555` | Celery 监控面板 |

所有服务通过 `yolo-net` 网络互联，数据卷持久化存储。

**Dockerfile 说明：**

- `Dockerfile.backend`：基于 `python:3.10-slim`，安装后端依赖，运行 `uvicorn main:app --port 10003 --workers 4`
- `Dockerfile.frontend`：多阶段构建，先 `node:18-alpine` 构建前端，再 `nginx:alpine` 提供静态服务
- `Dockerfile.worker`：基于 `pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime`，包含 GPU 支持

**Nginx 配置（`docker/nginx.conf`）：**

- `/` → SPA fallback（静态文件）
- `/api/` → 反向代理到 `backend:8000`
- `/docs` `/redoc` `/openapi.json` → 代理到 backend
- Gzip 压缩已开启

### 5. 开发模式

开发模式支持热重载，使用覆盖文件启动：

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up
```

开发模式的差异：

- **前端**：使用 `node:18-alpine` 镜像，`npm run dev`（Vite HMR），端口 `5173:5173`
- **后端**：使用 `python:3.10-slim` 镜像，`uvicorn --reload`，端口 `10003:8000` + `5678:5678`（debugpy）
- 代码文件通过 volume 挂载，修改即生效
- 不启动 worker 和 flower

---

## 环境变量参考

所有环境变量定义在 `.env.example` 文件中，由 `backend/app/core/config.py` 中的 `Settings` 类（基于 `pydantic-settings`）加载。

### 应用配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_NAME` | `YOLO Trainer` | 应用名称 |
| `APP_VERSION` | `1.0.0` | 应用版本 |
| `DEBUG` | `false` | 调试模式（生产环境务必设置为 `false`） |
| `SECRET_KEY` | `change-me-in-production` | 通用密钥 |

### JWT 认证

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `JWT_SECRET_KEY` | 开发默认值 | JWT 签名密钥（**生产环境必须修改**） |
| `JWT_ALGORITHM` | `HS256` | JWT 签名算法 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | Token 有效期（分钟），默认 7 天 |

> ⚠️ 生产环境下，如果 `JWT_SECRET_KEY` 仍为默认值且 `DEBUG=false`，应用会拒绝启动。

### 数据库配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./yolo_trainer.db` | 数据库连接串 |

- **开发（SQLite）**：`sqlite+aiosqlite:///./yolo_trainer.db`
- **生产（PostgreSQL）**：`postgresql+asyncpg://user:password@host:5432/yolo_trainer`

> Docker 部署中会自动设置为 PostgreSQL 连接串，指向 `postgres` 服务。

### Redis / Celery

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接地址 |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery 消息队列 |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | Celery 结果存储 |

### MinIO 对象存储

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO 服务地址 |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO 访问密钥 |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO 密钥 |
| `MINIO_BUCKET` | `yolo-trainer` | 存储桶名称 |

### 服务器端口

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_HOST` | `0.0.0.0` | API 监听地址 |
| `API_PORT` | `10003` | API 监听端口 |

### 部署配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEPLOY_HOST` | `0.0.0.0` | 模型推理服务监听地址 |
| `DEPLOY_PORT_START` | `8080` | 模型推理服务起始端口 |
| `TORCHSERVE_MANAGEMENT_PORT` | `8081` | TorchServe 管理端口 |

### 文件上传

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MAX_UPLOAD_SIZE_MB` | `2048` | 最大上传文件大小（MB） |
| `UPLOAD_DIR` | `/data/uploads` | 上传文件存储目录 |
| `MODEL_DIR` | `/data/models` | 模型文件存储目录 |
| `TRAINING_DIR` | `/data/training` | 训练数据存储目录 |

### GPU 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CUDA_VISIBLE_DEVICES` | `0` | 可见 GPU 设备编号（多 GPU 用逗号分隔，如 `0,1`） |

### CORS

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CORS_ORIGINS` | `http://localhost,http://127.0.0.1` | 允许跨域的来源（逗号分隔） |

### 日志

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LOG_LEVEL` | `INFO` | 日志级别（`DEBUG`/`INFO`/`WARNING`/`ERROR`） |
| `LOG_FILE` | `/var/log/yolo-trainer/app.log` | 日志文件路径 |

---

## 常见问题

### 1. 端口被占用

```bash
# 查看端口占用
lsof -i :10001
lsof -i :10003

# 释放端口
kill -9 $(lsof -t -i:10001) 2>/dev/null
kill -9 $(lsof -t -i:10003) 2>/dev/null
```

### 2. 数据库迁移失败

```bash
# 开发环境：删除 SQLite 数据库后重启（自动重建）
rm backend/yolo_trainer.db
cd backend && DEBUG=true uvicorn main:app --port 10003

# 生产环境：使用 Alembic 迁移
cd backend
alembic upgrade head
```

### 3. 前端无法连接后端

1. 确认后端服务运行正常：`curl http://localhost:10003/health`
2. 确认前端服务器已启动：`curl http://localhost:10001`
3. 检查 CORS 配置：确认 `CORS_ORIGINS` 包含前端地址
4. Docker 部署：确认 Nginx 代理配置正确，`backend` 服务名可解析

### 4. Docker GPU 不可用

```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 检查 Docker GPU 支持
docker run --rm --gpus all nvidia/cuda:12.1-base nvidia-smi

# 确保安装了 nvidia-container-toolkit
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 5. Celery Worker 连接不上 Redis

```bash
# 检查 Redis 是否运行
redis-cli ping                # 应返回 PONG

# 检查环境变量
echo $REDIS_URL
echo $CELERY_BROKER_URL

# Docker 环境确认服务名可解析
docker compose -f docker/docker-compose.yml exec backend ping redis
```

### 6. 文件上传失败

```bash
# 检查并创建上传目录
sudo mkdir -p /data/uploads /data/models /data/training
sudo chown -R $USER:$USER /data/uploads /data/models /data/training
sudo chmod -R 755 /data
```

### 7. JWT_SECRET_KEY 未设置导致启动失败

生产环境下（`DEBUG=false`），必须设置自定义 `JWT_SECRET_KEY`：

```bash
# 生成安全密钥
python -c "import secrets; print(secrets.token_hex(32))"

# 设置环境变量
export JWT_SECRET_KEY="your-generated-hex-string"
```

---

*更多架构细节请参考 [架构设计文档](architecture.md)。*
