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
- [安全设计](#安全设计)
- [模型对比模块](#模型对比模块)
- [模型部署模块](#模型部署模块)
- [超参搜索模块](#超参搜索模块)
- [团队协作模块](#团队协作模块)
- [监控模块](#监控模块)

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
- API 路由 / 服务层 / 数据模型三层分离
- 便于单元测试和维护

### 2. 可扩展性
- 策略模式支持多版本 YOLO 训练器
- 插件化设计，易于添加新功能
- 水平扩展：支持多 Celery Worker 并行训练

### 3. 高可用性
- 异步任务队列隔离训练与 API 服务
- 数据库连接池与重试机制
- 数据持久化存储

### 4. 安全性
- JWT 无状态认证
- bcrypt 密码哈希
- CSP 安全头、CORS 白名单
- 安全中间件（路径穿越检测、SQL 注入检测）

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户层 (User Layer)                      │
│           浏览器 / 移动端 / API 客户端 / CLI 工具              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    前端 (Frontend)                            │
│          Vue 3 + Naive UI + Pinia + Vue Router               │
│       ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│       │  页面组件 │  │ 状态管理 │  │ API 封装  │              │
│       └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP / REST
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  后端 API (FastAPI)                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  中间件: SecurityMiddleware + CORS + Metrics         │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  API 路由 (v1): auth / training / model / dataset   │    │
│  │              : test / compare / deploy / hyperparam  │    │
│  │              : team / activity / metrics              │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Services │  │ Schemas  │  │  Models   │  │  Tasks   │   │
│  │ 业务逻辑  │  │ 数据校验 │  │ ORM 模型  │  │ Celery   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                    │                    │
                    ▼                    ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│    SQLite / PostgreSQL   │  │     Redis (可选)          │
│      数据持久化           │  │   缓存 / 任务队列         │
└──────────────────────────┘  └──────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    训练引擎 (Worker)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ YOLOv5   │  │ YOLOv8   │  │ YOLOv9   │  │ YOLOv10  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  Evaluator   │  │   Exporter   │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 前端架构

### 技术选型

| 技术 | 说明 |
|------|------|
| Vue 3 | 渐进式框架，Composition API + `<script setup>` |
| Naive UI | Vue 3 组件库 |
| Pinia | 状态管理 |
| Vue Router | 路由管理（带 JWT 守卫） |
| Axios | HTTP 客户端（封装在 `api/request.js`） |

### 目录结构

```
frontend/src/
├── api/                    # API 接口封装
│   ├── request.js          # Axios 实例（基础 URL、Token 拦截器）
│   ├── auth.js             # 认证 API
│   ├── training.js         # 训练 API
│   ├── model.js            # 模型 API
│   ├── dataset.js          # 数据集 API
│   ├── test.js             # 测试 API
│   ├── compare.js          # 对比 API
│   ├── deploy.js           # 部署 API
│   ├── hyperparameter.js   # 超参搜索 API
│   ├── team.js             # 团队 API
│   └── activity.js         # 活动日志 API
│
├── views/                  # 页面组件
│   ├── Dashboard/          # 仪表盘
│   ├── Training/           # 训练管理（TrainingCreate / TrainingList / TrainingDetail）
│   ├── Model/              # 模型管理（ModelList / ModelDetail）
│   ├── Dataset/            # 数据集管理（DatasetList）
│   ├── Test/               # 测试中心
│   ├── Compare/            # 模型对比
│   ├── Deploy/             # 部署管理
│   ├── Hyperparameter/     # 超参搜索
│   ├── Team/               # 团队管理
│   ├── Activity/           # 活动日志
│   └── LoginView.vue       # 登录页
│
├── stores/                 # Pinia 状态
│   ├── user.js             # 用户状态（Token 管理）
│   ├── training.js         # 训练状态
│   ├── model.js            # 模型状态
│   └── dataset.js          # 数据集状态
│
├── router/
│   └── index.js            # 路由配置（15 个路由）
│
└── utils/
    └── format.js           # 格式化工具函数
```

### 路由设计

| 路径 | 组件 | 说明 |
|------|------|------|
| `/login` | LoginView | 登录页（公开） |
| `/` | DashboardView | 仪表盘 |
| `/training` | TrainingList | 训练列表 |
| `/training/create` | TrainingCreate | 创建训练 |
| `/training/:id` | TrainingDetail | 训练详情 |
| `/models` | ModelList | 模型列表 |
| `/models/:id` | ModelDetail | 模型详情 |
| `/datasets` | DatasetList | 数据集列表 |
| `/test` | TestView | 测试中心 |
| `/compare` | CompareView | 模型对比 |
| `/deploy` | DeployView | 部署管理 |
| `/hyperparameter` | SearchView | 超参搜索 |
| `/team` | TeamView | 团队管理 |
| `/activity` | ActivityView | 活动日志 |

### 认证流程

```
用户登录 → API 返回 JWT Token → localStorage 存储
                                    ↓
每次请求 → Axios 拦截器自动附加 Authorization: Bearer <token>
                                    ↓
Token 过期 → 401 响应 → 跳转到 /login
```

---

## 后端架构

### 技术选型

| 技术 | 说明 |
|------|------|
| FastAPI | 高性能异步框架，自动 OpenAPI 文档 |
| SQLAlchemy 2.0 | 异步 ORM（AsyncSession） |
| Pydantic v2 | 数据验证与序列化 |
| Celery | 分布式任务队列（训练、导出、超参搜索） |
| python-jose | JWT 令牌处理 |
| bcrypt/passlib | 密码哈希 |

### API 路由结构

```
/api/v1/
├── /auth/
│   ├── POST /register     # 用户注册
│   └── POST /login        # 用户登录
├── /training/
│   ├── POST /             # 创建训练任务
│   ├── GET /              # 训练列表（分页、筛选）
│   ├── GET /{id}          # 训练详情
│   ├── POST /{id}/stop    # 停止训练
│   ├── GET /{id}/logs     # 训练日志
│   └── GET /{id}/metrics  # 训练指标
├── /models/
│   ├── GET /              # 模型列表
│   ├── GET /{id}          # 模型详情
│   ├── POST /{id}/export  # 导出模型
│   ├── POST /{id}/tags    # 添加标签
│   ├── GET /{id}/versions # 版本历史
│   ├── GET /{id}/download # 下载模型
│   └── DELETE /{id}       # 删除模型
├── /datasets/
│   ├── POST /upload       # 上传数据集
│   ├── GET /              # 数据集列表
│   ├── GET /{id}          # 数据集详情
│   └── DELETE /{id}       # 删除数据集
├── /test/
│   ├── POST /predict      # 单图推理
│   ├── POST /batch        # 批量推理
│   ├── GET /{id}/results  # 测试结果
│   └── GET /{id}/result-image  # 结果图片
├── /compare/
│   ├── POST /             # 创建对比任务
│   ├── GET /{id}          # 对比结果
│   └── GET /              # 对比列表
├── /deployments/
│   ├── POST /             # 创建部署
│   ├── GET /              # 部署列表
│   ├── GET /{id}          # 部署详情
│   ├── GET /{id}/status   # 部署状态
│   └── POST /{id}/stop    # 停止部署
├── /hyperparameter/
│   ├── POST /search       # 创建搜索任务
│   ├── GET /search        # 搜索列表
│   ├── GET /search/{id}   # 搜索详情
│   ├── GET /search/{id}/trials  # 试验列表
│   └── POST /search/{id}/cancel # 取消搜索
├── /teams/
│   ├── POST /teams        # 创建团队
│   ├── GET /teams         # 团队列表
│   ├── GET /teams/{id}    # 团队详情
│   ├── PATCH /teams/{id}  # 更新团队
│   ├── POST /teams/{id}/members  # 添加成员
│   └── DELETE /teams/{id}/members/{uid}  # 移除成员
├── /activities/
│   └── GET /activities    # 活动日志列表
└── (独立路由)
    ├── GET /health        # 健康检查
    └── GET /metrics       # Prometheus 指标
```

### 数据模型

```
┌──────────┐     ┌──────────────┐     ┌───────────────┐
│  User    │──┬──│   Training   │────│ Dataset       │
│          │  │  │              │     │               │
│ id       │  │  │ id           │     │ id            │
│ username │  │  │ name         │     │ name          │
│ email    │  │  │ model_version│     │ format        │
│ password │  │  │ dataset_id   │     │ classes       │
│ is_active│  │  │ status       │     │ stats         │
└──────────┘  │  │ config       │     │ file_path     │
              │  │ metrics      │     │ status        │
              │  │ progress     │     └───────────────┘
              │  │ user_id      │
              │  └──────────────┘
              │         │
              │         ▼
              │  ┌───────────────┐     ┌───────────────┐
              │  │ ModelVersion  │────│  Deployment   │
              │  │               │     │               │
              │  │ id            │     │ id            │
              │  │ training_id   │     │ model_id      │
              │  │ name          │     │ name          │
              │  │ version       │     │ status        │
              │  │ model_version │     │ platform      │
              │  │ file_path     │     │ endpoint      │
              │  │ metrics       │     │ config        │
              │  │ tags          │     └───────────────┘
              │  └───────────────┘
              │
              ├──┌───────────────┐     ┌───────────────┐
              │  │  Team         │────│ TeamMember    │
              │  │               │     │               │
              │  │ id            │     │ team_id       │
              │  │ name          │     │ user_id       │
              │  │ owner_id      │     │ role          │
              │  └───────────────┘     └───────────────┘
              │
              └──┌───────────────┐
                 │  Activity     │
                 │               │
                 │ id            │
                 │ user_id       │
                 │ action        │
                 │ resource_type │
                 │ resource_id   │
                 │ details       │
                 └───────────────┘

┌────────────────────┐     ┌─────────────────────┐
│ HyperparameterSearch│────│ HyperparameterTrial │
│                     │     │                     │
│ id                  │     │ id                  │
│ name                │     │ search_id           │
│ model_version       │     │ trial_number        │
│ method              │     │ params              │
│ search_space        │     │ metric_value        │
│ n_trials            │     │ metrics             │
│ best_metric         │     │ duration            │
│ best_params         │     └─────────────────────┘
└────────────────────┘

┌───────────────────┐
│ CompareResult     │
│                   │
│ id                │
│ name              │
│ model_ids         │
│ test_dataset_id   │
│ results           │
└───────────────────┘
```

---

## 训练引擎

### 多版本支持

训练引擎采用策略模式，通过 `BaseTrainer` 抽象基类统一接口：

```python
class BaseTrainer(ABC):
    @abstractmethod
    def train(self, config: TrainConfig) -> TrainResult: ...

    @abstractmethod
    def validate(self, model_path: str, dataset_config: Optional[str] = None) -> ValidateResult: ...

    @abstractmethod
    def export(self, model_path: str, export_format: str = "onnx") -> ExportResult: ...
```

| 训练器 | 文件 | 支持的模型 |
|--------|------|-----------|
| YOLOv5Trainer | `worker/trainer/yolov5.py` | yolov5n/s/m/l/x |
| YOLOv8Trainer | `worker/trainer/yolov8.py` | yolov8n/s/m/l/x |
| YOLOv9Trainer | `worker/trainer/yolov9.py` | yolov9c/e |
| YOLOv10Trainer | `worker/trainer/yolov10.py` | yolov10n/s/m/b/l/x |

### 训练配置

```python
@dataclass
class TrainConfig:
    model_version: str = "yolov8n"
    dataset_config: str = ""
    epochs: int = 100
    batch_size: int = 16
    img_size: int = 640
    learning_rate: float = 0.01
    device: str = "0"          # GPU id 或 "cpu"
    workers: int = 8
    resume: bool = False
    pretrained_weights: Optional[str] = None
    output_dir: str = "runs/train"
    patience: int = 50
    augment: bool = True
    extra: Dict[str, Any] = {}  # 额外参数
```

### 任务调度流程

```
前端创建训练 → API 保存记录 → Celery 异步提交
                                    ↓
                            Worker 接收任务
                                    ↓
                    获取对应训练器 → 执行训练
                                    ↓
                    训练完成 → 保存模型 → 更新状态
```

---

## 数据存储

### 开发环境（SQLite）

开发环境使用 SQLite，数据库文件位于 `backend/yolo_trainer.db`，无需额外配置。

### 生产环境（PostgreSQL）

生产环境推荐切换为 PostgreSQL，通过环境变量配置：

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/yolo_trainer
```

### 连接池配置

```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,  # 30 分钟回收
)
```

### 文件存储

| 类型 | 目录 | 说明 |
|------|------|------|
| 数据集 | `/data/uploads/datasets/{user_id}/{dataset_id}.zip` | ZIP 压缩包 |
| 模型权重 | 由训练器 `output_dir` 决定 | `.pt` 文件 |
| 导出模型 | 与权重同级 `exports/` 目录 | ONNX/TensorRT 等 |

---

## 安全设计

### 认证机制

- **JWT Token**: 无状态认证，有效期 24 小时
- **密码哈希**: bcrypt 算法
- **路由守卫**: 前端 `router.beforeEach` + 后端 `get_current_user` 依赖

### 安全中间件

```python
# SecurityMiddleware 提供：
# - CSP 安全头 (Content-Security-Policy)
# - 路径穿越检测
# - SQL 注入模式检测（辅助，主要依赖 ORM）
```

### CORS 配置

通过环境变量 `CORS_ORIGINS` 控制允许的跨域来源，默认仅允许 localhost。

### 限流

`RateLimiter` 基于 Redis 滑动窗口实现，可按端点配置：

```python
# 限流器已实现，待在路由上激活
@router.post("/login", dependencies=[Depends(get_rate_limiter(times=5, seconds=60))])
```

---

## 模型对比模块

### 工作流程

1. 用户选择 2-6 个模型和测试数据集
2. 创建对比任务，状态为 `pending`
3. Celery Worker 异步执行对比：
   - 加载所有模型
   - 在测试数据集上推理
   - 计算各维度指标
4. 结果保存到 `compare_results` 表

### 对比指标

| 指标 | 说明 |
|------|------|
| mAP50 | IoU=0.5 时的平均精度 |
| mAP50-95 | IoU=0.5:0.95 的平均精度 |
| Precision | 精确率 |
| Recall | 召回率 |
| F1 Score | 调和平均 |
| FPS | 推理帧率 |
| 模型大小 | 文件体积 |

---

## 模型部署模块

### 支持平台

| 平台 | 说明 |
|------|------|
| ONNX Runtime | 通用推理引擎 |
| TensorRT | NVIDIA GPU 加速 |
| TorchServe | PyTorch 官方服务 |

### 部署配置

```json
{
  "platform": "onnx_runtime",
  "port": 8080,
  "workers": 4,
  "batch_size": 1,
  "gpu": true
}
```

### 状态流转

```
pending → deploying → running → stopped
                   ↘ failed
```

---

## 超参搜索模块

### 搜索算法

| 算法 | 说明 |
|------|------|
| 随机搜索 | 随机采样参数组合 |
| 贝叶斯优化 | 基于历史结果智能推荐 |
| 网格搜索 | 遍历所有参数组合 |

### 搜索空间类型

| 类型 | 说明 |
|------|------|
| `uniform` | 均匀采样 |
| `log_uniform` | 对数均匀采样 |
| `int_uniform` | 整数均匀采样 |
| `choice` | 离散选择 |

### 数据模型

每个搜索任务包含多个试验（Trial），每个试验记录使用的参数和得到的指标。搜索完成后自动标记最优试验。

---

## 团队协作模块

### 角色权限

| 角色 | 权限 |
|------|------|
| owner | 创建/更新/删除团队、添加/移除成员 |
| member | 查看团队信息 |

### 数据结构

- `teams` 表：团队基本信息
- `team_members` 表：团队成员关系（复合主键：team_id + user_id）

---

## 监控模块

### API 指标

通过 HTTP 中间件自动收集：

```python
metrics.record_api_request(
    method=request.method,
    path=request.url.path,
    status_code=response.status_code,
    duration=duration,
)
```

### 端点

| 端点 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `GET /metrics` | Prometheus 格式指标 |

---

*更多部署细节请参考 [部署指南](deployment.md)，API 接口请参考 [API 文档](api-reference.md)。*
