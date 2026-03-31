from pathlib import Path
from typing import Any

import httpx
import importlib_metadata
import re
from nonebot import logger

try:  # py311+
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # py310-
    import tomli as tomllib  # type: ignore[import-not-found,assignment]

from ..config import plugin_config

from .models import NBPluginMetadata, PluginInfo


async def get_store_plugins() -> list[NBPluginMetadata]:
    """获取nb商店中的所有插件

    Returns:
        list[NBPluginMetadata]: 插件元信息列表
    """
    proxy = plugin_config.updater_proxy or None
    async with httpx.AsyncClient(proxy=proxy) as ctx:
        response: httpx.Response = await ctx.get(
            'https://raw.githubusercontent.com/nonebot/registry/results/plugins.json'
        )
        if response.status_code == 200:
            data: list[NBPluginMetadata] = [
                NBPluginMetadata(**item) for item in response.json()
            ]
            return data
    raise httpx.NetworkError('获取nb商店插件信息失败')


def find_project_root() -> Path:
    """获取项目根目录

    Raises:
        FileNotFoundError: 无法找到项目根目录

    Returns:
        Path: 项目根目录
    """
    parent: Path = Path.cwd().resolve()
    if (parent / 'pyproject.toml').exists():
        return parent
    raise FileNotFoundError("Could not find 'pyproject.toml' in any parent directory")


def get_plugin_module_list() -> list[str]:
    """从项目根目录下的pyproject.toml中获取已安装的插件列表

    Returns:
        list[str]: 已安装的插件列表
    """
    project_root: Path = find_project_root()
    pyproject_path: Path = project_root / 'pyproject.toml'
    with pyproject_path.open('rb') as fp:
        config: dict[str, Any] = tomllib.load(fp)
    plugin_list: list[str] = config['tool']['nonebot']['plugins']
    return plugin_list


def _normalize_version(version_str: str) -> tuple:
    parts: list[str] = re.split(r'[.+-]', version_str)
    return tuple(int(part) if part.isdigit() else part for part in parts)


def _is_newer_version(latest_version: str, current_version: str) -> bool:
    try:
        from packaging.version import Version  # type: ignore[import]

        return Version(latest_version) > Version(current_version)
    except Exception:
        return _normalize_version(latest_version) > _normalize_version(current_version)


async def get_plugin_info_list(plugin_list: list[str]) -> list[NBPluginMetadata]:
    from nonebot import logger
    import importlib.metadata

    plugin_info_list: list[NBPluginMetadata] = []
    
    # 1. 先去拉取官方商店数据备用
    store_plugins: list[NBPluginMetadata] = []
    try:
        store_plugins = await get_store_plugins()
    except Exception:
        logger.warning("无法获取商店信息，将仅显示本地基础信息")

    # 2.命名统一：无论原作者在商店里注册的是横杠还是下划线，统统把对照字典的 key 转成下划线
    store_dict = {p.project_link.replace("-", "_"): p for p in store_plugins}

    # 3. 遍历获取到的插件列表
    for plugin_name in plugin_list:
        # 把待查询的插件名也统一转成下划线，彻底抹平 `-` 和 `_` 的差异
        normalized_name = plugin_name.replace("-", "_")
        
        if normalized_name in store_dict:
            # 如果商店里能匹配上，直接使用官方丰富的展示数据
            plugin_info_list.append(store_dict[normalized_name])
        else:
            # 4.如果商店里真没有，自己拼凑一个本地信息
            try:
                # importlib 底层很聪明，能自动容错横杠和下划线
                dist = importlib.metadata.distribution(plugin_name)
                version = dist.version
                desc = dist.metadata.get("Summary", "这是一个非官方商店的本地插件")
                author = dist.metadata.get("Author", "未知作者")
            except importlib.metadata.PackageNotFoundError:
                # 连 pip 记录都找不到（比如直接塞进 src/plugins 的本地源码插件）
                version = "未知"
                desc = "未通过包管理器安装的本地源码插件"
                author = "未知"

            # 强行打包塞进最终的展示列表中
            plugin_info_list.append(
                NBPluginMetadata(
                    module_name=normalized_name,
                    project_link=plugin_name, # 保持最初始的名字给后面用
                    author=author,
                    tags=[],
                    is_official=False,
                    type="application",
                    supported_adapters=[],
                    name=plugin_name,
                    desc=desc,
                    valid=True,
                    version=version,
                    time="",
                )
            )

    return plugin_info_list


async def get_plugin_update_list() -> list[PluginInfo]:
    """获取可用的插件更新列表

    Returns:
        list[PluginInfo]: 可用的插件更新列表
    """
    plugin_module_list: list[str] = get_plugin_module_list()
    plugin_update_list: list[PluginInfo] = []
    for module in plugin_module_list:
        # 过滤本地插件
        store_plugins: list[NBPluginMetadata] = await get_store_plugins()
        for plugin in store_plugins:
            if module == plugin.module_name:
                current_version: str = importlib_metadata.version(
                    plugin.project_link.replace('-', '_')
                )
                latest_version: str = plugin.version
                if _is_newer_version(latest_version, current_version):
                    plugin_update_list.append(
                        PluginInfo(
                            name=plugin.project_link,
                            current_version=current_version,
                            latest_version=latest_version,
                        )
                    )
    return plugin_update_list


def plugin_info_text_builder(plugin_list: list[NBPluginMetadata]) -> str:
    """生成插件信息文本

    Args:
        plugin_list (list[NBPluginMetadata]): 插件列表

    Returns:
        str:生成的插件信息文本
    """
    if len(plugin_list) == 0:
        return '无已安装的插件\n'
    msg: str = '已安装的插件\n'
    for plugin in plugin_list:
        msg += f'\n📦️ {plugin.project_link}\n插件描述：{plugin.desc}\n插件作者：{plugin.author}'
    return msg


def plugin_update_text_builder(plugin_update_list: list[PluginInfo]) -> str:
    """生成可更新插件文本

    Args:
        plugin_update_list (list[PluginInfo]): 可更新的插件列表

    Returns:
        str: 生成的可更新插件文本
    """
    if len(plugin_update_list) == 0:
        return '无可更新的插件\n'
    msg: str = '可更新的插件\n'
    for plugin in plugin_update_list:
        msg += f'\n📦️ {plugin.name}\n🔖 {plugin.current_version} --> {plugin.latest_version}'
    return msg
