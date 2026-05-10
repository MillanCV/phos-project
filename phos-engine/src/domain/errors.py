class DomainError(Exception):
    """Base class for domain/application errors."""


class CameraUnavailableError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class NotFoundError(DomainError):
    pass
