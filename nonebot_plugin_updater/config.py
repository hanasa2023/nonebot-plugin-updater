from typing import Literal

from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    # 获取插件信息的url
    pypi_info_url: str = 'https://mirrors.ustc.edu.cn/pypi'
    # 发送信息的模式
    info_send_mode: Literal['text', 'pic'] = 'pic'


plugin_config = get_plugin_config(Config)
