# API 参考文档

> YOLO Trainer REST API 完整参考

---

## 📋 目录

- [概述](#概述)
- [认证](#认证)
- [训练接口](#训练接口)
- [模型接口](#模型接口)
- [数据集接口](#数据集接口)
- [测试接口](#测试接口)
- [错误码](#错误码)

---

## 概述

### 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token (JWT)
- **数据格式**: JSON
- **字符编码**: UTF-8

### 请求头

```http
Content-Type: application/json
Authorization: Bearer <your-token>
```

### 响应格式

**成功响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

**错误响应：**
```json
{
  "code": 400,
  "message": "Error message",
  "detail": "Detailed error information"
}
```

### 分页参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |

**分页响应：**
```json
{
  "code": 200,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "pages": 5
  }
}
```

---

## 认证

### POST /auth/login

用户登录，获取访问令牌。

**请求体：**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### POST /auth/register

用户注册。

**请求体：**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**响应：**
```json
{
  "code": 201,
  "message": "User created successfully",
  "data": {
    "id": "uuid",
    "username": "string",
    "email": "string"
  }
}
```

---

## 训练接口

### POST /trainings

创建训练任务。

**请求体：**
```json
{
  "name": "yolov8n-coco-2024",
  "model_version": "yolov8n",
  "dataset_id": "dataset-uuid",
  "config": {
    "epochs": 100,
    "batch_size": 16,
    "img_size": 640,
    "learning_rate": 0.01,
    "optimizer": "Adam",
    "device": "0",
    "workers": 8,
    "patience": 50,
    "save_period": 10
  }
}
```

**响应：**
```json
{
  "code": 201,
  "data": {
    "id": "training-uuid",
    "name": "yolov8n-coco-2024",
    "model_version": "yolov8n",
    "status": "pending",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### GET /trainings

获取训练任务列表。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态筛选：pending/running/completed/failed |
| model_version | string | 否 | 模型版本筛选 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应：**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "training-uuid",
        "name": "yolov8n-coco-2024",
        "model_version": "yolov8n",
        "status": "completed",
        "progress": 100,
        "metrics": {
          "mAP50": 0.523,
          "mAP50-95": 0.367,
          "precision": 0.589,
          "recall": 0.478
        },
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
  }
}
```

### GET /trainings/{training_id}

获取训练任务详情。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| training_id | string | 训练任务 ID |

**响应：**
```json
{
  "code": 200,
  "data": {
    "id": "training-uuid",
    "name": "yolov8n-coco-2024",
    "model_version": "yolov8n",
    "dataset_id": "dataset-uuid",
    "status": "completed",
    "config": {
      "epochs": 100,
      "batch_size": 16,
      "img_size": 640
    },
    "metrics": {
      "mAP50": 0.523,
      "mAP50-95": 0.367,
      "precision": 0.589,
      "recall": 0.478,
      "train_loss": 0.0234,
      "val_loss": 0.0312
    },
    "model_id": "model-uuid",
    "started_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T02:30:00Z",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### POST /trainings/{training_id}/stop

停止训练任务。

**响应：**
```json
{
  "code": 200,
  "message": "Training stopped successfully"
}
```

### GET /trainings/{training_id}/logs

获取训练日志（流式）。

**响应：**
```json
{
  "code": 200,
  "data": {
    "logs": [
      {
        "timestamp": "2024-01-01T00:01:00Z",
        "level": "info",
        "message": "Epoch 1/100: loss=0.0523, mAP50=0.123"
      },
      ...
    ]
  }
}
```

### GET /trainings/{training_id}/metrics

获取训练指标历史（用于绘图）。

**响应：**
```json
{
  "code": 200,
  "data": {
    "epochs": [1, 2, 3, ...],
    "train_loss": [0.0523, 0.0412, 0.0356, ...],
    "val_loss": [0.0612, 0.0523, 0.0445, ...],
    "mAP50": [0.123, 0.234, 0.345, ...],
    "mAP50-95": [0.089, 0.167, 0.234, ...],
    "precision": [0.234, 0.345, 0.456, ...],
    "recall": [0.189, 0.278, 0.367, ...]
  }
}
```

---

## 模型接口

### GET /models

获取模型列表。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model_version | string | 否 | 模型版本筛选 |
| tags | string | 否 | 标签筛选（逗号分隔） |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应：**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "model-uuid",
        "name": "yolov8n-coco-best",
        "version": "1.0.0",
        "model_version": "yolov8n",
        "training_id": "training-uuid",
        "metrics": {
          "mAP50": 0.523,
          "mAP50-95": 0.367
        },
        "tags": ["production", "v1.0"],
        "file_size": 12582912,
        "created_at": "2024-01-01T02:30:00Z"
      }
    ],
    "total": 25,
    "page": 1,
    "page_size": 20
  }
}
```

### GET /models/{model_id}

获取模型详情。

**响应：**
```json
{
  "code": 200,
  "data": {
    "id": "model-uuid",
    "name": "yolov8n-coco-best",
    "version": "1.0.0",
    "model_version": "yolov8n",
    "training_id": "training-uuid",
    "description": "YOLOv8n trained on COCO dataset",
    "config": {
      "img_size": 640,
      "num_classes": 80,
      "class_names": ["person", "bicycle", "car", ...]
    },
    "metrics": {
      "mAP50": 0.523,
      "mAP50-95": 0.367,
      "precision": 0.589,
      "recall": 0.478,
      "inference_time_ms": 23.5
    },
    "tags": ["production", "v1.0"],
    "file_path": "models/model-uuid/weights/best.pt",
    "file_size": 12582912,
    "created_at": "2024-01-01T02:30:00Z"
  }
}
```

### POST /models/{model_id}/export

导出模型为其他格式。

**请求体：**
```json
{
  "format": "onnx",
  "img_size": 640,
  "simplify": true,
  "dynamic": false
}
```

**支持的格式：**
- `onnx` - ONNX 格式
- `torchscript` - TorchScript 格式
- `tensorrt` - TensorRT 格式
- `coreml` - CoreML 格式
- `tflite` - TensorFlow Lite 格式
- `paddle` - PaddlePaddle 格式

**响应：**
```json
{
  "code": 200,
  "data": {
    "export_id": "export-uuid",
    "format": "onnx",
    "file_path": "models/model-uuid/exports/best.onnx",
    "file_size": 12582912,
    "status": "completed"
  }
}
```

### POST /models/{model_id}/tags

为模型添加标签。

**请求体：**
```json
{
  "tags": ["production", "v1.0", "best"]
}
```

**响应：**
```json
{
  "code": 200,
  "message": "Tags added successfully",
  "data": {
    "tags": ["production", "v1.0", "best"]
  }
}
```

### GET /models/{model_id}/versions

获取模型版本历史。

**响应：**
```json
{
  "code": 200,
  "data": {
    "versions": [
      {
        "version": "1.2.0",
        "created_at": "2024-01-15T00:00:00Z",
        "metrics": {"mAP50": 0.567},
        "tags": ["production"]
      },
      {
        "version": "1.1.0",
        "created_at": "2024-01-10T00:00:00Z",
        "metrics": {"mAP50": 0.534},
        "tags": ["staging"]
      },
      {
        "version": "1.0.0",
        "created_at": "2024-01-01T00:00:00Z",
        "metrics": {"mAP50": 0.523},
        "tags": ["archive"]
      }
    ]
  }
}
```

### GET /models/{model_id}/download

下载模型文件。

**响应：**
- Content-Type: `application/octet-stream`
- 文件流

### DELETE /models/{model_id}

删除模型。

**响应：**
```json
{
  "code": 200,
  "message": "Model deleted successfully"
}
```

---

## 数据集接口

### POST /datasets/upload

上传数据集。

**请求：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 数据集文件（ZIP 格式） |
| name | string | 是 | 数据集名称 |
| format | string | 是 | 数据格式：coco/voc/yolo |
| description | string | 否 | 描述 |

**响应：**
```json
{
  "code": 201,
  "data": {
    "id": "dataset-uuid",
    "name": "my-dataset",
    "format": "yolo",
    "status": "processing",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### GET /datasets

获取数据集列表。

**响应：**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "dataset-uuid",
        "name": "my-dataset",
        "format": "yolo",
        "classes": ["person", "car", "dog"],
        "stats": {
          "total_images": 1000,
          "total_annotations": 5000,
          "class_distribution": {
            "person": 2000,
            "car": 2000,
            "dog": 1000
          }
        },
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

### GET /datasets/{dataset_id}

获取数据集详情。

**响应：**
```json
{
  "code": 200,
  "data": {
    "id": "dataset-uuid",
    "name": "my-dataset",
    "format": "yolo",
    "description": "My custom dataset",
    "classes": ["person", "car", "dog"],
    "stats": {
      "total_images": 1000,
      "total_annotations": 5000,
      "train_images": 700,
      "val_images": 200,
      "test_images": 100,
      "class_distribution": {
        "person": 2000,
        "car": 2000,
        "dog": 1000
      }
    },
    "file_path": "datasets/dataset-uuid/dataset.yaml",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### DELETE /datasets/{dataset_id}

删除数据集。

**响应：**
```json
{
  "code": 200,
  "message": "Dataset deleted successfully"
}
```

---

## 测试接口

### POST /tests/predict

单图预测。

**请求：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| image | file | 是 | 图片文件 |
| model_id | string | 是 | 模型 ID |
| conf_threshold | float | 否 | 置信度阈值（默认 0.25） |
| iou_threshold | float | 否 | IoU 阈值（默认 0.45） |

**响应：**
```json
{
  "code": 200,
  "data": {
    "test_id": "test-uuid",
    "model_id": "model-uuid",
    "image_info": {
      "width": 640,
      "height": 480
    },
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
      },
      {
        "class": "car",
        "class_id": 2,
        "confidence": 0.867,
        "bbox": {
          "x1": 350,
          "y1": 200,
          "x2": 550,
          "y2": 380
        }
      }
    ],
    "result_image_url": "/api/v1/tests/test-uuid/result-image",
    "inference_time_ms": 23.5
  }
}
```

### POST /tests/batch

批量预测。

**请求：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| images | file[] | 是 | 图片文件列表 |
| model_id | string | 是 | 模型 ID |
| conf_threshold | float | 否 | 置信度阈值 |
| iou_threshold | float | 否 | IoU 阈值 |

**响应：**
```json
{
  "code": 200,
  "data": {
    "batch_id": "batch-uuid",
    "total_images": 10,
    "results": [
      {
        "image_name": "image1.jpg",
        "detections": [...],
        "inference_time_ms": 23.5
      },
      ...
    ],
    "summary": {
      "total_detections": 45,
      "avg_inference_time_ms": 24.2,
      "class_counts": {
        "person": 20,
        "car": 15,
        "dog": 10
      }
    }
  }
}
```

### GET /tests/{test_id}/results

获取测试结果。

**响应：**
```json
{
  "code": 200,
  "data": {
    "test_id": "test-uuid",
    "status": "completed",
    "results": {...}
  }
}
```

### GET /tests/{test_id}/result-image

获取结果图片（带检测框）。

**响应：**
- Content-Type: `image/jpeg`
- 图片流

---

## 错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

### 错误响应示例

**400 Bad Request:**
```json
{
  "code": 400,
  "message": "Validation error",
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**404 Not Found:**
```json
{
  "code": 404,
  "message": "Training not found",
  "detail": "Training with id 'xxx' does not exist"
}
```

**500 Internal Server Error:**
```json
{
  "code": 500,
  "message": "Internal server error",
  "detail": "An unexpected error occurred"
}
```

---

## WebSocket 接口

### 训练进度实时推送

**连接地址：** `ws://localhost:8000/ws/trainings/{training_id}`

**消息格式：**
```json
{
  "type": "progress",
  "data": {
    "epoch": 50,
    "total_epochs": 100,
    "progress": 50,
    "metrics": {
      "train_loss": 0.0234,
      "val_loss": 0.0312,
      "mAP50": 0.456
    },
    "eta_seconds": 3600
  }
}
```

**消息类型：**
- `progress` - 训练进度
- `log` - 训练日志
- `completed` - 训练完成
- `failed` - 训练失败

---

*最后更新：2026 年 6 月*
