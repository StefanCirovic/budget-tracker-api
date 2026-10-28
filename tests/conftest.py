import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def point_app_to_test_database() -> None:
    load_dotenv()
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        raise RuntimeError("TEST_DATABASE_URL environment variable is not set.")
    if test_database_url == os.environ.get("DATABASE_URL"):
        raise RuntimeError("TEST_DATABASE_URL must point to a different database than DATABASE_URL.")
    os.environ["DATABASE_URL"] = test_database_url


point_app_to_test_database()


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    from alembic import command
    from alembic.config import Config

    config = Config(str(ALEMBIC_INI))
    config.attributes["configure_logger"] = False
    command.downgrade(config, "base")
    command.upgrade(config, "head")


@pytest.fixture(autouse=True)
def clean_tables(migrated_database: None) -> None:
    from sqlalchemy import text

    from app.database import engine
    from app.models import Base

    table_names = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
