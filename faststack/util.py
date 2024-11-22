from types import get_original_bases
from typing import get_args


def resolve_generic_type(cls: type) -> type:
    if not (orig_bases := get_original_bases(cls)) or len(orig_bases) == 0:
        raise RuntimeError(f"Unable to introspect model for manager {cls}")

    return get_args(orig_bases[0])[0]
