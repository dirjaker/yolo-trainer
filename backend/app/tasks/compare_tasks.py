"""模型对比 Celery 任务"""

from celery import shared_task


@shared_task(bind=True, name="tasks.run_compare", max_retries=1)
def run_compare_task(self, compare_id: str):
    """执行模型对比任务。"""
    from app.core.database import SessionLocal
    from app.services.compare_service import run_compare

    db = SessionLocal()
    try:
        run_compare(db, compare_id)
    finally:
        db.close()
