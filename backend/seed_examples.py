"""
YOLO Trainer — 案例种子数据

运行方式:
    cd backend
    python seed_examples.py

将创建 4 个数据集、4 个训练任务、2 个模型版本、1 次超参搜索及其 trial、
以及若干活动日志，全部归属于已存在的 demo3 用户。
"""

import asyncio
import sys
import uuid
import os
from datetime import datetime, timedelta, timezone

# 确保项目在 sys.path 中
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BACKEND_DIR)

# 强制使用绝对路径的数据库
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_BACKEND_DIR}/yolo_trainer.db"

from app.core.database import async_session
from app.models.user import User
from app.models.dataset import Dataset
from app.models.training import Training
from app.models.model import ModelVersion
from app.models.activity import Activity
from app.models.hyperparameter import HyperparameterSearch, HyperparameterTrial

NOW = datetime.now(timezone.utc)


async def seed():
    async with async_session() as db:
        from sqlalchemy import select

        r = await db.execute(select(User).where(User.username == "demo3"))
        admin = r.scalar_one_or_none()
        if not admin:
            print("[ERROR] demo3 用户不存在，请先创建。")
            return
        admin_id = admin.id

        # ── 生成随机 UUID ─────────────────────────────────────────────────
        DS_CV = uuid.uuid4()
        DS_VOC = uuid.uuid4()
        DS_HELMET = uuid.uuid4()
        DS_BCCD = uuid.uuid4()
        TRAIN_CV = uuid.uuid4()
        TRAIN_VOC = uuid.uuid4()
        TRAIN_HELMET = uuid.uuid4()
        TRAIN_BCCD = uuid.uuid4()
        MODEL_CV = uuid.uuid4()
        MODEL_VOC = uuid.uuid4()
        SEARCH_ID = uuid.uuid4()

        print(f" 使用 demo3 用户: {admin_id}")

        # ── 1) 数据集 ────────────────────────────────────────────────────
        datasets = [
            Dataset(
                id=DS_CV,
                name="COCO 2017 行人检测",
                description="从 COCO 2017 提取的行人子集，包含 6,731 张训练图 + 1,489 张验证图。仅保留 person 类。",
                format="yolo",
                classes=["person"],
                stats={"train": 6731, "val": 1489, "test": 1200, "img_size": "640x640"},
                file_path="/data/datasets/coco_person/",
                status="ready",
                user_id=admin_id,
                created_at=NOW - timedelta(days=14),
            ),
            Dataset(
                id=DS_VOC,
                name="Pascal VOC 车辆检测",
                description="Pascal VOC 2007+2012 合并车辆类（car, bus, bicycle, motorbike, train）。共 16,551 张。",
                format="voc",
                classes=["car", "bus", "bicycle", "motorbike", "train"],
                stats={"train": 11540, "val": 5011, "test": 4952},
                file_path="/data/datasets/voc_vehicles/",
                status="ready",
                user_id=admin_id,
                created_at=NOW - timedelta(days=10),
            ),
            Dataset(
                id=DS_HELMET,
                name="安全帽佩戴检测数据集",
                description="施工现场安全帽佩戴检测，含 7,581 张图片，标注 helmet / no_helmet 两类。",
                format="yolo",
                classes=["helmet", "no_helmet"],
                stats={"train": 5000, "val": 1500, "test": 1081},
                file_path="/data/datasets/safety_helmet/",
                status="ready",
                user_id=admin_id,
                created_at=NOW - timedelta(days=5),
            ),
            Dataset(
                id=DS_BCCD,
                name="BCCD 血细胞检测",
                description="Blood Cell Count and Detection，标注 RBC / WBC / Platelets 三类血细胞。医疗影像分析入门案例。",
                format="yolo",
                classes=["RBC", "WBC", "Platelets"],
                stats={"train": 261, "val": 73, "test": 72},
                file_path="/data/datasets/bccd/",
                status="ready",
                user_id=admin_id,
                created_at=NOW - timedelta(days=3),
            ),
        ]
        db.add_all(datasets)
        await db.flush()
        print("  ✓ 数据集: 4 个")

        # ── 2) 训练任务 ──────────────────────────────────────────────────
        trainings = [
            Training(
                id=TRAIN_CV,
                name="YOLOv8n 行人检测 (Baseline)",
                model_version="yolov8n.pt",
                dataset_id=DS_CV,
                status="completed",
                config={
                    "epochs": 100, "batch": 16, "imgsz": 640,
                    "optimizer": "SGD", "lr0": 0.01, "lrf": 0.01,
                    "momentum": 0.937, "weight_decay": 0.0005,
                    "warmup_epochs": 3, "cos_lr": True,
                    "augment": True, "mosaic": 1.0, "mixup": 0.1, "patience": 50,
                },
                metrics={
                    "mAP50": 0.824, "mAP50-95": 0.578,
                    "precision": 0.853, "recall": 0.762, "F1": 0.805, "best_epoch": 87,
                },
                progress=100.0,
                started_at=NOW - timedelta(days=12, hours=3),
                completed_at=NOW - timedelta(days=12),
                user_id=admin_id,
                created_at=NOW - timedelta(days=12, hours=3, minutes=10),
            ),
            Training(
                id=TRAIN_VOC,
                name="YOLOv10n 多车型检测",
                model_version="yolov10n.pt",
                dataset_id=DS_VOC,
                status="running",
                config={
                    "epochs": 150, "batch": 32, "imgsz": 640,
                    "optimizer": "AdamW", "lr0": 0.002, "lrf": 0.001,
                    "momentum": 0.95, "weight_decay": 0.001,
                    "warmup_epochs": 5, "cos_lr": True,
                    "augment": True, "mosaic": 0.8, "mixup": 0.15, "label_smoothing": 0.1,
                },
                progress=62.5,
                started_at=NOW - timedelta(hours=4),
                user_id=admin_id,
                created_at=NOW - timedelta(hours=4, minutes=5),
            ),
            Training(
                id=TRAIN_HELMET,
                name="YOLOv9s 安全帽检测 v1",
                model_version="yolov9s.pt",
                dataset_id=DS_HELMET,
                status="failed",
                config={
                    "epochs": 200, "batch": 8, "imgsz": 640,
                    "optimizer": "AdamW", "lr0": 0.001, "lrf": 0.0001,
                    "momentum": 0.937, "weight_decay": 0.0005,
                    "warmup_epochs": 3, "cos_lr": True,
                    "augment": True, "patience": 100,
                },
                metrics={
                    "error": "CUDA out of memory [epoch 34]\n最大显存占用: 22.3GB / 24GB available\n建议减小 batch_size 或 imgsz",
                    "last_epoch": 34, "best_mAP50_so_far": 0.712,
                },
                progress=17.0,
                started_at=NOW - timedelta(days=2, hours=1),
                completed_at=NOW - timedelta(days=2),
                user_id=admin_id,
                created_at=NOW - timedelta(days=2, hours=1, minutes=5),
            ),
            Training(
                id=TRAIN_BCCD,
                name="YOLOv8m 血细胞检测",
                model_version="yolov8m.pt",
                dataset_id=DS_BCCD,
                status="pending",
                config={
                    "epochs": 300, "batch": 8, "imgsz": 416,
                    "optimizer": "SGD", "lr0": 0.005, "lrf": 0.0001,
                    "momentum": 0.937, "weight_decay": 0.0005,
                    "warmup_epochs": 10, "cos_lr": True,
                    "augment": False, "patience": 150,
                },
                user_id=admin_id,
                created_at=NOW - timedelta(hours=1),
            ),
        ]
        db.add_all(trainings)
        await db.flush()
        print("  ✓ 训练任务: 4 个 (1 完成 / 1 运行中 / 1 失败 / 1 排队)")

        # ── 3) 模型版本 ──────────────────────────────────────────────────
        models = [
            ModelVersion(
                id=MODEL_CV,
                training_id=TRAIN_CV,
                name="行人检测 v1.0",
                version="1.0",
                description="基准行人检测模型，mAP50=82.4%，适用于室内外监控场景。",
                model_version="yolov8n",
                file_path="/data/models/person_detection_v1.pt",
                file_size=6_489_600,
                metrics={
                    "mAP50": 0.824, "mAP50-95": 0.578,
                    "precision": 0.853, "recall": 0.762, "F1": 0.805,
                    "inference_latency_ms": 12.3, "FPS_GPU": 82,
                    "params_M": 3.2, "GFLOPs": 8.7,
                },
                tags=["baseline", "person", "production"],
                created_at=NOW - timedelta(days=12),
            ),
            ModelVersion(
                id=MODEL_VOC,
                training_id=TRAIN_VOC,
                name="车辆检测 v0.1 (训练中)",
                version="0.1-alpha",
                description="YOLOv10 多车型检测（训练进行中）。当前最佳 mAP50 约 42%。",
                model_version="yolov10n",
                file_path="/data/models/vehicle_detection_checkpoint.pt",
                file_size=8_953_856,
                metrics={
                    "mAP50": 0.423, "mAP50-95": 0.287,
                    "precision": 0.451, "recall": 0.389,
                    "note": "训练中，当前第 95/150 轮",
                },
                tags=["vehicle", "in-progress", "yolov10"],
                created_at=NOW - timedelta(hours=3),
            ),
        ]
        db.add_all(models)
        await db.flush()
        print("  ✓ 模型版本: 2 个")

        # ── 4) 活动日志 ──────────────────────────────────────────────────
        activities = [
            Activity(user_id=admin_id, action="dataset_uploaded", resource_type="dataset",
                     resource_id=str(DS_CV), details="上传数据集「COCO 2017 行人检测」",
                     created_at=NOW - timedelta(days=14)),
            Activity(user_id=admin_id, action="training_created", resource_type="training",
                     resource_id=str(TRAIN_CV), details="创建训练「YOLOv8n 行人检测 (Baseline)」",
                     created_at=NOW - timedelta(days=12, hours=3, minutes=10)),
            Activity(user_id=admin_id, action="training_completed", resource_type="training",
                     resource_id=str(TRAIN_CV), details="训练完成 mAP50=82.4% 第 87 轮最佳",
                     created_at=NOW - timedelta(days=12)),
            Activity(user_id=admin_id, action="model_registered", resource_type="model",
                     resource_id=str(MODEL_CV), details="注册模型「行人检测 v1.0」",
                     created_at=NOW - timedelta(days=12)),
            Activity(user_id=admin_id, action="dataset_uploaded", resource_type="dataset",
                     resource_id=str(DS_VOC), details="上传数据集「Pascal VOC 车辆检测」",
                     created_at=NOW - timedelta(days=10)),
            Activity(user_id=admin_id, action="training_created", resource_type="training",
                     resource_id=str(TRAIN_VOC), details="创建训练「YOLOv10n 多车型检测」",
                     created_at=NOW - timedelta(hours=4, minutes=5)),
            Activity(user_id=admin_id, action="training_created", resource_type="training",
                     resource_id=str(TRAIN_HELMET), details="创建训练「YOLOv9s 安全帽检测 v1」",
                     created_at=NOW - timedelta(days=2, hours=1, minutes=5)),
            Activity(user_id=admin_id, action="training_failed", resource_type="training",
                     resource_id=str(TRAIN_HELMET), details="训练失败 CUDA OOM (第 34 轮) | 请减小 batch_size 或 imgsz",
                     created_at=NOW - timedelta(days=2)),
            Activity(user_id=admin_id, action="hyperparameter_search_created", resource_type="hyperparameter_search",
                     resource_id=str(SEARCH_ID), details="创建超参搜索「安全帽-Bayesian优化」",
                     created_at=NOW - timedelta(days=1, hours=6)),
            Activity(user_id=admin_id, action="training_created", resource_type="training",
                     resource_id=str(TRAIN_BCCD), details="创建训练「YOLOv8m 血细胞检测」",
                     created_at=NOW - timedelta(hours=1)),
        ]
        db.add_all(activities)
        await db.flush()
        print("  ✓ 活动日志: 10 条")

        # ── 5) 超参搜索 ──────────────────────────────────────────────────
        search = HyperparameterSearch(
            id=SEARCH_ID,
            name="安全帽检测 - Bayesian 超参优化",
            model_version="yolov9s",
            dataset_id=str(DS_HELMET),
            user_id=admin_id,
            status="completed",
            method="bayesian",
            search_space={
                "lr0": {"type": "loguniform", "min": 1e-4, "max": 1e-2},
                "batch": {"type": "choice", "values": [4, 8, 16]},
                "momentum": {"type": "uniform", "min": 0.85, "max": 0.98},
                "weight_decay": {"type": "loguniform", "min": 1e-5, "max": 1e-3},
                "warmup_epochs": {"type": "int", "min": 1, "max": 10},
            },
            search_config={
                "n_init": 5, "direction": "maximize",
                "target_metric": "mAP50", "early_stop_rounds": 20,
            },
            base_config={"epochs": 50, "imgsz": 640, "optimizer": "AdamW", "cos_lr": True},
            n_trials=12, completed_trials=12,
            best_metric=0.763,
            best_params={"lr0": 0.0021, "batch": 16, "momentum": 0.945, "weight_decay": 3.8e-05, "warmup_epochs": 6},
            best_trial_id=None,  # will set after trials
            created_at=NOW - timedelta(days=1, hours=6),
            updated_at=NOW - timedelta(days=1),
        )
        db.add(search)
        await db.flush()

        # ── 6) 超参搜索 Trials ───────────────────────────────────────────
        trial_params_list = [
            (1, 0.0010, 8, 0.937, 0.0005, 3, 0.681, 1847),
            (2, 0.0050, 16, 0.900, 0.0001, 5, 0.712, 1912),
            (3, 0.0021, 16, 0.945, 0.000038, 6, 0.763, 1803),
            (4, 0.0005, 4, 0.920, 0.0002, 8, 0.653, 2034),
            (5, 0.0080, 8, 0.960, 0.00001, 2, 0.719, 1650),
            (6, 0.0030, 8, 0.880, 0.0008, 4, 0.698, 1788),
            (7, 0.0015, 16, 0.955, 0.0003, 7, 0.742, 1795),
            (8, 0.0002, 4, 0.910, 0.00005, 10, 0.607, 1980),
            (9, 0.0040, 8, 0.930, 0.0004, 5, 0.731, 1822),
            (10, 0.0025, 16, 0.970, 0.00002, 3, 0.715, 1756),
            (11, 0.0060, 4, 0.850, 0.0006, 9, 0.538, 2014),
            (12, 0.0018, 8, 0.938, 0.00015, 6, 0.726, 1805),
        ]

        best_trial_id = None
        best_mAP = 0
        trials = []
        for num, lr0, bs, mom, wd, warm, mAP, dur in trial_params_list:
            tid = uuid.uuid4()
            if mAP > best_mAP:
                best_mAP = mAP
                best_trial_id = tid
            trial = HyperparameterTrial(
                id=tid,
                search_id=SEARCH_ID,
                trial_number=num,
                status="completed",
                params={"lr0": lr0, "batch": bs, "momentum": mom,
                        "weight_decay": wd, "warmup_epochs": warm},
                metric_value=mAP,
                metrics={"mAP50": mAP, "mAP50-95": round(mAP - 0.18, 3),
                         "precision": round(mAP + 0.05, 3), "recall": round(mAP - 0.08, 3)},
                started_at=NOW - timedelta(days=1, hours=6 - num * 0.5),
                completed_at=NOW - timedelta(days=1, hours=6 - num * 0.5, seconds=-dur),
                duration=dur,
            )
            trials.append(trial)

        db.add_all(trials)
        await db.flush()

        # Update best_trial_id on search
        search.best_trial_id = str(best_trial_id)
        await db.flush()

        await db.commit()
        print("  ✓ 超参搜索: 1 次 + 12 个 Trial")

    print("=" * 60)
    print("  案例数据 seed 完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
