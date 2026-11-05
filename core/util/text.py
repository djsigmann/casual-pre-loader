import re
from collections.abc import Iterable
from functools import Placeholder, partial
from itertools import islice

# vertical lists get more room than inline ones
DEFAULT_LIST_LIMIT = 10
DEFAULT_INLINE_LIMIT = 5


def _more(remaining: int, noun: str) -> str:
    '''
    Format the count of truncated items, e.g. "2 more VPK files" or "1 more VPK file".

    Args:
        remaining: How many items were left out.
        noun: Optional plural word for the items. When `remaining` is 1 a single
            trailing "s" is stripped, so irregular plurals like "directories"
            won't singularize correctly.

    Returns:
        The count, followed by the noun if one was given.
    '''

    if remaining == 1:
        noun = noun.removesuffix('s')
    return f"{remaining} more{f' {noun}' if noun else ''}"


def bullet_list(items: Iterable[object], limit: int = DEFAULT_LIST_LIMIT, *, noun: str = "", bullet: str = "• ") -> str:
    '''
    Format items one per line, truncating past `limit` with an "... and N more" line.

    Args:
        items: The things to list.
        limit: How many to show before truncating.
        noun: Optional plural word for the truncation line, e.g. "VPK files".
        bullet: Prefix for each line; pass "" for a plain newline-joined list.

    Returns:
        The formatted list, without a trailing newline.
    '''

    items = iter(items)
    lines = [f"{bullet}{item}" for item in islice(items, limit)]

    # whatever islice didn't take is the overflow
    remaining = sum(1 for _ in items)
    if remaining:
        lines.append(f"{bullet}... and {_more(remaining, noun)}")

    return "\n".join(lines)


def inline_list(items: Iterable[object], limit: int = DEFAULT_INLINE_LIMIT, *, noun: str = "", empty: str = "none") -> str:
    '''
    Format items as a comma-separated run, truncating past `limit` with "and N more".

    Args:
        items: The things to list.
        limit: How many to show before truncating.
        noun: Optional plural word for the truncation tail, e.g. "mods".
        empty: What to return when there is nothing to list.

    Returns:
        The formatted list, without a trailing newline.
    '''

    items = iter(items)
    shown = [str(item) for item in islice(items, limit)]
    if not shown:
        return empty

    text = ", ".join(shown)

    remaining = sum(1 for _ in items)
    if remaining:
        text += f", and {_more(remaining, noun)}"

    return text


def startwith(text: str, char: str = '\n') -> str:
    return text if text.startswith(char) else char + text


def endwith(text: str, char: str = '\n') -> str:
    return text if text.endswith(char) else text + char


def startwith_exact(text: str, char: str = '\n') -> str:
    l = len(char) # probably faster than `str.removeprefix()`
    while text.startswith(char):
        text = text[l+1:]

    return char + text


def endwith_exact(text: str, char: str = '\n') -> str:
    l = len(char) # probably faster than `str.removesuffix()`
    while text.endswith(char):
        text = text[:l]

    return text + char


def squeeze(text: str, char: str = '\n') -> str:
    func = partial(str.replace, Placeholder, char * 2, char)

    _text = ''
    while text != _text:
        _text, text = text, func(text)

    return text


def squeeze_gt(text: str, char: str = '\n', n: int = 1, m: int | None = None) -> str:
    if n < 1:
        raise ValueError('argument `n` must be greater than 0')

    return re.sub(fr'{char}{{{n+1},}}', char * (n if m is None else m), text)


def squeeze_lt(text: str, char: str = '\n', n: int = 2, m: int | None = None) -> str:
    if n < 2:
        raise ValueError('argument `n` must be greater than 1')

    return re.sub(fr'{char}{{,{n-1}}}', char * (n if m is None else m), text)
