"""Turn content/raw.json (classified lines) + content/art.json (figures) into
content/handbook.json: front matter + chapters -> sections -> blocks.

Block types: p, li (ordered/bullet), question, h3, h4, note, tip, figure,
box (kind: voices|artistic|concept|journey, with child blocks), story.
"""
import json, re, collections, html

raw = json.load(open("content/raw.json"))
art = json.load(open("content/art.json"))
curation = json.load(open("content/curation.json"))
DROP_ART = set(curation["drop_art"])

# ---------- vocabulary for de-hyphenation / ligature repair ----------
alltext = " ".join(l["raw"] for p in raw for h in p["halves"] for l in h)
alltext = re.sub(r"[ﬀ-ﬄ] ?", "fi", alltext)
words = collections.Counter(w.lower() for w in re.findall(r"[A-Za-zÀ-ž]+", alltext))
compounds = set(m.lower() for m in re.findall(r"[A-Za-zÀ-ž]+-[A-Za-zÀ-ž]+(?=[\s,.;:)”’])", alltext))
for c in curation.get("keep_hyphen", []):
    compounds.add(c)


def join_lines(a, b):
    """join line html b onto a, handling end-of-line hyphenation"""
    a = a.rstrip()
    b = b.lstrip()
    m = re.search(r"([A-Za-zÀ-ž]+)-(</\w+>)?$", a)
    if m:
        n = re.match(r"(<\w+>)?([A-Za-zÀ-ž]+)", b)
        if n:
            left, right = m.group(1), n.group(2)
            comp = (left + "-" + right).lower()
            joined = (left + right).lower()
            last_token = a.rsplit(" ", 1)[-1]
            in_url = "/" in last_token  # hyphens inside wrapped URLs are real
            keep = in_url or right[0].isupper() or (comp in compounds and words[joined] < 2)
            if keep:
                return a + b
            return a[: m.start(1) + len(left)] + (m.group(2) or "") + b
        return a + b
    return a + " " + b


def clean(h):
    h = re.sub(r"ﬁ ?", "fi", h)
    h = re.sub(r"ﬂ ?", "fl", h)
    h = re.sub(r"ﬀ ?", "ff", h)
    h = re.sub(r"ﬃ ?", "ffi", h)
    h = h.replace("­", "").replace("\t", " ")
    h = re.sub(r"</(strong|em)>(\s*)<\1>", r"\2", h)
    h = re.sub(r"\s+", " ", h).strip()
    h = re.sub(r"<(strong|em)>\s*</\1>", " ", h)
    h = re.sub(r"\s+([,.;:])", r"\1", h) if False else h
    return h.strip()


STORY_FIX = curation["story_fix"]


def repair_story(h):
    for a, b in STORY_FIX.items():
        h = h.replace(a, b)
    return h


MAIN = {"h1", "h2", "h3", "h4", "body", "box", "boxhead", "boxsub", "story", "dropcap"}
TERMINAL = tuple(".!?:”\"’)")


def text_of(h):
    return re.sub(r"<[^>]+>", "", h)


flow = []


def last_text_block():
    for b in reversed(flow):
        if b["type"] in ("note", "art"):
            continue
        return b
    return None


for p in raw:
    page_art = [a for a in art if a["page"] == p["page"] and a["name"] not in DROP_ART]
    for hi, half in enumerate(p["halves"]):
        lines = [l for l in half if l["cls"] in MAIN]
        lines.sort(key=lambda l: (round(l["y0"]), l["x0"]))
        notes_lines = [l for l in half if l["cls"] == "note"]
        notes_lines.sort(key=lambda l: (round(l["x0"] / 60), l["y0"]))
        notes = []
        for l in notes_lines:
            if notes and abs(l["x0"] - notes[-1]["x0"]) < 30 and -8 < l["y0"] - notes[-1]["y1"] < 5:
                notes[-1]["html"] = join_lines(notes[-1]["html"], l["html"])
                notes[-1]["y1"] = l["y1"]
            else:
                notes.append({"type": "note", "html": l["html"], "x0": l["x0"], "y0": l["y0"], "y1": l["y1"]})
        items = []
        prev = None
        dropcap = ""
        prev_minx = 0
        for l in lines:
            c = l["cls"]
            if c == "dropcap":
                dropcap = text_of(l["html"]).strip()
                continue
            new = True
            if prev is not None and prev["cls"] == c:
                gap = l["y0"] - prev["y1"]
                if c == "story":
                    new = gap > 4 or (l["block"] != prev["block"] and l["x0"] > prev_minx + 4)
                elif c in ("h1", "h2", "h3", "h4", "boxhead", "boxsub"):
                    new = gap > 6
                else:
                    new = gap > 4
            if new:
                blk = {"type": c, "lines": [l["html"]], "y0": l["y0"], "y1": l["y1"], "x0": l["x0"]}
                if dropcap and c == "story":
                    blk["dropcap"] = dropcap
                    dropcap = ""
                items.append(blk)
                prev_minx = l["x0"]
            else:
                items[-1]["lines"].append(l["html"])
                items[-1]["y1"] = l["y1"]
                prev_minx = min(prev_minx, l["x0"])
            prev = l
        for it in items:
            h = it["lines"][0]
            for nxt in it["lines"][1:]:
                h = join_lines(h, nxt)
            h = clean(h)
            if it.get("dropcap"):
                first = re.match(r"(<\w+>)?([A-Za-z]+)", h)
                w = first.group(2) if first else ""
                sep = "" if words[(it["dropcap"] + w).lower()] else " "
                h = it["dropcap"] + sep + h
            it["html"] = h
            del it["lines"]
        for n in notes:
            n["html"] = clean(n["html"])
        figs = []
        for a in page_art:
            if a["half"] != hi:
                continue
            x0, y0, x1, y1 = a["bbox"]
            figs.append({"type": "art", "name": a["name"], "y0": y0, "y1": y1, "x0": x0, "x1": x1,
                         "wide": a["wide"], "px": a["px"], "frac": (x1 - x0) / 510})
        for extra in notes + figs:
            pos = len(items)
            for i, it in enumerate(items):
                if it["y1"] >= extra["y0"] + 2:
                    pos = i
                    break
            extra["_pos"] = pos
        merged = []
        for i in range(len(items) + 1):
            merged += sorted([e for e in notes + figs if e["_pos"] == i], key=lambda e: e["y0"])
            if i < len(items):
                merged.append(items[i])
        for b in merged:
            b.pop("_pos", None)
            b["page"] = p["page"]
            b["half"] = hi
            if b["type"] in ("body", "box", "story"):
                lp = last_text_block()
                # stray punctuation or a sentence continuing around a figure
                if lp is not None and lp["type"] == b["type"] and (
                        re.fullmatch(r"[.,;:)]+", text_of(b["html"]).strip()) or
                        (re.match(r"[a-z]", text_of(b["html"]).strip()) and not text_of(lp["html"]).rstrip().endswith(TERMINAL))):
                    lp["html"] = clean(join_lines(lp["html"], b["html"])).replace(" .", ".")
                    continue
                if lp is not None and lp["type"] == b["type"] and (lp["page"], lp["half"]) != (p["page"], hi) and \
                        (not text_of(lp["html"]).rstrip().endswith(TERMINAL) or re.match(r"(<\w+>)?[a-z]", b["html"])) \
                        and not b.get("dropcap"):
                    lp["html"] = clean(join_lines(lp["html"], b["html"]))
                    continue
            flow.append(b)

# ---------- text patches ----------
PATCH = curation["patch"]
for b in flow:
    if "html" in b:
        if b["type"] == "story":
            b["html"] = repair_story(b["html"])
        for a, r in PATCH.items():
            b["html"] = b["html"].replace(a, r)

# ---------- URL repair + autolink inside notes ----------
TLD = r"(?:com|org|se|net|io|as|si|dk|nl|jp|eu|systems|co|edu|gov|int|info|uk|de)"
URL_RE = re.compile(r"(?<![\w@/])((?:https?://)?(?:[a-z0-9-]+\.)+" + TLD + r"(?:/[^\s<]*)?)", re.I)


def fix_urls(h):
    # glue wrapped URL fragments: "youtube.com/ watch?v=..." -> "youtube.com/watch?v=..."
    for _ in range(4):
        h = re.sub(r"((?:[a-z0-9-]+\.)+" + TLD + r"/(?:[^\s<]*[/\-_=.])?)\s+(?=[\w%?=&;#.-]+(?:[/\s<]|$))",
                   r"\1", h, flags=re.I)
    return h


def autolink(h):
    def rep(m):
        u = m.group(1).rstrip(".,;)")
        tail = m.group(1)[len(u):]
        href = html.unescape(u if u.startswith("http") else "https://" + u)
        return f'<a href="{html.escape(href)}" target="_blank" rel="noopener">{u}</a>{tail}'
    return URL_RE.sub(rep, h)


for b in flow:
    if b["type"] == "note":
        b["html"] = autolink(fix_urls(b["html"]))

# ---------- assemble ----------
def slug(s):
    s = text_of(s).lower()
    s = re.sub(r"[^a-z0-9åäöé -]+", "", s).strip()
    s = s.replace("å", "a").replace("ä", "a").replace("ö", "o").replace("é", "e")
    return re.sub(r"\s+", "-", s)[:60].strip("-")


BOX_KIND = [("voices from the field", "voices"), ("voice from the artistic field", "artistic"),
            ("journey", "journey"), ("lidingö", "journey"), ("umeå", "journey"), ("uppsala", "journey")]

book = {"front": {"credits": [], "sections": []}, "chapters": []}
chapter = None
section = None
box = None
last_kind = None


def target():
    return section["blocks"] if section is not None else None


def new_section(title_html, page):
    global section
    t = text_of(title_html).strip()
    m = re.match(r"(\d+\.\d+)\s+(.*)", t)
    num, title = (m.group(1), m.group(2)) if m else ("", t)
    section = {"num": num, "title": title, "id": slug(title) or "section", "blocks": [], "page": page}
    (chapter["sections"] if chapter else book["front"]["sections"]).append(section)


for b in flow:
    t = b["type"]
    if b["page"] == 3 and t == "note":
        book["front"]["credits"].append(b["html"])
        continue
    if t == "h2" and "Table of Contents" in b["html"]:
        continue
    if t == "h1":
        chapter = {"num": len(book["chapters"]) + 1, "title": text_of(b["html"]).strip(), "story": [],
                   "sections": [], "page": b["page"]}
        book["chapters"].append(chapter)
        section = None
        box = None
        continue
    if t == "story":
        chapter["story"].append({"html": b["html"], "dropcap": bool(b.get("dropcap"))})
        continue
    if t == "h2":
        new_section(b["html"], b["page"])
        box = None
        continue
    if section is None:
        # art on a chapter opener before the first section belongs to the story spread
        if chapter is not None and t == "art":
            chapter.setdefault("art", []).append(b)
        continue
    blocks = section["blocks"]
    if t in ("boxhead",):
        title = text_of(b["html"]).strip()
        kind = "concept"
        for k, v in BOX_KIND:
            if k in title.lower():
                kind = v
                break
        box = {"type": "box", "kind": kind, "title": title, "blocks": []}
        last_kind = kind
        blocks.append(box)
        continue
    if t in ("box", "boxsub"):
        if box is None or box not in blocks:
            # continuation of a box that started on a previous page
            box = {"type": "box", "kind": last_kind or "voices", "title": "", "blocks": []}
            blocks.append(box)
        if t == "boxsub":
            box["blocks"].append({"type": "h4", "html": text_of(b["html"]).strip()})
        else:
            box["blocks"].append({"type": "p", "html": b["html"]})
        continue
    if t in ("note", "art") and box is not None and blocks and blocks[-1] is box and not b.get("wide"):
        dest = box["blocks"]
    else:
        dest = blocks
        if t not in ("note", "art"):
            box = None
    if t == "art":
        dest.append({"type": "figure", "name": b["name"], "wide": b["wide"], "px": b["px"],
                     "frac": round(b["frac"], 2), "page": b["page"]})
        continue
    if t == "note":
        h = b["html"]
        if text_of(h).startswith("Tip"):
            dest.append({"type": "tip", "html": re.sub(r"^<em>Tip</em>:\s*", "", h)})
        else:
            dest.append({"type": "note", "html": h})
        continue
    if t == "h3":
        dest.append({"type": "h3", "html": text_of(b["html"]).strip(), "id": slug(b["html"])})
        continue
    if t == "h4":
        dest.append({"type": "h4", "html": b["html"], "id": slug(b["html"])})
        continue
    if t == "body":
        h = b["html"]
        m = re.match(r"^(\d+)\.\s+(.*)$", h)
        if m and "question" in section["title"].lower():
            dest.append({"type": "question", "n": int(m.group(1)), "html": m.group(2)})
            continue
        if m:
            dest.append({"type": "li", "list": "ol", "n": int(m.group(1)), "html": m.group(2)})
            continue
        m = re.match(r"^([a-h])\.\s+(.*)$", h)
        if m:
            dest.append({"type": "li", "list": "ol-alpha", "n": ord(m.group(1)) - 96, "html": m.group(2)})
            continue
        if h.startswith("• "):
            dest.append({"type": "li", "list": "ul", "html": h[2:]})
            continue
        # inline bullets inside a paragraph
        if " • " in h:
            head, *rest = h.split(" • ")
            dest.append({"type": "p", "html": head})
            for r in rest:
                dest.append({"type": "li", "list": "ul", "html": r})
            continue
        dest.append({"type": "p", "html": h})
        continue

# ---------- captions: attach a short note that sits right next to a figure ----------
def attach_captions(blocks):
    for i, b in enumerate(blocks):
        if b["type"] == "box":
            attach_captions(b["blocks"])
    i = 0
    while i < len(blocks):
        b = blocks[i]
        if b["type"] == "figure" and "caption" not in b:
            for j in (i + 1, i - 1, i + 2):
                if 0 <= j < len(blocks) and blocks[j]["type"] == "note":
                    txt = text_of(blocks[j]["html"])
                    if len(txt) < 220 and "http" not in blocks[j]["html"] and not txt.startswith(("*", "To learn", "To find", "Learn more", "For ")):
                        b["caption"] = blocks[j]["html"]
                        blocks.pop(j)
                        if j < i:
                            i -= 1
                        break
        i += 1


for ch in book["chapters"]:
    for s in ch["sections"]:
        attach_captions(s["blocks"])
for s in book["front"]["sections"]:
    attach_captions(s["blocks"])

# unique ids per chapter
for ch in [{"sections": book["front"]["sections"]}] + book["chapters"]:
    seen = collections.Counter()
    for s in ch["sections"]:
        seen[s["id"]] += 1
        if seen[s["id"]] > 1:
            s["id"] += f"-{seen[s['id']]}"

json.dump(book, open("content/handbook.json", "w"), ensure_ascii=False, indent=1)

# review dump
with open("content/review.txt", "w") as f:
    def dump(blocks, ind=""):
        for b in blocks:
            if b["type"] == "box":
                f.write(f"{ind}BOX[{b['kind']}] {b['title']}\n")
                dump(b["blocks"], ind + "    ")
            elif b["type"] == "figure":
                f.write(f"{ind}FIG {b['name']} wide={b['wide']} frac={b['frac']} cap={text_of(b.get('caption',''))[:60]}\n")
            else:
                f.write(f"{ind}{b['type'].upper()}: {text_of(b.get('html',''))}\n")
    for s in book["front"]["sections"]:
        f.write(f"\n## {s['title']}\n")
        dump(s["blocks"])
    for ch in book["chapters"]:
        f.write(f"\n\n# CHAPTER {ch['num']}: {ch['title']}\n")
        for st in ch["story"]:
            f.write(f"STORY: {text_of(st['html'])}\n")
        for s in ch["sections"]:
            f.write(f"\n## {s['num']} {s['title']}  #{s['id']}\n")
            dump(s["blocks"])
print("chapters", len(book["chapters"]), "sections", sum(len(c["sections"]) for c in book["chapters"]))
