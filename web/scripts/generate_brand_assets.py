"""
Generate MotoQuant brand assets: favicon set + OG preview image.

Outputs (written to web/public/):
  - favicon.ico            (16 + 32 + 48 bundled)
  - favicon-16x16.png
  - favicon-32x32.png
  - favicon-48x48.png
  - apple-touch-icon.png   (180x180, for iOS home screen + iMessage previews)
  - icon-192.png           (Android / PWA)
  - icon-512.png           (Android / PWA / high-res)
  - icon.svg               (scalable source)
  - site.webmanifest       (PWA manifest)

og-image.png is NOT written here — scripts/audit_headline_stats.py owns it
(single ownership; its card is evergreen by design, July 2026).
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------------------
# Brand tokens (IGNITION v5 — MotoQuant_Identity_Kit + web/tailwind.config.js)
# ----------------------------------------------------------------------------
ORANGE = "#FF5E1F"  # Signal (identity kit)
ORANGE_LIGHT = "#FF8F57"
ORANGE_DEEP = "#CC4000"
ACCENT_MINT = "#00FFB2"
CARBON = "#0A0A0B"  # Ink (identity kit)
INK_2 = "#111113"
INK_3 = "#1A1A1D"
INK_4 = "#27272A"
WHITE = "#FFFFFF"
WHITE_DIM = "#D4D4D7"
WHITE_SUB = "#8A8A90"


def _first_font(*candidates: str) -> str:
    """Return the first font path that exists (containers vary in font sets)."""
    for c in candidates:
        if Path(c).exists():
            return c
    raise FileNotFoundError(f"No usable font among: {candidates}")


FONT_BOLD_IT = _first_font(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf",
)
FONT_BOLD = _first_font(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
)
FONT_COND_B = _first_font(
    "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
)
FONT_MONO_B = _first_font(
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
)
FONT_MONO = _first_font(
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
)
FONT_REGULAR = _first_font(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
)

# Resolve relative to this script so the generator works from any checkout
# (the old hardcoded sandbox mount path broke everywhere else).
OUT_DIR = Path(__file__).resolve().parent.parent / "public"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------------
# Logo mark: the identity kit "redline Q" (MotoQuant_Identity_Kit, July 2026).
# Heavyweight dial ring, 30-degree sector gap at 315, tapered needle that
# accelerates outward through the gap, hub dot at large sizes (the kit app
# icon drops the hub below 64px). Geometry lifted from the kit SVGs verbatim
# and scaled from the 512 reference frame. Rendered supersampled 4x.
# ----------------------------------------------------------------------------


def render_mark(size: int, *, include_accents: bool = True) -> Image.Image:
    """Render the redline-Q app icon at the given pixel size.

    include_accents toggles the hub dot (kept for API compatibility; the
    ring + needle always render — they ARE the mark).
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = size / 512.0  # kit app-icon reference frame

    # Ink rounded square
    radius = max(2, int(112 * k))
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=CARBON)

    # Dial: white annulus, center (256, 263.6), r_out 153.6, r_in 107.52
    cx, cy = 256 * k, 263.6 * k
    r_out, r_in = 153.6 * k, 107.52 * k
    d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill="#FFFFFF")
    d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=CARBON)
    # 30-degree gap centered on the 315 axis (PIL angles: y-down, from 3 o'clock)
    gap_r = r_out * 1.25
    d.pieslice([cx - gap_r, cy - gap_r, cx + gap_r, cy + gap_r], -60, -30, fill=CARBON)

    # Needle — tapered quad, exact kit coordinates (512 frame)
    quad = [(296.89, 240.25), (397.22, 152.95), (392.58, 95.69), (278.97, 222.33)]
    d.polygon([(x * k, y * k) for x, y in quad], fill=ORANGE)

    # Hub dot — only at sizes where it survives (the kit's full mark has it,
    # the app icon drops it; we keep it for >=128px renders)
    if include_accents and size >= 128:
        hub_r = 13.6 * k
        d.ellipse([cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r], fill=ORANGE)

    return img


def render_mark_hires(size: int) -> Image.Image:
    """Downscale from a 4× master for extra sharpness."""
    master = render_mark(size * 4, include_accents=(size >= 128))
    return master.resize((size, size), Image.LANCZOS)


# ----------------------------------------------------------------------------
# SVG source — the identity kit app icon VERBATIM (its README nominates it
# as the drop-in replacement for web/public/icon.svg).
# ----------------------------------------------------------------------------
ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512"><rect width="512" height="512" rx="112" fill="#0A0A0B"/><path d="M 389.02 186.42 A 153.6 153.6 0 1 1 332.80 130.20 L 309.76 170.10 A 107.52 107.52 0 1 0 349.12 209.46 Z" fill="#FFFFFF"/><path d="M 296.89 240.25 L 397.22 152.95 L 392.58 95.69 L 278.97 222.33 Z" fill="#FF5E1F"/></svg>"""


# ----------------------------------------------------------------------------
# OG image: 1200x630, brand-consistent, with live project numbers.
# Layout: left = brand lockup + tagline + stat strip, right = v(t) curve card.
# ----------------------------------------------------------------------------
def draw_grid(
    d: ImageDraw.ImageDraw, w: int, h: int, color=(255, 255, 255, 10), step: int = 60
) -> None:
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=color, width=1)
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=color, width=1)


def hex_rgba(hexcode: str, alpha: int = 255) -> tuple:
    hexcode = hexcode.lstrip("#")
    r, g, b = int(hexcode[:2], 16), int(hexcode[2:4], 16), int(hexcode[4:6], 16)
    return (r, g, b, alpha)


def velocity_curve_points(t_total=12.0, v_trap_kmh=240.0, samples=180):
    """Return [(t, v_kmh), ...] for a plausible GSX-R K5 quarter-mile v(t)."""
    import math

    pts = []
    v_trap_ms = v_trap_kmh / 3.6
    # Classic drag-racing profile: big launch accel, tapering toward trap.
    # v(t) = v_trap * (1 - exp(-t/tau)) + small noise-free early-launch bump
    tau = 3.2
    for i in range(samples):
        t = i * (t_total / (samples - 1))
        v_ms = v_trap_ms * (1.0 - math.exp(-t / tau))
        # Gear-shift micro-plateaus
        for shift_t, shift_dur in [(1.8, 0.12), (3.4, 0.12), (5.2, 0.12), (7.6, 0.12)]:
            if shift_t <= t <= shift_t + shift_dur:
                v_ms *= 0.995
        pts.append((t, v_ms * 3.6))
    return pts


def render_og_image(path: Path) -> None:
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), hex_rgba(CARBON)[:3])
    d = ImageDraw.Draw(img, "RGBA")

    # Subtle carbon grid with orange accent lines at specific cols
    draw_grid(d, W, H, color=(255, 255, 255, 9), step=60)
    for x in (60, 300, 540, 720, 900, 1140):
        d.line([(x, 0), (x, H)], fill=(255, 94, 31, 14), width=1)

    # Left rail — signal orange vertical accent
    d.rectangle([60, 90, 66, 540], fill=ORANGE)

    # ----- Left side: brand lockup -----
    pill_font = ImageFont.truetype(FONT_MONO_B, 22)
    pill_text = "Proudly Built in India"
    pill_bbox = d.textbbox((0, 0), pill_text, font=pill_font)
    pill_w = pill_bbox[2] - pill_bbox[0] + 72
    pill_h = 48
    pill_x, pill_y = 110, 90
    d.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=pill_h // 2,
        fill=(0, 0, 0, 0),
        outline=(255, 255, 255, 60),
        width=1,
    )
    # pill dot
    d.ellipse(
        [pill_x + 16, pill_y + pill_h // 2 - 6, pill_x + 28, pill_y + pill_h // 2 + 6],
        fill=ORANGE,
    )
    d.text(
        (pill_x + 38, pill_y + 11), pill_text, font=pill_font, fill=hex_rgba(WHITE_DIM)
    )

    # Wordmark: "Moto" orange, "Quant" white. Sized to fit in ~600px of
    # left column without crowding the simulation card at x≈720.
    wm_font = ImageFont.truetype(FONT_BOLD, 92)
    wm_y = 180
    moto_text = "Moto"
    quant_text = "Quant"
    moto_w = d.textbbox((0, 0), moto_text, font=wm_font)[2]
    d.text((110, wm_y), moto_text, font=wm_font, fill=ORANGE)
    d.text((110 + moto_w, wm_y), quant_text, font=wm_font, fill=WHITE)

    # Tagline
    tag_font = ImageFont.truetype(FONT_BOLD, 30)
    d.text(
        (110, 295), "The Physics of Faster", font=tag_font, fill=hex_rgba(WHITE, 230)
    )

    # Subline — trimmed so it fits in the left column
    sub_font = ImageFont.truetype(FONT_REGULAR, 20)
    d.text(
        (110, 338),
        "Quarter-mile simulation  ·  250 validated benchmarks",
        font=sub_font,
        fill=hex_rgba(WHITE_SUB, 255),
    )

    # Stat strip — 4 stats (dropped 'tires' for horizontal budget).
    # NOTE: scripts/audit_headline_stats.py --regen-og owns the live
    # og-image.png; these values are the fallback and must track it.
    stats = [
        ("541", "bikes"),
        ("593", "parts"),
        ("20", "venues"),
        ("4393", "tests"),
    ]
    stat_x = 110
    stat_y = 420
    stat_num_font = ImageFont.truetype(FONT_BOLD, 46)
    stat_lbl_font = ImageFont.truetype(FONT_MONO, 15)
    for num, lbl in stats:
        n_bbox = d.textbbox((0, 0), num, font=stat_num_font)
        n_w = n_bbox[2] - n_bbox[0]
        d.text((stat_x, stat_y), num, font=stat_num_font, fill=ORANGE)
        d.text(
            (stat_x, stat_y + 58),
            lbl.upper(),
            font=stat_lbl_font,
            fill=hex_rgba(WHITE_SUB),
        )
        stat_x += max(n_w + 42, 120)

    # ----- Right side: v(t) simulation card -----
    card_x, card_y, card_w, card_h = 720, 90, 420, 450
    card_r = 18

    # Card background with subtle orange glow border
    card_bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(card_bg)
    cdraw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=card_r,
        fill=(17, 17, 19, 255),
        outline=(255, 94, 31, 120),
        width=2,
    )
    img.paste(Image.alpha_composite(img.convert("RGBA"), card_bg).convert("RGB"))
    d = ImageDraw.Draw(img, "RGBA")

    # Card header
    hdr_font = ImageFont.truetype(FONT_MONO, 18)
    d.text(
        (card_x + 24, card_y + 20),
        "GSX-R 1000 K5  —  v(t) simulation",
        font=hdr_font,
        fill=hex_rgba(WHITE_SUB),
    )

    # Plot area inside card
    plot_x1 = card_x + 60
    plot_y1 = card_y + 70
    plot_x2 = card_x + card_w - 30
    plot_y2 = card_y + card_h - 80

    # Plot grid
    for i in range(7):
        gy = plot_y1 + i * (plot_y2 - plot_y1) // 6
        d.line([(plot_x1, gy), (plot_x2, gy)], fill=(255, 255, 255, 15), width=1)
    for i in range(7):
        gx = plot_x1 + i * (plot_x2 - plot_x1) // 6
        d.line([(gx, plot_y1), (gx, plot_y2)], fill=(255, 255, 255, 15), width=1)

    # Axis labels
    axis_font = ImageFont.truetype(FONT_MONO, 14)
    # y-axis (km/h) — 0, 60, 120, 180, 240
    for i, v in enumerate([240, 180, 120, 60]):
        gy = plot_y1 + i * (plot_y2 - plot_y1) // 4
        d.text(
            (plot_x1 - 44, gy - 9),
            f"{v:>3d}",
            font=axis_font,
            fill=hex_rgba(WHITE_SUB, 200),
        )
    # x-axis (time)
    d.text(
        (plot_x1 - 6, plot_y2 + 10), "0", font=axis_font, fill=hex_rgba(WHITE_SUB, 200)
    )
    d.text(
        (plot_x2 - 24, plot_y2 + 10),
        "12s",
        font=axis_font,
        fill=hex_rgba(WHITE_SUB, 200),
    )

    # Curve
    pts = velocity_curve_points()
    t_max = 12.0
    v_max = 245.0
    px = [
        (
            plot_x1 + (t / t_max) * (plot_x2 - plot_x1),
            plot_y2 - (v / v_max) * (plot_y2 - plot_y1),
        )
        for t, v in pts
    ]

    # Fill under curve
    fill_poly = px + [(plot_x2, plot_y2), (plot_x1, plot_y2)]
    d.polygon(fill_poly, fill=(255, 94, 31, 40))

    # Line
    for i in range(len(px) - 1):
        d.line([px[i], px[i + 1]], fill=ORANGE, width=3)

    # ET marker at quarter-mile (t ≈ 10.03s, v ≈ 239 km/h)
    et_t = 10.03
    et_v = 239.0
    et_x = plot_x1 + (et_t / t_max) * (plot_x2 - plot_x1)
    et_y = plot_y2 - (et_v / v_max) * (plot_y2 - plot_y1)
    # vertical dashed line
    dash_len = 6
    y = plot_y1
    while y < plot_y2:
        d.line(
            [(et_x, y), (et_x, min(y + dash_len, plot_y2))],
            fill=(255, 94, 31, 200),
            width=1,
        )
        y += dash_len * 2
    # dot
    d.ellipse([et_x - 7, et_y - 7, et_x + 7, et_y + 7], fill=ORANGE)
    d.ellipse([et_x - 3, et_y - 3, et_x + 3, et_y + 3], fill=WHITE)

    # ET callout pill
    call_font = ImageFont.truetype(FONT_MONO_B, 16)
    call_text = "10.03s  ·  239 km/h"
    c_bbox = d.textbbox((0, 0), call_text, font=call_font)
    c_w = c_bbox[2] - c_bbox[0] + 24
    c_h = 30
    c_x = min(et_x + 14, plot_x2 - c_w)
    c_y = et_y - 36
    d.rounded_rectangle(
        [c_x, c_y, c_x + c_w, c_y + c_h],
        radius=c_h // 2,
        fill=CARBON,
        outline=ORANGE,
        width=1,
    )
    d.text((c_x + 12, c_y + 6), call_text, font=call_font, fill=ORANGE)

    # Bottom-right domain pill
    dom_font = ImageFont.truetype(FONT_MONO_B, 18)
    dom_text = "motoquant.in"
    d_bbox = d.textbbox((0, 0), dom_text, font=dom_font)
    d_w = d_bbox[2] - d_bbox[0] + 40
    d_h = 42
    d_x = W - d_w - 40
    d_y = H - d_h - 40
    d.rounded_rectangle(
        [d_x, d_y, d_x + d_w, d_y + d_h],
        radius=d_h // 2,
        fill=(0, 0, 0, 0),
        outline=(255, 255, 255, 70),
        width=1,
    )
    d.text((d_x + 20, d_y + 11), dom_text, font=dom_font, fill=hex_rgba(WHITE_DIM))

    # Bottom-left tagline chip
    bl_font = ImageFont.truetype(FONT_MONO, 16)
    d.text(
        (110, 585), "The physics of faster", font=bl_font, fill=hex_rgba(WHITE_SUB, 220)
    )

    img.save(path, "PNG", optimize=True)


# ----------------------------------------------------------------------------
# Web manifest
# ----------------------------------------------------------------------------
WEBMANIFEST = """{
  "name": "MotoQuant Pro",
  "short_name": "MotoQuant",
  "description": "First-principles physics simulation for quarter-mile drag racing.",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "theme_color": "#FF5E1F",
  "background_color": "#0A0A0B",
  "display": "standalone",
  "start_url": "/"
}
"""


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main() -> None:
    # SVG icon source
    (OUT_DIR / "icon.svg").write_text(ICON_SVG, encoding="utf-8")

    # PNG favicons — render each at its native size via 4× downscale
    sizes = {
        "favicon-16x16.png": 16,
        "favicon-32x32.png": 32,
        "favicon-48x48.png": 48,
        "apple-touch-icon.png": 180,
        "icon-192.png": 192,
        "icon-512.png": 512,
    }
    rasters = {}
    for name, px in sizes.items():
        img = render_mark_hires(px)
        out = OUT_DIR / name
        img.save(out, "PNG", optimize=True)
        rasters[px] = img
        print(f"wrote {out.name} ({px}x{px})")

    # favicon.ico — bundle 16/32/48 for legacy browsers + Google
    ico_path = OUT_DIR / "favicon.ico"
    rasters[16].save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"wrote {ico_path.name}")

    # App-directory copies — Next.js app-router picks these up automatically.
    # Putting the mark there ensures the root /icon and /apple-icon endpoints
    # resolve to the brand mark without extra metadata wiring.
    app_dir = OUT_DIR.parent / "app"
    rasters[192].save(app_dir / "icon.png", "PNG", optimize=True)
    rasters[180].save(app_dir / "apple-icon.png", "PNG", optimize=True)
    # Small favicon.ico next to the app so /favicon.ico is served.
    (OUT_DIR / "favicon.ico").replace(OUT_DIR / "favicon.ico")  # no-op
    print("wrote app/icon.png and app/apple-icon.png")

    # Web manifest
    (OUT_DIR / "site.webmanifest").write_text(WEBMANIFEST, encoding="utf-8")
    print("wrote site.webmanifest")

    # og-image.png deliberately NOT written here — the evergreen card is
    # owned by scripts/audit_headline_stats.py (single ownership; the
    # render_og_image() above is retained only as a reference layout for
    # future marketing banners).


if __name__ == "__main__":
    main()
