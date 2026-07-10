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
  - og-image.png           (1200x630, WhatsApp/Instagram/Twitter link preview)
  - site.webmanifest       (PWA manifest)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------------------
# Brand tokens (STAGED v4 — from web/tailwind.config.js / web/DESIGN.md)
# Variable names kept from the v3 script so the 400 lines below need no edits:
# "ORANGE" now carries the volt accent, "CARBON"/"INK_*" the asphalt scale.
# ----------------------------------------------------------------------------
ORANGE = "#C9F231"  # accent volt
ORANGE_LIGHT = "#DBFF57"  # accent bright
ORANGE_DEEP = "#9CBE1E"  # accent deep
ACCENT_MINT = "#6FE3B2"
CARBON = "#07090C"  # asphalt-0
INK_2 = "#10141B"  # asphalt-2
INK_3 = "#171C25"  # asphalt-3
INK_4 = "#232A37"  # asphalt-4
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
# Logo mark: bold italic "M" in orange on carbon rounded square,
# with a staging dot top-right and a drag-strip bar at the bottom.
# Rendered at master size then downscaled — sharper than per-size render.
# ----------------------------------------------------------------------------
def render_mark(size: int, *, include_accents: bool = True) -> Image.Image:
    """Render the MotoQuant logo mark at the given pixel size.

    include_accents=False is used for the 16x16 / 32x32 rasters so the tiny
    dot + bar don't become sub-pixel mush — at that size the M alone is
    cleaner.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Carbon rounded-square background
    radius = max(2, int(size * 0.22))
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=CARBON)

    if include_accents:
        # Drag-strip bar at the bottom — the sole secondary mark.
        # An earlier design had a staging-light dot in the top-right too,
        # but the dot visually collided with the italic M's top-right
        # serif at every size ≥48px, so it's been removed.
        bar_y1 = int(size * 0.83)
        bar_h = max(1, int(size * 0.05))
        bar_x1 = int(size * 0.22)
        bar_x2 = int(size * 0.78)
        d.rectangle([bar_x1, bar_y1, bar_x2, bar_y1 + bar_h], fill=ORANGE)

    # Bold italic M — the hero mark. Fills the square but leaves breathing
    # room above (for the italic top-right reach to not clip the corner)
    # and below (for the drag-strip bar).
    if include_accents:
        font_size = int(size * 0.76)
        cy_target = int(size * 0.46)
    else:
        # No accents at 16/32 → M takes more vertical space
        font_size = int(size * 0.86)
        cy_target = int(size * 0.50)

    font = ImageFont.truetype(FONT_BOLD_IT, font_size)
    text = "M"
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = cy_target - th // 2 - bbox[1]
    d.text((tx, ty), text, fill=ORANGE, font=font)

    return img


def render_mark_hires(size: int) -> Image.Image:
    """Downscale from a 4× master for extra sharpness."""
    master = render_mark(size * 4, include_accents=(size >= 48))
    return master.resize((size, size), Image.LANCZOS)


# ----------------------------------------------------------------------------
# SVG source — hand-written, matches the raster logic.
# This is the scalable "truth" for any future editing.
# ----------------------------------------------------------------------------
ICON_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="MotoQuant">
  <title>MotoQuant</title>
  <rect x="0" y="0" width="64" height="64" rx="14" ry="14" fill="{CARBON}"/>
  <!-- drag-strip bar -->
  <rect x="14" y="53" width="36" height="3.2" fill="{ORANGE}"/>
  <!-- bold italic M -->
  <text x="32" y="43"
        font-family="'Helvetica Neue', 'Arial', 'DejaVu Sans', sans-serif"
        font-weight="900"
        font-style="italic"
        font-size="50"
        text-anchor="middle"
        fill="{ORANGE}"
        letter-spacing="-1">M</text>
</svg>
"""


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
        d.line([(x, 0), (x, H)], fill=(201, 242, 49, 12), width=1)

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
        "Quarter-mile simulation  ·  221 validated benchmarks",
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
        fill=(16, 20, 27, 255),
        outline=(201, 242, 49, 110),
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
    d.polygon(fill_poly, fill=(201, 242, 49, 34))

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
            fill=(201, 242, 49, 200),
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
  "theme_color": "#C9F231",
  "background_color": "#07090C",
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

    # OG image
    og_path = OUT_DIR / "og-image.png"
    render_og_image(og_path)
    print(f"wrote {og_path.name}")


if __name__ == "__main__":
    main()
