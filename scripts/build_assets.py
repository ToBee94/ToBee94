#!/usr/bin/env python3
"""Generates the animated SVG assets used in README.md.

Run from the repo root:  python3 scripts/build_assets.py
"""
import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

CYAN, NAVY, VIOLET, CORAL, HONEY = "#26d0ce", "#1a2980", "#8b6cff", "#ff9a8b", "#ffb703"
LANG = {"PHP": "#4F5D95", "JavaScript": "#f1e05a", "Rust": "#dea584", "TypeScript": "#3178c6"}


def hexagon(cx, cy, r):
    w = math.sqrt(3) * r / 2
    pts = [(cx, cy - r), (cx + w, cy - r / 2), (cx + w, cy + r / 2),
           (cx, cy + r), (cx - w, cy + r / 2), (cx - w, cy - r / 2)]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def honeycomb(x0, x1, y0, y1, r, seed, fade_from=None):
    """Pointy-top honeycomb; cells pulse with staggered delays, a few in honey amber."""
    rnd = random.Random(seed)
    w, out = math.sqrt(3) * r, []
    row, y = 0, y0
    while y < y1 + r:
        x = x0 + (w / 2 if row % 2 else 0)
        while x < x1 + w:
            fade = 1.0 if fade_from is None else max(0.0, min(1.0, (x - fade_from) / 260))
            if fade > 0:
                color = HONEY if rnd.random() < 0.12 else CYAN
                cls = "hex" if rnd.random() < 0.45 else "hex idle"
                out.append(
                    f'<polygon class="{cls}" points="{hexagon(x, y, r - 3)}" fill="{color}" '
                    f'stroke="{color}" opacity="{fade:.2f}" '
                    f'style="animation-delay:{rnd.uniform(0, 6):.2f}s"/>')
            x += w
        y += 1.5 * r
        row += 1
    return "\n".join(out)


HEX_STYLE = """
.hex{fill-opacity:.03;stroke-opacity:.18;stroke-width:1.5;animation:pulse 6s ease-in-out infinite}
.hex.idle{animation:none}
@keyframes pulse{0%,100%{fill-opacity:.03;stroke-opacity:.18}50%{fill-opacity:.32;stroke-opacity:.9}}
.blob{transform-box:fill-box;transform-origin:center;animation:drift 16s ease-in-out infinite alternate}
@keyframes drift{0%{transform:translate(0,0) scale(1)}50%{transform:translate(70px,-30px) scale(1.15)}100%{transform:translate(-50px,25px) scale(.92)}}
.in{opacity:0;animation:in .9s cubic-bezier(.2,.7,.2,1) forwards}
@keyframes in{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.blink{animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
"""


def chips(items, x, y, color, size=17, bg_opacity=0.12):
    out = []
    for label in items:
        w = len(label) * size * 0.56 + 30
        out.append(
            f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="{size + 17}" rx="{(size + 17) / 2}" '
            f'fill="{color}" fill-opacity="{bg_opacity}" stroke="{color}" stroke-opacity=".45"/>'
            f'<text x="{x + w / 2:.0f}" y="{y + size + 4}" text-anchor="middle" font-family="{SANS}" '
            f'font-size="{size}" font-weight="600" fill="#e6edf3">{escape(label)}</text>')
        x += w + 10
    return "\n".join(out)


def typing(lines, x, y, size, color, cycle=4.0):
    """Rotating typewriter line using SMIL clip reveal; each phrase owns one slot of the cycle."""
    total, cw = cycle * len(lines), size * 0.61
    kt = f"0;{1.1 / total:.4f};{(cycle - 0.7) / total:.4f};{(cycle - 0.25) / total:.4f};1"
    defs, body = [], []
    for i, text in enumerate(lines):
        w = len(text) * cw + 4
        b = f'begin="{i * cycle}s" dur="{total}s" repeatCount="indefinite"'
        defs.append(
            f'<clipPath id="t{i}"><rect x="{x}" y="{y - size}" height="{size * 1.5}" width="0">'
            f'<animate attributeName="width" values="0;{w:.0f};{w:.0f};0;0" keyTimes="{kt}" {b}/>'
            f'</rect></clipPath>')
        body.append(
            f'<text clip-path="url(#t{i})" x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" '
            f'fill="#e6edf3">{escape(text)}</text>'
            f'<g class="blink"><rect x="{x}" y="{y - size + 3}" width="{cw:.0f}" height="{size + 2}" '
            f'fill="{color}" opacity="0">'
            f'<animate attributeName="x" values="{x};{x + w:.0f};{x + w:.0f};{x};{x}" keyTimes="{kt}" {b}/>'
            f'<animate attributeName="opacity" values="1;0" keyTimes="0;{cycle / total:.4f}" '
            f'calcMode="discrete" {b}/></rect></g>')
    return "".join(defs), "\n".join(body)


def header():
    W, H = 1200, 360
    tdefs, tbody = typing([
        "shipping Mumcord: voice chat in Rust",
        "building clean APIs & SDKs in PHP",
        "multi-tenant SSH keys with Shellock",
        "open source from Bremen, Germany",
    ], 96, 252, 22, CYAN)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Tobias Vorwachs: Backend Engineer, founder of Mumcord">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#060a14"/><stop offset=".55" stop-color="#0a1424"/><stop offset="1" stop-color="#0d0a1f"/></linearGradient>
<linearGradient id="name" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#a5f3fc"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity=".7"/><stop offset=".5" stop-color="#ffffff" stop-opacity=".08"/><stop offset="1" stop-color="{VIOLET}" stop-opacity=".7"/></linearGradient>
<pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse"><path d="M36 0H0V36" fill="none" stroke="#fff" stroke-opacity=".035"/></pattern>
<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="70"/></filter>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="26"/></clipPath>
{tdefs}
</defs>
<style>{HEX_STYLE}</style>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#grid)"/>
<g filter="url(#blur)" opacity=".75">
<circle class="blob" cx="980" cy="70" r="190" fill="{CYAN}" opacity=".55"/>
<circle class="blob" cx="260" cy="360" r="170" fill="#3a5bff" opacity=".45" style="animation-delay:-6s"/>
<circle class="blob" cx="1150" cy="330" r="160" fill="{VIOLET}" opacity=".5" style="animation-delay:-11s"/>
</g>
{honeycomb(640, W, 0, H, 38, 94, fade_from=640)}
<g class="in" style="animation-delay:.1s"><text x="96" y="86" font-family="{MONO}" font-size="19" fill="#7d8590"><tspan fill="{CYAN}">tobias@bremen</tspan>:<tspan fill="{VIOLET}">~</tspan>$ whoami</text></g>
<g class="in" style="animation-delay:.3s"><text x="92" y="162" font-family="{SANS}" font-size="74" font-weight="800" letter-spacing="-2" fill="url(#name)">Tobias Vorwachs</text></g>
<g class="in" style="animation-delay:.5s"><text x="96" y="204" font-family="{SANS}" font-size="26" font-weight="500" fill="#c9d1d9">Backend Engineer <tspan fill="#484f58">/</tspan> Founder of <tspan fill="{VIOLET}" font-weight="700">Mumcord</tspan> <tspan fill="#484f58">/</tspan> fuewa.systems</text></g>
<text x="70" y="252" font-family="{MONO}" font-size="22" fill="{CYAN}">›</text>
{tbody}
<g class="in" style="animation-delay:.8s">{chips(["PHP", "Symfony", "Rust", "Tauri", "TypeScript", "Docker"], 96, 286, CYAN)}</g>
</g>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="26" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
</svg>'''


def mumcord():
    W, H = 1200, 440
    bullets = [
        "Low-latency Mumble voice, push-to-talk on mouse buttons",
        "Text channels you can follow without joining",
        "No telemetry, TLS always on, no server changes needed",
    ]
    bl = "\n".join(
        f'<circle cx="74" cy="{262 + i * 36}" r="5" fill="{CORAL}"/>'
        f'<text x="92" y="{269 + i * 36}" font-family="{SANS}" font-size="21" fill="#cfc8ef">{escape(b)}</text>'
        for i, b in enumerate(bullets))

    # App mockup (decorative): server rail, channel tree with a voice channel, chat pane.
    X, Y, MW, MH = 680, 44, 480, 352
    servers = "\n".join(
        f'<circle cx="{X + 34}" cy="{Y + 82 + i * 54}" r="19" fill="{c}"/>'
        for i, c in enumerate([VIOLET, "#3ddc84", CORAL, "#4c8dff"]))
    users = [("ToBee", True), ("mika", False), ("alex", True)]
    voice = "\n".join(
        f'<circle cx="{X + 104}" cy="{Y + 222 + i * 30}" r="10" fill="{["#ffb703", "#4c8dff", "#ff6b9a"][i]}"/>'
        + (f'<circle class="talk" cx="{X + 104}" cy="{Y + 222 + i * 30}" r="13" fill="none" stroke="#3ddc84" stroke-width="2.5" style="animation-delay:{i * .7}s"/>' if talking else "")
        + f'<text x="{X + 122}" y="{Y + 227 + i * 30}" font-family="{SANS}" font-size="14" fill="#cfc8ef">{name}</text>'
        for i, (name, talking) in enumerate(users))
    chans = "\n".join(
        f'<text x="{X + 82}" y="{Y + 108 + i * 28}" font-family="{SANS}" font-size="15" fill="{"#ffffff" if i == 0 else "#8f88b3"}">'
        f'<tspan fill="#5d567f">#</tspan> {c}</text>'
        for i, c in enumerate(["general", "clips", "builds"]))
    msgs = [("ToBee", "#ffb703", "gg! ready for round two?", 0),
            ("alex", "#ff6b9a", "joining Lobby in 2 min", 1),
            ("mika", "#4c8dff", None, 2)]
    chat = []
    cx = X + 232
    for name, col, text, i in msgs:
        yy = Y + 96 + i * 64
        chat.append(f'<circle cx="{cx + 14}" cy="{yy + 6}" r="14" fill="{col}"/>'
                    f'<text x="{cx + 38}" y="{yy + 2}" font-family="{SANS}" font-size="14" font-weight="700" fill="#ffffff">{name}</text>')
        if text:
            chat.append(f'<text x="{cx + 38}" y="{yy + 24}" font-family="{SANS}" font-size="14" fill="#cfc8ef">{text}</text>')
        else:
            chat.append(f'<rect x="{cx + 38}" y="{yy + 12}" width="170" height="48" rx="8" fill="{VIOLET}" fill-opacity=".18" stroke="{VIOLET}" stroke-opacity=".5"/>'
                        f'<rect x="{cx + 50}" y="{yy + 26}" width="110" height="8" rx="4" fill="#cfc8ef" fill-opacity=".5"/>'
                        f'<rect x="{cx + 50}" y="{yy + 44}" width="140" height="8" rx="4" fill="#cfc8ef" fill-opacity=".3"/>'
                        )
    dots = "".join(
        f'<circle class="dot" cx="{cx + 20 + i * 12}" cy="{Y + MH - 62}" r="4" fill="#8f88b3" style="animation-delay:{i * .18}s"/>'
        for i in range(3))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Mumcord: modern voice chat for any Mumble server">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0c0819"/><stop offset=".6" stop-color="#170f2e"/><stop offset="1" stop-color="#241327"/></linearGradient>
<linearGradient id="title" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff"/><stop offset=".5" stop-color="#d4c8ff"/><stop offset="1" stop-color="{CORAL}"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".8"/><stop offset=".5" stop-color="#ffffff" stop-opacity=".06"/><stop offset="1" stop-color="{CORAL}" stop-opacity=".8"/></linearGradient>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.2" fill="#fff" fill-opacity=".06"/></pattern>
<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="70"/></filter>
<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="18" stdDeviation="22" flood-color="#000" flood-opacity=".55"/></filter>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="26"/></clipPath>
<clipPath id="win"><rect x="{X}" y="{Y}" width="{MW}" height="{MH}" rx="16"/></clipPath>
</defs>
<style>{HEX_STYLE}
.talk{{transform-box:fill-box;transform-origin:center;animation:talk 1.4s ease-in-out infinite}}
@keyframes talk{{0%,100%{{opacity:.25;transform:scale(.92)}}50%{{opacity:1;transform:scale(1.08)}}}}
.dot{{animation:bounce 1.2s ease-in-out infinite}}
@keyframes bounce{{0%,60%,100%{{transform:translateY(0);opacity:.4}}30%{{transform:translateY(-5px);opacity:1}}}}
.float{{animation:float 7s ease-in-out infinite}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-8px)}}}}
.wave{{transform-box:fill-box;transform-origin:center bottom;animation:eq 1s ease-in-out infinite}}
@keyframes eq{{0%,100%{{transform:scaleY(.3)}}50%{{transform:scaleY(1)}}}}
</style>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#dots)"/>
<g filter="url(#blur)" opacity=".8">
<circle class="blob" cx="300" cy="40" r="200" fill="{VIOLET}" opacity=".45"/>
<circle class="blob" cx="1000" cy="420" r="200" fill="{CORAL}" opacity=".35" style="animation-delay:-7s"/>
<circle class="blob" cx="760" cy="40" r="140" fill="#4c8dff" opacity=".3" style="animation-delay:-12s"/>
</g>
<g class="in" style="animation-delay:.1s"><text x="66" y="82" font-family="{MONO}" font-size="17" font-weight="700" letter-spacing="3" fill="{CORAL}">FOUNDER &amp; MAINTAINER</text></g>
<g class="in" style="animation-delay:.25s"><text x="62" y="156" font-family="{SANS}" font-size="78" font-weight="800" letter-spacing="-2.5" fill="url(#title)">Mumcord</text></g>
<g class="in" style="animation-delay:.4s"><text x="66" y="208" font-family="{SANS}" font-size="27" font-weight="600" fill="#ffffff">Modern voice chat for any Mumble server.</text></g>
<g transform="translate(560 112)">{"".join(f'<rect class="wave" x="{i * 9}" y="{-38 + abs(3 - i) * 4}" width="5" height="{38 - abs(3 - i) * 4}" rx="2.5" fill="{VIOLET if i % 2 else CORAL}" style="animation-delay:{i * .13:.2f}s"/>' for i in range(7))}</g>
<g class="in" style="animation-delay:.55s">{bl}</g>
<g class="in" style="animation-delay:.75s">{chips(["Rust", "Tauri", "TypeScript", "AGPL-3.0", "Win / macOS / Linux"], 66, 366, VIOLET, size=16)}</g>
<g class="float">
<g filter="url(#shadow)"><rect x="{X}" y="{Y}" width="{MW}" height="{MH}" rx="16" fill="#100b20"/></g>
<g clip-path="url(#win)">
<rect x="{X}" y="{Y}" width="{MW}" height="34" fill="#0a0716"/>
<circle cx="{X + 20}" cy="{Y + 17}" r="5.5" fill="#ff5f57"/><circle cx="{X + 38}" cy="{Y + 17}" r="5.5" fill="#febc2e"/><circle cx="{X + 56}" cy="{Y + 17}" r="5.5" fill="#28c840"/>
<text x="{X + MW / 2}" y="{Y + 22}" text-anchor="middle" font-family="{SANS}" font-size="13" fill="#6f6893">Mumcord</text>
<rect x="{X}" y="{Y + 34}" width="68" height="{MH}" fill="#0a0716"/>
<rect x="{X}" y="{Y + 68}" width="4" height="28" rx="2" fill="#ffffff"/>
{servers}
<rect x="{X + 68}" y="{Y + 34}" width="152" height="{MH}" fill="#130d27"/>
<text x="{X + 82}" y="{Y + 62}" font-family="{SANS}" font-size="15" font-weight="700" fill="#ffffff">Gaming Crew</text>
{chans}
<text x="{X + 82}" y="{Y + 196}" font-family="{SANS}" font-size="11" font-weight="700" letter-spacing="1.2" fill="#6f6893">VOICE / LOBBY</text>
{voice}
<rect x="{X + 76}" y="{Y + MH - 46}" width="136" height="34" rx="8" fill="#0a0716"/>
<circle cx="{X + 96}" cy="{Y + MH - 29}" r="5" fill="#3ddc84"/>
<text x="{X + 108}" y="{Y + MH - 24}" font-family="{SANS}" font-size="12" fill="#3ddc84">Voice connected</text>
<text x="{X + 236}" y="{Y + 62}" font-family="{SANS}" font-size="15" font-weight="700" fill="#ffffff"><tspan fill="#5d567f">#</tspan> general</text>
<line x1="{X + 220}" y1="{Y + 76}" x2="{X + MW}" y2="{Y + 76}" stroke="#ffffff" stroke-opacity=".06"/>
{"".join(chat)}
{dots}
<rect x="{cx}" y="{Y + MH - 46}" width="{MW - 248}" height="34" rx="9" fill="#1b1436"/>
<text x="{cx + 14}" y="{Y + MH - 24}" font-family="{SANS}" font-size="13" fill="#6f6893">Message #general</text>
</g>
<rect x="{X + .5}" y="{Y + .5}" width="{MW - 1}" height="{MH - 1}" rx="16" fill="none" stroke="#ffffff" stroke-opacity=".1"/>
</g>
</g>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="26" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
</svg>'''


def wrap(text, width):
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + [cur]


def card(slug, owner, name, desc, tag, lang, meta, accent, wide=False, delay=0.0):
    W, H = (820, 186) if wide else (400, 212)
    lines = wrap(desc, 104 if wide else 50)[:3]
    a1, a2 = accent
    tag_w = len(tag) * 7.6 + 24
    desc_svg = "".join(
        f'<text x="26" y="{108 + i * 21}" font-family="{SANS}" font-size="14.5" fill="#9da7b3">{escape(l)}</text>'
        for i, l in enumerate(lines))
    fy = H - 24
    foot = []
    if lang:
        foot.append(f'<circle cx="32" cy="{fy - 5}" r="6" fill="{LANG[lang]}"/>'
                    f'<text x="45" y="{fy}" font-family="{SANS}" font-size="13.5" fill="#c9d1d9">{lang}</text>')
    x = 45 + len(lang) * 8 + 20 if lang else 26
    for m in meta:
        foot.append(f'<text x="{x:.0f}" y="{fy}" font-family="{SANS}" font-size="13.5" fill="#7d8590">{escape(m)}</text>')
        x += len(m) * 7.4 + 22
    (OUT / f"card-{slug}.svg").write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(owner)}/{escape(name)}: {escape(desc)}">
<defs>
<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{a1}"/><stop offset="1" stop-color="{a2}"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a1}" stop-opacity=".55"/><stop offset=".45" stop-color="#30363d"/><stop offset="1" stop-color="#30363d"/></linearGradient>
<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="40"/></filter>
<clipPath id="c"><rect width="{W}" height="{H}" rx="16"/></clipPath>
</defs>
<style>
.sheen{{animation:sheen 8s ease-in-out infinite;animation-delay:{delay}s}}
@keyframes sheen{{0%{{transform:translateX(-260px) skewX(-20deg)}}35%,100%{{transform:translateX({W + 160}px) skewX(-20deg)}}}}
.glow{{animation:glow 6s ease-in-out infinite alternate}}
@keyframes glow{{from{{opacity:.22}}to{{opacity:.45}}}}
</style>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="#0d1117"/>
<circle class="glow" cx="{W - 30}" cy="10" r="90" fill="{a1}" filter="url(#blur)"/>
<rect width="{W}" height="3" fill="url(#bar)"/>
<rect class="sheen" x="0" y="0" width="140" height="{H}" fill="url(#sheen)"/>
<text x="26" y="44" font-family="{MONO}" font-size="13.5" fill="#7d8590">{escape(owner)} /</text>
<text x="25" y="74" font-family="{SANS}" font-size="23" font-weight="700" fill="#ffffff">{escape(name)}</text>
<rect x="{W - 22 - tag_w:.0f}" y="26" width="{tag_w:.0f}" height="22" rx="11" fill="{a1}" fill-opacity=".14" stroke="{a1}" stroke-opacity=".5"/>
<text x="{W - 22 - tag_w / 2:.0f}" y="41" text-anchor="middle" font-family="{MONO}" font-size="11" font-weight="700" letter-spacing="1" fill="{a1}">{escape(tag)}</text>
{desc_svg}
{"".join(foot)}
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="url(#edge)"/>
</svg>''')


def footer():
    W, H = 1200, 170
    waves = "".join(
        f'<path class="w{i}" d="M0 {110 + i * 14} Q 150 {80 + i * 14} 300 {110 + i * 14} T 600 {110 + i * 14} T 900 {110 + i * 14} T 1200 {110 + i * 14} T 1500 {110 + i * 14} T 1800 {110 + i * 14} V {H} H 0 Z" fill="{c}" fill-opacity="{o}"/>'
        for i, (c, o) in enumerate([(VIOLET, .25), (CYAN, .22), (NAVY, .55)]))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Thanks for stopping by">
<defs><clipPath id="frame"><rect width="{W}" height="{H}" rx="26"/></clipPath>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#060a14"/><stop offset="1" stop-color="#0d0a1f"/></linearGradient></defs>
<style>{HEX_STYLE}
.w0{{animation:sway 9s linear infinite}}.w1{{animation:sway 13s linear infinite reverse}}.w2{{animation:sway 17s linear infinite}}
@keyframes sway{{from{{transform:translateX(0)}}to{{transform:translateX(-600px)}}}}
</style>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
{honeycomb(0, W, 0, 110, 26, 7)}
{waves}
<text x="{W / 2}" y="62" text-anchor="middle" font-family="{SANS}" font-size="30" font-weight="800" fill="#ffffff">Thanks for stopping by.</text>
<text x="{W / 2}" y="96" text-anchor="middle" font-family="{MONO}" font-size="17" fill="#9da7b3">fuewa.systems <tspan fill="{CYAN}">·</tspan> mumcord.app <tspan fill="{CYAN}">·</tspan> github.com/ToBee94</text>
</g>
</svg>'''


CARDS = [
    # Mumcord family
    ("mumbot", "Mumcord", "mumbot", "Bots for any Mumble server: a webhook bot for alerts and CI, plus a scripted test bot. Part of the Mumcord family.", "BOT", "Rust", ["AGPL-3.0", "Docker"], (VIOLET, CORAL)),
    ("mumpeer", "Mumcord", "mumpeer", "Small relay for Mumcord's peer-to-peer features like screen sharing. Hides IPs, only verified Mumcord/Mumble users get in.", "RELAY", None, ["Coming soon"], (CORAL, VIOLET)),
    # ToBee94
    ("shellock", "ToBee94", "Shellock", "Multi-tenant SSH key management: central control, role-based access and audit logging on a Dockerized Symfony stack.", "SECURITY", "PHP", ["Symfony", "Docker"], (CYAN, NAVY)),
    ("phpass", "ToBee94", "phpass", "Openwall's phpass password hashing, modernised with namespaces and Composer support. Based on release 0.3.", "CRYPTO", "PHP", ["Composer"], (CYAN, NAVY)),
    ("cloudns", "ToBee94", "cloudns-api-php", "Clean PHP SDK for the ClouDNS API. DNS zones and records, made simple.", "SDK", "PHP", ["MIT"], (CYAN, NAVY)),
    ("acinfinity", "ToBee94", "ac-infinity-php", "PHP SDK for the AC Infinity API. Typed access to controllers and sensors.", "SDK", "PHP", ["MIT"], (CYAN, NAVY)),
    # Die PARTEI in Europa
    ("wordpress-api", "Die-PARTEI-in-Europa", "wordpress-api", "PHP SDK for the WordPress REST API: posts, pages, menus, search and settings, with pagination and Polylang support.", "SDK", "PHP", ["MIT"], ("#ff4d5e", "#b5121b")),
    ("headless-mode", "Die-PARTEI-in-Europa", "headless-mode", "Turns WordPress into a headless CMS: disables the frontend, redirects view links and adds a signed preview endpoint.", "WORDPRESS", "PHP", ["GPL-2.0"], ("#ff4d5e", "#b5121b")),
    ("block-manager", "Die-PARTEI-in-Europa", "block-manager", "Enable or disable individual Gutenberg blocks through a simple settings dialog. Works with any registered block.", "WORDPRESS", "PHP", ["GPL-2.0"], ("#ff4d5e", "#b5121b")),
    ("eu-captcha", "Die-PARTEI-in-Europa", "EU-Politics-CAPTCHA", "A CAPTCHA built from memes and scandals of the European Parliament. Yes, really.", "SATIRE", "JavaScript", ["MIT"], ("#ff4d5e", "#b5121b")),
]


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    (OUT / "header.svg").write_text(header())
    (OUT / "mumcord.svg").write_text(mumcord())
    (OUT / "footer.svg").write_text(footer())
    for i, c in enumerate(CARDS):
        card(*c, delay=(i % 2) * 1.5 + (i // 2) * 0.6)
    card("growdata-hub", "unserioes24", "growdata-hub",
         "Open, structured data on grow equipment: lights, tents, filters, fans, controllers and the ecosystems that work together.",
         "OPEN DATA", "JavaScript", ["MIT", "JSON"], ("#3ddc84", "#0f9d58"), wide=True, delay=2)
    print("wrote", len(list(OUT.glob("*.svg"))), "SVGs to", OUT)
