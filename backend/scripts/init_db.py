"""初始化开发环境默认数据。"""

from __future__ import annotations

import asyncio

import bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import AsyncSessionLocal, engine
from app.models import AdminUser, Pet, User


def hash_password(password: str) -> str:
    """使用 bcrypt 生成密码哈希。"""

    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


async def ensure_admin() -> bool:
    """确保默认管理员账号存在。"""

    async with AsyncSessionLocal() as session:
        existing_admin = await session.scalar(
            select(AdminUser).where(AdminUser.username == "admin")
        )
        if existing_admin is not None:
            return False

        admin = AdminUser(
            username="admin",
            password_hash=hash_password("admin123"),
        )
        session.add(admin)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return False
        return True


async def ensure_test_user_and_pet() -> tuple[bool, bool]:
    """确保测试用户和测试宠物存在。"""

    async with AsyncSessionLocal() as session:
        user_created = False
        pet_created = False

        test_user = await session.scalar(
            select(User).where(User.nickname == "测试用户")
        )
        if test_user is None:
            test_user = User(
                nickname="测试用户",
                user_type="normal",
            )
            session.add(test_user)
            await session.flush()
            user_created = True

        test_pet = await session.scalar(
            select(Pet).where(
                Pet.user_id == test_user.id,
                Pet.nickname == "小橘",
                Pet.is_deleted.is_(False),
            )
        )
        if test_pet is None:
            test_pet = Pet(
                user_id=test_user.id,
                nickname="小橘",
                species="猫",
                breed="中华田园猫",
                weight=4.5,
            )
            session.add(test_pet)
            pet_created = True

        await session.commit()
        return user_created, pet_created


async def seed_initial_data() -> None:
    """插入默认管理员、测试用户与测试宠物。"""

    admin_created = await ensure_admin()
    user_created, pet_created = await ensure_test_user_and_pet()

    print(f"管理员账号: {'已创建' if admin_created else '已存在'}")
    print(f"测试用户: {'已创建' if user_created else '已存在'}")
    print(f"测试宠物: {'已创建' if pet_created else '已存在'}")


async def async_main() -> None:
    """执行异步初始化逻辑。"""

    try:
        await seed_initial_data()
    finally:
        await engine.dispose()


def main() -> None:
    """脚本入口。"""

    asyncio.run(async_main())


if __name__ == "__main__":
    main()
