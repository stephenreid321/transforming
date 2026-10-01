"""Generate the static website from content/handbook.json.

    python3 tools/build.py

Outputs index.html, introduction.html, chapter-N.html, practices.html,
voices.html, elena.html, journal.html and assets/search-index.js in the repo root.
"""
import html
import json
import re

book = json.load(open("content/handbook.json"))
curation = json.load(open("content/curation.json"))
SITE_TITLE = "Transforming how we lead together"
PDF = "Transforming%20how%20we%20lead%20together.pdf"
PDF_SIZE = "71 MB"

# ---------- colours ----------
PALETTE = {
    0: ("4f0e64", "e9d1e5"),
    1: ("4f0e64", "e9d1e5"),
    2: ("232176", "e2d9ed"),
    3: ("004b1c", "d3eadf"),
    4: ("005e5a", "dfeac6"),
    5: ("5c5349", "f1f3c2"),
    6: ("700044", "d8cdd6"),
}


def mix(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def colours(n):
    ink, paper = PALETTE[n]
    return {"ink": "#" + ink, "paper": "#" + paper,
            "ink_d": "#" + mix(paper, "ffffff", .15) if n != 5 else "#" + mix(paper, "ffffff", .05),
            "paper_d": "#" + mix(ink, "0e0b10", .80)}


def cvars(n, prefix="c-"):
    c = colours(n)
    return f"--{prefix}ink:{c['ink']};--{prefix}paper:{c['paper']};--{prefix}ink-d:{c['ink_d']};--{prefix}paper-d:{c['paper_d']}"


def root_vars(n):
    c = colours(n)
    return (f":root{{--ink:{c['ink']};--paper:{c['paper']};--ink-d:{c['ink_d']};--paper-d:{c['paper_d']};"
            f"--ink-l:{c['ink']};--paper-l:{c['paper']}}}")


# ---------- helpers ----------
def text_of(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h or ""))


def esc(s):
    return html.escape(s, quote=True)


def words(h):
    return len(text_of(h).split())


def slug(s):
    s = text_of(s).lower()
    s = s.replace("å", "a").replace("ä", "a").replace("ö", "o").replace("é", "e")
    s = re.sub(r"[^a-z0-9 -]+", "", s).strip()
    return re.sub(r"[\s-]+", "-", s)[:60].strip("-") or "s"


ICON = {
    "search": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    "moon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h10"/></svg>',
    "down": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>',
    "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    "file": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11m0 0 4.5-4.5M12 15l-4.5-4.5M5 20h14"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14m-5-5 5 5-5 5"/></svg>',
    "pen": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16v4z"/></svg>',
    "play": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15l13-7.5z"/></svg>',
    "x": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>',
    "layers": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="m12 3 9 5-9 5-9-5 9-5z"/><path d="m3 13 9 5 9-5"/></svg>',
    "quote": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 18v-5.5C4 8.4 6.3 5.7 10 5l.6 1.6C8.2 7.4 7.3 9 7.2 11H10v7H4zm10 0v-5.5c0-4.1 2.3-6.8 6-7.5l.6 1.6c-2.4.8-3.3 2.4-3.4 4.4H20v7h-6z"/></svg>',
    "move": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13" cy="4" r="2"/><path d="m9 20 3-6 3 2v5M6 12l3-4 4 1 3 3 3 1"/></svg>',
    "book": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2V5z"/><path d="M4 19a2 2 0 0 1 2-2h13"/></svg>',
}

ICON_SVG_READERS = [
    '<svg class="ico" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M8 38c6-14 12-20 32-28"/><path d="M30 9l10 1-3 9"/><circle cx="12" cy="14" r="4"/></svg>',
    '<svg class="ico" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="10" width="32" height="26" rx="4"/><path d="M16 22h16M16 28h10M24 36v6M16 42h16"/></svg>',
    '<svg class="ico" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="24" cy="20" r="11"/><path d="M24 31v4M20 42h8M19 16a6 6 0 0 1 9-2"/></svg>',
]

ART = {a["name"]: a for a in json.load(open("content/art.json"))}
FUNDER_LOGOS = [(n, "%d/%d" % tuple(ART[n]["px"])) for n in ("p3-3", "p3-4", "p3-5")]
SPEAKERS = ["Mette Aagaard", "Karin Tenelius", "Nati Lombardo", "Dejan Srhoj"]
SPEAKER_SHORT = {"Mette Aagaard": "Mette", "Karin Tenelius": "Karin", "Nati Lombardo": "Nati", "Dejan Srhoj": "Dejan"}

PHOTOS = set(curation["photos"])
PRACTICE_RE = re.compile(curation["practice_regex"], re.I)
PRACTICE_SKIP = set(curation["practice_skip"])

# ---------- page shell ----------
def chapter_menu():
    items = [f'<a class="intro" href="introduction.html" style="{cvars(0)}"><span class="n">i</span><span>Introduction</span></a>']
    for ch in book["chapters"]:
        items.append(f'<a href="chapter-{ch["num"]}.html" style="{cvars(ch["num"])}"><span class="n">{ch["num"]}</span><span>{esc(ch["title"])}</span></a>')
    return "".join(items)


def shell(title, body, *, n=0, desc="", current="", chapter_key="", head_extra="", progress=False):
    full = f"{title} · {SITE_TITLE}" if title else f"{SITE_TITLE}: moving from hierarchies towards co-creation"
    desc = desc or "A handbook for resilient and sustainable organisations and society: practices, stories and reflections for moving from hierarchies towards co-creation."

    def cur(k):
        return ' aria-current="page"' if current == k else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(full)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="book">
<meta property="og:image" content="assets/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="{colours(n)['paper']}">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="assets/fonts/bitter-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/fonts/hanken-grotesk-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/fonts.css">
<link rel="stylesheet" href="assets/style.css">
<style>{root_vars(n)}</style>
<script>try{{var t=JSON.parse(localStorage.getItem("theme"));if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
{head_extra}
</head>
<body data-chapter="{chapter_key}">
<a class="skip" href="#main">Skip to content</a>
{'<div class="progress" aria-hidden="true"></div>' if progress else ''}
<header class="topbar">
  <a class="brand" href="index.html" aria-label="Home: {esc(SITE_TITLE)}"><svg class="brand-mark" viewBox="0 0 40 38" aria-hidden="true"><circle class="c1" cx="20" cy="13" r="10"/><circle class="c2" cx="13" cy="25" r="10"/><circle class="c3" cx="27" cy="25" r="10"/></svg><span>Leading together<small>Web edition of the 2026 handbook</small></span></a>
  <button class="icon-btn search-btn" aria-label="Search the handbook">{ICON['search']}<kbd>/</kbd></button>
  <nav class="nav" aria-label="Main">
    <div class="chapters-menu">
      <button aria-expanded="false" aria-haspopup="true"{cur('chapters')}>Chapters {ICON['down']}</button>
      <div class="chapters-pop">{chapter_menu()}</div>
    </div>
    <a href="practices.html"{cur('practices')}>Practices</a>
    <a href="voices.html"{cur('voices')}>Voices</a>
    <a href="elena.html"{cur('elena')}>Elena’s story</a>
    <a href="journal.html"{cur('journal')}>Journal</a>
    <button class="icon-btn" id="theme-btn" aria-label="Toggle dark mode">{ICON['moon']}</button>
  </nav>
  <button class="icon-btn menu-btn" aria-label="Menu" aria-expanded="false">{ICON['menu']}</button>
</header>
<div class="scrim"></div>
<main id="main">
{body}
</main>
{footer()}
<div class="search" role="dialog" aria-modal="true" aria-label="Search">
  <div class="search-panel">
    <label class="search-field">{ICON['search']}<span class="sr-only">Search</span><input type="search" placeholder="Search practices, voices, ideas…" autocomplete="off"><kbd>esc</kbd></label>
    <div class="search-results" role="listbox" data-hints='{SEARCH_HINTS}'></div>
  </div>
</div>
<div class="lightbox" role="dialog" aria-label="Image"><div class="ink-img"></div><p></p></div>
<div class="timer" role="timer" aria-live="off">
  <svg class="ring" viewBox="0 0 50 50"><circle class="bg" cx="25" cy="25" r="22"/><circle class="fg" cx="25" cy="25" r="22"/></svg>
  <div><div class="t">0:00</div><div class="lbl"></div></div>
  <button class="pause" aria-label="Pause"></button>
  <button class="close" aria-label="Stop timer">{ICON['x']}</button>
</div>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><filter id="rough"><feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="2" seed="7"/><feDisplacementMap in="SourceGraphic" scale="7"/></filter></svg>
<script src="assets/app.js" defer></script>
</body>
</html>
"""


SEARCH_HINTS = esc('<div class="search-hints">' + "".join(
    f'<button class="chip" data-q="{q}">{q}</button>' for q in
    ["psychological safety", "consent", "self-leadership", "feedback", "power", "movement score", "Buurtzorg", "Lidingö"]) + "</div>")


def footer():
    chapters = "".join(f'<li><a href="chapter-{c["num"]}.html">{c["num"]}. {esc(c["title"])}</a></li>' for c in book["chapters"])
    return f"""<footer class="footer">
  <div class="wrap cols">
    <div>
      <h4>About this handbook</h4>
      <p>Nina Božič Yams, Laura Gottlieb and Álvaro Aranda Muñoz. Published as an outcome of two research projects led by RISE Research Institutes of Sweden, funded by AFA Försäkring and Forte. Stockholm, 2026.</p>
      <p>Licensed under <a href="https://creativecommons.org/licenses/by/4.0/" rel="license">Creative Commons Attribution (CC BY 4.0)</a>. Graphic design &amp; lettering by Fredrik Andersson Nygren.</p>
      <p><a class="btn ghost" href="{PDF}" download>{ICON['file']} Download the PDF ({PDF_SIZE})</a></p>
      <div class="funders" aria-label="RISE, AFA Försäkring and Forte">{''.join(f'<div class="ink-img" data-src="assets/art/{n}.webp" style="aspect-ratio:{r}"></div>' for n, r in FUNDER_LOGOS)}</div>
    </div>
    <div><h4>Read</h4><ul><li><a href="introduction.html">Introduction</a></li>{chapters}</ul></div>
    <div><h4>Explore</h4><ul><li><a href="practices.html">Practice library</a></li><li><a href="voices.html">Voices from the field</a></li><li><a href="elena.html">Elena’s story</a></li><li><a href="journal.html">Reflection journal</a></li></ul></div>
  </div>
</footer>"""


# ---------- block rendering ----------
class Ctx:
    def __init__(self, page, n):
        self.page = page
        self.n = n
        self.ids = set()
        self.tid = 0
        self.search = []
        self.section = None
        self.anchor = None
        self.boxes = []
        self.practices = []
        self.questions = []

    def uid(self, base):
        base = base or "s"
        i, cand = 1, base
        while cand in self.ids:
            i += 1
            cand = f"{base}-{i}"
        self.ids.add(cand)
        return cand

    def index(self, h, kind="p"):
        txt = text_of(h).strip()
        if len(txt) < 3:
            return ""
        self.tid += 1
        pid = f"t{self.tid}"
        where = "Introduction" if self.n == 0 else f"Chapter {self.n}"
        self.search.append({"k": kind, "t": self.section["title"] if self.section else "", "w": where,
                            "u": f"{self.page}#{pid}", "x": txt, "c": colours(self.n)["ink"]})
        return f' id="{pid}"'


def figure(b, in_box=False):
    w, h = b["px"]
    src = f"assets/art/{b['name']}.webp"
    frac = b["frac"]
    if b.get("wide"):
        cls = "fig--interlude" if not in_box else ""
    elif frac >= 0.72:
        cls = ""
    elif frac >= 0.38:
        cls = "fig--medium"
    else:
        cls = "fig--small"
    if b["name"] in PHOTOS:
        cls += " fig--photo"
    zoom = " zoomable" if (frac >= 0.38 or b.get("wide")) and w * h > 250000 else ""
    cap = f'<figcaption>{b["caption"]}</figcaption>' if b.get("caption") else ""
    alt = esc(text_of(b.get("caption", ""))) or ""
    img = (f'<div class="ink-img" role="img" aria-label="{alt or ("Photo" if b["name"] in PHOTOS else "Illustration")}" '
           f'data-src="{src}" style="aspect-ratio:{w}/{h}"></div>')
    if b["name"] in PHOTOS:
        img = f'<div class="frame">{img}</div>'
    return f'<figure class="fig {cls}{zoom}">{img}{cap}</figure>'



def speakerise(h):
    for s in SPEAKERS:
        if s in h:
            return h.replace(s, f'<span class="speaker">{s}</span>', 1)
    return h


def heading_practice(title_html, ctx, level, blocks, i):
    t = text_of(title_html)
    clean_title = re.sub(r"\s*\(\s*\d+\s*min\s*\)\s*$", "", t).strip().rstrip(":")
    hid = ctx.uid(slug(clean_title))
    mins = re.search(r"\((\d+)\s*min\)", t)
    is_practice = bool(PRACTICE_RE.search(t)) and clean_title not in PRACTICE_SKIP
    out = ""
    if is_practice:
        kind = "Movement score" if t.lower().startswith("movement score") else "Practice"
        out += f'<div class="practice-mark">{ICON["move"] if kind == "Movement score" else ICON["layers"]} {kind}</div>'.replace("<svg ", '<svg width="14" height="14" ')
        # gather following text for the library card
        follow = []
        for nb in blocks[i + 1:i + 8]:
            if nb["type"] in ("h2", "h3") or (nb["type"] == "h4" and PRACTICE_RE.search(text_of(nb["html"]))):
                break
            if nb["type"] in ("p", "li"):
                follow.append(text_of(nb["html"]))
        body = " ".join(follow)
        team = re.search(r"\b(team|group|participants|colleagues|everyone|circle)\b", body, re.I)
        tags = ["movement"] if kind == "Movement score" else []
        tags.append("team" if team else "individual")
        short = clean_title.replace("Movement score: ", "").replace("Practice: ", "")
        tags = curation["practice_tags"].get(short, tags)
        short = curation["practice_titles"].get(short, short)
        ctx.practices.append({"title": short[:1].upper() + short[1:], "kind": kind,
                              "id": hid, "mins": int(mins.group(1)) if mins else None, "excerpt": body[:400],
                              "tags": tags, "section": ctx.section["title"] if ctx.section else ""})
    tag = f"h{level}"
    inner = title_html if level == 4 else esc(t)
    out += f'<{tag} id="{hid}">{inner}<a class="anchor" href="#{hid}" aria-label="Copy link to this heading">#</a></{tag}>'
    if mins:
        out += (f'<button class="timer-btn" data-minutes="{mins.group(1)}" data-label="{esc(clean_title)}">'
                f'{ICON["play"]} Start a {mins.group(1)}-minute timer</button>')
    return out


def render_blocks(blocks, ctx, in_box=False):
    out = []
    i = 0
    while i < len(blocks):
        b = blocks[i]
        t = b["type"]
        if t == "p":
            h = speakerise(b["html"]) if in_box else b["html"]
            out.append(f"<p{ctx.index(h)}>{h}</p>")
        elif t == "li":
            kind = b["list"]
            items = []
            start = b.get("n", 1)
            while i < len(blocks) and blocks[i]["type"] == "li" and blocks[i]["list"] == kind:
                items.append(f"<li{ctx.index(blocks[i]['html'])}>{blocks[i]['html']}</li>")
                i += 1
            i -= 1
            if kind == "ul":
                out.append("<ul>" + "".join(items) + "</ul>")
            else:
                cls = ' class="alpha"' if kind == "ol-alpha" else ""
                st = f' start="{start}"' if start != 1 else ""
                out.append(f"<ol{cls}{st}>" + "".join(items) + "</ol>")
        elif t == "question":
            items = []
            while i < len(blocks) and blocks[i]["type"] == "question":
                q = blocks[i]
                qid = f"ch{ctx.n}-q{q['n']}"
                ctx.questions.append({"id": qid, "html": q["html"]})
                items.append(question_html(qid, q["html"], ctx.index(q["html"], "question")))
                i += 1
            i -= 1
            out.append('<ol class="questions">' + "".join(items) + "</ol>")
            out.append(f'<div class="journal-cta"><span>Your reflections are saved privately in this browser. Collect them all in your journal.</span>'
                       f'<a class="btn ghost" href="journal.html#chapter-{ctx.n}">{ICON["pen"]} Open journal</a></div>')
        elif t == "h3":
            out.append(heading_practice(b["html"], ctx, 3, blocks, i))
        elif t == "h4":
            out.append(heading_practice(b["html"], ctx, 4, blocks, i))
        elif t == "note":
            out.append(f'<aside class="note">{b["html"]}</aside>')
        elif t == "tip":
            out.append(f'<aside class="tip"><b>Tip</b>{b["html"]}</aside>')
        elif t == "figure":
            out.append(figure(b, in_box))
        elif t == "box":
            out.append(render_box(b, ctx))
        i += 1
    return "\n".join(out)


def question_html(qid, h, idattr=""):
    return (f'<li class="q" data-qid="{qid}"{idattr}><p>{h}</p><div class="q-actions">'
            f'<button class="reflect" aria-expanded="false">{ICON["pen"].replace("<svg ", "<svg width=14 height=14 ")}<span>Write a reflection</span></button>'
            f'<span class="saved" aria-live="polite"></span></div>'
            f'<textarea hidden aria-label="Your reflection" placeholder="What comes up for you? Write freely, nothing leaves this device."></textarea></li>')


def journey_title(t):
    t = t.strip()
    m = re.match(r"^([A-ZÅÄÖ’' ]+?)(’S JOURNEY|:)(.*)$", t)
    fixed = curation["journey_titles"].get(t)
    return fixed or t


def render_box(b, ctx):
    kind = b["kind"]
    bid = ctx.uid(f"{kind}-{len(ctx.boxes) + 1}")
    if kind == "journey":
        title = journey_title(b["title"])
        subs = [x["html"] for x in b["blocks"] if x["type"] == "h4"]
        chips = "".join(f"<span>{esc(s)}</span>" for s in subs[:5])
        inner = []
        for x in b["blocks"]:
            if x["type"] == "h4":
                inner.append(f"<h4>{esc(x['html'])}</h4>")
            else:
                inner.append(render_blocks([x], ctx, True))
        prev_section = ctx.section
        return (f'<details class="journey" id="{bid}"><summary><span class="k">Case journey</span><h3>{esc(title)}</h3>'
                f'<span class="plus" aria-hidden="true">+</span><div class="chips">{chips}</div></summary>'
                f'<div class="jbody">{"".join(inner)}</div></details>')
    label = {"voices": "Voices from the field", "artistic": "Voice from the artistic field"}.get(kind, b["title"])
    icon = ICON["quote"] if kind in ("voices", "artistic") else ICON["layers"]
    body = render_blocks(b["blocks"], ctx, True)
    speakers = [SPEAKER_SHORT[s] for s in SPEAKERS if any(s in x.get("html", "") for x in b["blocks"])]
    if kind == "artistic" and "Dejan" not in speakers:
        speakers.append("Dejan")
    ctx.boxes.append({"id": bid, "kind": kind, "speakers": speakers, "html": body,
                      "section": ctx.section["title"] if ctx.section else "", "label": label})
    return f'<aside class="box box--{kind}" id="{bid}"><div class="box-label">{icon} {esc(label)}</div>{body}</aside>'


def render_story(story, collapsible=True, n=1):
    paras = []
    after_break = False
    first = True
    for st in story:
        h = st["html"]
        if text_of(h).strip() == "*":
            paras.append('<p class="brk" aria-hidden="true">* * *</p>')
            after_break = True
            continue
        cls = []
        if first:
            cls.append("first")
            m = re.match(r"^(<\w+>)?([A-Za-zÀ-ž“”\"])", h)
            if m:
                h = h[:m.start(2)] + f'<span class="drop">{m.group(2)}</span>' + h[m.end(2):]
            first = False
        elif after_break:
            cls.append("after-break")
        after_break = False
        c = f' class="{" ".join(cls)}"' if cls else ""
        paras.append(f"<p{c}>{h}</p>")
    more = '<button class="more">Continue Elena’s story ↓</button>' if collapsible else ""
    foot = (f'<div class="elena-foot"><a href="elena.html#chapter-{n}">follow elena through the handbook</a></div>' if collapsible
            else '<div class="elena-foot"><span>✳</span></div>')
    return (f'<article class="elena{" collapsible" if collapsible else ""}" style="--c-ink:{colours(n)["ink"]}" aria-label="Elena’s story">'
            f'<div class="elena-head">{{elena’s story}}</div><div class="elena-body">{"".join(paras)}</div>{more}{foot}</article>')


def count_words_blocks(blocks):
    n = 0
    for b in blocks:
        if b["type"] == "box":
            n += count_words_blocks(b["blocks"])
        elif "html" in b:
            n += words(b["html"])
    return n


def reading_minutes(ch):
    n = sum(words(s["html"]) for s in ch.get("story", []))
    for s in ch["sections"]:
        n += count_words_blocks(s["blocks"])
    return max(1, round(n / 220))


# ---------- chapters ----------
search_index = []
all_practices = []
all_voices = []
all_questions = []


def toc_html(sections, ctx_ids):
    items = []
    for s, sid, subs in ctx_ids:
        num = f"<b>{s['num']}</b>" if s["num"] else ""
        items.append(f'<li><a href="#{sid}">{num}{esc(s["title"])}</a></li>')
    return "<ol>" + "".join(items) + "</ol>"


def render_sections(sections, ctx):
    out = []
    toc = []
    for s in sections:
        ctx.section = s
        sid = ctx.uid(s["id"])
        num = f'<span class="num">{s["num"]}</span>' if s["num"] else ""
        body = render_blocks(s["blocks"], ctx)
        ctx.search.append({"k": "section", "t": s["title"], "w": "Introduction" if ctx.n == 0 else f"Chapter {ctx.n}",
                           "u": f"{ctx.page}#{sid}", "x": text_of(body)[:260], "c": colours(ctx.n)["ink"]})
        out.append(f'<section class="sec" id="{sid}"><h2>{num}{esc(s["title"])}<a class="anchor" href="#{sid}" aria-label="Copy link to this section">#</a></h2>\n{body}\n</section>')
        toc.append((s, sid, []))
    return "\n".join(out), toc


def pager(prev, nxt):
    def card(item, cls, label):
        if not item:
            return ""
        href, n, title = item
        return f'<a class="{cls}" href="{href}" style="{cvars(n)}"><span class="k">{label}</span><b>{esc(title)}</b></a>'
    return f'<nav class="pager" aria-label="Chapters">{card(prev, "prev", "← Previous")}{card(nxt, "next", "Next →")}</nav>'


def chapter_page(ch):
    n = ch["num"]
    page = f"chapter-{n}.html"
    ctx = Ctx(page, n)
    sections_html, toc = render_sections(ch["sections"], ctx)
    mins = reading_minutes(ch)
    nprac = len(ctx.practices)
    jump = "".join(f'<a href="#{sid}"><b>{s["num"]}</b>{esc(s["title"])}</a>' for s, sid, _ in toc
                   if not re.search(r"questions for reflection|conclusions", s["title"], re.I))
    hero = f"""<header class="ch-hero">
  <div class="photo"><div class="ink-img" data-src="assets/hero/chapter-{n}.webp" role="img" aria-label="Chapter {n} opening artwork" style="height:100%;-webkit-mask-size:cover;mask-size:cover;-webkit-mask-position:left center;mask-position:left center"></div></div>
  <div class="titles">
    <span class="kicker">Chapter {n}</span>
    <h1>{esc(ch['title'])}</h1>
    <div class="meta"><span>{ICON['clock']} {mins} min read</span><span>{ICON['layers']} {len(toc)} sections</span>{f"<span>{ICON['move']} {nprac} practices</span>" if nprac else ""}</div>
    <nav class="jump" aria-label="Sections in this chapter">{jump}</nav>
  </div>
</header>"""
    story = render_story(ch["story"], True, n) if ch["story"] else ""
    prev = ("introduction.html", 0, "Introduction") if n == 1 else (f"chapter-{n - 1}.html", n - 1, book["chapters"][n - 2]["title"])
    nxt = (f"chapter-{n + 1}.html", n + 1, book["chapters"][n]["title"]) if n < len(book["chapters"]) else None
    mobile = "".join(f'<li><a href="#{sid}"><b>{s["num"]}</b>{esc(s["title"])}</a></li>' for s, sid, _ in toc)
    body = f"""{hero}
{story}
<div class="reader-layout">
  <aside class="toc" aria-label="In this chapter"><h2>In this chapter</h2>{toc_html(ch['sections'], toc)}
    <div class="tools"><a href="journal.html#chapter-{n}">{ICON['pen'].replace('<svg ', '<svg width=14 height=14 ')} Reflection journal</a><a href="practices.html">{ICON['layers'].replace('<svg ', '<svg width=14 height=14 ')} All practices</a></div>
  </aside>
  <article class="prose">
{sections_html}
  </article>
</div>
<div class="mobile-toc"><button aria-label="Sections in this chapter">{ICON['menu'].replace('<svg ', '<svg width=16 height=16 ')}<span>Chapter {n} · Sections</span></button><nav class="sheet"><ol>{mobile}</ol></nav></div>
{pager(prev, nxt)}"""
    search_index.extend(ctx.search)
    for p in ctx.practices:
        p.update({"ch": n, "url": f"{page}#{p['id']}"})
    all_practices.extend(ctx.practices)
    for v in ctx.boxes:
        if v["kind"] in ("voices", "artistic"):
            v.update({"ch": n, "url": f"{page}#{v['id']}"})
            all_voices.append(v)
    all_questions.append((n, ch["title"], ctx.questions))
    desc = text_of(ch["sections"][0]["blocks"][0].get("html", ""))[:180] if ch["sections"] and ch["sections"][0]["blocks"] else ""
    return shell(f"Chapter {n}: {ch['title']}", body, n=n, current="chapters", chapter_key=f"chapter-{n}", progress=True, desc=desc)


def intro_page():
    order = curation["intro_order"]
    secs = sorted(book["front"]["sections"], key=lambda s: order.index(s["title"]) if s["title"] in order else 99)
    ctx = Ctx("introduction.html", 0)
    sections_html, toc = render_sections(secs, ctx)
    credits = "".join(f"<p>{c}</p>" for c in book["front"]["credits"])
    mobile = "".join(f'<li><a href="#{sid}">{esc(s["title"])}</a></li>' for s, sid, _ in toc)
    body = f"""<header class="page-hero wrap"><span class="kicker">Introduction</span><h1>A companion for a journey</h1>
<p>Where this handbook comes from, who it is for, and how to find your way through its practices, voices and stories.</p></header>
<div class="reader-layout" style="margin-top:1rem">
  <aside class="toc" aria-label="In the introduction"><h2>Introduction</h2>{toc_html(secs, toc)}</aside>
  <article class="prose">
{sections_html}
<section class="sec" id="credits"><h2>Credits</h2><div class="note" style="float:none;width:auto;margin:0;border:0;padding:0;background:none;font-size:.9rem">{credits}</div></section>
  </article>
</div>
<div class="mobile-toc"><button>{ICON['menu'].replace('<svg ', '<svg width=16 height=16 ')}<span>Introduction · Sections</span></button><nav class="sheet"><ol>{mobile}</ol></nav></div>
{pager(None, ("chapter-1.html", 1, book["chapters"][0]["title"]))}"""
    search_index.extend(ctx.search)
    return shell("Introduction", body, n=0, current="chapters", chapter_key="introduction", progress=True)


# ---------- home ----------
def home_page():
    cards = [f'''<a class="ch-card intro-card reveal" href="introduction.html" style="{cvars(0)}">
  <div class="num">Introduction</div>
  <div class="body"><span class="kicker">Start here</span><h3>Where this handbook comes from, who it is for and how to use it</h3>
  <div class="meta"><span>{reading_minutes({"sections": book["front"]["sections"]})} min read</span><span class="pct"></span></div>
  <div class="bar" data-progress="introduction"><i></i></div></div></a>''']
    for ch in book["chapters"]:
        n = ch["num"]
        cards.append(f'''<a class="ch-card reveal" href="chapter-{n}.html" style="{cvars(n)}">
  <div class="art"><div class="ink-img" data-src="assets/hero/chapter-{n}.webp"></div></div>
  <div class="num">{n}</div>
  <div class="body"><span class="kicker">Chapter {n}</span><h3>{esc(ch["title"])}</h3>
  <div class="meta"><span>{reading_minutes(ch)} min read</span><span>{len(ch["sections"])} sections</span><span class="pct"></span></div>
  <div class="bar" data-progress="chapter-{n}"><i></i></div></div></a>''')
    n_prac = len(all_practices)
    n_voice = len(all_voices)
    n_q = sum(len(q) for _, _, q in all_questions)
    quote_art = curation["home_quote_art"]
    people = curation["home_people"]
    people_html = "".join(
        f'<div class="person"><div class="face"><div class="ink-img" data-src="assets/art/{p["art"]}.webp"></div></div><div><b>{esc(p["name"])}</b><span>{esc(p["role"])}</span></div></div>'
        for p in people)
    readers = curation["home_readers"]
    readers_html = "".join(
        f'<div class="reader reveal">{ICON_SVG_READERS[i]}<h3>{esc(r["title"])}</h3><p>{esc(r["text"])}</p></div>'
        for i, r in enumerate(readers))
    body = f"""<section class="cover" aria-labelledby="cover-title">
  <h1 class="cover-title" id="cover-title" aria-label="Transforming how we lead together: moving from hierarchies towards co-creation">
    <span class="l" aria-hidden="true">Transf<i class="cap"></i></span>
    <span class="l" aria-hidden="true"><i class="cap c2"></i>rming how</span>
    <span class="l" aria-hidden="true">we lead together:</span>
    <span class="l" aria-hidden="true">m<i class="cap c3"></i>ving</span>
    <span class="l" aria-hidden="true">from hierarchies</span>
    <span class="l" aria-hidden="true">t<i class="cap c4"></i>wards</span>
    <span class="l" aria-hidden="true">co-creation<span class="cover-tag">For Resilient<br>and Sustainable<br>Organisations<br>and Society</span></span>
  </h1>
  <div class="cover-foot">
    <p class="cover-sub"><strong>A handbook</strong> of practices, stories and reflections for public sector teams moving from hierarchies towards trust, participation and leading together.<br><span style="opacity:.85">Nina Božič Yams, Laura Gottlieb &amp; Álvaro Aranda Muñoz</span></p>
    <div class="btns"><a class="btn" href="introduction.html">Start reading {ICON['arrow']}</a><a class="btn ghost" href="{PDF}" download>{ICON['file']} PDF</a></div>
  </div>
</section>

<section class="home-section wrap video-band" aria-labelledby="video-title">
  <div class="video-head reveal"><span class="kicker">The handbook in two minutes</span>
    <h2 id="video-title" class="lede" style="font-family:var(--sans);font-weight:700;letter-spacing:-.03em;margin-top:.6rem">Why leading together, what is inside, and how to use this site.</h2></div>
  <div class="video-frame reveal">
    <video controls preload="none" playsinline poster="assets/video/explainer-poster.jpg">
      <source src="assets/video/explainer.mp4" type="video/mp4">
      <source src="assets/video/explainer.webm" type="video/webm">
      <track kind="captions" src="assets/video/explainer.vtt" srclang="en" label="English">
    </video>
    <button class="video-play" aria-label="Play the two-minute explainer video">{ICON['play']}<span>Play · 2 min</span></button>
  </div>
</section>

<section class="home-section wrap">
  <div class="split">
    <div class="reveal">
      <span class="kicker">Why this handbook</span>
      <p class="lede">Swedish public institutions name <em>self-leadership</em> and <em>trust-based leadership</em> as priorities, yet the gap between policy and daily work remains wide. This handbook grew out of four years of participatory research with municipalities and agencies, exploring how we can <em>lead more together</em>.</p>
    </div>
    <div class="reveal"><div class="ink-img" data-src="assets/art/{quote_art}.webp" role="img" aria-label="Hand lettering: We do not exist on our own, but we exist as relational beings to other humans, living beings and objects." style="aspect-ratio:{curation['home_quote_ratio']}"></div></div>
  </div>
  <div class="readers">{readers_html}</div>
</section>

<section class="home-section wrap" id="chapters" style="padding-top:0">
  <span class="kicker">The journey</span>
  <h2 class="lede" style="font-family:var(--sans);font-weight:700;letter-spacing:-.03em;margin-top:.6rem">Six chapters, from the cracks in today’s systems to designing your own transformation.</h2>
  <div class="ch-cards">{''.join(cards)}</div>
</section>

<section class="home-section wrap" style="padding-top:0">
  <span class="kicker">Ways in</span>
  <h2 class="lede" style="font-family:var(--sans);font-weight:700;letter-spacing:-.03em;margin-top:.6rem">Read it start to finish, or follow a thread.</h2>
  <div class="ways">
    <a class="way reveal" href="practices.html"><span class="big">{n_prac}</span><h3>Practice library</h3><p>Tried-and-tested exercises, from five-minute reflections to movement scores and consent-based decision-making.</p><span class="go">Browse practices →</span></a>
    <a class="way reveal" href="voices.html"><span class="big">{n_voice}</span><h3>Voices from the field</h3><p>Excerpts from conversations with Mette Aagaard, Karin Tenelius, Nati Lombardo and choreographer Dejan Srhoj.</p><span class="go">Listen in →</span></a>
    <a class="way reveal" href="elena.html"><span class="big">6</span><h3>Elena’s story</h3><p>A fictional manager in elderly care, trying to lead differently inside a system full of barriers. Told across six chapters.</p><span class="go">Follow Elena →</span></a>
    <a class="way reveal" href="journal.html"><span class="big">{n_q}</span><h3>Reflection journal</h3><p>Questions for reflection from every chapter, with space to write. Your answers stay in your browser.</p><span class="go">Start reflecting →</span></a>
  </div>
</section>

<section class="home-section wrap" style="padding-top:0">
  <div class="split" style="align-items:start">
    <div class="reveal">
      <span class="kicker">How it was made</span>
      <p class="lede" style="font-size:clamp(1.15rem,2vw,1.5rem)">Participatory action research with Lidingö, Umeå, Eskilstuna and Uppsala municipalities, the Swedish Police, the Swedish Transport Administration, the Swedish National Grid, Formas and RISE. Workshops combined theory with choreography, Photovoice, poetry and design, in museums and galleries rather than conference rooms.</p>
      <p style="margin-top:1.5rem"><a class="btn ghost" href="introduction.html#what-did-the-learning-process-look-like">The learning process {ICON['arrow']}</a></p>
    </div>
    <div class="reveal">
      <span class="kicker">The authors</span>
      <div class="people">{people_html}</div>
    </div>
  </div>
</section>"""
    return shell("", body, n=0, current="home")


# ---------- library pages ----------
def practices_page():
    chips = ['<button class="chip" data-value="all" aria-pressed="true">All</button>',
             '<button class="chip" data-value="individual" aria-pressed="false">On your own</button>',
             '<button class="chip" data-value="team" aria-pressed="false">With a team</button>',
             '<button class="chip" data-value="movement" aria-pressed="false">Movement scores</button>']
    chips += [f'<button class="chip" data-value="ch{c["num"]}" aria-pressed="false">Chapter {c["num"]}</button>' for c in book["chapters"]]
    cards = []
    for p in all_practices:
        tags = " ".join(p["tags"] + [f"ch{p['ch']}"])
        label = {"individual": "On your own", "team": "With a team", "movement": "Movement"}
        tag_html = "".join(f"<span>{label[t]}</span>" for t in p["tags"]) + (f"<span>{p['mins']} min</span>" if p["mins"] else "")
        cards.append(f'''<a class="lib-card" href="{p["url"]}" data-tags="{tags}" style="{cvars(p["ch"])}">
  <span class="k"><span>{p["kind"]}</span><span>Chapter {p["ch"]}</span></span><h3>{esc(p["title"])}</h3><p>{esc(p["excerpt"])}</p><div class="tags">{tag_html}</div></a>''')
    body = f"""<header class="page-hero wrap"><span class="kicker">Practice library</span><h1>Practices for leading together</h1>
<p>Concrete, tried-and-tested exercises from the research workshops. Some take five minutes on your own, others are structured processes to facilitate with a group. <span id="pcount">{len(all_practices)}</span> practices.</p></header>
<div class="wrap"><div class="filters" data-filter-group data-filter-target=".lib-card" data-filter-count="#pcount" role="group" aria-label="Filter practices">{''.join(chips)}</div>
<div class="lib">{''.join(cards)}</div></div>"""
    return shell("Practice library", body, n=2, current="practices",
                 desc="Tried-and-tested practices for self-leadership, dialogue, feedback, power, participatory meetings and decision-making.")


def voices_page():
    names = ["Mette", "Karin", "Nati", "Dejan"]
    chips = ['<button class="chip" data-value="all" aria-pressed="true">Everyone</button>']
    chips += [f'<button class="chip" data-value="{n.lower()}" aria-pressed="false">{n}</button>' for n in names]
    cards = []
    for v in all_voices:
        tags = " ".join(s.lower() for s in v["speakers"]) or "other"
        cards.append(f'''<div class="voice-card" data-tags="{tags}" style="{cvars(v["ch"])}">
  <aside class="box box--{v["kind"]}"><div class="box-label">{ICON["quote"]} {esc(v["label"])}</div><div class="clip">{re.sub(r' id="t[0-9]+"', '', v["html"])}</div>
  <button class="expand">Read the full excerpt</button></aside>
  <p class="src">Chapter {v["ch"]} · <a href="{v["url"]}">{esc(v["section"])}</a></p></div>''')
    bios = "".join(f"<li><b>{n}</b> {esc(d)}</li>" for n, d in curation["voice_bios"])
    body = f"""<header class="page-hero wrap"><span class="kicker">Voices from the field</span><h1>Conversation partners</h1>
<p>Edited excerpts from interviews with three senior practitioners who have spent years accompanying organisations towards leading together, and one choreographer who brings an artist’s way of knowing.</p></header>
<div class="wrap"><ul style="list-style:none;padding:0;margin:0;display:grid;gap:.4rem;font-family:var(--sans);font-size:.92rem;color:var(--muted);max-width:46rem">{bios}</ul>
<div class="filters" data-filter-group data-filter-target=".voice-card" role="group" aria-label="Filter by voice">{''.join(chips)}</div>
<div class="voice-list">{''.join(cards)}</div></div>"""
    return shell("Voices from the field", body, n=1, current="voices",
                 desc="Excerpts from conversations with Mette Aagaard, Karin Tenelius, Nati Lombardo and choreographer Dejan Srhoj.")


def elena_page():
    parts = []
    for ch in book["chapters"]:
        if not ch["story"]:
            continue
        n = ch["num"]
        for st in ch["story"]:
            search_index.append({"k": "story", "t": "Elena’s story", "w": f"Chapter {n}", "u": f"elena.html#chapter-{n}",
                                 "x": text_of(st["html"]), "c": colours(n)["ink"]})
        parts.append(f'''<section class="elena-chapter" id="chapter-{n}">
  <div class="elena-marker" style="{cvars(n)}">Chapter<b>{n}</b>{esc(ch["title"])}</div>
  {render_story(ch["story"], False, n)}
  <p style="text-align:center;margin-top:1.4rem;font-family:var(--sans);font-weight:700;font-size:.9rem"><a href="chapter-{n}.html">Read chapter {n} →</a></p>
</section>''')
    body = f"""<header class="page-hero wrap" style="text-align:center"><span class="kicker">A voice from fiction</span><h1>Elena’s story</h1>
<p style="margin-inline:auto">Elena is not real. Her doubts, decisions, moments of recognition and setbacks are a collage of what the authors heard and witnessed across many real-life journeys. She manages an elderly care department in a Swedish municipality, and something is not working.</p></header>
{''.join(parts)}"""
    return shell("Elena’s story", body, n=1, current="elena",
                 desc="A fictional story told across six chapters: Elena, a manager in elderly care, tries to lead differently.")


def journal_page():
    parts = []
    for n, title, qs in all_questions:
        if not qs:
            continue
        items = "".join(question_html(q["id"], q["html"]) for q in qs)
        parts.append(f'''<section class="journal-ch" id="chapter-{n}" style="{cvars(n)}"><h2><span>{n}</span> {esc(title)}</h2>
<ol class="questions" data-journal>{items}</ol><p style="font:600 .9rem var(--sans)"><a href="chapter-{n}.html">Read chapter {n} →</a></p></section>''')
    body = f"""<header class="page-hero wrap"><span class="kicker">Reflection journal</span><h1>Questions for reflection</h1>
<p>There are no right answers. Use these questions alone, with colleagues, in a study circle or a learning group. Whatever you write is saved only in this browser, never sent anywhere.</p>
<div class="journal-tools"><button class="btn" id="journal-export">{ICON['file']} Download as Markdown</button><button class="btn ghost" id="journal-print">Print</button><button class="btn ghost" id="journal-clear">Clear all</button></div>
<p class="journal-stats" style="margin-top:1rem"></p></header>
<div class="wrap" data-journal><div style="max-width:48rem;padding-bottom:4rem">{''.join(parts)}</div></div>"""
    return shell("Reflection journal", body, n=3, current="journal",
                 desc="Questions for reflection from every chapter, with a private journal saved in your browser.")


# ---------- build ----------
pages = {}
pages["introduction.html"] = intro_page()
for ch in book["chapters"]:
    pages[f"chapter-{ch['num']}.html"] = chapter_page(ch)
pages["elena.html"] = elena_page()
pages["practices.html"] = practices_page()
pages["voices.html"] = voices_page()
pages["journal.html"] = journal_page()
pages["index.html"] = home_page()
for name, content in pages.items():
    open(name, "w").write(content)
with open("assets/search-index.js", "w") as f:
    f.write("window.SEARCH_INDEX=" + json.dumps(search_index, ensure_ascii=False, separators=(",", ":")) + ";")
print(f"{len(pages)} pages, {len(search_index)} search entries, {len(all_practices)} practices, {len(all_voices)} voices")
