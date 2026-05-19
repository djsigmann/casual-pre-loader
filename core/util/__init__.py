from collections.abc import Callable, Iterable
from dataclasses import Field
from typing import Any, ClassVar, Protocol, runtime_checkable


@runtime_checkable
class DataClass(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]


def all_predicates(*preds: Callable[[Any], bool]) -> Callable[[Any], bool]:
    """
    Returns a function that returns true if all functions return a truthy vlaue when run with the same arguements.

    Args:
        preds: Any number of functions.

    Returns:
        A function that lazily calls all previously provided functions with the same arguments and returns true if they all return true.

    """

    return lambda x: all(p(x) for p in preds)


def filter_dict_keys[T](d: dict[T, Any], keys: Iterable[T]) -> dict[T, Any]:
    return {
        key: d[key]
        for key in keys
        if key in d
    }


def update_dataclass[T: DataClass](obj: T, *args, **kwargs) -> None:
    obj.__dict__.update(*args, **kwargs)
