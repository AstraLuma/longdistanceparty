import contextlib
import dataclasses
import mimetypes
import pathlib

import aiofiles
import aiohttp


@dataclasses.dataclass
class Sheep:
    flock: int
    id: int
    first: int  # Node ID
    last: int  # Node ID

    path: str

    @contextlib.asynccontextmanager
    async def open(self):
        with aiofiles.open(self.path, 'rb') as obj:
            yield obj


class DirStore:
    """
    A very basic sheep store that uses directories and filenames.
    """
    def __init__(self, root):
        self.root = pathlib.Path(root)

    def __bool__(self):
        return bool(list(self.root.iterdir()))

    async def __aiter__(self):
        for file in self.root.iterdir():
            if '=' not in file.name:
                continue
            flock, id, first, last = file.stem.split('=', 3)
            yield Sheep(flock=int(flock), id=int(id), first=int(first), last=int(last), path=file)

    async def add(self, sheep):
        """
        Adds the given sheep to the client
        """
        if list(self.root.glob(f"{sheep.flock:05}={sheep.id:05}=*")):
            # A sheep with this ID exists
            return
        print(f"Downloading {sheep.url}")
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(sheep.url) as resp:
                ext = mimetypes.guess_extension(resp.headers.get('Content-Type')) or ''
                filename = self.root / f"{sheep.flock:05}={sheep.id:05}={sheep.first:05}={sheep.last:05}{ext}"
                async with aiofiles.open(filename, 'wb') as dest:
                    async for chunk in resp.content.iter_any():  # Variable-sized chunks
                        await dest.write(chunk)
