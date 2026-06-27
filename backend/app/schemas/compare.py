"""模型对比 Schemas"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ModelMetrics(BaseModel):
    """单个模型的评估指标"""

    model_id: str
    model_name: str
    model_version: str
    mAP50: Optional[float] = Field(None, description="mAP@0.5")
    mAP50_95: Optional[float] = Field(None, description="mAP@0.5:0.95")
    precision: Optional[float] = Field(None, description="精确率")
    recall: Optional[float] = Field(None, description="召回率")
    f1_score: Optional[float] = Field(None, description="F1 分数")
    inference_speed_ms: Optional[float] = Field(None, description="推理速度 (ms)")
    model_size_mb: Optional[float] = Field(None, description="模型大小 (MB)")
    params_count: Optional[int] = Field(None, description="参数量")
    flops: Optional[float] = Field(None, description="FLOPs (G)")
    per_class_metrics: Optional[Dict[str, Dict[str, float]]] = Field(
        None, description="每类指标"
    )


class CompareCreate(BaseModel):
    """创建模型对比请求"""

    model_ids: List[str] = Field(..., min_length=2, max_length=10, description="要对比的模型 ID 列表")
    test_dataset_id: str = Field(..., description="测试数据集 ID")
    name: Optional[str] = Field(None, description="对比任务名称")


class CompareResponse(BaseModel):
    """模型对比响应"""

    id: str
    name: str
    status: str
    model_ids: List[str]
    test_dataset_id: str
    results: Optional[List[ModelMetrics]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    @field_validator("id", "test_dataset_id", mode="before")
    @classmethod
    def coerce_uuid(cls, v: Any) -> str:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class CompareListResponse(BaseModel):
    """对比任务列表响应"""

    items: List[CompareResponse]
    total: int
