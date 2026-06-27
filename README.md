<div align="center">

<img src="assets/banner.svg" width="100%" alt="YOLO 目标检测模型训练平台">

<br>

### 👁️ YOLO 目标检测模型训练管理平台

[![Stars](https://img.shields.io/github/stars/dirjaker/yolo-trainer?style=flat-square&label=Stars&color=FFD700)](https://github.com/dirjaker/yolo-trainer/stargazers)
[![Forks](https://img.shields.io/github/forks/dirjaker/yolo-trainer?style=flat-square&label=Forks&color=4A90D9)](https://github.com/dirjaker/yolo-trainer/network/members)
[![Contributors](https://img.shields.io/github/contributors/dirjaker/yolo-trainer?style=flat-square&label=Contributors&color=8B4513)](https://github.com/dirjaker/yolo-trainer/graphs/contributors)
[![License](https://img.shields.io/github/license/dirjaker/yolo-trainer?style=flat-square&label=License&color=20B2AA)](https://github.com/dirjaker/yolo-trainer/blob/dev/LICENSE)

</div>

---

> 一站式 YOLO 目标检测模型训练管理平台，覆盖从数据集管理、模型训练、在线推理测试、模型对比评估到生产部署的完整 ML 生命周期。

## ✨ 功能特性

| 模块 | 说明 |
|------|------|
| 📊 **仪表盘** | 训练概览、模型统计、数据集统计，ECharts 训练曲线 |
| 🏋️ **训练管理** | 支持 YOLOv5 / v8 / v9 / v10，自定义超参，异步 Celery 任务队列 |
| 🧠 **模型管理** | 模型版本注册、标签分类、权重文件下载、多格式导出 |
| 📦 **数据集管理** | ZIP 上传，自动解析 YOLO / COCO / VOC 格式，类别统计 |
| 🧪 **测试中心** | 单图/批量推理，YOLO 实时检测，结果可视化标注 |
| ⚖️ **模型对比** | 多模型横向对比（mAP50、mAP50-95、Precision、Recall、F1、FPS） |
| 🔍 **超参搜索** | 贝叶斯优化 / 网格搜索 / 随机搜索，自动寻找最优超参数组合 |
| 🚀 **模型部署** | 一键部署为 REST API / gRPC / WebSocket 服务 |
| 👥 **团队管理** | 团队创建、成员邀请、角色权限控制 |
| 📝 **活动日志** | 全操作审计追踪，按用户、资源类型、时间范围筛选 |

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+（前端构建）
- Redis（Celery 任务队列，可选）

### 后端启动

```bash
cd backend
conda create -n yolo-trainer python=3.12 -y
conda activate yolo-trainer
pip install -r requirements.txt

# 启动 API 服务（端口 10003）
DEBUG=true uvicorn main:app --host 127.0.0.1 --port 10003
```

### 前端启动

```bash
cd frontend
npm install
npm run dev                # Vite 开发服务器（端口 5173），API 代理到 10003
npm run build              # 生产构建 → dist/
```

### 一体化启动

项目提供了 `docs-ui/server.py`，可作为前端静态文件服务 + API 反向代理一体运行：

```bash
cd docs-ui
python server.py           # 端口 10001，/api/v1/→127.0.0.1:10003
```

启动后访问：
- **Web 界面**：http://localhost:10001
- **API 文档**：http://localhost:10003/docs
- **ReDoc**：http://localhost:10003/redoc

### 种子数据

```bash
cd backend
python seed_examples.py    # 插入示例数据集、训练任务、模型记录
```

默认测试账号：`demo3` / `demo123`

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 (Composition API), Naive UI, Pinia, Vue Router, Axios, ECharts |
| **后端** | FastAPI, SQLAlchemy 2.0 (async + sync), Pydantic v2, Alembic |
| **任务队列** | Celery + Redis |
| **训练引擎** | PyTorch, Ultralytics (YOLOv5/v8/v9/v10) |
| **数据库** | SQLite（开发） / PostgreSQL（生产） |
| **安全** | JWT 认证, bcrypt 密码哈希, CORS, 速率限制 |
| **监控** | Prometheus 指标, 结构化日志 |

## 📁 项目结构

```
yolo-trainer/
├── backend/                   # FastAPI 后端服务
│   ├── app/
│   │   ├── api/v1/            # REST API 路由（11 模块）
│   │   │   ├── auth.py        #   认证（注册/登录/JWT）
│   │   │   ├── training.py    #   训练管理（CRUD / 启动 / 停止 / 指标）
│   │   │   ├── model.py       #   模型管理（版本 / 标签 / 导出 / 下载）
│   │   │   ├── dataset.py     #   数据集管理（上传 / 解析 / 统计）
│   │   │   ├── test.py        #   测试中心（单图/批量推理 YOLO）
│   │   │   ├── compare.py     #   模型对比
│   │   │   ├── deploy.py      #   模型部署
│   │   │   ├── hyperparameter.py  # 超参搜索
│   │   │   ├── team.py        #   团队管理
│   │   │   ├── activity.py    #   活动日志
│   │   │   └── metrics.py     #   健康检查 / Prometheus
│   │   ├── core/              # 核心基础设施
│   │   │   ├── config.py      #   配置管理 (pydantic-settings)
│   │   │   ├── database.py    #   数据库引擎 (async + sync)
│   │   │   ├── security.py    #   认证与授权
│   │   │   └── rate_limiter.py
│   │   ├── models/            # SQLAlchemy 数据模型
│   │   ├── schemas/           # Pydantic 请求/响应模型
│   │   ├── services/          # 业务逻辑层
│   │   └── tasks/             # Celery 异步任务
│   ├── main.py                # FastAPI 应用入口
│   ├── seed_examples.py       # 种子数据
│   └── requirements.txt
├── frontend/                  # Vue 3 前端应用
│   └── src/
│       ├── api/               # API 接口封装（request.js + 各模块）
│       ├── views/             # 页面组件（Dashboard/Training/Model/…）
│       ├── stores/            # Pinia 状态管理
│       ├── router/            # Vue Router 路由配置
│       └── utils/             # 工具函数 + SVG 几何图标
├── worker/                    # 训练引擎
│   ├── trainer/               # YOLO 训练器（v5/v8/v9/v10）
│   ├── evaluator/             # 模型评估器
│   └── exporter/              # 模型导出器
├── docs-ui/                   # 一体化前端服务器
│   └── server.py              # HTTP 静态服务 + /api/v1/ 反向代理
├── docker/                    # Docker 部署配置
├── scripts/                   # 部署/运维脚本
├── docs/                      # 技术文档
└── assets/                    # README 横幅等静态资源
```

## 📚 文档

| 文档 | 说明 |
|------|------|
| [架构设计](docs/architecture.md) | 系统架构、数据流、组件设计 |
| [API 参考](docs/api-reference.md) | REST API 完整接口文档 |
| [部署指南](docs/deployment.md) | Docker / 手动部署 |
| [开发指南](docs/development.md) | 开发环境搭建与贡献规范 |
| [更新日志](docs/CHANGELOG.md) | 版本更新记录 |

## 📝 开发日志

- [x] 多版本 YOLO 训练支持（v5/v8/v9/v10）
- [x] 异步 Celery 任务队列
- [x] 模型版本控制与标签管理
- [x] 数据集上传与自动解析（YOLO/COCO/VOC）
- [x] 单图/批量 YOLO 推理测试 + 结果可视化
- [x] Vue 3 + Naive UI 管理界面（10 模块）
- [x] JWT 认证 + bcrypt 密码哈希
- [x] 多模型横向对比评估
- [x] 超参自动搜索（贝叶斯/网格/随机）
- [x] 模型多格式导出（ONNX / TensorRT / TorchScript）
- [x] 一键模型部署（REST/gRPC/WebSocket）
- [x] 团队协作与权限管理
- [x] 全操作审计日志
- [x] Prometheus 指标监控
- [x] 活跃种子数据（4 数据集 + 4 训练任务 + 2 模型版本）
- [ ] 分布式训练
- [ ] 更多模型支持（YOLOv11+）
- [ ] 云端部署方案

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">

🔗 **GitHub**: [dirjaker/yolo-trainer](https://github.com/dirjaker/yolo-trainer)

⭐ 如果这个项目对你有帮助，请给一个 Star！

</div>
