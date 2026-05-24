"""Domain exceptions mapped to HTTP responses by handlers in app/main.py."""

from __future__ import annotations


class DomainError(Exception):
    status_code: int = 400
    detail: str = "domain error"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class EmailTakenError(DomainError):
    status_code = 409
    detail = "email already registered"


class UsernameTakenError(DomainError):
    status_code = 409
    detail = "username already taken"


class InvalidCredentialsError(DomainError):
    status_code = 401
    detail = "invalid credentials"


class InvalidRefreshError(DomainError):
    status_code = 401
    detail = "invalid refresh token"


class MissingRefreshError(DomainError):
    status_code = 401
    detail = "missing refresh token"


class TemplateNotFoundError(DomainError):
    status_code = 404
    detail = "activity not found"


class TemplateDisabledError(DomainError):
    status_code = 409
    detail = "activity disabled"
