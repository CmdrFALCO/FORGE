"""FORGE materials package.

Exports repository and academic parameter-set APIs.
"""

from .academic import *  # noqa: F403
from .academic import __all__ as _academic_all
from .repositories import *  # noqa: F403
from .repositories import __all__ as _repositories_all

__all__ = _repositories_all + _academic_all
