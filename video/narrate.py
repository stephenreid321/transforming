"""Synthesise the narration for each scene in script.json (Google TTS via gTTS),
trim silence, speed up slightly, and write build/<id>.wav + build/timing.json/.js."""
import json, subprocess
from gtts import gTTS

script = json.load(open("script.json"))
for sc in script:
    raw, wav = f"build/{sc['id']}.raw.mp3", f"build/{sc['id']}.wav"
    gTTS(sc["say"], lang="en", tld="co.uk").save(raw)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,atempo=1.14",
                    "-ar", "44100", "-ac", "1", wav], check=True)
    sc["dur"] = round(float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav])), 2)
json.dump(script, open("build/timing.json", "w"), indent=1)
open("build/timing.js", "w").write("window.TIMING=" + json.dumps(script) + ";")
print(round(sum(s["dur"] for s in script), 1), "s of narration")
