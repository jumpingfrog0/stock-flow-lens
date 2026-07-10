from app.db.models import Base
from app.db.session import engine
from sqlalchemy import inspect, text


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def _ensure_sqlite_columns() -> None:
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "stocks" not in inspector.get_table_names():
        return

    stock_columns = {column["name"] for column in inspector.get_columns("stocks")}
    if "industry" not in stock_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE stocks ADD COLUMN industry VARCHAR"))
