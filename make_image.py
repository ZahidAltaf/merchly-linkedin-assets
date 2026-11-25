#!/usr/bin/env python3
"""Merchly LinkedIn image generator (1080x1080 PNG, brand style).

Usage:
  python3 make_image.py spec.json out.png

spec.json shapes (pick one "type"):

  {"type": "workflow", "title": "How a COD order should move",
   "steps": ["Order placed", "Confirm call", "Dispatch", "Delivered"],
   "footer": "Profit Desk by Merchly"}

  {"type": "checklist", "title": "Before you ship a COD order",
   "items": ["Call the customer", "Check address", "..."],
   "footer": "Merchly"}

  {"type": "compare", "title": "Revenue vs real profit",
   "left_label": "What the dashboard says", "left": ["..."],
   "right_label": "What you actually keep", "right": ["..."],
   "footer": "Profit Desk by Merchly"}

  {"type": "statement", "kicker": "UNPOPULAR OPINION",
   "text": "COD is not the problem. Unconfirmed COD is.",
   "footer": "Merchly"}
  {"type": "bars", "title": "COD vs prepaid return rate",
   "bars": [{"label": "COD", "value": 37.5}, {"label": "Prepaid", "value": 5.3}],
   "unit": "%", "source": "Source: ClickPost India RTO data, 2026",
   "footer": "CODless by Merchly"}
   (2-6 bars; only real sourced numbers; "source" is required)

  {"type": "bignumber", "number": "7x", "text": "more COD parcels come back than prepaid ones",
   "source": "Source: ...", "footer": "Merchly"}

  {"type": "mythfact", "title": "COD myths we hear a lot",
   "pairs": [{"myth": "COD buyers are just careless", "fact": "Most refusals start with no confirmation call"}],
   "footer": "Merchly"}   (1-3 pairs)

  {"type": "grid", "title": "4 ways to cut refused parcels",
   "cells": [{"head": "Confirm", "body": "Call before you dispatch"}, ...],
   "footer": "Merchly"}   (exactly 4 cells)
"""
import json
import sys

from PIL import Image, ImageDraw, ImageFont

S = 1080
SCALE = 2
W = S * SCALE

PURPLE_A = (67, 56, 202)
PURPLE_B = (124, 58, 237)
DEEP = (46, 16, 101)
YELLOW = (250, 204, 21)
WHITE = (255, 255, 255)
SOFT = (226, 222, 255)
CARD = (255, 255, 255)
INK = (30, 27, 75)
MUTED = (91, 86, 140)

FONT_DIRS = [
    "/usr/share/fonts/truetype/google-fonts/",
    "/usr/share/fonts/truetype/poppins/",
]


def font(weight, size):
    names = {"bold": ["Poppins-Bold.ttf", "DejaVuSans-Bold.ttf"],
             "medium": ["Poppins-Medium.ttf", "DejaVuSans.ttf"],
             "regular": ["Poppins-Regular.ttf", "DejaVuSans.ttf"]}[weight]
    for d in FONT_DIRS + ["/usr/share/fonts/truetype/dejavu/"]:
        for n in names:
            try:
                return ImageFont.truetype(d + n, size * SCALE)
            except OSError:
                pass
    return ImageFont.load_default()


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def background():
    img = Image.new("RGBA", (W, W))
    d = ImageDraw.Draw(img)
    for i in range(2 * W):
        t = i / (2 * W)
        c = tuple(int(PURPLE_A[k] + (PURPLE_B[k] - PURPLE_A[k]) * t) for k in range(3)) + (255,)
        d.line([(i, 0), (0, i)], fill=c, width=3)
    ov = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    o = ImageDraw.Draw(ov)
    o.ellipse([-W * 0.35, -W * 0.35, W * 0.45, W * 0.45], fill=(255, 255, 255, 16))
    o.ellipse([W * 0.6, W * 0.65, W * 1.4, W * 1.45], fill=(255, 255, 255, 12))
    img.alpha_composite(ov)
    return img


def header(d, title, y=90):
    f = font("bold", 56)
    lines = wrap(d, title, f, W - 2 * 90 * SCALE)
    yy = y * SCALE
    for ln in lines:
        d.text((90 * SCALE, yy), ln, font=f, fill=WHITE)
        yy += int(70 * SCALE)
    d.ellipse([90 * SCALE, yy + 14 * SCALE, 90 * SCALE + 22 * SCALE, yy + 36 * SCALE], fill=YELLOW)
    return yy + 70 * SCALE


def footer(d, text):
    f = font("medium", 28)
    tw = d.textlength(text, font=f)
    x = W - 90 * SCALE - tw
    y = W - 95 * SCALE
    d.ellipse([x - 34 * SCALE, y + 10 * SCALE, x - 14 * SCALE, y + 30 * SCALE], fill=YELLOW)
    d.text((x, y), text, font=f, fill=SOFT)


def card(d, box, r=28):
    d.rounded_rectangle([int(v * SCALE) for v in box], radius=r * SCALE, fill=CARD)


def render_workflow(d, spec, top):
    steps = spec["steps"][:6]
    n = len(steps)
    f = font("bold", 34)
    fn = font("bold", 30)
    avail = (S - 110) - top / SCALE - 40
    gap = 26
    h = min(120, (avail - gap * (n - 1)) / n)
    y = top / SCALE
    for i, s in enumerate(steps):
        card(d, [90, y, S - 90, y + h])
        cx, cy = 90 + 30 + 32, y + h / 2
        d.ellipse([(cx - 32) * SCALE, (cy - 32) * SCALE, (cx + 32) * SCALE, (cy + 32) * SCALE], fill=PURPLE_B)
        num = str(i + 1)
        nw = d.textlength(num, font=fn)
        d.text((cx * SCALE - nw / 2, (cy - 22) * SCALE), num, font=fn, fill=WHITE)
        lines = wrap(d, s, f, (S - 90 - 30 - (cx + 50)) * SCALE)[:2]
        lh = 44
        ty = cy - lh * len(lines) / 2
        for ln in lines:
            d.text(((cx + 50) * SCALE, ty * SCALE), ln, font=f, fill=INK)
            ty += lh
        if i < n - 1:
            ax = cx
            d.polygon([((ax - 12) * SCALE, (y + h + 4) * SCALE), ((ax + 12) * SCALE, (y + h + 4) * SCALE),
                       (ax * SCALE, (y + h + gap - 4) * SCALE)], fill=YELLOW)
        y += h + gap


def render_checklist(d, spec, top):
    items = spec["items"][:7]
    f = font("medium", 36 if len(items) <= 5 else 32)
    y = top / SCALE
    est = 40
    for it in items:
        est += max(46 * len(wrap(d, it, f, (S - 90 - 40 - 194) * SCALE)[:2]), 52) + 30
    card(d, [90, y, S - 90, min(S - 140, y + est + 10)])
    y += 40
    for it in items:
        bx, by = 130, y + 4
        d.rounded_rectangle([bx * SCALE, by * SCALE, (bx + 40) * SCALE, (by + 40) * SCALE], radius=10 * SCALE, fill=PURPLE_B)
        d.line([((bx + 9) * SCALE, (by + 21) * SCALE), ((bx + 17) * SCALE, (by + 30) * SCALE),
                ((bx + 31) * SCALE, (by + 11) * SCALE)], fill=WHITE, width=6 * SCALE)
        lines = wrap(d, it, f, (S - 90 - 40 - (bx + 64)) * SCALE)[:2]
        ty = y
        for ln in lines:
            d.text(((bx + 64) * SCALE, ty * SCALE), ln, font=f, fill=INK)
            ty += 46
        y = max(ty, y + 52) + 30


def render_compare(d, spec, top):
    fl = font("bold", 32)
    fi = font("medium", 30)
    y0 = top / SCALE
    colw = (S - 180 - 30) / 2
    def col_h(label, items):
        h = 30 + 42 * len(wrap(d, label, fl, (colw - 60) * SCALE)[:2]) + 34
        for it in items[:6]:
            h += 40 * len(wrap(d, it, fi, (colw - 90) * SCALE)[:3]) + 20
        return h + 20
    bottom = min(S - 140, y0 + max(col_h(spec["left_label"], spec["left"]), col_h(spec["right_label"], spec["right"])))
    for j, (label, items, accent) in enumerate([(spec["left_label"], spec["left"], (220, 38, 38)),
                                                 (spec["right_label"], spec["right"], (22, 163, 74))]):
        x0 = 90 + j * (colw + 30)
        card(d, [x0, y0, x0 + colw, bottom])
        ly = y0 + 30
        for ln in wrap(d, label, fl, (colw - 60) * SCALE)[:2]:
            d.text(((x0 + 30) * SCALE, ly * SCALE), ln, font=fl, fill=INK)
            ly += 42
        d.line([((x0 + 30) * SCALE, (ly + 10) * SCALE), ((x0 + colw - 30) * SCALE, (ly + 10) * SCALE)], fill=SOFT, width=3 * SCALE)
        ly += 34
        for it in items[:6]:
            d.ellipse([((x0 + 30) * SCALE), ((ly + 12) * SCALE), ((x0 + 44) * SCALE), ((ly + 26) * SCALE)], fill=accent)
            for ln in wrap(d, it, fi, (colw - 90) * SCALE)[:3]:
                d.text(((x0 + 58) * SCALE, ly * SCALE), ln, font=fi, fill=MUTED)
                ly += 40
            ly += 20


def render_statement(d, spec):
    fk = font("bold", 30)
    ft = font("bold", 68)
    kicker = spec.get("kicker", "")
    lines = wrap(d, spec["text"], ft, W - 2 * 110 * SCALE)[:6]
    total = len(lines) * 86 + (70 if kicker else 0)
    y = (S - total) / 2 - 30
    if kicker:
        kw = d.textlength(kicker, font=fk)
        d.rounded_rectangle([110 * SCALE, y * SCALE, 110 * SCALE + kw + 48 * SCALE, (y + 52) * SCALE], radius=26 * SCALE, fill=YELLOW)
        d.text((134 * SCALE, (y + 6) * SCALE), kicker, font=fk, fill=DEEP)
        y += 90
    for ln in lines:
        d.text((110 * SCALE, y * SCALE), ln, font=ft, fill=WHITE)
        y += 86


GREEN = (22, 163, 74)
RED = (220, 38, 38)


def source_line(d, text):
    if not text:
        return
    f = font("regular", 22)
    d.text((90 * SCALE, (S - 95) * SCALE), text, font=f, fill=SOFT)


def render_bars(d, spec, top):
    bars = spec["bars"][:6]
    unit = spec.get("unit", "")
    vmax = max(b["value"] for b in bars) or 1
    y0 = top / SCALE
    fl = font("bold", 30)
    fv = font("bold", 34)
    n = len(bars)
    inner_top = y0 + 40
    row = min(130, ((S - 190) - inner_top) / n)
    card(d, [90, y0, S - 90, inner_top + row * n + 30])
    bh = min(64, row * 0.55)
    label_w = 210
    x_start = 130 + label_w
    x_end = S - 130 - 120
    for i, b in enumerate(bars):
        cy = inner_top + row * i + row / 2
        lines = wrap(d, b["label"], fl, label_w * SCALE)[:2]
        ly = cy - 20 * len(lines)
        for ln in lines:
            d.text((130 * SCALE, ly * SCALE), ln, font=fl, fill=INK)
            ly += 40
        w = max(8, (x_end - x_start) * b["value"] / vmax)
        col = PURPLE_B if i % 2 == 0 else (99, 102, 241)
        if b.get("highlight"):
            col = YELLOW
        d.rounded_rectangle([x_start * SCALE, (cy - bh / 2) * SCALE, (x_start + w) * SCALE, (cy + bh / 2) * SCALE], radius=12 * SCALE, fill=col)
        val = (str(b["value"]).rstrip("0").rstrip(".") if isinstance(b["value"], float) else str(b["value"])) + unit
        d.text(((x_start + w + 16) * SCALE, (cy - 22) * SCALE), val, font=fv, fill=INK)


def render_bignumber(d, spec):
    fn = font("bold", 220)
    ft = font("bold", 50)
    num = spec["number"]
    nw = d.textlength(num, font=fn)
    lines = wrap(d, spec["text"], ft, W - 2 * 110 * SCALE)[:4]
    total = 250 + 64 * len(lines)
    y = (S - total) / 2 - 40
    d.text(((W - nw) / 2, y * SCALE), num, font=fn, fill=YELLOW)
    y += 270
    for ln in lines:
        lw = d.textlength(ln, font=ft)
        d.text(((W - lw) / 2, y * SCALE), ln, font=ft, fill=WHITE)
        y += 64


def render_mythfact(d, spec, top):
    pairs = spec["pairs"][:3]
    fk = font("bold", 24)
    ft = font("medium", 30)
    y = top / SCALE
    avail = (S - 150) - y
    gap = 22
    h = (avail - gap * (len(pairs) - 1)) / len(pairs)
    for p in pairs:
        card(d, [90, y, S - 90, y + h])
        half = h / 2
        for k, (tag, txt, col) in enumerate([("MYTH", p["myth"], RED), ("FACT", p["fact"], GREEN)]):
            yy = y + half * k
            tw = d.textlength(tag, font=fk)
            d.rounded_rectangle([120 * SCALE, (yy + half / 2 - 20) * SCALE, 120 * SCALE + tw + 32 * SCALE, (yy + half / 2 + 20) * SCALE], radius=20 * SCALE, fill=col)
            d.text((136 * SCALE, (yy + half / 2 - 15) * SCALE), tag, font=fk, fill=WHITE)
            lines = wrap(d, txt, ft, (S - 90 - 30 - 250) * SCALE)[:2]
            ly = yy + half / 2 - 20 * len(lines)
            for ln in lines:
                d.text((250 * SCALE, ly * SCALE), ln, font=ft, fill=INK if k else MUTED)
                ly += 40
        d.line([(120 * SCALE, (y + half) * SCALE), ((S - 120) * SCALE, (y + half) * SCALE)], fill=SOFT, width=2 * SCALE)
        y += h + gap


def render_grid(d, spec, top):
    cells = spec["cells"][:4]
    fh = font("bold", 34)
    fb = font("medium", 27)
    y0 = top / SCALE
    gap = 24
    cw = (S - 180 - gap) / 2
    ch = ((S - 150) - y0 - gap) / 2
    for i, c in enumerate(cells):
        x = 90 + (i % 2) * (cw + gap)
        y = y0 + (i // 2) * (ch + gap)
        card(d, [x, y, x + cw, y + ch])
        d.ellipse([(x + 28) * SCALE, (y + 28) * SCALE, (x + 76) * SCALE, (y + 76) * SCALE], fill=PURPLE_B)
        num = str(i + 1)
        f2 = font("bold", 28)
        nw = d.textlength(num, font=f2)
        d.text(((x + 52) * SCALE - nw / 2, (y + 32) * SCALE), num, font=f2, fill=WHITE)
        ty = y + 96
        for ln in wrap(d, c["head"], fh, (cw - 56) * SCALE)[:2]:
            d.text(((x + 28) * SCALE, ty * SCALE), ln, font=fh, fill=INK)
            ty += 44
        ty += 6
        for ln in wrap(d, c["body"], fb, (cw - 56) * SCALE)[:4]:
            d.text(((x + 28) * SCALE, ty * SCALE), ln, font=fb, fill=MUTED)
            ty += 38


def main(spec_path, out_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    img = background()
    d = ImageDraw.Draw(img)
    t = spec["type"]
    if t == "statement":
        render_statement(d, spec)
    elif t == "bignumber":
        render_bignumber(d, spec)
    else:
        top = header(d, spec["title"])
        {"workflow": render_workflow, "checklist": render_checklist, "compare": render_compare,
         "bars": render_bars, "mythfact": render_mythfact, "grid": render_grid}[t](d, spec, top)
    if t in ("bars", "bignumber") and not spec.get("source"):
        raise SystemExit("bars/bignumber need a 'source' (real, cited data only)")
    source_line(d, spec.get("source", ""))
    footer(d, spec.get("footer", "Merchly"))
    img.resize((S, S), Image.LANCZOS).convert("RGB").save(out_path, optimize=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
