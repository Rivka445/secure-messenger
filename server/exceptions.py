from typing import Optional

class AppError(Exception):
    """Base class for application-level exceptions.

    Subclass this for typed business errors which can be mapped to HTTP responses.
    """
    status_code: int = 500

    def __init__(self, detail: Optional[str] = None) -> None:
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


def map_app_error_to_http(exc: AppError) -> tuple[int, str]:
    """Map an AppError to an (HTTP status code, detail) tuple.

    This helper is used by the FastAPI exception handler to build a JSON
    response payload for the client.
    """
    return getattr(exc, "status_code", 500), getattr(exc, "detail", str(exc))
