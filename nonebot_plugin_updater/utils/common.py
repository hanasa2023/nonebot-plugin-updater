from pathlib import Path
from typing import Any

import httpx
import importlib_metadata
import toml

from ..config import plugin_config
from .models import PluginInfo, PypiResponse


async def get_plugin_latest_version(package_name: str) -> str:
    async with httpx.AsyncClient() as ctx:
        response: httpx.Response = await ctx.get(
            f'{plugin_config.pypi_info_url}/{package_name}/json'
        )
        if response.status_code == 200:
            data: PypiResponse = PypiResponse(**response.json())
            return data.info.version
        else:
            return 'None'


def find_project_root() -> Path:
    for parent in Path(__file__).parents:
        if (parent / 'pyproject.toml').exists():
            return parent
    raise FileNotFoundError("Could not find 'pyproject.toml' in any parent directory")


def get_plugin_module_list(project_root: Path) -> list[str]:
    pyproject_path: Path = project_root / 'pyproject.toml'
    config: dict[str, Any] = toml.load(pyproject_path)
    plugin_list: list[str] = config['tool']['nonebot']['plugins']
    return plugin_list


async def get_plugin_update_list() -> list[PluginInfo]:
    project_root = find_project_root()
    plugin_module_list = get_plugin_module_list(project_root)
    plugin_update_list: list[PluginInfo] = []
    for module in plugin_module_list:
        plugin = module.replace('_', '-')
        current_version = importlib_metadata.version(module)
        lastest_version = await get_plugin_latest_version(plugin)
        if current_version != lastest_version:
            plugin_update_list.append(
                PluginInfo(
                    name=plugin,
                    current_version=current_version,
                    latest_version=lastest_version,
                )
            )
    return plugin_update_list
