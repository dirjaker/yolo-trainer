# 开发指南

> YOLO Trainer 开发环境搭建、代码规范与贡献指南

---

## 📋 目录

- [环境要求](#环境要求)
- [开发环境搭建](#开发环境搭建)
- [项目架构概览](#项目架构概览)
- [后端开发](#后端开发)
- [前端开发](#前端开发)
- [训练引擎开发](#训练引擎开发)
- [数据库迁移](#数据库迁移)
- [测试](#测试)
- [代码规范](#代码规范)
- [Git 工作流](#git-工作流)
- [常见开发任务](#常见开发任务)

---

## 环境要求

| 工具 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.10+ | 推荐 3.12 |
| Node.js | 18+ | 前端构建 |
| Conda | 最新 | Python 环境管理（可选） |
| Git | 2.30+ | 版本控制 |
| NVIDIA Driver | 525+ | GPU 训练（可选） |
| CUDA | 11.8+ | GPU 训练（可选） |

---

## 开发环境搭建

### 1. 克隆项目

```bash
git clone https://github.com/dirjaker/yolo-trainer.git
cd yolo-trainer
git checkout dev  # 开发分支
```

### 2. 后端环境

```bash
# 创建 Python 虚拟环境
conda create -n yolo-trainer python=3.12 -y
conda activate yolo-trainer

# 安装后端依赖
pip install -r requirements.txt

# 创建 .env 配置文件（可选，有默认值）
cat > backend/.env << 'EOF'
DATABASE_URL=sqlite+aiosqlite:///./yolo_trainer.db
JWT_SECRET_KEY=your-dev-secret-key
SECRET_KEY=your-dev-secret-key
DEBUG=true
EOF
```

### 3. 前端环境

```bash
cd frontend
npm install
```

### 4. 启动开发服务

```bash
# 终端 1：启动后端
cd backend
python main.py
# API 服务运行在 http://localhost:8000
# Swagger 文档: http://localhost:8000/docs

# 终端 2：启动前端
cd frontend
npm run dev
# 前端运行在 http://localhost:5173
```

### 5. 可选：启动 Celery Worker（训练功能）

```bash
# 需要先启动 Redis
redis-server

# 启动 Celery Worker
celery -A app.core.celery worker --loglevel=info
```

---

## 项目架构概览

```
yolo-trainer/
├── backend/                     # FastAPI 后端
│   ├── main.py                  # 应用入口
│   ├── app/
│   │   ├── api/                 # API 路由层
│   │   │   ├── v1/              # API v1 端点
│   │   │   │   ├── auth.py      # 认证（注册/登录）
│   │   │   │   ├── training.py  # 训练管理
│   │   │   │   ├── model.py     # 模型管理
│   │   │   │   ├── dataset.py   # 数据集管理
│   │   │   │   ├── test.py      # 测试中心
│   │   │   │   ├── compare.py   # 模型对比
│   │   │   │   ├── deploy.py    # 模型部署
│   │   │   │   ├── hyperparameter.py # 超参搜索
│   │   │   │   ├── team.py      # 团队管理
│   │   │   │   ├── activity.py  # 活动日志
│   │   │   │   └── metrics.py   # 监控指标
│   │   │   └── deps.py          # 通用依赖注入
│   │   ├── core/                # 核心模块
│   │   │   ├── config.py        # 应用配置（Pydantic Settings）
│   │   │   ├── database.py      # 数据库连接与会话管理
│   │   │   ├── security.py      # JWT 令牌与密码哈希
│   │   │   ├── security_middleware.py  # 安全中间件（CSP、路径检测）
│   │   │   ├── rate_limiter.py  # Redis 滑动窗口限流器
│   │   │   ├── cache.py         # 缓存封装
│   │   │   ├── monitoring.py    # API 请求指标收集
│   │   │   ├── logging_config.py # 日志配置
│   │   │   └── celery.py        # Celery 配置
│   │   ├── models/              # SQLAlchemy ORM 模型
│   │   │   ├── user.py          # 用户
│   │   │   ├── training.py      # 训练任务
│   │   │   ├── model.py         # 模型版本
│   │   │   ├── dataset.py       # 数据集
│   │   │   ├── deployment.py    # 部署记录
│   │   │   ├── compare.py       # 对比结果
│   │   │   ├── hyperparameter.py # 超参搜索与试验
│   │   │   ├── team.py          # 团队与成员
│   │   │   └── activity.py      # 活动日志
│   │   ├── schemas/             # Pydantic 请求/响应 Schema
│   │   ├── services/            # 业务逻辑服务层
│   │   └── tasks/               # Celery 异步任务
│
├── frontend/                    # Vue 3 前端
│   └── src/
│       ├── api/                 # HTTP 请求封装
│       │   ├── request.js       # Axios 实例与拦截器
│       │   ├── auth.js          # 认证 API
│       │   ├── training.js      # 训练 API
│       │   ├── model.js         # 模型 API
│       │   ├── dataset.js       # 数据集 API
│       │   ├── test.js          # 测试 API
│       │   ├── compare.js       # 对比 API
│       │   ├── deploy.js        # 部署 API
│       │   ├── hyperparameter.js # 超参 API
│       │   ├── team.js          # 团队 API
│       │   └── activity.js      # 活动日志 API
│       ├── views/               # 页面组件
│       │   ├── Dashboard/       # 仪表盘
│       │   ├── Training/        # 训练管理（创建/列表/详情）
│       │   ├── Model/           # 模型管理（列表/详情）
│       │   ├── Dataset/         # 数据集管理
│       │   ├── Test/            # 测试中心
│       │   ├── Compare/         # 模型对比
│       │   ├── Deploy/          # 部署管理
│       │   ├── Hyperparameter/  # 超参搜索
│       │   ├── Team/            # 团队管理
│       │   ├── Activity/        # 活动日志
│       │   └── LoginView.vue    # 登录页
│       ├── stores/              # Pinia 状态管理
│       ├── router/              # Vue Router 配置
│       ├── utils/               # 工具函数
│       ├── App.vue              # 根组件
│       └── main.js              # 应用入口
│
├── worker/                      # 训练引擎
│   ├── trainer/                 # YOLO 训练器
│   │   ├── base.py              # 抽象基类 (BaseTrainer)
│   │   ├── yolov5.py            # YOLOv5 实现
│   │   ├── yolov8.py            # YOLOv8 实现
│   │   ├── yolov9.py            # YOLOv9 实现
│   │   └── yolov10.py           # YOLOv10 实现
│   ├── evaluator/               # 模型评估器
│   └── exporter/                # 模型导出器
│
└── docs/                        # 项目文档
```

---

## 后端开发

### 添加新的 API 端点

1. **定义 Schema**（`backend/app/schemas/`）:

```python
# backend/app/schemas/example.py
from pydantic import BaseModel
from typing import Optional
import uuid

class ExampleCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ExampleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True
```

2. **定义数据模型**（`backend/app/models/`）:

```python
# backend/app/models/example.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Example(Base):
    __tablename__ = "examples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
```

3. **创建路由**（`backend/app/api/v1/`）:

```python
# backend/app/api/v1/example.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.example import ExampleCreate, ExampleResponse

router = APIRouter()

@router.post("/", response_model=ExampleResponse, status_code=status.HTTP_201_CREATED)
async def create_example(
    data: ExampleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建示例资源。"""
    # 实现逻辑...
    pass
```

4. **注册路由**（`backend/app/api/v1/__init__.py`）:

```python
from app.api.v1.example import router as example_router
api_router.include_router(example_router, prefix="/examples", tags=["示例"])
```

### 配置说明

应用配置通过 `backend/app/core/config.py` 中的 `Settings` 类管理，支持环境变量和 `.env` 文件：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `APP_NAME` | YOLO Trainer | 应用名称 |
| `APP_VERSION` | 1.0.0 | 应用版本 |
| `DEBUG` | False | 调试模式 |
| `DATABASE_URL` | sqlite+aiosqlite:///./yolo_trainer.db | 数据库连接串 |
| `REDIS_URL` | redis://localhost:6379/0 | Redis 连接 |
| `JWT_SECRET_KEY` | (默认值) | JWT 签名密钥 |
| `JWT_ALGORITHM` | HS256 | JWT 算法 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 1440 | Token 有效期（分钟） |
| `UPLOAD_DIR` | /data/uploads | 文件上传目录 |

---

## 前端开发

### 添加新页面

1. 在 `frontend/src/views/` 下创建页面组件:

```vue
<!-- frontend/src/views/Example/ExampleView.vue -->
<template>
  <n-card title="示例页面">
    <n-data-table :columns="columns" :data="data" />
  </n-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { NCard, NDataTable } from 'naive-ui'

const data = ref([])
const columns = [
  { title: '名称', key: 'name' },
  { title: '描述', key: 'description' },
]

onMounted(async () => {
  // 加载数据
})
</script>
```

2. 注册路由（`frontend/src/router/index.js`）:

```javascript
{ path: '/example', name: 'Example', component: () => import('../views/Example/ExampleView.vue') },
```

3. 封装 API（`frontend/src/api/example.js`）:

```javascript
import request from './request'

export function getExamples(params) {
  return request.get('/api/v1/examples', { params })
}

export function createExample(data) {
  return request.post('/api/v1/examples', data)
}
```

### 技术栈说明

- **Vue 3**: 使用 Composition API (`<script setup>`)
- **Naive UI**: 组件库，按需导入
- **Pinia**: 状态管理（`frontend/src/stores/`）
- **Vue Router**: 路由管理，带 JWT 守卫
- **Axios**: HTTP 客户端，封装在 `frontend/src/api/request.js`

---

## 训练引擎开发

### 添加新的 YOLO 版本

1. 在 `worker/trainer/` 下创建训练器:

```python
# worker/trainer/yolovXX.py
from worker.trainer.base import BaseTrainer, TrainConfig, TrainResult, ValidateResult, ExportResult

class YOLOvXXTrainer(BaseTrainer):
    """YOLOvXX 训练器"""

    _MODEL_MAP = {
        "yolovxxn": "yolovxxn.pt",
        "yolovxxs": "yolovxxs.pt",
        "yolovxxm": "yolovxxm.pt",
    }

    def train(self, config: TrainConfig) -> TrainResult:
        from ultralytics import YOLO
        model = self._resolve_model(config)
        results = model.train(
            data=config.dataset_config,
            epochs=config.epochs,
            batch=config.batch_size,
            imgsz=config.img_size,
            device=config.device,
            workers=config.workers,
            patience=config.patience,
        )
        return TrainResult(
            success=True,
            model_path=str(results.save_dir / "weights" / "best.pt"),
            metrics=results.results_dict,
        )

    def validate(self, model_path: str, dataset_config=None) -> ValidateResult:
        # 实现验证逻辑
        pass

    def export(self, model_path: str, export_format="onnx") -> ExportResult:
        # 实现导出逻辑
        pass
```

### 训练器接口

所有训练器必须继承 `BaseTrainer` 并实现以下方法：

| 方法 | 说明 | 返回 |
|------|------|------|
| `train(config)` | 执行训练 | `TrainResult` |
| `validate(model_path)` | 验证模型 | `ValidateResult` |
| `export(model_path, format)` | 导出模型 | `ExportResult` |

### 回调机制

通过 `TrainCallback` 类监听训练事件：

```python
class TrainCallback:
    def on_train_start(self, config: TrainConfig) -> None: ...
    def on_epoch_end(self, epoch: int, metrics: dict) -> None: ...
    def on_train_end(self, result: TrainResult) -> None: ...
```

---

## 数据库迁移

### 使用 Alembic

```bash
# 初始化迁移（首次）
cd backend
alembic init alembic

# 生成迁移脚本
alembic revision --autogenerate -m "描述信息"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看当前版本
alembic current

# 查看历史
alembic history
```

### SQLite 开发模式

开发环境默认使用 SQLite，数据库文件位于 `backend/yolo_trainer.db`。首次启动时会自动创建表结构（通过 `init_db()`）。

---

## 测试

### 运行后端测试

```bash
cd backend
pytest tests/ -v
pytest tests/ -v --cov=app  # 带覆盖率
```

### 运行前端测试

```bash
cd frontend
npm run test
```

### 手动测试 API

```bash
# 注册用户
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

# 登录获取 Token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'

# 使用 Token 调用 API
curl http://localhost:8000/api/v1/training/ \
  -H "Authorization: Bearer <your-token>"
```

---

## 代码规范

### Python（后端）

- 遵循 PEP 8
- 使用 `ruff` 进行 lint 检查
- 类型注解：所有公共函数必须有类型注解
- Docstring：所有 API 端点和公共方法必须有中文 Docstring
- 异步优先：数据库操作使用 `AsyncSession`

```bash
# 代码格式化
ruff format backend/

# Lint 检查
ruff check backend/
```

### JavaScript（前端）

- 使用 ESLint + Prettier
- 组件使用 `<script setup>` 语法
- API 调用统一通过 `frontend/src/api/` 封装

```bash
cd frontend
npm run lint
npm run format
```

### 提交规范

提交信息格式：

```
<type>(<scope>): <description>

[可选正文]

[可选脚注]
```

| type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具变更 |

示例：
```
feat(training): 支持 YOLOv10 训练
fix(auth): 修复 JWT Token 过期后未正确返回 401 的问题
docs: 更新 API 参考文档
```

---

## Git 工作流

### 分支策略

| 分支 | 说明 |
|------|------|
| `main` | 稳定发布版本 |
| `dev` | 开发主分支 |
| `feat/*` | 功能分支 |
| `fix/*` | 修复分支 |

### 开发流程

```bash
# 1. 从 dev 创建功能分支
git checkout dev
git pull
git checkout -b feat/my-feature

# 2. 开发并提交
git add .
git commit -m "feat(module): 描述"

# 3. 推送并创建 PR
git push origin feat/my-feature
```

---

## 常见开发任务

### 添加新的数据模型字段

1. 修改 `backend/app/models/` 中的 ORM 模型
2. 更新 `backend/app/schemas/` 中的 Pydantic Schema
3. 如需迁移：`alembic revision --autogenerate -m "添加xxx字段"`
4. 执行迁移：`alembic upgrade head`

### 修改 API 响应格式

1. 更新 `backend/app/schemas/` 中的 Response Schema
2. 更新 `backend/app/api/v1/` 中的路由端点
3. 更新 `frontend/src/api/` 中的前端调用

### 调整训练参数

1. 修改 `worker/trainer/base.py` 中的 `TrainConfig` dataclass
2. 更新 `backend/app/schemas/training.py` 中的 Schema
3. 更新 `frontend/src/views/Training/TrainingCreate.vue` 中的表单

---

*更多开发细节请参考 [架构设计文档](architecture.md) 和 [API 参考文档](api-reference.md)。*
