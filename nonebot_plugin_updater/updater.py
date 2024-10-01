from nonebot import require

from .utils.comman import get_latest_package_version

require('nonebot_plugin_alconna')
from nonebot_plugin_alconna import Alconna, on_alconna

u = Alconna('检查插件更新')
updater = on_alconna(u, use_cmd_start=True)


@updater.handle()
async def _():
    version: str = await get_latest_package_version('nonebot-plugin-ba-tools')
    await updater.finish(version)
