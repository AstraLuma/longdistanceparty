#!/usr/bin/env xonsh

DEST_DIR = p"~/.sheep/download"
DEST_DIR.mkdir(exist_ok=True)

for group in range(55000, 0, -2500):
    print(f"Grabbing {group}...", end='', flush=True)
    for i in range(0, 10):
        print(i, end='', flush=True)
        src = f"https://archive.org/compress/electricsheep-flock-247-{group:05}-{i}/formats=CINEPACK",
        dst = DEST_DIR / f"247-{group:05}-{i}.zip"
        if dst.exists():
            continue
        proc = ![wget --quiet @(src) -O @(dst) --continue]
        if not proc:
            dst.unlink()
            break
    print("", flush=True)
