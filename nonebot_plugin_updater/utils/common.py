from pathlib import Path
from typing import Any

import httpx
import importlib_metadata
import toml

from ..config import plugin_config
from .models import NBResponse, PluginInfo


async def get_plugin_latest_version(package_name: str) -> str:
    async with httpx.AsyncClient() as ctx:
        response: httpx.Response = await ctx.get(
            f'{plugin_config.github_proxy}/https://raw.githubusercontent.com/nonebot/registry/results/plugins.json'
        )
        if response.status_code == 200:
            data: list[NBResponse] = [NBResponse(**item) for item in response.json()]
            for d in data:
                if d.project_link == package_name:
                    return d.version
        return 'None'


def find_project_root() -> Path:
    for parent in Path(__file__).parents:
        if (parent / 'pyproject.toml').exists():
            return parent
    raise FileNotFoundError("Could not find 'pyproject.toml' in any parent directory")


def get_plugin_module_list() -> list[str]:
    project_root = find_project_root()
    pyproject_path: Path = project_root / 'pyproject.toml'
    config: dict[str, Any] = toml.load(pyproject_path)
    plugin_list: list[str] = config['tool']['nonebot']['plugins']
    return plugin_list


async def get_plugin_info_list(plugin_list: list[str]) -> list[NBResponse]:
    plugin_info_list: list[NBResponse] = []
    async with httpx.AsyncClient() as ctx:
        response: httpx.Response = await ctx.get(
            f'{plugin_config.github_proxy}/https://raw.githubusercontent.com/nonebot/registry/results/plugins.json'
        )
        if response.status_code == 200:
            data: list[NBResponse] = [NBResponse(**item) for item in response.json()]
            for d in data:
                if d.project_link in plugin_list:
                    plugin_info_list.append(d)
    return plugin_info_list


async def get_plugin_update_list() -> list[PluginInfo]:
    plugin_module_list = get_plugin_module_list()
    plugin_update_list: list[PluginInfo] = []
    for module in plugin_module_list:
        # 过滤本地插件
        async with httpx.AsyncClient() as ctx:
            response: httpx.Response = await ctx.get(
                f'{plugin_config.github_proxy}/https://raw.githubusercontent.com/nonebot/registry/results/plugins.json'
            )
            if response.status_code == 200:
                data: list[NBResponse] = [
                    NBResponse(**item) for item in response.json()
                ]
                for d in data:
                    if module in d.module_name:
                        plugin = module.replace('_', '-')
                        current_version: str = importlib_metadata.version(module)
                        lastest_version: str = await get_plugin_latest_version(plugin)
                        if current_version != lastest_version:
                            plugin_update_list.append(
                                PluginInfo(
                                    name=plugin,
                                    current_version=current_version,
                                    latest_version=lastest_version,
                                )
                            )
    return plugin_update_list
