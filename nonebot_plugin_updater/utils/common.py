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
    from nonebot import get_loaded_plugins
    
    # 直接获取 NoneBot 内存里所有已成功加载的插件
    loaded_plugins = get_loaded_plugins()
    plugin_list: list[str] = []
    
    for plugin in loaded_plugins:
        # 过滤掉 NoneBot 内置的元插件和基础插件 (如 echo)
        if plugin.name.startswith("nonebot") and not plugin.name.startswith("nonebot_plugin"):
            continue
        if plugin.name == "echo":
            continue
            
        # 把内存里真实存在的插件名丢进列表
        plugin_list.append(plugin.name)
        
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
    import httpx
    import asyncio
    import importlib.metadata
    from nonebot import logger

    plugin_info_list: list[NBPluginMetadata] = []

    # 1. 定义直连 PyPI 的异步请求函数
    async def fetch_pypi_version(pkg_name: str) -> tuple[str, str]:
        # 【关键修复】剥离拓展名，且必须把下划线换成横杠以适配 PyPI 标准！
        clean_name = pkg_name.split("[")[0]
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"https://pypi.org/pypi/{clean_name}/json", timeout=5.0)
                if res.status_code == 200:
                    return pkg_name, res.json()["info"]["version"]
        except Exception:
            pass
        return pkg_name, ""

    # 2. 并发向 PyPI 请求所有插件的最新版本
    tasks = [fetch_pypi_version(p) for p in plugin_list]
    pypi_results = await asyncio.gather(*tasks)
    pypi_versions = dict(pypi_results)

    # 3. 组装展示数据
    for plugin_name in plugin_list:
        normalized_name = plugin_name.replace("-", "_")

        # 从本地环境提取信息
        try:
            dist = importlib.metadata.distribution(plugin_name)
            local_version = dist.version
            desc = dist.metadata.get("Summary", "本地插件")
            author = dist.metadata.get("Author", "未知")
            homepage = dist.metadata.get("Home-page", "")
        except importlib.metadata.PackageNotFoundError:
            local_version = "未知"
            desc = "未通过包管理器安装的本地源码插件"
            author = "未知"
            homepage = ""

        latest_version = pypi_versions.get(plugin_name)
        if not latest_version:
            latest_version = local_version

        plugin_info_list.append(
            NBPluginMetadata(
                module_name=normalized_name,
                project_link=plugin_name.replace("_", "-"), # 强行规范化为横杠标准名
                author=author,
                tags=[],
                is_official=False,
                type="application",
                supported_adapters=[],
                name=plugin_name,
                desc=desc,
                valid=True,
                version=latest_version,
                time="",
                homepage=homepage,
                skip_test=False
            )
        )

    return plugin_info_list


async def get_plugin_update_list() -> list[PluginInfo]:
    """获取可用的插件更新列表"""
    import importlib.metadata
    
    plugin_module_list: list[str] = get_plugin_module_list()
    plugin_update_list: list[PluginInfo] = []
    
    # 【神级改造】直接复用我们写好的、无延迟且支持并发直连 PyPI 的函数！彻底抛弃原作者的嵌套循环！
    plugin_info_list = await get_plugin_info_list(plugin_module_list)
    
    for plugin in plugin_info_list:
        try:
            # 获取本地环境安装的版本
            current_version: str = importlib.metadata.version(plugin.project_link)
        except importlib.metadata.PackageNotFoundError:
            continue  # 本地没走 pip 安装的（如直接丢在src/plugins下的），跳过更新检测
            
        latest_version: str = plugin.version
        
        # 如果获取不到 PyPI 版本，或者两者版本一样，则跳过
        if latest_version == "未知" or current_version == latest_version:
            continue
            
        if _is_newer_version(latest_version, current_version):
            plugin_update_list.append(
                PluginInfo(
                    name=plugin.project_link,
                    current_version=current_version,
                    latest_version=latest_version,
                )
            )
            
    return plugin_update_list
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
