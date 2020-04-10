"""
API around VLC
"""
# See https://github.com/videolan/vlc/blob/master/share/lua/http/requests/README.txt
import asyncio
import contextlib
import subprocess
import traceback
import xml.etree.ElementTree as ET

import aiohttp

from aioevents import Event


def walk_playlist(root):
    yield root
    for child in root['children']:
        yield from walk_playlist(child)


async def dump_traceback(func, *p, **kw):
    try:
        return await func(*p, **kw)
    except Exception:
        traceback.print_exc()


class Vlc:
    on_time_update = Event("Timestamp update")
    on_current_changed = Event("Current video has changed")
    on_impending_end = Event("Playback is going to stop soon")

    def __init__(self):
        self._stack = contextlib.AsyncExitStack()
        self._password = "foo"  # secrets.token_urlsafe()
        self._port = 8080  # random.randint(1024, 65535)

    async def __aenter__(self):
        self.proc = await asyncio.create_subprocess_exec(
            'vlc', '-I', 'http', '--http-password', self._password, '--http-port', str(self._port),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self._stack.callback(self.proc.terminate)
        self._http = await self._stack.enter_async_context(
            aiohttp.ClientSession(auth=aiohttp.BasicAuth('', self._password), raise_for_status=True)
        )
        self._url = f"http://localhost:{self._port}"

        while True:
            try:
                async with self._http.get(f"{self._url}/requests/status.json"):
                    pass
            except Exception:
                continue
            else:
                break

        proc = asyncio.create_task(dump_traceback(self._maintenance_task), name=f"VLC Manager: {self!r}")
        self._stack.callback(proc.cancel)
        return self

    async def __aexit__(self, *exc):
        await self._stack.aclose()

    async def _maintenance_task(self):
        """
        Handles polling VLC and shuffling data around
        """
        old_filename = None
        old_time = None
        while True:
            status = await self.vlc_status()
            try:
                time_total, time_elapsed = status['length'], status['time']
                remaining = time_total - time_elapsed
                filename = status['information']['category']['meta']['filename']
            except KeyError:
                time_total, time_elapsed = None, None
                remaining = None
                filename = None

            # Publish timestamp updates
            if filename != old_filename:
                self.on_current_changed(filename=filename)

            if time_elapsed != old_time:
                self.on_time_update(elapsed=time_elapsed, total=time_total)

            if remaining is not None and remaining < 2:
                await self._update_playlist(status['currentplid'])

            old_time = time_elapsed
            old_filename = filename

    async def _update_playlist(self, plid):
        playlist = await self.vlc_playlist_etree()

        parent = playlist.find(f".//*[@id='{plid}']..")
        for i, current in enumerate(parent):
            if current.get('id') == str(plid):
                break
        else:
            # Odd...
            return

        if len(parent) == i + 1:
            # Last item
            self.on_impending_end()

    async def vlc_status(self):
        """
        Get raw VLC status
        """
        async with self._http.get(f"{self._url}/requests/status.json") as resp:
            return await resp.json(content_type='text/plain')

    async def vlc_playlist(self):
        """
        Get raw VLC playlist
        """
        async with self._http.get(f"{self._url}/requests/playlist.json") as resp:
            return await resp.json(content_type='text/plain')

    async def vlc_playlist_etree(self):
        """
        Get raw VLC playlist (as an ElementTree)
        """
        async with self._http.get(f"{self._url}/requests/playlist.xml") as resp:
            return ET.fromstring(await resp.text())

    async def vlc_queue_item(self, url):
        """
        Add a file to the end of the playlist.
        """
        async with self._http.get(
            f"{self._url}/requests/playlist.json",
            params={'command': 'in_enqueue', 'input': url},
        ):
            pass

    async def vlc_play_item(self, url):
        """
        Play a file immediately
        """
        async with self._http.get(
            f"{self._url}/requests/playlist.json",
            params={'command': 'in_play', 'input': url},
        ):
            pass

    async def vlc_pause(self, url):
        """
        Pause playback
        """
        async with self._http.get(
            f"{self._url}/requests/playlist.json",
            params={'command': 'pl_forcepause', 'input': url},
        ):
            pass

    async def vlc_unpause(self, url):
        """
        Resume playback
        """
        async with self._http.get(
            f"{self._url}/requests/playlist.json",
            params={'command': 'pl_forceresume', 'input': url},
        ):
            pass
