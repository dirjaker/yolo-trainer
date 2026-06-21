# YOLO Trainer — 代码审查与安全扫描报告

**审查日期**: 2026-06-22  
**审查范围**: 74 Python 文件 + 15 Vue 文件 (backend / worker / frontend)  
**审查重点**: 文件上传安全、命令注入、模型文件安全、API 认证、GPU/资源管理

---

## 严重级别说明

| 级别 | 含义 |
|------|------|
| 🔴 严重 (Critical) | 可被远程利用，导致 RCE、数据泄露等 |
| 🟠 高危 (High) | 存在明显安全隐患，需优先修复 |
| 🟡 中危 (Medium) | 安全薄弱环节，应尽快加固 |
| 🔵 低危 (Low) | 代码质量 / 最佳实践问题 |
| ⚪ 信息 (Info) | 建议改进项 |

---

## 🔴 严重问题 (Critical)

### C-1: CORS 完全放开 — `allow_origins=["*"]`

**文件**: `backend/main.py:52`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请替换为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**风险**: `allow_origins=["*"]` + `allow_credentials=True` 是**极其危险**的组合。任何恶意网站都可以携带用户 Cookie 发起跨域请求，实现 CSRF 攻击和数据窃取。浏览器实际上会拒绝此组合，但部分旧浏览器或非标准客户端仍可能生效。更重要的是，注释中的"请替换"说明这是开发遗留，但很可能直接上线。

**修复**: 将 `allow_origins` 替换为前端实际域名白名单，并从环境变量读取。

---

### C-2: 模型文件下载缺少所有权校验 — 任意模型可被下载

**文件**: `backend/app/api/v1/model.py:147-167`

```python
@router.get("/{model_id}/download")
async def download_model(model_id: uuid.UUID, db, current_user):
    result = await db.execute(select(ModelVersion).where(ModelVersion.id == model_id))
    model = result.scalar_one_or_none()
    # ⚠️ 没有检查 model 是否属于 current_user
    return FileResponse(path=model.file_path, ...)
```

**风险**: 任何已认证用户只需猜测/遍历 model_id (UUID) 即可下载**其他用户**的模型权重文件。模型权重是核心知识产权。

**修复**: 添加 `ModelVersion.user_id == current_user.id` 条件（或通过关联的 training.user_id 校验）。

---

### C-3: 模型删除/导出/标签操作缺少所有权校验

**文件**: `backend/app/api/v1/model.py` 中的 `export_model`、`add_tags`、`delete_model`、`get_model_versions` 端点

所有模型操作端点均只按 `model_id` 查询，**未校验当前用户是否为模型所有者**。

**风险**: 任意认证用户可删除/导出/篡改其他用户的模型。

---

### C-4: 部署 API 缺少所有权校验

**文件**: `backend/app/api/v1/deploy.py` 全部端点

部署接口的 `get_deployment`、`get_deployment_status`、`stop_deployment` 均未校验 `current_user` 与部署记录的归属关系。

**风险**: 任何认证用户可查看/停止其他用户的部署。

---

## 🟠 高危问题 (High)

### H-1: 文件上传仅检查扩展名，无内容验证

**文件**: `backend/app/api/v1/dataset.py:32`

```python
if not file.filename or not file.filename.endswith(".zip"):
```

**风险**:
- 仅靠 `endswith(".zip")` 检查，攻击者可上传 `evil.zip` 内含路径穿越文件（Zip Slip）或恶意脚本。
- 无文件大小限制 — 可耗尽磁盘空间（DoS）。
- 未验证是否为合法 ZIP 文件（magic bytes）。
- `file.read()` 一次性读入内存，大文件可导致 OOM。

**修复建议**:
1. 添加 `MAX_UPLOAD_SIZE` 限制（如 2GB），使用分块读写。
2. 使用 `zipfile.is_zipfile()` 验证文件格式。
3. 解压时检测路径穿越（`../`）。
4. 限制上传速率（Rate Limit）。

---

### H-2: 模型文件可作为任意路径提供给 YOLO 加载

**文件**: `worker/trainer/yolov8.py:42-46`

```python
def _resolve_model(self, config: TrainConfig) -> str:
    if config.pretrained_weights and Path(config.pretrained_weights).exists():
        return config.pretrained_weights  # ⚠️ 用户可控路径
    return self._MODEL_MAP.get(config.model_version.lower(), f"{config.model_version}.pt")
```

**风险**: `pretrained_weights` 来自用户输入的训练配置。如果传入 `/etc/passwd` 或恶意 `.pt` 文件路径，YOLO 的 `torch.load()` 会执行任意代码（PyTorch 反序列化漏洞）。

**修复**: 校验 `pretrained_weights` 必须在允许的目录下（白名单路径）。

---

### H-3: `config.extra` 直接传递给 `model.train()` — 参数注入

**文件**: `worker/trainer/yolov8.py:89`

```python
train_args.update(config.extra)  # ⚠️ 用户输入直接传入
results = model.train(**train_args)
```

**风险**: 用户可通过 `config.extra` 注入任意 ultralytics 训练参数，如覆盖 `project` 路径、设置恶意 `cfg` 文件路径、或利用未来版本的 RCE 漏洞。

**修复**: 对 `config.extra` 进行白名单过滤，仅允许已知安全的训练参数。

---

### H-4: 数据集/模型删除使用 `shutil.rmtree` 基于数据库路径

**文件**: `backend/app/api/v1/dataset.py:128`, `backend/app/api/v1/model.py:186`

```python
shutil.rmtree(os.path.dirname(dataset.file_path), ignore_errors=True)
```

**风险**: 如果 `file_path` 被篡改（如通过 SQL 注入或数据库污染），`shutil.rmtree` 会递归删除任意目录。虽然当前使用 UUID 路径，但缺少路径白名单校验是防御纵深的缺失。

**修复**: 删除前校验路径必须在 `UPLOAD_DIR` 或 `/models/` 下。

---

### H-5: JWT Secret 硬编码默认值风险

**文件**: `backend/app/core/config.py`

```python
JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
SECRET_KEY: str = "change-me-in-production"
```

**风险**: 如果部署时未覆盖环境变量，所有 JWT 令牌可被伪造。两处分别定义了 `JWT_SECRET_KEY` 和 `SECRET_KEY`，存在混淆风险。

**修复**: 启动时强制检查 secret 是否为默认值，若是则拒绝启动。

---

## 🟡 中危问题 (Medium)

### M-1: 训练配置中 `model_version` 未做白名单校验

**文件**: `backend/app/api/v1/training.py`, `backend/app/schemas/training.py`

用户可传入任意 `model_version` 字符串（如 `../../etc/passwd`），最终会拼接到模型文件路径中。

**修复**: 使用 `Literal["yolov8n", "yolov8s", ...]` 或枚举约束。

---

### M-2: 登录接口无暴力破解防护

**文件**: `backend/app/api/v1/auth.py:46`

`/auth/login` 端点未应用 `RateLimiter`。虽然 `rate_limiter.py` 已实现，但未在登录路由上使用。

**修复**: 为登录接口添加严格的限流（如 5次/分钟/IP）。

---

### M-3: 两套认证模块并存，逻辑不一致

- `backend/app/core/security.py` — 使用 `JWT_SECRET_KEY` + `JWT_ALGORITHM`
- `backend/app/api/deps.py` — 使用 `SECRET_KEY` + `ALGORITHM`
- `backend/app/services/auth_service.py` — 使用 `SECRET_KEY` + 硬编码 `HS256`

三处 JWT 配置不一致，可能导致令牌验证混乱。

**修复**: 统一为一个认证模块。

---

### M-4: Token 有效期过长

**文件**: `backend/app/services/auth_service.py:16`

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
```

24 小时的 Token 有效期过长，且无 Refresh Token 机制。泄露后攻击窗口大。

---

### M-5: 静态文件服务直接挂载上传目录

**文件**: `backend/main.py:86-87`

```python
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")
```

上传的原始数据集文件可通过 `/static/` 路径直接公开访问，无需认证。

---

### M-6: 注册接口无输入长度/格式校验

**文件**: `backend/app/api/v1/auth.py:16`

注册接口未对用户名、邮箱、密码长度做限制（依赖 Pydantic schema 但未确认约束）。

---

## 🔵 低危问题 (Low)

### L-1: 同步/异步 ORM 混用

项目同时存在 `sqlalchemy.orm.Session`（同步）和 `sqlalchemy.ext.asyncio.AsyncSession`（异步）的用法。`training_service.py`、`dataset_service.py`、`model_service.py` 使用同步 Session，而 API 路由使用异步 Session。这在 Celery 任务中是合理的，但两套 service 层容易导致维护混乱。

### L-2: Celery 异常静默吞掉

**文件**: `backend/app/api/v1/training.py:50-52`, `dataset.py:67-68`

```python
except Exception:
    pass  # Celery 不可用时不阻塞创建
```

任务提交失败时完全静默，用户会以为任务已提交但永远不会执行。

### L-3: `datetime.utcnow()` 已弃用

**文件**: `backend/app/services/auth_service.py:81-83`

Python 3.12+ 中 `datetime.utcnow()` 已弃用，应使用 `datetime.now(timezone.utc)`。项目中 `security.py` 已正确使用 `timezone.utc`，但 `auth_service.py` 未同步。

### L-4: 错误信息泄露内部细节

多处 `raise self.retry(exc=exc)` 将异常信息重试传播，日志中可能包含路径、数据库连接串等敏感信息。

---

## ⚪ 信息项 (Info)

### I-1: `RateLimiter` 已实现但未在任何路由上应用

`rate_limiter.py` 完整实现了 Redis 滑动窗口限流，但全项目无一处使用 `Depends(get_rate_limiter(...))`。

### I-2: `SecurityMiddleware` 中 SQL 注入检测是"安慰剂"

项目使用 SQLAlchemy ORM，本身防 SQL 注入。中间件的正则检测仅对原始请求参数做模式匹配，容易误报且对真正的注入无效（ORM 已处理）。建议移除或仅用于日志审计。

### I-3: 前端未审查

15 个 Vue 文件未详细审查。快速扫描发现前端使用 `localStorage` 存储 JWT Token，应注意 XSS 风险（但 CSP 头已设置 `default-src 'self'`，部分缓解）。

### I-4: 缺少 HTTPS 强制

未发现 HSTS 头设置或 HTTP→HTTPS 重定向逻辑。

### I-5: 数据库默认 SQLite

`config.py` 默认使用 SQLite，适合开发但不适合生产环境的并发场景。

---

## 问题统计

| 级别 | 数量 |
|------|------|
| 🔴 严重 (Critical) | 4 |
| 🟠 高危 (High) | 5 |
| 🟡 中危 (Medium) | 6 |
| 🔵 低危 (Low) | 4 |
| ⚪ 信息 (Info) | 5 |
| **总计** | **24** |

---

## 安全评分

| 维度 | 得分 | 说明 |
|------|------|------|
| 文件上传安全 | 3/10 | 仅扩展名校验，无大小限制、无内容验证、无路径穿越防护 |
| 命令/参数注入 | 4/10 | ORM 防 SQL 注入，但训练参数和模型路径可被注入 |
| 模型文件安全 | 3/10 | 缺少所有权校验，任意用户可下载/删除他人模型 |
| API 认证授权 | 5/10 | JWT 认证框架完整，但授权（所有权校验）大面积缺失 |
| GPU/资源管理 | 6/10 | 通过 Celery 异步隔离，但无 GPU 占用限制和任务队列隔离 |
| 整体安全架构 | 5/10 | 有安全中间件和限流器的骨架，但均未真正生效 |

### 综合评分: **4.2 / 10** ⚠️

> **结论**: 项目具备基本的安全架构意识（JWT、安全中间件、限流器、CORS），但关键安全措施均未真正落地。最紧迫的问题是**所有权校验完全缺失**（C-2/C-3/C-4）和**CORS 配置危险**（C-1）。建议在上线前按 🔴→🟠→🟡 优先级逐项修复。

---

## 修复优先级建议

1. **立即修复** (P0): C-1 CORS、C-2/C-3/C-4 所有权校验
2. **尽快修复** (P1): H-1 上传安全、H-2 模型路径校验、H-3 参数白名单、H-5 Secret 默认值
3. **计划修复** (P2): M-1~M-6 中危项
4. **持续改进** (P3): L/I 低危和信息项
