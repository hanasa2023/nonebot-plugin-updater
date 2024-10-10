from __future__ import annotations

from pydantic import BaseModel, Field


class Info(BaseModel):
    author: str | None = Field(None)
    author_email: str | None = Field(None)
    summary: str | None = Field(None)
    version: str | None = Field(None)


class PypiResponse(BaseModel):
    info: Info


class PluginInfo(BaseModel):
    name: str
    current_version: str
    latest_version: str
