import random
import string
from dataclasses import asdict, dataclass, fields
from functools import partial
from typing import Any

import pytest

from core.util import (
    DataClass,
    FieldCompatibleIterable,
    FieldCompatibleMapping,
    all_predicates,
    as_base_class,
    filterval,
    pack_args_and_call,
    update_dataclass,
)

alnum = string.ascii_letters + string.digits


class Base:
    def func(self) -> type:
        return type(self)


class Base2:
    def func(self) -> type:
        return type(self)


def test_filterval() -> None:
    r = list(range(1024))
    items = [None] + r + [None]

    assert list(filterval(None, items)) == r


def test_pack_args_and_call() -> None:
    args = [''.join(random.choices(alnum, k=1024)) for _ in range(1024)]

    s = '\n'
    assert pack_args_and_call(s.join, *args) == s.join(args)


def test_all_predicates() -> None:
    count = 0

    def is_string(*s: str) -> bool:
        nonlocal count
        count += 1
        return all(isinstance(_, str) for _ in s)

    def last_is_none(*s: Any) -> bool:
        nonlocal count
        count += 1
        return s[-1] is None

    args = ('', '', '')

    assert all_predicates(is_string)(*args) == True
    assert count == 1

    assert all_predicates(is_string, is_string)(*args) == True
    assert count == 3

    assert all_predicates(is_string, last_is_none, is_string)(*args) == False
    assert count == 5


@pytest.mark.parametrize('cls', (False, True))
def test_as_base_class(cls: bool) -> None:
    result_base = Base().func()

    if not cls:
        decorator = as_base_class
    else:
        result_base2 = Base2().func()

        decorator = partial(as_base_class, cls=Base2)

    class Derived(Base):
        @decorator
        def func(self) -> type:
            return type(self)

    result_derived = Derived().func()

    if not cls:
        assert result_derived == result_base
    else:
        assert result_derived != result_base
        assert result_derived == result_base2


@pytest.mark.parametrize('cls', (False, True))
def test_as_base_class_nodecorator(cls: bool) -> None:
    result_base = Base().func()

    decorator = as_base_class(cls=(Base2 if cls else None))

    class Derived(Base):
        def func(self) -> type:
            return type(self)

    Derived.func = decorator(Derived.func) # ty: ignore error[invalid-assignment]

    result_derived = Derived().func()

    if not cls:
        assert result_derived == result_base
    else:
        assert result_derived != result_base
        assert result_derived == Base2().func()


@pytest.mark.parametrize('other_type', (DataClass, FieldCompatibleMapping, FieldCompatibleIterable, None))
def test_update_dataclass(other_type) -> None:
    @dataclass
    class Obj:
        a: int
        b: str
        c: list[str]
        d: float

    obj = Obj(33, 'cactus', ['yes', 'indeed'], 42.0)
    _other = Obj(1, 'x', ['', ''], 6.9)

    if other_type is DataClass:
        other = _other
    elif other_type is FieldCompatibleMapping:
        other = asdict(_other)
    elif other_type is FieldCompatibleIterable:
        other = tuple(asdict(_other).items())

    if other_type is not None:
        update_dataclass(obj, other)
    else:
        update_dataclass(obj, other=None, **asdict(_other))

    for f in fields(Obj):
        assert getattr(obj, f.name) == getattr(_other, f.name)


def test_update_dataclass_partial() -> None:
    @dataclass
    class Obj:
        a: int
        b: str
        c: list[str]
        d: float

    obj = Obj(33, 'cactus', ['yes', 'indeed'], 42.0)
    obj2 = Obj(33, 'cactus', ['yes', 'indeed'], 42.0)

    @dataclass
    class Other:
        a: int
        c: list[str]

    other = Other(1, ['', ''])

    update_dataclass(obj, other)

    for f in fields(Obj):
        for _f in fields(Other):
            if f.name == _f.name:
                break
        else:
            assert getattr(obj, f.name) == getattr(obj2, f.name)
            continue

        assert getattr(obj, f.name) == getattr(other, f.name)
