#!/usr/bin/env python3
"""Generate branded SVG figures for the book (vector, zero deps, light/dark safe).

Figures are *illustrative snapshots* (early-2026, inspired by artificialanalysis.ai
benchmarks and the book's own tables) — clearly labelled as such in captions.
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "chapters", "figures")

# brand palette — drawn on a white plate so both light/dark modes read it
INK = "#24292f"
MUTED = "#57606a"
GRID = "#e4e8ee"
SKY = "#0ea5e9"  # darker sky so it holds on white
SKY_SOFT = "#7dd3fc"
TEAL = "#14b8a6"
CORAL = "#f97316"


def svg_open(w, h):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" font-family="DM Sans, sans-serif">\n'
        f'<rect width="{w}" height="{h}" rx="12" fill="#ffffff"/>\n'
    )


def text(
    x, y, s, size: float = 13, fill=INK, anchor="start", weight="normal", mono=False
):
    fam = "JetBrains Mono, monospace" if mono else "DM Sans, sans-serif"
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
        f'text-anchor="{anchor}" font-weight="{weight}" font-family="{fam}">{s}</text>\n'
    )


def line(x1, y1, x2, y2, stroke=GRID, w=1, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{w}"{d}/>\n'


def save(name, body):
    try:
        os.makedirs(OUT, exist_ok=True)
    except OSError as e:
        raise SystemExit(f"make_figs: {e}") from e
    try:
        with open(os.path.join(OUT, name), "w") as f:
            f.write(body + "</svg>\n")
    except OSError as e:
        raise SystemExit(f"make_figs: {e}") from e
    print("wrote", name)


# ── 1. quality vs price scatter (open-model landscape) ──────────────────────
def fig_quality_price():
    W, H = 720, 420
    L, R, T, B = 64, 40, 40, 56
    pw, ph = W - L - R, H - T - B
    s = [svg_open(W, H)]

    # axes: price $/Mtok blended, log 0.05..100 ; quality index 20..80
    import math

    def px(v):
        lo, hi = math.log10(0.1), math.log10(100)
        return L + (math.log10(max(v, 0.1)) - lo) / (hi - lo) * pw

    def py(v):
        return T + (80 - v) / 60 * ph

    for g in [30, 40, 50, 60, 70]:
        s.append(line(L, py(g), L + pw, py(g)))
        s.append(text(L - 8, py(g) + 4, str(g), 11, MUTED, "end"))
    for g, lab in [(0.1, "0.1"), (1, "1"), (10, "10"), (100, "$100")]:
        s.append(line(px(g), T + ph, px(g), T + ph + 5, MUTED))
        s.append(text(px(g), T + ph + 20, lab, 11, MUTED, "middle", mono=True))

    # models from the book's own AA snapshot (ch. 2) + plausible blended prices
    pts = [
        ("Claude Opus 5", 12, 63, False),
        ("Claude Fable 5", 10, 62, False),
        ("GPT-5.6 Sol", 9, 61, False),
        ("Grok 4.6", 7, 61, False),
        ("Gemini 3.7 Flash", 0.6, 56, False),
        ("Kimi K3", 0.9, 60, True),
        ("GLM-5.3", 0.7, 59, True),
        ("Muse Spark 1.2", 0.35, 57, True),
        ("DeepSeek V4 Pro", 0.45, 53, True),
    ]
    offs = {
        "Claude Opus 5": (-10, -10, "end"),
        "Claude Fable 5": (-12, 12, "end"),
        "GPT-5.6 Sol": (12, -4, "start"),
        "Grok 4.6": (12, 10, "start"),
        "Gemini 3.7 Flash": (12, 8, "start"),
        "Kimi K3": (-12, -8, "end"),
        "GLM-5.3": (12, -6, "start"),
        "Muse Spark 1.2": (-12, 14, "end"),
        "DeepSeek V4 Pro": (12, 4, "start"),
    }
    # frontier zone hint
    s.append(
        f'<path d="M {px(2)} {py(82)} Q {px(60)} {py(78)} {px(100)} {py(70)} '
        f'L {px(100)} {py(84)} Z" fill="{SKY_SOFT}" opacity="0.18"/>\n'
    )
    s.append(text(px(30), py(81), "closed frontier", 11, SKY, "middle"))

    for name, p, q, is_open in pts:
        cx, cy = px(p), py(q)
        col = TEAL if is_open else CORAL
        s.append(
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="6" fill="{col}" opacity="0.9"/>'
        )
        dx, dy, anc = offs[name]
        s.append(text(cx + dx, cy + dy + 4, name, 11, INK, anc, mono=is_open))

    s.append(
        text(
            L + pw / 2,
            H - 14,
            "blended API price, $ / M tokens (log scale)",
            12,
            MUTED,
            "middle",
        )
    )
    s.append(
        f'<text x="16" y="{T + ph / 2}" font-size="12" fill="{MUTED}" text-anchor="middle" '
        f'transform="rotate(-90 16 {T + ph / 2})">composite intelligence index</text>'
    )
    s.append(
        f'<circle cx="{L + 12}" cy="{H - 34}" r="5" fill="{TEAL}"/>'
        + text(L + 22, H - 30, "open weights", 11, MUTED)
        + f'<circle cx="{L + 130}" cy="{H - 34}" r="5" fill="{CORAL}"/>'
        + text(L + 140, H - 30, "closed (reference)", 11, MUTED)
    )
    save("fig-quality-price.svg", "".join(s))


# ── 2. quantization: size vs retained quality ────────────────────────────────
def fig_quant():
    W, H = 700, 380
    L, R, T, B = 64, 36, 36, 56
    pw, ph = W - L - R, H - T - B
    levels = ["FP16", "Q8", "Q6", "Q5", "Q4", "Q3", "Q2"]
    gb = [64, 34, 26, 22, 18, 14, 11]
    qual = [100, 99, 98, 97, 95, 88, 75]

    s = [svg_open(W, H)]
    maxgb = 70

    def bx(i):
        return L + i * (pw / len(levels)) + 14

    def bh(v):
        return v / maxgb * ph

    # quality polyline (right axis 60..105)
    def qy(v):
        return T + (105 - v) / 50 * ph

    for g in [0, 25, 50]:
        s.append(line(L, T + g / maxgb * ph, L + pw, T + g / maxgb * ph))
    for i, (lv, sz) in enumerate(zip(levels, gb, strict=True)):
        x = bx(i)
        h = bh(sz)
        col = SKY if i <= 4 else CORAL
        s.append(
            f'<rect x="{x:.0f}" y="{T + ph - h:.0f}" width="44" height="{h:.0f}" rx="5" fill="{col}" opacity="0.85"/>'
        )
        s.append(text(x + 22, T + ph - h - 7, str(sz), 11, INK, "middle", mono=True))
        s.append(
            text(x + 22, T + ph + 20, lv, 12, INK, "middle", weight="500", mono=True)
        )
        if i:
            px_, py_ = bx(i - 1) + 22, qy(qual[i - 1])
            cx, cy = x + 22, qy(qual[i])
            s.append(
                f'<line x1="{px_:.0f}" y1="{py_:.0f}" x2="{cx:.0f}" y2="{cy:.0f}" stroke="{TEAL}" stroke-width="2.5"/>'
            )
    for i in range(len(levels)):
        s.append(
            f'<circle cx="{bx(i) + 22:.0f}" cy="{qy(qual[i]):.0f}" r="4" fill="#fff" stroke="{TEAL}" stroke-width="2.5"/>'
        )
        s.append(
            text(
                bx(i) + 34,
                qy(qual[i]) + (14 if i == 0 else -8),
                f"{qual[i]}%",
                10.5,
                TEAL,
                "start",
                mono=True,
            )
        )

    s.append(
        text(
            L,
            20,
            "32 B model on disk, GB (bars) · task-quality retained (line)",
            12.5,
            INK,
            weight="500",
        )
    )
    s.append(text(L + pw / 2, H - 14, "GGUF quantization level", 12, MUTED, "middle"))
    save("fig-quant.svg", "".join(s))


# ── 3. decode throughput per hardware tier ───────────────────────────────────
def fig_throughput():
    W, H = 700, 360
    L, R, T, B = 210, 60, 36, 48
    pw, ph = W - L - R, H - T - B
    rows = [
        ("laptop CPU · 8 B Q4", (5, 15), 10),
        ("Mac M-Pro 64 GB · 32 B Q4", (15, 25), 20),
        ("RTX 3090 · 8 B Q4", (90, 130), 110),
        ("RTX 3090 · 32 B Q4", (25, 40), 33),
        ("RTX 4090 · 8 B Q4", (120, 170), 145),
        ("2×3090 server · 70 B Q4", (12, 20), 16),
    ]
    mx = 180
    s = [svg_open(W, H)]
    rh = ph / len(rows)
    for i, (lab, rng, mid) in enumerate(rows):
        y = T + i * rh + rh / 2
        bw = mid / mx * pw
        lo, hi = rng
        xlo, xhi = lo / mx * pw, hi / mx * pw
        s.append(
            f'<rect x="{L + xlo:.0f}" y="{y - 5:.0f}" width="{xhi - xlo:.0f}" height="10" rx="5" fill="{SKY_SOFT}" opacity="0.5"/>'
        )
        s.append(f'<circle cx="{L + bw:.0f}" cy="{y:.0f}" r="7" fill="{SKY}"/>')
        s.append(text(L - 12, y + 4, lab, 12, INK, "end", mono=False))
        s.append(text(L + bw + 12, y + 4, f"{mid} t/s", 11, MUTED, "start", mono=True))
    s.append(
        text(
            W / 2,
            H - 12,
            "decode speed, tokens/s (typical range ◁—●)",
            12,
            MUTED,
            "middle",
        )
    )
    save("fig-throughput.svg", "".join(s))


# ── 4. TCO: local workstation vs cloud API ───────────────────────────────────
def fig_tco():
    W, H = 720, 400
    L, R, T, B = 70, 40, 40, 56
    pw, ph = W - L - R, H - T - B
    months, ymax = 36, 6000

    def px(m):
        return L + m / months * pw

    def py(e):
        return T + (ymax - e) / ymax * ph

    s = [svg_open(W, H)]
    for g in range(0, ymax + 1, 1500):
        s.append(line(L, py(g), L + pw, py(g)))
        s.append(
            text(L - 8, py(g) + 4, f"{g // 1000}k" if g else "€0", 11, MUTED, "end")
        )
    for m in [6, 12, 18, 24, 30, 36]:
        s.append(line(px(m), T + ph, px(m), T + ph + 5, MUTED))
        s.append(text(px(m), T + ph + 20, f"M{m}", 11, MUTED, "middle", mono=True))

    # api: €95/mo avg growing ~5%/mo compounding usage; local: €4200 + €18/mo
    api_pts, loc_pts = [], []
    api_cost = 0.0
    for m in range(months + 1):
        api_cost += 95 * (1.05**m)
        api_pts.append((m, api_cost))
        loc_pts.append((m, 4200 + 18 * m))

    def path(pts, color, dash="", width=3):
        d = f"M {px(pts[0][0]):.0f} {py(pts[0][1]):.0f}"
        for m, c in pts[1:]:
            d += f" L {px(m):.0f} {py(c):.0f}"
        dd = f' stroke-dasharray="{dash}"' if dash else ""
        return (
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dd}/>'
        )

    s.append(path(api_pts, CORAL))
    s.append(path(loc_pts, TEAL))
    beak = next(m for (m, a), (_, loc) in zip(api_pts, loc_pts, strict=True) if a > loc)
    s.append(
        f'<circle cx="{px(beak):.0f}" cy="{py(4200 + 18 * beak):.0f}" r="6" fill="{INK}"/>'
    )
    s.append(
        text(px(beak) + 10, py(4200 + 18 * beak) - 10, "break-even", 11.5, INK, "start")
    )
    s.append(
        text(
            px(30),
            py(api_pts[30][1]) - 12,
            "cloud API rental",
            12,
            CORAL,
            "middle",
            "500",
        )
    )
    s.append(
        text(px(31), py(loc_pts[31][1]) + 22, "local box", 12, TEAL, "middle", "500")
    )
    s.append(
        text(
            L + pw / 2,
            H - 14,
            "months of a 5-seat team running a 30 B-class model daily",
            12,
            MUTED,
            "middle",
        )
    )
    s.append(
        f'<text x="16" y="{T + ph / 2}" font-size="12" fill="{MUTED}" text-anchor="middle" '
        f'transform="rotate(-90 16 {T + ph / 2})">cumulative cost</text>'
    )
    save("fig-tco.svg", "".join(s))


fig_quality_price()
fig_quant()
fig_throughput()
fig_tco()
