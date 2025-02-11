from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable
from fastapi import FastAPI, Depends
from starlette.requests import HTTPConnection
from that_depends import BaseContainer, container_context
from that_depends.providers.context_resources import ContextScopes
from faststack.apps.ioc import FASTAPI_REQUEST_KEY, FaststackContainer


def build_fastapi_app(
    *,
    containers: type[BaseContainer] | list[type[BaseContainer]] | None = None,
    **fastapi_kwargs: Any,  # TODO: Inherit the ParamSpec from FastAPI (e.g. the callable signature approach)
) -> FastAPI:
    """
    Builds a FastAPI application, with the Faststack container lifecycle management.

    """

    """
    Link application containers to the global container to propagate init_resources, tear_down, etc.
    
    """
    all_containers = []
    if isinstance(containers, BaseContainer):
        all_containers.append(containers)
    elif isinstance(containers, list):
        all_containers.extend(containers)

    FaststackContainer.connect_containers(*all_containers)

    """
    Application lifespans

    We need to call tear_down after the application has stopped, but also support an application lifespan.
    
    """
    custom_lifespan: Callable[[FastAPI], AsyncIterator[None | Any]] | None = (
        fastapi_kwargs.pop("lifespan", None)
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None | Any]:
        # Wrap the custom lifespan if provided
        if custom_lifespan:
            async for state in custom_lifespan(app):
                yield state
        else:
            yield None

        await FaststackContainer.tear_down()

    dependencies = fastapi_kwargs.pop("dependencies", [])

    async def websocket_di(httpconn: HTTPConnection) -> AsyncIterator[None]:
        """Ensure container context is set for both http and websocket requests"""
        async with container_context(
            scope=ContextScopes.REQUEST,
            global_context={FASTAPI_REQUEST_KEY: httpconn},
            reset_all_containers=True,
        ):
            yield

    dependencies.insert(0, Depends(websocket_di))

    app = FastAPI(**fastapi_kwargs, lifespan=lifespan, dependencies=dependencies)

    """
    Dependency injection context

    Here we inject the request into the container context, so that it can be used by other dependencies.

    This needs to be done as a middleware, as request dependencies appear to resolve before app dependencies.

    """

    # TODO: Rewrite as a starlette custom middleware
    # @app.middleware("http")
    # async def add_request_to_container_context(request: HTTPConnection, call_next):
    #    async with container_context({FASTAPI_REQUEST_KEY: request}):
    #        return await call_next(request)

    return app
