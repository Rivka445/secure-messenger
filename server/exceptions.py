from typing import Optional

class AppError(Exception):
    """Base class for application-level exceptions."""
    status_code: int = 500

    def __init__(self, detail: Optional[str] = None):
        super().__init__(detail or self.__class__.__name__)
        self.detail = detail or self.__class__.__name__


class NotFoundError(AppError):
    status_code = 404


class ForbiddenError(AppError):
    status_code = 403


class ConflictError(AppError):
    status_code = 409


class BadRequestError(AppError):
    status_code = 400


def map_app_error_to_http(exc: AppError):
    """Return a tuple (status_code, detail) suitable for raising HTTPException."""
    return getattr(exc, "status_code", 500), getattr(exc, "detail", str(exc))
