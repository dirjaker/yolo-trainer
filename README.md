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

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 🎯 **模型训练** | 支持 YOLOv5/v8/v9/v10 多版本训练 |
| 📦 **版本控制** | 模型版本管理和对比评估 |
| 🏷️ **数据标注** | 集成标注工具，支持 COCO/YOLO 格式 |
| 🧪 **自动测试** | 训练完成自动运行测试评估 |
| 📊 **训练监控** | 实时查看训练进度和指标曲线 |
| 🔌 **模型导出** | 支持 ONNX、TensorRT 等格式导出 |


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

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3, Naive UI |
| **后端** | FastAPI, SQLAlchemy |
| **训练** | PyTorch, Ultralytics |
| **数据库** | SQLite |

## 📝 开发日志

- [x] 多版本 YOLO 训练
- [x] 模型版本控制
- [x] 数据标注集成
- [x] 自动测试评估
- [x] Web 管理界面
- [ ] 分布式训练
- [ ] 更多模型支持
- [ ] 云端部署

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">

🔗 **GitHub**: [dirjaker/yolo-trainer](https://github.com/dirjaker/yolo-trainer)

⭐ 如果这个项目对你有帮助，请给一个 Star 支持一下！

</div>
