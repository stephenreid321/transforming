"""Build the soundtrack: narration placed on the scene timeline + a soft generated pad.
Writes build/voice.wav, build/music.wav, build/mix.m4a and explainer.vtt captions."""
import json, re, subprocess, wave
import numpy as np

SR = 44100
T = json.load(open("build/timing.json"))
LEAD, TAIL = 0.8, 1.0
t = 0
for i, s in enumerate(T):
    s["lead"] = 1.8 if i == 0 else LEAD
    tail = 6.5 if i == len(T) - 1 else TAIL
    s["start"] = t
    t += s["lead"] + s["dur"] + tail
TOTAL = t
N = int(TOTAL * SR) + SR


def read_wav(p):
    with wave.open(p) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a


def write_wav(p, a):
    a = np.clip(a, -1, 1)
    with wave.open(p, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


voice = np.zeros(N, np.float32)
for s in T:
    a = read_wav(f"build/{s['id']}.wav")
    o = int((s["start"] + s["lead"]) * SR)
    voice[o:o + len(a)] += a
voice *= 0.9 / max(1e-6, np.abs(voice).max())
write_wav("build/voice.wav", voice)

# ---- generated pad: slow D major progression with a little shimmer ----
rng = np.random.default_rng(7)
f = lambda midi: 440 * 2 ** ((midi - 69) / 12)
CHORDS = [[38, 62, 66, 69, 73, 76], [35, 59, 62, 66, 69, 74], [43, 59, 62, 66, 71, 74], [45, 61, 64, 66, 69, 76]]
music = np.zeros(N, np.float32)
tt = np.arange(N) / SR
step = 8.0
k = 0
start = 0.0
while start < TOTAL:
    chord = CHORDS[k % len(CHORDS)]
    a0, a1 = int(start * SR), min(N, int((start + step + 4) * SR))
    seg = tt[a0:a1] - start
    env = np.clip(seg / 2.5, 0, 1) * np.clip((step + 4 - seg) / 4, 0, 1)
    for j, m in enumerate(chord):
        amp = 0.16 if j == 0 else 0.07
        for det in (-0.0015, 0.0015):
            ph = rng.uniform(0, 2 * np.pi)
            fr = f(m) * (1 + det)
            music[a0:a1] += amp * env * (np.sin(2 * np.pi * fr * seg + ph) + 0.18 * np.sin(4 * np.pi * fr * seg + ph))
    start += step
    k += 1
# shimmer: soft high notes from the D major pentatonic
pent = [74, 76, 78, 81, 83, 86]
for s0 in np.arange(1.5, TOTAL - 3, 2.6):
    m = pent[rng.integers(len(pent))]
    a0 = int(s0 * SR); seg = np.arange(int(3 * SR)) / SR
    if a0 + len(seg) > N: break
    music[a0:a0 + len(seg)] += 0.035 * np.exp(-seg * 1.6) * np.sin(2 * np.pi * f(m) * seg) * np.clip(seg / 0.02, 0, 1)
music *= 0.35 * np.clip(tt / 3, 0, 1) * np.clip((TOTAL - tt) / 4, 0, 1)
music /= max(1e-6, np.abs(music).max())
write_wav("build/music_dry.wav", music)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "build/music_dry.wav", "-af",
                "lowpass=f=3200,aecho=0.8:0.6:120|260|430:0.32|0.22|0.14,volume=0.9", "build/music.wav"], check=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "build/voice.wav", "-i", "build/music.wav", "-filter_complex",
                "[1:a]volume=0.17[m];[0:a]volume=1.0[v];[v][m]amix=inputs=2:duration=longest:normalize=0,"
                "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "128k", "-t", f"{TOTAL:.2f}",
                "build/mix.m4a"], check=True)


# ---- captions ----
def ts(x):
    h, m = divmod(x, 3600); m, s = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


cues = []
for s in T:
    text = s["say"].replace("A.I.", "AI")
    parts = [p.strip() for p in re.split(r"(?<=[.:?!])\s+", text) if p.strip()]
    chunks = []
    for p in parts:  # split long sentences at commas into ~70 char chunks
        words, cur = p.split(), ""
        for w_ in words:
            if len(cur) + len(w_) > 70 and cur:
                chunks.append(cur); cur = w_
            else:
                cur = (cur + " " + w_).strip()
        chunks.append(cur)
    total_chars = sum(len(c) for c in chunks)
    t0 = s["start"] + s["lead"]
    for c in chunks:
        d = s["dur"] * len(c) / total_chars
        cues.append((t0, t0 + d, c)); t0 += d
with open("explainer.vtt", "w") as fh:
    fh.write("WEBVTT\n\n")
    for i, (a, b, c) in enumerate(cues, 1):
        fh.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c}\n\n")
print(f"total {TOTAL:.2f}s, {len(cues)} captions")
