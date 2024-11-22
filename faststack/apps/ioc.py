from typing import (
    AsyncIterator,
)
from fastapi import Request
from that_depends import BaseContainer, fetch_context_item
from that_depends.providers import Singleton, Factory, ContextResource
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from faststack.apps.settings import FaststackSettings


FASTAPI_REQUEST_KEY = "fastapi_request"


def get_db_engine(settings: FaststackSettings) -> AsyncEngine:
    return create_async_engine(str(settings.db_dsn))


async def get_db_session(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_maker() as session:
        yield session


class FaststackContainer(BaseContainer):
    settings: Singleton[FaststackSettings] = Singleton(FaststackSettings)  # type: ignore[call-arg] # Ignore required arguments for BaseSettings

    db_engine: Factory[AsyncEngine] = Factory(get_db_engine, settings.cast)
    db_session_maker: Factory[async_sessionmaker[AsyncSession]] = Factory(
        async_sessionmaker,
        db_engine.cast,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    db_session: ContextResource[AsyncSession] = ContextResource(
        get_db_session, db_session_maker.cast
    )

    context_request: Factory[Request] = Factory(
        lambda: fetch_context_item(FASTAPI_REQUEST_KEY),
    )
