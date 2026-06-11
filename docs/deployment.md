# 部署指南

> YOLO Trainer 完整部署指南

---

## 📋 目录

- [环境要求](#环境要求)
- [快速部署（Docker）](#快速部署docker)
- [手动部署](#手动部署)
- [GPU 配置](#gpu-配置)
- [生产环境部署](#生产环境部署)
- [常见问题](#常见问题)

---

## 环境要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4 核 | 8 核+ |
| 内存 | 8GB | 16GB+ |
| GPU | NVIDIA GPU 4GB+ | NVIDIA GPU 8GB+ |
| 存储 | 50GB | 200GB+ SSD |

### 软件要求

| 软件 | 版本 |
|------|------|
| 操作系统 | Ubuntu 20.04+ / CentOS 7+ |
| Python | 3.10+ |
| Node.js | 18+ |
| Docker | 20.10+ |
| Docker Compose | 2.0+ |
| NVIDIA Driver | 525+ |
| CUDA | 11.8+ |
| cuDNN | 8.0+ |

---

## 快速部署（Docker）

### 1. 克隆项目

```bash
git clone https://github.com/dirjaker/yolo-trainer.git
cd yolo-trainer
```

### 2. 配置环境变量

```bash
cp .env.example .env
vim .env
```

**.env 配置示例：**
```bash
# 数据库
POSTGRES_DB=yolo_trainer
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Redis
REDIS_PASSWORD=your_redis_password

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_minio_password

# 应用配置
SECRET_KEY=your_secret_key_here
API_HOST=0.0.0.0
API_PORT=8000

# GPU 配置
CUDA_VISIBLE_DEVICES=0
```

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

### 4. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:5173 | Web UI |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| Flower | http://localhost:5555 | Celery 监控 |
| MinIO Console | http://localhost:9001 | 文件存储管理 |

### 5. 初始化数据

```bash
# 创建管理员用户
docker-compose exec backend python scripts/create_admin.py

# 初始化数据库
docker-compose exec backend alembic upgrade head
```

---

## 手动部署

### 1. 安装系统依赖

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3.10 python3.10-venv nodejs npm nginx redis-server postgresql
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3 nodejs npm nginx redis postgresql-server
```

### 2. 安装 NVIDIA 驱动和 CUDA

```bash
# 安装 NVIDIA 驱动
sudo apt install -y nvidia-driver-525

# 安装 CUDA 11.8
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
sudo sh cuda_11.8.0_520.61.05_linux.run

# 配置环境变量
echo 'export PATH=/usr/local/cuda-11.8/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# 验证安装
nvidia-smi
nvcc --version
```

### 3. 安装 MinIO

```bash
# 下载 MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# 创建数据目录
sudo mkdir -p /data/minio
sudo chown $USER:$USER /data/minio

# 启动 MinIO
minio server /data/minio --console-address ":9001"
```

### 4. 部署后端

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export DATABASE_URL=postgresql://postgres:password@localhost:5432/yolo_trainer
export REDIS_URL=redis://localhost:6379/0
export MINIO_ENDPOINT=localhost:9000
export MINIO_ACCESS_KEY=minioadmin
export MINIO_SECRET_KEY=minioadmin

# 初始化数据库
alembic upgrade head

# 启动后端服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. 部署 Worker

```bash
# 进入 worker 目录
cd worker

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖（包含 PyTorch 和 Ultralytics）
pip install -r requirements.txt

# 启动 Celery Worker
celery -A app.tasks worker --loglevel=info --concurrency=2
```

### 6. 部署前端

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build

# 部署到 Nginx
sudo cp -r dist/* /var/www/html/
```

### 7. 配置 Nginx

```nginx
# /etc/nginx/sites-available/yolo-trainer
server {
    listen 80;
    server_name your_domain.com;

    # 前端
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # MinIO
    location /files {
        proxy_pass http://localhost:9000;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/yolo-trainer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## GPU 配置

### 检查 GPU 状态

```bash
# 查看 GPU 信息
nvidia-smi

# 查看 CUDA 版本
nvcc --version

# 测试 PyTorch GPU
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

### 多 GPU 配置

```bash
# .env
CUDA_VISIBLE_DEVICES=0,1  # 使用 GPU 0 和 1
```

**在训练配置中指定 GPU：**
```json
{
  "config": {
    "device": "0,1"  // 使用多 GPU
  }
}
```

### GPU 内存优化

```python
# 启用混合精度训练
config = {
    "amp": True,  # 自动混合精度
    "cache": "ram",  # 缓存到内存
    "workers": 4  # 减少数据加载线程
}
```

---

## 生产环境部署

### 1. 安全配置

**生成安全密钥：**
```bash
# 生成 SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# 生成数据库密码
openssl rand -base64 32
```

**配置 HTTPS：**
```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your_domain.com

# 自动续期
sudo crontab -e
0 0 1 * * certbot renew --quiet
```

### 2. 数据库优化

```sql
-- PostgreSQL 配置优化
-- /etc/postgresql/15/main/postgresql.conf

shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB
```

### 3. Redis 配置

```conf
# /etc/redis/redis.conf

maxmemory 4gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
```

### 4. 系统服务配置

**创建 systemd 服务：**
```ini
# /etc/systemd/system/yolo-backend.service
[Unit]
Description=YOLO Trainer Backend
After=network.target postgresql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/yolo-trainer/backend
Environment="PATH=/opt/yolo-trainer/backend/venv/bin"
ExecStart=/opt/yolo-trainer/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/yolo-worker.service
[Unit]
Description=YOLO Trainer Worker
After=network.target redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/yolo-trainer/worker
Environment="PATH=/opt/yolo-trainer/worker/venv/bin"
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/opt/yolo-trainer/worker/venv/bin/celery -A app.tasks worker --loglevel=info --concurrency=2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable yolo-backend yolo-worker
sudo systemctl start yolo-backend yolo-worker
```

### 5. 监控配置

**Prometheus + Grafana:**
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 6. 备份策略

**数据库备份：**
```bash
#!/bin/bash
# scripts/backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgresql"

pg_dump -U postgres yolo_trainer > $BACKUP_DIR/yolo_trainer_$DATE.sql

# 保留最近 7 天的备份
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

**MinIO 备份：**
```bash
#!/bin/bash
# scripts/backup_minio.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/minio"

mc alias set local http://localhost:9000 minioadmin minioadmin
mc mirror local/yolo-trainer $BACKUP_DIR/yolo_trainer_$DATE/

# 保留最近 7 天的备份
find $BACKUP_DIR -maxdepth 1 -mtime +7 -exec rm -rf {} \;
```

**定时任务：**
```bash
crontab -e

# 每天凌晨 2 点备份数据库
0 2 * * * /opt/yolo-trainer/scripts/backup_db.sh

# 每天凌晨 3 点备份 MinIO
0 3 * * * /opt/yolo-trainer/scripts/backup_minio.sh
```

---

## 常见问题

### 1. GPU 未检测到

**问题：** 训练时提示"No GPU available"

**解决方案：**
```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 检查 CUDA
nvcc --version

# 检查 PyTorch
python -c "import torch; print(torch.cuda.is_available())"

# 如果 PyTorch 未检测到 GPU
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 2. 内存不足

**问题：** 训练时 OOM (Out of Memory)

**解决方案：**
```json
{
  "config": {
    "batch_size": 8,  // 减小批量大小
    "img_size": 416,  // 减小图片尺寸
    "amp": true,      // 启用混合精度
    "cache": "ram"    // 缓存到内存
  }
}
```

### 3. 数据库连接失败

**问题：** 无法连接到 PostgreSQL

**解决方案：**
```bash
# 检查 PostgreSQL 状态
sudo systemctl status postgresql

# 检查连接
psql -U postgres -h localhost

# 修改 pg_hba.conf 允许连接
sudo vim /etc/postgresql/15/main/pg_hba.conf
# 添加: host all all 0.0.0.0/0 md5
```

### 4. MinIO 访问失败

**问题：** 无法上传文件到 MinIO

**解决方案：**
```bash
# 检查 MinIO 状态
curl http://localhost:9000/minio/health/live

# 检查 Access Key
mc alias set local http://localhost:9000 minioadmin minioadmin
mc ls local/
```

### 5. 训练任务卡住

**问题：** 训练任务一直在 pending 状态

**解决方案：**
```bash
# 检查 Celery Worker
celery -A app.tasks status

# 检查任务队列
celery -A app.tasks inspect active

# 重启 Worker
sudo systemctl restart yolo-worker
```

---

## 性能调优

### 1. 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_trainings_status ON trainings(status);
CREATE INDEX idx_models_model_version ON models(model_version);
CREATE INDEX idx_datasets_created_at ON datasets(created_at);
```

### 2. 缓存优化

```python
# Redis 缓存配置
REDIS_CACHE_CONFIG = {
    "model_metadata": {"ttl": 3600},  # 1 小时
    "training_status": {"ttl": 60},   # 1 分钟
    "dataset_stats": {"ttl": 1800}    # 30 分钟
}
```

### 3. 并发优化

```bash
# 后端 Worker 数量
uvicorn app.main:app --workers 4

# Celery Worker 并发数
celery -A app.tasks worker --concurrency=2  # 根据 GPU 数量调整
```

---

*最后更新：2026 年 6 月*
