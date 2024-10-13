from __future__ import annotations

from pydantic import BaseModel, Field


class Tag(BaseModel):
    label: str
    color: str


class NBPluginMetadata(BaseModel):
    module_name: str
    project_link: str
    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: bool
    type: str | None
    supported_adapters: list[str] | None
    valid: bool
    version: str
    time: str
    skip_test: bool


class PluginInfo(BaseModel):
    name: str
    current_version: str
    latest_version: str
