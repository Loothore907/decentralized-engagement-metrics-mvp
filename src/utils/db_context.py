# src/utils/db_context.py

from contextlib import asynccontextmanager
from src.database.sql_db_manager import SQLDBManager

@asynccontextmanager
async def get_db():
    db = SQLDBManager()
    await db.initialize()
    try:
        yield db
    finally:
        await db.close()