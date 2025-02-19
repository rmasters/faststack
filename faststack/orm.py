from typing import TypeVar, Generic, Any

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from faststack.util import resolve_generic_type


Model = TypeVar("Model", bound=SQLModel)


class SQLModelRepository(Generic[Model]):
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    def get_model_cls(self) -> type[Model]:
        return resolve_generic_type(type(self))

    async def get(self, pk: Any) -> Model | None:
        return await self.session.get(self.get_model_cls(), pk)
