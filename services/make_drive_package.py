#!/usr/bin/env python3
"""Package all produced assets into per-category Drive-upload-ready folders.

Structure on Drive:
  THM_Offical - Uretim Arsivi/
    01_Cinematic/        -> video, parts, cover, layers, music (wav/mp3)
    02_Lofi/             -> ...
    ...
"""
import os, shutil, subprocess, json

BASE = '/home/ubuntu/muzik/instrumental'
PKG = '/home/ubuntu/drive_package'

CATS = [
    ('01_cinematic', '01_Cinematic'),
    ('02_lofi', '02_Lofi'),
    ('03_jazz', '03_Jazz'),
    ('04_classical_piano', '04_Classical_Piano'),
    ('05_ambient_electronic', '05_Ambient_Electronic'),
    ('06_deep_bass', '06_Deep_Bass'),
    ('07_sleep_healing', '07_Sleep_Healing'),
    ('08_nature', '08_Nature'),
    ('09_epic_fantasy', '09_Epic_Fantasy'),
    ('10_meditation', '10_Meditation'),
    ('11_chinese_guzheng', '11_Chinese_Guzheng'),
    ('12_incense_ambient', '12_Incense_Ambient'),
    ('14_indian_sitar', '14_Indian_Sitar'),
    ('16_arabic_oud', '16_Arabic_Oud'),
    ('17_acem_ottoman', '17_Acem_Ottoman'),
    ('19_african_savanna', '19_African_Savanna'),
    ('22_celtic_harp', '22_Celtic_Harp'),
    ('23_viking_nordic', '23_Viking_Nordic'),
    ('27_turkish_instrumental', '27_Turkish_Instrumental'),
]

STEM = {
    '01_cinematic': 'cinematic', '02_lofi': 'lofi', '03_jazz': 'jazz',
    '04_classical_piano': 'classical', '05_ambient_electronic': 'ambient',
    '06_deep_bass': 'deepbass', '07_sleep_healing': 'sleep',
    '08_nature': 'nature', '09_epic_fantasy': 'epic', '10_meditation': 'meditation',
    '11_chinese_guzheng': 'guzheng', '12_incense_ambient': 'incense',
    '14_indian_sitar': 'sitar', '16_arabic_oud': 'oud', '17_acem_ottoman': 'acem',
    '19_african_savanna': 'savanna', '22_celtic_harp': 'harp',
    '23_viking_nordic': 'viking', '27_turkish_instrumental': 'saz',
}

def main():
    if os.path.exists(PKG):
        shutil.rmtree(PKG)
    os.makedirs(PKG)
    report = {}
    for slug, name in CATS:
        src = os.path.join(BASE, slug)
        dst = os.path.join(PKG, name)
        os.makedirs(dst, exist_ok=True)
        files = {}
        # cover & layers
        for f in ['cover.png', 'fg_layer.png', 'bg_layer.png']:
            p = os.path.join(src, f)
            if os.path.exists(p):
                shutil.copy(p, os.path.join(dst, 'artwork_' + f))
                files[f] = True
        # music
        stem = STEM[slug]
        music_dir = os.path.join(dst, 'music')
        os.makedirs(music_dir, exist_ok=True)
        for f in [f'{stem}_a.mp3', f'{stem}_b.mp3', f'{stem}_a.wav', f'{stem}_b.wav',
                  f'{stem}_extended.mp3', f'{stem}_preview_60.mp3']:
            p = os.path.join(src, f)
            if os.path.exists(p):
                shutil.copy(p, music_dir)
                files[f] = True
        # video & parts
        v = os.path.join(src, f'{slug}_video.mp4')
        if os.path.exists(v):
            shutil.copy(v, dst)
            files['video'] = os.path.getsize(v)
        s = os.path.join(src, f'{slug}_short.mp4')
        if os.path.exists(s):
            shutil.copy(s, dst)
            files['short'] = os.path.getsize(s)
        parts_dir = os.path.join(src, 'parts')
        if os.path.isdir(parts_dir):
            pd = os.path.join(dst, 'parts_14min')
            os.makedirs(pd, exist_ok=True)
            for f in sorted(os.listdir(parts_dir)):
                if f.endswith('.mp4'):
                    shutil.copy(os.path.join(parts_dir, f), pd)
                    files['part_' + f] = os.path.getsize(os.path.join(parts_dir, f))
        report[name] = files
        total = sum(v for k, v in files.items() if isinstance(v, int)) / 1e9
        print(f"{name}: {len(files)} files, {total:.2f} GB")
    with open(os.path.join(PKG, 'package_report.json'), 'w') as fp:
        json.dump(report, fp, indent=1)
    # also create README per folder listing files
    for name in report:
        with open(os.path.join(PKG, name, 'README.txt'), 'w') as fp:
            fp.write(f"THM Official production package - {name}\n")
            for k in report[name]:
                fp.write(f"- {k}\n")
    print('done')

if __name__ == '__main__':
    main()
