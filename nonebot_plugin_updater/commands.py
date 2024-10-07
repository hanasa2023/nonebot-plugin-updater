from os import close
from pathlib import Path
from typing import Any, NoReturn

from arclet.alconna import Arparma
from nonebot import require

from .utils.common import (
    find_project_root,
    get_plugin_module_list,
    get_plugin_update_list,
)
from .utils.models import PluginInfo
from .utils.updater import Updater

require('nonebot_plugin_alconna')
from nonebot_plugin_alconna import (
    Alconna,
    AlconnaMatch,
    AlconnaMatcher,
    Args,
    Match,
    Option,
    on_alconna,
)

_l: Alconna[Any] = Alconna('获取插件列表')
g_plugin_list: type[AlconnaMatcher] = on_alconna(_l, use_cmd_start=True)

_u: Alconna[Any] = Alconna('检查插件更新')
check_update: type[AlconnaMatcher] = on_alconna(_u, use_cmd_start=True)

_udr: Alconna[Any] = Alconna('更新插件', Option('name', Args['plugin_name', str]))
update_plugin: type[AlconnaMatcher] = on_alconna(_udr, use_cmd_start=True)

_c: Alconna[Any] = Alconna('关闭nb')
close_nb: type[AlconnaMatcher] = on_alconna(_c, use_cmd_start=True)

_r: Alconna[Any] = Alconna('重启nb')
restart_nb: type[AlconnaMatcher] = on_alconna(_r, use_cmd_start=True)


@g_plugin_list.handle()
async def _() -> None:
    project_root: Path = find_project_root()
    plugin_module_list: list[str] = get_plugin_module_list(project_root)
    plugin_list: list[str] = []
    for moudle in plugin_module_list:
        plugin_list.append(moudle.replace('_', '-'))
    msg: str = '通过pypi安装的插件有：\n'
    for plugin in plugin_list:
        msg = msg + f'{plugin}\n'
    await g_plugin_list.finish(msg)


@check_update.handle()
async def _() -> None:
    plugin_update_list: list[PluginInfo] = await get_plugin_update_list()
    msg: str = '插件名 现版本 最新版本\n'
    for plugin in plugin_update_list:
        msg = msg + f'{plugin.name} {plugin.current_version} {plugin.latest_version}'
    await check_update.finish(msg)


@update_plugin.handle()
async def _(
    result: Arparma, plugin_name: Match[str] = AlconnaMatch('plugin_name')
) -> None:
    plugin_update_list = await get_plugin_update_list()
    await update_plugin.send('正在更新插件中……')
    if result.find('name'):
        if plugin_name.available and plugin_name.result in [
            plugin.name for plugin in plugin_update_list
        ]:
            updater = Updater(plugin_update_list, plugin_name=plugin_name.result)
            await updater.do_update()
        else:
            await update_plugin.finish('无效的插件名')
    else:
        updater = Updater(plugin_update_list)
        await updater.do_update()


@close_nb.handle()
async def _() -> None:
    await close_nb.send('关闭nb中……')
    await Updater.do_stop()


@restart_nb.handle()
async def _() -> None:
    await restart_nb.send('重启nb中……')
    await Updater([]).do_restart()