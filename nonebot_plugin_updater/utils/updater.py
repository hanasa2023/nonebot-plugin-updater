from __future__ import annotations

import inspect
import socket
from pathlib import Path
from shutil import which
from subprocess import PIPE
from typing import TYPE_CHECKING

from nonebot import get_driver, logger

from nonebot_plugin_updater.utils.models import PluginInfo

if TYPE_CHECKING:
    from uvicorn.server import Server

driver = get_driver()


class Updater:
    def __init__(
        self, plugin_update_list: list[PluginInfo], plugin_name: str | None = None
    ) -> None:
        self.plugin_update_list = plugin_update_list
        self.plugin_name = plugin_name

    def _restart(self) -> None:
        from os import execlp
        from sys import argv

        nb = which('nb')
        py = which('python')

        # 尝试使用 nb 命令
        if nb:
            try:
                execlp(nb, nb, 'run')
            except Exception as e:
                logger.warning(f'使用 nb 命令重启失败: {e}')

        # 尝试使用当前启动脚本
        if py and argv:
            if len(argv) > 0 and Path(argv[0]).exists():
                try:
                    execlp(py, py, *argv)
                except Exception as e:
                    logger.warning(f'使用当前脚本重启失败: {e}')

        # 尝试常见的启动文件
        common_start_files = ['bot.py', 'main.py', 'app.py', 'run.py']
        if py:
            for start_file in common_start_files:
                if Path(start_file).exists():
                    try:
                        execlp(py, py, start_file)
                    except Exception as e:
                        logger.warning(f'使用 {start_file} 重启失败: {e}')
                        continue

        # 尝试使用 nbr 启动
        nbr = which('nbr')
        if nbr:
            try:
                execlp(nbr, nbr, 'run')
            except Exception as e:
                logger.warning(f'使用 nbr 重启失败: {e}')

        logger.error('所有重启尝试均失败，请手动重启')
        raise Exception('无法重启')

    @staticmethod
    def _uvicorn_getserver() -> 'Server':
        from uvicorn.server import Server

        fis = inspect.getouterframes(inspect.currentframe())
        svrs = (fi.frame.f_locals.get('server', None) for fi in fis[::-1])
        server, *_ = (s for s in svrs if isinstance(s, Server))
        return server

    @staticmethod
    def _uvicorn_getsocket() -> list[socket.socket]:
        fis = inspect.getouterframes(inspect.currentframe())
        skvars = (fi.frame.f_locals.get('sockets', None) for fi in fis[::-1])
        try:
            valid_sockets = [
                s
                for s in skvars
                if isinstance(s, list) and all(isinstance(x, socket.socket) for x in s)
            ]

            if valid_sockets:
                return valid_sockets[0]
            return []
        except Exception as e:
            logger.exception(e)
            return []

    @staticmethod
    def _none_stop() -> None:
        if TYPE_CHECKING:
            from nonebot.drivers.none import Driver as NoneDriver

            assert isinstance(driver, NoneDriver)
        driver.exit()

    @staticmethod
    def _uvicorn_stop() -> None:
        server = Updater._uvicorn_getserver()
        server.should_exit = True

    @staticmethod
    async def do_stop() -> None:
        if 'fastapi' in driver.type or 'quart' in driver.type:
            Updater._uvicorn_stop()
        if 'none' in driver.type:
            Updater._none_stop()

    async def shutdown_with_timeout(self, server: Server) -> None:
        import asyncio
        import os
        import signal
        import atexit

        try:
            await asyncio.wait_for(
                server.shutdown(self._uvicorn_getsocket()), timeout=5.0
            )
            logger.info('正常关闭完成，执行重启')
        except asyncio.TimeoutError:
            logger.warning('关闭超时，执行强制重启')
            # 注册重启回调后再强制终止
            atexit.register(self._restart)
            os.kill(os.getpid(), signal.SIGTERM)

    async def do_update(self) -> None:
        import atexit
        import subprocess

        if 'none' in driver.type:
            atexit.register(self._restart)
            self._none_stop()
        if 'fastapi' in driver.type or 'quart' in driver.type:
            try:
                server = self._uvicorn_getserver()
                server.should_exit = True
                await self.shutdown_with_timeout(server)
                nb = which('nb')
                if nb:
                    if self.plugin_name is not None:
                        subprocess.run(
                            [nb, 'plugin', 'update', self.plugin_name], check=True
                        )
                    else:
                        for plugin in self.plugin_update_list:
                            subprocess.run(
                                [nb, 'plugin', 'update', plugin.name], check=True
                            )
                self._restart()
            except Exception as e:
                logger.exception(e)
                await self.do_stop()

    async def do_install(self) -> None:
        import atexit
        import subprocess

        if 'none' in driver.type:
            atexit.register(self._restart)
            self._none_stop()
        if 'fastapi' in driver.type or 'quart' in driver.type:
            try:
                server = self._uvicorn_getserver()
                server.should_exit = True
                await self.shutdown_with_timeout(server)
                nb = which('nb')
                if nb:
                    if self.plugin_name is not None:
                        subprocess.run(
                            [nb, 'plugin', 'install', self.plugin_name], check=True
                        )
                self._restart()
            except Exception as e:
                logger.exception(e)
                await self.do_stop()

    async def do_uninstall(self) -> None:
        import atexit
        import subprocess

        if 'none' in driver.type:
            atexit.register(self._restart)
            self._none_stop()
        if 'fastapi' in driver.type or 'quart' in driver.type:
            try:
                server = self._uvicorn_getserver()
                server.should_exit = True
                await self.shutdown_with_timeout(server)
                nb = which('nb')
                if nb:
                    if self.plugin_name is not None:
                        subprocess.run(
                            [nb, 'plugin', 'uninstall', self.plugin_name, '-y'],
                        )
                self._restart()
            except Exception as e:
                logger.exception(e)
                await self.do_stop()

    async def do_restart(self) -> None:
        import atexit

        if 'none' in driver.type:
            atexit.register(self._restart)
            self._none_stop()
        if 'fastapi' in driver.type or 'quart' in driver.type:
            try:
                server = self._uvicorn_getserver()
                server.should_exit = True
                # 注册重启回调，确保即使超时也能重启
                atexit.register(self._restart)
                await self.shutdown_with_timeout(server)
                # 如果正常关闭，直接执行重启
                self._restart()
            except Exception as e:
                logger.error(f'重启过程中出现错误: {e}')
                # 尝试基本的停止操作
                await self.do_stop()
