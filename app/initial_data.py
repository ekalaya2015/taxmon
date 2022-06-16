"""
Put here any Python code that must be runned before application startup.
It is included in `init.sh` script.

By defualt `main` create a superuser if not exists
"""

import asyncio
from datetime import datetime

from sqlalchemy import select

from app.core import config, security

# from app.core.session import async_session
from app.core.session import SessionLocal
from app.model.models import Role, User


async def main() -> None:
    print("Start initial data")
    async with SessionLocal() as session:
        result = await session.exec(
            select(User).where(User.username == config.settings.FIRST_SUPERUSER_EMAIL)
        )
        user = result.one_or_none()
        if user is None:
            new_superuser = User(
                username=config.settings.FIRST_SUPERUSER_EMAIL,
                hashed_password=security.get_password_hash(
                    config.settings.FIRST_SUPERUSER_PASSWORD
                ),
                role=Role.admin,
                created_at=datetime.now(),
                modified_at=datetime.now(),
                first_name="Ridwan",
                last_name="Fardani",
            )
            session.add(new_superuser)
            await session.commit()
            print("Superuser was created")
        else:
            print("Superuser already exists in database")

        print("Initial data created")


if __name__ == "__main__":
    asyncio.run(main())
