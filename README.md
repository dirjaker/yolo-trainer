<div align="center">

<img src="assets/banner.svg" width="100%" alt="YOLO 模型训练平台">

<br>

### 👁️ YOLO 模型训练平台

[![Stars](https://img.shields.io/github/stars/dirjaker/yolo-trainer?style=flat-square&label=Stars&color=FFD700)](https://github.com/dirjaker/yolo-trainer/stargazers)
[![Forks](https://img.shields.io/github/forks/dirjaker/yolo-trainer?style=flat-square&label=Forks&color=4A90D9)](https://github.com/dirjaker/yolo-trainer/network/members)
[![Contributors](https://img.shields.io/github/contributors/dirjaker/yolo-trainer?style=flat-square&label=Contributors&color=8B4513)](https://github.com/dirjaker/yolo-trainer/graphs/contributors)
[![License](https://img.shields.io/github/license/dirjaker/yolo-trainer?style=flat-square&label=License&color=20B2AA)](https://github.com/dirjaker/yolo-trainer/blob/dev/LICENSE)

</div>

---

> 基于 YOLO 的一站式目标检测模型训练管理平台，支持从数据集上传、模型训练、在线测试到模型部署的全流程管理。

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 🎯 **模型训练** | 支持 YOLOv5/v8/v9/v10 多版本训练，异步任务队列 |
| 📦 **模型管理** | 模型版本控制、标签管理、文件下载与导出 |
| 📂 **数据集管理** | ZIP 上传，支持 YOLO / COCO / VOC 格式 |
| 🧪 **测试中心** | 单图/批量推理，实时检测结果可视化 |
| 📊 **模型对比** | 多模型同维度对比（mAP、Precision、Recall、F1、FPS） |
| 🔍 **超参搜索** | 随机/贝叶斯/网格搜索，自动寻找最优超参数组合 |
| 🚀 **模型部署** | 支持 ONNX Runtime / TensorRT / TorchServe 多平台部署 |
| 👥 **团队管理** | 团队创建、成员邀请、角色权限控制 |
| 📝 **活动日志** | 全操作审计日志，支持按用户、资源类型、时间范围筛选 |
| 📈 **监控仪表盘** | API 请求指标、系统健康检查、Prometheus 集成 |

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/dirjaker/yolo-trainer.git
cd yolo-trainer

# 创建虚拟环境
conda create -n yolo-trainer python=3.12 -y
conda activate yolo-trainer

# 安装依赖
pip install -r requirements.txt

# 运行项目
python main.py
```

启动后访问：
- **Web 界面**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3, Naive UI, Pinia, Vue Router, Axios |
| **后端** | FastAPI, SQLAlchemy (async), Pydantic v2 |
| **任务队列** | Celery + Redis |
| **训练引擎** | PyTorch, Ultralytics (YOLOv5/v8/v9/v10) |
| **数据库** | SQLite（开发） / PostgreSQL（生产） |
| **安全** | JWT 认证, bcrypt 密码哈希, CORS, CSP |

## 📁 项目结构

```
yolo-trainer/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/v1/          # REST API 路由
│   │   ├── core/            # 核心配置（数据库、安全、缓存、监控）
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   ├── services/        # 业务逻辑层
│   │   └── tasks/           # Celery 异步任务
│   └── main.py              # FastAPI 应用入口
├── frontend/                # 前端应用
│   └── src/
│       ├── api/             # API 接口封装
│       ├── views/           # 页面组件
│       ├── stores/          # Pinia 状态管理
│       ├── router/          # 路由配置
│       └── utils/           # 工具函数
├── worker/                  # 训练引擎
│   ├── trainer/             # YOLO 训练器（v5/v8/v9/v10）
│   ├── evaluator/           # 模型评估器
│   └── exporter/            # 模型导出器
├── docs/                    # 项目文档
└── assets/                  # 静态资源
```

## 📚 文档

- [用户指南](docs/user-guide.md) — 完整使用教程
- [API 参考](docs/api-reference.md) — REST API 接口文档
- [架构设计](docs/architecture.md) — 系统架构详细设计
- [部署指南](docs/deployment.md) — Docker / 手动部署
- [开发指南](docs/DEVELOPMENT.md) — 开发环境搭建与贡献规范
- [更新日志](docs/CHANGELOG.md) — 版本更新记录

## 📝 开发日志

- [x] 多版本 YOLO 训练（v5/v8/v9/v10）
- [x] 模型版本控制与标签管理
- [x] 数据集上传与管理
- [x] 单图/批量推理测试
- [x] Web 管理界面（Vue3 + NaiveUI）
- [x] JWT 用户认证与授权
- [x] 模型对比评估
- [x] 超参自动搜索
- [x] 模型多格式导出（ONNX / TensorRT / TorchScript）
- [x] 模型部署管理
- [x] 团队协作管理
- [x] 活动日志审计
- [ ] 分布式训练
- [ ] 更多模型支持（YOLOv11+）
- [ ] 云端部署方案

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">

🔗 **GitHub**: [dirjaker/yolo-trainer](https://github.com/dirjaker/yolo-trainer)

⭐ 如果这个项目对你有帮助，请给一个 Star 支持一下！

</div>
