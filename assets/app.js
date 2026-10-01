/* Transforming how we lead together: web edition. Plain JS, no dependencies. */
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const store = {
    get(k, d = null) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* storage unavailable */ } },
    del(k) { try { localStorage.removeItem(k); } catch { /* ignore */ } },
    keys() { try { return Object.keys(localStorage); } catch { return []; } },
  };
  const root = document.documentElement;
  const ROOT = document.body.dataset.root || "";
  const ASSET_V = (document.currentScript?.src.match(/[?&]v=([^&]+)/) || [])[1] || "";

  /* ---------- theme ---------- */
  const themeBtn = $("#theme-btn");
  const applyTheme = (t) => { if (t) root.dataset.theme = t; else delete root.dataset.theme; };
  applyTheme(store.get("theme"));
  themeBtn?.addEventListener("click", () => {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    const next = dark ? "light" : "dark";
    applyTheme(next); store.set("theme", next);
  });

  /* ---------- toast ---------- */
  const toast = (msg) => {
    let t = $(".toast");
    if (!t) { t = document.createElement("div"); t.className = "toast"; t.setAttribute("role", "status"); document.body.append(t); }
    t.textContent = msg; t.classList.add("on");
    clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("on"), 2200);
  };

  /* ---------- nav (mobile drawer + chapters popover) ---------- */
  const nav = $(".nav"), scrim = $(".scrim"), menuBtn = $(".menu-btn");
  const setMenu = (open) => {
    nav?.classList.toggle("open", open); scrim?.classList.toggle("on", open);
    document.body.classList.toggle("menu-open", open);
    if (menuBtn) {
      menuBtn._icon = menuBtn._icon || menuBtn.innerHTML;
      menuBtn.innerHTML = open ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>' : menuBtn._icon;
      menuBtn.setAttribute("aria-label", open ? "Close menu" : "Menu");
    }
    menuBtn?.setAttribute("aria-expanded", open);
  };
  menuBtn?.addEventListener("click", () => setMenu(!nav.classList.contains("open")));
  scrim?.addEventListener("click", () => setMenu(false));
  const chMenu = $(".chapters-menu");
  chMenu?.querySelector("button").addEventListener("click", (e) => {
    e.stopPropagation();
    const open = !chMenu.classList.contains("open");
    chMenu.classList.toggle("open", open);
    e.currentTarget.setAttribute("aria-expanded", open);
  });
  document.addEventListener("click", (e) => { if (chMenu && !chMenu.contains(e.target)) chMenu.classList.remove("open"); });

  /* ---------- top bar + progress ---------- */
  const bar = $(".topbar"), prog = $(".progress"), article = $(".prose");
  const chapterKey = document.body.dataset.chapter;
  let ticking = false;
  const onScroll = () => {
    ticking = false;
    bar?.classList.toggle("scrolled", scrollY > 10);
    if (prog && article) {
      const r = article.getBoundingClientRect();
      const total = r.height - innerHeight * 0.6;
      const p = Math.min(1, Math.max(0, -r.top / Math.max(1, total)));
      prog.style.transform = `scaleX(${p})`;
      if (chapterKey) {
        const k = "progress:" + chapterKey;
        if (p > (store.get(k, 0) || 0) + 0.02 || p > 0.98) store.set(k, Math.round(p * 100) / 100);
      }
    }
  };
  addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();

  /* ---------- lazy ink images ---------- */
  const loadInk = (el) => {
    if (!el.dataset.src || el.classList.contains("loaded")) return;
    const src = new URL(el.dataset.src, document.baseURI).href; // absolute: var() urls resolve against the stylesheet
    const img = new Image();
    img.onload = () => { el.style.setProperty("--src", `url("${src}")`); el.classList.add("loaded"); };
    img.src = src;
  };
  const inkIO = "IntersectionObserver" in window ? new IntersectionObserver((es) => {
    es.forEach((e) => { if (e.isIntersecting) { loadInk(e.target); inkIO.unobserve(e.target); } });
  }, { rootMargin: "600px 0px" }) : null;
  $$(".ink-img[data-src]").forEach((el) => inkIO ? inkIO.observe(el) : loadInk(el));

  /* ---------- reveal ---------- */
  const revIO = "IntersectionObserver" in window ? new IntersectionObserver((es) => {
    es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); revIO.unobserve(e.target); } });
  }, { rootMargin: "0px 0px -8% 0px" }) : null;
  $$(".reveal").forEach((el) => revIO ? revIO.observe(el) : el.classList.add("in"));

  /* ---------- cover animation ---------- */
  const cover = $(".cover");
  if (cover) requestAnimationFrame(() => setTimeout(() => cover.classList.add("go"), 250));

  /* ---------- explainer video ---------- */
  $$(".video-frame").forEach((fr) => {
    const v = fr.querySelector("video"), b = fr.querySelector(".video-play");
    b?.addEventListener("click", () => { v.play(); });
    v.addEventListener("play", () => fr.classList.add("playing"));
    v.addEventListener("ended", () => fr.classList.remove("playing"));
  });

  /* ---------- chapter progress on home ---------- */
  $$("[data-progress]").forEach((el) => {
    const p = store.get("progress:" + el.dataset.progress, 0) || 0;
    const i = el.querySelector("i"); if (i) requestAnimationFrame(() => (i.style.width = Math.round(p * 100) + "%"));
    const lbl = el.parentElement.querySelector(".pct");
    if (lbl && p > 0.01) lbl.textContent = p > 0.97 ? "Read ✓" : Math.round(p * 100) + "% read";
  });

  /* ---------- TOC active section ---------- */
  const tocLinks = $$(".toc a[href^='#'], .mobile-toc .sheet a[href^='#']");
  const mobileLabel = $(".mobile-toc > button span");
  const tocTargets = [];
  tocLinks.forEach((a) => {
    const el = document.getElementById(decodeURIComponent(a.getAttribute("href").slice(1)));
    if (el) tocTargets.push([el, a]);
  });
  let lastActive = null;
  const updateToc = () => {
    let cur = null;
    for (const [el] of tocTargets) { if (el.getBoundingClientRect().top < innerHeight * 0.3) cur = el; }
    if (cur === lastActive) return;
    lastActive = cur;
    tocTargets.forEach(([el, a]) => a.classList.toggle("active", el === cur));
    const hit = tocTargets.find(([el]) => el === cur);
    if (hit && mobileLabel) mobileLabel.textContent = hit[1].textContent;
    const side = tocTargets.find(([el, a]) => el === cur && a.closest(".toc"));
    const box = $(".toc");
    if (side && box && box.scrollHeight > box.clientHeight) {
      const top = side[1].offsetTop;
      if (top < box.scrollTop || top > box.scrollTop + box.clientHeight - 40) box.scrollTop = top - box.clientHeight / 3;
    }
  };
  if (tocTargets.length) {
    addEventListener("scroll", () => requestAnimationFrame(updateToc), { passive: true });
    updateToc();
  }
  const mtoc = $(".mobile-toc");
  if (mtoc) {
    mtoc.querySelector("button").addEventListener("click", (e) => { e.stopPropagation(); mtoc.classList.toggle("open"); });
    mtoc.querySelectorAll(".sheet a").forEach((a) => a.addEventListener("click", () => mtoc.classList.remove("open")));
    document.addEventListener("click", (e) => { if (!mtoc.contains(e.target)) mtoc.classList.remove("open"); });
  }

  /* ---------- copy section links ---------- */
  $$(".anchor").forEach((a) => a.addEventListener("click", (e) => {
    e.preventDefault();
    const url = location.href.split("#")[0] + a.getAttribute("href");
    history.replaceState(null, "", a.getAttribute("href"));
    navigator.clipboard?.writeText(url).then(() => toast("Link copied"), () => {});
  }));

  /* ---------- Elena: collapse long stories on chapter pages ---------- */
  $$(".elena.collapsible").forEach((el) => {
    if (el.querySelector(".elena-body").scrollHeight > 900) {
      el.classList.add("collapsed");
      el.querySelector(".more").addEventListener("click", () => el.classList.remove("collapsed"));
    }
  });

  /* ---------- reflections (questions for reflection + journal) ---------- */
  const qKey = (id) => "reflect:" + id;
  $$(".q[data-qid]").forEach((q) => {
    const id = q.dataset.qid, ta = q.querySelector("textarea"), btn = q.querySelector("button.reflect"), saved = q.querySelector(".saved");
    const val = store.get(qKey(id), "");
    const show = () => { ta.hidden = false; btn.setAttribute("aria-expanded", "true"); };
    if (val) { ta.value = val; q.classList.add("has-note"); if (!q.closest("[data-journal]")) btn.querySelector("span").textContent = "Edit your reflection"; }
    if (val || q.closest("[data-journal]")) show();
    btn?.addEventListener("click", () => {
      if (ta.hidden) { show(); ta.focus(); } else if (!ta.value) { ta.hidden = true; btn.setAttribute("aria-expanded", "false"); }
      else ta.focus();
    });
    let h;
    ta.addEventListener("input", () => {
      clearTimeout(h);
      h = setTimeout(() => {
        const v = ta.value.trim();
        v ? store.set(qKey(id), ta.value) : store.del(qKey(id));
        q.classList.toggle("has-note", !!v);
        if (saved) { saved.textContent = v ? "Saved on this device" : ""; }
        updateJournalStats();
      }, 350);
    });
  });
  const updateJournalStats = () => {
    const el = $(".journal-stats"); if (!el) return;
    const n = store.keys().filter((k) => k.startsWith("reflect:")).length;
    el.textContent = n ? `You have written ${n} reflection${n === 1 ? "" : "s"}. They are stored only in this browser.` : "Nothing written yet. Your reflections are stored only in this browser.";
  };
  updateJournalStats();
  $("#journal-export")?.addEventListener("click", () => {
    let md = "# My reflections\n_Transforming how we lead together_\n\n";
    $$(".journal-ch").forEach((ch) => {
      const qs = $$(".q[data-qid]", ch).filter((q) => store.get(qKey(q.dataset.qid)));
      if (!qs.length) return;
      md += `## ${ch.querySelector("h2").textContent.trim()}\n\n`;
      qs.forEach((q) => { md += `**${q.querySelector("p").textContent.trim()}**\n\n${store.get(qKey(q.dataset.qid)).trim()}\n\n`; });
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([md], { type: "text/markdown" }));
    a.download = "my-reflections.md"; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  });
  $("#journal-print")?.addEventListener("click", () => print());
  $("#journal-clear")?.addEventListener("click", () => {
    if (!confirm("Delete all reflections stored in this browser?")) return;
    store.keys().filter((k) => k.startsWith("reflect:")).forEach((k) => store.del(k));
    $$(".q textarea").forEach((t) => (t.value = "")); $$(".q").forEach((q) => q.classList.remove("has-note"));
    updateJournalStats(); toast("Reflections cleared");
  });

  /* ---------- practice timer ---------- */
  let timer = null;
  const fmt = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  const chime = () => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      [523.25, 659.25, 783.99].forEach((f, i) => {
        const o = ctx.createOscillator(), g = ctx.createGain();
        o.frequency.value = f; o.type = "sine";
        g.gain.setValueAtTime(0, ctx.currentTime + i * 0.18);
        g.gain.linearRampToValueAtTime(0.18, ctx.currentTime + i * 0.18 + 0.02);
        g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.18 + 1.6);
        o.connect(g).connect(ctx.destination); o.start(ctx.currentTime + i * 0.18); o.stop(ctx.currentTime + i * 0.18 + 1.7);
      });
    } catch { /* audio unavailable */ }
  };
  const ui = $(".timer");
  const draw = () => {
    if (!timer || !ui) return;
    ui.querySelector(".t").textContent = fmt(timer.left);
    const C = 2 * Math.PI * 22;
    ui.querySelector(".fg").style.strokeDashoffset = C * (1 - timer.left / timer.total);
    ui.querySelector(".pause").innerHTML = timer.running
      ? '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15l13-7.5z"/></svg>';
    ui.querySelector(".pause").setAttribute("aria-label", timer.running ? "Pause" : "Resume");
  };
  const tick = () => {
    if (!timer?.running) return;
    timer.left = Math.max(0, Math.round((timer.end - Date.now()) / 1000));
    draw();
    if (timer.left === 0) { timer.running = false; chime(); toast("Time is up. Take a breath."); draw(); return; }
    timer.h = setTimeout(tick, 250);
  };
  $$(".timer-btn").forEach((b) => b.addEventListener("click", () => {
    const mins = +b.dataset.minutes;
    clearTimeout(timer?.h);
    timer = { total: mins * 60, left: mins * 60, end: Date.now() + mins * 60000, running: true };
    ui.querySelector(".lbl").textContent = b.dataset.label;
    const C = 2 * Math.PI * 22; ui.querySelector(".fg").style.strokeDasharray = C;
    ui.classList.add("on"); draw(); tick();
  }));
  ui?.querySelector(".pause").addEventListener("click", () => {
    if (!timer) return;
    if (timer.running) { timer.running = false; clearTimeout(timer.h); }
    else if (timer.left > 0) { timer.running = true; timer.end = Date.now() + timer.left * 1000; tick(); }
    draw();
  });
  ui?.querySelector(".close").addEventListener("click", () => { clearTimeout(timer?.h); timer = null; ui.classList.remove("on"); });

  /* ---------- filters (practices + voices) ---------- */
  $$("[data-filter-group]").forEach((group) => {
    const items = $$(group.dataset.filterTarget);
    const count = $(group.dataset.filterCount || "#none");
    group.addEventListener("click", (e) => {
      const chip = e.target.closest(".chip"); if (!chip) return;
      $$(".chip", group).forEach((c) => c.setAttribute("aria-pressed", c === chip));
      const f = chip.dataset.value;
      let n = 0;
      items.forEach((it) => { const show = f === "all" || it.dataset.tags.split(" ").includes(f); it.hidden = !show; n += show; });
      if (count) count.textContent = n;
    });
  });
  $$(".voice-card .expand").forEach((b) => b.addEventListener("click", () => {
    const c = b.closest(".voice-card"); c.classList.toggle("open");
    b.textContent = c.classList.contains("open") ? "Show less" : "Read the full excerpt";
  }));

  /* ---------- lightbox ---------- */
  const lb = $(".lightbox");
  $$(".fig.zoomable").forEach((f) => f.addEventListener("click", () => {
    const src = new URL(f.querySelector(".ink-img").dataset.src, document.baseURI).href;
    lb.querySelector(".ink-img").style.setProperty("--src", `url("${src}")`);
    lb.querySelector("p").innerHTML = f.querySelector("figcaption")?.innerHTML || "";
    lb.classList.add("open");
  }));
  lb?.addEventListener("click", () => lb.classList.remove("open"));

  /* ---------- search ---------- */
  const search = $(".search"), input = $(".search input"), results = $(".search-results");
  let index = null, sel = 0, hits = [];
  const norm = (s) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  const loadIndex = () => new Promise((res) => {
    if (index) return res(index);
    if (window.SEARCH_INDEX) { index = window.SEARCH_INDEX.map((r) => ({ ...r, n: norm(r.t + " " + r.x) })); return res(index); }
    const s = document.createElement("script"); s.src = ROOT + "assets/search-index.js" + (ASSET_V ? "?v=" + ASSET_V : "");
    s.onload = () => { index = window.SEARCH_INDEX.map((r) => ({ ...r, n: norm(r.t + " " + r.x) })); res(index); };
    document.head.append(s);
  });
  const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const snippet = (text, terms) => {
    const n = norm(text);
    let at = -1;
    for (const t of terms) { at = n.indexOf(t); if (at >= 0) break; }
    const start = Math.max(0, at - 70);
    let s = (start ? "…" : "") + text.slice(start, start + 220) + (start + 220 < text.length ? "…" : "");
    let out = esc(s);
    terms.forEach((t) => {
      if (t.length < 2) return;
      const re = new RegExp("(" + t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  };
  const render = () => {
    const q = norm(input.value.trim());
    const terms = q.split(/\s+/).filter(Boolean);
    if (!terms.length) { results.innerHTML = results.dataset.hints || ""; hits = []; return; }
    hits = index.map((r) => {
      let score = 0;
      for (const t of terms) { const i = r.n.indexOf(t); if (i < 0) return null; score += (norm(r.t).includes(t) ? 6 : 1) + (i < 200 ? 0.5 : 0); }
      if (r.k === "section") score += 3;
      return [score, r];
    }).filter(Boolean).sort((a, b) => b[0] - a[0]).slice(0, 40).map((x) => x[1]);
    sel = 0;
    results.innerHTML = hits.length ? hits.map((r, i) =>
      `<a href="${ROOT}${r.u}" role="option" aria-selected="${i === 0}" style="--r-ink:${r.c}"><div class="where">${esc(r.w)}</div><div><b>${esc(r.t)}</b></div><div class="snip">${snippet(r.x, terms)}</div></a>`
    ).join("") : `<div class="search-empty">Nothing found for “${esc(input.value)}”.</div>`;
  };
  const openSearch = () => {
    search.classList.add("open"); input.value = ""; input.focus();
    results.innerHTML = results.dataset.hints || "";
    loadIndex();
  };
  const closeSearch = () => search.classList.remove("open");
  $$(".search-btn").forEach((b) => b.addEventListener("click", () => { setMenu(false); openSearch(); }));
  search?.addEventListener("click", (e) => {
    if (e.target === search) closeSearch();
    const hint = e.target.closest("[data-q]");
    if (hint) { input.value = hint.dataset.q; loadIndex().then(render); }
  });
  input?.addEventListener("input", () => loadIndex().then(render));
  input?.addEventListener("keydown", (e) => {
    const links = $$("a", results);
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault(); if (!links.length) return;
      sel = (sel + (e.key === "ArrowDown" ? 1 : -1) + links.length) % links.length;
      links.forEach((a, i) => a.setAttribute("aria-selected", i === sel)); links[sel].scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter" && links[sel]) { links[sel].click(); closeSearch(); }
  });
  results?.addEventListener("click", (e) => { if (e.target.closest("a")) closeSearch(); });
  addEventListener("keydown", (e) => {
    const typing = /INPUT|TEXTAREA/.test(document.activeElement?.tagName);
    if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !typing)) { e.preventDefault(); openSearch(); }
    if (e.key === "Escape") { closeSearch(); lb?.classList.remove("open"); setMenu(false); mtoc?.classList.remove("open"); }
  });

  /* ---------- highlight search target ---------- */
  const flashHash = () => {
    if (!location.hash) return;
    const el = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (el && !el.matches(".sec")) { el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); }
  };
  addEventListener("hashchange", flashHash); flashHash();
})();
