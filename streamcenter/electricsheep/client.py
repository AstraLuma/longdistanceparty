#| pip: requests
import dataclasses
import datetime
import gzip
import io
import time
import xml.etree.ElementTree as ET

import aiohttp


@dataclasses.dataclass
class Sheep:
    id: int
    type: int  # ???
    state: str  # enum of some kind
    time: datetime.datetime
    size: int
    rating: int  # ???
    first: int  # Node ID
    last: int  # Node ID
    url: str

    flock: int


class Client:
    _server = None
    _next_retry = None

    async def _async_init(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://community.sheepserver.net/query.php?q=redir', ssl=False) as resp:
                resp.raise_for_status()
                xml = ET.fromstring(await resp.text())

        redir = xml.find('redir')
        self._server = redir.get('host')

    async def itersheep(self):
        if self._server is None:
            await self._async_init()
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self._server}cgi/list') as resp:
                resp.raise_for_status()
                # We could, in theory, fix this up to be a fully async pipeline,
                # but the dataset is just not that big.
                with gzip.open(io.BytesIO(await resp.read()), 'rt', encoding='utf-8') as gz:
                    xml = ET.fromstring(gz.read())

        self._next_retry = time.time() + int(xml.get('retry'))
        flock = int(xml.get('gen'))

        for elem in xml.findall('sheep'):
            yield Sheep(
                id=int(elem.get('id')),
                type=int(elem.get('type')),
                state=elem.get('state'),
                time=datetime.datetime.utcfromtimestamp(int(elem.get('time'))),
                size=int(elem.get('size')),
                rating=int(elem.get('rating')),
                first=int(elem.get('first')),
                last=int(elem.get('last')),
                url=elem.get('url'),
                flock=flock
            )

    def time_until_next_try(self):
        if self._next_retry:
            return self._next_retry - time.time()
        else:
            return 0
