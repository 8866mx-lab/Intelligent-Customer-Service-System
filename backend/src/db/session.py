"""
智能客服系统数据库会话管理。

基于 pycore.integrations.db.session 模板配置异步数据库引擎和会话。
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from pycore.core.logger import get_logger

logger = get_logger()


class DBSettings(BaseSettings):
    """数据库配置。"""

    database_url: str = Field(default="sqlite+aiosqlite:///./data/app.db")

    model_config = {
        "env_file": str(Path(__file__).parent.parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


_db_settings = DBSettings()
DATABASE_URL = _db_settings.database_url

# SQLite 路径规范化：解析为绝对路径，并自动创建父目录
if DATABASE_URL.startswith("sqlite"):
    # 提取路径部分（去掉 sqlite+aiosqlite:///./ 或 sqlite:///./）
    if ":///./" in DATABASE_URL:
        relative_path = DATABASE_URL.split(":///.")[1]
    elif ":///" in DATABASE_URL:
        relative_path = DATABASE_URL.split(":///")[1]
    else:
        relative_path = "data/app.db"

    # 去掉开头的 ./ 或 .\
    relative_path = relative_path.lstrip("./").lstrip(".\\")

    # 转换为绝对路径（从项目根目录，即 backend/ 的上一级）
    project_root = Path(__file__).parent.parent.parent.parent
    db_file = project_root / relative_path
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # 重构 DATABASE_URL
    DATABASE_URL = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    logger.info(f"SQLite database path: {db_file}")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"timeout": 30},
)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # noqa: ARG001
    """Improve SQLite concurrency for API + background ingest."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（用于 FastAPI Depends）。"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """上下文管理器形式的数据库会话。"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库（创建表）。"""
    from src.db.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


async def close_db() -> None:
    """关闭数据库连接。"""
    await engine.dispose()
    logger.info("Database connection closed")
