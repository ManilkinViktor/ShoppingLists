from typing import Type

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

class EntityNotFound(DomainException):
    error_code: str = 'ENTITY_NOT_FOUND'

    def __init__(self, t: Type):
        super()
        self.public_message = f'{t.__class__.__name__} not found'


