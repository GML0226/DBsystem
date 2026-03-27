from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 使用 SQLite 数据库，方便本地演示和开发。生产环境可轻松切换为 PostgreSQL 或 MySQL。
DATABASE_URL = "sqlite+aiosqlite:///./lab_management.db"

# 创建异步数据库引擎
# echo=True 会在终端显示执行的 SQL 语句，方便调试
engine = create_async_engine(DATABASE_URL, echo=True)

# 创建异步 Session 工厂
# expire_on_commit=False 避免 commit 之后对已加载关系进行过期操作，防爆 MissingGreenlet
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine, class_=AsyncSession)

# FastAPI 依赖项注入：获取数据库会话
async def get_db():
    async with SessionLocal() as session:
        yield session
