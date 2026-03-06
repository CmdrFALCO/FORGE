"""YAML template conversion to FORGE engine input dataclasses.

This module provides conversion functions to transform validated YAML templates
into FORGE engine input objects ready for calculation.

Supports all cell types:
- Prismatic: from_template_format() -> PrismaticCellInput
- Pouch: from_pouch_template_format() -> PouchCellInput
- Cylindrical: from_cylindrical_template_format() -> CylindricalCellInput
"""

from .exceptions import MappingError, MissingFieldError
from .template_to_input import (
    from_cylindrical_template_format,
    from_cylindrical_yaml_file,
    from_pouch_template_format,
    from_pouch_yaml_file,
    from_template_format,
    from_yaml_file,
)

__all__ = [
    # Prismatic conversion
    "from_template_format",
    "from_yaml_file",
    # Pouch conversion
    "from_pouch_template_format",
    "from_pouch_yaml_file",
    # Cylindrical conversion
    "from_cylindrical_template_format",
    "from_cylindrical_yaml_file",
    # Exceptions
    "MappingError",
    "MissingFieldError",
]
