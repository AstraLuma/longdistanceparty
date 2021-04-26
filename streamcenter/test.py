import asyncio
import importlib.resources
import os
import traceback

from streamcenter.electricsheep import Shepherd, Client, DirStore

from streamcenter.mediaplayer import Vlc


SHEEP_DIR = os.path.expanduser("~/.sheep")


async def run(cmd):
    proc = await asyncio.create_subprocess_exec(*cmd)
    await proc.communicate()
    if proc.returncode:
        raise Exception("idk, program failed")


async def main():
    try:
        os.makedirs(SHEEP_DIR, exist_ok=True)
        shepherd = Shepherd(
            client=Client(),
            store=DirStore(SHEEP_DIR),
        )
        async with shepherd:
            while not shepherd.store:
                print("Waiting for sheep...")
                await asyncio.sleep(10)
            seq = shepherd.run_sequence()
            next_item = seq.__anext__

            with importlib.resources.path('streamcenter.logos', 'electricsheep-attr.png') as logo:
                async with Vlc() as player:
                    @player.on_impending_end.handler
                    async def add_next(**_):
                        n = await next_item()
                        await player.vlc_queue_item(n.path.as_uri(), logo_file=logo)

                    n = await next_item()
                    await player.vlc_play_item(n.path.as_uri(), logo_file=logo)

                    while True:
                        await asyncio.sleep(300)
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
