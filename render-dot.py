#!/usr/bin/env python3
"""
Write out a graphviz file of the stored sheep
"""
import glob
import os

os.chdir(os.path.expanduser("~/.sheep"))

print("digraph {")
print("repulsiveforce=50")
print("K=1")

for file in glob.glob("00247=*.*"):
    stem, ext = os.path.splitext(file)
    flock, sid, first, last = map(int, stem.split('=', 3))
    assert flock == 247
    print(f"{first} -> {last}")

print("}")
