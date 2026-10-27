"""Core domain exceptions for DataSentinel."""


class DataSentinelError(Exception):
    """Base exception for all DataSentinel operations."""

    pass


class IngestionError(DataSentinelError):
    """Raised when an uploaded file cannot be parsed or read."""

    pass


class FileSecurityError(DataSentinelError):
    """Raised when an uploaded file violates security constraints."""

    pass


class ValidationError(DataSentinelError):
    """Raised when validation rules or schema definitions fail."""

    pass


class AnalysisError(DataSentinelError):
    """Raised when a quality analysis computation fails."""

    pass
