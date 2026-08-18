#!/usr/bin/env python3
"""THM skill arşivini Drive'a senkronize eder (gws +upload ile tek tar.gz dosyası)."""
import subprocess, os, sys, json, datetime

ARCHIVE = '/home/ubuntu/muzik/THM_skills_archive.tar.gz'
SKILLS_DIR = '/home/ubuntu/skills'
PARENT = '1qccnkOh5A0oXsOaIKF0h06L2vXk2F2qL'  # THM_Offical_Uretim_Arsivi

# THM ile ilgili skill'ler
SKILLS = ['thm-agents', 'hit-analyzer', 'music-prompter', 'instrumental-studio']

def main():
    if not os.path.exists(ARCHIVE):
        os.remove(ARCHIVE) if os.path.exists(ARCHIVE) else None
    for s in SKILLS:
        src = os.path.join(SKILLS_DIR, s)
        if not os.path.isdir(src):
            print(f'  WARN missing: {src}')
            continue
    tar_files = ' '.join(SKILLS)
    cmd = ['tar', '-czf', ARCHIVE, '-C', SKILLS_DIR] + [
        s for s in SKILLS if os.path.isdir(os.path.join(SKILLS_DIR, s))]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print('tar failed:', r.stderr[-500:])
        sys.exit(1)
    name = f'THM_skills_archive_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.tar.gz'
    r2 = subprocess.run(['gws', 'drive', '+upload', ARCHIVE, '--parent', PARENT, '--name', name],
                        capture_output=True, text=True)
    print(r2.stdout[-800:])
    if r2.returncode != 0:
        print('upload failed:', r2.stderr[-800:])
        sys.exit(1)

if __name__ == '__main__':
    main()
