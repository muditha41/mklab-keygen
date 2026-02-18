"""
Seed the first admin user. Run from repo root with PYTHONPATH=server:
  python -m scripts.seed_admin

Or from server directory:
  python -m scripts.seed_admin

Requires env: DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD (or prompts).
"""
import asyncio
import os
import sys

# Ensure app is on path
_server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

from sqlalchemy import select
from app.core.database import async_session_maker
from app.core.security import hash_password
from app.models.admin import Admin


async def main() -> None:
    email = os.environ.get("DEFAULT_ADMIN_EMAIL") or input("Admin email: ").strip()
    password = os.environ.get("DEFAULT_ADMIN_PASSWORD") or input("Admin password: ").strip()
    if not email or not password:
        print("Email and password required.")
        sys.exit(1)
    async with async_session_maker() as session:
        result = await session.execute(select(Admin).where(Admin.email == email).limit(1))
        if result.scalar_one_or_none():
            print(f"Admin {email} already exists.")
            return
        admin = Admin(
            email=email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"Created admin: {email}")


if __name__ == "__main__":
    asyncio.run(main())
