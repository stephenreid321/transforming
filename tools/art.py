"""Render the 'ink layer' of every spread (text removed) and cut it into
figures: photos, drawings, scribbles and lettering become alpha masks that the
site recolours with CSS (mask-image), so they follow each chapter's ink colour.

Writes assets/art/*.webp and content/art.json (chapter heroes: tools/hero.py).
Usage: python3 tools/art.py [page ...]   # optional pages to re-run
"""
import json
import numpy as np
import pymupdf
from PIL import Image
from scipy import ndimage

PDF = "Transforming how we lead together.pdf"
ZOOM = 2  # 144 dpi
INK = [(3, "4f0e64"), (33, "232176"), (50, "004b1c"), (69, "005e5a"), (88, "5c5349"), (106, "700044")]
MAIN = {"h1", "h2", "h3", "h4", "body", "box", "boxhead", "boxsub", "story"}


def ink_for(page):
    c = INK[0][1]
    for start, col in INK:
        if page >= start:
            c = col
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


import sys
raw = {p["page"]: p for p in json.load(open("content/raw.json"))}
doc = pymupdf.open(PDF)
MERGE = json.load(open("content/curation.json")).get("merge_art", [])
ONLY = {int(a) for a in sys.argv[1:]}  # optionally re-run just these pages
art = [a for a in json.load(open("content/art.json")) if a["page"] not in ONLY] if ONLY else []

for pno in range(2, len(doc) - 1):
    page_no = pno + 1
    if ONLY and page_no not in ONLY:
        continue
    page = doc[pno]
    W, H = page.rect.width, page.rect.height
    page.add_redact_annot(page.rect)
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                          text=pymupdf.PDF_REDACT_TEXT_REMOVE)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].astype(np.float32)
    ink = ink_for(page_no)
    alpha = np.zeros(img.shape[:2], dtype=np.float32)
    halves = [(0, pix.width // 2), (pix.width // 2, pix.width)] if W > 600 else [(0, pix.width)]
    for x0, x1 in halves:
        part = img[:, x0:x1]
        q = (part[::8, ::8] // 8).reshape(-1, 3)
        vals, counts = np.unique(q, axis=0, return_counts=True)
        bg = vals[counts.argmax()] * 8 + 4
        v = ink - bg
        a = ((part - bg) @ v) / max(1.0, float(v @ v))
        alpha[:, x0:x1] = np.clip((a - 0.06) / 0.94, 0, 1)  # floor drops faint paper-tone rectangles
    binary = alpha > 0.22
    small = binary[: binary.shape[0] // 4 * 4, : binary.shape[1] // 4 * 4]
    small = small.reshape(small.shape[0] // 4, 4, small.shape[1] // 4, 4).any(axis=(1, 3))
    grown = ndimage.binary_dilation(small, structure=np.ones((7, 7)))
    labels, n = ndimage.label(grown)
    # text line centres in page coordinates
    centres = []
    for hi, half in enumerate(raw[page_no]["halves"]):
        for l in half:
            if l["cls"] in MAIN:
                off = W / 2 if (hi == 1 and W > 600) else 0
                centres.append(((l["x0"] + l["x1"]) / 2 + off, (l["y0"] + l["y1"]) / 2))
    k = 0
    comps = []
    for sl in ndimage.find_objects(labels):
        ys, xs = sl
        X0, X1, Y0, Y1 = xs.start * 4, xs.stop * 4, ys.start * 4, ys.stop * 4
        crop = alpha[Y0:Y1, X0:X1]
        wpt, hpt = (X1 - X0) / ZOOM, (Y1 - Y0) / ZOOM
        if (wpt < 22 and hpt < 22) or (crop > 0.22).sum() < 400:
            continue
        bx0, by0, bx1, by1 = X0 / ZOOM, Y0 / ZOOM, X1 / ZOOM, Y1 / ZOOM
        inside = [(cx, cy) for cx, cy in centres if bx0 <= cx <= bx1 and by0 <= cy <= by1]
        # text printed on top of ink means this is a background (halftone behind a story, ink box)
        covered = sum(1 for cx, cy in inside
                      if alpha[max(0, int(cy * ZOOM) - 3):int(cy * ZOOM) + 4, max(0, int(cx * ZOOM) - 3):int(cx * ZOOM) + 4].max() > 0.22)
        inside = len(inside)
        solid = (crop > 0.8).mean()
        if covered >= 2 or solid > 0.8:
            continue
        comps.append([f"p{page_no}-{k}", X0, Y0, X1, Y1, inside])
        k += 1
    for group in MERGE:
        members = [c for c in comps if c[0] in group]
        if len(members) > 1:
            comps = [c for c in comps if c[0] not in group]
            comps.append([members[0][0], min(c[1] for c in members), min(c[2] for c in members),
                          max(c[3] for c in members), max(c[4] for c in members), 0])
    for name, X0, Y0, X1, Y1, inside in comps:
        crop = alpha[Y0:Y1, X0:X1]
        bx0, by0, bx1, by1 = X0 / ZOOM, Y0 / ZOOM, X1 / ZOOM, Y1 / ZOOM
        rgba = np.zeros(crop.shape + (4,), dtype=np.uint8)
        rgba[:, :, 3] = (crop * 255).astype(np.uint8)
        Image.fromarray(rgba, "RGBA").save(f"assets/art/{name}.webp", quality=80, method=6)
        wide = W > 600 and bx0 < W / 2 - 40 and bx1 > W / 2 + 40
        half = 0 if (W < 600 or (bx0 + bx1) / 2 < W / 2 or wide) else 1
        off = W / 2 if half == 1 else 0
        art.append({"name": name, "page": page_no, "half": half, "wide": wide,
                    "bbox": [bx0 - off, by0, bx1 - off, by1], "px": [X1 - X0, Y1 - Y0],
                    "inside": inside, "density": float((crop > 0.22).mean())})

art.sort(key=lambda a: (a["page"], int(a["name"].split("-")[1])))
json.dump(art, open("content/art.json", "w"), indent=1)
print(len(art), "figures")
