from typing import Literal

from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    # GitHub代理
    github_proxy: str = ''
    # 发送信息的模式
    info_send_mode: Literal['text', 'pic'] = 'pic'


plugin_config = get_plugin_config(Config)
