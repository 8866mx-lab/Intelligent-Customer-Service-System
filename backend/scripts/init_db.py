"""
数据库初始化脚本。

创建所有表并插入种子数据。

运行方式：
    cd backend
    PYTHONPATH=.. python scripts/init_db.py

Windows PowerShell:
    cd backend
    $env:PYTHONPATH=".."
    python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

# 确保 src 可导入
sys.path.insert(0, str(Path(__file__).parent.parent))

import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Base, User
from src.db.session import async_session_maker, engine


async def create_tables() -> None:
    """创建所有数据库表。"""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Tables created")


async def insert_seed_data() -> None:
    """插入种子数据：测试用户。"""
    print("Inserting seed data...")

    async with async_session_maker() as session:
        # 检查是否已存在种子用户
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.username == "zhangsan"))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("[OK] Seed user 'zhangsan' already exists, skipping")
            return

        # 创建种子用户：zhangsan / password123（bcrypt hash）
        password_plain = "password123"
        password_hash = bcrypt.hashpw(
            password_plain.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        seed_user = User(username="zhangsan", password_hash=password_hash)

        session.add(seed_user)
        await session.commit()
        await session.refresh(seed_user)

        print(f"[OK] Seed user created: username=zhangsan, id={seed_user.id}")


async def main() -> None:
    """主函数。"""
    print("=" * 60)
    print("智能客服系统 - 数据库初始化")
    print("=" * 60)

    try:
        await create_tables()
        await insert_seed_data()

        print("=" * 60)
        print("[SUCCESS] Database initialization completed successfully")
        print("=" * 60)
        print("\nYou can now start the backend server:")
        print("  cd backend")
        print("  PYTHONPATH=.. python -m uvicorn src.main:app --host 127.0.0.1 --port 8099")
        print("\nTest login credentials:")
        print("  Username: zhangsan")
        print("  Password: password123")

    except Exception as e:
        print(f"[ERROR] Error during database initialization: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
