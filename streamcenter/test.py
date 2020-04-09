import asyncio
import os

from electricsheep import Shepherd, Client, DirStore

from mediaplayer import Vlc


async def run(cmd):
    proc = await asyncio.create_subprocess_exec(*cmd)
    await proc.communicate()
    if proc.returncode:
        raise Exception("idk, program failed")


async def main():
    os.makedirs('/tmp/sheep', exist_ok=True)
    shepherd = Shepherd(
        client=Client(),
        store=DirStore('/tmp/sheep'),
    )
    async with shepherd:
        while not shepherd.store:
            print("Waiting for sheep...")
            await asyncio.sleep(10)
        seq = shepherd.run_sequence()
        next_item = seq.__anext__

        async with Vlc() as player:
            @player.on_impending_end.handler
            async def add_next(**_):
                n = await next_item()
                await player.vlc_queue_item(n.path.as_uri())

            n = await next_item()
            await player.vlc_play_item(n.path.as_uri())

            await asyncio.sleep(300)


if __name__ == '__main__':
    asyncio.run(main())
