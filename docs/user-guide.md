# 用户指南

> YOLO Trainer 使用指南

---

## 📋 目录

- [快速开始](#快速开始)
- [数据集管理](#数据集管理)
- [模型训练](#模型训练)
- [模型测试](#模型测试)
- [版本控制](#版本控制)
- [常见问题](#常见问题)

---

## 快速开始

### 第一步：注册账号

1. 访问 http://localhost:5173
2. 点击"注册"按钮
3. 填写用户名、邮箱和密码
4. 完成注册并登录

### 第二步：上传数据集

1. 进入"数据集管理"页面
2. 点击"上传数据集"按钮
3. 填写数据集信息：
   - 名称：数据集名称
   - 格式：选择 COCO、VOC 或 YOLO 格式
   - 描述：数据集说明
4. 上传 ZIP 压缩包
5. 等待数据集处理完成

### 第三步：创建训练任务

1. 进入"训练管理"页面
2. 点击"创建训练"按钮
3. 配置训练参数：
   - 任务名称
   - 模型版本（YOLOv5/v8/v9/v10）
   - 选择数据集
   - 训练参数（epochs、batch_size 等）
4. 点击"开始训练"

### 第四步：查看训练进度

1. 在训练列表中找到正在训练的任务
2. 点击查看详情
3. 实时查看：
   - 训练进度
   - Loss 曲线
   - mAP 指标
   - 训练日志

### 第五步：测试模型

1. 训练完成后，进入"测试中心"
2. 选择训练好的模型
3. 上传测试图片
4. 查看检测结果

---

## 数据集管理

### 支持的数据格式

#### YOLO 格式

```
dataset/
├── images/
│   ├── train/
│   │   ├── image1.jpg
│   │   └── image2.jpg
│   └── val/
│       ├── image3.jpg
│       └── image4.jpg
├── labels/
│   ├── train/
│   │   ├── image1.txt
│   │   └── image2.txt
│   └── val/
│       ├── image3.txt
│       └── image4.txt
└── dataset.yaml
```

**dataset.yaml 示例：**
```yaml
train: ./images/train
val: ./images/val

nc: 3
names: ['person', 'car', 'dog']
```

**标注格式（每行一个目标）：**
```
class_id x_center y_center width height
0 0.5 0.5 0.3 0.4
1 0.2 0.3 0.1 0.2
```

#### COCO 格式

```json
{
  "images": [
    {
      "id": 1,
      "file_name": "image1.jpg",
      "width": 640,
      "height": 480
    }
  ],
  "annotations": [
    {
      "id": 1,
      "image_id": 1,
      "category_id": 0,
      "bbox": [100, 150, 200, 250],
      "area": 50000,
      "iscrowd": 0
    }
  ],
  "categories": [
    {
      "id": 0,
      "name": "person"
    }
  ]
}
```

### 上传数据集

1. 将数据集打包成 ZIP 文件
2. 确保目录结构符合规范
3. 在"数据集管理"页面上传
4. 等待处理完成（通常 1-5 分钟）

### 数据集统计

上传成功后，系统会自动统计：
- 图片总数
- 标注总数
- 各类别分布
- 训练/验证/测试集划分

### 数据增强配置

在训练时可以配置数据增强：

```json
{
  "augmentation": {
    "hsv_h": 0.015,
    "hsv_s": 0.7,
    "hsv_v": 0.4,
    "degrees": 0.0,
    "translate": 0.1,
    "scale": 0.5,
    "shear": 0.0,
    "perspective": 0.0,
    "flipud": 0.0,
    "fliplr": 0.5,
    "mosaic": 1.0,
    "mixup": 0.0
  }
}
```

---

## 模型训练

### 支持的模型版本

| 模型 | 特点 | 推荐场景 |
|------|------|---------|
| YOLOv5n | 轻量级，速度快 | 移动端部署 |
| YOLOv5s | 平衡速度和精度 | 通用场景 |
| YOLOv5m | 中等模型 | 需要更高精度 |
| YOLOv5l | 大模型 | 高精度需求 |
| YOLOv5x | 超大模型 | 最高精度 |
| YOLOv8n | 最新轻量级 | 移动端部署 |
| YOLOv8s | 最新平衡型 | 通用场景 |
| YOLOv8m | 最新中等模型 | 需要更高精度 |
| YOLOv8l | 最新大模型 | 高精度需求 |
| YOLOv8x | 最新超大模型 | 最高精度 |
| YOLOv9c | 高效架构 | 资源受限场景 |
| YOLOv9e | 增强版 | 更高精度 |
| YOLOv10n | 最新轻量级 | 实时检测 |
| YOLOv10s | 最新平衡型 | 通用场景 |

### 训练参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| epochs | 100 | 训练轮数 |
| batch_size | 16 | 批量大小 |
| img_size | 640 | 输入图片尺寸 |
| learning_rate | 0.01 | 学习率 |
| optimizer | Adam | 优化器（SGD/Adam/AdamW） |
| patience | 50 | 早停轮数 |
| workers | 8 | 数据加载线程数 |
| device | 0 | GPU 编号 |
| amp | true | 自动混合精度 |
| cache | false | 数据缓存（ram/disk） |

### 创建训练任务

**方式一：Web UI**

1. 点击"训练管理" -> "创建训练"
2. 填写表单：
   ```
   任务名称：yolov8n-custom
   模型版本：YOLOv8n
   数据集：my-dataset
   训练轮数：100
   批量大小：16
   图片尺寸：640
   ```
3. 点击"开始训练"

**方式二：API**

```python
import requests

data = {
    "name": "yolov8n-custom",
    "model_version": "yolov8n",
    "dataset_id": "dataset-uuid",
    "config": {
        "epochs": 100,
        "batch_size": 16,
        "img_size": 640,
        "learning_rate": 0.01
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/trainings",
    json=data,
    headers={"Authorization": "Bearer your_token"}
)

print(response.json())
```

### 监控训练进度

**实时指标：**
- Train Loss：训练损失
- Val Loss：验证损失
- mAP50：IoU=0.5 时的平均精度
- mAP50-95：IoU=0.5:0.95 时的平均精度
- Precision：精确率
- Recall：召回率

**查看日志：**
```bash
# 通过 API 获取日志
curl http://localhost:8000/api/v1/trainings/{id}/logs

# 通过 WebSocket 实时推送
ws://localhost:8000/ws/trainings/{id}
```

### 断点续训

如果训练中断，可以从 checkpoint 继续训练：

```json
{
  "config": {
    "resume": true,
    "checkpoint": "path/to/last.pt"
  }
}
```

---

## 模型测试

### 单图测试

1. 进入"测试中心"
2. 选择模型
3. 上传图片
4. 调整参数：
   - 置信度阈值（0-1）：过滤低置信度检测
   - IoU 阈值（0-1）：NMS 阈值
5. 点击"开始测试"
6. 查看结果：
   - 检测框
   - 类别标签
   - 置信度分数
   - 推理时间

### 批量测试

1. 选择"批量测试"
2. 上传多张图片或 ZIP 文件
3. 选择模型和参数
4. 开始测试
5. 下载结果：
   - 带检测框的图片
   - JSON 格式检测结果
   - 统计报告

### 测试结果解读

**检测结果示例：**
```json
{
  "detections": [
    {
      "class": "person",
      "class_id": 0,
      "confidence": 0.923,
      "bbox": {
        "x1": 100,
        "y1": 150,
        "x2": 300,
        "y2": 400
      }
    }
  ]
}
```

**指标说明：**

| 指标 | 说明 |
|------|------|
| Precision | 精确率：预测为正样本中实际为正的比例 |
| Recall | 召回率：实际为正样本中被预测为正的比例 |
| mAP50 | IoU=0.5 时的平均精度 |
| mAP50-95 | IoU=0.5:0.95 时的平均精度 |
| F1 Score | Precision 和 Recall 的调和平均 |

### 模型对比

1. 进入"模型管理" -> "模型对比"
2. 选择要对比的模型（2-4 个）
3. 上传测试图片
4. 查看对比结果：
   - 各模型的检测结果
   - 推理时间对比
   - 精度指标对比
   - 可视化对比图

---

## 版本控制

### 模型版本

每个训练完成的模型都会自动创建一个版本：

```
v1.0.0 - 初始版本
v1.1.0 - 增加训练轮数
v1.2.0 - 调整学习率
v2.0.0 - 更换模型架构
```

### 版本标签

为模型打标签便于管理：

```bash
# 通过 API 添加标签
curl -X POST http://localhost:8000/api/v1/models/{id}/tags \
  -H "Authorization: Bearer token" \
  -d '{"tags": ["production", "best"]}'
```

**常用标签：**
- `production`：生产环境使用
- `staging`：测试环境使用
- `best`：当前最佳模型
- `archive`：归档版本

### 版本对比

1. 进入"模型管理" -> "版本对比"
2. 选择要对比的版本
3. 查看对比：
   - mAP 指标对比
   - 推理速度对比
   - 模型大小对比
   - 训练配置对比

### 版本回滚

如果新版本效果不好，可以回滚到历史版本：

1. 找到要回滚的版本
2. 点击"回滚到此版本"
3. 确认回滚
4. 系统会将该版本标记为当前版本

### 版本导出

导出模型用于部署：

1. 选择模型版本
2. 选择导出格式：
   - ONNX：通用格式
   - TensorRT：NVIDIA GPU 优化
   - CoreML：Apple 设备
   - TFLite：移动端
3. 下载导出文件

---

## 常见问题

### Q1: 训练速度很慢怎么办？

**可能原因：**
- GPU 未正确使用
- 数据加载瓶颈
- 图片尺寸太大

**解决方案：**
```json
{
  "config": {
    "device": "0",           // 确认使用 GPU
    "workers": 8,            // 增加数据加载线程
    "amp": true,             // 启用混合精度
    "img_size": 416,         // 减小图片尺寸
    "batch_size": 32         // 增加批量大小（如果显存允许）
  }
}
```

### Q2: 模型精度不高怎么办？

**可能原因：**
- 数据量不足
- 标注质量差
- 训练轮数不够
- 模型太小

**解决方案：**
1. 增加数据量和数据增强
2. 检查并修正标注错误
3. 增加训练轮数（epochs）
4. 使用更大的模型（如 YOLOv8m 或 YOLOv8l）
5. 调整学习率和优化器

### Q3: 如何选择合适的模型？

| 场景 | 推荐模型 |
|------|---------|
| 实时检测（移动端） | YOLOv8n / YOLOv10n |
| 通用场景 | YOLOv8s / YOLOv10s |
| 高精度需求 | YOLOv8m / YOLOv8l |
| 最高精度 | YOLOv8x |
| 资源受限 | YOLOv9c |

### Q4: 数据集格式不对怎么办？

**格式转换工具：**
```bash
# COCO 转 YOLO
python scripts/convert_coco_to_yolo.py --input coco.json --output yolo/

# VOC 转 YOLO
python scripts/convert_voc_to_yolo.py --input voc/ --output yolo/
```

### Q5: 训练中断了怎么办？

**恢复训练：**
1. 系统会自动保存 checkpoint
2. 在创建训练时选择"继续训练"
3. 选择上次的 checkpoint 文件
4. 继续训练

### Q6: 如何部署训练好的模型？

**导出为 ONNX：**
```bash
# 通过 API 导出
curl -X POST http://localhost:8000/api/v1/models/{id}/export \
  -H "Authorization: Bearer token" \
  -d '{"format": "onnx"}'
```

**使用 ONNX Runtime 推理：**
```python
import onnxruntime as ort
import numpy as np

session = ort.InferenceSession("model.onnx")
results = session.run(None, {"images": input_tensor})
```

---

## 最佳实践

### 1. 数据集准备

- ✅ 确保标注质量
- ✅ 保持类别平衡
- ✅ 划分训练/验证/测试集
- ✅ 数据增强

### 2. 模型选择

- ✅ 根据场景选择合适大小的模型
- ✅ 先用小模型验证流程
- ✅ 再用大模型提升精度

### 3. 训练策略

- ✅ 使用预训练权重
- ✅ 启用混合精度训练
- ✅ 设置早停防止过拟合
- ✅ 定期保存 checkpoint

### 4. 模型评估

- ✅ 在测试集上评估
- ✅ 对比多个版本
- ✅ 关注实际场景效果
- ✅ 考虑推理速度

---

*最后更新：2026 年 6 月*
