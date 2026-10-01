# Transforming how we lead together: web edition

An interactive website for the handbook *Transforming how we lead together – Moving from hierarchies towards co-creation* (Nina Božič Yams, Laura Gottlieb and Álvaro Aranda Muñoz, Stockholm 2026, CC BY 4.0). The full PDF is in this repository.

The site is plain static HTML, CSS and JavaScript with no build step needed to serve it. Open `index.html` locally, or publish the repository root with GitHub Pages (Settings → Pages → Deploy from a branch → `/ (root)`).

## What's in it

- **Home**: the cover lettering, why the handbook exists, the six chapters (with your reading progress) and ways in.
- **Introduction and chapters 1–6**: the full text, with each chapter in its print colour. It includes the halftone photos, hand-drawn diagrams and scribbles from the book, margin notes and links, Voices from the field on notebook paper, and the case journeys as expandable panels.
- **Elena's story**: the fictional thread that opens every chapter, collected on one page.
- **Practice library**: every practice and movement score, filterable (on your own, with a team, movement, by chapter). Movement scores that have a duration come with a built-in timer.
- **Reflection journal**: the end-of-chapter questions. Reflections are saved only in the reader's browser (localStorage) and can be downloaded as Markdown or printed.
- **Voices**: all practitioner and artist excerpts, filterable by person.
- **Search** (press `/` or `Ctrl/⌘ K`) across the whole handbook, plus a dark mode.

Images are alpha masks taken from the PDF and recoloured with CSS (`mask-image`), so each chapter's ink colour carries through and dark mode works. Fonts (Bitter, Hanken Grotesk, EB Garamond; SIL OFL) are self-hosted, so the site makes no third-party requests.

## Rebuilding from the PDF

Requires Python 3 with `pymupdf numpy scipy pillow`.

```sh
python3 tools/extract.py    # PDF text -> content/raw.json (classified lines)
python3 tools/art.py        # PDF ink layer -> assets/art/*.webp + content/art.json (slow; pass page numbers to redo only those)
python3 tools/hero.py       # chapter opener artwork + social image
python3 tools/structure.py  # -> content/handbook.json (chapters, sections, boxes, figures, notes)
python3 tools/build.py      # -> *.html + assets/search-index.js
```

Hand corrections live in `content/curation.json`: figures to drop or merge, words the PDF fonts split apart, practice titles and tags, and small text patches. Fix content there and re-run `structure.py` and `build.py`.

## Explainer video

`assets/video/explainer.mp4` (plus a WebM fallback, poster and captions) is a 2-minute motion-graphics explainer made from the handbook's own artwork. It is embedded on the homepage. To change it, edit `video/script.json` (narration) or `video/stage.html` (scenes), then:

```sh
mkdir -p video/build/frames && cd video
python3 narrate.py                      # narration per scene (gTTS) + timing
python3 audio.py                        # narration on the timeline + generated music bed + captions
cd .. && python3 -m http.server 8765 &  # stage.html is rendered from a local server
for w in 0 1 2 3; do node video/render.js $w 4 & done; wait   # 30 fps JPEG frames (Playwright)
ffmpeg -framerate 30 -i video/build/frames/%05d.jpg -i video/build/mix.m4a -c:v libx264 -crf 23 -pix_fmt yuv420p -c:a copy -shortest -movflags +faststart assets/video/explainer.mp4
```

Open `video/stage.html` in a browser to preview it as a live loop, or add `?t=42` to see one moment. The narration is a synthetic voice; to use a human recording, replace `video/build/<scene>.wav` and re-run `audio.py`.
