from pydantic import BaseModel


class Info(BaseModel):
    author: str
    author_email: str
    summary: str
    version: str


class PypiResponse(BaseModel):
    info: Info


class PluginInfo(BaseModel):
    name: str
    current_version: str
    latest_version: str
