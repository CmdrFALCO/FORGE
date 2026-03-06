"""YAML template conversion to FORGE engine input dataclasses.

This module provides conversion functions to transform validated YAML templates
into FORGE engine input objects ready for calculation.

Supports all cell types:
- Prismatic: from_template_format() -> PrismaticCellInput
- Pouch: from_pouch_template_format() -> PouchCellInput
- Cylindrical: from_cylindrical_template_format() -> CylindricalCellInput
"""

from .exceptions import MappingError, MissingFieldError
from .reference_to_input import (
    from_reference_cylindrical,
    from_reference_pouch,
    from_reference_prismatic,
)
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
    # Reference conversion
    "from_reference_pouch",
    "from_reference_prismatic",
    "from_reference_cylindrical",
    # Exceptions
    "MappingError",
    "MissingFieldError",
]
