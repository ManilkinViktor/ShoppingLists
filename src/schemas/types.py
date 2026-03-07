from typing import TypeVar, Generic
from uuid import UUID
from pydantic import BaseModel

CreateDTO = TypeVar('CreateDTO', bound=BaseModel)
PatchDTO = TypeVar('PatchDTO', bound=BaseModel)
DTO = TypeVar('DTO', bound=BaseModel)


class OperationBase(BaseModel):
    op: str

class CreateOperation(OperationBase, Generic[CreateDTO]):
    data: CreateDTO

class PatchOperation(OperationBase, Generic[PatchDTO]):
    data: PatchDTO

class DeleteOperation(OperationBase):
    id: UUID