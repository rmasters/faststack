import secrets
from typing import Annotated
import warnings
from pydantic import Field, SecretStr, UrlConstraints
from pydantic_core import MultiHostUrl, Url
from pydantic_settings import BaseSettings


AsyncPostgresDsn = Annotated[
    MultiHostUrl,
    UrlConstraints(
        host_required=True,
        allowed_schemes=[
            "postgres",
            "postgresql",
            "postgresql+asyncpg",
            "postgresql+psycopg",
        ],
    ),
]

AsyncMySQLDsn = Annotated[
    MultiHostUrl,
    UrlConstraints(
        host_required=True,
        allowed_schemes=["mysql", "mysql+aiomysql", "mysql+asyncmy"],
    ),
]

AsyncSqliteDsn = Annotated[
    Url,
    UrlConstraints(allowed_schemes=["sqlite", "sqlite+aiosqlite"], host_required=False),
]


DEFAULT_SECRET_KEY_LENGTH = 32


def default_secret_key() -> str:
    warnings.warn("Using default secret key, this should not be used in production")
    return secrets.token_urlsafe(DEFAULT_SECRET_KEY_LENGTH)


class FaststackSettings(BaseSettings):
    db_dsn: AsyncPostgresDsn | AsyncMySQLDsn | AsyncSqliteDsn
    secret_key: SecretStr = Field(
        default_factory=default_secret_key, description="Used in cookie signing, etc."
    )
