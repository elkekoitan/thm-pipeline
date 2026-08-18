#!/usr/bin/env python3
"""Persistent build queue: keeps trying remaining slugs in order,
waits between attempts (for layer availability), one render at a time.
Uses per-slug lockfiles so the render check is slug-specific and safe."""
import os
import signal
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

ORDER = ["01_cinematic", "02_lofi", "05_ambient_electronic",
         "07_sleep_healing", "03_jazz", "04_classical_piano",
         "06_deep_bass", "08_nature", "09_epic_fantasy", "10_meditation",
         "11_chinese_guzheng", "14_indian_sitar", "16_arabic_oud",
         "17_acem_ottoman", "19_african_savanna", "22_celtic_harp",
         "23_viking_nordic", "27_turkish_instrumental", "12_incense_ambient"]
STEMS = {"01_cinematic": "cinematic", "02_lofi": "lofi", "03_jazz": "jazz",
         "04_classical_piano": "classical", "05_ambient_electronic": "ambient",
         "06_deep_bass": "deepbass", "07_sleep_healing": "sleep",
         "08_nature": "nature", "09_epic_fantasy": "epic",
         "10_meditation": "meditation",
         "11_chinese_guzheng": "guzheng", "14_indian_sitar": "sitar",
         "16_arabic_oud": "oud", "17_acem_ottoman": "acem",
         "19_african_savanna": "savanna", "22_celtic_harp": "harp",
         "23_viking_nordic": "viking", "27_turkish_instrumental": "saz",
         "12_incense_ambient": "incense"}

MAX_RETRIES = 3


def layers_ready(slug):
    return all(os.path.exists(f"{slug}/{p}")
               for p in ("cover.png", "fg_layer.png", "bg_layer.png"))


def is_render_running(slug):
    """True only if THIS slug's builder process is alive."""
    lock = f"/tmp/render_{slug}.lock"
    if os.path.exists(lock):
        try:
            pid = int(open(lock).read().strip())
            os.kill(pid, 0)
            return True
        except (ValueError, OSError, ProcessLookupError):
            try:
                os.remove(lock)
            except OSError:
                pass
    return False


def any_build_running():
    """True if ANY builder runs (protects 4GB RAM)."""
    for line in subprocess.check_output(
            ["ps", "aux"]).decode().splitlines():
        if "build_wave1_cinematic.py" in line:
            return True
    return False


def main():
    retries = {}
    while ORDER:
        for slug in list(ORDER):
            if not layers_ready(slug):
                continue
            if any_build_running():
                print(f"[queue] render busy, waiting 60s ...", flush=True)
                time.sleep(60)
                break  # re-scan loop
            if is_render_running(slug):
                time.sleep(30)
                continue
            print(f"[queue] building {slug} ...", flush=True)
            lock = f"/tmp/render_{slug}.lock"
            with open(lock, "w") as fh:
                fh.write(str(os.getpid()))
            try:
                rc = subprocess.run(
                    ["python3", "build_wave1_cinematic.py", slug],
                    capture_output=False).returncode
            finally:
                try:
                    os.remove(lock)
                except OSError:
                    pass
            final_exists = os.path.exists(f"{slug}/{slug}_video.mp4")
            if final_exists:
                ORDER.remove(slug)
                retries.pop(slug, None)
                print(f"[queue] {slug} DONE", flush=True)
            else:
                n = retries.get(slug, 0) + 1
                retries[slug] = n
                if n >= MAX_RETRIES:
                    print(f"[queue] {slug} FAILED {n}x, giving up",
                          flush=True)
                    ORDER.remove(slug)
                else:
                    print(f"[queue] {slug} failed rc={rc}, "
                          f"retry {n}/{MAX_RETRIES}", flush=True)
            time.sleep(10)
        print("[queue] waiting 10 min before next round ...", flush=True)
        time.sleep(600)


if __name__ == "__main__":
    main()
