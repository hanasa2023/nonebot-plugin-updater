from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config
from .updater import updater

__plugin_meta__ = PluginMetadata(
    name='nonebot-plugin-updater',
    description='',
    usage='',
    config=Config,
)

config = get_plugin_config(Config)
