# faststack

A set of common utilities that I add to nearly every FastAPI project, including:

- A pure-Python healthcheck,
- An SQLModel-bound model repository class,
- An async-friendly Typer base-class, based on discussions in the Typer repo

The intent is to grow this organically into a more fully-featured web stack,
based on FastAPI, SQLModel, and other async friendly packages.

## Usage: install `faststack`

### SQLModel repository class

The repository class binds to an AsyncSession, and provides a few common methods
for model retrieval:

*   `get(pk) -> Model | None`
*   `all() -> Sequence[Model]`

```python
from typing import Sequence
from faststack.models import SQLModelRepository
from sqlalchemy import desc
from sqlalchemy.orm import selectinload
from sqlmodel import select

from .models import Article, Comment

class ArticleRepository(SQLModelRepository[Article]): ...

class CommentRepository(SQLModelRepository[Comment]):
    async def get_for_article(self, article: Article) -> Sequence[Comment]:
        qry = select(Comment) \
            .where(Comment.article == article) \
            .order_by(desc(Comment.posted_at)) \
            .options(selectinload(Comment.article))
        return (await self.session.exec(qry)).fetch_all()
```

This will be extended to add pagination, magic methods, etc.

### Healthchecks

Provides a healthcheck endpoint and a command-line tool to add a container
healthcheck. The main motivation behind this is to remove the need to add
cURL to the application container image.

The default healthcheck router adds an endpoint at `/health` that returns a HTTP 204 response.

A command line utility is provided to hit this endpoint, and alert based on status.

```python
from faststack.healthcheck import build_healthcheck_router

app = FastAPI()

app.include_router(build_healthcheck_router(path="/health"))
```

```Dockerfile
HEALTHCHECK CMD ["python", "-m", "faststack.healthcheck"]

# Supported arguments
EXPOSE 3000
HEALTHCHECK CMD ["python", "-m", "faststack.healthcheck", "--status=204", "--status=200", "--url=http://localhost:3000/custom-health"]
```

### Async-friendly Typer

A stop-gap Typer class that supports async commands, based on comments from:

* https://github.com/tiangolo/typer/issues/88
* https://github.com/tiangolo/typer/issues/80

```
from faststack.cli import AsyncTyper

app = AsyncTyper()

@app.command()
async def my_command():
    await asyncio.sleep(1)
```

