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
- [模型对比接口](#模型对比接口)
- [模型部署接口](#模型部署接口)
- [超参搜索接口](#超参搜索接口)
- [团队管理接口](#团队管理接口)
- [活动日志接口](#活动日志接口)
- [监控接口](#监控接口)
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

## 模型对比接口

### POST /compare/models

创建模型对比任务。

**请求体：**
```json
{
  "name": "yolov8n vs yolov8s comparison",
  "model_ids": ["model-uuid-1", "model-uuid-2", "model-uuid-3"],
  "dataset_id": "dataset-uuid",
  "metrics": ["mAP50", "mAP50-95", "precision", "recall", "inference_time_ms"],
  "config": {
    "conf_threshold": 0.25,
    "iou_threshold": 0.45,
    "img_size": 640
  }
}
```

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 对比任务名称 |
| model_ids | string[] | 是 | 模型 ID 列表（至少 2 个） |
| dataset_id | string | 否 | 用于对比的测试数据集 ID |
| metrics | string[] | 否 | 要对比的指标列表 |
| config | object | 否 | 测试配置 |

**响应：**
```json
{
  "code": 201,
  "data": {
    "id": "compare-uuid",
    "name": "yolov8n vs yolov8s comparison",
    "model_ids": ["model-uuid-1", "model-uuid-2", "model-uuid-3"],
    "status": "pending",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### GET /compare/models/{id}

获取模型对比详情。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 对比任务 ID |

**响应：**
```json
{
  "code": 200,
  "data": {
    "id": "compare-uuid",
    "name": "yolov8n vs yolov8s comparison",
    "status": "completed",
    "models": [
      {
        "model_id": "model-uuid-1",
        "model_name": "yolov8n-coco-best",
        "metrics": {
          "mAP50": 0.523,
          "mAP50-95": 0.367,
          "precision": 0.589,
          "recall": 0.478,
          "inference_time_ms": 23.5
        }
      },
      {
        "model_id": "model-uuid-2",
        "model_name": "yolov8s-coco-best",
        "metrics": {
          "mAP50": 0.612,
          "mAP50-95": 0.445,
          "precision": 0.645,
          "recall": 0.534,
          "inference_time_ms": 35.2
        }
      }
    ],
    "ranking": {
      "mAP50": ["model-uuid-2", "model-uuid-1"],
      "inference_time_ms": ["model-uuid-1", "model-uuid-2"]
    },
    "created_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T00:05:00Z"
  }
}
```

### GET /compare/models

获取模型对比任务列表。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态筛选：pending/running/completed/failed |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应：**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "compare-uuid",
        "name": "yolov8n vs yolov8s comparison",
        "model_ids": ["model-uuid-1", "model-uuid-2"],
        "status": "completed",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 模型部署接口

### POST /deployments

创建模型部署。

**请求体：**
```json
{
  "name": "yolov8n-production-v1",
  "model_id": "model-uuid",
  "replicas": 2,
  "config": {
    "format": "onnx",
    "gpu_enabled": true,
    "max_batch_size": 8,
    "timeout_ms": 5000,
    "auto_scaling": {
      "enabled": true,
      "min_replicas": 1,
      "max_replicas": 5,
      "target_cpu_percent": 70
    }
  },
  "resources": {
    "cpu": "2",
    "memory": "4Gi",
    "gpu": "1"
  }
}
```

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 部署名称 |
| model_id | string | 是 | 模型 ID |
| replicas | int | 否 | 副本数（默认 1） |
| config | object | 否 | 部署配置 |
| resources | object | 否 | 资源配置 |

**响应：**
```json
{
  "code": 201,
  "data": {
    "id": "deployment-uuid",
    "name": "yolov8n-production-v1",
    "model_id": "model-uuid",
    "status": "deploying",
    "endpoint": null,
    "replicas": 2,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### GET /deployments

获取部署列表。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态筛选：deploying/running/stopped/failed |
| model_id | string | 否 | 模型 ID 筛选 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应：**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "deployment-uuid",
        "name": "yolov8n-production-v1",
        "model_id": "model-uuid",
        "status": "running",
        "endpoint": "https://api.example.com/deploy/deployment-uuid/predict",
        "replicas": 2,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 3,
    "page": 1,
    "page_size": 20
  }
}
```

### GET /deployments/{id}

获取部署详情。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 部署 ID |

**响应：**
```json
{
  "code": 200,
  "data": {
    "id": "deployment-uuid",
    "name": "yolov8n-production-v1",
    "model_id": "model-uuid",
    "model_name": "yolov8n-coco-best",
    "status": "running",
    "endpoint": "https://api.example.com/deploy/deployment-uuid/predict",
    "replicas": 2,
    "config": {
      "format": "onnx",
      "gpu_enabled": true,
      "max_batch_size": 8,
      "timeout_ms": 5000
    },
    "resources": {
      "cpu": "2",
      "memory": "4Gi",
      "gpu": "1"
    },
    "stats": {
      "total_requests": 12500,
      "avg_latency_ms": 45.3,
      "error_rate": 0.001,
      "uptime_hours": 120.5
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T01:00:00Z"
  }
}
```

### GET /deployments/{id}/status

获取部署状态和运行指标。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 部署 ID |

**响应：**
```json
{
  "code": 200,
  "data": {
    "id": "deployment-uuid",
    "status": "running",
    "replicas": {
      "desired": 2,
      "ready": 2,
      "available": 2
    },
    "metrics": {
      "requests_per_second": 15.3,
      "avg_latency_ms": 45.3,
      "p95_latency_ms": 78.2,
      "p99_latency_ms": 125.6,
      "error_rate": 0.001,
      "cpu_usage_percent": 45.2,
      "memory_usage_percent": 62.8
    },
    "last_health_check": "2024-01-01T01:00:00Z"
  }
}
```

### POST /deployments/{id}/stop

停止部署。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 部署 ID |

**响应：**
```json
{
  "code": 200,
  "message": "Deployment stopped successfully",
  "data": {
    "id": "deployment-uuid",
    "status": "stopped"
  }
}
```

---

## 超参搜索接口

### POST /hyperparameter/search

创建超参数搜索任务。

**请求体：**
```json
{
  "name": "yolov8n-hpo-search-001",
  "model_version": "yolov8n",
  "dataset_id": "dataset-uuid",
  "search_space": {
    "learning_rate": {
      "type": "float",
      "min": 0.001,
      "max": 0.1,
      "log": true
    },
    "batch_size": {
      "type": "choice",
      "values": [8, 16, 32]
    },
    "epochs": {
      "type": "int",
      "min": 50,
      "max": 200
    },
    "optimizer": {
      "type": "choice",
      "values": ["SGD", "Adam", "AdamW"]
    },
    "weight_decay": {
      "type": "float",
      "min": 0.0001,
      "max": 0.01
    }
  },
  "search_config": {
    "algorithm": "bayesian",
    "max_trials": 20,
    "max_concurrent": 3,
    "objective": "mAP50-95",
    "direction": "maximize",
    "early_stopping": {
      "enabled": true,
      "patience": 5,
      "min_delta": 0.001
    }
  }
}
```

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 搜索任务名称 |
| model_version | string | 是 | 模型版本 |
| dataset_id | string | 是 | 数据集 ID |
| search_space | object | 是 | 超参数搜索空间定义 |
| search_config | object | 是 | 搜索配置 |

**search_space 参数类型：**
- `float` - 连续浮点数范围
- `int` - 连续整数范围
- `choice` - 离散值列表

**search_config.algorithm 可选值：**
- `random` - 随机搜索
- `bayesian` - 贝叶斯优化
- `grid` - 网格搜索

**响应：**
```json
{
  "code": 201,
  "data": {
    "id": "hpo-uuid",
    "name": "yolov8n-hpo-search-001",
    "status": "pending",
    "max_trials": 20,
    "completed_trials": 0,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### GET /hyperparameter/search

获取超参数搜索任务列表。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态筛选：pending/running/completed/failed/cancelled |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应：**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "hpo-uuid",
        "name": "yolov8n-hpo-search-001",
        "model_version": "yolov8n",
        "status": "completed",
        "max_trials": 20,
        "completed_trials": 20,
        "best_trial": {
          "trial_id": "trial-uuid-15",
          "objective_value": 0.456
        },
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 3,
    "page": 1,
    "page_size": 20
  }
}
```

### GET /hyperparameter/search/{id}

获取超参数搜索详情。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 搜索任务 ID |

**响应：**
```json
{
  "code": 200,
  "data": {
    "id": "hpo-uuid",
    "name": "yolov8n-hpo-search-001",
    "model_version": "yolov8n",
    "dataset_id": "dataset-uuid",
    "status": "completed",
    "search_space": {
      "learning_rate": {"type": "float", "min": 0.001, "max": 0.1, "log": true},
      "batch_size": {"type": "choice", "values": [8, 16, 32]},
      "optimizer": {"type": "choice", "values": ["SGD", "Adam", "AdamW"]}
    },
    "search_config": {
      "algorithm": "bayesian",
      "max_trials": 20,
      "objective": "mAP50-95",
      "direction": "maximize"
    },
    "max_trials": 20,
    "completed_trials": 20,
    "best_params": {
      "learning_rate": 0.0052,
      "batch_size": 16,
      "optimizer": "AdamW",
      "weight_decay": 0.0023
    },
    "best_metrics": {
      "mAP50-95": 0.456,
      "mAP50": 0.612,
      "precision": 0.645,
      "recall": 0.534
    },
    "best_training_id": "training-uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-02T12:00:00Z"
  }
}
```

### GET /hyperparameter/search/{id}/trials

获取搜索任务的所有试验详情。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 搜索任务 ID |

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态筛选：running/completed/failed/pruned |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应：**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "trial_id": "trial-uuid-15",
        "trial_number": 15,
        "status": "completed",
        "params": {
          "learning_rate": 0.0052,
          "batch_size": 16,
          "optimizer": "AdamW",
          "weight_decay": 0.0023
        },
        "metrics": {
          "mAP50-95": 0.456,
          "mAP50": 0.612,
          "train_loss": 0.0234,
          "val_loss": 0.0312
        },
        "training_id": "training-uuid",
        "duration_seconds": 3600,
        "created_at": "2024-01-01T06:00:00Z",
        "completed_at": "2024-01-01T07:00:00Z"
      },
      {
        "trial_id": "trial-uuid-03",
        "trial_number": 3,
        "status": "pruned",
        "params": {
          "learning_rate": 0.08,
          "batch_size": 32,
          "optimizer": "SGD",
          "weight_decay": 0.0001
        },
        "metrics": {
          "mAP50-95": 0.123
        },
        "training_id": "training-uuid-2",
        "duration_seconds": 900,
        "created_at": "2024-01-01T01:00:00Z",
        "completed_at": "2024-01-01T01:15:00Z"
      }
    ],
    "total": 20,
    "page": 1,
    "page_size": 20
  }
}
```

### POST /hyperparameter/search/{id}/cancel

取消正在进行的搜索任务。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 搜索任务 ID |

**响应：**
```json
{
  "code": 200,
  "message": "Search cancelled successfully",
  "data": {
    "id": "hpo-uuid",
    "status": "cancelled",
    "completed_trials": 12
  }
}
```

---

## 团队管理接口

### POST /teams

创建团队。

**请求体：**
```json
{
  "name": "ML Research Team",
  "description": "负责模型训练和优化的研究团队"
}
```

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 团队名称 |
| description | string | 否 | 团队描述 |

**响应：**
```json
{
  "code": 201,
  "data": {
    "id": "team-uuid",
    "name": "ML Research Team",
    "description": "负责模型训练和优化的研究团队",
    "owner_id": "user-uuid",
    "member_count": 1,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### GET /teams

获取团队列表。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应：**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "team-uuid",
        "name": "ML Research Team",
        "description": "负责模型训练和优化的研究团队",
        "owner_id": "user-uuid",
        "member_count": 5,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 2,
    "page": 1,
    "page_size": 20
  }
}
```

### GET /teams/{id}

获取团队详情。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 团队 ID |

**响应：**
```json
{
  "code": 200,
  "data": {
    "id": "team-uuid",
    "name": "ML Research Team",
    "description": "负责模型训练和优化的研究团队",
    "owner_id": "user-uuid",
    "members": [
      {
        "user_id": "user-uuid-1",
        "username": "alice",
        "email": "alice@example.com",
        "role": "owner",
        "joined_at": "2024-01-01T00:00:00Z"
      },
      {
        "user_id": "user-uuid-2",
        "username": "bob",
        "email": "bob@example.com",
        "role": "member",
        "joined_at": "2024-01-02T00:00:00Z"
      }
    ],
    "member_count": 5,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-05T00:00:00Z"
  }
}
```

### POST /teams/{id}/members

添加团队成员。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 团队 ID |

**请求体：**
```json
{
  "user_id": "user-uuid-new",
  "role": "member"
}
```

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户 ID |
| role | string | 否 | 角色：admin/member（默认 member） |

**响应：**
```json
{
  "code": 200,
  "message": "Member added successfully",
  "data": {
    "team_id": "team-uuid",
    "user_id": "user-uuid-new",
    "role": "member",
    "joined_at": "2024-01-06T00:00:00Z"
  }
}
```

### DELETE /teams/{id}/members/{user_id}

移除团队成员。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 团队 ID |
| user_id | string | 用户 ID |

**响应：**
```json
{
  "code": 200,
  "message": "Member removed successfully"
}
```

---

## 活动日志接口

### GET /activities

获取活动日志列表。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 否 | 用户 ID 筛选 |
| action | string | 否 | 操作类型筛选：create/update/delete/start/stop |
| resource_type | string | 否 | 资源类型筛选：training/model/dataset/deployment/team |
| resource_id | string | 否 | 资源 ID 筛选 |
| start_date | string | 否 | 开始日期（ISO 8601 格式） |
| end_date | string | 否 | 结束日期（ISO 8601 格式） |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应：**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "activity-uuid",
        "user_id": "user-uuid",
        "username": "alice",
        "action": "create",
        "resource_type": "training",
        "resource_id": "training-uuid",
        "resource_name": "yolov8n-coco-2024",
        "detail": {
          "model_version": "yolov8n",
          "epochs": 100
        },
        "ip_address": "192.168.1.100",
        "created_at": "2024-01-01T00:00:00Z"
      },
      {
        "id": "activity-uuid-2",
        "user_id": "user-uuid",
        "username": "alice",
        "action": "start",
        "resource_type": "deployment",
        "resource_id": "deployment-uuid",
        "resource_name": "yolov8n-production-v1",
        "detail": {
          "replicas": 2
        },
        "ip_address": "192.168.1.100",
        "created_at": "2024-01-01T01:00:00Z"
      }
    ],
    "total": 150,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 监控接口

### GET /metrics

获取系统指标（Prometheus 格式）。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| format | string | 否 | 返回格式：prometheus/json（默认 prometheus） |

**响应（Prometheus 格式）：**
```
# HELP yolo_trainer_training_tasks_total Total number of training tasks
# TYPE yolo_trainer_training_tasks_total counter
yolo_trainer_training_tasks_total{status="completed"} 150
yolo_trainer_training_tasks_total{status="failed"} 5
yolo_trainer_training_tasks_total{status="running"} 3

# HELP yolo_trainer_active_deployments Number of active deployments
# TYPE yolo_trainer_active_deployments gauge
yolo_trainer_active_deployments 8

# HELP yolo_trainer_api_request_duration_seconds API request duration
# TYPE yolo_trainer_api_request_duration_seconds histogram
yolo_trainer_api_request_duration_seconds_bucket{le="0.01"} 1000
yolo_trainer_api_request_duration_seconds_bucket{le="0.05"} 5000
yolo_trainer_api_request_duration_seconds_bucket{le="0.1"} 8000
yolo_trainer_api_request_duration_seconds_bucket{le="+Inf"} 10000
```

**响应（JSON 格式）：**
```json
{
  "code": 200,
  "data": {
    "system": {
      "cpu_usage_percent": 45.2,
      "memory_usage_percent": 62.8,
      "disk_usage_percent": 35.4,
      "gpu_usage_percent": 78.5,
      "gpu_memory_usage_percent": 55.3
    },
    "tasks": {
      "total_trainings": 158,
      "active_trainings": 3,
      "completed_trainings": 150,
      "failed_trainings": 5
    },
    "deployments": {
      "total": 10,
      "active": 8,
      "stopped": 2
    },
    "api": {
      "total_requests": 50000,
      "avg_response_time_ms": 45.3,
      "error_rate": 0.002,
      "requests_per_second": 15.3
    },
    "collected_at": "2024-01-01T12:00:00Z"
  }
}
```

### GET /health

健康检查接口。

**响应：**
```json
{
  "code": 200,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime_seconds": 864000,
    "services": {
      "database": {
        "status": "healthy",
        "latency_ms": 2.5
      },
      "redis": {
        "status": "healthy",
        "latency_ms": 0.8
      },
      "storage": {
        "status": "healthy",
        "latency_ms": 15.2
      },
      "gpu": {
        "status": "healthy",
        "devices": 2,
        "available": 2
      }
    },
    "checked_at": "2024-01-01T12:00:00Z"
  }
}
```

**健康状态说明：**

| 状态 | 说明 |
|------|------|
| healthy | 所有服务正常 |
| degraded | 部分服务异常，系统可继续运行 |
| unhealthy | 关键服务不可用 |

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
