from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable
from fastapi import Depends, FastAPI, Request
from that_depends import BaseContainer, container_context
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

    if "lifespan" in fastapi_kwargs:
        del fastapi_kwargs["lifespan"]

    """
    Dependency injection context

    Here we inject the request into the container context, so that it can be used by other dependencies.

    """

    async def init_di_context(request: Request) -> AsyncIterator[None]:
        async with container_context({FASTAPI_REQUEST_KEY: request}):
            yield

    if "dependencies" in fastapi_kwargs:
        fastapi_kwargs["dependencies"].insert(0, Depends(init_di_context))

    """
    Finally, Build the application

    """
    return FastAPI(**fastapi_kwargs, lifespan=lifespan)
