from typing import TypeVar, Generic, get_args, Any

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


Model = TypeVar("Model", bound=SQLModel)


class SQLModelRepository(Generic[Model]):
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    def get_model_cls(self) -> type[Model]:
        cls = type(self)
        if not (orig_bases := getattr(cls, "__orig_bases__")) or len(orig_bases) == 0:
            raise RuntimeError(f"Unable to introspect model for manager {cls}")

        return get_args(orig_bases[0])[0]

    async def get(self, pk: Any) -> Model | None:
        return await self.session.get(self.get_model_cls(), pk)
