from typing import Annotated

from that_depends import BaseContainer
from that_depends.providers import Factory

from fastapi import WebSocket, Depends, Response
from fastapi.testclient import TestClient
from starlette.requests import HTTPConnection

import pytest

from faststack.apps.fastapi_app import build_fastapi_app
from faststack.apps.ioc import FaststackContainer


@pytest.fixture()
def app() -> TestClient:
    def get_http_path(request: HTTPConnection) -> str:
        return str(request.url.path)

    class Container(BaseContainer):
        debug: Factory[str] = Factory(
            get_http_path, FaststackContainer.context_request.cast
        )

    app = build_fastapi_app(containers=[Container])

    @app.get("/")
    async def http_handler(http_path: Annotated[str, Depends(Container.debug)]):
        return Response(http_path, media_type="text/plain")

    @app.websocket("/ws")
    async def ws_handler(
        ws: WebSocket, http_path: Annotated[str, Depends(Container.debug)]
    ):
        await ws.accept()
        await ws.send_text(http_path)

    client = TestClient(app)
    return client


async def test_container_context_set_for_http(app: TestClient):
    resp = app.get("/")
    assert resp.text == "/"


async def test_container_context_set_for_websockets(app: TestClient):
    with app.websocket_connect("/ws") as websocket:
        data = websocket.receive_text()
        assert data == "/ws"
