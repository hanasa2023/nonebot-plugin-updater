from nonebot.plugin import PluginMetadata, inherit_supported_adapters

from .commands import check_update, g_plugin_list, update_plugin
from .config import Config

__version__ = '0.1.2'
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
|   `更新插件`   |  无  |  无   | 更新已安装的插件，若需只更新单个插件，则指令为`更新插件 name <需要更新的插件名>` | `/更新插件 name nonebot-pluign-status` |
|    `关闭nb`    |  无  |  无   |                                  远程关闭 nb nb                                  |               `/关闭nb`                |
|    `重启nb`    |  无  |  无   |                                  远程重启 nb nb                                  |               `/重启nb`                |""",
    config=Config,
    supported_adapters=inherit_supported_adapters('nonebot_plugin_alconna'),
    extra={
        'version': __version__,
        'authors': [
            'hanasaki <hanasakayui2022@gmail.com>',
        ],
    },
)
