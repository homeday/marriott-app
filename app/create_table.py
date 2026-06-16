import os
import time

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import inspect


def build_connection_url() -> str:
    username = os.environ.get("USERNAME")
    password = os.environ.get("PASSWORD")
    endpoint = os.environ.get("ENDPOINT")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "appdb")

    missing = [
        name
        for name, value in {
            "USERNAME": username,
            "PASSWORD": password,
            "ENDPOINT": endpoint,
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(f"Missing required DB env vars: {', '.join(missing)}")

    return f"postgresql+psycopg2://{username}:{password}@{endpoint}:{db_port}/{db_name}"


def create_table() -> None:
    connection_url = build_connection_url()

    table_name = os.environ.get("INIT_TABLE_NAME", "app_table")
    retries = int(os.environ.get("DB_INIT_RETRIES", "5"))
    retry_delay_seconds = int(os.environ.get("DB_INIT_RETRY_DELAY", "3"))

    metadata = MetaData()
    Table(
        table_name,
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
        Column("note", String, nullable=True),
    )

    for attempt in range(1, retries + 1):
        try:
            engine = create_engine(connection_url)
            inspector = inspect(engine)
            existed_before = inspector.has_table(table_name)
            metadata.create_all(engine)

            inspector = inspect(engine)
            if not inspector.has_table(table_name):
                raise RuntimeError(f"Table '{table_name}' was not found after create_all")

            required_columns = {"id", "created_at", "note"}
            actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
            missing_columns = required_columns - actual_columns
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise RuntimeError(f"Table '{table_name}' is missing required columns: {missing}")

            engine.dispose()
            status = "already existed" if existed_before else "created"
            print(f"Table '{table_name}' {status} and schema check passed")
            return
        except Exception as exc:
            if attempt == retries:
                raise RuntimeError(
                    f"Failed creating table '{table_name}' after {retries} attempts"
                ) from exc
            print(f"Attempt {attempt}/{retries} failed: {exc}. Retrying in {retry_delay_seconds}s")
            time.sleep(retry_delay_seconds)


if __name__ == "__main__":
    create_table()
