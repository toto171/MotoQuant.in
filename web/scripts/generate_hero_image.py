"""
Generate the landing-page hero image: "THE LAUNCH".

A procedural night-drag-strip scene in the STAGED v4 palette
(web/DESIGN.md): asphalt night, perspective strip with dashed centerline
and timing gates, and a single volt light-trail launching toward the
vanishing point, staged behind the amber-amber-green tree dots.

Deterministic (seeded) so re-runs are reproducible. Outputs:
  - web/public/hero/launch.png   (2400x1200 master, optimized)
  - web/public/hero/launch.webp  (same frame, ~10x smaller — the one the
                                  page actually loads)

Run: python3 web/scripts/generate_hero_image.py
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT_DIR = Path(__file__).resolve().parent.parent / "public" / "hero"
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 2400, 1200
VP = (int(W * 0.66), int(H * 0.34))  # vanishing point

# STAGED v4 palette
ASPHALT_0 = (7, 9, 12)
ASPHALT_SKY = (5, 6, 9)
VOLT = (201, 242, 49)
VOLT_BRIGHT = (219, 255, 87)
GO = (52, 217, 123)
STAGE = (255, 178, 36)

rng = random.Random(402)  # 402m — the quarter mile


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pt(p, q, t):
    return (lerp(p[0], q[0], t), lerp(p[1], q[1], t))


def base_canvas() -> Image.Image:
    """Night gradient: near-black sky into asphalt ground, subtle horizon."""
    img = Image.new("RGB", (W, H), ASPHALT_0)
    d = ImageDraw.Draw(img)
    horizon = VP[1]
    for y in range(H):
        if y < horizon:
            t = y / max(1, horizon)
            c = tuple(int(lerp(ASPHALT_SKY[i], ASPHALT_0[i], t)) for i in range(3))
        else:
            t = (y - horizon) / max(1, H - horizon)
            # ground brightens very slightly toward the viewer
            c = tuple(int(lerp(ASPHALT_0[i], ASPHALT_0[i] + 6, t)) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    return img


def draw_strip(img: Image.Image) -> None:
    """Perspective lane edges, dashed centerline, timing gates."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    left_base = (int(W * 0.02), H + 40)
    right_base = (int(W * 1.16), H + 40)

    # lane edges — drawn as depth-faded segments
    for base in (left_base, right_base):
        steps = 90
        for i in range(steps):
            t0, t1 = i / steps, (i + 1) / steps
            p0, p1 = lerp_pt(base, VP, t0), lerp_pt(base, VP, t1)
            alpha = int(46 * (1 - t0) ** 1.6) + 6
            width = max(1, int(7 * (1 - t0) ** 1.5))
            d.line([p0, p1], fill=(255, 255, 255, alpha), width=width)

    # dashed centerline
    center_base = (int(W * 0.56), H + 40)
    t = 0.0
    while t < 0.96:
        dash = 0.030 * (1 - t) + 0.004
        gap = dash * 1.1
        p0, p1 = (
            lerp_pt(center_base, VP, t),
            lerp_pt(center_base, VP, min(0.97, t + dash)),
        )
        alpha = int(60 * (1 - t) ** 1.4) + 8
        width = max(1, int(6 * (1 - t) ** 1.6))
        d.line([p0, p1], fill=(255, 255, 255, alpha), width=width)
        t += dash + gap

    # timing gates — thin ticks inside the lane at two depths
    for tg, label_alpha in [(0.46, 16), (0.68, 11)]:
        pl0 = lerp_pt(left_base, VP, tg)
        pr0 = lerp_pt(right_base, VP, tg)
        pl = lerp_pt(pl0, pr0, 0.09)
        pr = lerp_pt(pl0, pr0, 0.91)
        d.line([pl, pr], fill=(255, 255, 255, label_alpha), width=2)
        for px, py in (pl, pr):
            d.line(
                [(px, py), (px, py - 30 * (1 - tg))],
                fill=(255, 255, 255, label_alpha + 10),
                width=2,
            )

    # faint horizon glow + a few distant tower lights
    hz = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hz)
    hd.rectangle([0, VP[1] - 3, W, VP[1] + 3], fill=(210, 225, 235, 14))
    hz = hz.filter(ImageFilter.GaussianBlur(26))
    hd = ImageDraw.Draw(hz)
    for lx, la in [(0.30, 26), (0.47, 20), (0.815, 30), (0.90, 16)]:
        x = int(W * lx)
        hd.ellipse([x - 2, VP[1] - 8, x + 2, VP[1] - 4], fill=(235, 240, 245, la))
    layer = Image.alpha_composite(hz, layer)

    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"), (0, 0))


def streak_path(t: float) -> tuple[float, float]:
    """Quadratic bezier from launch box toward the vanishing point."""
    p0 = (W * 0.175, H * 1.04)
    p1 = (W * 0.385, H * 0.875)  # control — keeps the trail hugging the lane
    p2 = lerp_pt((W * 0.56, H * 1.03), VP, 0.62)  # head, 62% down the strip
    mt = 1 - t
    x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
    y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
    return x, y


def draw_streak(img: Image.Image) -> None:
    """The volt launch trail: layered blurred passes + hot core + head glow."""
    rgba = img.convert("RGBA")

    # pass spec: (blur radius, base width, color, alpha at head)
    passes = [
        (70, 90, VOLT, 95),
        (30, 40, VOLT, 160),
        (11, 14, VOLT_BRIGHT, 225),
        (3, 4.5, (255, 255, 255), 245),
        (1, 2, VOLT_BRIGHT, 255),
    ]
    for blur, base_w, color, head_alpha in passes:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        steps = 260
        for i in range(steps):
            t0, t1 = i / steps, (i + 1) / steps
            p0, p1 = streak_path(t0), streak_path(t1)
            # trail fades in from the tail, is hottest at the head; width
            # tapers with perspective toward the head
            fade = 0.12 + 0.88 * t0**1.15
            alpha = int(head_alpha * fade)
            width = max(1, int(base_w * (1 - 0.45 * t0)))
            if alpha > 2:
                d.line([p0, p1], fill=(*color, alpha), width=width)
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        rgba = Image.alpha_composite(rgba, layer)

    # head: hot dot + bloom
    hx, hy = streak_path(1.0)
    head = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(head)
    hd.ellipse([hx - 30, hy - 30, hx + 30, hy + 30], fill=(*VOLT, 120))
    head = head.filter(ImageFilter.GaussianBlur(18))
    hd = ImageDraw.Draw(head)
    hd.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], fill=(*VOLT_BRIGHT, 235))
    hd.ellipse([hx - 3, hy - 3, hx + 3, hy + 3], fill=(255, 255, 255, 255))
    rgba = Image.alpha_composite(rgba, head)

    # two faint echo filaments below the main trail (tire-groove reflections)
    echo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(echo)
    for dy, a in [(26, 26), (52, 13)]:
        for i in range(200):
            t0, t1 = i / 200, (i + 1) / 200
            p0, p1 = streak_path(t0), streak_path(t1)
            alpha = int(a * (t0**1.8))
            if alpha > 1:
                ed.line(
                    [(p0[0], p0[1] + dy * (1 - t0)), (p1[0], p1[1] + dy * (1 - t1))],
                    fill=(*VOLT, alpha),
                    width=2,
                )
    echo = echo.filter(ImageFilter.GaussianBlur(3))
    rgba = Image.alpha_composite(rgba, echo)

    # ground glow pooling under the trail (light reflecting off asphalt)
    pool = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pool)
    for i in range(40):
        t0 = i / 40
        px, py = streak_path(t0)
        rr = 120 * (1 - 0.5 * t0)
        alpha = int(26 * (0.15 + 0.85 * t0**1.2))
        pd.ellipse(
            [px - rr, py - rr * 0.28, px + rr, py + rr * 0.28], fill=(*VOLT, alpha)
        )
    pool = pool.filter(ImageFilter.GaussianBlur(60))
    rgba = Image.alpha_composite(rgba, pool)

    img.paste(rgba.convert("RGB"), (0, 0))


def draw_stage_dots(img: Image.Image) -> None:
    """The tree, armed, at the launch box — amber · amber · GO."""
    rgba = img.convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0 = W * 0.052, H * 0.855
    r, gap = 9, 34
    # glow under the green
    d.ellipse([x0 + 2 * gap - 26, y0 - 26, x0 + 2 * gap + 26, y0 + 26], fill=(*GO, 70))
    layer = layer.filter(ImageFilter.GaussianBlur(12))
    d = ImageDraw.Draw(layer)
    for i, color in enumerate([STAGE, STAGE, GO]):
        cx = x0 + i * gap
        d.ellipse([cx - r, y0 - r, cx + r, y0 + r], fill=(*color, 255))
    rgba = Image.alpha_composite(rgba, layer)
    img.paste(rgba.convert("RGB"), (0, 0))


def vignette_and_grain(img: Image.Image) -> Image.Image:
    """Edge darkening + fine mono grain so flat gradients don't band."""
    # vignette
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([-W * 0.25, -H * 0.35, W * 1.25, H * 1.35], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(220))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.composite(img, black, mask.point(lambda v: 90 + v * 165 // 255))

    # grain (deterministic)
    noise = Image.effect_noise((W, H), 12).convert("L")
    img = Image.composite(
        img.point(lambda v: min(255, v + 4)),
        img,
        noise.point(lambda v: 255 if v > 200 else 0),
    )
    return img


def main() -> None:
    img = base_canvas()
    draw_strip(img)
    draw_streak(img)
    draw_stage_dots(img)
    img = vignette_and_grain(img)

    png = OUT_DIR / "launch.png"
    webp = OUT_DIR / "launch.webp"
    img.save(png, "PNG", optimize=True)
    img.save(webp, "WEBP", quality=82, method=6)
    print(f"wrote {png} ({png.stat().st_size // 1024} KB)")
    print(f"wrote {webp} ({webp.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
