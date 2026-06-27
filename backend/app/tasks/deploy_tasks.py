"""模型部署 Celery 任务"""

from celery import shared_task


@shared_task(bind=True, name="tasks.deploy_model", max_retries=1)
def deploy_model_task(self, deploy_id: str):
    """执行模型部署任务。"""
    from app.core.database import SessionLocal
    from app.services.deploy_service import execute_deployment

    db = SessionLocal()
    try:
        execute_deployment(db, deploy_id)
    finally:
        db.close()


@shared_task(bind=True, name="tasks.stop_deployment", max_retries=1)
def stop_deployment_task(self, deploy_id: str):
    """停止部署任务。"""
    from app.core.database import SessionLocal
    from app.services.deploy_service import execute_stop

    db = SessionLocal()
    try:
        execute_stop(db, deploy_id)
    finally:
        db.close()
