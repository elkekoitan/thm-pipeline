import numpy as np
import librosa

y, sr = librosa.load('/home/ubuntu/muzik/saltwater.mp3', sr=None)
duration = len(y) / sr
print(f"Duration: {duration:.2f}s, sr={sr}")

# Detect tempo
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
beat_times = librosa.frames_to_time(beats, sr=sr)
print(f"Estimated tempo: {tempo[0]:.2f} BPM, {len(beat_times)} beats")

# Energy per half-beat window for animation sync
hop = len(y) // 6000  # ~30ms windows -> 6000 frames
rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop)[0]
times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)

# Output as JSON: per-second min/max/mean energy + beat times
out = {
    "duration": float(duration),
    "tempo": float(tempo[0]),
    "beats": [round(float(t), 3) for t in beat_times],
    "per_second": [],
}
import json
for s in range(int(np.ceil(duration))):
    mask = (times >= s) & (times < s + 1)
    seg = rms[mask]
    if len(seg) == 0:
        continue
    # normalize energy 0-1 with dynamic range mapping
    db = 20 * np.log10(seg.clip(min=1e-6))
    mn, mx = -40, -12
    norm = np.clip((seg.mean() - 10**(mn/20)) / (10**(mx/20) - 10**(mn/20)), 0, 1)
    out["per_second"].append({"t": s, "norm": round(float(norm), 3), "loud": bool(norm > 0.55)})

# Beat pulse markers
pulses = []
for i, t in enumerate(beat_times):
    pulses.append(round(float(t), 3))
out["pulses"] = pulses

with open('/home/ubuntu/muzik/saltwater_rhythm.json', 'w') as f:
    json.dump(out, f)
print("Saved saltwater_rhythm.json")

# Print beat times in groups of 16 for structure
for start in range(0, len(beat_times), 16):
    chunk = beat_times[start:start+16]
    if len(chunk):
        print(f"beats {start}-{min(start+15, len(beat_times)-1)}: {chunk[0]:.2f}s -> {chunk[-1]:.2f}s")
