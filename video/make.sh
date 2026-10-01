#!/usr/bin/env bash
# Rebuild the explainer end to end: narration -> soundtrack/captions -> frames -> MP4/WebM.
# Run from the repo root: bash video/make.sh   (set ELEVENLABS_API_KEY for the ElevenLabs voice)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build/frames
find build/frames -name '*.jpg' -delete
python3 narrate.py
python3 audio.py
cp explainer.vtt ../assets/video/explainer.vtt
cd ..
python3 -m http.server 8765 >/dev/null 2>&1 & SERVER=$!
trap 'kill $SERVER' EXIT
sleep 1
for w in 0 1 2 3; do node video/render.js "$w" 4 & done; wait $(jobs -p | grep -v "^$SERVER$") || true
ffmpeg -y -v error -framerate 30 -i video/build/frames/%05d.jpg -i video/build/mix.m4a -c:v libx264 -preset slow -crf 23 \
  -pix_fmt yuv420p -tune animation -c:a copy -shortest -movflags +faststart assets/video/explainer.mp4
ffmpeg -y -v error -framerate 30 -i video/build/frames/%05d.jpg -i video/build/mix.m4a -vf scale=1280:720 -c:v libvpx-vp9 \
  -crf 35 -b:v 0 -deadline good -cpu-used 4 -row-mt 1 -c:a libopus -b:a 96k -shortest assets/video/explainer.webm
ffmpeg -y -v error -i video/build/frames/00210.jpg -vf scale=1280:-2 -q:v 4 assets/video/explainer-poster.jpg
echo "done: $(ffprobe -v error -show_entries format=duration -of csv=p=0 assets/video/explainer.mp4)s"
