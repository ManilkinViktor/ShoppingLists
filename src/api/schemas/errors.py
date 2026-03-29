from pydantic import BaseModel


class ErrorDetailDTO(BaseModel):
    code: str
    message: str


class ErrorResponseDTO(BaseModel):
    detail: ErrorDetailDTO


class ErrorTextResponseDTO(BaseModel):
    detail: str
