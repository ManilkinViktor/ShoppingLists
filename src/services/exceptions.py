class DomainException(Exception):
    error_code: str
    public_message: str

class EmailAlreadyExists(DomainException):
    error_code: str = 'EMAIL_ALREADY_EXISTS'
    public_message: str = 'A user with this email is already registered'

class ConflictUUID(DomainException):
    error_code: str = 'CONFLICT_UUID'
    public_message: str = 'UUID already exists'


class InvalidCredentials(DomainException):
    error_code: str = 'INVALID_CREDENTIALS'
    public_message: str = 'Incorrect email or password'
