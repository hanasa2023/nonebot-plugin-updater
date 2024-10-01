from pydantic import BaseModel


class Info(BaseModel):
    author: str
    author_email: str
    summary: str
    version: str


class PypiResponse(BaseModel):
    info: Info
