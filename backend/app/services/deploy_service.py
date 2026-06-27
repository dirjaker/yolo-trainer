"""模型部署服务"""

import os
import subprocess
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.deployment import Deployment
from app.models.model import ModelVersion
from app.core.config import get_settings

_settings = get_settings()


def get_deployment(db: Session, deploy_id: str) -> Optional[Deployment]:
    """获取部署记录。"""
    try:
        uid = uuid.UUID(deploy_id)
    except (ValueError, AttributeError):
        return None
    return db.query(Deployment).filter(Deployment.id == uid).first()


def create_deployment(
    db: Session,
    model_id: str,
    name: str,
    config: dict,
    user_id=None,
) -> Deployment:
    """创建部署任务。"""
    platform = config.get("platform", "onnx_runtime")
    port = int(config.get("port") or os.environ.get("DEPLOY_PORT_START", "8080"))

    deployment = Deployment(
        id=uuid.uuid4(),
        user_id=user_id,
        model_id=uuid.UUID(model_id) if isinstance(model_id, str) else model_id,
        name=name,
        status="pending",
        platform=platform,
        config={**config, "port": port},
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    # 异步执行部署
    from app.tasks.deploy_tasks import deploy_model_task
    deploy_model_task.delay(str(deployment.id))

    return deployment


def stop_deployment(db: Session, deploy_id: str) -> Optional[Deployment]:
    """停止部署。"""
    deployment = get_deployment(db, deploy_id)
    if not deployment:
        return None
    if deployment.status not in ("running", "deploying"):
        return deployment

    from app.tasks.deploy_tasks import stop_deployment_task
    stop_deployment_task.delay(str(deployment.id))

    deployment.status = "stopping"
    db.commit()
    db.refresh(deployment)
    return deployment


def get_deployment_status(db: Session, deploy_id: str) -> Optional[dict]:
    """获取部署状态。"""
    deployment = get_deployment(db, deploy_id)
    if not deployment:
        return None

    now = datetime.now(timezone.utc)
    uptime = None
    if deployment.status == "running" and deployment.updated_at:
        uptime = (now - deployment.updated_at).total_seconds()

    return {
        "id": str(deployment.id),
        "status": deployment.status,
        "endpoint": deployment.endpoint,
        "health": _check_health(deployment),
        "uptime_seconds": uptime,
        "request_count": None,
        "avg_latency_ms": None,
    }


def _check_health(deployment: Deployment) -> str:
    """检查部署健康状态。"""
    if deployment.status != "running":
        return "unknown"
    if not deployment.endpoint:
        return "unknown"
    try:
        import httpx
        resp = httpx.get(f"{deployment.endpoint}/health", timeout=5)
        return "healthy" if resp.status_code == 200 else "unhealthy"
    except Exception:
        return "unhealthy"


# ═══════════════════════════════════════════════════════════════════════
# 部署执行（由 Celery 任务调用）
# ═══════════════════════════════════════════════════════════════════════

def execute_deployment(db: Session, deploy_id: str) -> None:
    """执行部署。"""
    deployment = get_deployment(db, deploy_id)
    if not deployment:
        return

    deployment.status = "deploying"
    db.commit()

    try:
        model = db.query(ModelVersion).filter(ModelVersion.id == deployment.model_id).first()
        if not model:
            raise ValueError(f"模型不存在: {deployment.model_id}")

        config = deployment.config or {}
        platform = config.get("platform", "onnx_runtime")
        port = config.get("port", 8080)

        if platform == "onnx_runtime":
            endpoint = _deploy_onnx(model, config, port)
        elif platform == "tensorrt":
            endpoint = _deploy_tensorrt(model, config, port)
        elif platform == "torchserve":
            endpoint = _deploy_torchserve(model, config, port)
        else:
            raise ValueError(f"不支持的部署平台: {platform}")

        deployment.status = "running"
        deployment.endpoint = endpoint
        deployment.updated_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        deployment.status = "failed"
        deployment.error_message = str(e)
        db.commit()


def execute_stop(db: Session, deploy_id: str) -> None:
    """停止部署。"""
    deployment = get_deployment(db, deploy_id)
    if not deployment:
        return

    try:
        platform = deployment.platform
        pid_file = f"/tmp/deploy_{deploy_id}.pid"
        if os.path.exists(pid_file):
            with open(pid_file) as f:
                pid = int(f.read().strip())
            os.kill(pid, 15)  # SIGTERM
            os.remove(pid_file)

        deployment.status = "stopped"
        deployment.stopped_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        deployment.status = "failed"
        deployment.error_message = f"停止失败: {e}"
        db.commit()


# ═══════════════════════════════════════════════════════════════════════
# 部署平台实现
# ═══════════════════════════════════════════════════════════════════════

def _deploy_onnx(model: ModelVersion, config: dict, port: int) -> str:
    """部署 ONNX Runtime Server。"""
    # 确保模型是 ONNX 格式
    onnx_path = model.file_path
    if not onnx_path.endswith(".onnx"):
        export_dir = os.path.join(os.path.dirname(model.file_path), "exports")
        onnx_path = os.path.join(export_dir, f"{model.id}.onnx")
        if not os.path.exists(onnx_path):
            from ultralytics import YOLO
            yolo_model = YOLO(model.file_path)
            onnx_path = str(yolo_model.export(format="onnx"))

    import subprocess
    proc = subprocess.Popen(
        ["python", "-m", "onnxruntime.transformers.ort_server",
         "--model", onnx_path, "--port", str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    # 写 PID 文件供停止时使用
    deploy_id = str(model.id)
    with open(f"/tmp/deploy_{deploy_id}.pid", "w") as f:
        f.write(str(proc.pid))

    host = os.environ.get("DEPLOY_HOST", "0.0.0.0")
    return f"http://{host}:{port}"


def _deploy_tensorrt(model: ModelVersion, config: dict, port: int) -> str:
    """部署 TensorRT (Triton Inference Server)。"""
    model_repo = os.environ.get("TRITON_MODEL_REPO", "/data/triton/models")
    host = os.environ.get("DEPLOY_HOST", "0.0.0.0")

    # 简单 HTTP 服务包装（生产环境应使用 Triton Server）
    import subprocess
    script = f"""
import os, sys
sys.path.insert(0, '{os.path.dirname(os.path.dirname(__file__))}')
from http.server import HTTPServer, BaseHTTPRequestHandler
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b'{{"status":"ok"}}')
HTTPServer(('{host}', {port}), H).serve_forever()
"""
    proc = subprocess.Popen(
        ["python", "-c", script],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    # PID file
    import uuid as _uuid
    deploy_id = str(_uuid.uuid4())
    with open(f"/tmp/deploy_{deploy_id}.pid", "w") as f:
        f.write(str(proc.pid))

    return f"http://{host}:{port}"


def _deploy_torchserve(model: ModelVersion, config: dict, port: int) -> str:
    """部署 TorchServe。"""
    host = os.environ.get("DEPLOY_HOST", "0.0.0.0")
    management_port = int(os.environ.get("TORCHSERVE_MANAGEMENT_PORT", "8081"))

    model_name = model.name.replace(" ", "_")[:64]
    mar_path = os.path.join(os.path.dirname(model.file_path), f"{model_name}.mar")

    # 打包 .mar
    if not os.path.exists(mar_path):
        import subprocess
        subprocess.run(
            ["torch-model-archiver", "--model-name", model_name,
             "--version", "1.0", "--serialized-file", model.file_path,
             "--handler", "image_classifier", "--export-path",
             os.path.dirname(mar_path)],
            check=True, capture_output=True,
        )

    host_str = f"http://{host}:{port}"
    return host_str
