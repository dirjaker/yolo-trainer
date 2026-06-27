"""训练相关 Celery 任务 —— 调度 Worker 训练器执行真实 YOLO 训练。"""

import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from celery import shared_task

logger = logging.getLogger(__name__)

# 确保 worker/ 包可被导入
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# 训练输出 & 日志根目录
_TRAINING_ROOT = Path(os.environ.get("TRAINING_DIR", "/data/training"))
_LOGS_DIR = _TRAINING_ROOT / "logs"


def _get_trainer(model_version: str):
    """根据 model_version 前缀分派到对应的训练器。"""
    mv_lower = model_version.lower()
    if mv_lower.startswith("yolov5"):
        from worker.trainer.yolov5 import YOLOv5Trainer
        return YOLOv5Trainer()
    elif mv_lower.startswith("yolov8"):
        from worker.trainer.yolov8 import YOLOv8Trainer
        return YOLOv8Trainer()
    elif mv_lower.startswith("yolov9"):
        from worker.trainer.yolov9 import YOLOv9Trainer
        return YOLOv9Trainer()
    elif mv_lower.startswith("yolov10"):
        from worker.trainer.yolov10 import YOLOv10Trainer
        return YOLOv10Trainer()
    else:
        # 默认回退到 YOLOv8 trainer（ultralytics 通用）
        from worker.trainer.yolov8 import YOLOv8Trainer
        return YOLOv8Trainer()


def _resolve_dataset_config(dataset_id: str) -> str:
    """从数据集记录解析出 YOLO 格式的 data.yaml 路径。"""
    from app.core.database import SessionLocal
    from app.models.dataset import Dataset

    db = SessionLocal()
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

        # 数据集解压后在同目录下应有 data.yaml
        extract_dir = Path(dataset.file_path).with_suffix("")
        data_yaml = extract_dir / "data.yaml"
        if data_yaml.exists():
            return str(data_yaml)

        # 回退：在 extract_dir 下查找任意 .yaml
        yamls = list(extract_dir.glob("*.yaml")) + list(extract_dir.glob("*.yml"))
        if yamls:
            return str(yamls[0])

        raise ValueError(f"No data.yaml found in {extract_dir}")
    finally:
        db.close()


@shared_task(bind=True, name="tasks.train_model", max_retries=0)
def train_model_task(self, training_id: str, config: dict) -> dict:
    """执行模型训练 —— 调用真实 YOLO 训练引擎。

    Args:
        training_id: 训练任务 ID (UUID string)
        config: {
            model_version, dataset_id, epochs, batch_size, img_size,
            learning_rate, device, workers, resume, augment, extra, ...
        }
    """
    from app.core.database import SessionLocal
    from app.models.training import Training
    from app.models.model import ModelVersion

    db = SessionLocal()
    training = None
    try:
        training = db.query(Training).filter(Training.id == training_id).first()
        if not training:
            raise ValueError(f"Training {training_id} not found")

        # 更新状态为 running
        training.status = "running"
        training.started_at = datetime.now(timezone.utc)
        db.commit()

        # 解析数据集配置路径
        dataset_config = _resolve_dataset_config(str(training.dataset_id))

    except Exception as exc:
        logger.exception("训练前置准备失败 training=%s", training_id)
        if training:
            training.status = "failed"
            training.metrics = {"error": str(exc)}
            db.commit()
        db.close()
        return {"status": "failed", "error": str(exc)}

    db.close()

    # ── 构造日志文件 ──────────────────────────────────────────────────
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = _LOGS_DIR / f"{training_id}.log"

    # ── 构造 TrainConfig ──────────────────────────────────────────────
    from worker.trainer.base import TrainConfig, TrainCallback, TrainResult

    output_dir = str(_TRAINING_ROOT / training_id)

    train_cfg = TrainConfig(
        model_version=config.get("model_version", training.model_version),
        dataset_config=dataset_config,
        epochs=config.get("epochs", 100),
        batch_size=config.get("batch_size", 16),
        img_size=config.get("img_size", 640),
        learning_rate=config.get("learning_rate", 0.01),
        device=config.get("device", "0"),
        workers=config.get("workers", 8),
        resume=config.get("resume", False),
        pretrained_weights=config.get("pretrained_weights"),
        output_dir=output_dir,
        project_name=training.name.replace(" ", "_")[:64],
        patience=config.get("patience", 50),
        augment=config.get("augment", True),
        extra=config.get("extra", {}),
    )

    # ── 训练回调：写日志 + 更新进度 ───────────────────────────────────
    class _TaskCallback(TrainCallback):
        def on_train_start(self, cfg: TrainConfig) -> None:
            msg = f"[{datetime.now(timezone.utc).isoformat()}] 训练开始 model={cfg.model_version} epochs={cfg.epochs}\n"
            _append_log(log_path, msg)

        def on_epoch_end(self, epoch: int, metrics: dict) -> None:
            parts = [f"[{datetime.now(timezone.utc).isoformat()}] Epoch {epoch}"]
            for k, v in metrics.items():
                parts.append(f"{k}={v:.4f}")
            _append_log(log_path, "  ".join(parts) + "\n")

            # 更新数据库进度
            _update_progress(training_id, epoch, train_cfg.epochs)

        def on_train_end(self, result: TrainResult) -> None:
            status_str = "成功" if result.success else f"失败: {result.error}"
            _append_log(log_path, f"[{datetime.now(timezone.utc).isoformat()}] 训练{status_str} 耗时={result.train_time:.1f}s\n")

    callback = _TaskCallback()

    # ── 执行真实训练 ──────────────────────────────────────────────────
    trainer = _get_trainer(train_cfg.model_version)
    trainer.callback = callback
    result: TrainResult = trainer.train(train_cfg)

    # ── 保存结果 ──────────────────────────────────────────────────────
    db = SessionLocal()
    try:
        training = db.query(Training).filter(Training.id == training_id).first()
        if not training:
            raise ValueError(f"Training {training_id} disappeared")

        if result.success:
            training.status = "completed"
            training.completed_at = datetime.now(timezone.utc)
            training.progress = 100.0
            training.metrics = {
                "mAP50": result.best_map50,
                "mAP50-95": result.best_map50_95,
                "total_epochs": result.total_epochs,
                "train_time_s": result.train_time,
                **result.metrics,
            }

            # 创建 ModelVersion 记录
            model = ModelVersion(
                training_id=training.id,
                name=f"{training.name}",
                version=f"v1-{training_id[:8]}",
                model_version=train_cfg.model_version,
                file_path=result.model_path,
                file_size=os.path.getsize(result.model_path) if os.path.isfile(result.model_path) else 0,
                metrics=training.metrics,
                tags=[train_cfg.model_version],
            )
            db.add(model)
            db.commit()
            db.refresh(model)
            model_id = str(model.id)
        else:
            training.status = "failed"
            training.metrics = {"error": result.error or "未知错误"}
            db.commit()
            model_id = ""

        logger.info("训练 %s 完成 status=%s", training_id, training.status)
        return {"status": training.status, "model_id": model_id, "metrics": training.metrics}

    except Exception as exc:
        logger.exception("保存训练结果失败 training=%s", training_id)
        if training:
            training.status = "failed"
            training.metrics = {"error": str(exc)}
            db.commit()
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


@shared_task(bind=True, name="tasks.process_dataset", max_retries=2)
def process_dataset_task(self, dataset_id: str) -> dict:
    """异步处理数据集：解压 ZIP、验证格式、统计信息。

    数据集 ZIP 解压到同目录（去除 .zip 后缀），并在目录下生成 data.yaml。
    """
    import json
    import zipfile

    from app.core.database import SessionLocal
    from app.models.dataset import Dataset

    db = SessionLocal()
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

        dataset.status = "processing"
        db.commit()

        zip_path = Path(dataset.file_path)
        if not zip_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        extract_dir = zip_path.with_suffix("")
        extract_dir.mkdir(parents=True, exist_ok=True)

        # 解压（防 Zip Slip）
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.namelist():
                # 拒绝路径穿越
                member_path = (extract_dir / member).resolve()
                if not str(member_path).startswith(str(extract_dir.resolve())):
                    logger.warning("跳过危险路径: %s", member)
                    continue
                zf.extract(member, extract_dir)

        # 统计信息
        images_dir = extract_dir / "images"
        labels_dir = extract_dir / "labels"
        train_images = list((images_dir / "train").glob("*")) if (images_dir / "train").exists() else []
        val_images = list((images_dir / "val").glob("*")) if (images_dir / "val").exists() else []
        test_images = list((images_dir / "test").glob("*")) if (images_dir / "test").exists() else []

        # 读取类别
        classes = []
        data_yaml = extract_dir / "data.yaml"
        if data_yaml.exists():
            import yaml
            try:
                with open(data_yaml) as f:
                    yaml_data = yaml.safe_load(f)
                classes = yaml_data.get("names", []) or yaml_data.get("nc", [])
                if isinstance(classes, dict):
                    classes = list(classes.values())
            except Exception:
                pass

        stats = {
            "total_images": len(train_images) + len(val_images) + len(test_images),
            "train_images": len(train_images),
            "val_images": len(val_images),
            "test_images": len(test_images),
            "classes": len(classes),
            "class_names": classes,
        }

        dataset.stats = stats
        dataset.status = "ready"
        db.commit()

        logger.info("数据集 %s 处理完成 stats=%s", dataset_id, json.dumps(stats, ensure_ascii=False))
        return {"status": "ready", "dataset_id": dataset_id, "stats": stats}

    except Exception as exc:
        logger.exception("数据集处理失败 dataset=%s", dataset_id)
        try:
            dataset2 = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if dataset2:
                dataset2.status = "error"
                db.commit()
        except Exception:
            pass
        raise
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════
# 内部辅助函数
# ═══════════════════════════════════════════════════════════════════════

def _append_log(log_path: Path, line: str) -> None:
    """追加一行日志到训练日志文件。"""
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def _update_progress(training_id: str, current_epoch: int, total_epochs: int) -> None:
    """更新训练任务进度到数据库。"""
    from app.core.database import SessionLocal
    from app.models.training import Training

    db = SessionLocal()
    try:
        training = db.query(Training).filter(Training.id == training_id).first()
        if training and total_epochs > 0:
            training.progress = min(99.0, round(current_epoch / total_epochs * 100, 1))
            db.commit()
    except Exception:
        pass
    finally:
        db.close()
