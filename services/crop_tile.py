import sys
from PIL import Image

src, dst, row, col = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
im = Image.open(src)
w, h = im.size
tw, th = w // 3, h // 2
tile = im.crop((col * tw, row * th, (col + 1) * tw, (row + 1) * th))
tile = tile.resize((2048, 1152), Image.LANCZOS)
tile.save(dst)
print('saved', dst, tile.size)
