# Faststack app provisioner

This modules provides a pydantic-settings class, a that-depends IoC container, and a FastAPI application factory. This enables a quickstart for FastAPI applications that use a database.

## Usage

Here's a sample application that reads 3 random users from an SQLModel table, and writes a short story about them using OpenAI.

```python
from pydantic import BaseSettings
from that_depends import BaseContainer
from that_depends.providers import Factory
from fastapi import Depends, FastAPI
from faststack.apps import build_fastapi_app
from faststack.models import SQLModelRepository
from sqlalchemy import func
from sqlmodel import SQLModel, Field, select


class MySettings(BaseSettings):
    openai_api_key: SecretStr


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str


class UserRepository(SQLModelRepository[User]):
    async def random(self, count: int = 3) -> Sequence[User]:
        qry = select(User).order_by(func.random()).limit(count)
        return (await self.session.exec(qry)).all()


class MyContainer(BaseContainer):
    settings: Singleton[MySettings] = Singleton(MySettings)
    di_settings: MySettings = settings.cast

    users: Factory[UserRepository] = Factory(UserRepository, FaststackContainer.db_session)

    openai: Singleton[AsyncOpenAI] = Singleton(AsyncOpenAI, api_key=di_settings.openai_api_key.get_secret_value())


app: FastAPI = build_fastapi_app(containers=[MyContainer], title="Storyteller")


@app.get("/")
async def write_story(
    users: Annotated[UserRepository, Depends(MyContainer.users)],
    openai: Annotated[AsyncOpenAI, Depends(MyContainer.openai)],
) -> list[User]:
    # Pick 3 random users
    random_users = await users.random()

    # Write a short story about them
    prompt = f"Write a short story featuring three characters: {", ".join(user.name for user in random_users)}"
    response = await openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a world class short story writer."}, {"role": "user", "content": prompt}],
    )
    story = response.choices[0].message.content

    return {"story": story, "characters": [user.name for user in random_users]}
```

## Under the hood

We provide a Pydantic settings class with the following variables:

- `DB_DSN`: The database connection string
- `SECRET_KEY`: The secret key for the application, used in cookie signing, JWTs, etc.

We also provide an IoC container with the following resources:

- `settings`: Our FaststackSettings instance,
- `db_session`: A context resource of an `AsyncSession` - this will be a fresh session for each request
- `context_request`: Provides the current `fastapi.Request` to dependencies

You can also access the `AsyncEngine` and `async_sessionmaker` via the `db_engine` and `db_session_maker` resources.

Finally the `build_fastapi_app` function creates the FastAPI application, wiring up the container's lifecycle management, and injecting the request into the container context. This function accepts the same arguments as the `FastAPI` constructor.

Container resources can then be accessed using the FastAPI dependency injection system, or directly with `FaststackContainer.settings.sync_resolve()` / `await FaststackContainer.settings.async_resolve()`.

On top of this, you can build your own Settings and Container classes that are specific to your application. If you do create your own container, be sure to pass it to the `containers: list[type[BaseContainer]] | BaseContainer` argument of `build_fastapi_app`, which will connect the container's lifecycle management to the Faststack container.

## Opinionated choices

Faststack serves as a consolidated stack for my side-projects, so I'm starting with what I use. These will be made more flexible in the future.

### SQLModel and async SQLAlchemy connections

I use SQLModel as my ORM, and asynchronous SQLAlchemy - I like the typing-based ORM SQLModel provides, and async database connections enable supporting more web requests per application instance.

## Still to come

- [ ] Alembic database migrations, in practice, this includes:
    - Passing the `SQLModel.metadata` base model from the application code in `alembic/env.py`
    - Setting `config.set_main_option("sqlalchemy.url", str(settings.DB_DSN))` in `alembic/env.py`
    - Changing `connectable` to `settings.db_engine.async_resolve()` in `alembic/env.py`
    - Adding `import sqlmodel` to the migration script template
- [ ] A built-in user/signup/authentication provider
- [ ] Including [SQLAdmin](https://github.com/aminalaee/sqladmin)
- [ ] Add the healthcheck endpoints to the application
- [ ] Support apps without a database
    - Will involve a second container that doesn't include the database.