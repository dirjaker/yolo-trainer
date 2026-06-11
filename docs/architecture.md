# 架构设计文档

> YOLO Trainer 系统架构详细设计

---

## 📋 目录

- [系统概述](#系统概述)
- [架构设计原则](#架构设计原则)
- [整体架构](#整体架构)
- [前端架构](#前端架构)
- [后端架构](#后端架构)
- [训练引擎](#训练引擎)
- [数据存储](#数据存储)
- [部署架构](#部署架构)
- [安全设计](#安全设计)

---

## 系统概述

YOLO Trainer 是一个面向目标检测模型训练的 Web 平台，核心目标是：
- 简化 YOLO 模型训练流程
- 提供完整的模型版本控制
- 支持在线模型测试和评估
- 实现团队协作和知识共享

---

## 架构设计原则

### 1. 模块化设计
- 各组件职责单一，松耦合
- 支持独立扩展和升级
- 便于单元测试和维护

### 2. 可扩展性
- 水平扩展：支持多 Worker 并行训练
- 垂直扩展：支持更大模型和数据集
- 功能扩展：插件化设计，易于添加新功能

### 3. 高可用性
- 服务无状态设计
- 数据持久化和备份
- 故障自动恢复

### 4. 安全性
- 用户认证和授权
- 数据加密传输和存储
- 资源访问控制

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          用户层 (User Layer)                        │
│    浏览器  │  移动端  │  API 客户端  │  CLI 工具                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        接入层 (Access Layer)                        │
│    Nginx 反向代理  │  负载均衡  │  SSL 终止  │  静态资源服务           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       应用层 (Application Layer)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   前端服务   │  │   后端 API  │  │  WebSocket  │                 │
│  │  (Vue 3)    │  │  (FastAPI)  │  │   服务      │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       服务层 (Service Layer)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ 训练服务 │  │ 模型服务 │  │ 数据服务 │  │ 测试服务 │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ 用户服务 │  │ 任务服务 │  │ 通知服务 │  │ 日志服务 │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       引擎层 (Engine Layer)                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    训练引擎 (Training Engine)                 │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐            │  │
│  │  │ YOLOv5 │  │ YOLOv8 │  │ YOLOv9 │  │ YOLOv10│  ...       │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    评估引擎 (Evaluation Engine)               │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐                        │  │
│  │  │  mAP   │  │  FPS   │  │  IoU   │  ...                   │  │
│  │  └────────┘  └────────┘  └────────┘                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    导出引擎 (Export Engine)                   │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐            │  │
│  │  │  ONNX  │  │TensorRT│  │ CoreML │  │  TFLite│  ...       │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       数据层 (Data Layer)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  PostgreSQL  │  │    Redis     │  │    MinIO     │             │
│  │   元数据     │  │   任务队列   │  │   文件存储   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       基础设施层 (Infrastructure Layer)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │    Docker    │  │   NVIDIA     │  │   K8s/Docker │             │
│  │   容器化     │  │   GPU 驱动   │  │   编排       │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 前端架构

### 技术选型

| 技术 | 说明 |
|------|------|
| Vue 3 | 渐进式框架，Composition API |
| Naive UI | Vue 3 组件库，TypeScript 友好 |
| Pinia | 状态管理，替代 Vuex |
| Vue Router | 路由管理 |
| Axios | HTTP 客户端 |
| ECharts | 图表可视化 |

### 目录结构

```
frontend/
├── src/
│   ├── api/                    # API 接口
│   │   ├── training.ts         # 训练相关
│   │   ├── model.ts            # 模型相关
│   │   ├── dataset.ts          # 数据集相关
│   │   └── test.ts             # 测试相关
│   │
│   ├── views/                  # 页面组件
│   │   ├── Training/           # 训练管理
│   │   │   ├── Create.vue      # 创建训练
│   │   │   ├── List.vue        # 训练列表
│   │   │   └── Detail.vue      # 训练详情
│   │   ├── Model/              # 模型管理
│   │   │   ├── List.vue        # 模型列表
│   │   │   ├── Detail.vue      # 模型详情
│   │   │   └── Compare.vue     # 模型对比
│   │   ├── Dataset/            # 数据集管理
│   │   ├── Test/               # 测试中心
│   │   └── Dashboard/          # 仪表盘
│   │
│   ├── components/             # 通用组件
│   │   ├── charts/             # 图表组件
│   │   ├── forms/              # 表单组件
│   │   └── layout/             # 布局组件
│   │
│   ├── stores/                 # Pinia 状态
│   │   ├── training.ts
│   │   ├── model.ts
│   │   └── user.ts
│   │
│   └── utils/                  # 工具函数
│       ├── request.ts          # Axios 封装
│       └── format.ts           # 格式化工具
│
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### 状态管理

```typescript
// stores/training.ts
export const useTrainingStore = defineStore('training', () => {
  const trainings = ref<Training[]>([])
  const currentTraining = ref<Training | null>(null)
  
  async function fetchTrainings() {
    const response = await api.getTrainings()
    trainings.value = response.data
  }
  
  async function createTraining(data: CreateTrainingDTO) {
    const response = await api.createTraining(data)
    trainings.value.push(response.data)
    return response.data
  }
  
  return { trainings, currentTraining, fetchTrainings, createTraining }
})
```

---

## 后端架构

### 技术选型

| 技术 | 说明 |
|------|------|
| FastAPI | 高性能异步框架 |
| SQLAlchemy | ORM，异步支持 |
| Alembic | 数据库迁移 |
| Celery | 分布式任务队列 |
| Pydantic | 数据验证 |

### 目录结构

```
backend/
├── app/
│   ├── api/                    # API 路由
│   │   ├── v1/                 # API v1
│   │   │   ├── training.py     # 训练接口
│   │   │   ├── model.py        # 模型接口
│   │   │   ├── dataset.py      # 数据集接口
│   │   │   └── test.py         # 测试接口
│   │   └── deps.py             # 依赖注入
│   │
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 配置管理
│   │   ├── security.py         # 安全相关
│   │   └── celery.py           # Celery 配置
│   │
│   ├── models/                 # SQLAlchemy 模型
│   │   ├── training.py
│   │   ├── model.py
│   │   ├── dataset.py
│   │   └── user.py
│   │
│   ├── schemas/                # Pydantic 模型
│   │   ├── training.py
│   │   ├── model.py
│   │   └── dataset.py
│   │
│   ├── services/               # 业务逻辑
│   │   ├── training_service.py
│   │   ├── model_service.py
│   │   └── dataset_service.py
│   │
│   ├── tasks/                  # Celery 任务
│   │   ├── training_tasks.py
│   │   └── evaluation_tasks.py
│   │
│   └── main.py                 # FastAPI 入口
│
├── alembic/                    # 数据库迁移
├── requirements.txt
└── alembic.ini
```

### API 设计规范

```python
# app/api/v1/training.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.training import TrainingCreate, TrainingResponse
from app.services.training_service import TrainingService

router = APIRouter(prefix="/trainings", tags=["trainings"])

@router.post("/", response_model=TrainingResponse)
async def create_training(
    data: TrainingCreate,
    service: TrainingService = Depends()
):
    """创建训练任务"""
    return await service.create(data)

@router.get("/{training_id}", response_model=TrainingResponse)
async def get_training(
    training_id: str,
    service: TrainingService = Depends()
):
    """获取训练详情"""
    training = await service.get(training_id)
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    return training
```

---

## 训练引擎

### 多版本支持

```python
# worker/trainer/base.py
from abc import ABC, abstractmethod

class BaseTrainer(ABC):
    """训练器基类"""
    
    @abstractmethod
    def train(self, config: TrainConfig) -> TrainResult:
        """执行训练"""
        pass
    
    @abstractmethod
    def validate(self, model_path: str) -> ValidateResult:
        """验证模型"""
        pass
    
    @abstractmethod
    def export(self, model_path: str, format: str) -> str:
        """导出模型"""
        pass

# worker/trainer/yolov8.py
from ultralytics import YOLO

class YOLOv8Trainer(BaseTrainer):
    """YOLOv8 训练器"""
    
    def train(self, config: TrainConfig) -> TrainResult:
        model = YOLO(config.model_path)
        results = model.train(
            data=config.data_config,
            epochs=config.epochs,
            batch=config.batch_size,
            imgsz=config.img_size,
            device=config.device
        )
        return TrainResult(
            model_path=results.save_dir / 'weights' / 'best.pt',
            metrics=results.results_dict
        )
```

### 训练任务调度

```python
# worker/tasks/training_tasks.py
from celery import shared_task
from worker.trainer import get_trainer

@shared_task(bind=True)
def train_model(self, training_id: str, config: dict):
    """训练模型任务"""
    trainer = get_trainer(config['model_version'])
    
    try:
        # 更新任务状态
        update_training_status(training_id, 'running')
        
        # 执行训练
        result = trainer.train(TrainConfig(**config))
        
        # 保存模型
        model_id = save_model(training_id, result)
        
        # 更新任务状态
        update_training_status(training_id, 'completed', model_id)
        
        return {'status': 'success', 'model_id': model_id}
        
    except Exception as e:
        update_training_status(training_id, 'failed', str(e))
        raise
```

---

## 数据存储

### 存储架构

```
┌─────────────────────────────────────────────────────────────┐
│                     MinIO 对象存储                           │
├─────────────────────────────────────────────────────────────┤
│  /datasets/           # 数据集                              │
│    ├── {dataset_id}/                                        │
│    │   ├── images/     # 图片                               │
│    │   ├── labels/     # 标注                               │
│    │   └── dataset.yaml                                     │
│                                                             │
│  /models/             # 模型文件                            │
│    ├── {model_id}/                                          │
│    │   ├── weights/    # 权重文件                           │
│    │   ├── config/     # 配置文件                           │
│    │   └── exports/    # 导出模型                           │
│                                                             │
│  /results/            # 测试结果                            │
│    ├── {test_id}/                                           │
│    │   ├── images/     # 结果图片                           │
│    │   └── metrics/    # 指标文件                           │
└─────────────────────────────────────────────────────────────┘
```

### 数据库设计

```sql
-- 训练任务表
CREATE TABLE trainings (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    dataset_id UUID REFERENCES datasets(id),
    status VARCHAR(20) DEFAULT 'pending',
    config JSONB,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 模型版本表
CREATE TABLE models (
    id UUID PRIMARY KEY,
    training_id UUID REFERENCES trainings(id),
    version VARCHAR(50) NOT NULL,
    name VARCHAR(255),
    description TEXT,
    file_path VARCHAR(500),
    metrics JSONB,
    tags VARCHAR[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- 数据集表
CREATE TABLE datasets (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    format VARCHAR(20) NOT NULL,
    classes JSONB,
    stats JSONB,
    file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 部署架构

### Docker Compose 部署

```yaml
# docker/docker-compose.yml
version: '3.8'

services:
  # 前端
  frontend:
    build:
      context: ../frontend
      dockerfile: ../docker/Dockerfile.frontend
    ports:
      - "5173:80"
    depends_on:
      - backend

  # 后端 API
  backend:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/yolo_trainer
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
    depends_on:
      - db
      - redis
      - minio

  # GPU Worker
  worker:
    build:
      context: ../worker
      dockerfile: ../docker/Dockerfile.worker
    environment:
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    depends_on:
      - redis

  # 数据库
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=yolo_trainer
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis
  redis:
    image: redis:7-alpine

  # MinIO
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

### 生产环境部署

```
                    ┌─────────────────┐
                    │   Nginx/LB      │
                    │   (SSL 终止)    │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   Frontend   │  │   Backend    │  │   Worker     │
    │   (多实例)   │  │   (多实例)   │  │   (GPU)      │
    └──────────────┘  └──────────────┘  └──────────────┘
                             │                │
                             ▼                ▼
                    ┌──────────────┐  ┌──────────────┐
                    │   DB 集群    │  │   Redis 集群  │
                    └──────────────┘  └──────────────┘
```

---

## 安全设计

### 认证授权

```python
# app/core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### 资源访问控制

```python
# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return payload
```

---

## 性能优化

### 1. 数据库优化
- 使用连接池
- 添加适当索引
- 查询优化和缓存

### 2. 缓存策略
- Redis 缓存热点数据
- 模型元数据缓存
- 训练状态缓存

### 3. 文件传输
- 分片上传大文件
- 断点续传支持
- CDN 加速静态资源

### 4. 并发处理
- 异步 I/O
- 任务队列削峰
- 连接池复用

---

*最后更新：2026 年 6 月*
