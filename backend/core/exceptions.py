"""
Domain exceptions — mapped to HTTP responses in routers.
Following RFC 7807 (Problem Details for HTTP APIs).
"""

from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(self, entity: str, entity_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"type": "not_found", "entity": entity, "id": entity_id},
        )


class ValidationError(HTTPException):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"type": "validation_error", "message": message, "field": field},
        )


class ConflictError(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": "conflict", "message": message},
        )


class ExternalServiceError(HTTPException):
    def __init__(self, service: str, message: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"type": "external_service_error", "service": service, "message": message},
        )
