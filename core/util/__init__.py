from collections.abc import Callable


def all_predicates[**P](*predicates: Callable[P, bool]) -> Callable[P, bool]:
    """
    Returns a function that returns true if all functions return a truthy value when run with the same arguements.

    Args:
        predicates: Any number of functions.

    Returns:
        A function that lazily calls all previously provided functions with the same arguments and returns true if they all return true.
    """

    def inner(*args: P.args, **kwargs: P.kwargs) -> bool:
        return all(predicate(*args, **kwargs) for predicate in predicates)

    return inner
