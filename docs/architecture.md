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
- [模型对比模块](#模型对比模块)
- [模型部署模块](#模型部署模块)
- [超参搜索模块](#超参搜索模块)
- [团队协作模块](#团队协作模块)
- [安全与监控模块](#安全与监控模块)

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

## 模型对比模块

### 模块架构

```
┌─────────────────────────────────────────────────────────┐
│                   模型对比模块                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────┐                │
│  │  Compare API  │─────▶│CompareService│                │
│  │  (REST)       │      │  对比服务     │                │
│  └──────────────┘      └──────┬───────┘                │
│                               │                         │
│               ┌───────────────┼───────────────┐         │
│               ▼               ▼               ▼         │
│      ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │
│      │ 评估引擎      │ │ 模型服务      │ │ 可视化服务  │  │
│      │ 指标计算      │ │ 元数据查询    │ │ 图表生成    │  │
│      └──────────────┘ └──────────────┘ └────────────┘  │
│               │               │               │         │
│               ▼               ▼               ▼         │
│      ┌──────────────────────────────────────────────┐   │
│      │              CompareResult 数据模型            │   │
│      │  model_id | mAP | Precision | Recall | F1    │   │
│      │  inference_speed | model_size | export_formats│   │
│      └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 组件说明

| 组件 | 说明 |
|------|------|
| **CompareService** | 对比服务核心，负责协调多个模型的评估和指标汇总 |
| **CompareResult** | 对比结果数据模型，存储各模型的性能指标 |
| **评估引擎** | 运行各模型推理，计算对比指标 |
| **可视化服务** | 生成对比图表（雷达图、柱状图、表格） |

### 对比指标

| 指标 | 说明 | 单位 |
|------|------|------|
| mAP@0.5 | IoU=0.5 时的平均精度 | % |
| mAP@0.5:0.95 | IoU 0.5-0.95 的平均精度 | % |
| Precision | 精确率 | % |
| Recall | 召回率 | % |
| F1 Score | F1 分数 | % |
| Inference Speed | 推理速度（单张图片） | ms |
| Model Size | 模型文件大小 | MB |

### 数据模型

```python
# app/models/compare.py
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class ModelMetrics(BaseModel):
    model_id: UUID
    model_name: str
    map_50: float
    map_50_95: float
    precision: float
    recall: float
    f1_score: float
    inference_speed_ms: float
    model_size_mb: float

class CompareResult(BaseModel):
    compare_id: UUID
    models: List[ModelMetrics]
    dataset_id: UUID
    created_at: datetime
    summary: Optional[str] = None  # AI 生成的对比总结
```

### 数据流

```
用户选择模型 → CompareService.compare()
    → 并行加载模型权重
    → 在指定数据集上运行推理
    → 计算各项指标
    → 生成 CompareResult
    → 可视化服务渲染对比图表
    → 返回对比报告给用户
```

---

## 模型部署模块

### 模块架构

```
┌─────────────────────────────────────────────────────────┐
│                   模型部署模块                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────┐                │
│  │  Deploy API   │─────▶│DeployService │                │
│  │  (REST)       │      │  部署服务     │                │
│  └──────────────┘      └──────┬───────┘                │
│                               │                         │
│               ┌───────────────┼───────────────┐         │
│               ▼               ▼               ▼         │
│      ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │
│      │ ONNX Runtime │ │  TensorRT    │ │ TorchServe │  │
│      │  推理服务     │ │  推理服务     │ │  推理服务   │  │
│      └──────────────┘ └──────────────┘ └────────────┘  │
│               │               │               │         │
│               ▼               ▼               ▼         │
│      ┌──────────────────────────────────────────────┐   │
│      │              Deployment 数据模型               │   │
│      │  deploy_id | model_id | platform | endpoint  │   │
│      │  status | config | health_check_url          │   │
│      └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 组件说明

| 组件 | 说明 |
|------|------|
| **DeployService** | 部署服务核心，管理模型导出、打包和部署全流程 |
| **Deployment** | 部署实例数据模型，记录部署配置和状态 |
| **ONNX Runtime** | 跨平台高性能推理引擎，适合 CPU/GPU 通用部署 |
| **TensorRT** | NVIDIA GPU 优化推理引擎，极致推理性能 |
| **TorchServe** | PyTorch 官方模型服务框架，支持动态批处理 |

### 支持平台

| 平台 | 适用场景 | 导出格式 | 硬件要求 |
|------|---------|---------|---------|
| ONNX Runtime | 通用部署、边缘设备 | .onnx | CPU / GPU |
| TensorRT | 高性能 GPU 推理 | .engine | NVIDIA GPU |
| TorchServe | 云端大规模部署 | .mar | CPU / GPU |

### 数据模型

```python
# app/models/deployment.py
from pydantic import BaseModel
from uuid import UUID
from enum import Enum
from typing import Dict, Optional

class DeployPlatform(str, Enum):
    ONNX_RUNTIME = "onnx_runtime"
    TENSORRT = "tensorrt"
    TORCHSERVE = "torchserve"

class DeploymentStatus(str, Enum):
    PENDING = "pending"
    EXPORTING = "exporting"
    DEPLOYING = "deploying"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"

class Deployment(BaseModel):
    deploy_id: UUID
    model_id: UUID
    platform: DeployPlatform
    status: DeploymentStatus
    endpoint_url: Optional[str] = None
    health_check_url: Optional[str] = None
    config: Dict  # 平台特定配置（batch_size, precision 等）
    created_at: datetime
    updated_at: datetime
```

### 数据流

```
用户选择模型和目标平台 → DeployService.deploy()
    → 模型格式转换（PyTorch → ONNX/TensorRT/TorchServe）
    → 打包部署产物
    → 部署到目标推理服务
    → 健康检查确认服务就绪
    → 更新 Deployment 状态为 running
    → 返回 endpoint_url 给用户
```

---

## 超参搜索模块

### 模块架构

```
┌─────────────────────────────────────────────────────────┐
│                   超参搜索模块                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌───────────────────────┐       │
│  │ Hyperparam   │─────▶│HyperparameterService  │       │
│  │ API (REST)   │      │  超参搜索服务          │       │
│  └──────────────┘      └──────────┬────────────┘       │
│                                   │                     │
│               ┌───────────────────┼───────────────────┐ │
│               ▼                   ▼                   ▼ │
│      ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│      │ 贝叶斯优化    │  │  随机搜索     │  │  网格搜索 │ │
│      │ (Optuna)     │  │  Random       │  │  Grid     │ │
│      └──────┬───────┘  └──────┬───────┘  └─────┬─────┘ │
│             │                 │                 │       │
│             └────────┬────────┘─────────────────┘       │
│                      ▼                                  │
│             ┌──────────────────┐                        │
│             │  TrainingEngine  │ ← 复用训练引擎          │
│             │  执行训练任务     │                        │
│             └────────┬─────────┘                        │
│                      ▼                                  │
│             ┌──────────────────┐                        │
│             │  最优参数结果     │                        │
│             │  BestTrial       │                        │
│             └──────────────────┘                        │
└─────────────────────────────────────────────────────────┘
```

### 组件说明

| 组件 | 说明 |
|------|------|
| **HyperparameterService** | 超参搜索服务核心，管理搜索空间定义、算法选择和结果分析 |
| **Optuna (贝叶斯优化)** | 基于贝叶斯优化的高效搜索，自动剪枝低效试验 |
| **随机搜索** | 随机采样参数组合，适合快速探索 |
| **网格搜索** | 穷举所有参数组合，适合小范围精细搜索 |
| **TrainingEngine** | 复用现有训练引擎执行每次试验 |

### 支持算法对比

| 算法 | 优势 | 劣势 | 适用场景 |
|------|------|------|---------|
| 贝叶斯优化 (Optuna) | 高效收敛、自动剪枝 | 需要更多初始试验 | 默认推荐，大搜索空间 |
| 随机搜索 | 简单快速、并行友好 | 不保证收敛 | 快速探索、基线对比 |
| 网格搜索 | 穷举无遗漏 | 计算代价高 | 小范围精细调优 |

### 搜索空间示例

```python
# app/schemas/hyperparameter.py
from pydantic import BaseModel
from typing import Dict, List, Any

class SearchSpace(BaseModel):
    """搜索空间定义"""
    learning_rate: Dict = {"type": "log_uniform", "low": 1e-5, "high": 1e-1}
    batch_size: Dict = {"type": "categorical", "choices": [8, 16, 32, 64]}
    epochs: Dict = {"type": "int_uniform", "low": 50, "high": 300}
    img_size: Dict = {"type": "categorical", "choices": [416, 512, 640, 800]}
    optimizer: Dict = {"type": "categorical", "choices": ["SGD", "Adam", "AdamW"]}
    augmentations: Dict = {"type": "categorical", "choices": [
        "default", "strong", "light", "custom"
    ]}

class SearchConfig(BaseModel):
    algorithm: str = "optuna"  # optuna | random | grid
    n_trials: int = 50
    search_space: SearchSpace
    objective_metric: str = "mAP50"  # 优化目标
    direction: str = "maximize"  # maximize | minimize
```

### 数据流

```
用户定义搜索空间和算法 → HyperparameterService.start_search()
    → 创建 Study / Search 任务
    → 调度器按算法生成参数组合
    → 每组参数提交到 TrainingEngine 执行训练
    → 收集训练结果（loss, mAP 等）
    → 算法更新内部模型（贝叶斯优化）
    → 重复直到达到 n_trials 或 early_stop
    → 输出最优参数组合和对应指标
    → 用户可一键使用最优参数创建正式训练
```

---

## 团队协作模块

### 模块架构

```
┌─────────────────────────────────────────────────────────┐
│                   团队协作模块                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────┐                │
│  │  Team API     │─────▶│ TeamService  │                │
│  │  (REST)       │      │  团队服务     │                │
│  └──────────────┘      └──────┬───────┘                │
│                               │                         │
│         ┌─────────────────────┼───────────────────┐     │
│         ▼                     ▼                   ▼     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Team        │  │  TeamMember  │  │ ActivityLog  │  │
│  │  团队数据     │  │  成员数据     │  │  活动日志     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                  │          │
│         ▼                 ▼                  ▼          │
│  ┌──────────────────────────────────────────────────┐   │
│  │                PostgreSQL                         │   │
│  │  teams | team_members | activity_logs            │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────┐      ┌──────────────────┐            │
│  │ Activity API  │─────▶│ActivityService   │            │
│  │  (REST)       │      │  活动日志服务     │            │
│  └──────────────┘      └──────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

### 组件说明

| 组件 | 说明 |
|------|------|
| **TeamService** | 团队服务核心，管理团队创建、成员邀请和权限管理 |
| **Team** | 团队数据模型，包含团队名称、描述、所有者等 |
| **TeamMember** | 团队成员数据模型，关联用户和团队，定义角色权限 |
| **ActivityService** | 活动日志服务，记录团队内所有操作和变更历史 |

### 数据模型

```python
# app/models/team.py
from pydantic import BaseModel
from uuid import UUID
from enum import Enum
from typing import List, Optional

class TeamRole(str, Enum):
    OWNER = "owner"       # 所有者，完全控制
    ADMIN = "admin"       # 管理员，管理成员和资源
    MEMBER = "member"     # 成员，使用资源
    VIEWER = "viewer"     # 查看者，只读访问

class Team(BaseModel):
    team_id: UUID
    name: str
    description: Optional[str] = None
    owner_id: UUID
    avatar_url: Optional[str] = None
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

class TeamMember(BaseModel):
    member_id: UUID
    team_id: UUID
    user_id: UUID
    role: TeamRole
    joined_at: datetime
    invited_by: Optional[UUID] = None

class ActivityLog(BaseModel):
    log_id: UUID
    team_id: UUID
    user_id: UUID
    action: str       # e.g., "model.created", "training.started"
    resource_type: str  # e.g., "model", "training", "dataset"
    resource_id: UUID
    details: Optional[Dict] = None
    created_at: datetime
```

### 权限矩阵

| 操作 | Owner | Admin | Member | Viewer |
|------|:-----:|:-----:|:------:|:------:|
| 管理团队设置 | ✅ | ✅ | ❌ | ❌ |
| 邀请/移除成员 | ✅ | ✅ | ❌ | ❌ |
| 创建训练任务 | ✅ | ✅ | ✅ | ❌ |
| 上传数据集 | ✅ | ✅ | ✅ | ❌ |
| 查看资源 | ✅ | ✅ | ✅ | ✅ |
| 删除团队 | ✅ | ❌ | ❌ | ❌ |

### 数据流

```
团队创建 → TeamService.create_team()
    → 创建 Team 记录（owner=创建者）
    → 自动添加 TeamMember（role=owner）

成员邀请 → TeamService.invite_member()
    → 生成邀请链接/发送通知
    → 用户接受 → 添加 TeamMember

活动记录 → 任何资源操作触发 ActivityService.log()
    → 记录操作人、动作、资源信息
    → 团队动态页面实时展示
```

---

## 安全与监控模块

### 模块架构

```
┌─────────────────────────────────────────────────────────────────┐
│                       安全与监控模块                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─── 请求入口 ───────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │  │
│  │  │ RateLimiter  │──▶│  Security    │──▶│   Metrics    │   │  │
│  │  │  限流器       │   │  Middleware  │   │  Collector   │   │  │
│  │  │              │   │  安全中间件   │   │  监控收集器   │   │  │
│  │  └──────────────┘   └──────────────┘   └──────────────┘   │  │
│  │         │                  │                   │           │  │
│  │         ▼                  ▼                   ▼           │  │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │  │
│  │  │    Redis     │   │   Redis      │   │  Prometheus  │   │  │
│  │  │   计数器      │   │   黑名单      │   │  指标存储     │   │  │
│  │  └──────────────┘   └──────────────┘   └──────────────┘   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── 缓存层 ────────────────────────────────────────────────┐  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │                   RedisCache                         │ │  │
│  │  │  会话缓存 │ 热点数据缓存 │ 限流计数器 │ 分布式锁     │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─── 日志层 ────────────────────────────────────────────────┐  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │              Structured Logger                        │ │  │
│  │  │  JSON 格式 │ 请求追踪 │ 操作审计 │ 错误告警          │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 组件说明

| 组件 | 说明 |
|------|------|
| **RedisCache** | 基于 Redis 的分布式缓存，提供会话管理、热点数据缓存和分布式锁 |
| **RateLimiter** | 基于滑动窗口的 API 限流器，支持按用户/IP/接口维度限流 |
| **SecurityMiddleware** | 安全中间件，处理 CORS、CSRF 防护、请求签名验证和 IP 黑名单 |
| **MetricsCollector** | Prometheus 指标收集器，收集请求量、延迟、错误率等系统指标 |
| **Structured Logger** | 结构化日志，JSON 格式输出，支持请求链路追踪和操作审计 |

### RedisCache 缓存策略

```python
# app/core/cache.py
import redis.asyncio as redis
from typing import Optional, Any
import json

class RedisCache:
    """分布式缓存服务"""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存，带过期时间"""
        await self.redis.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str):
        """删除缓存"""
        await self.redis.delete(key)

    async def get_or_set(self, key: str, factory, ttl: int = 3600):
        """缓存穿透保护：不存在时调用 factory 生成"""
        value = await self.get(key)
        if value is None:
            value = await factory()
            await self.set(key, value, ttl)
        return value

    async def acquire_lock(self, key: str, timeout: int = 10) -> bool:
        """分布式锁"""
        return await self.redis.set(f"lock:{key}", "1", ex=timeout, nx=True)
```

### RateLimiter 限流策略

```python
# app/core/rate_limiter.py
import redis.asyncio as redis
from fastapi import Request, HTTPException
from typing import Optional

class RateLimiter:
    """滑动窗口限流器"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int  # 秒
    ) -> bool:
        """检查请求是否允许"""
        now = int(time.time())
        pipeline = self.redis.pipeline()
        pipeline.zremrangebyscore(key, 0, now - window)
        pipeline.zadd(key, {str(now): now})
        pipeline.zcard(key)
        pipeline.expire(key, window)
        results = await pipeline.execute()
        return results[2] <= limit

    def limit(self, limit: int = 60, window: int = 60):
        """FastAPI 依赖注入装饰器"""
        async def _check(request: Request):
            key = f"rate:{request.client.host}:{request.url.path}"
            if not await self.is_allowed(key, limit, window):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )
        return _check
```

### MetricsCollector 监控指标

| 指标类型 | 指标名 | 说明 |
---------|--------|------|
| Counter | `http_requests_total` | HTTP 请求总数 |
| Histogram | `http_request_duration_seconds` | 请求延迟分布 |
| Gauge | `active_training_tasks` | 当前活跃训练任务数 |
| Gauge | `gpu_utilization` | GPU 使用率 |
| Counter | `model_deployments_total` | 模型部署总数 |
| Histogram | `model_inference_duration_seconds` | 推理延迟分布 |

### 结构化日志

```python
# app/core/logger.py
import structlog
import logging

def setup_logging():
    """配置结构化日志"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.INFO
        ),
    )

# 使用示例
# logger = structlog.get_logger()
# logger.info("training_started", training_id="xxx", model="yolov8")
# 输出: {"event": "training_started", "training_id": "xxx", "model": "yolov8", "level": "info", "timestamp": "2026-06-12T10:00:00Z"}
```

### 请求处理流水线

```
客户端请求
    │
    ▼
RateLimiter（检查限流）
    │ 超限 → 429 Too Many Requests
    ▼
SecurityMiddleware（安全检查）
    │ IP 黑名单 / CSRF / CORS
    │ 不合法 → 403 Forbidden
    ▼
MetricsCollector（记录请求指标）
    │
    ▼
业务处理（路由 → Service → DB）
    │
    ▼
RedisCache（缓存结果，可选）
    │
    ▼
Structured Logger（记录操作日志）
    │
    ▼
MetricsCollector（记录响应指标）
    │
    ▼
返回响应给客户端
```

---

*最后更新：2026 年 6 月*
