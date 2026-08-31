from uuid import UUID


class DomainError(Exception):
    """Base for errors translated to a specific HTTP response by main.py's handlers."""


class NotFoundError(DomainError):
    def __init__(self, resource_type: str, resource_id: UUID | str) -> None:
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} {resource_id} not found")


class ConflictError(DomainError):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ValidationConflictError(DomainError):
    """A business-rule violation (e.g. an illegal status transition), as opposed
    to a malformed request — that's still Pydantic's job."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidCursorError(DomainError):
    def __init__(self, cursor: str) -> None:
        self.cursor = cursor
        super().__init__(f"Invalid pagination cursor: {cursor!r}")


class AuthenticationError(DomainError):
    """Missing, invalid, expired, or revoked credentials — always a 401."""

    def __init__(self, message: str = "Not authenticated") -> None:
        self.message = message
        super().__init__(message)


class AuthorizationError(DomainError):
    """Authenticated, but not allowed to do this — always a 403."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        self.message = message
        super().__init__(message)
