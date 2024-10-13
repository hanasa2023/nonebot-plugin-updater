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

        nb = which('nb')
        py = which('python')
        if nb:
            execlp(nb, nb, 'run')
        elif py:
            from sys import argv

            if argv and Path(argv[0]).exists():
                execlp(py, py, argv[0])
            if Path('bot.py').exists():
                execlp(py, py, 'bot.py')
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
            socks, *_ = (
                s
                for s in skvars
                if isinstance(s, list) and all(isinstance(x, socket.socket) for x in s)
            )
            return socks
        except Exception:
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

    async def do_update(self) -> None:
        import atexit
        import subprocess

        if 'none' in driver.type:
            atexit.register(self._restart)
            self._none_stop()
        if 'fastapi' in driver.type or 'quart' in driver.type:
            server = self._uvicorn_getserver()
            await server.shutdown(self._uvicorn_getsocket())
            try:
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
            server = self._uvicorn_getserver()
            await server.shutdown(self._uvicorn_getsocket())
            try:
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
            server = self._uvicorn_getserver()
            await server.shutdown(self._uvicorn_getsocket())
            try:
                nb = which('nb')
                if nb:
                    if self.plugin_name is not None:
                        process = subprocess.Popen(
                            [nb, 'plugin', 'uninstall', self.plugin_name],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                        process.communicate(input=b'y\n')
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
            server = self._uvicorn_getserver()
            await server.shutdown(self._uvicorn_getsocket())
            try:
                self._restart()
            except Exception as e:
                logger.error(e)
                await self.do_stop()
