#!/usr/bin/env python3
"""Derive parallax layer assets from an existing cover image.

bg_layer.png  = distant elements: keep the far (upper/vanishing) region,
                blur horizon detail, preserve glow/colors.
fg_layer.png  = near elements: darkened copy of full cover for the
                foreground parallax overlay (builder multiplies it in).

Usage: python3 make_layers_from_cover.py <slug_dir>

The cover is 1344x768 (16:9). Output layers at 1920x1080 (slightly larger
than render frame so parallax crop has margin).
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

BASE = "/home/ubuntu/muzik/instrumental"
W, H = 1920, 1080


def main():
    slug = sys.argv[1]
    cover = Image.open(f"{BASE}/{slug}/cover.png").convert("RGB")
    cw, ch = cover.size

    # --- bg_layer: distant region (upper ~45% + vanishing point area) ---
    bg = cover.resize((cw * 2, ch * 2), Image.LANCZOS)  # upscale 2x for 1920w
    arr = np.asarray(bg).astype(np.float32)
    # darken lower half (near ground/road reflections belong to fg)
    h2 = arr.shape[0] // 2
    arr[h2:] *= 0.35
    # soften distant lights slightly (motion will blur them anyway)
    bg_img = Image.fromarray(arr.astype("uint8"))
    # crop to 1920x1080 with margin 1.14 handled by builder; here make exact
    if bg_img.size != (W, H):
        bg_img = bg_img.resize((W, H), Image.LANCZOS)
    bg_img = bg_img.filter(ImageFilter.GaussianBlur(2.0))
    bg_img.save(f"{BASE}/{slug}/bg_layer.png")
    print(f"{slug}/bg_layer.png saved {bg_img.size}")

    # --- fg_layer: full frame darkened for overlay ---
    fg = np.asarray(cover.resize((W, H), Image.LANCZOS)).astype(np.float32)
    # keep it dim so mid elements (drawn from cover) stay visible
    fg *= 0.55
    Image.fromarray(fg.astype("uint8")).save(f"{BASE}/{slug}/fg_layer.png")
    print(f"{slug}/fg_layer.png saved")


if __name__ == "__main__":
    main()
