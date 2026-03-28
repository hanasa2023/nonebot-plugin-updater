import json
import os
from nonebot import get_driver
from nonebot.adapters import Bot
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

driver = get_driver()

from .commands import (
    check_update,
    g_plugin_list,
    install_plugin,
    uninstall_plugin,
    update_plugin,
)
from .config import Config

__version__ = '0.2.5'
__plugin_meta__ = PluginMetadata(
    name='nb插件更新器',
    description='一款全新的检测已安装插件更新情况的插件',
    type='application',
    homepage='https://github.com/hanasa2023/nonebot-plugin-updater#readme',
    usage="""
|      指令      | 权限 | 需要@ |                                       说明                                       |                  示例                  |
| :------------: | :--: | :---: | :------------------------------------------------------------------------------: | :------------------------------------: |
| `获取插件列表` |  无  |  无   |                               获取已安装的插件列表                               |            `/获取插件列表`             |
| `检查插件更新` |  无  |  无   |                                检查可用的插件更新                                |            `/检查插件更新`             |
|   `更新插件`   |  SUPERUSERS  |  无   | 更新已安装的插件，若需只更新单个插件，则指令为`更新插件 name <需要更新的插件名>` | `/更新插件 name nonebot-pluign-status` |
|    `关闭nb`    |  SUPERUSERS  |  无   |                                  远程关闭 nb nb                                  |               `/关闭nb`                |
|    `重启nb`    |  SUPERUSERS  |  无   |                                  远程重启 nb nb                                  |               `/重启nb`                |""",
    config=Config,
    supported_adapters=inherit_supported_adapters('nonebot_plugin_alconna'),
    extra={
        'version': __version__,
        'authors': ['hanasaki <hanasakayui2022@gmail.com>', 'MoonShadow1976 <>'],
    },
)

@driver.on_bot_connect
async def _(bot: Bot):
    status_file = ".restart_info.json"
    if os.path.exists(status_file):
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                info = json.load(f)
            # 读完立刻删掉，防止下次被重复触发
            os.remove(status_file)

            if bot.self_id == info.get("bot_id"):
                target_id = info.get("target_id")
                is_group = info.get("is_group")
                msg = info.get("message", "✨ 重启成功！")

                # 适配你主力使用的 OneBot V11 协议
                if bot.adapter.get_name() == "OneBot V11":
                    if is_group:
                        await bot.send_group_msg(group_id=int(target_id), message=msg)
                    else:
                        await bot.send_private_msg(user_id=int(target_id), message=msg)
        except Exception:
            # 万一出错，也要确保残留文件被清理
            if os.path.exists(status_file):
                os.remove(status_file)
