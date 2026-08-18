"""Chain scene clips with xfade transitions by writing the filter to a file.
ffmpeg 6.1's -filter_complex via subprocess splits arguments oddly; pass the
entire complex filter as a single -filter_complex option whose value comes
from a file is not supported, so we run one filter_complex with the full
semicolon-joined string passed as ONE argument via a list (which worked in
isolation), but the shell session strips ';'. Here we chain iteratively:
each step merges two files -> next input.
"""
import subprocess, sys, os

CROSSFADE = 1.0

def dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
        'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', p],
        capture_output=True, text=True).stdout.strip())

def xfade_two(a, b, out, offset):
    fc = f'[0:v][1:v]xfade=transition=fade:duration={CROSSFADE}:offset={offset:.3f}[v]'
    subprocess.run(['ffmpeg', '-y', '-i', a, '-i', b, '-filter_complex', fc,
        '-map', '[v]', '-c:v', 'libx264', '-preset', 'fast', '-crf', '19',
        '-pix_fmt', 'yuv420p', '-r', '30', out], check=True)

def main(clips, out):
    cur = clips[0]
    acc = dur(cur)
    for i in range(1, len(clips)):
        nxt = clips[i]
        offset = acc - CROSSFADE
        tmp = out + f'.step{i}.mp4'
        xfade_two(cur, nxt, tmp, offset)
        # xfade output length = offset + (dur(nxt) - CROSSFADE)
        acc = offset + (dur(nxt) - CROSSFADE)
        os.rename(tmp, cur)  # reuse file as accumulator
    os.rename(cur, out)
    print('Final chain duration:', dur(out))

if __name__ == '__main__':
    out = sys.argv[-1]
    clips = sys.argv[1:-1]
    main(clips, out)
