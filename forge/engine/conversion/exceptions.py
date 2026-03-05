"""Custom exceptions for conversion errors."""


class MappingError(Exception):
    """Error during template → dataclass conversion."""

    def __init__(self, message: str, yaml_path: str = None, field: str = None):
        self.yaml_path = yaml_path
        self.field = field
        super().__init__(message)


class MissingFieldError(MappingError):
    """Required field missing from template."""

    def __init__(self, yaml_path: str, field: str):
        message = f"Missing required field: {yaml_path}.{field}"
        super().__init__(message, yaml_path, field)
