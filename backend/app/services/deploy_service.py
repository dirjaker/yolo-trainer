"""模型部署服务"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.deployment import Deployment
from app.models.model import ModelVersion


def create_deployment(
    db: Session,
    model_id: str,
    name: str,
    config: dict,
) -> Deployment:
    """创建部署任务

    Args:
        db: 数据库会话
        model_id: 模型 ID
        name: 部署名称
        config: 部署配置

    Returns:
        Deployment: 部署对象
    """
    platform = config.get("platform", "onnx_runtime")

    deployment = Deployment(
        id=uuid.uuid4(),
        model_id=uuid.UUID(model_id) if isinstance(model_id, str) else model_id,
        name=name,
        status="pending",
        platform=platform,
        config=config,
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    # 异步执行部署任务
    from app.tasks.deploy_tasks import deploy_model_task

    deploy_model_task.delay(str(deployment.id))

    return deployment


def get_deployment(db: Session, deploy_id: str) -> Optional[Deployment]:
    """获取部署详情

    Args:
        db: 数据库会话
        deploy_id: 部署 ID

    Returns:
        Deployment or None
    """
    return db.query(Deployment).filter(Deployment.id == deploy_id).first()


def list_deployments(
    db: Session,
    status: Optional[str] = None,
    platform: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[List[Deployment], int]:
    """列出部署

    Args:
        db: 数据库会话
        status: 按状态筛选
        platform: 按平台筛选
        page: 页码
        page_size: 每页数量

    Returns:
        (list, total): 部署列表和总数
    """
    query = db.query(Deployment)
    if status:
        query = query.filter(Deployment.status == status)
    if platform:
        query = query.filter(Deployment.platform == platform)

    total = query.count()
    items = (
        query.order_by(Deployment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def stop_deployment(db: Session, deploy_id: str) -> Optional[Deployment]:
    """停止部署

    Args:
        db: 数据库会话
        deploy_id: 部署 ID

    Returns:
        Deployment or None
    """
    deployment = get_deployment(db, deploy_id)
    if not deployment:
        return None

    if deployment.status not in ("running", "deploying"):
        return deployment

    # 异步执行停止任务
    from app.tasks.deploy_tasks import stop_deployment_task

    stop_deployment_task.delay(str(deployment.id))

    deployment.status = "stopping"
    db.commit()
    db.refresh(deployment)

    return deployment


def get_deployment_status(db: Session, deploy_id: str) -> Optional[dict]:
    """获取部署状态

    Args:
        db: 数据库会话
        deploy_id: 部署 ID

    Returns:
        dict or None
    """
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
        "request_count": None,  # TODO: 从监控系统获取
        "avg_latency_ms": None,  # TODO: 从监控系统获取
    }


def _check_health(deployment: Deployment) -> str:
    """检查部署健康状态

    Args:
        deployment: 部署对象

    Returns:
        str: healthy, unhealthy, unknown
    """
    if deployment.status != "running":
        return "unknown"
    if not deployment.endpoint:
        return "unknown"

    # TODO: 实际的健康检查逻辑
    # import httpx
    # try:
    #     resp = httpx.get(f"{deployment.endpoint}/health", timeout=5)
    #     return "healthy" if resp.status_code == 200 else "unhealthy"
    # except Exception:
    #     return "unhealthy"

    return "healthy"


def execute_deployment(db: Session, deploy_id: str) -> None:
    """执行部署（同步版本，供 Celery Task 调用）

    Args:
        db: 数据库会话
        deploy_id: 部署 ID
    """
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

        if platform == "onnx_runtime":
            endpoint = _deploy_onnx_runtime(model, config)
        elif platform == "tensorrt":
            endpoint = _deploy_tensorrt(model, config)
        elif platform == "torchserve":
            endpoint = _deploy_torchserve(model, config)
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
    """执行停止部署（同步版本，供 Celery Task 调用）

    Args:
        db: 数据库会话
        deploy_id: 部署 ID
    """
    deployment = get_deployment(db, deploy_id)
    if not deployment:
        return

    try:
        platform = deployment.platform
        if platform == "onnx_runtime":
            _stop_onnx_runtime(deployment)
        elif platform == "tensorrt":
            _stop_tensorrt(deployment)
        elif platform == "torchserve":
            _stop_torchserve(deployment)

        deployment.status = "stopped"
        deployment.stopped_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        deployment.status = "failed"
        deployment.error_message = f"停止失败: {e}"
        db.commit()


def _deploy_onnx_runtime(model: ModelVersion, config: dict) -> str:
    """部署到 ONNX Runtime Server

    Args:
        model: 模型对象
        config: 部署配置

    Returns:
        str: 服务端点 URL
    """
    port = config.get("port", 8080)
    # TODO: 实际部署逻辑
    # 1. 如果模型不是 ONNX 格式，先转换
    # 2. 启动 ONNX Runtime Server
    return f"http://localhost:{port}"


def _deploy_tensorrt(model: ModelVersion, config: dict) -> str:
    """部署到 TensorRT

    Args:
        model: 模型对象
        config: 部署配置

    Returns:
        str: 服务端点 URL
    """
    port = config.get("port", 8080)
    # TODO: 实际部署逻辑
    # 1. 转换模型为 TensorRT 引擎
    # 2. 启动 Triton Inference Server
    return f"http://localhost:{port}"


def _deploy_torchserve(model: ModelVersion, config: dict) -> str:
    """部署到 TorchServe

    Args:
        model: 模型对象
        config: 部署配置

    Returns:
        str: 服务端点 URL
    """
    port = config.get("port", 8080)
    # TODO: 实际部署逻辑
    # 1. 打包模型为 .mar 格式
    # 2. 启动 TorchServe
    return f"http://localhost:{port}"


def _stop_onnx_runtime(deployment: Deployment) -> None:
    """停止 ONNX Runtime Server"""
    # TODO: 实际停止逻辑
    pass


def _stop_tensorrt(deployment: Deployment) -> None:
    """停止 TensorRT Server"""
    # TODO: 实际停止逻辑
    pass


def _stop_torchserve(deployment: Deployment) -> None:
    """停止 TorchServe"""
    # TODO: 实际停止逻辑
    pass
