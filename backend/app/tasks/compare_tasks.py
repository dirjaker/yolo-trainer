"""模型对比 Celery 任务"""

from app.core.celery import celery_app


@celery_app.task(name="tasks.run_compare", bind=True, max_retries=1)
def run_compare_task(self, compare_id: str):
    """执行模型对比任务

    Args:
        compare_id: 对比任务 ID
    """
    from app.core.database import async_session
    from app.services.compare_service import run_compare

    # Celery 任务是同步的，需要创建同步数据库会话
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker

    from app.core.config import get_settings

    settings = get_settings()
    # 将 async URL 转为 sync URL
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    SyncSession = sessionmaker(bind=engine)

    db = SyncSession()
    try:
        run_compare(db, compare_id)
    finally:
        db.close()
