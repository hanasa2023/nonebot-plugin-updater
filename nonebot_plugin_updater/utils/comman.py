import httpx

from .models import PypiResponse


async def get_latest_package_version(package_name: str) -> str:
    async with httpx.AsyncClient() as ctx:
        response: httpx.Response = await ctx.get(
            f'https://mirrors.ustc.edu.cn/pypi/{package_name}/json'
        )
        if response.status_code == 200:
            data: PypiResponse = PypiResponse(**response.json())
            return data.info.version
        else:
            return 'None'
