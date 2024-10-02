from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    # 获取插件信息的url
    pypi_info_url: str = 'https://mirrors.ustc.edu.cn/pypi'


plugin_config = get_plugin_config(Config)
