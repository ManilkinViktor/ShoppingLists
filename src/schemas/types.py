from typing import TypeVar

from pydantic import BaseModel

from database.base import Base

ModelOrm = TypeVar('ModelOrm', bound=Base)
AddDTO = TypeVar('AddDTO', bound=BaseModel)
DTO = TypeVar('DTO', bound=BaseModel)