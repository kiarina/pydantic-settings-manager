class UserConfigError(ValueError):
    """Raised when a user configuration fails to validate.

    The message is a commented-YAML rendering of the offending fields; the
    original ``pydantic.ValidationError`` is preserved as ``__cause__``.
    """
