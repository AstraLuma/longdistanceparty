import asyncio
import random

from .client import Client
from .directory_store import DirStore

__all__ = 'Client', 'DirStore', 'Shepherd',


class Shepherd:
    """
    Full Electric Sheep handler. Includes:
    * Background task for downloading new sheep
    * Management of storage

    Use as an async context manager.
    """

    def __init__(self, *, client, store):
        self.client = client
        self.store = store

    async def __aenter__(self):
        self._task = asyncio.create_task(self._background_poll(), name=f"Shepherd poll: {self!r}")
        return self

    async def __aexit__(self, *exc):
        self._task.cancel()

    async def _background_poll(self):
        while True:
            t = self.client.time_until_next_try()
            if t > 0:
                print(f"Sleeping {t} seconds...")
                await asyncio.sleep(t)
            async for sheep in self.client.itersheep():
                await self.store.add(sheep)

    async def run_sequence(self, loop_chance=0.5):
        """
        An algorithm for producing sheep for playback.

        At each node, will use a fixed chance to take a loop or branch to a new
        node.
        """
        current = random.choice([s async for s in self.store])
        while True:
            yield current

            loops = [s async for s in self.store if s.first == s.last == current.last]
            branches = [s async for s in self.store if s.first == current.last != s.last]
            if not loops and not branches:
                # Stuck! Pick one at random
                current = random.choice([s async for s in self.store])
            elif loops and random.random() < loop_chance:
                current = random.choice(loops)
            else:
                current = random.choice(branches)
