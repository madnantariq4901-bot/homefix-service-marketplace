# app/core/exceptions.py
class AppError(Exception):
    """Base class for domain-level errors."""


class NotFoundError(AppError):
    pass


class PermissionDeniedError(AppError):
    pass


class ConflictError(AppError):
    pass