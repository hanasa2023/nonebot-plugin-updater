from __future__ import annotations

from pathlib import Path
from typing import Any

from nonebot import require
from nonebot.permission import SUPERUSER

from .config import plugin_config
from .utils.common import (
    get_plugin_info_list,
    get_plugin_module_list,
    get_plugin_update_list,
    get_store_plugins,
    plugin_info_text_builder,
    plugin_update_text_builder,
)
from .utils.models import NBPluginMetadata, PluginInfo
from .utils.updater import Updater

require('nonebot_plugin_alconna')
from nonebot_plugin_alconna import (
    Alconna,
    AlconnaMatch,
    AlconnaMatcher,
    Args,
    Image,
    Match,
    Text,
    UniMessage,
    on_alconna,
)

_l: Alconna[Any] = Alconna('获取插件列表')
g_plugin_list: type[AlconnaMatcher] = on_alconna(_l, use_cmd_start=True)

_u: Alconna[Any] = Alconna('检查插件更新')
check_update: type[AlconnaMatcher] = on_alconna(_u, use_cmd_start=True)

_udr: Alconna[Any] = Alconna('更新插件', Args['plugin_name', str])
update_plugin: type[AlconnaMatcher] = on_alconna(
    _udr, use_cmd_start=True, permission=SUPERUSER
)

_idr: Alconna[Any] = Alconna('安装插件', Args['plugin_name', str])
install_plugin: type[AlconnaMatcher] = on_alconna(
    _idr, use_cmd_start=True, permission=SUPERUSER
)

_uidr: Alconna[Any] = Alconna('卸载插件', Args['plugin_name', str])
uninstall_plugin: type[AlconnaMatcher] = on_alconna(
    _uidr, use_cmd_start=True, permission=SUPERUSER
)

_c: Alconna[Any] = Alconna('关闭nb')
close_nb: type[AlconnaMatcher] = on_alconna(
    _c, use_cmd_start=True, permission=SUPERUSER
)

_r: Alconna[Any] = Alconna('重启nb')
restart_nb: type[AlconnaMatcher] = on_alconna(
    _r, use_cmd_start=True, permission=SUPERUSER
)


@g_plugin_list.handle()
async def _() -> None:
    plugin_module_list: list[str] = get_plugin_module_list()
    plugin_list: list[str] = []
    for moudle in plugin_module_list:
        plugin_list.append(moudle.replace('_', '-'))
    plugin_info_list: list[NBPluginMetadata] = await get_plugin_info_list(plugin_list)
    if plugin_config.info_send_mode == 'text':
        msg: UniMessage[Text] | UniMessage[Image] = UniMessage().text(
            plugin_info_text_builder(plugin_info_list)
        )
    else:
        from .utils.addition_for_htmlrender import template_element_to_pic

        template_path: Path = Path(__file__).parent / 'templates'
        img: bytes = await template_element_to_pic(
            str(template_path),
            template_name='plugin_info.jinja2',
            templates={'plugins': plugin_info_list},
            element='#container',
            wait=2,
        )
        msg = UniMessage().image(raw=img)
    await g_plugin_list.finish(msg)


@check_update.handle()
async def _() -> None:
    plugin_update_list: list[PluginInfo] = await get_plugin_update_list()
    if plugin_config.info_send_mode == 'text':
        msg: UniMessage[Text] | UniMessage[Image] = UniMessage().text(
            plugin_update_text_builder(plugin_update_list)
        )
    else:
        from .utils.addition_for_htmlrender import template_element_to_pic

        template_path: Path = Path(__file__).parent / 'templates'
        img: bytes = await template_element_to_pic(
            str(template_path),
            template_name='check_plugin_update.jinja2',
            templates={'plugins': plugin_update_list},
            element='#container',
            wait=2,
        )
        msg = UniMessage().image(raw=img)
    await check_update.finish(msg)


@update_plugin.handle()
async def _(plugin_name: Match[str] = AlconnaMatch('plugin_name')) -> None:
    if plugin_name.available:
        plugin_update_list: list[PluginInfo] = await get_plugin_update_list()
        if plugin_name.result == 'all':
            if not plugin_update_list:
                await update_plugin.finish('所有插件已是最新')
            else:
                await update_plugin.send('正在更新插件中……')
                updater: Updater = Updater(plugin_update_list)
                await updater.do_update()
        elif plugin_name.result in [plugin.name for plugin in plugin_update_list]:
            await update_plugin.send('正在更新插件中……')
            updater = Updater(plugin_update_list, plugin_name=plugin_name.result)
            await updater.do_update()
        else:
            await update_plugin.finish('无效的插件名/插件已是最新')


@install_plugin.handle()
async def _(plugin_name: Match[str] = AlconnaMatch('plugin_name')) -> None:
    if plugin_name.available:
        store_plugins: list[NBPluginMetadata] = await get_store_plugins()
        if plugin_name.result in [plugin.project_link for plugin in store_plugins]:
            await install_plugin.send('正在安装插件中……')
            updater: Updater = Updater([], plugin_name.result)
            await updater.do_install()
        else:
            await install_plugin.finish('插件不存在')


@uninstall_plugin.handle()
async def _(plugin_name: Match[str] = AlconnaMatch('plugin_name')) -> None:
    if plugin_name.available:
        store_plugins: list[NBPluginMetadata] = await get_store_plugins()
        if plugin_name.result in [plugin.project_link for plugin in store_plugins]:
            await uninstall_plugin.send('正在卸载插件中……')
            updater: Updater = Updater([], plugin_name.result)
            await updater.do_uninstall()
        else:
            await uninstall_plugin.finish('插件不存在')


@close_nb.handle()
async def _() -> None:
    await close_nb.send('关闭nb中……')
    await Updater.do_stop()


@restart_nb.handle()
async def _() -> None:
    await restart_nb.send('重启nb中……')
    await Updater([]).do_restart()
