# YOLO Trainer API 参考文档

> 基于 YOLO 的目标检测模型训练平台 REST API 完整接口文档

---

## 目录

1. [基础信息](#1-基础信息)
2. [认证模块](#2-认证模块)
3. [训练管理](#3-训练管理)
4. [模型管理](#4-模型管理)
5. [数据集管理](#5-数据集管理)
6. [测试中心](#6-测试中心)
7. [模型对比](#7-模型对比)
8. [模型部署](#8-模型部署)
9. [超参搜索](#9-超参搜索)
10. [团队管理](#10-团队管理)
11. [活动日志](#11-活动日志)

---

## 1. 基础信息

| 项目 | 说明 |
|------|------|
| **Base URL** | `http://localhost:10003/api/v1` |
| **认证方式** | Bearer Token（JWT） |
| **Content-Type** | `application/json`（除文件上传外） |
| **响应格式** | JSON |
| **HTTP 方法** | GET / POST / PUT / PATCH / DELETE |

### 通用请求头

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 通用分页响应格式

分页接口统一返回以下结构：

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### 通用错误响应

```json
{
  "detail": "错误描述信息"
}
```

常见 HTTP 状态码：

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无响应体） |
| 400 | 请求参数错误 |
| 401 | 未认证 / Token 无效 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 413 | 上传文件过大 |
| 422 | 请求体验证失败 |
| 500 | 服务器内部错误 |
| 503 | 服务暂不可用 |

### 限流说明

| 接口 | 限制 |
|------|------|
| 注册 (`/auth/register`) | 每 IP 每小时 5 次 |
| 登录 (`/auth/login`) | 每 IP 每 5 分钟 10 次 |

---

## 2. 认证模块

### 2.1 用户注册

```http
POST /api/v1/auth/register
```

**请求参数（JSON Body）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | string | ✅ | 用户名，3–50 字符，仅允许字母/数字/下划线/连字符 |
| `email` | string | ✅ | 邮箱地址 |
| `password` | string | ✅ | 密码，8–128 字符 |

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo3",
    "email": "demo3@example.com",
    "password": "demo12345678"
  }'
```

**响应示例（201 Created）**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "demo3",
  "email": "demo3@example.com",
  "is_active": true,
  "created_at": "2024-01-15T08:30:00.000000Z"
}
```

**错误响应**

| 状态码 | detail |
|--------|--------|
| 400 | `用户名已被注册` |
| 400 | `邮箱已被注册` |

---

### 2.2 用户登录

```http
POST /api/v1/auth/login
```

**请求参数（JSON Body）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | string | ✅ | 用户名 |
| `password` | string | ✅ | 密码 |

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo3",
    "password": "demo123"
  }'
```

**响应示例（200 OK）**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

> 后续所有需要认证的请求，均在 `Authorization` 头中携带：
> ```
> Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
> ```

**错误响应**

| 状态码 | detail |
|--------|--------|
| 401 | `用户名或密码错误` |
| 403 | `用户已被禁用` |

---

## 3. 训练管理

### 3.1 创建训练任务

```http
POST /api/v1/trainings/
```

**请求参数（JSON Body）**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | string | ✅ | — | 训练任务名称（1–200 字符） |
| `model_version` | string | ❌ | `yolov8n` | YOLO 版本，见下方可选值 |
| `dataset_id` | UUID | ✅ | — | 数据集 ID |
| `config` | object | ❌ | `null` | 训练配置（见子字段） |

**`model_version` 可选值**

```
yolov5n, yolov5s, yolov5m, yolov5l, yolov5x,
yolov8n, yolov8s, yolov8m, yolov8l, yolov8x,
yolov9t, yolov9s, yolov9m, yolov9c, yolov9e,
yolov10n, yolov10s, yolov10m, yolov10b, yolov10l, yolov10x
```

**`config` 子字段**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `epochs` | int | 100 | 训练轮数（1–10000） |
| `batch_size` | int | 16 | 批次大小（1–512） |
| `img_size` | int | 640 | 输入图像尺寸（32–4096） |
| `learning_rate` | float | 0.01 | 初始学习率（>0, ≤1.0） |
| `optimizer` | string | `SGD` | 优化器（SGD, Adam, AdamW 等） |
| `device` | string | `0` | 训练设备（cpu, 0, 0,1 等） |
| `workers` | int | 8 | 数据加载线程数（0–32） |
| `patience` | int | 50 | 早停耐心值（0–1000） |
| `amp` | bool | true | 是否使用自动混合精度 |

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/trainings/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "行人检测训练-v1",
    "model_version": "yolov8n",
    "dataset_id": "550e8400-e29b-41d4-a716-446655440001",
    "config": {
      "epochs": 100,
      "batch_size": 16,
      "img_size": 640,
      "learning_rate": 0.01,
      "optimizer": "SGD",
      "device": "0",
      "workers": 8
    }
  }'
```

**响应示例（201 Created）**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440002",
  "name": "行人检测训练-v1",
  "model_version": "yolov8n",
  "dataset_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "pending",
  "config": {
    "epochs": 100,
    "batch_size": 16,
    "img_size": 640,
    "learning_rate": 0.01,
    "optimizer": "SGD",
    "device": "0",
    "workers": 8,
    "patience": 50,
    "amp": true
  },
  "metrics": null,
  "progress": 0.0,
  "started_at": null,
  "completed_at": null,
  "created_at": "2024-01-15T09:00:00.000000Z"
}
```

**训练状态说明**

| 状态 | 说明 |
|------|------|
| `pending` | 等待中 |
| `running` | 训练中 |
| `completed` | 已完成 |
| `failed` | 失败 |
| `cancelled` | 已取消 |

---

### 3.2 获取训练任务列表

```http
GET /api/v1/trainings/
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `status` | string | ❌ | — | 按状态筛选 |
| `model_version` | string | ❌ | — | 按模型版本筛选 |
| `page` | int | ❌ | 1 | 页码（≥1） |
| `page_size` | int | ❌ | 20 | 每页数量（1–100） |

**请求示例**

```bash
# 获取所有训练任务
curl -X GET "http://localhost:10003/api/v1/trainings/" \
  -H "Authorization: Bearer <token>"

# 筛选运行中的任务
curl -X GET "http://localhost:10003/api/v1/trainings/?status=running&page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440002",
      "name": "行人检测训练-v1",
      "model_version": "yolov8n",
      "dataset_id": "550e8400-e29b-41d4-a716-446655440001",
      "status": "running",
      "config": { "epochs": 100, "batch_size": 16 },
      "metrics": null,
      "progress": 45.5,
      "started_at": "2024-01-15T09:05:00.000000Z",
      "completed_at": null,
      "created_at": "2024-01-15T09:00:00.000000Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 3.3 获取训练任务详情

```http
GET /api/v1/trainings/{training_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `training_id` | UUID | 训练任务 ID |

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/trainings/660e8400-e29b-41d4-a716-446655440002 \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440002",
  "name": "行人检测训练-v1",
  "model_version": "yolov8n",
  "dataset_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "running",
  "config": { "epochs": 100, "batch_size": 16 },
  "metrics": {
    "mAP50": 0.785,
    "mAP50-95": 0.562,
    "precision": 0.823,
    "recall": 0.741
  },
  "progress": 45.5,
  "started_at": "2024-01-15T09:05:00.000000Z",
  "completed_at": null,
  "created_at": "2024-01-15T09:00:00.000000Z"
}
```

**错误响应**

| 状态码 | detail |
|--------|--------|
| 404 | `训练任务不存在` |

---

### 3.4 停止训练任务

```http
POST /api/v1/trainings/{training_id}/stop
```

**说明**：仅可停止状态为 `pending`、`running` 的训练任务。

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/trainings/660e8400-e29b-41d4-a716-446655440002/stop \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440002",
  "name": "行人检测训练-v1",
  "status": "cancelled",
  ...
}
```

**错误响应**

| 状态码 | detail |
|--------|--------|
| 404 | `训练任务不存在` |
| 400 | `无法停止状态为 completed 的训练任务` |

---

### 3.5 获取训练指标

```http
GET /api/v1/trainings/{training_id}/metrics
```

**说明**：获取训练过程中的实时指标数据，用于前端绘制训练曲线。

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/trainings/660e8400-e29b-41d4-a716-446655440002/metrics \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "training_id": "660e8400-e29b-41d4-a716-446655440002",
  "status": "running",
  "progress": 45.5,
  "metrics": {
    "mAP50": 0.785,
    "mAP50-95": 0.562,
    "precision": 0.823,
    "recall": 0.741,
    "box_loss": 0.034,
    "cls_loss": 0.012,
    "dfl_loss": 0.025
  }
}
```

---

### 3.6 获取训练日志（附加）

```http
GET /api/v1/trainings/{training_id}/logs
```

**说明**：获取训练任务最近 200 行实时日志。

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/trainings/660e8400-e29b-41d4-a716-446655440002/logs \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "training_id": "660e8400-e29b-41d4-a716-446655440002",
  "logs": [
    "Epoch 1/100: loss=2.345, mAP=0.123",
    "Epoch 2/100: loss=1.876, mAP=0.234",
    "..."
  ]
}
```

---

## 4. 模型管理

### 4.1 获取模型列表

```http
GET /api/v1/models/
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `model_version` | string | ❌ | — | 按模型架构版本筛选（如 `yolov8n`） |
| `tags` | string[] | ❌ | — | 按标签筛选（可多个） |
| `page` | int | ❌ | 1 | 页码 |
| `page_size` | int | ❌ | 20 | 每页数量（1–100） |

**请求示例**

```bash
# 获取所有模型
curl -X GET "http://localhost:10003/api/v1/models/" \
  -H "Authorization: Bearer <token>"

# 筛选 yolov8n 且有 production 标签的模型
curl -X GET "http://localhost:10003/api/v1/models/?model_version=yolov8n&tags=production&tags=verified" \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440003",
      "training_id": "660e8400-e29b-41d4-a716-446655440002",
      "name": "行人检测模型",
      "version": "v1.0",
      "model_version": "yolov8n",
      "description": "行人检测模型 - 首版训练",
      "file_size": 6234128,
      "metrics": {
        "mAP50": 0.785,
        "mAP50-95": 0.562,
        "precision": 0.823,
        "recall": 0.741,
        "f1_score": 0.780
      },
      "tags": ["production", "verified"],
      "created_at": "2024-01-15T12:00:00.000000Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 4.2 获取模型详情

```http
GET /api/v1/models/{model_id}
```

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/models/770e8400-e29b-41d4-a716-446655440003 \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440003",
  "training_id": "660e8400-e29b-41d4-a716-446655440002",
  "name": "行人检测模型",
  "version": "v1.0",
  "model_version": "yolov8n",
  "description": "行人检测模型 - 首版训练",
  "file_size": 6234128,
  "metrics": {
    "mAP50": 0.785,
    "mAP50-95": 0.562
  },
  "tags": ["production"],
  "created_at": "2024-01-15T12:00:00.000000Z"
}
```

---

### 4.3 导出模型

```http
POST /api/v1/models/{model_id}/export
```

**请求参数（JSON Body）**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `format` | string | ✅ | — | 导出格式：`onnx`, `torchscript`, `tflite`, `paddle`, `coreml` |
| `img_size` | int | ❌ | 640 | 导出图像尺寸（32–4096） |
| `simplify` | bool | ❌ | true | 是否简化模型（ONNX） |
| `dynamic` | bool | ❌ | false | 是否使用动态输入尺寸（ONNX） |

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/models/770e8400-e29b-41d4-a716-446655440003/export \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "onnx",
    "img_size": 640,
    "simplify": true,
    "dynamic": false
  }'
```

**响应示例（200 OK）**

```json
{
  "message": "导出任务已提交",
  "model_id": "770e8400-e29b-41d4-a716-446655440003",
  "format": "onnx"
}
```

---

### 4.4 删除模型

```http
DELETE /api/v1/models/{model_id}
```

**说明**：删除模型记录及关联的权重文件。

**请求示例**

```bash
curl -X DELETE http://localhost:10003/api/v1/models/770e8400-e29b-41d4-a716-446655440003 \
  -H "Authorization: Bearer <token>"
```

**响应**：`204 No Content`（无响应体）

---

### 4.5 添加模型标签

```http
POST /api/v1/models/{model_id}/tags
```

**请求参数（JSON Body）**

Body 为字符串数组，表示要添加的标签列表。

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/models/770e8400-e29b-41d4-a716-446655440003/tags \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '["production", "verified", "行人检测"]'
```

**响应示例（200 OK）**

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440003",
  "tags": ["production", "verified", "行人检测"],
  ...
}
```

---

### 4.6 下载模型文件（附加）

```http
GET /api/v1/models/{model_id}/download
```

**说明**：下载模型的权重文件（二进制流）。

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/models/770e8400-e29b-41d4-a716-446655440003/download \
  -H "Authorization: Bearer <token>" \
  -o model.pt
```

**响应**：二进制文件流，`Content-Type: application/octet-stream`

---

### 4.7 获取模型版本历史（附加）

```http
GET /api/v1/models/{model_id}/versions
```

**说明**：获取同名模型的所有历史版本。

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/models/770e8400-e29b-41d4-a716-446655440003/versions \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440003",
    "version": "v2.0",
    "model_version": "yolov8n",
    "created_at": "2024-01-15T12:00:00.000000Z",
    "metrics": { "mAP50": 0.821 }
  },
  {
    "id": "880e8400-e29b-41d4-a716-446655440004",
    "version": "v1.0",
    "model_version": "yolov8n",
    "created_at": "2024-01-10T08:00:00.000000Z",
    "metrics": { "mAP50": 0.785 }
  }
]
```

---

## 5. 数据集管理

### 5.1 上传数据集

```http
POST /api/v1/datasets/upload
```

**说明**：使用 `multipart/form-data` 上传。仅支持 `.zip` 格式，自动解析 YOLO / COCO / VOC 格式。

**表单参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `file` | file | ✅ | — | 数据集压缩文件（.zip） |
| `name` | string | ✅ | — | 数据集名称（1–200 字符） |
| `description` | string | ❌ | — | 数据集描述（≤2000 字符） |
| `format` | string | ❌ | `yolo` | 数据集格式：`yolo`, `coco`, `voc` |

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/datasets/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@dataset.zip" \
  -F "name=行人检测数据集" \
  -F "description=包含10000张行人标注图片" \
  -F "format=yolo"
```

**响应示例（201 Created）**

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440005",
  "name": "行人检测数据集",
  "description": "包含10000张行人标注图片",
  "format": "yolo",
  "classes": null,
  "stats": null,
  "file_path": "/data/uploads/datasets/<user_id>/990e8400-....zip",
  "status": "uploading",
  "created_at": "2024-01-15T10:00:00.000000Z"
}
```

**数据集状态说明**

| 状态 | 说明 |
|------|------|
| `uploading` | 上传中，正在处理 |
| `processing` | 正在解析格式与类别 |
| `ready` | 可用的 |
| `error` | 处理失败 |

**错误响应**

| 状态码 | detail |
|--------|--------|
| 400 | `不支持的格式: xxx，允许: {'yolo', 'coco', 'voc'}` |
| 400 | `仅支持 .zip 格式的数据集文件` |
| 400 | `文件不是合法的 ZIP 格式` |
| 413 | `文件大小超过限制 (500MB)` |

---

### 5.2 获取数据集列表

```http
GET /api/v1/datasets/
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `page` | int | ❌ | 1 | 页码 |
| `page_size` | int | ❌ | 20 | 每页数量（1–100） |

**请求示例**

```bash
curl -X GET "http://localhost:10003/api/v1/datasets/?page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "items": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440005",
      "name": "行人检测数据集",
      "description": "包含10000张行人标注图片",
      "format": "yolo",
      "classes": ["person", "car", "bicycle"],
      "stats": {
        "total_images": 10000,
        "train_images": 8000,
        "val_images": 2000,
        "num_classes": 3
      },
      "file_path": "/data/uploads/datasets/<user_id>/990e8400-....zip",
      "status": "ready",
      "created_at": "2024-01-15T10:00:00.000000Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 5.3 获取数据集详情

```http
GET /api/v1/datasets/{dataset_id}
```

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/datasets/990e8400-e29b-41d4-a716-446655440005 \
  -H "Authorization: Bearer <token>"
```

**响应示例**：同列表中的单条数据结构。

---

### 5.4 删除数据集

```http
DELETE /api/v1/datasets/{dataset_id}
```

**说明**：删除数据集记录及关联的文件。

**请求示例**

```bash
curl -X DELETE http://localhost:10003/api/v1/datasets/990e8400-e29b-41d4-a716-446655440005 \
  -H "Authorization: Bearer <token>"
```

**响应**：`204 No Content`（无响应体）

---

## 6. 测试中心

### 6.1 单图推理预测

```http
POST /api/v1/test/predict
```

**说明**：上传单张图片，使用指定模型进行 YOLO 目标检测推理。

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `file` | file | ✅ | — | 待检测图片 |
| `model_id` | UUID (query) | ✅ | — | 使用的模型 ID |
| `confidence` | float (query) | ❌ | 0.25 | 置信度阈值（0.0–1.0） |

**请求示例**

```bash
curl -X POST "http://localhost:10003/api/v1/test/predict?model_id=770e8400-e29b-41d4-a716-446655440003&confidence=0.5" \
  -H "Authorization: Bearer <token>" \
  -F "file=@test_image.jpg"
```

**响应示例（200 OK）**

```json
{
  "test_id": "aa0e8400-e29b-41d4-a716-446655440006",
  "model_id": "770e8400-e29b-41d4-a716-446655440003",
  "detections": [
    {
      "class_name": "person",
      "class_id": 0,
      "confidence": 0.923,
      "bbox": { "x1": 120.5, "y1": 80.3, "x2": 350.8, "y2": 480.2 }
    },
    {
      "class_name": "car",
      "class_id": 2,
      "confidence": 0.876,
      "bbox": { "x1": 400.0, "y1": 200.0, "x2": 600.0, "y2": 400.0 }
    }
  ],
  "inference_time_ms": 45.23
}
```

**错误响应**

| 状态码 | detail |
|--------|--------|
| 404 | `模型不存在或无权使用` |
| 404 | `模型文件不存在` |
| 503 | `推理引擎未安装，请安装 ultralytics` |
| 500 | `推理失败: <详细信息>` |

---

### 6.2 批量推理预测

```http
POST /api/v1/test/batch-predict
```

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `files` | file[] | ✅ | — | 待检测图片列表（多文件上传） |
| `model_id` | UUID (query) | ✅ | — | 使用的模型 ID |
| `confidence` | float (query) | ❌ | 0.25 | 置信度阈值（0.0–1.0） |

**请求示例**

```bash
curl -X POST "http://localhost:10003/api/v1/test/batch-predict?model_id=770e8400-e29b-41d4-a716-446655440003&confidence=0.3" \
  -H "Authorization: Bearer <token>" \
  -F "files=@img1.jpg" \
  -F "files=@img2.jpg" \
  -F "files=@img3.jpg"
```

**响应示例（200 OK）**

```json
{
  "batch_id": "bb0e8400-e29b-41d4-a716-446655440007",
  "total": 3,
  "results": [
    {
      "test_id": "cc0e8400-...",
      "model_id": "770e8400-...",
      "detections": [...],
      "inference_time_ms": 45.23
    },
    {
      "test_id": "dd0e8400-...",
      "model_id": "770e8400-...",
      "detections": [...],
      "inference_time_ms": 38.91
    },
    {
      "test_id": "ee0e8400-...",
      "model_id": "770e8400-...",
      "detections": [],
      "inference_time_ms": 42.10
    }
  ]
}
```

---

### 6.3 获取测试结果

```http
GET /api/v1/test/results/{test_id}
```

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/test/results/aa0e8400-e29b-41d4-a716-446655440006 \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "test_id": "aa0e8400-e29b-41d4-a716-446655440006",
  "model_id": "770e8400-e29b-41d4-a716-446655440003",
  "detections": [
    {
      "class_name": "person",
      "class_id": 0,
      "confidence": 0.923,
      "bbox": { "x1": 120.5, "y1": 80.3, "x2": 350.8, "y2": 480.2 }
    }
  ],
  "inference_time_ms": 45.23
}
```

---

### 6.4 获取带标注的结果图片（附加）

```http
GET /api/v1/test/{test_id}/result-image
```

**说明**：返回在原始图片上绘制了检测框和类别标签的 PNG 图片。

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/test/aa0e8400-e29b-41d4-a716-446655440006/result-image \
  -H "Authorization: Bearer <token>" \
  -o annotated_result.png
```

**响应**：PNG 图片二进制流，`Content-Type: image/png`

---

## 7. 模型对比

### 7.1 创建模型对比任务

```http
POST /api/v1/compares/
```

**请求参数（JSON Body）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model_ids` | string[] | ✅ | 要对比的模型 ID 列表（2–10 个） |
| `test_dataset_id` | string | ✅ | 测试数据集 ID |
| `name` | string | ❌ | 对比任务名称 |

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/compares/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "model_ids": [
      "770e8400-e29b-41d4-a716-446655440003",
      "880e8400-e29b-41d4-a716-446655440004"
    ],
    "test_dataset_id": "990e8400-e29b-41d4-a716-446655440005",
    "name": "yolov8n v1 vs v2 对比"
  }'
```

**响应示例（200 OK）**

```json
{
  "id": "ff0e8400-e29b-41d4-a716-446655440008",
  "name": "yolov8n v1 vs v2 对比",
  "status": "pending",
  "model_ids": [
    "770e8400-e29b-41d4-a716-446655440003",
    "880e8400-e29b-41d4-a716-446655440004"
  ],
  "test_dataset_id": "990e8400-e29b-41d4-a716-446655440005",
  "results": null,
  "error_message": null,
  "created_at": "2024-01-15T14:00:00.000000Z",
  "completed_at": null
}
```

---

### 7.2 获取对比任务列表

```http
GET /api/v1/compares/
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `page` | int | ❌ | 1 | 页码 |
| `page_size` | int | ❌ | 20 | 每页数量（1–100） |

**请求示例**

```bash
curl -X GET "http://localhost:10003/api/v1/compares/?page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "items": [
    {
      "id": "ff0e8400-e29b-41d4-a716-446655440008",
      "name": "yolov8n v1 vs v2 对比",
      "status": "completed",
      "model_ids": ["770e8400-...", "880e8400-..."],
      "test_dataset_id": "990e8400-...",
      "results": [
        {
          "model_id": "770e8400-...",
          "model_name": "行人检测模型",
          "model_version": "yolov8n",
          "mAP50": 0.785,
          "mAP50_95": 0.562,
          "precision": 0.823,
          "recall": 0.741,
          "f1_score": 0.780,
          "inference_speed_ms": 12.5,
          "model_size_mb": 6.2,
          "params_count": 3150000,
          "flops": 8.7,
          "per_class_metrics": {
            "person": { "precision": 0.85, "recall": 0.78, "f1": 0.81 }
          }
        },
        {
          "model_id": "880e8400-...",
          "model_name": "行人检测模型",
          "model_version": "yolov8n",
          "mAP50": 0.821,
          "mAP50_95": 0.601,
          "precision": 0.851,
          "recall": 0.782,
          "f1_score": 0.815,
          "inference_speed_ms": 13.1,
          "model_size_mb": 6.2,
          "params_count": 3150000,
          "flops": 8.7,
          "per_class_metrics": {
            "person": { "precision": 0.88, "recall": 0.80, "f1": 0.84 }
          }
        }
      ],
      "created_at": "2024-01-15T14:00:00.000000Z",
      "completed_at": "2024-01-15T14:05:00.000000Z"
    }
  ],
  "total": 1
}
```

**对比指标说明**

| 指标 | 说明 |
|------|------|
| `mAP50` | IoU=0.5 时的平均精度均值 |
| `mAP50_95` | IoU 从 0.5 到 0.95 的平均精度均值 |
| `precision` | 精确率 |
| `recall` | 召回率 |
| `f1_score` | F1 分数 |
| `inference_speed_ms` | 单张推理耗时（毫秒） |
| `model_size_mb` | 模型文件大小（MB） |
| `params_count` | 模型参数量 |
| `flops` | 计算量（GFLOPs） |
| `per_class_metrics` | 每个类别的细化指标 |

---

### 7.3 获取对比任务详情

```http
GET /api/v1/compares/{compare_id}
```

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/compares/ff0e8400-e29b-41d4-a716-446655440008 \
  -H "Authorization: Bearer <token>"
```

**响应示例**：同列表中的单条数据结构。

**错误响应**

| 状态码 | detail |
|--------|--------|
| 404 | `对比任务不存在` |
| 403 | `无权访问此对比任务` |

---

## 8. 模型部署

### 8.1 创建部署任务

```http
POST /api/v1/deployments/
```

**请求参数（JSON Body）**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `model_id` | UUID | ✅ | — | 模型 ID |
| `name` | string | ✅ | — | 部署名称（1–255 字符） |
| `config` | object | ❌ | 默认值 | 部署配置（见子字段） |

**`config` 子字段**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `platform` | string | `onnx_runtime` | 部署平台：`onnx_runtime`, `tensorrt`, `torchserve` |
| `port` | int | 8080 | 服务端口（1024–65535） |
| `workers` | int | 1 | 工作进程数（1–16） |
| `batch_size` | int | 1 | 批量大小（1–64） |
| `gpu` | bool | true | 是否使用 GPU |
| `img_size` | int | 640 | 输入图像大小（32–4096） |
| `conf_threshold` | float | 0.25 | 置信度阈值（0.0–1.0） |
| `iou_threshold` | float | 0.45 | IOU 阈值（0.0–1.0） |

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/deployments/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "770e8400-e29b-41d4-a716-446655440003",
    "name": "行人检测-生产部署",
    "config": {
      "platform": "onnx_runtime",
      "port": 8080,
      "workers": 2,
      "batch_size": 4,
      "gpu": true,
      "img_size": 640,
      "conf_threshold": 0.5,
      "iou_threshold": 0.45
    }
  }'
```

**响应示例（200 OK）**

```json
{
  "id": "110e8400-e29b-41d4-a716-446655440009",
  "model_id": "770e8400-e29b-41d4-a716-446655440003",
  "name": "行人检测-生产部署",
  "status": "starting",
  "platform": "onnx_runtime",
  "endpoint": null,
  "config": {
    "platform": "onnx_runtime",
    "port": 8080,
    "workers": 2,
    "batch_size": 4,
    "gpu": true,
    "img_size": 640,
    "conf_threshold": 0.5,
    "iou_threshold": 0.45
  },
  "error_message": null,
  "created_at": "2024-01-15T15:00:00.000000Z",
  "updated_at": "2024-01-15T15:00:00.000000Z",
  "stopped_at": null
}
```

---

### 8.2 获取部署列表

```http
GET /api/v1/deployments/
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `status` | string | ❌ | — | 按状态筛选 |
| `platform` | string | ❌ | — | 按平台筛选（`onnx_runtime`, `tensorrt`, `torchserve`） |
| `page` | int | ❌ | 1 | 页码 |
| `page_size` | int | ❌ | 20 | 每页数量（1–100） |

**请求示例**

```bash
# 获取所有部署
curl -X GET "http://localhost:10003/api/v1/deployments/" \
  -H "Authorization: Bearer <token>"

# 筛选运行中的 onnx_runtime 部署
curl -X GET "http://localhost:10003/api/v1/deployments/?status=running&platform=onnx_runtime" \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "items": [
    {
      "id": "110e8400-e29b-41d4-a716-446655440009",
      "model_id": "770e8400-e29b-41d4-a716-446655440003",
      "name": "行人检测-生产部署",
      "status": "running",
      "platform": "onnx_runtime",
      "endpoint": "http://localhost:8080",
      "config": { "port": 8080, "workers": 2 },
      "error_message": null,
      "created_at": "2024-01-15T15:00:00.000000Z",
      "updated_at": "2024-01-15T15:01:00.000000Z",
      "stopped_at": null
    }
  ],
  "total": 1
}
```

---

### 8.3 获取部署详情

```http
GET /api/v1/deployments/{deploy_id}
```

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/deployments/110e8400-e29b-41d4-a716-446655440009 \
  -H "Authorization: Bearer <token>"
```

---

### 8.4 获取部署运行状态

```http
GET /api/v1/deployments/{deploy_id}/status
```

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/deployments/110e8400-e29b-41d4-a716-446655440009/status \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "id": "110e8400-e29b-41d4-a716-446655440009",
  "status": "running",
  "endpoint": "http://localhost:8080",
  "health": "healthy",
  "uptime_seconds": 3600.0,
  "request_count": 15420,
  "avg_latency_ms": 28.5
}
```

---

### 8.5 停止部署

```http
POST /api/v1/deployments/{deploy_id}/stop
```

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/deployments/110e8400-e29b-41d4-a716-446655440009/stop \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "id": "110e8400-e29b-41d4-a716-446655440009",
  "status": "stopped",
  "stopped_at": "2024-01-15T16:00:00.000000Z",
  ...
}
```

---

## 9. 超参搜索

### 9.1 创建超参搜索任务

```http
POST /api/v1/hyperparameter/searches
```

**请求参数（JSON Body）**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | string | ✅ | — | 搜索任务名称（1–200 字符） |
| `model_version` | string | ❌ | `yolov8n` | YOLO 模型版本 |
| `dataset_id` | string | ✅ | — | 数据集 ID |
| `search_space` | object | ✅ | — | 搜索空间定义（key: 参数名, value: 范围定义） |
| `search_config` | object | ❌ | 默认值 | 搜索配置（见子字段） |
| `base_config` | object | ❌ | `{}` | 基础训练配置（不在搜索空间中的固定参数） |

**`search_space` 子字段（每个参数的定义）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ❌ (`float`) | 参数类型：`float`, `int`, `categorical` |
| `low` | float | ❌ | 下界（连续型） |
| `high` | float | ❌ | 上界（连续型） |
| `values` | any[] | ❌ | 离散值列表（分类型或网格搜索） |
| `log` | bool | ❌ (`false`) | 是否在对数尺度采样 |
| `step` | float | ❌ | 步长（网格搜索用） |

**`search_config` 子字段**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `method` | string | `bayesian` | 搜索方法：`grid`（网格）, `random`（随机）, `bayesian`（贝叶斯） |
| `n_trials` | int | 20 | 试验次数（1–500） |
| `metric` | string | `metrics/mAP50-95(B)` | 优化指标 |
| `direction` | string | `maximize` | 优化方向：`maximize` 或 `minimize` |
| `epochs_per_trial` | int | 50 | 每个试验的训练轮数（1–1000） |
| `timeout` | int | ❌ | 整体搜索超时时间（秒） |
| `seed` | int | ❌ | 随机种子（可复现） |

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/hyperparameter/searches \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "yolov8n 超参搜索",
    "model_version": "yolov8n",
    "dataset_id": "990e8400-e29b-41d4-a716-446655440005",
    "search_space": {
      "learning_rate": {
        "type": "float",
        "low": 1e-05,
        "high": 0.1,
        "log": true
      },
      "batch_size": {
        "type": "int",
        "values": [8, 16, 32, 64]
      },
      "img_size": {
        "type": "int",
        "values": [416, 640, 800]
      }
    },
    "search_config": {
      "method": "bayesian",
      "n_trials": 30,
      "metric": "metrics/mAP50-95(B)",
      "direction": "maximize",
      "epochs_per_trial": 50
    },
    "base_config": {
      "optimizer": "SGD",
      "device": "0",
      "workers": 8,
      "patience": 20
    }
  }'
```

**响应示例（201 Created）**

```json
{
  "id": "220e8400-e29b-41d4-a716-446655440010",
  "name": "yolov8n 超参搜索",
  "model_version": "yolov8n",
  "dataset_id": "990e8400-e29b-41d4-a716-446655440005",
  "status": "pending",
  "method": "bayesian",
  "search_space": {
    "learning_rate": { "type": "float", "low": 1e-05, "high": 0.1, "log": true },
    "batch_size": { "type": "int", "values": [8, 16, 32, 64] },
    "img_size": { "type": "int", "values": [416, 640, 800] }
  },
  "search_config": {
    "method": "bayesian",
    "n_trials": 30,
    "metric": "metrics/mAP50-95(B)",
    "direction": "maximize",
    "epochs_per_trial": 50
  },
  "n_trials": 30,
  "completed_trials": 0,
  "best_metric": null,
  "best_params": null,
  "created_at": "2024-01-15T16:00:00.000000Z"
}
```

---

### 9.2 获取超参搜索列表

```http
GET /api/v1/hyperparameter/searches
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `status` | string | ❌ | — | 按状态筛选 |
| `page` | int | ❌ | 1 | 页码 |
| `page_size` | int | ❌ | 20 | 每页数量（1–100） |

**请求示例**

```bash
curl -X GET "http://localhost:10003/api/v1/hyperparameter/searches?status=completed&page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "items": [
    {
      "id": "220e8400-e29b-41d4-a716-446655440010",
      "name": "yolov8n 超参搜索",
      "model_version": "yolov8n",
      "dataset_id": "990e8400-...",
      "status": "completed",
      "method": "bayesian",
      "search_space": { ... },
      "search_config": { ... },
      "n_trials": 30,
      "completed_trials": 30,
      "best_metric": 0.612,
      "best_params": {
        "learning_rate": 0.005,
        "batch_size": 32,
        "img_size": 640
      },
      "created_at": "2024-01-15T16:00:00.000000Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 9.3 获取搜索任务详情

```http
GET /api/v1/hyperparameter/searches/{search_id}
```

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/hyperparameter/searches/220e8400-e29b-41d4-a716-446655440010 \
  -H "Authorization: Bearer <token>"
```

---

### 9.4 获取所有试验结果

```http
GET /api/v1/hyperparameter/searches/{search_id}/trials
```

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/hyperparameter/searches/220e8400-e29b-41d4-a716-446655440010/trials \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
[
  {
    "id": "330e8400-e29b-41d4-a716-446655440011",
    "search_id": "220e8400-e29b-41d4-a716-446655440010",
    "trial_number": 1,
    "status": "completed",
    "params": {
      "learning_rate": 0.005,
      "batch_size": 32,
      "img_size": 640
    },
    "metric_value": 0.612,
    "metrics": {
      "mAP50": 0.821,
      "mAP50-95": 0.612,
      "precision": 0.851,
      "recall": 0.782
    },
    "started_at": "2024-01-15T16:01:00.000000Z",
    "completed_at": "2024-01-15T16:05:00.000000Z",
    "duration": 240.0,
    "error": null
  },
  {
    "id": "340e8400-e29b-41d4-a716-446655440012",
    "search_id": "220e8400-e29b-41d4-a716-446655440010",
    "trial_number": 2,
    "status": "completed",
    "params": {
      "learning_rate": 0.001,
      "batch_size": 16,
      "img_size": 800
    },
    "metric_value": 0.589,
    "metrics": { ... },
    "started_at": "2024-01-15T16:06:00.000000Z",
    "completed_at": "2024-01-15T16:10:00.000000Z",
    "duration": 245.0,
    "error": null
  }
]
```

---

### 9.5 取消超参搜索（附加）

```http
POST /api/v1/hyperparameter/searches/{search_id}/cancel
```

**说明**：仅可取消状态为 `pending` 或 `running` 的搜索任务。

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/hyperparameter/searches/220e8400-e29b-41d4-a716-446655440010/cancel \
  -H "Authorization: Bearer <token>"
```

---

## 10. 团队管理

### 10.1 创建团队

```http
POST /api/v1/teams/
```

**请求参数（JSON Body）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 团队名称（1–100 字符） |
| `description` | string | ❌ | 团队描述 |

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/teams/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI 视觉团队",
    "description": "负责目标检测模型研发"
  }'
```

**响应示例（201 Created）**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440013",
  "name": "AI 视觉团队",
  "description": "负责目标检测模型研发",
  "owner_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T17:00:00.000000Z",
  "members": []
}
```

---

### 10.2 获取团队列表

```http
GET /api/v1/teams/
```

**说明**：返回当前用户所属的所有团队。

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/teams/ \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440013",
      "name": "AI 视觉团队",
      "description": "负责目标检测模型研发",
      "owner_id": "550e8400-...",
      "created_at": "2024-01-15T17:00:00.000000Z",
      "members": [
        {
          "team_id": "550e8400-...",
          "user_id": "550e8400-...",
          "role": "owner",
          "joined_at": "2024-01-15T17:00:00.000000Z"
        }
      ]
    }
  ],
  "total": 1
}
```

---

### 10.3 获取团队详情

```http
GET /api/v1/teams/{team_id}
```

**请求示例**

```bash
curl -X GET http://localhost:10003/api/v1/teams/550e8400-e29b-41d4-a716-446655440013 \
  -H "Authorization: Bearer <token>"
```

---

### 10.4 更新团队信息（附加）

```http
PATCH /api/v1/teams/{team_id}
```

**说明**：仅团队 Owner 可操作。

**请求参数（JSON Body）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ❌ | 团队名称（1–100 字符） |
| `description` | string | ❌ | 团队描述 |

**请求示例**

```bash
curl -X PATCH http://localhost:10003/api/v1/teams/550e8400-e29b-41d4-a716-446655440013 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI 视觉团队 v2",
    "description": "升级版团队描述"
  }'
```

---

### 10.5 添加团队成员

```http
POST /api/v1/teams/{team_id}/members
```

**说明**：仅团队 Owner 可操作。

**请求参数（JSON Body）**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | UUID | ✅ | 要添加的用户 ID |
| `role` | string | ❌ (`member`) | 角色：`owner`, `admin`, `member` |

**请求示例**

```bash
curl -X POST http://localhost:10003/api/v1/teams/550e8400-e29b-41d4-a716-446655440013/members \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "660e8400-e29b-41d4-a716-446655440014",
    "role": "admin"
  }'
```

**响应示例（201 Created）**

```json
{
  "team_id": "550e8400-e29b-41d4-a716-446655440013",
  "user_id": "660e8400-e29b-41d4-a716-446655440014",
  "role": "admin",
  "joined_at": "2024-01-15T17:30:00.000000Z"
}
```

**角色说明**

| 角色 | 权限 |
|------|------|
| `owner` | 团队创建者，拥有全部权限 |
| `admin` | 管理员，可管理团队资源 |
| `member` | 普通成员 |

---

### 10.6 移除团队成员（附加）

```http
DELETE /api/v1/teams/{team_id}/members/{user_id}
```

**说明**：仅团队 Owner 可操作。

**请求示例**

```bash
curl -X DELETE http://localhost:10003/api/v1/teams/550e8400-e29b-41d4-a716-446655440013/members/660e8400-e29b-41d4-a716-446655440014 \
  -H "Authorization: Bearer <token>"
```

**响应**：`204 No Content`

---

## 11. 活动日志

### 11.1 获取活动日志列表

```http
GET /api/v1/activities/
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `user_id` | UUID | ❌ | — | 按用户 ID 筛选 |
| `resource_type` | string | ❌ | — | 按资源类型筛选（如 `training`, `model`, `dataset`） |
| `start_date` | datetime | ❌ | — | 开始日期（ISO 8601） |
| `end_date` | datetime | ❌ | — | 结束日期（ISO 8601） |
| `page` | int | ❌ | 1 | 页码 |
| `page_size` | int | ❌ | 20 | 每页数量（1–100） |

**请求示例**

```bash
# 获取所有活动日志
curl -X GET "http://localhost:10003/api/v1/activities/?page=1&page_size=20" \
  -H "Authorization: Bearer <token>"

# 按用户和资源类型筛选
curl -X GET "http://localhost:10003/api/v1/activities/?user_id=550e8400-...&resource_type=training&page=1" \
  -H "Authorization: Bearer <token>"

# 按时间范围筛选
curl -X GET "http://localhost:10003/api/v1/activities/?start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59" \
  -H "Authorization: Bearer <token>"
```

**响应示例（200 OK）**

```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440015",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "action": "create_training",
      "resource_type": "training",
      "resource_id": "660e8400-e29b-41d4-a716-446655440002",
      "details": "创建训练任务：行人检测训练-v1（yolov8n）",
      "created_at": "2024-01-15T09:00:00.000000Z"
    },
    {
      "id": "780e8400-e29b-41d4-a716-446655440016",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "action": "upload_dataset",
      "resource_type": "dataset",
      "resource_id": "990e8400-e29b-41d4-a716-446655440005",
      "details": "上传数据集：行人检测数据集（yolo 格式）",
      "created_at": "2024-01-15T10:00:00.000000Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20
}
```

---

## 附录

### A. 完整端点速查表

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 | ❌ |
| POST | `/api/v1/auth/login` | 用户登录 | ❌ |
| POST | `/api/v1/trainings/` | 创建训练任务 | ✅ |
| GET | `/api/v1/trainings/` | 获取训练列表 | ✅ |
| GET | `/api/v1/trainings/{id}` | 获取训练详情 | ✅ |
| POST | `/api/v1/trainings/{id}/stop` | 停止训练 | ✅ |
| GET | `/api/v1/trainings/{id}/metrics` | 获取训练指标 | ✅ |
| GET | `/api/v1/trainings/{id}/logs` | 获取训练日志 | ✅ |
| GET | `/api/v1/models/` | 获取模型列表 | ✅ |
| GET | `/api/v1/models/{id}` | 获取模型详情 | ✅ |
| POST | `/api/v1/models/{id}/export` | 导出模型 | ✅ |
| DELETE | `/api/v1/models/{id}` | 删除模型 | ✅ |
| POST | `/api/v1/models/{id}/tags` | 添加模型标签 | ✅ |
| GET | `/api/v1/models/{id}/download` | 下载模型文件 | ✅ |
| GET | `/api/v1/models/{id}/versions` | 获取版本历史 | ✅ |
| POST | `/api/v1/datasets/upload` | 上传数据集 | ✅ |
| GET | `/api/v1/datasets/` | 获取数据集列表 | ✅ |
| GET | `/api/v1/datasets/{id}` | 获取数据集详情 | ✅ |
| DELETE | `/api/v1/datasets/{id}` | 删除数据集 | ✅ |
| POST | `/api/v1/test/predict` | 单图推理 | ✅ |
| POST | `/api/v1/test/batch-predict` | 批量推理 | ✅ |
| GET | `/api/v1/test/results/{id}` | 获取测试结果 | ✅ |
| GET | `/api/v1/test/{id}/result-image` | 获取标注图片 | ✅ |
| POST | `/api/v1/compares/` | 创建模型对比 | ✅ |
| GET | `/api/v1/compares/` | 获取对比列表 | ✅ |
| GET | `/api/v1/compares/{id}` | 获取对比详情 | ✅ |
| POST | `/api/v1/deployments/` | 创建部署 | ✅ |
| GET | `/api/v1/deployments/` | 获取部署列表 | ✅ |
| GET | `/api/v1/deployments/{id}` | 获取部署详情 | ✅ |
| GET | `/api/v1/deployments/{id}/status` | 获取部署状态 | ✅ |
| POST | `/api/v1/deployments/{id}/stop` | 停止部署 | ✅ |
| POST | `/api/v1/hyperparameter/searches` | 创建超参搜索 | ✅ |
| GET | `/api/v1/hyperparameter/searches` | 获取搜索列表 | ✅ |
| GET | `/api/v1/hyperparameter/searches/{id}` | 获取搜索详情 | ✅ |
| GET | `/api/v1/hyperparameter/searches/{id}/trials` | 获取所有试验 | ✅ |
| POST | `/api/v1/hyperparameter/searches/{id}/cancel` | 取消搜索 | ✅ |
| POST | `/api/v1/teams/` | 创建团队 | ✅ |
| GET | `/api/v1/teams/` | 获取团队列表 | ✅ |
| GET | `/api/v1/teams/{id}` | 获取团队详情 | ✅ |
| PATCH | `/api/v1/teams/{id}` | 更新团队信息 | ✅ |
| POST | `/api/v1/teams/{id}/members` | 添加成员 | ✅ |
| DELETE | `/api/v1/teams/{id}/members/{uid}` | 移除成员 | ✅ |
| GET | `/api/v1/activities/` | 获取活动日志 | ✅ |

### B. 认证流程

```
1. POST /api/v1/auth/register  → 创建账号
2. POST /api/v1/auth/login     → 获取 access_token
3. 后续所有请求携带 Header:  Authorization: Bearer <access_token>
```

### C. 典型工作流

```
1. 上传数据集    POST   /api/v1/datasets/upload
2. 创建训练任务  POST   /api/v1/trainings/
3. 监控训练进度  GET    /api/v1/trainings/{id}/metrics
4. 查看训练模型  GET    /api/v1/models/
5. 测试模型推理  POST   /api/v1/test/predict
6. 多模型对比    POST   /api/v1/compares/
7. 部署到生产    POST   /api/v1/deployments/
```

### D. 在线 API 文档

启动后端服务后，可通过以下地址访问交互式 API 文档：

- **Swagger UI**：`http://localhost:10003/docs`
- **ReDoc**：`http://localhost:10003/redoc`
- **OpenAPI Schema**：`http://localhost:10003/openapi.json`
