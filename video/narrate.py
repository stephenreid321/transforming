"""Synthesise the narration for each scene in script.json and write
build/<id>.wav + build/timing.json/.js (the stage re-times itself to these).

Uses ElevenLabs when ELEVENLABS_API_KEY is set (voice ELEVENLABS_VOICE_ID,
default below); otherwise falls back to gTTS so the pipeline still runs."""
import json, os, subprocess, urllib.request

VOICE = os.environ.get("ELEVENLABS_VOICE_ID", "wbvPJtdvQElwzVU138tF")
KEY = os.environ.get("ELEVENLABS_API_KEY")
TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
        "silenceremove=start_periods=1:start_threshold=-45dB,areverse")

script = json.load(open("script.json"))
for i, sc in enumerate(script):
    raw, wav = f"build/{sc['id']}.raw.mp3", f"build/{sc['id']}.wav"
    if KEY:
        body = {"text": sc["say"].replace("A.I.", "AI"), "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.15, "use_speaker_boost": True}}
        # neighbouring lines keep intonation consistent across scenes
        if i > 0:
            body["previous_text"] = script[i - 1]["say"]
        if i < len(script) - 1:
            body["next_text"] = script[i + 1]["say"]
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128",
            data=json.dumps(body).encode(), method="POST",
            headers={"xi-api-key": KEY, "Content-Type": "application/json", "Accept": "audio/mpeg"})
        with urllib.request.urlopen(req) as r, open(raw, "wb") as f:
            f.write(r.read())
        af = TRIM
    else:
        from gtts import gTTS
        gTTS(sc["say"], lang="en", tld="co.uk").save(raw)
        af = TRIM + ",atempo=1.14"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", af, "-ar", "44100", "-ac", "1", wav], check=True)
    sc["dur"] = round(float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav])), 2)
    print(f"{sc['id']:10s} {sc['dur']:5.1f}s")
json.dump(script, open("build/timing.json", "w"), indent=1)
open("build/timing.js", "w").write("window.TIMING=" + json.dumps(script) + ";")
print(round(sum(s["dur"] for s in script), 1), "s of narration", "(ElevenLabs)" if KEY else "(gTTS fallback)")
