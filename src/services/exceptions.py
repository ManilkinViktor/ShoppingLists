from typing import Any, Type


class DomainException(Exception):
    error_code: str
    public_message: str


class EmailAlreadyExists(DomainException):
    error_code: str = 'EMAIL_ALREADY_EXISTS'
    public_message: str = 'A user with this email is already registered'


class InvalidCredentials(DomainException):
    error_code: str = 'INVALID_CREDENTIALS'
    public_message: str = 'Incorrect email or password'


class ConflictUUID(DomainException):
    error_code: str = 'CONFLICT_UUID'
    public_message: str = 'UUID already exists'


class WorkspaceVersionMismatch(DomainException):
    error_code: str = 'WORKSPACE_VERSION_MISMATCH'
    public_message: str = 'Workspace version mismatch'


class EntityNotFound(DomainException):
    error_code: str = 'ENTITY_NOT_FOUND'

    def __init__(self, t: Type[Any]) -> None:
        super().__init__()
        type_name = t.__name__ if hasattr(t, '__name__') else t.__class__.__name__
        self.public_message = f'{type_name} not found'


class DuplicateWorkspaceSyncPayload(DomainException):
    error_code: str = 'DUPLICATE_WORKSPACE_SYNC_PAYLOAD'
    public_message: str = 'Sync payload must contain one item per workspace'


class OwnerRoleChangeForbidden(DomainException):
    error_code: str = 'OWNER_ROLE_CHANGE_FORBIDDEN'
    public_message: str = 'Workspace owner role cannot be changed'


class OwnerRemovalForbidden(DomainException):
    error_code: str = 'OWNER_REMOVAL_FORBIDDEN'
    public_message: str = 'Workspace owner cannot be removed'


class InvalidListItemQuantity(DomainException):
    error_code: str = 'INVALID_ITEM_QUANTITY'
    public_message: str = "Item quantity must be positive"
