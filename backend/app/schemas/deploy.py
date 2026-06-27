"""模型部署 Schemas"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DeployPlatform(str, Enum):
    """部署平台"""

    ONNX_RUNTIME = "onnx_runtime"
    TENSORRT = "tensorrt"
    TORCHSERVE = "torchserve"


class DeployConfig(BaseModel):
    """部署配置"""

    platform: DeployPlatform = Field(DeployPlatform.ONNX_RUNTIME, description="部署平台")
    port: int = Field(8080, ge=1024, le=65535, description="服务端口")
    workers: int = Field(1, ge=1, le=16, description="工作进程数")
    batch_size: int = Field(1, ge=1, le=64, description="批量大小")
    gpu: bool = Field(True, description="是否使用 GPU")
    img_size: int = Field(640, ge=32, le=4096, description="输入图像大小")
    conf_threshold: float = Field(0.25, ge=0.0, le=1.0, description="置信度阈值")
    iou_threshold: float = Field(0.45, ge=0.0, le=1.0, description="IOU 阈值")
    # extra 字段已移除，避免任意参数注入


class DeploymentCreate(BaseModel):
    """创建部署请求"""

    model_id: uuid.UUID = Field(..., description="模型 ID")
    name: str = Field(..., min_length=1, max_length=255, description="部署名称")
    config: DeployConfig = Field(default_factory=DeployConfig, description="部署配置")


class DeploymentResponse(BaseModel):
    """部署响应"""

    id: str
    model_id: str
    name: str
    status: str
    platform: str
    endpoint: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    stopped_at: Optional[datetime] = None

    @field_validator("id", "model_id", mode="before")
    @classmethod
    def coerce_uuid(cls, v: Any) -> str:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class DeploymentListResponse(BaseModel):
    """部署列表响应"""

    items: List[DeploymentResponse]
    total: int


class DeploymentStatusResponse(BaseModel):
    """部署状态响应"""

    id: str
    status: str
    endpoint: Optional[str] = None
    health: Optional[str] = None  # healthy, unhealthy, unknown
    uptime_seconds: Optional[float] = None
    request_count: Optional[int] = None
    avg_latency_ms: Optional[float] = None

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v: Any) -> str:
        if isinstance(v, UUID):
            return str(v)
        return v
