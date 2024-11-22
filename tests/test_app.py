import os
from typing import AsyncIterator
from unittest import mock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
import pytest
from faststack.apps import FaststackSettings
from faststack.apps.fastapi_app import build_fastapi_app
from sqlalchemy.ext.asyncio import AsyncEngine

from faststack.apps.ioc import FaststackContainer


async def test_app() -> None:
    app = build_fastapi_app()

    assert isinstance(app, FastAPI)

    with mock.patch.dict(
        os.environ,
        {
            "SECRET_KEY": "test",
            "DB_DSN": "sqlite+aiosqlite:///:memory:",
            "OPENAI_API_KEY": "sk-test",
        },
        clear=True,
    ):
        settings = await FaststackContainer.settings.async_resolve()
        assert isinstance(settings, FaststackSettings)
        assert str(settings.db_dsn) == "sqlite+aiosqlite:///:memory:"

        engine = await FaststackContainer.db_engine.async_resolve()
        assert isinstance(engine, AsyncEngine)

    await FaststackContainer.tear_down()


async def test_app_raises_warning_with_default_secret_key() -> None:
    with pytest.warns(
        UserWarning,
        match="Using default secret key, this should not be used in production",
    ):
        with mock.patch("os.environ", {"DB_DSN": "sqlite+aiosqlite:///:memory:"}):
            settings = await FaststackContainer.settings.async_resolve()
            assert isinstance(settings, FaststackSettings)
            assert isinstance(settings.secret_key, SecretStr)
            assert settings.secret_key.get_secret_value() != ""

    await FaststackContainer.tear_down()


async def test_app_with_custom_lifespan(capsys: pytest.CaptureFixture[str]) -> None:
    async def custom_lifespan(_: FastAPI) -> AsyncIterator[None]:
        print("App started")
        yield
        print("App stopped")

    app = build_fastapi_app(lifespan=custom_lifespan)
    assert isinstance(app, FastAPI)

    with TestClient(app) as testclient:
        response = testclient.get("/")
        assert response.status_code == 404

    assert capsys.readouterr().out == "App started\nApp stopped\n"
