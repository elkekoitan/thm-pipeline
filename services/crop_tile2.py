#!/usr/bin/env python3
"""Crop tile (col, row) from Higgsfield gallery grid and save as 2048x1152 scene."""
import sys
from PIL import Image

def main():
    grid_path, col, row, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    im = Image.open(grid_path).convert('RGB')
    w, h = im.size
    tw, th = w // 3, h // 2
    # trim bottom overlap of tiles (row boundary artifacts)
    th2 = int(th * 0.65)
    tile = im.crop((col * tw, row * th, col * tw + tw, row * th + th2))
    nw = 2048
    nh = int(tile.height * nw / tile.width)
    tile = tile.resize((nw, nh), Image.LANCZOS)
    if nh != 1152:
        cy = nh // 2
        tile = tile.crop((0, max(0, cy - 576), nw, max(0, cy - 576) + 1152))
    tile.save(out)
    print('saved', out, tile.size)

if __name__ == '__main__':
    main()
