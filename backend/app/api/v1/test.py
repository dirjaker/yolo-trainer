"""测试 / 推理路由。"""

import io
import os
import time
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.model import ModelVersion
from app.models.training import Training
from app.models.user import User
from app.schemas.test import TestResult

router = APIRouter()

# 简单的内存缓存（生产环境应使用 Redis）
_test_results: dict = {}


async def _get_owned_model_for_test(
    model_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> ModelVersion:
    """获取模型并校验所有权（通过 Training.user_id）。"""
    result = await db.execute(
        select(ModelVersion)
        .join(Training, ModelVersion.training_id == Training.id)
        .where(ModelVersion.id == model_id, Training.user_id == user_id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在或无权使用")
    if not model.file_path or not os.path.isfile(model.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型文件不存在")
    return model


def _draw_boxes(image_bytes: bytes, detections: list, class_names: dict = None) -> bytes:
    """在图片上绘制检测框并返回带标注的 PNG 字节。"""
    from PIL import Image, ImageDraw, ImageFont

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(image)

    # 尝试加载字体，失败则用默认
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except (OSError, IOError):
        font = ImageFont.load_default()

    # 为每个类别分配颜色
    class_colors: dict = {}

    for det in detections:
        bbox = det.get("bbox", {})
        x1, y1, x2, y2 = bbox.get("x1", 0), bbox.get("y1", 0), bbox.get("x2", 0), bbox.get("y2", 0)
        cls_name = det.get("class_name", "?")
        conf = det.get("confidence", 0.0)

        # 每类固定颜色
        if cls_name not in class_colors:
            import hashlib
            h = int(hashlib.md5(cls_name.encode()).hexdigest()[:8], 16)
            class_colors[cls_name] = (
                (h >> 16) & 0xFF,
                (h >> 8) & 0xFF,
                h & 0xFF,
            )
        color = class_colors[cls_name]

        # 画矩形
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)

        # 画标签
        label = f"{cls_name} {conf:.2f}"
        bbox = draw.textbbox((x1, y1 - 18), label, font=font)
        draw.rectangle(bbox, fill=color)
        # 计算文字亮度来确定文字颜色
        brightness = (color[0] * 299 + color[1] * 587 + color[2] * 114) / 1000
        text_color = (255, 255, 255) if brightness < 128 else (0, 0, 0)
        draw.text((x1, y1 - 18), label, fill=text_color, font=font)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


@router.post("/predict", response_model=TestResult)
async def predict_single(
    file: UploadFile = File(..., description="待检测图片"),
    model_id: uuid.UUID = Query(..., description="使用的模型 ID"),
    confidence: float = Query(0.25, ge=0.0, le=1.0, description="置信度阈值"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """单图推理预测（仅限自己的模型）。"""
    model = await _get_owned_model_for_test(model_id, current_user.id, db)

    image_bytes = await file.read()
    start_time = time.time()

    try:
        from ultralytics import YOLO

        yolo_model = YOLO(model.file_path)
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

    _test_results[test_id] = {
        "result": test_result,
        "image_bytes": image_bytes,
        "detections": detections,
        "filename": file.filename,
    }
    return test_result


@router.post("/batch-predict")
async def predict_batch(
    files: list[UploadFile] = File(..., description="待检测图片列表"),
    model_id: uuid.UUID = Query(..., description="使用的模型 ID"),
    confidence: float = Query(0.25, ge=0.0, le=1.0, description="置信度阈值"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量推理预测（仅限自己的模型）。"""
    model = await _get_owned_model_for_test(model_id, current_user.id, db)

    try:
        from ultralytics import YOLO
        yolo_model = YOLO(model.file_path)
    except ImportError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="推理引擎未安装")

    batch_id = str(uuid.uuid4())
    batch_results = []

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
        tr = TestResult(
            test_id=test_id,
            model_id=str(model_id),
            detections=detections,
            inference_time_ms=round(inference_time_ms, 2),
        )
        batch_results.append(tr)
        _test_results[test_id] = {
            "result": tr, "image_bytes": image_bytes, "detections": detections, "filename": upload_file.filename
        }

    return {"batch_id": batch_id, "total": len(batch_results), "results": batch_results}


@router.get("/results/{test_id}", response_model=TestResult)
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
    """获取带检测框标注的结果图片。"""
    cached = _test_results.get(test_id)
    if not cached:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试结果不存在")

    try:
        annotated = _draw_boxes(cached["image_bytes"], cached["detections"])
        return StreamingResponse(io.BytesIO(annotated), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"生成结果图片失败: {e}")
