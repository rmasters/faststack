import os
from typing import Annotated, Any, AsyncIterator, Callable
from unittest import mock
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import SecretStr
import pytest
from that_depends import BaseContainer
from that_depends.providers import Factory
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


def container_context_test_app(
    dependencies: list[Callable[[Request], Any]] | None = None,
) -> FastAPI:
    """
    A test app that uses the container context to get the user agent from the context request.

    This addresses an issue where the DI middleware was not being added when there were app-side dependencies.

    """

    class Container(BaseContainer):
        user_agent: Factory[str] = Factory(
            lambda req: req.headers.get("user-agent"),
            req=FaststackContainer.context_request,
        )

    if dependencies:
        app = build_fastapi_app(dependencies=dependencies)
    else:
        app = build_fastapi_app()

    @app.get("/")
    async def root(
        user_agent: Annotated[str, Depends(Container.user_agent)],
    ) -> dict[str, str]:
        return {
            "user_agent": user_agent,
        }

    return app


async def test_ensure_container_context_is_available_without_dependencies() -> None:
    app = container_context_test_app()

    with TestClient(app) as testclient:
        response = testclient.get("/", headers={"user-agent": "test-1"})
        assert "user_agent" in response.json()
        assert response.json()["user_agent"] == "test-1"


async def test_ensure_container_context_is_available_with_dependencies() -> None:
    def my_dependency(request: Request) -> int:
        return 123

    app = container_context_test_app(dependencies=[Depends(my_dependency)])

    with TestClient(app) as testclient:
        response = testclient.get("/", headers={"user-agent": "test-2"})
        assert response.json()["user_agent"] == "test-2"
