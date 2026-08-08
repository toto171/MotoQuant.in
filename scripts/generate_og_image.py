#!/usr/bin/env python3
"""Generate the MotoQuant Pro Open Graph / social-share card.

Renders web/public/og-image.png at 1200x630 (the canonical OG size) with the
brand identity: near-black cockpit background, the "MotoQuant Pro" wordmark,
the "The physics of faster" tagline, brand-orange accents, and the canonical
catalog stats. Re-runnable and deterministic — running it again reproduces the
same PNG byte-for-byte (modulo Pillow version), which is exactly what the
headline-stats auditor's og_image_stale mtime check wants after a stats change.

Usage
-----
    pip install pillow --break-system-packages    # only dependency
    python3 scripts/generate_og_image.py           # writes web/public/og-image.png
    python3 scripts/generate_og_image.py --out /tmp/preview.png

When the canonical stats change, edit STATS below (or, better, keep them in sync
with scripts/audit_headline_stats.py's source-of-truth) and re-run.

Fallbacks
---------
Fonts are resolved from a list of common locations; if none are found Pillow's
built-in bitmap font is used (the card still renders, just less polished). If
Pillow itself is unavailable the script prints an SVG fallback path and exits
non-zero with a clear message (PNG conversion then needs an external tool such
as rsvg-convert or Inkscape).
"""

from __future__ import annotations

import argparse
import os
import sys

# ---------------------------------------------------------------------------
# Brand + content constants (single source of truth for the card)
# ---------------------------------------------------------------------------
W, H = 1200, 630

# Brand palette — mirrors web/tailwind.config.js `theme.extend.colors.brand/ink`.
INK_0 = (0, 0, 0)
INK_1 = (10, 10, 11)
INK_2 = (17, 17, 19)
INK_3 = (26, 26, 29)
ORANGE = (255, 94, 31)  # brand-orange  #FF5E1F
ORANGE_DEEP = (204, 64, 0)  # brand-orangeDeep #CC4000
ACCENT = (0, 255, 178)  # brand-accent  #00FFB2
WHITE = (255, 255, 255)
WHITE_70 = (200, 200, 205)
WHITE_45 = (150, 150, 156)

TITLE = "MotoQuant Pro"
TAGLINE = "The physics of faster"
DOMAIN = "motoquant.in"

# Canonical catalog stats. Keep in sync with scripts/audit_headline_stats.py.
# (2026-08-08: the benchmark tile had sat at 221 — the July-6 count — through
# two corpus epochs because nothing audited the rendered card's numbers.)
STATS = [
    ("541", "bikes"),
    ("593", "parts"),
    ("254", "tires"),
    ("20", "venues"),
    ("250", "benchmarks"),
]

# Font search paths (display = geometric bold, mono = stats/labels).
_DISPLAY_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/poppins/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
_DISPLAY_MED_CANDIDATES = [
    "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
_MONO_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "C:/Windows/Fonts/consolab.ttf",
]
_MONO_REG_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "C:/Windows/Fonts/consola.ttf",
]


def _first_existing(paths):
    for p in paths:
        if os.path.isfile(p):
            return p
    return None


def _font(candidates, size, ImageFont):
    path = _first_existing(candidates)
    if path is None:
        return ImageFont.load_default()
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _text_w(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def build(out_path: str) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        sys.stderr.write(
            "Pillow not installed. Install with:\n"
            "    pip install pillow --break-system-packages\n"
            "or render og-image.svg (see scripts/) and convert to PNG with "
            "rsvg-convert / Inkscape.\n"
        )
        sys.exit(2)

    img = Image.new("RGB", (W, H), INK_0)
    draw = ImageDraw.Draw(img)

    # --- Vertical near-black gradient (ink-1 top -> ink-0 bottom) ---------
    for y in range(H):
        t = y / (H - 1)
        r = int(INK_1[0] + (INK_0[0] - INK_1[0]) * t)
        g = int(INK_1[1] + (INK_0[1] - INK_1[1]) * t)
        b = int(INK_1[2] + (INK_0[2] - INK_1[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # --- Soft orange glow in the lower-right (cockpit dial vibe) ----------
    glow = Image.new("RGB", (W, H), INK_0)
    gdraw = ImageDraw.Draw(glow)
    cx, cy, maxr = int(W * 0.84), int(H * 0.78), 360
    for rad in range(maxr, 0, -6):
        a = (1 - rad / maxr) ** 2 * 0.30
        col = (int(ORANGE[0] * a), int(ORANGE[1] * a), int(ORANGE[2] * a))
        gdraw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=col)
    img = Image.blend(img, glow, 0.6)
    draw = ImageDraw.Draw(img)

    # --- Fonts ------------------------------------------------------------
    f_title = _font(_DISPLAY_BOLD_CANDIDATES, 96, ImageFont)
    f_tag = _font(_DISPLAY_MED_CANDIDATES, 40, ImageFont)
    f_kicker = _font(_MONO_CANDIDATES, 24, ImageFont)
    f_stat_num = _font(_MONO_CANDIDATES, 46, ImageFont)
    f_stat_lbl = _font(_MONO_REG_CANDIDATES, 20, ImageFont)
    f_domain = _font(_MONO_CANDIDATES, 26, ImageFont)

    margin = 80

    # --- Top brand bar accent + kicker -----------------------------------
    draw.rectangle([0, 0, W, 6], fill=ORANGE)
    kicker = "FIRST-PRINCIPLES DRAG-RACING PHYSICS ENGINE"
    draw.text((margin, 70), kicker, font=f_kicker, fill=ACCENT)

    # --- Title ------------------------------------------------------------
    title_y = 150
    draw.text((margin, title_y), TITLE, font=f_title, fill=WHITE)
    # accent underbar beneath the wordmark
    tw = _text_w(draw, TITLE, f_title)
    draw.rectangle(
        [margin, title_y + 118, margin + min(tw, 560), title_y + 126], fill=ORANGE
    )

    # --- Tagline ----------------------------------------------------------
    draw.text((margin, title_y + 150), TAGLINE, font=f_tag, fill=WHITE_70)

    # --- Stats strip (timing-board tiles) --------------------------------
    strip_y = 440
    gap = 24
    n = len(STATS)
    tile_w = (W - 2 * margin - gap * (n - 1)) // n
    tile_h = 110
    for i, (num, lbl) in enumerate(STATS):
        x0 = margin + i * (tile_w + gap)
        x1 = x0 + tile_w
        y0, y1 = strip_y, strip_y + tile_h
        draw.rectangle([x0, y0, x1, y1], fill=INK_2, outline=(40, 40, 44), width=1)
        draw.rectangle([x0, y0, x1, y0 + 3], fill=ORANGE)  # top accent line
        nw = _text_w(draw, num, f_stat_num)
        draw.text((x0 + (tile_w - nw) / 2, y0 + 22), num, font=f_stat_num, fill=ORANGE)
        lw = _text_w(draw, lbl.upper(), f_stat_lbl)
        draw.text(
            (x0 + (tile_w - lw) / 2, y0 + 76),
            lbl.upper(),
            font=f_stat_lbl,
            fill=WHITE_45,
        )

    # --- Footer domain ----------------------------------------------------
    draw.text((margin, H - 56), DOMAIN, font=f_domain, fill=WHITE_45)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    print("wrote %s (%dx%d)" % (out_path, W, H))


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    default_out = os.path.normpath(
        os.path.join(here, "..", "web", "public", "og-image.png")
    )
    ap = argparse.ArgumentParser(
        description="Generate the MotoQuant Pro OG card (1200x630)."
    )
    ap.add_argument(
        "--out",
        default=default_out,
        help="output PNG path (default: web/public/og-image.png)",
    )
    args = ap.parse_args()
    build(args.out)


if __name__ == "__main__":
    main()
