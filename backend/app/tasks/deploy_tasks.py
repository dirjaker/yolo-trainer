"""模型部署 Celery 任务"""

from app.core.celery import celery_app


@celery_app.task(name="tasks.deploy_model", bind=True, max_retries=1)
def deploy_model_task(self, deploy_id: str):
    """执行模型部署任务

    Args:
        deploy_id: 部署 ID
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import get_settings
    from app.services.deploy_service import execute_deployment

    settings = get_settings()
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    SyncSession = sessionmaker(bind=engine)

    db = SyncSession()
    try:
        execute_deployment(db, deploy_id)
    finally:
        db.close()


@celery_app.task(name="tasks.stop_deployment", bind=True, max_retries=1)
def stop_deployment_task(self, deploy_id: str):
    """停止部署任务

    Args:
        deploy_id: 部署 ID
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import get_settings
    from app.services.deploy_service import execute_stop

    settings = get_settings()
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    SyncSession = sessionmaker(bind=engine)

    db = SyncSession()
    try:
        execute_stop(db, deploy_id)
    finally:
        db.close()
