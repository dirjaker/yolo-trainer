# 开发指南

> YOLO Trainer 开发环境搭建、代码规范与贡献流程

---

## 📋 目录

- [环境要求](#环境要求)
- [项目克隆与分支管理](#项目克隆与分支管理)
- [后端开发环境搭建](#后端开发环境搭建)
- [前端开发环境搭建](#前端开发环境搭建)
- [启动开发服务](#启动开发服务)
- [项目架构概览](#项目架构概览)
- [开发数据库（SQLite）](#开发数据库sqlite)
- [代码风格与架构约定](#代码风格与架构约定)
- [Git 工作流与贡献流程](#git-工作流与贡献流程)
- [常见开发任务](#常见开发任务)
- [调试技巧](#调试技巧)

---

## 环境要求

| 工具 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.10+ / 推荐 3.12 | 后端运行环境 |
| Node.js | 18+ | 前端构建与开发 |
| Conda / Miniconda | 最新 | Python 环境管理（推荐） |
| Git | 2.30+ | 版本控制 |
| npm | 9+ | 前端包管理 |
| Redis | 6.0+ | Celery 任务队列（训练功能需要，可选） |
| NVIDIA Driver | 525+ | GPU 训练（可选） |
| CUDA | 11.8+ | GPU 训练（可选） |

---

## 项目克隆与分支管理

### 克隆项目

```bash
git clone https://github.com/dirjaker/yolo-trainer.git
cd yolo-trainer
```

### 分支策略

| 分支 | 说明 |
|------|------|
| `main` | 稳定发布版本，只接受来自 `dev` 的合并 |
| `dev` | 开发主分支，所有功能分支从此拉出 |
| `feat/*` | 功能分支（如 `feat/yolov11-support`） |
| `fix/*` | 修复分支（如 `fix/auth-token-expiry`） |

### 切换到开发分支

```bash
git checkout dev
git pull origin dev
```

> **所有开发工作都在 `dev` 分支上进行。** 不要直接在 `main` 上开发。

---

## 后端开发环境搭建

### 1. 创建 Conda 虚拟环境

```bash
conda create -n yolo-trainer python=3.12 -y
conda activate yolo-trainer
```

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

`backend/requirements.txt` 包含：

| 依赖 | 用途 |
|------|------|
| `fastapi` | Web 框架 |
| `uvicorn[standard]` | ASGI 服务器 |
| `sqlalchemy[asyncio]` | 异步 ORM |
| `asyncpg` | PostgreSQL 异步驱动 |
| `alembic` | 数据库迁移 |
| `pydantic[email]` | 数据校验 |
| `pydantic-settings` | 配置管理 |
| `python-jose[cryptography]` | JWT 处理 |
| `passlib[bcrypt]` | 密码哈希 |
| `python-multipart` | 文件上传 |
| `celery[redis]` | 异步任务队列 |
| `redis` | Redis 客户端 |
| `minio` | 对象存储客户端 |
| `httpx` | HTTP 客户端 |
| `Pillow` | 图像处理 |
| `pyyaml` | YAML 解析 |

### 3. 配置文件

项目通过 `pydantic-settings` 加载配置，优先级：**环境变量 > `.env` 文件 > 代码默认值**。

```bash
# 从模板创建 .env（可选，默认值可直接运行）
cp .env.example .env
```

开发环境最小配置：

```ini
# .env
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./yolo_trainer.db
JWT_SECRET_KEY=dev-secret-key-for-local
SECRET_KEY=dev-secret-key-for-local
```

> **开发环境默认使用 SQLite**，无需安装 PostgreSQL。详见[开发数据库](#开发数据库sqlite)章节。

---

## 前端开发环境搭建

### 1. 安装 Node.js 依赖

```bash
cd frontend
npm install
```

### 2. 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.4 | 渐进式框架（Composition API + `<script setup>`） |
| Vite | ^5.4 | 构建工具与开发服务器 |
| Vue Router | ^4.3 | 路由管理 |
| Pinia | ^2.1 | 状态管理 |
| Naive UI | ^2.38 | Vue 3 组件库 |
| Axios | ^1.7 | HTTP 客户端 |
| ECharts | ^5.5 | 数据可视化 |

### 3. Vite 开发代理

`frontend/vite.config.js` 已配置 API 代理：

```javascript
// Vite 开发服务器将 /api 请求代理到后端
proxy: {
  '/api': {
    target: 'http://localhost:10003',
    changeOrigin: true,
  },
}
```

---

## 启动开发服务

需要同时运行后端和前端两个进程：

### 终端 1：启动后端 API

```bash
cd backend
conda activate yolo-trainer

# 开发模式（DEBUG=true，日志更详细）
DEBUG=true uvicorn main:app --host 127.0.0.1 --port 10003 --reload
```

启动后可访问：
- Swagger UI：http://localhost:10003/docs
- ReDoc：http://localhost:10003/redoc
- 健康检查：http://localhost:10003/health

`--reload` 选项在代码修改时自动重启服务器。

### 终端 2：启动前端开发服务器

```bash
cd frontend
npm run dev
```

Vite 开发服务器运行在 http://localhost:5173，API 请求自动代理到 `:10003`。

### 终端 3（可选）：启动 Celery Worker

训练、导出、评估等功能需要 Celery Worker：

```bash
# 先启动 Redis
redis-server

# 启动 Worker
cd backend
celery -A app.core.celery worker --loglevel=info --concurrency=1 -Q training,export,evaluate
```

### 种子数据

```bash
cd backend && python seed_examples.py
```

默认测试账号：`demo3` / `demo123`

---

## 项目架构概览

```
yolo-trainer/
├── backend/                     # FastAPI 后端
│   ├── main.py                  # 应用入口（FastAPI 实例创建、中间件、路由注册）
│   ├── requirements.txt         # Python 依赖
│   ├── seed_examples.py         # 种子数据脚本
│   └── app/
│       ├── api/v1/              # API 路由层
│       │   ├── auth.py          #   认证（注册/登录/JWT）
│       │   ├── training.py      #   训练管理
│       │   ├── model.py         #   模型管理
│       │   ├── dataset.py       #   数据集管理
│       │   ├── test.py          #   测试中心
│       │   ├── compare.py       #   模型对比
│       │   ├── deploy.py        #   模型部署
│       │   ├── hyperparameter.py #  超参搜索
│       │   ├── team.py          #   团队管理
│       │   ├── activity.py      #   活动日志
│       │   └── metrics.py       #   监控指标/健康检查
│       ├── core/                # 核心基础设施
│       │   ├── config.py        #   配置管理（pydantic-settings）
│       │   ├── database.py      #   数据库引擎（async + sync）
│       │   ├── security.py      #   JWT 认证与密码哈希
│       │   ├── security_middleware.py  # 安全中间件
│       │   ├── rate_limiter.py  #   速率限制
│       │   ├── cache.py         #   缓存封装
│       │   ├── monitoring.py    #   请求指标收集
│       │   ├── logging_config.py #  日志配置
│       │   └── celery.py        #   Celery 配置
│       ├── models/              # SQLAlchemy ORM 数据模型
│       ├── schemas/             # Pydantic 请求/响应 Schema
│       ├── services/            # 业务逻辑层
│       └── tasks/               # Celery 异步任务
│
├── frontend/                    # Vue 3 前端
│   ├── package.json             # 前端依赖与脚本
│   ├── vite.config.js           # Vite 配置
│   └── src/
│       ├── main.js              # 应用入口
│       ├── App.vue              # 根组件
│       ├── api/                 # HTTP 请求封装
│       │   └── request.js       #   Axios 实例（Token 拦截器）
│       ├── views/               # 页面组件（10 个模块）
│       ├── stores/              # Pinia 状态管理
│       ├── router/              # Vue Router 路由配置
│       └── utils/               # 工具函数
│
├── worker/                      # 训练引擎
│   ├── trainer/                 # YOLO 训练器（v5/v8/v9/v10）
│   │   ├── base.py              #   抽象基类（BaseTrainer）
│   │   ├── yolov5.py
│   │   ├── yolov8.py
│   │   ├── yolov9.py
│   │   └── yolov10.py
│   ├── evaluator/               # 模型评估器
│   └── exporter/                # 模型导出器
│
├── docs-ui/                     # 一体化前端服务器
│   └── server.py                # HTTP 静态服务 + /api/ 反向代理
│
├── docker/                      # Docker 部署配置
├── scripts/                     # 运维脚本
└── docs/                        # 项目文档
```

### 后端分层架构

```
API 路由 (api/v1/)
    ↓ 调用
服务层 (services/)
    ↓ 操作
数据模型 (models/)  ←  数据校验 (schemas/)
    ↓
数据库 (SQLite / PostgreSQL)
```

- **路由层** (`api/v1/`)：只做参数解析、调用服务、返回响应，不写业务逻辑
- **服务层** (`services/`)：包含所有业务逻辑，可被路由和 Celery 任务复用
- **数据模型** (`models/`)：SQLAlchemy ORM 模型定义
- **Schema** (`schemas/`)：Pydantic 请求/响应校验模型
- **任务** (`tasks/`)：Celery 异步任务，调用服务层完成耗时操作

---

## 开发数据库（SQLite）

### 为什么使用 SQLite

开发环境默认使用 SQLite，原因：

- **零配置**：无需安装 PostgreSQL，开箱即用
- **轻量便携**：数据库文件可删除重建，方便调试
- **高度兼容**：SQLAlchemy 抽象了差异，代码无需修改

### 数据库文件位置

```
backend/yolo_trainer.db          # SQLite 数据库文件（已在 .gitignore 中）
```

### 重置数据库

```bash
# 删除旧数据库
rm backend/yolo_trainer.db

# 重启后端，自动创建表结构
cd backend
DEBUG=true uvicorn main:app --port 10003
```

应用启动时 `init_db()` 会自动调用 `Base.metadata.create_all()` 创建所有表。

### 切换到 PostgreSQL

当需要测试 PostgreSQL 特性时，修改 `.env`：

```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/yolo_trainer
```

### 数据库连接池配置

```python
# backend/app/core/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,        # 开发模式打印 SQL
    pool_pre_ping=True,         # 连接前测试有效性
    pool_size=10,               # 连接池大小
    max_overflow=20,            # 最大溢出连接
    pool_timeout=30,            # 获取连接超时
    pool_recycle=1800,          # 30 分钟回收连接
)
```

数据库操作支持自动重试（最多 3 次，指数退避）。

### 同步会话

Celery 任务无法使用异步会话，项目同时提供了同步 Session：

```python
from app.core.database import SessionLocal

db = SessionLocal()
try:
    # 同步数据库操作
    ...
finally:
    db.close()
```

`DATABASE_URL` 会自动转换驱动：`+aiosqlite` → `+pysqlite`（同步），`+asyncpg` → `+psycopg2`（同步）。

---

## 代码风格与架构约定

### Python（后端）

**风格规范：**

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 代码风格
- 使用 `ruff` 进行代码格式化和 lint 检查
- 所有公共函数和方法必须有**类型注解**
- 所有 API 端点和服务方法必须有**中文 Docstring**
- 异步优先：数据库操作使用 `AsyncSession`

```bash
# 代码格式化
ruff format backend/

# Lint 检查
ruff check backend/

# 自动修复
ruff check --fix backend/
```

**命名约定：**

| 类型 | 约定 | 示例 |
|------|------|------|
| 模块 | `snake_case` | `training_service.py` |
| 类 | `PascalCase` | `TrainingService` |
| 函数/方法 | `snake_case` | `create_training()` |
| 变量 | `snake_case` | `training_id` |
| 常量 | `UPPER_SNAKE` | `MAX_UPLOAD_SIZE` |
| 数据库模型 | `PascalCase` 单数 | `Training`, `Model` |
| Schema | `PascalCase` + 后缀 | `TrainingCreate`, `TrainingResponse` |
| API 路径 | `kebab-case` | `/model-versions`, `/training-jobs` |

**架构约定：**

1. **路由层** (`api/v1/`) 不做业务逻辑，只负责：
   - 参数校验（由 Pydantic Schema 自动完成）
   - 调用服务层方法
   - 返回 HTTP 响应（状态码 + 数据）

2. **服务层** (`services/`) 包含所有业务逻辑，职责：
   - 数据库 CRUD 操作
   - 业务规则校验
   - 调用外部服务
   - 可被路由和 Celery 任务复用

3. **数据模型** (`models/`) 使用 SQLAlchemy 2.0 Mapped 风格：
   ```python
   class User(Base):
       __tablename__ = "users"
       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
   ```

4. **Schema** (`schemas/`) 使用 Pydantic v2 风格：
   ```python
   class UserCreate(BaseModel):
       username: str
       email: EmailStr
       password: str = Field(min_length=8)

   class UserResponse(BaseModel):
       id: uuid.UUID
       username: str
       model_config = ConfigDict(from_attributes=True)
   ```

### JavaScript / Vue（前端）

**风格规范：**

- 使用 `<script setup>` 语法
- 页面组件放在 `views/` 目录下，按模块分文件夹
- API 调用统一通过 `src/api/` 封装，不要直接在组件中写 axios 调用
- 状态管理使用 Pinia Store，放在 `stores/` 目录
- 使用 ESLint + Prettier 进行代码格式化

**目录约定：**

| 目录 | 用途 |
|------|------|
| `src/api/` | HTTP 请求封装，每个模块一个文件 |
| `src/views/` | 页面组件，每个模块一个文件夹 |
| `src/stores/` | Pinia 状态管理 |
| `src/router/` | 路由配置 |
| `src/utils/` | 工具函数 |

**API 封装示例：**

```javascript
// src/api/training.js
import request from './request'

export const createTraining = (data) => request.post('/training/', data)
export const getTrainingList = (params) => request.get('/training/', { params })
export const getTrainingDetail = (id) => request.get(`/training/${id}`)
```

**请求拦截器**（`src/api/request.js`）自动处理：
- 附加 `Authorization: Bearer <token>` 请求头
- 401 响应自动跳转登录页
- 统一错误处理

### 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <description>

[可选正文]

[可选脚注]
```

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能变动） |
| `refactor` | 代码重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖变更 |

示例：

```
feat(training): 支持 YOLOv10 训练
fix(auth): 修复 Token 过期后未正确返回 401 的问题
docs: 更新 API 参考文档
refactor(database): 提取连接池配置到独立模块
```

---

## Git 工作流与贡献流程

### 开发流程

```bash
# 1. 确保在 dev 分支且是最新代码
git checkout dev
git pull origin dev

# 2. 创建功能分支
git checkout -b feat/my-feature

# 3. 开发并提交（遵循提交规范）
git add .
git commit -m "feat(module): 简短描述"

# 4. 定期同步 dev 分支（避免冲突）
git checkout dev
git pull origin dev
git checkout feat/my-feature
git rebase dev

# 5. 推送功能分支
git push origin feat/my-feature

# 6. 在 GitHub 上创建 Pull Request
#    - 源分支：feat/my-feature
#    - 目标分支：dev
#    - 填写 PR 描述，说明改动内容和原因
#    - 等待 Code Review
```

### PR 规范

- **PR 标题**：使用与提交一致的前缀格式
- **PR 描述**：包含以下内容：
  - 改动摘要
  - 测试方法
  - 影响范围
  - 关联 Issue（如有）
- **PR 大小**：保持小而专注，一个 PR 只做一件事
- **Code Review**：至少一人 Review 通过后才能合并

### 分支清理

```bash
# 功能分支合并后，删除本地和远程分支
git branch -d feat/my-feature
git push origin --delete feat/my-feature
```

---

## 常见开发任务

### 添加新的 API 端点

1. **定义 Schema**（`backend/app/schemas/`）:
   ```python
   from pydantic import BaseModel
   from typing import Optional
   import uuid

   class ExampleCreate(BaseModel):
       name: str
       description: Optional[str] = None

   class ExampleResponse(BaseModel):
       id: uuid.UUID
       name: str
       model_config = ConfigDict(from_attributes=True)
   ```

2. **定义数据模型**（`backend/app/models/`）:
   ```python
   import uuid
   from sqlalchemy import String
   from sqlalchemy.dialects.postgresql import UUID
   from sqlalchemy.orm import Mapped, mapped_column
   from app.core.database import Base

   class Example(Base):
       __tablename__ = "examples"
       id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       name: Mapped[str] = mapped_column(String(255), nullable=False)
   ```

3. **创建路由**（`backend/app/api/v1/`）:
   ```python
   from fastapi import APIRouter, Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from app.core.database import get_db
   from app.schemas.example import ExampleCreate, ExampleResponse

   router = APIRouter()

   @router.post("/", response_model=ExampleResponse, status_code=201)
   async def create_example(data: ExampleCreate, db: AsyncSession = Depends(get_db)):
       """创建示例资源。"""
       ...
   ```

4. **注册路由**（编辑 `backend/app/api/v1/__init__.py`）:
   ```python
   from app.api.v1.example import router as example_router
   api_router.include_router(example_router, prefix="/examples", tags=["示例"])
   ```

5. **添加前端 API 封装**（`frontend/src/api/example.js`）:
   ```javascript
   import request from './request'
   export const createExample = (data) => request.post('/examples/', data)
   ```

### 添加新的数据模型字段

1. 修改 `backend/app/models/` 中的 ORM 模型
2. 更新 `backend/app/schemas/` 中的 Pydantic Schema
3. 如需数据库迁移：`alembic revision --autogenerate -m "添加xxx字段"` → `alembic upgrade head`
4. 更新对应前端组件

### 添加新的 YOLO 版本支持

1. 在 `worker/trainer/` 创建新的训练器类，继承 `BaseTrainer`
2. 实现 `train()`、`validate()`、`export()` 方法
3. 在 `backend/app/schemas/training.py` 的版本枚举中添加新版本

### 调整训练参数

1. 修改 `worker/trainer/base.py` 中的 `TrainConfig` dataclass
2. 更新 `backend/app/schemas/training.py` 中的 Schema
3. 更新 `frontend/src/views/Training/TrainingCreate.vue` 中的表单组件

---

## 调试技巧

### 后端调试

```bash
# 1. 开启 DEBUG 模式（打印 SQL、详细日志）
DEBUG=true uvicorn main:app --port 10003 --reload

# 2. 使用 Python 调试器（debugpy，端口 5678）
pip install debugpy
python -m debugpy --listen 0.0.0.0:5678 -m uvicorn main:app --port 10003

# 3. 查看 Swagger UI 交互测试
# http://localhost:10003/docs → 可直接测试每个 API 端点

# 4. 使用 curl 测试
curl -X POST http://localhost:10003/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo3", "password": "demo123"}'
```

### 前端调试

```bash
# Vite 开发服务器自带 HMR 和 Source Map
npm run dev

# Vue DevTools（浏览器插件）可用于：
# - 查看组件树和状态
# - 追踪 Pinia Store 变化
# - 监控路由导航
```

### 测试 API

```bash
# 1. 登录获取 Token
TOKEN=$(curl -s -X POST http://localhost:10003/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo3","password":"demo123"}' | jq -r '.access_token')

# 2. 使用 Token 调用受保护 API
curl http://localhost:10003/api/v1/training/ \
  -H "Authorization: Bearer $TOKEN"

# 3. 健康检查
curl http://localhost:10003/health
```

---

*更多架构与设计细节请参考 [架构设计文档](architecture.md) 和 [API 参考文档](api-reference.md)。*
