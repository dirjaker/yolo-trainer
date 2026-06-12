# YOLO Trainer

> YOLO 视觉模型训练、版本控制与测试一体化平台

[![GitHub](https://img.shields.io/badge/GitHub-dirjaker-181717?style=flat&logo=github)](https://github.com/dirjaker)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![YOLO](https://img.shields.io/badge/YOLO-v5%20%7C%20v8%20%7C%20v9%20%7C%20v10-green.svg)](https://github.com/ultralytics/ultralytics)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📖 项目简介

YOLO Trainer 是一个专为目标检测模型训练设计的 Web 平台，支持 YOLO 各版本（v5、v8、v9、v10）的训练、版本控制和测试。

**核心功能：**
- 🚀 **模型训练** - 支持 YOLOv5/v8/v9/v10 多版本训练
- 📦 **版本控制** - 完整的模型版本管理，支持回滚和对比
- 🧪 **模型测试** - 在线测试模型效果，支持批量推理
- 📊 **训练监控** - 实时查看训练进度和指标
- 🗂️ **数据集管理** - 数据集上传、标注、版本管理
- 🔍 **模型对比** - 多模型指标对比，可视化分析
- ⚡ **超参搜索** - 自动超参数优化（贝叶斯/随机/网格）
- 🚢 **模型部署** - 一键部署到 ONNX Runtime/TensorRT/TorchServe
- 👥 **团队协作** - 多用户支持，权限管理，活动日志
- 🔒 **安全防护** - SQL 注入检测、XSS 防护、请求限流
- 📈 **监控告警** - Prometheus 指标、健康检查、结构化日志

---

## 🎯 核心功能

### 1. 模型训练

| 功能 | 说明 |
|------|------|
| 多版本支持 | YOLOv5、YOLOv8、YOLOv9、YOLYOv10 |
| 参数配置 | 学习率、批量大小、训练轮数等 |
| GPU 支持 | 自动检测 GPU，支持多卡训练 |
| 训练监控 | 实时 Loss、mAP 曲线 |
| 断点续训 | 支持从 checkpoint 继续训练 |

### 2. 版本控制

| 功能 | 说明 |
|------|------|
| 版本管理 | 自动版本号，语义化版本控制 |
| 版本对比 | 对比不同版本的 mAP、速度等指标 |
| 版本回滚 | 快速回滚到历史版本 |
| 模型标签 | 为模型打标签（production、staging 等） |
| 版本快照 | 保存训练配置和环境信息 |

### 3. 模型测试

| 功能 | 说明 |
|------|------|
| 单图测试 | 上传图片进行推理 |
| 批量测试 | 批量图片/视频推理 |
| 结果可视化 | 检测结果可视化展示 |
| 指标统计 | Precision、Recall、mAP 等 |
| 导出功能 | 导出 ONNX、TensorRT 等格式 |

### 4. 数据集管理

| 功能 | 说明 |
|------|------|
| 数据上传 | 支持 COCO、VOC、YOLO 格式 |
| 数据标注 | 集成标注工具或导入标注 |
| 数据版本 | 数据集版本管理 |
| 数据增强 | 自动数据增强配置 |
| 数据统计 | 类别分布、标注统计 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3 + Naive UI)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 训练管理 │ │ 模型管理 │ │ 数据管理 │ │ 测试中心 │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI + Celery)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 训练服务 │ │ 模型服务 │ │ 数据服务 │ │ 测试服务 │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    PostgreSQL   │ │     Redis       │ │   MinIO/S3      │
│    (元数据)      │ │    (任务队列)    │ │   (文件存储)     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GPU Worker (Celery)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Ultralytics (YOLO)                       │  │
│  │    v5    │    v8    │    v9    │    v10    │    ...       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
yolo-trainer/
│
├── README.md                              # 项目说明（本文件）
│
├── docs/                                  # 📚 文档
│   ├── architecture.md                    # 架构设计文档
│   ├── api-reference.md                   # API 参考文档
│   ├── deployment.md                      # 部署指南
│   └── user-guide.md                      # 用户指南
│
├── frontend/                              # 🎨 前端
│   ├── src/
│   │   ├── views/                         # 页面
│   │   ├── components/                    # 组件
│   │   ├── stores/                        # 状态管理
│   │   └── api/                           # API 接口
│   ├── package.json
│   └── vite.config.js
│
├── backend/                               # ⚙️ 后端
│   ├── app/
│   │   ├── api/                           # API 路由
│   │   ├── core/                          # 核心模块
│   │   ├── models/                        # 数据模型
│   │   ├── schemas/                       # Pydantic 模型
│   │   ├── services/                      # 业务逻辑
│   │   └── tasks/                         # Celery 任务
│   ├── main.py                            # FastAPI 入口
│   └── requirements.txt
│
├── worker/                                # 🔧 GPU Worker
│   ├── trainer/                           # 训练器
│   │   ├── yolov5.py                      # YOLOv5 训练
│   │   ├── yolov8.py                      # YOLOv8 训练
│   │   ├── yolov9.py                      # YOLOv9 训练
│   │   └── yolov10.py                     # YOLYOv10 训练
│   ├── evaluator/                         # 评估器
│   └── exporter/                          # 模型导出
│
├── docker/                                # 🐳 Docker 配置
│   ├── Dockerfile.frontend
│   ├── Dockerfile.backend
│   ├── Dockerfile.worker
│   └── docker-compose.yml
│
├── scripts/                               # 📜 脚本
│   ├── setup.sh                           # 环境配置
│   ├── train.sh                           # 训练脚本
│   └── deploy.sh                          # 部署脚本
│
├── tests/                                 # 🧪 测试
│   ├── test_api.py
│   ├── test_trainer.py
│   └── test_evaluator.py
│
├── .env.example                           # 环境变量示例
├── .gitignore
└── LICENSE
```

---

## 🛠️ 技术栈

### 前端

| 技术 | 说明 |
|------|------|
| Vue 3 | 渐进式 JavaScript 框架 |
| Naive UI | Vue 3 组件库 |
| Pinia | 状态管理 |
| Axios | HTTP 客户端 |
| ECharts | 图表可视化 |

### 后端

| 技术 | 说明 |
|------|------|
| FastAPI | 高性能 Python Web 框架 |
| SQLAlchemy | ORM |
| Celery | 分布式任务队列 |
| Redis | 消息队列/缓存 |
| PostgreSQL | 关系型数据库 |

### AI/ML

| 技术 | 说明 |
|------|------|
| Ultralytics | YOLO 官方实现 |
| PyTorch | 深度学习框架 |
| ONNX | 模型导出格式 |
| TensorRT | NVIDIA 推理优化 |

### 基础设施

| 技术 | 说明 |
|------|------|
| Docker | 容器化部署 |
| MinIO | 对象存储 |
| Nginx | 反向代理 |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- NVIDIA GPU（推荐）

### 一键部署

```bash
# 克隆项目
git clone https://github.com/dirjaker/yolo-trainer.git
cd yolo-trainer

# 复制环境变量
cp .env.example .env

# 编辑配置（设置数据库密码、GPU 配置等）
vim .env

# Docker Compose 启动
docker-compose up -d
```

### 访问服务

- 前端界面：http://localhost:5173
- API 文档：http://localhost:8000/docs
- Flower（Celery 监控）：http://localhost:5555

---

## 📝 使用示例

### 1. 创建数据集

```python
import requests

# 上传数据集
files = {'file': open('dataset.zip', 'rb')}
response = requests.post('http://localhost:8000/api/datasets/upload', files=files)
dataset_id = response.json()['id']
```

### 2. 创建训练任务

```python
# 创建训练任务
task_data = {
    'name': 'yolov8n-coco',
    'model_version': 'yolov8n',
    'dataset_id': dataset_id,
    'epochs': 100,
    'batch_size': 16,
    'img_size': 640,
    'learning_rate': 0.01
}
response = requests.post('http://localhost:8000/api/trainings', json=task_data)
```

### 3. 测试模型

```python
# 上传图片进行测试
files = {'image': open('test.jpg', 'rb')}
params = {'model_id': 'model-123'}
response = requests.post('http://localhost:8000/api/tests/predict', files=files, params=params)
```

---

## 📊 API 接口

### 训练相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/trainings | 创建训练任务 |
| GET | /api/trainings | 获取训练列表 |
| GET | /api/trainings/{id} | 获取训练详情 |
| POST | /api/trainings/{id}/stop | 停止训练 |
| GET | /api/trainings/{id}/logs | 获取训练日志 |

### 模型相关

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/models | 获取模型列表 |
| GET | /api/models/{id} | 获取模型详情 |
| POST | /api/models/{id}/export | 导出模型 |
| DELETE | /api/models/{id} | 删除模型 |
| GET | /api/models/{id}/versions | 获取版本历史 |

### 数据集相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/datasets/upload | 上传数据集 |
| GET | /api/datasets | 获取数据集列表 |
| GET | /api/datasets/{id} | 获取数据集详情 |
| DELETE | /api/datasets/{id} | 删除数据集 |

### 测试相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/tests/predict | 单图预测 |
| POST | /api/tests/batch | 批量预测 |
| GET | /api/tests/{id}/results | 获取测试结果 |

---

## 🔧 配置说明

### 环境变量

```bash
# 数据库
DATABASE_URL=postgresql://user:password@localhost:5432/yolo_trainer

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# GPU 配置
CUDA_VISIBLE_DEVICES=0,1

# 训练配置
MAX_CONCURRENT_TRAININGS=2
DEFAULT_MODEL_PATH=/models/pretrained
```

---

## 📈 性能指标

| 指标 | 说明 |
|------|------|
| 训练吞吐量 | 支持 2 个并发训练任务 |
| 推理速度 | 单张图片 < 50ms（GPU） |
| 存储容量 | 支持 TB 级模型存储 |
| 用户并发 | 支持 50+ 并发用户 |

---

## 🗺️ 开发路线

### Phase 1（MVP）- 核心功能 ✅ 已完成
- [x] 项目架构设计
- [x] YOLOv8 训练集成
- [x] 基础版本控制
- [x] 单图测试
- [x] 基础 UI

### Phase 2 - 功能完善 ✅ 已完成
- [x] YOLOv5 支持
- [x] YOLOv9/v10 支持
- [x] 数据集管理
- [x] 训练监控
- [x] 批量测试

### Phase 3 - 高级功能 ✅ 已完成
- [x] 模型对比
- [x] 自动超参搜索
- [x] 模型部署
- [x] 团队协作

### Phase 4 - 生产就绪 ✅ 已完成
- [x] 性能优化
- [x] 安全加固
- [x] 监控告警
- [x] 文档完善

---

## 🤝 如何贡献

欢迎提交 Issue 和 Pull Request！

### 贡献方式

1. **报告问题**：发现 Bug 或有改进建议
2. **功能开发**：实现新功能或优化现有功能
3. **文档完善**：补充或修正文档
4. **测试反馈**：使用并反馈问题

### 开发流程

```bash
# 1. Fork 项目
# 2. 创建特性分支
git checkout -b feature/amazing-feature

# 3. 提交改动
git commit -m 'Add amazing feature'

# 4. 推送到远程
git push origin feature/amazing-feature

# 5. 创建 Pull Request
```

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👤 作者

**dirjaker**
- GitHub: [@dirjaker](https://github.com/dirjaker)

---

## 🙏 致谢

- [Ultralytics](https://github.com/ultralytics/ultralytics) - YOLO 官方实现
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架

---

## 📞 联系方式

如有问题或建议，欢迎通过以下方式联系：
- GitHub Issues：[提交问题](https://github.com/dirjaker/yolo-trainer/issues)

---

## ⭐ 支持项目

如果这个项目对你有帮助，请给个 Star ⭐！

---

*最后更新：2026 年 6 月*

### 模型对比

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/compare/models | 创建模型对比任务 |
| GET | /api/compare/models/{id} | 获取对比结果 |
| GET | /api/compare/models | 获取对比列表 |

### 模型部署

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/deployments | 创建部署任务 |
| GET | /api/deployments | 获取部署列表 |
| GET | /api/deployments/{id} | 获取部署详情 |
| GET | /api/deployments/{id}/status | 获取部署状态 |
| POST | /api/deployments/{id}/stop | 停止部署 |

### 超参搜索

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/hyperparameter/search | 创建搜索任务 |
| GET | /api/hyperparameter/search | 获取搜索列表 |
| GET | /api/hyperparameter/search/{id} | 获取搜索结果 |
| GET | /api/hyperparameter/search/{id}/trials | 获取所有试验 |
| POST | /api/hyperparameter/search/{id}/cancel | 取消搜索 |

### 团队管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/teams | 创建团队 |
| GET | /api/teams | 获取团队列表 |
| GET | /api/teams/{id} | 获取团队详情 |
| POST | /api/teams/{id}/members | 添加成员 |
| DELETE | /api/teams/{id}/members/{user_id} | 移除成员 |

### 活动日志

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/activities | 获取活动日志 |

### 监控

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/metrics | Prometheus 指标 |
| GET | /api/health | 健康检查 |
