from typing import Generic, TypeVar

from faststack.util import resolve_generic_type


T = TypeVar("T")


class Stub(Generic[T]): ...


class IntStub(Stub[int]): ...


class StrStub(Stub[str]): ...


def test_resolve_generic_type():
    assert resolve_generic_type(IntStub) is int
    assert resolve_generic_type(StrStub) is str
