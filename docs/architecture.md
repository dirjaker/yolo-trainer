# YOLO Trainer 架构设计文档

> 面向 YOLO 目标检测模型训练管理平台 — 系统架构、数据流与安全设计

---

## 目录

- [1. 系统总览](#1-系统总览)
- [2. 后端分层架构](#2-后端分层架构)
- [3. 数据流设计](#3-数据流设计)
- [4. 异步任务架构](#4-异步任务架构)
- [5. 数据库设计](#5-数据库设计)
- [6. 安全设计](#6-安全设计)
- [7. 部署架构](#7-部署架构)

---

## 1. 系统总览

### 1.1 整体架构图

YOLO Trainer 采用经典的前后端分离架构，前端为 Vue 3 SPA（单页应用），后端为 FastAPI RESTful API 服务。生产环境下通过 Nginx 或 `docs-ui/server.py` 作为统一入口，将前端静态文件与 API 反向代理合二为一。

```
                              ┌────────────────────┐
                              │     浏览器 / 客户端    │
                              └─────────┬──────────┘
                                        │  HTTP / WebSocket
                                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                    反向代理层（二选一）                              │
│  ┌───────────────────────────┐   ┌─────────────────────────────┐ │
│  │  docs-ui/server.py (10001) │   │  Nginx (生产)                │ │
│  │  • /       → 前端 dist/     │   │  • /       → 前端 dist/      │ │
│  │  • /api/*  → 127.0.0.1:   │   │  • /api/*  → 127.0.0.1:    │ │
│  │            10003           │   │            10003            │ │
│  └───────────────────────────┘   └─────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                          │ /api/v1/*            │ 静态文件
                          ▼                      ▼
┌─────────────────────────────────┐   ┌──────────────────────────┐
│   FastAPI 后端 (端口 10003)       │   │  Vue 3 前端 (端口 5173 dev │
│                                  │   │  或构建为 dist/ 静态文件)   │
│  ┌────────────────────────────┐ │   │                          │
│  │ 中间件链                     │ │   │  Naive UI + Pinia        │
│  │ SecurityMiddleware → CORS  │ │   │  + Vue Router + Axios     │
│  │ → Metrics                  │ │   │  + ECharts                │
│  └────────────────────────────┘ │   └──────────────────────────┘
│  ┌────────────────────────────┐ │
│  │ API 路由层 /api/v1/         │ │
│  └────────────────────────────┘ │
│  ┌────────────────────────────┐ │
│  │ 业务服务层 services/        │ │
│  └────────────────────────────┘ │
│  ┌────────────────────────────┐ │
│  │ ORM 模型层 models/          │ │
│  └────────────────────────────┘ │
└─────────────────────────────────┘
              │                           │
    ┌─────────┴─────────┐        ┌───────┴────────┐
    ▼                   ▼        ▼                ▼
┌──────────┐   ┌──────────────┐ ┌────────┐ ┌──────────────┐
│ SQLite / │   │    Redis     │ │Celery  │ │  文件存储     │
│PostgreSQL│   │ 缓存+限流+队列 │ │Worker  │ │ /data/upload │
└──────────┘   └──────────────┘ └────────┘ └──────────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │  训练引擎 Worker  │
                                     │ YOLOv5/v8/v9/v10 │
                                     │ + Evaluator      │
                                     │ + Exporter        │
                                     └─────────────────┘
```

### 1.2 组件说明

| 组件 | 技术 | 端口 | 职责 |
|------|------|------|------|
| **前端** | Vue 3 + Naive UI + Pinia | 5173 (dev) | 用户交互界面，SPA 单页应用 |
| **docs-ui/server.py** | Python http.server | 10001 | 一体化入口：静态文件 + `/api/*` 反向代理 |
| **FastAPI 后端** | FastAPI + SQLAlchemy 2.0 | 10003 | REST API 服务、认证、业务逻辑 |
| **Redis** | Redis 6+ | 6379 | 限流计数、缓存、Celery broker/backend |
| **Celery Worker** | Celery | — | 异步任务执行：训练、导出、对比、超参搜索 |
| **Worker 训练引擎** | PyTorch + Ultralytics | — | 实际执行 YOLO 训练/评估/导出 |
| **数据库** | SQLite（开发）/ PostgreSQL（生产） | — | 持久化存储 |

### 1.3 请求代理路径

两种模式，统一 API 路由：

```
开发模式:
  浏览器 :5173  →  Vite Dev Server  →  proxy /api/* → :10003 (FastAPI)

一体化模式:
  浏览器 :10001  →  docs-ui/server.py  →  /api/* → :10003 (FastAPI)
                                      →  /*     → frontend/dist/

生产模式:
  浏览器 :80/443  →  Nginx  →  /api/* → :10003 (FastAPI)
                            →  /*     → frontend/dist/
```

---

## 2. 后端分层架构

### 2.1 分层示意

```
┌─────────────────────────────────────────────────────────────┐
│  入口层 main.py                                              │
│  • 应用创建、生命周期管理（init_db）                           │
│  • 中间件注册（SecurityMiddleware / CORS / Metrics）          │
│  • 路由挂载（/api/v1 + /health + /metrics）                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  API 路由层 app/api/v1/                                      │
│  • 11 个路由模块，仅负责参数校验、调用 Service、返回响应        │
│  • auth / training / model / dataset / test / compare        │
│  • deploy / hyperparameter / team / activity / metrics        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  业务服务层 app/services/ （部分路由直连 ORM，复杂逻辑在此）    │
│  • 训练编排、数据集处理、模型对比计算等业务逻辑                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  数据模型层 app/models/                                       │
│  • SQLAlchemy 2.0 ORM 声明式模型                              │
│  • 10 个模型：User / Training / ModelVersion / Dataset /      │
│    Team / TeamMember / Activity / HyperparameterSearch /     │
│    HyperparameterTrial / CompareResult / Deployment          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  数据访问层 app/core/database.py                              │
│  • 异步引擎（async_session）供 FastAPI 使用                    │
│  • 同步引擎（SessionLocal）供 Celery Worker 使用               │
│  • 连接池配置 + 指数退避重试                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  数据库                                                       │
│  • SQLite（开发）/ PostgreSQL（生产）                          │
│  • 通过环境变量 DATABASE_URL 切换                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心模块目录结构

```
backend/app/
├── api/v1/               # API 路由层（11 模块）
│   ├── __init__.py       # APIRouter 聚合（prefix="/api/v1"）
│   ├── auth.py           # 注册 / 登录（含 RateLimiter）
│   ├── training.py       # 训练 CRUD + 启动 / 停止 / 日志 / 指标
│   ├── model.py          # 模型版本管理 + 导出 / 标签 / 下载
│   ├── dataset.py        # 数据集上传 / 列表 / 删除
│   ├── test.py           # 单图 / 批量 YOLO 推理
│   ├── compare.py        # 多模型对比
│   ├── deploy.py         # 模型部署管理
│   ├── hyperparameter.py # 超参搜索
│   ├── team.py           # 团队管理
│   ├── activity.py       # 活动日志查询
│   └── metrics.py        # /health + /metrics (Prometheus)
│
├── core/                 # 核心基础设施
│   ├── config.py         # pydantic-settings 配置管理
│   ├── database.py       # 异步 / 同步双引擎 + 连接池
│   ├── security.py       # JWT 认证 + bcrypt 哈希
│   ├── security_middleware.py  # XSS 检测 + 安全响应头
│   ├── rate_limiter.py   # Redis 滑动窗口限流
│   ├── cache.py          # Redis 缓存 + @cached 装饰器
│   ├── celery.py         # Celery 实例配置
│   ├── logging_config.py # 结构化日志
│   └── monitoring.py     # Prometheus 指标收集
│
├── models/               # ORM 数据模型（10 个）
├── schemas/              # Pydantic 请求 / 响应模型
├── services/             # 业务逻辑层
└── tasks/                # Celery 异步任务
    ├── training_tasks.py       # 训练任务
    ├── export_tasks.py         # 模型导出任务
    ├── compare_tasks.py        # 模型对比任务
    ├── deploy_tasks.py         # 部署任务
    └── hyperparameter_tasks.py # 超参搜索任务
```

### 2.3 代码示例：典型 API 路由

```python
# backend/app/api/v1/training.py（简化示例）

from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.tasks.training_tasks import train_model_task

router = APIRouter()

@router.post("/")
async def create_training(
    payload: TrainingCreate,
    user: User = Depends(get_current_user),   # JWT 认证
    db: AsyncSession = Depends(get_db),       # 数据库会话
):
    """创建训练任务 — 路由层仅做参数校验 + 记录入库 + 派发 Celery 任务"""
    # 1. 保存训练记录
    training = Training(name=payload.name, ..., user_id=user.id)
    db.add(training)
    await db.commit()

    # 2. 提交 Celery 异步任务
    train_model_task.delay(str(training.id), payload.config)

    return training
```

---

## 3. 数据流设计

### 3.1 完整请求链路

```
用户操作（点击"开始训练"按钮）
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│  前端 Vue 3 (浏览器)                                       │
│                                                          │
│  TrainingCreate.vue                                      │
│    → trainingStore.createTraining(formData)              │
│      → api/training.js: POST /api/v1/training            │
│        → Axios 拦截器附加 Authorization: Bearer <JWT>     │
└──────────────────────────────────────────────────────────┘
        │ HTTP POST /api/v1/training
        ▼
┌──────────────────────────────────────────────────────────┐
│  反向代理层                                                │
│                                                          │
│  docs-ui/server.py (或 Nginx)                              │
│    • 匹配 /api/* → 转发到 FastAPI :10003                  │
│    • 透传所有请求头和请求体                                  │
└──────────────────────────────────────────────────────────┘
        │ 转发 POST /api/v1/training
        ▼
┌──────────────────────────────────────────────────────────┐
│  FastAPI 后端 :10003                                       │
│                                                          │
│  1. SecurityMiddleware: XSS 检测 + 安全响应头              │
│  2. CORS Middleware: 校验 Origin                          │
│  3. Metrics Middleware: 记录请求指标                       │
│  4. RateLimiter: Redis 滑动窗口检查（注册/登录路由）        │
│  5. get_current_user: 解析 JWT → 查询 User                │
│  6. API 路由处理: 参数校验 → Service → ORM                │
└──────────────────────────────────────────────────────────┘
        │
        ├─── 同步路径 ──────────────────────────
        │     路由 → Service → ORM → DB
        │     返回 JSON 响应
        │
        └─── 异步路径（训练/导出/部署等）──────
              路由 → 保存 DB 记录 → Celery.delay()
                  │
                  ▼
              Redis broker (消息队列)
                  │
                  ▼
              Celery Worker
                  │
                  ▼
              Worker 训练引擎 (PyTorch)
                  │
                  ├── 训练中：回调更新 DB 进度
                  │     前端轮询 GET /training/{id} 获取 progress
                  │
                  └── 训练完成：写 ModelVersion 记录
                         前端收到 status="completed"
```

### 3.2 实时进度推送机制

由于训练是长时间运行任务，前后端通过**轮询**实现进度感知：

```
前端（每 2-5 秒）                   后端
     │                               │
     ├── GET /api/v1/training/{id} ──→ 查询 training.progress (0.0~100.0)
     │←── { progress: 45.2, status: "running" }
     │
     ├── GET /api/v1/training/{id}/logs ──→ 读取日志文件
     │←── 训练日志文本
     │
     ├── GET /api/v1/training/{id}/metrics ──→ 查询 training.metrics (JSON)
     │←── { mAP50: 0.723, mAP50-95: 0.451, ... }
```

### 3.3 典型数据流：训练任务完整生命周期

```
阶段                Training.status         Celery Task 状态
─────────────────────────────────────────────────────────────
用户提交             pending                 未创建
路由层入库            pending                 未创建
API 返回             pending (前端跳转详情页)  未创建
Celery.delay()       queued (可选)            等待 Worker 领取
Worker 领取           running                 执行中
训练回调更新进度       running (progress 递增)  执行中
训练完成              completed               返回结果
训练失败              failed                  抛出异常
用户取消              cancelled               revoke()
```

---

## 4. 异步任务架构

### 4.1 Celery 配置

```python
# backend/app/core/celery.py

celery_app = Celery(
    "yolo_trainer",
    broker=settings.CELERY_BROKER_URL,       # redis://localhost:6379/0
    backend=settings.CELERY_RESULT_BACKEND,  # redis://localhost:6379/0
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600 * 24,               # 24h 硬超时
    task_soft_time_limit=3600 * 23,           # 23h 软超时
    worker_prefetch_multiplier=1,             # 每次只取一个任务
    worker_max_tasks_per_child=10,            # 10 个任务后重启子进程（释放内存）
)

celery_app.autodiscover_tasks(["app.tasks"])
```

### 4.2 任务类型与生命周期

| 任务 | 文件 | 触发方式 | 状态流转 |
|------|------|---------|---------|
| **训练** (train_model) | `training_tasks.py` | POST /training | pending → queued → running → completed/failed |
| **数据集处理** (process_dataset) | `training_tasks.py` | POST /datasets/upload | uploading → processing → ready/error |
| **模型导出** | `export_tasks.py` | POST /models/{id}/export | pending → running → completed/failed |
| **模型对比** | `compare_tasks.py` | POST /compare | pending → running → completed/failed |
| **超参搜索** | `hyperparameter_tasks.py` | POST /hyperparameter/search | pending → running → completed/failed |
| **模型部署** | `deploy_tasks.py` | POST /deployments | pending → deploying → running → stopped/failed |

### 4.3 训练任务内部流程

```python
# backend/app/tasks/training_tasks.py 核心流程

@shared_task(bind=True, name="tasks.train_model", max_retries=0)
def train_model_task(self, training_id: str, config: dict) -> dict:
    """完整训练生命周期：

    1. 前置准备（同步 DB 会话）:
       - 查询 Training 记录
       - 更新 status → "running"，记录 started_at
       - 解析 dataset → data.yaml 路径

    2. 构造 TrainConfig:
       - model_version, dataset_config, epochs, batch_size,
         img_size, learning_rate, device, workers, augment, ...

    3. 注册回调:
       - on_train_start: 写日志文件
       - on_epoch_end: 写日志 + 更新 training.progress（百分比）
       - on_train_end: 写日志 + 记录耗时

    4. 分派训练器:
       - _get_trainer(model_version) → YOLOv5/v8/v9/v10Trainer

    5. 执行训练:
       - trainer.train(config) → TrainResult

    6. 保存结果（同步 DB 会话）:
       - 更新 training.status / metrics / progress
       - 创建 ModelVersion 记录（关联训练结果）
       - 记录模型文件路径和文件大小
    """
```

### 4.4 Worker 训练引擎

训练引擎位于 `worker/` 目录，采用策略模式设计：

```
worker/
├── trainer/
│   ├── base.py       # BaseTrainer 抽象基类 + TrainConfig/TrainResult
│   ├── yolov5.py     # YOLOv5 训练器（v5n/s/m/l/x）
│   ├── yolov8.py     # YOLOv8 训练器（v8n/s/m/l/x）
│   ├── yolov9.py     # YOLOv9 训练器（v9c/e）
│   └── yolov10.py    # YOLOv10 训练器（v10n/s/m/b/l/x）
├── evaluator/
│   └── evaluator.py  # 模型评估器（mAP 计算）
└── exporter/
    └── exporter.py   # 模型导出器（ONNX / TensorRT / TorchScript）
```

```python
# worker/trainer/base.py 核心接口

@dataclass
class TrainConfig:
    model_version: str = "yolov8n"
    dataset_config: str = ""
    epochs: int = 100
    batch_size: int = 16
    img_size: int = 640
    learning_rate: float = 0.01
    device: str = "0"
    workers: int = 8
    resume: bool = False
    pretrained_weights: Optional[str] = None
    output_dir: str = "runs/train"
    patience: int = 50
    augment: bool = True
    extra: Dict[str, Any] = field(default_factory=dict)

class BaseTrainer(ABC):
    @abstractmethod
    def train(self, config: TrainConfig) -> TrainResult: ...
    @abstractmethod
    def validate(self, model_path: str, dataset_config: Optional[str] = None) -> ValidateResult: ...
    @abstractmethod
    def export(self, model_path: str, export_format: str = "onnx") -> ExportResult: ...
```

### 4.5 启动 Celery Worker

```bash
cd backend

# 单 Worker
celery -A app.core.celery worker --loglevel=info

# 多 Worker（按 GPU 分配）
celery -A app.core.celery worker --loglevel=info --concurrency=2

# 指定 GPU
CUDA_VISIBLE_DEVICES=0 celery -A app.core.celery worker --loglevel=info
CUDA_VISIBLE_DEVICES=1 celery -A app.core.celery worker --loglevel=info
```

---

## 5. 数据库设计

### 5.1 表结构总览

```
                         ┌──────────────────┐
                         │      users       │
                         │──────────────────│
                         │ id (UUID, PK)    │
                         │ username (UQ)    │
                         │ email (UQ)       │
                         │ hashed_password  │
                         │ is_active        │
                         │ created_at       │
                         └────────┬─────────┘
                                  │ 1
                                  │
            ┌──────────┬──────────┼──────────┬──────────┬──────────┬──────────┐
            │          │          │          │          │          │          │
            ▼ N        ▼ N        ▼ N        ▼ N        ▼ N        ▼ 1        ▼ N
   ┌────────────┐ ┌────────┐ ┌──────────┐ ┌──────┐ ┌──────────┐ ┌──────┐ ┌──────────┐
   │ trainings  │ │datasets│ │  teams   │ │dep...│ │hyper...  │ │comp..│ │activities│
   │────────────│ │────────│ │──────────│ │ments │ │searches  │ │res...│ │──────────│
   │id (PK)     │ │id (PK) │ │id (PK)   │ │(PK)  │ │id (PK)   │ │(PK)  │ │id (PK)   │
   │user_id(FK) │ │user_id │ │owner(FK) │ │u_id  │ │user_id   │ │u_id  │ │user_id   │
   │dataset(FK) │ │  ...   │ │...       │ │mod.. │ │...       │ │...   │ │action    │
   │status      │ └────────┘ └────┬─────┘ └──────┘ └────┬─────┘ └──────┘ │res_type  │
   │config(JSON)│                 │                      │               │res_id    │
   │metrics(JSON│           ┌─────┴─────┐          ┌─────┴──────┐        │details   │
   │progress    │           │team_members│         │hyperparam..│        └──────────┘
   │...         │           │────────────│         │trials      │
   └─────┬──────┘           │team_id(PK) │         │────────────│
         │ 1                │user_id(PK) │         │id (PK)     │
         │                  │role        │         │search_id   │
         ▼ N                └────────────┘         │trial_number│
   ┌──────────────┐                                │params(JSON)│
   │model_versions│                                │metrics(JSON│
   │──────────────│                                │...         │
   │id (PK)       │                                └────────────┘
   │training_id   │
   │name          │
   │version       │
   │model_version │
   │file_path     │
   │file_size     │
   │metrics(JSON) │
   │tags (JSON)   │
   └──────────────┘
```

### 5.2 核心表详细定义

#### users — 用户表

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK, default=uuid4 | 用户唯一标识 |
| `username` | VARCHAR(50) | UNIQUE, INDEX, NOT NULL | 登录用户名 |
| `email` | VARCHAR(255) | UNIQUE, INDEX, NOT NULL | 邮箱地址 |
| `hashed_password` | VARCHAR(255) | NOT NULL | bcrypt 哈希后的密码 |
| `is_active` | BOOLEAN | NOT NULL, default=True | 账户激活状态 |
| `created_at` | DATETIME(tz) | NOT NULL | 注册时间 |

**关联关系**: User 1→N Training, 1→N Dataset, 1→N HyperparameterSearch, 1→N CompareResult, 1→N Deployment, 1→N Activity, 1→N Team (owner)

#### trainings — 训练任务表

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 训练唯一标识 |
| `name` | VARCHAR(255) | INDEX, NOT NULL | 训练任务名称 |
| `model_version` | VARCHAR(50) | NOT NULL | YOLO 版本（yolov8n等） |
| `dataset_id` | UUID | FK→datasets.id, NOT NULL | 关联数据集 |
| `user_id` | UUID | FK→users.id, NOT NULL | 创建者 |
| `status` | VARCHAR(20) | INDEX, default="pending" | pending/queued/running/completed/failed/cancelled |
| `config` | JSON | nullable | 训练超参配置 |
| `metrics` | JSON | nullable | 训练结果指标 |
| `progress` | FLOAT | default=0.0 | 训练进度 0~100 |
| `started_at` | DATETIME(tz) | nullable | 训练开始时间 |
| `completed_at` | DATETIME(tz) | nullable | 训练完成时间 |
| `created_at` | DATETIME(tz) | NOT NULL | 创建时间 |
| `updated_at` | DATETIME(tz) | NOT NULL, onupdate | 更新时间 |

**关联关系**: Training N→1 User, N→1 Dataset, 1→N ModelVersion

#### model_versions — 模型版本表

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 模型版本唯一标识 |
| `training_id` | UUID | FK→trainings.id, NOT NULL | 来源训练任务 |
| `name` | VARCHAR(255) | INDEX, NOT NULL | 模型名称 |
| `version` | VARCHAR(50) | NOT NULL | 版本号（如 v1-abc12345） |
| `model_version` | VARCHAR(50) | NOT NULL | YOLO 版本（yolov8n等） |
| `file_path` | VARCHAR(512) | NOT NULL | 模型权重文件路径 |
| `file_size` | BIGINT | NOT NULL, default=0 | 文件大小（字节） |
| `metrics` | JSON | nullable | 训练指标 |
| `tags` | JSON | nullable | 标签列表 |
| `description` | TEXT | nullable | 描述 |
| `created_at` | DATETIME(tz) | NOT NULL | 创建时间 |

#### datasets — 数据集表

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 数据集唯一标识 |
| `name` | VARCHAR(255) | INDEX, NOT NULL | 数据集名称 |
| `format` | VARCHAR(20) | default="yolo" | 标注格式（yolo/coco/voc） |
| `classes` | JSON | nullable | 类别列表 |
| `stats` | JSON | nullable | 统计信息（各子集图片数） |
| `file_path` | VARCHAR(512) | NOT NULL | ZIP 文件存储路径 |
| `status` | VARCHAR(20) | INDEX | uploading/processing/ready/error |
| `user_id` | UUID | FK→users.id, NOT NULL | 上传者 |
| `created_at` | DATETIME(tz) | NOT NULL | 创建时间 |

#### teams / team_members — 团队协作

| teams | 类型 | 说明 |
|-------|------|------|
| `id` | UUID PK | 团队 ID |
| `name` | VARCHAR(100) | 团队名称 |
| `owner_id` | UUID FK→users.id | 创建者/所有者 |
| `created_at` | DATETIME(tz) | 创建时间 |

| team_members | 类型 | 说明 |
|-------------|------|------|
| `team_id` | UUID PK, FK→teams | 团队 ID（复合主键） |
| `user_id` | UUID PK, FK→users | 用户 ID（复合主键） |
| `role` | VARCHAR(20) | owner / member |
| `joined_at` | DATETIME(tz) | 加入时间 |

#### activities — 活动审计日志

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 日志唯一标识 |
| `user_id` | UUID | FK→users.id, INDEX | 操作用户 |
| `action` | VARCHAR(50) | INDEX | 操作类型（create/update/delete等） |
| `resource_type` | VARCHAR(50) | INDEX | 资源类型（training/model/dataset等） |
| `resource_id` | VARCHAR(100) | nullable | 资源 ID |
| `details` | TEXT | nullable | 操作详情 |
| `created_at` | DATETIME(tz) | INDEX | 操作时间 |

#### 其他辅助表

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| `hyperparameter_searches` | 超参搜索任务 | method, search_space, n_trials, best_metric, best_params |
| `hyperparameter_trials` | 单次超参试验 | search_id, trial_number, params, metric_value, duration |
| `compare_results` | 模型对比结果 | model_ids(JSON), test_dataset_id, results(JSON) |
| `deployments` | 模型部署记录 | model_id, platform, status, endpoint, config |

### 5.3 数据库配置切换

```python
# backend/app/core/database.py

# 异步引擎（FastAPI 使用）
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,    # 30 分钟回收连接
)

# 同步引擎（Celery Worker 使用）
# 自动将 +aiosqlite → +pysqlite，+asyncpg → +psycopg2
_sync_url = settings.DATABASE_URL.replace("+aiosqlite", "+pysqlite").replace("+asyncpg", "+psycopg2")
_sync_engine = create_engine(_sync_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(bind=_sync_engine, autocommit=False, autoflush=False)
```

环境变量切换：

```bash
# 开发环境（默认）
DATABASE_URL=sqlite+aiosqlite:///./yolo_trainer.db

# 生产环境（PostgreSQL）
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/yolo_trainer
```

---

## 6. 安全设计

### 6.1 认证流程

```
用户注册                               用户登录
────────                              ────────
POST /api/v1/auth/register           POST /api/v1/auth/login
  │                                     │
  ├── RateLimiter (5次/小时/IP)          ├── RateLimiter (10次/5分钟/IP)
  ├── 校验 username/email 唯一性          ├── 查 User by username
  ├── bcrypt.hashpw(password)           ├── bcrypt.checkpw(password, hash)
  ├── 写入 users 表                      ├── JWT 签发:
  └── 返回 UserResponse                  │   payload: { sub: user.id }
                                         │   exp: now + 24h
用户登录                                 │   algorithm: HS256
────────                                └── 返回 Token { access_token }
POST /api/v1/auth/login
  │                               ┌─────────────────────────────┐
  └── 返回 JWT Token              │  后续请求认证                  │
                                  │                             │
     前端存储                      │  Authorization: Bearer <JWT>│
     localStorage.setItem(        │         │                   │
       'token', access_token)     │         ▼                   │
                                  │  get_current_user()          │
                                  │    ├── jwt.decode(token)     │
                                  │    ├── 提取 sub → user_id    │
                                  │    ├── 查询 User             │
                                  │    └── 校验 is_active        │
                                  └─────────────────────────────┘
```

### 6.2 JWT 配置

```python
# backend/app/core/config.py

JWT_SECRET_KEY: str = "dev-secret-change-in-production"  # 生产必须覆盖
JWT_ALGORITHM: str = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1440 分钟 = 24 小时
```

**生产环境安全检查**：启动时若 `DEBUG=False` 且 `JWT_SECRET_KEY` 仍为默认值，系统拒绝启动。

```python
# backend/app/core/config.py — 启动安全校验
if _settings.JWT_SECRET_KEY == "dev-secret-change-in-production" and not _settings.DEBUG:
    raise RuntimeError("JWT_SECRET_KEY 仍为默认值，禁止在生产环境启动。")
```

### 6.3 密码安全

```python
# backend/app/core/security.py

import bcrypt

def hash_password(password: str) -> str:
    """使用 bcrypt 自动生成盐值并哈希"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否匹配哈希值"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
```

### 6.4 速率限制（Rate Limiter）

基于 Redis 滑动窗口算法实现，Redis 不可用时自动降级放行：

```python
# backend/app/core/rate_limiter.py — 核心实现

class RateLimiter:
    """滑动窗口限流器。Redis 不可用时自动降级，放行所有请求。"""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def __call__(self, request: Request):
        r = await _get_pool()
        if r is None:
            return  # Redis 不可用，降级放行

        client_key = self.key_func(request)   # 基于 X-Forwarded-For 或 client IP
        redis_key = f"rate_limit:{client_key}"
        now = time.time()
        window_start = now - self.window_seconds

        pipe = r.pipeline(transaction=True)
        pipe.zremrangebyscore(redis_key, 0, window_start)  # 移除窗口外记录
        pipe.zcard(redis_key)                                # 计数
        pipe.zadd(redis_key, {str(now): now})               # 添加当前请求
        pipe.expire(redis_key, self.window_seconds)          # 设置过期
        results = await pipe.execute()

        if results[1] >= self.max_requests:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
```

**已接入限流的路由**：

| 路由 | 限制 | 说明 |
|------|------|------|
| `POST /api/v1/auth/login` | 10次/5分钟/IP | 防暴力破解 |
| `POST /api/v1/auth/register` | 5次/1小时/IP | 防批量注册 |

### 6.5 多层防护体系

```
┌────────────────────────────────────────────────────┐
│                     防护层次                        │
├────────────────────────────────────────────────────┤
│                                                    │
│  【传输层】                                          │
│  • Nginx / HTTPS (生产)                             │
│  • HSTS 响应头                                      │
│                                                    │
│  【应用层 - 中间件】                                  │
│  • SecurityMiddleware: XSS 检测 + 安全响应头          │
│    - CSP (Content-Security-Policy)                  │
│    - X-Frame-Options: SAMEORIGIN                   │
│    - X-Content-Type-Options: nosniff               │
│  • CORS Middleware: 基于环境变量白名单                 │
│  • RateLimiter: Redis 滑动窗口限流                   │
│                                                    │
│  【应用层 - 认证授权】                                │
│  • JWT 无状态认证（get_current_user 依赖注入）       │
│  • bcrypt 密码哈希（自动盐值）                        │
│  • 资源所有权校验（_get_owned_model 等）              │
│                                                    │
│  【数据层 - 防护】                                   │
│  • SQLAlchemy ORM 参数化查询（防 SQL 注入）           │
│  • Pydantic v2 Schema 输入校验                      │
│  • 文件上传：分块写入 + zipfile 格式验证              │
│  • Zip Slip 路径穿越防护                             │
│  • 文件大小限制                                      │
│                                                    │
│  【Worker 层 - 安全】                                │
│  • 训练器路径白名单（pretrained_weights）              │
│  • 额外参数白名单（SAFE_EXTRA_KEYS）                  │
│  • 文件删除路径校验（_safe_path）                     │
│                                                    │
└────────────────────────────────────────────────────┘
```

### 6.6 CORS 配置

```bash
# 环境变量：逗号分隔的允许来源
CORS_ORIGINS=http://localhost:5173,http://localhost:10001,https://your-domain.com
```

```python
# backend/main.py
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
```

---

## 7. 部署架构

### 7.1 开发环境（单机）

```
┌──────────────────────────────────────────────────────┐
│                    开发工作站                          │
│                                                      │
│  Terminal 1:  uvicorn main:app --port 10003          │
│              FastAPI + SQLite                        │
│                                                      │
│  Terminal 2:  cd frontend && npm run dev             │
│              Vite Dev Server (:5173) + proxy /api    │
│                                                      │
│  Terminal 3:  redis-server                           │
│              Redis (:6379)                            │
│                                                      │
│  Terminal 4:  celery -A app.core.celery worker        │
│              Celery Worker                           │
│                                                      │
│  浏览器访问: http://localhost:5173                     │
│              (Vite proxy /api → :10003)               │
│                                                      │
│  或一体化启动:                                         │
│  Terminal 5:  cd docs-ui && python server.py          │
│              静态文件 + /api/* 代理 (:10001)           │
│  浏览器访问: http://localhost:10001                    │
└──────────────────────────────────────────────────────┘
```

**开发环境配置文件结构与真实文件的对应**: 无需 `.env`，所有值使用 `config.py` 中定义的默认值。

### 7.2 Docker 生产环境

```
                               ┌──────────────────────┐
                               │     Nginx (:80/443)   │
                               │  • HTTPS (Let's Encrypt)│
                               │  • 前端静态文件服务      │
                               │  • /api/* → backend    │
                               │  • /static → backend   │
                               └──────────┬───────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
        ┌───────────────────┐ ┌──────────────────┐ ┌───────────────────┐
        │ Frontend Container │ │ Backend Container │ │ Celery Worker     │
        │                    │ │                   │ │ Container (GPU)   │
        │ nginx:alpine       │ │ FastAPI (:10003)  │ │                   │
        │ (静态文件)          │ │ + Gunicorn        │ │ Celery Worker     │
        │                    │ │ + UvicornWorker   │ │ + PyTorch         │
        └───────────────────┘ └────────┬──────────┘ │ + CUDA            │
                                       │             └────────┬──────────┘
                                       │                      │
                                       ▼                      │
                              ┌──────────────────┐            │
                              │ PostgreSQL       │            │
                              │ (容器或云服务)     │            │
                              └──────────────────┘            │
                                                            │
                                       ┌──────────────────┐  │
                                       │    Redis          │◄─┘
                                       │ (:6379)           │
                                       │ 队列 + 缓存 + 限流 │
                                       └──────────────────┘
```

### 7.3 生产环境关键配置

#### 环境变量

```bash
# .env 文件（生产环境必须配置）

# 数据库（PostgreSQL 替代 SQLite）
DATABASE_URL=postgresql+asyncpg://yolo_user:STRONG_PASSWORD@postgres:5432/yolo_trainer

# Redis（Celery broker + 限流 + 缓存）
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# 安全密钥（必须重新生成！）
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# CORS
CORS_ORIGINS=https://yolo-trainer.example.com

# 数据目录
UPLOAD_DIR=/data/uploads
TRAINING_DIR=/data/training

# 关闭调试模式
DEBUG=false
```

#### Gunicorn + Uvicorn Worker

```bash
# 生产启动命令（非 Docker 场景）
gunicorn main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:10003 \
  --timeout 120 \
  --access-logfile /var/log/yolo-trainer/access.log \
  --error-logfile /var/log/yolo-trainer/error.log
```

#### Nginx 配置

```nginx
server {
    listen 443 ssl http2;
    server_name yolo-trainer.example.com;

    # SSL 证书
    ssl_certificate     /etc/letsencrypt/live/yolo-trainer.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yolo-trainer.example.com/privkey.pem;

    # 前端 SPA
    location / {
        root /var/www/yolo-trainer;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:10003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # 静态文件
    location /static/ {
        proxy_pass http://127.0.0.1:10003;
    }

    # 安全响应头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000" always;
}
```

#### systemd 服务（无 Docker 场景）

```ini
# /etc/systemd/system/yolo-trainer.service
[Unit]
Description=YOLO Trainer Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/yolo-trainer/backend
ExecStart=/opt/yolo-trainer/venv/bin/gunicorn main:app \
  --worker-class uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:10003
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/yolo-trainer-worker.service
[Unit]
Description=YOLO Trainer Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/yolo-trainer/backend
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/opt/yolo-trainer/venv/bin/celery -A app.core.celery worker --loglevel=info --concurrency=2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 7.4 端口总览

| 服务 | 开发端口 | 生产端口 | 说明 |
|------|---------|---------|------|
| Nginx / docs-ui server | 10001 | 80/443 | 统一入口 |
| FastAPI | 10003 | 10003 (内部) | API 服务 |
| Vite Dev Server | 5173 | — | 仅开发环境 |
| Redis | 6379 | 6379 (内部) | 缓存/队列/限流 |
| PostgreSQL | — | 5432 (内部) | 生产数据库 |

---

## 附录：技术栈速查

| 层级 | 技术 | 版本/说明 |
|------|------|----------|
| **前端框架** | Vue 3 | Composition API + `<script setup>` |
| **UI 组件库** | Naive UI | Vue 3 原生组件库 |
| **状态管理** | Pinia | Vue 3 官方推荐 |
| **HTTP 客户端** | Axios | JWT 拦截器 + 401 跳转 |
| **路由** | Vue Router | beforeEach 守卫 |
| **图表** | ECharts | 训练曲线可视化 |
| **构建工具** | Vite | 开发 + 构建 |
| **后端框架** | FastAPI | 异步 + 自动 OpenAPI |
| **ORM** | SQLAlchemy 2.0 | AsyncSession + Session |
| **数据校验** | Pydantic v2 | Schema 层 |
| **任务队列** | Celery | Redis broker |
| **训练引擎** | PyTorch + Ultralytics | YOLOv5/v8/v9/v10 |
| **数据库** | SQLite / PostgreSQL | 开发/生产 |
| **缓存/限流** | Redis | 滑动窗口 + 装饰器缓存 |
| **认证** | JWT (python-jose) | HS256, 24h |
| **密码** | bcrypt | 自动盐值 |
| **监控** | Prometheus | /metrics 端点 |
| **容器化** | Docker + Nginx | 生产部署 |

---

*本文档覆盖 YOLO Trainer v1.0.0 的完整架构设计。API 接口详情请参阅 [API 参考文档](api-reference.md)，部署细节请参阅 [部署指南](deployment.md)。*
