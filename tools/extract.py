"""Extract the handbook PDF into a structured JSON stream of blocks.

Usage: python3 tools/extract.py  ->  content/raw.json
The PDF is laid out as two-page spreads; each spread is split into a left and
right half and the text is classified by font (see classify()).
"""
import json, re, html, collections
import pymupdf

PDF = "Transforming how we lead together.pdf"
doc = pymupdf.open(PDF)

LIG = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}


def fix_ligatures(t):
    for k, v in LIG.items():
        t = re.sub(k + r" ?", v, t)
    return t


def classify(span):
    f, sz, c = span["font"], round(span["size"], 1), span["color"]
    if sz < 5:
        return "skip"
    if f.startswith("Freya"):
        if sz > 20:
            return "dropcap"
        if 9 <= sz <= 10:
            return "story"
        return "skip"  # chapter markers, folios, miniature spreads
    if f.startswith("HalyardDisplay"):
        if sz >= 25:
            return "h1"
        if sz >= 15:
            return "h2"
        if f == "HalyardDisplay-Bold" and sz >= 11.5:
            return "h3"
        if sz >= 11.5:
            return "h4"
        return "skip"  # TOC / title page
    if f.startswith("JubilatBlack"):
        if sz >= 11.5:
            return "skip"  # folio
        if "Italic" in f:
            return "boxsub"
        return "boxhead"
    if f.startswith("Jubilat"):
        if sz <= 8.5:
            return "note"
        if f in ("Jubilat-Regular", "Jubilat-Italic", "JubilatMedium-Italic") :
            return "box"
        return "body"
    return "skip"


def inline(span):
    t = html.escape(fix_ligatures(span["text"]), quote=False)
    f = span["font"]
    if not t.strip():
        return t
    lead = t[: len(t) - len(t.lstrip())]
    trail = t[len(t.rstrip()):]
    core = t.strip()
    if "Black" in f or "Bold" in f or "Semibold" in f:
        core = f"<strong>{core}</strong>"
    if "Italic" in f:
        core = f"<em>{core}</em>"
    return lead + core + trail


def line_info(line):
    counts = collections.Counter()
    for s in line["spans"]:
        counts[classify(s)] += len(s["text"].strip())
    if not counts or sum(counts.values()) == 0:
        return None
    cls = counts.most_common(1)[0][0]
    # mixed lines such as "Nina Božič Yams is a ..." (boxhead + body) are body
    if cls == "boxhead" and counts["body"]:
        cls = "body"
    if cls == "boxhead" and counts["box"]:
        cls = "box"
    text = "".join(inline(s) for s in line["spans"] if classify(s) not in ("skip",) or cls == "skip")
    x0, y0, x1, y1 = line["bbox"]
    return {"cls": cls, "html": text, "x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "color": "%06x" % line["spans"][0]["color"],
            "raw": "".join(s["text"] for s in line["spans"])}


out = []  # list of pages -> halves -> items

for pno in range(2, len(doc) - 1):  # skip cover, title page, back cover
    page = doc[pno]
    W = page.rect.width
    halves = {0: [], 1: []}
    d = page.get_text("dict")
    for bi, b in enumerate(d["blocks"]):
        if "lines" not in b:
            continue
        for line in b["lines"]:
            li = line_info(line)
            if not li or li["cls"] == "skip":
                continue
            raw = li["raw"].strip()
            if re.fullmatch(r"[{}\s\d]*", raw):
                continue  # folios and story markers
            li["block"] = (pno, bi)
            cx = (li["x0"] + li["x1"]) / 2
            h = 0 if (W < 600 or li["x0"] < W / 2 - 5) else 1
            if W >= 600 and li["x0"] >= W / 2 - 5:
                li["x0"] -= W / 2; li["x1"] -= W / 2
            halves[h].append(li)
    imgs = []
    for info in page.get_image_info(xrefs=True):
        x0, y0, x1, y1 = info["bbox"]
        x0, x1 = max(x0, 0), min(x1, W)
        y0, y1 = max(y0, 0), min(y1, page.rect.height)
        if (x1 - x0) < 20 or (y1 - y0) < 20:
            continue
        imgs.append({"xref": info["xref"], "bbox": [x0, y0, x1, y1],
                     "w": info["width"], "h": info["height"]})
    out.append({"page": pno + 1, "width": W, "halves": [halves[0], halves[1]], "images": imgs})

json.dump(out, open("content/raw.json", "w"), ensure_ascii=False, indent=0)
print("pages", len(out))
