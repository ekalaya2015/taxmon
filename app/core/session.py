# """SQLAlchemy async engine and sessions tools"""

# from sqlmodel import create_engine
# from app.core import config

# if config.settings.ENVIRONMENT == "PYTEST":
#     sqlalchemy_database_uri = config.settings.TEST_SQLALCHEMY_DATABASE_URI
# else:
#     sqlalchemy_database_uri = config.settings.DEFAULT_SQLALCHEMY_DATABASE_URI


from sqlalchemy.ext.asyncio import create_async_engine

# engine = create_engine(sqlalchemy_database_uri)
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core import config as app_config

DB_POOL_SIZE = 83
WEB_CONCURRENCY = 9
POOL_SIZE = max(DB_POOL_SIZE // WEB_CONCURRENCY, 5)
SIZE_POOL_AIOHTTP = 100

# connect_args = {"check_same_thread": False}

# engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True, connect_args=connect_args, pool_size=POOL_SIZE, max_overflow=64)

engine = create_async_engine(
    app_config.settings.DEFAULT_SQLALCHEMY_DATABASE_URI,
    echo=True,
    future=True,
    pool_size=POOL_SIZE,
    max_overflow=64,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
