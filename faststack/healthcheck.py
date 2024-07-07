import argparse
import urllib.request
from http import HTTPStatus
from http.client import HTTPResponse
from urllib.error import URLError

from fastapi import APIRouter, status


def healthcheck(
    url: str, acceptable_status_codes: set[HTTPStatus] | None = None
) -> tuple[bool, HTTPResponse | None]:
    acceptable_status_codes = acceptable_status_codes or {HTTPStatus.OK}

    try:
        resp: HTTPResponse = urllib.request.urlopen(url)
        if resp.status not in acceptable_status_codes:
            return False, resp
        return True, resp
    except URLError:
        return False, None


def command():
    parser = argparse.ArgumentParser(description="Check the health of a service")
    parser.add_argument("url", type=str, help="URL to check")
    parser.add_argument(
        "--status",
        type=int,
        nargs="+",
        default=[HTTPStatus.OK],
        help="Acceptable status codes",
    )
    parser.add_argument("--verbose", action="store_true", help="Prints the response")

    args = parser.parse_args()

    is_healthy, resp = healthcheck(args.url, set(args.status))

    if is_healthy:
        if args.verbose:
            print(
                f"Service is healthy with status code {resp.status} and reason {resp.reason}"
            )
        exit(0)

    if args.verbose:
        print(
            f"Service is unhealthy with status code {resp.status} and reason {resp.reason}"
        )
    exit(1)


def build_healthcheck_router(path: str = "/health") -> APIRouter:
    router = APIRouter()

    @router.get("/health", status_code=status.HTTP_204_NO_CONTENT)
    async def health():
        return

    return router


if __name__ == "__main__":
    command()
