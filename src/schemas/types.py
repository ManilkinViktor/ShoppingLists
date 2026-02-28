from typing import TypeVar, Generic, ClassVar, get_args, Literal
from uuid import UUID
from pydantic import BaseModel

CreateDTO = TypeVar('CreateDTO', bound=BaseModel)
PatchDTO = TypeVar('PatchDTO', bound=BaseModel)
DTO = TypeVar('DTO', bound=BaseModel)

class CreateOperation(BaseModel, Generic[CreateDTO]):
    op: str
    data: CreateDTO

class PatchOperation(BaseModel, Generic[PatchDTO]):
    op: str
    data: PatchDTO

class DeleteOperation(BaseModel):
    op: str
    id: UUID


class OperationBase(BaseModel):
    op: str

    _registry: ClassVar[dict[str, type['OperationBase']]] = {}

    def init_subclass(cls, **kwargs): # type: ignore
        super().init_subclass(**kwargs)

        field = cls.model_fields.get("op")
        if not field:
            return

        args = get_args(field.annotation)
        if args:
            OperationBase._registry[args[0]] = type(cls)