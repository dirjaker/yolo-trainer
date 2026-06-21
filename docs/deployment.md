# 部署指南

> YOLO Trainer 完整部署指南

---

## 📋 目录

- [环境要求](#环境要求)
- [快速开始（开发环境）](#快速开始开发环境)
- [生产环境部署](#生产环境部署)
- [GPU 配置](#gpu-配置)
- [常见问题](#常见问题)

---

## 环境要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4 核 | 8 核+ |
| 内存 | 8GB | 16GB+ |
| GPU | NVIDIA GPU 4GB+（训练需要） | NVIDIA GPU 8GB+ |
| 存储 | 50GB | 200GB+ SSD |

### 软件要求

| 软件 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 推荐 3.12 |
| Node.js | 18+ | 前端构建 |
| NVIDIA Driver | 525+ | GPU 训练 |
| CUDA | 11.8+ | GPU 训练 |
| Redis | 6.0+ | 任务队列（可选） |

---

## 快速开始（开发环境）

### 1. 克隆项目

```bash
git clone https://github.com/dirjaker/yolo-trainer.git
cd yolo-trainer
```

### 2. 安装后端

```bash
# 创建虚拟环境
conda create -n yolo-trainer python=3.12 -y
conda activate yolo-trainer

# 安装依赖
pip install -r requirements.txt
```

### 3. 启动后端

```bash
cd backend
python main.py
```

后端服务启动后：
- API 服务: http://localhost:8000
- Swagger 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

### 4. 安装并启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173

### 5. 可选：启动 Redis（训练功能需要）

```bash
# 安装 Redis
sudo apt install redis-server

# 启动 Redis
redis-server

# 启动 Celery Worker
cd backend
celery -A app.core.celery worker --loglevel=info
```

---

## 生产环境部署

### 1. 环境变量配置

创建 `.env` 文件或设置环境变量：

```bash
# 数据库（生产推荐 PostgreSQL）
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/yolo_trainer

# Redis
REDIS_URL=redis://localhost:6379/0

# 安全密钥（必须修改！）
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# CORS 白名单
CORS_ORIGINS=https://your-domain.com

# 文件上传目录
UPLOAD_DIR=/data/uploads

# 调试模式
DEBUG=false
```

### 2. 部署后端

```bash
# 安装依赖
pip install -r requirements.txt
pip install uvicorn[standard] gunicorn

# 使用 Gunicorn + Uvicorn Worker 启动
cd backend
gunicorn main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile /var/log/yolo-trainer/access.log \
  --error-logfile /var/log/yolo-trainer/error.log
```

### 3. 部署前端

```bash
cd frontend
npm install
npm run build

# 部署到 Nginx
sudo cp -r dist/* /var/www/yolo-trainer/
```

### 4. 配置 Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /var/www/yolo-trainer;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # 静态文件代理
    location /static {
        proxy_pass http://127.0.0.1:8000;
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/yolo-trainer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. 配置 HTTPS

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 6. systemd 服务

**后端服务：**

```ini
# /etc/systemd/system/yolo-trainer.service
[Unit]
Description=YOLO Trainer Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/yolo-trainer/backend
Environment="PATH=/opt/yolo-trainer/venv/bin"
ExecStart=/opt/yolo-trainer/venv/bin/gunicorn main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Celery Worker：**

```ini
# /etc/systemd/system/yolo-trainer-worker.service
[Unit]
Description=YOLO Trainer Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/yolo-trainer/backend
Environment="PATH=/opt/yolo-trainer/venv/bin"
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/opt/yolo-trainer/venv/bin/celery -A app.core.celery worker --loglevel=info --concurrency=2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable yolo-trainer yolo-trainer-worker
sudo systemctl start yolo-trainer yolo-trainer-worker
```

---

## GPU 配置

### 检查 GPU 状态

```bash
# 查看 GPU 信息
nvidia-smi

# 测试 PyTorch GPU
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

### 多 GPU 配置

```bash
# 环境变量
export CUDA_VISIBLE_DEVICES=0,1
```

在训练配置中指定：
```json
{
  "config": {
    "device": "0,1"
  }
}
```

### GPU 内存优化

```json
{
  "config": {
    "batch_size": 8,
    "img_size": 416,
    "workers": 4
  }
}
```

---

## 常见问题

### 1. GPU 未检测到

```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 检查 CUDA
nvcc --version

# 检查 PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

### 2. 端口被占用

```bash
# 查看端口占用
lsof -i :8000

# 杀死进程
kill -9 <PID>
```

### 3. 数据库迁移失败

```bash
# 开发环境：删除数据库重新创建
rm backend/yolo_trainer.db
python main.py  # 自动创建

# 生产环境：使用 Alembic
cd backend
alembic upgrade head
```

### 4. 前端无法连接后端

检查：
1. 后端服务是否运行：`curl http://localhost:8000/health`
2. CORS 配置是否正确：检查 `CORS_ORIGINS` 环境变量
3. Nginx 代理是否配置正确

### 5. 文件上传失败

```bash
# 检查上传目录权限
ls -la /data/uploads
sudo chown -R www-data:www-data /data/uploads
sudo chmod -R 755 /data/uploads
```

---

*更多部署细节请参考 [架构设计文档](architecture.md)。*
