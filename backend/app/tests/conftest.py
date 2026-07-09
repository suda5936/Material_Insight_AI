from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db import models as _models  # noqa: F401  (registers ORM metadata)
from app.db.schema import Base
from app.db.session import create_db_engine, get_db
from app.main import create_app
from app.services.embeddings import provide_embedding_provider
from app.services.llm.registry import provide_llm_registry
from app.tests.fakes import HashingEmbeddingProvider, build_fake_registry


@pytest.fixture()
def client(tmp_path) -> Iterator[TestClient]:
    db_path = tmp_path / "test.db"
    engine = create_db_engine(f"sqlite+aiosqlite:///{db_path}")
    session_local = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    async def _create_tables() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _drop_engine() -> None:
        await engine.dispose()

    import asyncio

    asyncio.run(_create_tables())

    async def override_get_db():
        async with session_local() as db:
            yield db

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[provide_embedding_provider] = HashingEmbeddingProvider
    app.dependency_overrides[provide_llm_registry] = build_fake_registry

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(_drop_engine())


@pytest.fixture()
async def db_session(tmp_path):
    db_path = tmp_path / "test_service.db"
    engine = create_db_engine(f"sqlite+aiosqlite:///{db_path}")
    session_local = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_local() as session:
        yield session

    await engine.dispose()
