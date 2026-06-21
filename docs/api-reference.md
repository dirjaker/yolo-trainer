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
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### 请求头

```http
Content-Type: application/json
Authorization: Bearer <access_token>
```

### 分页参数

大部分列表接口支持分页：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码（≥1） |
| page_size | int | 20 | 每页数量（1-100） |

**分页响应格式：**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

## 认证

### POST /auth/register

用户注册。

**请求体：**
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

**响应：** `201 Created`
```json
{
  "id": "uuid",
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "created_at": "2026-01-01T00:00:00Z"
}
```

### POST /auth/login

用户登录，返回 JWT access token。

**请求体：**
```json
{
  "username": "testuser",
  "password": "password123"
}
```

**响应：** `200 OK`
```json
{
  "access_token": "eyJhbG...VCJ9...",
  "token_type": "bearer"
}
```

---

## 训练接口

### POST /training/

创建训练任务。任务创建后自动提交到 Celery 异步队列。

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
    "device": "0",
    "workers": 8,
    "patience": 50
  }
}
```

**响应：** `201 Created`
```json
{
  "id": "training-uuid",
  "name": "yolov8n-coco-2024",
  "model_version": "yolov8n",
  "dataset_id": "dataset-uuid",
  "status": "pending",
  "config": { ... },
  "progress": 0.0,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

### GET /training/

获取训练任务列表（当前用户的任务）。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态筛选：pending/queued/running/completed/failed/cancelled |
| model_version | string | 否 | 模型版本筛选 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

### GET /training/{training_id}

获取训练任务详情。

### POST /training/{training_id}/stop

停止训练任务（仅 pending/queued/running 状态可停止）。

### GET /training/{training_id}/logs

获取训练日志。

### GET /training/{training_id}/metrics

获取训练指标（用于前端绘图）。

**响应：**
```json
{
  "training_id": "uuid",
  "status": "completed",
  "progress": 100.0,
  "metrics": {
    "mAP50": 0.523,
    "mAP50-95": 0.367,
    "precision": 0.589,
    "recall": 0.478
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
| model_version | string | 否 | 模型架构版本筛选（yolov8n 等） |
| tags | string[] | 否 | 标签筛选 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

### GET /models/{model_id}

获取模型详情。

**响应：**
```json
{
  "id": "model-uuid",
  "training_id": "training-uuid",
  "name": "yolov8n-coco-best",
  "version": "1.0.0",
  "model_version": "yolov8n",
  "description": null,
  "file_path": "/models/uuid/weights/best.pt",
  "file_size": 12582912,
  "metrics": {
    "mAP50": 0.523,
    "mAP50-95": 0.367
  },
  "tags": ["production", "v1.0"],
  "created_at": "2026-01-01T02:30:00Z"
}
```

### POST /models/{model_id}/export

导出模型为指定格式（异步任务）。

**请求体：**
```json
{
  "format": "onnx",
  "img_size": 640,
  "simplify": true,
  "dynamic": false
}
```

**支持的格式：** `onnx`、`torchscript`、`tensorrt`、`coreml`、`tflite`、`paddle`

### POST /models/{model_id}/tags

为模型添加标签。

**请求体：**
```json
["production", "v1.0", "best"]
```

### GET /models/{model_id}/versions

获取同名模型的所有版本历史。

### GET /models/{model_id}/download

下载模型文件（`application/octet-stream`）。

### DELETE /models/{model_id}

删除模型及其文件（`204 No Content`）。

---

## 数据集接口

### POST /datasets/upload

上传数据集（`multipart/form-data`）。

**表单字段：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | ZIP 压缩包 |
| name | string | 是 | 数据集名称 |
| description | string | 否 | 描述 |
| format | string | 否 | 格式（yolo/coco/voc），默认 yolo |

**响应：** `201 Created`
```json
{
  "id": "dataset-uuid",
  "name": "my-dataset",
  "format": "yolo",
  "status": "uploading",
  "created_at": "2026-01-01T00:00:00Z"
}
```

### GET /datasets

获取数据集列表（当前用户）。

### GET /datasets/{dataset_id}

获取数据集详情。

### DELETE /datasets/{dataset_id}

删除数据集及其文件。

---

## 测试接口

### POST /test/predict

单图推理预测。

**请求：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 待检测图片 |
| model_id | UUID | 是 | 查询参数，模型 ID |
| confidence | float | 否 | 置信度阈值（0-1），默认 0.25 |

**响应：**
```json
{
  "test_id": "uuid",
  "model_id": "model-uuid",
  "detections": [
    {
      "class_name": "person",
      "class_id": 0,
      "confidence": 0.923,
      "bbox": {
        "x1": 100.0,
        "y1": 150.0,
        "x2": 300.0,
        "y2": 400.0
      }
    }
  ],
  "inference_time_ms": 23.5
}
```

### POST /test/batch

批量推理预测。

**请求：** `multipart/form-data`，files 为多文件字段。

**响应：**
```json
{
  "batch_id": "uuid",
  "total": 5,
  "results": [ ... ]
}
```

### GET /test/{test_id}/results

获取测试结果。

### GET /test/{test_id}/result-image

获取带检测框的结果图片（`image/png`）。

---

## 模型对比接口

### POST /compare/

创建模型对比任务。

**请求体：**
```json
{
  "model_ids": ["model-uuid-1", "model-uuid-2"],
  "test_dataset_id": "dataset-uuid",
  "name": "yolov8n vs yolov8s"
}
```

### GET /compare/{compare_id}

获取对比结果。

### GET /compare/

获取对比任务列表。

---

## 模型部署接口

### POST /deployments/

创建部署任务。

**请求体：**
```json
{
  "model_id": "model-uuid",
  "name": "my-deployment",
  "config": {
    "platform": "onnx_runtime",
    "port": 8080,
    "workers": 4,
    "batch_size": 1,
    "gpu": true
  }
}
```

### GET /deployments/

获取部署列表。

**查询参数：** `status`（pending/deploying/running/stopped/failed）、`platform`

### GET /deployments/{deploy_id}

获取部署详情。

### GET /deployments/{deploy_id}/status

获取部署运行状态（健康、运行时长、请求计数、平均延迟）。

### POST /deployments/{deploy_id}/stop

停止部署。

---

## 超参搜索接口

### POST /hyperparameter/search

创建超参搜索任务。

**请求体：**
```json
{
  "name": "lr-search-001",
  "model_version": "yolov8n",
  "dataset_id": "dataset-uuid",
  "search_space": {
    "learning_rate": { "type": "log_uniform", "min": 0.0001, "max": 0.1 },
    "batch_size": { "type": "choice", "values": [8, 16, 32] }
  },
  "search_config": {
    "method": "bayesian",
    "n_trials": 30
  },
  "base_config": {
    "epochs": 50,
    "img_size": 640
  }
}
```

### GET /hyperparameter/search

获取搜索任务列表。

### GET /hyperparameter/search/{search_id}

获取搜索详情（含最优参数和最佳指标）。

### GET /hyperparameter/search/{search_id}/trials

获取搜索任务的所有试验结果。

### POST /hyperparameter/search/{search_id}/cancel

取消搜索任务（仅 pending/running 状态可取消）。

---

## 团队管理接口

### POST /teams/teams

创建团队（当前用户成为 owner）。

**请求体：**
```json
{
  "name": "ML Team",
  "description": "机器学习团队"
}
```

### GET /teams/teams

获取当前用户所属的团队列表。

### GET /teams/teams/{team_id}

获取团队详情。

### PATCH /teams/teams/{team_id}

更新团队信息（仅 owner）。

### POST /teams/teams/{team_id}/members

添加团队成员（仅 owner）。

**请求体：**
```json
{
  "user_id": "user-uuid",
  "role": "member"
}
```

### DELETE /teams/teams/{team_id}/members/{user_id}

移除团队成员（仅 owner）。

---

## 活动日志接口

### GET /activities/activities

获取活动日志列表。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | UUID | 否 | 按用户筛选 |
| resource_type | string | 否 | 按资源类型筛选 |
| start_date | datetime | 否 | 起始时间 |
| end_date | datetime | 否 | 截止时间 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

---

## 监控接口

### GET /health

健康检查。

### GET /metrics

Prometheus 格式的 API 请求指标。

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无内容） |
| 400 | 请求参数错误 |
| 401 | 未认证（Token 缺失或过期） |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 422 | 请求体校验失败 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用（如推理引擎未安装） |

**错误响应格式：**
```json
{
  "detail": "错误描述信息"
}
```

---

*完整的交互式 API 文档请访问 `http://localhost:8000/docs`（Swagger UI）。*
