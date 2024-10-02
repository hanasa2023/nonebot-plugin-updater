from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .commands import check_update, g_plugin_list, update_plugin
from .config import Config

__version__ = '0.1.0'
__plugin_meta__ = PluginMetadata(
    name='nonebot-plugin-updater',
    description='一款全新的检测已安装插件更新情况的插件',
    type='application',
    homepage='https://github.com/hanasa2023/nonebot-plugin-updater#readme',
    usage='',
    config=Config,
    extra={
        'version': __version__,
        'authors': [
            'hanasaki <hanasakayui2022@gmail.com>',
        ],
    },
)

config = get_plugin_config(Config)
