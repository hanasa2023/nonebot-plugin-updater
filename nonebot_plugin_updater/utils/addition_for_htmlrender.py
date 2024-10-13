from __future__ import annotations

from typing import Any, Literal

import jinja2
from nonebot import logger, require

require('nonebot_plugin_htmlrender')
from nonebot_plugin_htmlrender import get_new_page  # noqa: E402, F401


async def template_element_to_pic(
    template_path: str,
    template_name: str,
    templates: dict[Any, Any],
    element: str,
    wait: float = 0,
    type: Literal['jpeg', 'png'] = 'png',  # noqa: A002
    quality: int | None = None,
    device_scale_factor: float = 2,
    filters: dict[str, Any] | None = None,
    omit_background: bool | None = None,
    **kwargs,
) -> bytes:
    """使用jinja2模板引擎通过html生成图片

    Args:
        template_path (str): 模板路径
        template_name (str): 模板名
        templates (dict[Any, Any]): 模板内参数 如: {"name": "abc"}
        element (str): CSS选择器，要截取的元素
        wait (float, optional): 网页载入等待时间. Defaults to 0.
        type (Literal["jpeg", "png"]): 图片类型, 默认 png
        quality (int, optional): 图片质量 0-100 当为`png`时无效
        device_scale_factor (float, optional): 缩放比例,类型为float,值越大越清晰(真正想让图片清晰更优先请调整此选项)
        filters (dict[str, Any] | None, optional): 自定义过滤器
        omit_background (bool | None, optional): 截图背景是否透明
        **kwargs: 传入 page 的参数

    Returns:
        bytes: 图片 可直接发送
    """

    template_env: jinja2.Environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path), enable_async=True
    )

    if filters:
        for filter_name, filter_func in filters.items():
            template_env.filters[filter_name] = filter_func
            logger.debug(f'加载自定义过滤器 {filter_name}')

    template: jinja2.Template = template_env.get_template(template_name)
    html: str = await template.render_async(**templates)
    async with get_new_page(device_scale_factor, **kwargs) as page:
        page.on('console', lambda msg: logger.debug(f'浏览器控制台: {msg.text}'))
        await page.goto(f'file://{template_path}')
        await page.set_content(html, wait_until='networkidle')
        await page.wait_for_timeout(wait)
        img: bytes = await page.locator(element).screenshot(
            type=type, quality=quality, omit_background=omit_background
        )
        return img
