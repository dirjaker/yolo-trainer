"""测试 / 推理路由。"""

import os
import time
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.model import ModelVersion
from app.models.user import User
from app.schemas.test import TestResult

router = APIRouter()

# 简单的内存缓存（生产环境应使用 Redis）
_test_results: dict = {}


@router.post("/predict", response_model=TestResult)
async def predict_single(
    file: UploadFile = File(..., description="待检测图片"),
    model_id: uuid.UUID = Query(..., description="使用的模型 ID"),
    confidence: float = Query(0.25, ge=0.0, le=1.0, description="置信度阈值"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """单图推理预测。"""
    # 验证模型存在
    result = await db.execute(select(ModelVersion).where(ModelVersion.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    if not model.file_path or not os.path.isfile(model.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型文件不存在")

    # 读取图片
    image_bytes = await file.read()

    # 执行推理
    start_time = time.time()
    try:
        from ultralytics import YOLO

        yolo_model = YOLO(model.file_path)
        results = yolo_model.predict(
            source=image_bytes,
            conf=confidence,
            verbose=False,
        )

        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    "class_name": r.names[int(box.cls)],
                    "class_id": int(box.cls),
                    "confidence": float(box.conf),
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                })
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="推理引擎未安装，请安装 ultralytics",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"推理失败: {str(e)}",
        )

    inference_time_ms = (time.time() - start_time) * 1000

    test_id = str(uuid.uuid4())
    test_result = TestResult(
        test_id=test_id,
        model_id=str(model_id),
        detections=detections,
        inference_time_ms=round(inference_time_ms, 2),
    )

    # 缓存结果
    _test_results[test_id] = {
        "result": test_result,
        "image_bytes": image_bytes,
        "filename": file.filename,
    }

    return test_result


@router.post("/batch")
async def predict_batch(
    files: list[UploadFile] = File(..., description="待检测图片列表"),
    model_id: uuid.UUID = Query(..., description="使用的模型 ID"),
    confidence: float = Query(0.25, ge=0.0, le=1.0, description="置信度阈值"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量推理预测。"""
    # 验证模型
    result = await db.execute(select(ModelVersion).where(ModelVersion.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    if not model.file_path or not os.path.isfile(model.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型文件不存在")

    batch_id = str(uuid.uuid4())
    batch_results = []

    try:
        from ultralytics import YOLO

        yolo_model = YOLO(model.file_path)
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="推理引擎未安装，请安装 ultralytics",
        )

    for upload_file in files:
        image_bytes = await upload_file.read()
        start_time = time.time()

        try:
            results = yolo_model.predict(source=image_bytes, conf=confidence, verbose=False)
            detections = []
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    detections.append({
                        "class_name": r.names[int(box.cls)],
                        "class_id": int(box.cls),
                        "confidence": float(box.conf),
                        "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    })
        except Exception:
            detections = []

        inference_time_ms = (time.time() - start_time) * 1000
        test_id = str(uuid.uuid4())

        test_result = TestResult(
            test_id=test_id,
            model_id=str(model_id),
            detections=detections,
            inference_time_ms=round(inference_time_ms, 2),
        )
        batch_results.append(test_result)

        _test_results[test_id] = {
            "result": test_result,
            "image_bytes": image_bytes,
            "filename": upload_file.filename,
        }

    return {"batch_id": batch_id, "total": len(batch_results), "results": batch_results}


@router.get("/{test_id}/results", response_model=TestResult)
async def get_test_results(
    test_id: str,
    current_user: User = Depends(get_current_user),
):
    """获取测试结果。"""
    cached = _test_results.get(test_id)
    if not cached:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试结果不存在")
    return cached["result"]


@router.get("/{test_id}/result-image")
async def get_result_image(
    test_id: str,
    current_user: User = Depends(get_current_user),
):
    """获取带检测框的结果图片。"""
    cached = _test_results.get(test_id)
    if not cached:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试结果不存在")

    try:
        import io

        from PIL import Image
        from ultralytics import YOLO

        # 在原图上绘制检测框
        image = Image.open(io.BytesIO(cached["image_bytes"]))
        # TODO: 使用 cv2/PIL 绘制检测框并返回标注后的图片
        # 目前返回原图
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)

        from fastapi.responses import StreamingResponse

        return StreamingResponse(buf, media_type="image/png")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成结果图片失败",
        )
