#!/usr/bin/env python3
"""Merchly designer-grade LinkedIn visuals, rendered from HTML/CSS with headless Chrome.

Usage:
  python3 -I render_html.py spec.json out.jpg      # single 4:5 image (2160x2700 JPEG, sharp on retina)
  python3 -I render_html.py spec.json out.pdf      # carousel (type "carousel"), also writes out.cover.jpg

Common fields (all types):
  "theme": "light" | "dark"      (alternate day to day so the feed doesn't look repetitive)
  "tag":   short topic pill, e.g. "COD OPERATIONS", "CHECKOUT", "PROFIT", "DATA"
  "footer": "CODless by Merchly" | "Merchly" ...
  "source": "Source: ..."        (required for bars / bignumber)
  In any title/text, wrap words in *asterisks* to highlight them.

Icons (optional "icon" on steps/cells/items): phone, box, truck, rupee, check, x, chart, cart,
  card, shield, flag, clock, users, map, tag, refresh, alert, target, filter, calc

Types:
  {"type":"bars","title":"...","subtitle":"...","unit":"%","bars":[{"label":"COD","value":37.5,"highlight":true},...],"note":"optional callout","source":"..."}
  {"type":"bignumber","number":"7x","text":"...","context":"optional smaller line","source":"..."}
  {"type":"mythfact","title":"...","pairs":[{"myth":"...","fact":"..."}]}          (1-3 pairs)
  {"type":"grid","title":"...","cells":[{"icon":"phone","head":"...","body":"..."}]}  (exactly 4)
  {"type":"workflow","title":"...","steps":[{"icon":"cart","head":"...","body":"optional"}]} (3-6; plain strings ok)
  {"type":"checklist","title":"...","items":["...", ...]}                          (3-7)
  {"type":"compare","title":"...","left_label":"...","left":["..."],"left_total":"optional",
     "right_label":"...","right":["..."],"right_total":"optional","example":true}
  {"type":"statement","kicker":"UNPOPULAR OPINION","text":"...","support":"optional smaller line"}
  {"type":"carousel","kicker":"COD PLAYBOOK","title":"...","subtitle":"optional",
     "slides":[{"icon":"phone","head":"...","body":"...","points":["..."],"metric":"optional: what to measure"}],
     "end_title":"...","end_body":"..."}                                            (3-8 slides)
"""
import html
import json
import re
import sys

W, H = 1080, 1350

ICONS = {
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>',
    "box": '<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5"/><path d="M12 13v8"/>',
    "truck": '<path d="M1 4h13v11H1z"/><path d="M14 8h4l3 3v4h-7z"/><circle cx="5.5" cy="18" r="2"/><circle cx="17.5" cy="18" r="2"/>',
    "rupee": '<path d="M6 3h12M6 8h12M6 13l8.5 8M6 13h3a5 5 0 0 0 0-10"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "x": '<path d="M18 6 6 18M6 6l12 12"/>',
    "chart": '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/>',
    "cart": '<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h3l2.7 12.2a2 2 0 0 0 2 1.6h7.7a2 2 0 0 0 2-1.5L21 8H6"/>',
    "card": '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "flag": '<path d="M4 22V4a1 1 0 0 1 1-1h12l-2 4 2 4H5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
    "map": '<path d="M12 22s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/>',
    "tag": '<path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    "refresh": '<path d="M21 12a9 9 0 0 1-15.5 6.2L3 16"/><path d="M3 12a9 9 0 0 1 15.5-6.2L21 8"/><path d="M21 3v5h-5M3 21v-5h5"/>',
    "alert": '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "filter": '<path d="M22 3H2l8 9.5V19l4 2v-8.5z"/>',
    "calc": '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 11h.01M12 11h.01M16 11h.01M8 15h.01M12 15h.01M16 15h.01M8 19h8"/>',
}


def icon(name, size=40, stroke="currentColor", sw=2):
    p = ICONS.get(name or "", ICONS["check"])
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{stroke}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{p}</svg>')


def rich(text):
    """Escape, then turn *word* into a highlighted span."""
    t = html.escape(str(text))
    return re.sub(r"\*(.+?)\*", r'<span class="hl">\1</span>', t)


THEMES = {
    "light": dict(bg="#F6F4EF", bg2="#EDE9FE", ink="#14112B", sub="#3D3954", card="#FFFFFF",
                  line="#E4E0D8", accent="#5B3DF5", accent2="#7C3AED", hl="#FDE68A", hlink="#14112B",
                  good="#15803D", goodbg="#DCFCE7", bad="#B91C1C", badbg="#FEE2E2", chip="#14112B", chipink="#FFFFFF",
                  glow="rgba(91,61,245,.10)"),
    "dark": dict(bg="#0F0B24", bg2="#1C1442", ink="#FFFFFF", sub="#D4CFEE", card="#1A1438",
                 line="#2E2659", accent="#8B7BFF", accent2="#A78BFA", hl="#FACC15", hlink="#0F0B24",
                 good="#4ADE80", goodbg="rgba(74,222,128,.12)", bad="#F87171", badbg="rgba(248,113,113,.12)",
                 chip="#FACC15", chipink="#0F0B24", glow="rgba(139,123,255,.25)"),
}


def base_css(t):
    return f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
body{{font-family:'Inter',sans-serif;color:{t['ink']};background:{t['bg']};-webkit-font-smoothing:antialiased;
  font-feature-settings:'ss01','cv11';position:relative}}
.canvas{{position:absolute;inset:0;padding:84px 84px 0 84px;display:flex;flex-direction:column}}
.glow{{position:absolute;width:900px;height:900px;border-radius:50%;background:radial-gradient(circle,{t['glow']} 0%,transparent 65%);right:-360px;top:-380px;pointer-events:none}}
.glow2{{position:absolute;width:700px;height:700px;border-radius:50%;background:radial-gradient(circle,{t['glow']} 0%,transparent 65%);left:-320px;bottom:-300px;pointer-events:none}}
.grain{{position:absolute;inset:0;opacity:.045;pointer-events:none;mix-blend-mode:multiply;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>")}}
.top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:56px;position:relative;z-index:2}}
.brand{{display:flex;align-items:center;gap:14px;font-family:'Inter Display';font-weight:800;font-size:26px;letter-spacing:.02em}}
.mark{{width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,#4F46E5,#7C3AED);position:relative;display:flex;align-items:center;justify-content:center}}
.mark svg{{display:block}}
.mark i{{position:absolute;width:10px;height:10px;border-radius:50%;background:#FACC15;right:6px;top:6px}}
.chip{{background:{t['chip']};color:{t['chipink']};font-weight:700;font-size:20px;letter-spacing:.14em;padding:12px 22px;border-radius:999px}}
h1{{font-family:'Inter Display';font-weight:800;font-size:76px;line-height:1.02;letter-spacing:-.035em;position:relative;z-index:2}}
h1.md{{font-size:64px}}
.subtitle{{font-size:30px;line-height:1.35;color:{t['sub']};margin-top:22px;max-width:860px;position:relative;z-index:2}}
.hl{{{'color:'+t['hl'] if t['bg'].startswith('#0') else 'background:linear-gradient(transparent 58%,'+t['hl']+' 58%,'+t['hl']+' 92%,transparent 92%);padding:0 4px;margin:0 -4px'}}}
.body{{flex:1;display:flex;flex-direction:column;justify-content:center;position:relative;z-index:2;padding:40px 0}}
.card{{background:{t['card']};border:1px solid {t['line']};border-radius:28px;box-shadow:0 1px 0 rgba(255,255,255,.04) inset,0 24px 60px -30px rgba(20,17,43,.35)}}
.foot{{height:118px;border-top:1px solid {t['line']};display:flex;align-items:center;justify-content:space-between;font-size:21px;color:{t['sub']};position:relative;z-index:2}}
.foot b{{color:{t['ink']};font-weight:700}}
.dot{{display:inline-block;width:12px;height:12px;border-radius:50%;background:#FACC15;margin-right:12px;vertical-align:middle}}
.ico{{display:flex;align-items:center;justify-content:center;border-radius:18px;flex:none}}
"""


def frame(t, inner, spec, extra_css="", page=None):
    tag = rich(spec.get("tag", "")) if spec.get("tag") else ""
    src = rich(spec.get("source", "")) if spec.get("source") else ""
    footer = rich(spec.get("footer", "Merchly"))
    right = f'<span><span class="dot"></span><b>{footer}</b></span>'
    if page:
        right = f'<span><b>{page}</b></span>'
    left = src or (f'<span><span class="dot"></span><b>{footer}</b></span>' if page else "")
    if not page and not src:
        left = '<span>Follow Merchly for practical COD playbooks</span>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{base_css(t)}{extra_css}</style></head>
<body><div class="glow"></div><div class="glow2"></div><div class="grain"></div>
<div class="canvas">
 <div class="top"><div class="brand"><div class="mark"><svg width="26" height="22" viewBox="0 0 26 22"><path d="M3 19V4l10 10L23 4v15" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg><i></i></div>Merchly</div>{f'<div class="chip">{tag}</div>' if tag else ''}</div>
 {inner}
 <div class="foot">{left}{right}</div>
</div></body></html>"""


def head_block(spec, cls=""):
    out = f'<h1 class="{cls}">{rich(spec["title"])}</h1>'
    if spec.get("subtitle"):
        out += f'<div class="subtitle">{rich(spec["subtitle"])}</div>'
    return out


def fmt_val(v, unit):
    if isinstance(v, float):
        s = f"{v:.1f}".rstrip("0").rstrip(".")
    else:
        s = str(v)
    return s + (unit or "")


def t_bars(spec, t):
    bars = spec["bars"][:6]
    unit = spec.get("unit", "")
    vmax = max(float(b["value"]) for b in bars) or 1
    rows = ""
    for b in bars:
        pct = max(3, 100 * float(b["value"]) / vmax)
        hi = b.get("highlight")
        col = f"linear-gradient(90deg,{t['accent']},{t['accent2']})" if hi else t['line']
        vcol = t['accent'] if hi else t['sub']
        rows += f"""<div class="row"><div class="lab">{rich(b['label'])}</div>
<div class="track"><div class="bar" style="width:{pct:.1f}%;background:{col}"></div></div>
<div class="val" style="color:{vcol}">{fmt_val(b['value'], unit)}</div></div>"""
    note = f'<div class="note">{icon("alert",30,t["accent"])}<span>{rich(spec["note"])}</span></div>' if spec.get("note") else ""
    css = f""".chartcard{{padding:56px 52px}}
.row{{display:grid;grid-template-columns:250px 1fr 170px;align-items:center;gap:26px;margin:34px 0}}
.lab{{font-weight:700;font-size:32px;line-height:1.2}}
.track{{height:76px;border-radius:14px;background:{t['bg']};overflow:hidden}}
.bar{{height:100%;border-radius:14px}}
.val{{font-family:'Inter Display';font-weight:800;font-size:54px;letter-spacing:-.02em;text-align:right}}
.note{{display:flex;gap:16px;align-items:flex-start;margin-top:30px;padding-top:30px;border-top:1px dashed {t['line']};font-size:29px;line-height:1.4;color:{t['sub']}}}
.note svg{{flex:none;margin-top:2px}}"""
    inner = head_block(spec, "md") + f'<div class="body"><div class="card chartcard">{rows}{note}</div></div>'
    return inner, css


def t_bignumber(spec, t):
    css = f""".bn{{font-family:'Inter Display';font-weight:900;font-size:300px;line-height:.9;letter-spacing:-.06em;
background:linear-gradient(135deg,{t['accent']},#EC4899 60%,#F59E0B);-webkit-background-clip:text;color:transparent}}
.bt{{font-family:'Inter Display';font-weight:800;font-size:60px;line-height:1.08;letter-spacing:-.03em;margin-top:30px;max-width:900px}}
.bc{{font-size:30px;line-height:1.4;color:{t['sub']};margin-top:30px;max-width:860px;padding-left:24px;border-left:5px solid {t['accent']}}}"""
    ctx = f'<div class="bc">{rich(spec["context"])}</div>' if spec.get("context") else ""
    inner = f'<div class="body"><div class="bn">{html.escape(spec["number"])}</div><div class="bt">{rich(spec["text"])}</div>{ctx}</div>'
    return inner, css


def t_mythfact(spec, t):
    pairs = spec["pairs"][:3]
    big = len(pairs) == 1
    items = ""
    for p in pairs:
        items += f"""<div class="pair card"><div class="m"><span class="pill pb">{icon('x',22,t['bad'],3)} MYTH</span><p class="mt">{rich(p['myth'])}</p></div>
<div class="f"><span class="pill pg">{icon('check',22,t['good'],3)} FACT</span><p class="ft">{rich(p['fact'])}</p></div></div>"""
    fs = 40 if big else 30
    css = f""".pair{{display:grid;grid-template-columns:1fr 1fr;overflow:hidden;margin:14px 0}}
.m,.f{{padding:34px 34px 38px}}
.m{{background:{t['badbg']}}} .f{{background:{t['goodbg']}}}
.pill{{display:inline-flex;align-items:center;gap:8px;font-weight:800;font-size:19px;letter-spacing:.14em;padding:8px 14px;border-radius:999px;background:{t['card']}}}
.pb{{color:{t['bad']}}} .pg{{color:{t['good']}}}
.mt{{margin-top:20px;font-size:{fs}px;line-height:1.3;color:{t['sub']};text-decoration:line-through;text-decoration-color:{t['bad']};text-decoration-thickness:3px}}
.ft{{margin-top:20px;font-size:{fs}px;line-height:1.3;font-weight:700}}"""
    inner = head_block(spec, "md") + f'<div class="body">{items}</div>'
    return inner, css


def t_grid(spec, t):
    cells = spec["cells"][:4]
    out = ""
    for i, c in enumerate(cells):
        out += f"""<div class="cell card"><div class="ico" style="width:76px;height:76px;background:{t['bg2']};color:{t['accent']}">{icon(c.get('icon','check'),38)}</div>
<div class="n">0{i+1}</div><h3>{rich(c['head'])}</h3><p>{rich(c.get('body',''))}</p></div>"""
    css = f""".g{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}
.cell{{padding:36px 34px 40px;position:relative;min-height:330px}}
.n{{position:absolute;right:30px;top:26px;font-family:'Inter Display';font-weight:800;font-size:28px;color:{t['line']}}}
.cell h3{{font-family:'Inter Display';font-weight:800;font-size:36px;line-height:1.1;letter-spacing:-.02em;margin-top:30px}}
.cell p{{font-size:25px;line-height:1.4;color:{t['sub']};margin-top:14px}}"""
    inner = head_block(spec, "md") + f'<div class="body"><div class="g">{out}</div></div>'
    return inner, css


def t_workflow(spec, t):
    steps = spec["steps"][:6]
    n = len(steps)
    out = ""
    for i, s in enumerate(steps):
        if isinstance(s, str):
            s = {"head": s}
        last = "last" if i == n - 1 else ""
        body = f'<p>{rich(s["body"])}</p>' if s.get("body") else ""
        out += f"""<div class="st {last}"><div class="rail"><div class="ico" style="width:72px;height:72px;background:{t['accent'] if i==n-1 else t['card']};color:{'#fff' if i==n-1 else t['accent']};border:2px solid {t['accent']}">{icon(s.get('icon','check'),34)}</div></div>
<div class="tx"><div class="k">STEP {i+1}</div><h3>{rich(s['head'])}</h3>{body}</div></div>"""
    gap = 26 if n <= 4 else 14
    css = f""".st{{display:grid;grid-template-columns:100px 1fr;gap:26px;position:relative;padding-bottom:{gap}px}}
.rail{{position:relative;display:flex;justify-content:center}}
.st:not(.last) .rail:after{{content:'';position:absolute;top:80px;bottom:-{gap+4}px;width:3px;background:repeating-linear-gradient({t['accent']} 0 10px,transparent 10px 18px);opacity:.6}}
.tx{{padding-top:6px}}
.k{{font-weight:800;font-size:17px;letter-spacing:.18em;color:{t['accent']}}}
.tx h3{{font-family:'Inter Display';font-weight:800;font-size:{40 if n<=4 else 34}px;line-height:1.12;letter-spacing:-.02em;margin-top:6px}}
.tx p{{font-size:25px;line-height:1.4;color:{t['sub']};margin-top:8px}}"""
    inner = head_block(spec, "md") + f'<div class="body">{out}</div>'
    return inner, css


def t_checklist(spec, t):
    items = spec["items"][:7]
    out = ""
    for it in items:
        if isinstance(it, dict):
            it = it.get("text", "")
        out += f'<li><span class="cb">{icon("check",26,"#fff",3.2)}</span><span>{rich(it)}</span></li>'
    fs = 36 if len(items) <= 5 else 31
    css = f""".cl{{list-style:none;padding:46px 48px}}
.cl li{{display:flex;gap:24px;align-items:flex-start;font-size:{fs}px;line-height:1.3;font-weight:600;padding:22px 0;border-bottom:1px solid {t['line']}}}
.cl li:last-child{{border-bottom:0}}
.cb{{flex:none;width:46px;height:46px;border-radius:12px;background:linear-gradient(135deg,{t['accent']},{t['accent2']});display:flex;align-items:center;justify-content:center;margin-top:-2px}}"""
    inner = head_block(spec, "md") + f'<div class="body"><ul class="cl card">{out}</ul></div>'
    return inner, css


def t_compare(spec, t):
    def col(label, items, total, kind):
        c = t['bad'] if kind == "bad" else t['good']
        bgc = t['badbg'] if kind == "bad" else t['goodbg']
        ic = "x" if kind == "bad" else "check"
        lis = "".join(f'<li>{icon(ic,26,c,3)}<span>{rich(x)}</span></li>' for x in items[:6])
        tot = f'<div class="tot" style="color:{c}">{rich(total)}</div>' if total else ""
        return f'<div class="col card"><div class="ch" style="background:{bgc};color:{c}">{rich(label)}</div><ul>{lis}</ul>{tot}</div>'
    ex = '<div class="ex">Example numbers, for illustration</div>' if spec.get("example") else ""
    css = f""".cmp{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}
.col{{overflow:hidden;display:flex;flex-direction:column}}
.ch{{font-family:'Inter Display';font-weight:800;font-size:30px;line-height:1.15;padding:28px 30px}}
.col ul{{list-style:none;padding:18px 30px 10px;flex:1}}
.col li{{display:flex;gap:14px;align-items:flex-start;font-size:27px;line-height:1.35;padding:14px 0;border-bottom:1px solid {t['line']}}}
.col li:last-child{{border-bottom:0}}
.col li svg{{flex:none;margin-top:4px}}
.tot{{font-family:'Inter Display';font-weight:900;font-size:40px;letter-spacing:-.02em;padding:22px 30px 30px;border-top:2px solid {t['line']}}}
.ex{{margin-top:18px;font-size:20px;color:{t['sub']};letter-spacing:.04em}}"""
    inner = head_block(spec, "md") + f'<div class="body"><div class="cmp">{col(spec["left_label"],spec["left"],spec.get("left_total"),"bad")}{col(spec["right_label"],spec["right"],spec.get("right_total"),"good")}</div>{ex}</div>'
    return inner, css


def t_statement(spec, t):
    k = f'<div class="kick">{rich(spec["kicker"])}</div>' if spec.get("kicker") else ""
    sup = f'<div class="sup">{rich(spec["support"])}</div>' if spec.get("support") else ""
    css = f""".q{{width:120px;height:10px;border-radius:6px;background:linear-gradient(90deg,{t['accent']},#EC4899);margin-bottom:44px}}
.kick{{align-self:flex-start;display:inline-block;background:#FACC15;color:#0F0B24;font-weight:800;font-size:22px;letter-spacing:.16em;padding:12px 22px;border-radius:999px;margin-bottom:34px}}
.stx{{font-family:'Inter Display';font-weight:800;font-size:86px;line-height:1.04;letter-spacing:-.04em}}
.sup{{font-size:32px;line-height:1.4;color:{t['sub']};margin-top:40px;max-width:820px}}"""
    inner = f'<div class="body">{k}<div class="q"></div><div class="stx">{rich(spec["text"])}</div>{sup}</div>'
    return inner, css


TYPES = {"bars": t_bars, "bignumber": t_bignumber, "mythfact": t_mythfact, "grid": t_grid,
         "workflow": t_workflow, "checklist": t_checklist, "compare": t_compare, "statement": t_statement}


def carousel_pages(spec, t):
    slides = spec["slides"][:8]
    total = len(slides) + 2
    pages = []
    prog = lambda i: f'<div class="prog"><i style="width:{100*i/total:.1f}%"></i></div>'
    base = f""".prog{{position:absolute;left:0;right:0;top:0;height:8px;background:{t['line']};z-index:3}}
.prog i{{display:block;height:100%;background:linear-gradient(90deg,{t['accent']},#EC4899)}}"""
    # cover
    k = f'<div class="kick">{rich(spec["kicker"])}</div>' if spec.get("kicker") else ""
    sub = f'<div class="subtitle">{rich(spec["subtitle"])}</div>' if spec.get("subtitle") else ""
    cover_css = base + f""".kick{{align-self:flex-start;display:inline-block;background:#FACC15;color:#0F0B24;font-weight:800;font-size:22px;letter-spacing:.16em;padding:12px 22px;border-radius:999px;margin-bottom:36px}}
.ct{{font-family:'Inter Display';font-weight:900;font-size:96px;line-height:1;letter-spacing:-.045em}}
.sw{{display:flex;align-items:center;gap:18px;margin-top:56px;font-weight:800;font-size:28px;color:{t['accent']};letter-spacing:.06em}}
.sw i{{display:block;width:90px;height:4px;background:{t['accent']};position:relative}}
.sw i:after{{content:'';position:absolute;right:-2px;top:-8px;border-left:16px solid {t['accent']};border-top:10px solid transparent;border-bottom:10px solid transparent}}"""
    inner = prog(1) + f'<div class="body">{k}<div class="ct">{rich(spec["title"])}</div>{sub}<div class="sw">SWIPE <i></i></div></div>'
    pages.append(frame(t, inner, {**spec, "source": ""}, cover_css, page=f"1 / {total}"))
    # slides
    for i, s in enumerate(slides):
        body = f'<p class="sb">{rich(s["body"])}</p>' if s.get("body") else ""
        pts = "".join(f'<li>{icon("check",26,t["accent"],3)}<span>{rich(p)}</span></li>' for p in s.get("points", [])[:4])
        pts = f'<ul class="sp">{pts}</ul>' if pts else ""
        met = f'<div class="met">{icon("target",32,"#fff")}<span><b>Measure:</b> {rich(s["metric"])}</span></div>' if s.get("metric") else ""
        css = base + f""".num{{font-family:'Inter Display';font-weight:900;font-size:150px;line-height:.8;letter-spacing:-.06em;color:{t['accent']};opacity:.18}}
.sh{{display:flex;align-items:center;gap:24px;margin-top:18px}}
.sh h2{{font-family:'Inter Display';font-weight:800;font-size:68px;line-height:1.04;letter-spacing:-.035em;color:{t['ink']}}}
.sc{{margin-top:36px;padding:40px 44px;background:{t['card']};border:1px solid {t['line']};border-radius:28px;box-shadow:0 24px 60px -30px rgba(20,17,43,.35)}}
.sb{{font-size:38px;line-height:1.42;color:{t['ink']};font-weight:500}}
.sp{{list-style:none}}
.sb + .sp{{margin-top:22px}}
.sp li{{display:flex;gap:18px;align-items:flex-start;font-size:36px;line-height:1.35;font-weight:600;color:{t['ink']};padding:14px 0}}
.sp li svg{{flex:none;margin-top:6px}}
.met{{display:flex;gap:16px;align-items:center;margin-top:28px;padding:24px 28px;border-radius:20px;background:{t['accent']};color:#fff;font-size:29px;line-height:1.35;font-weight:600}}
.met b{{font-weight:800}}
.met svg{{flex:none}}"""
        ic = f'<div class="ico" style="width:84px;height:84px;background:{t["bg2"]};color:{t["accent"]}">{icon(s.get("icon","check"),42)}</div>'
        card_html = f'<div class="sc">{body}{pts}</div>' if (body or pts) else ""
        inner = prog(i + 2) + f'<div class="body"><div class="num">{i+1:02d}</div><div class="sh">{ic}<h2>{rich(s["head"])}</h2></div>{card_html}{met}</div>'
        pages.append(frame(t, inner, {**spec, "source": s.get("source", "")}, css, page=f"{i+2} / {total}"))
    # end
    end_css = base + f""".et{{font-family:'Inter Display';font-weight:900;font-size:84px;line-height:1.02;letter-spacing:-.045em}}
.eb{{font-size:38px;line-height:1.42;color:{t['ink']};margin-top:30px;font-weight:500}}
.fl{{display:inline-flex;align-items:center;gap:16px;margin-top:56px;background:linear-gradient(135deg,{t['accent']},{t['accent2']});color:#fff;font-weight:800;font-size:30px;padding:24px 34px;border-radius:999px}}"""
    eb = f'<div class="eb">{rich(spec["end_body"])}</div>' if spec.get("end_body") else ""
    inner = prog(total) + f'<div class="body"><div class="et">{rich(spec.get("end_title","What would you add?"))}</div>{eb}<div><div class="fl">{icon("users",32,"#fff")} Follow Merchly for more COD playbooks</div></div></div>'
    pages.append(frame(t, inner, {**spec, "source": ""}, end_css, page=f"{total} / {total}"))
    return pages


def shoot(pages_html, png_paths):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        except Exception:
            b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        for h, out in zip(pages_html, png_paths):
            pg.set_content(h, wait_until="load")
            pg.evaluate("document.fonts.ready")
            overflow = pg.evaluate(
                "(()=>{const b=document.querySelector('.body');const f=document.querySelector('.foot');"
                "if(!b||!f)return false;const r=[...b.querySelectorAll('*')].map(e=>e.getBoundingClientRect().bottom);"
                "return Math.max(0,...r) > f.getBoundingClientRect().top+1})()")
            pg.screenshot(path=out, clip={"x": 0, "y": 0, "width": W, "height": H})
            if overflow:
                print(f"WARNING: content overflows the footer in {out}; shorten the text", file=sys.stderr)
        b.close()


def main(spec_path, out_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    t = THEMES.get(spec.get("theme", "light"), THEMES["light"])
    typ = spec["type"]
    if typ in ("bars", "bignumber") and not spec.get("source"):
        raise SystemExit("bars/bignumber need a 'source' (real, cited data only)")
    if typ == "carousel":
        if not out_path.endswith(".pdf"):
            raise SystemExit("carousel output must end in .pdf")
        pages = carousel_pages(spec, t)
        pngs = [f"{out_path[:-4]}.p{i+1}.png" for i in range(len(pages))]
        shoot(pages, pngs)
        from PIL import Image
        ims = [Image.open(p).convert("RGB") for p in pngs]
        ims = [i.resize((W, H), Image.LANCZOS) for i in ims]
        ims[0].save(out_path, save_all=True, append_images=ims[1:], resolution=144, quality=90)
        ims[0].save(out_path[:-4] + ".cover.jpg", "JPEG", quality=90, optimize=True)
        import os
        for p in pngs:
            os.remove(p)
        return
    inner, css = TYPES[typ](spec, t)
    if out_path.lower().endswith((".jpg", ".jpeg")):
        tmp = out_path + ".tmp.png"
        shoot([frame(t, inner, spec, css)], [tmp])
        from PIL import Image
        import os
        Image.open(tmp).convert("RGB").save(out_path, "JPEG", quality=92, optimize=True, progressive=True, subsampling=0)
        os.remove(tmp)
    else:
        shoot([frame(t, inner, spec, css)], [out_path])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
