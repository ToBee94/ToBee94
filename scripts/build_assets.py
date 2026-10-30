#!/usr/bin/env python3
"""Generates the SVGs in assets/ (dark + light variant each).

Run from anywhere:  python3 scripts/build_assets.py
"""
import math
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"
SANS = "'Helvetica Neue',-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

THEMES = {
    "dark": dict(bg="#0b0b0c", ink="#f2efe6", muted="#8a877f", rule="#2a2926", honey="#f5b301", on_honey="#0b0b0c"),
    "light": dict(bg="#faf8f2", ink="#141414", muted="#6b675f", rule="#e0dacb", honey="#e0a100", on_honey="#141414"),
}


def svg(w, h, label, body, style=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}">'
            + (f"<style>{style}</style>" if style else "") + body + "</svg>")


def text(x, y, s, size, fill, font=SANS, weight=400, anchor="start", spacing=0, extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{spacing}" {extra}>{s}</text>')


def hexagon(cx, cy, r):
    w = math.sqrt(3) * r / 2
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in
                    [(cx, cy - r), (cx + w, cy - r / 2), (cx + w, cy + r / 2),
                     (cx, cy + r), (cx - w, cy + r / 2), (cx - w, cy - r / 2)])


def wrap(s, width):
    lines, cur = [], ""
    for word in s.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + [cur]


def write(name, build):
    for mode, t in THEMES.items():
        (OUT / f"{name}-{mode}.svg").write_text(build(t))


# ── header ────────────────────────────────────────────────────────────────────

# Comb cells in offset coordinates (row, col); honey cells get filled last.
COMB = [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3),
        (3, 0), (3, 1), (3, 2), (4, 1), (4, 2), (5, 1)]
HONEY = {(2, 1), (2, 2), (3, 1)}


def header(t):
    W, H, R = 1200, 560, 36
    w = math.sqrt(3) * R
    cells = []
    for row, col in COMB:
        cx = 905 + col * w + (w / 2 if row % 2 else 0)
        cy = 130 + row * 1.5 * R
        honey = (row, col) in HONEY
        delay = 0.25 + math.hypot(cx - 1000, cy - 260) / 420 + (0.6 if honey else 0)
        cells.append(
            f'<polygon class="cell" style="animation-delay:{delay:.2f}s" points="{hexagon(cx, cy, R - 3)}" '
            f'fill="{t["honey"] if honey else "none"}" stroke="{t["honey"] if honey else t["muted"]}" '
            f'stroke-opacity="{1 if honey else .55}" stroke-width="2"/>')
    cols = [("01", "Backend", "PHP · Symfony · Docker"),
            ("02", "Founder", "Mumcord, voice chat"),
            ("03", "Based in", "Bremen, Germany")]
    foot = "".join(
        text(64 + i * 360, 488, n, 15, t["honey"], MONO, 700)
        + text(104 + i * 360, 488, k.upper(), 15, t["muted"], MONO, 400, spacing=1.5)
        + text(64 + i * 360, 520, v, 22, t["ink"], SANS, 600)
        for i, (n, k, v) in enumerate(cols))
    style = (".cell{opacity:0;transform-box:fill-box;transform-origin:center;"
             "animation:pop .55s cubic-bezier(.2,.8,.3,1.25) forwards}"
             "@keyframes pop{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:scale(1)}}"
             ".rise{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) forwards}"
             "@keyframes rise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}")
    body = (
        text(64, 58, "TOBEE94", 15, t["ink"], MONO, 700, spacing=3)
        + text(W - 64, 58, "53.08° N  8.80° E", 15, t["muted"], MONO, anchor="end", spacing=1.5)
        + f'<rect x="64" y="76" width="{W - 128}" height="4" fill="{t["ink"]}"/>'
        + f'<g class="rise" style="animation-delay:.05s">{text(56, 230, "Tobias", 150, t["ink"], SANS, 800, spacing=-7)}</g>'
        + f'<g class="rise" style="animation-delay:.18s">{text(56, 372, f"Vorwachs<tspan fill={chr(34)}{t["honey"]}{chr(34)}>.</tspan>", 150, t["ink"], SANS, 800, spacing=-7)}</g>'
        + "".join(cells)
        + f'<rect x="64" y="438" width="{W - 128}" height="1.5" fill="{t["rule"]}"/>'
        + foot
    )
    return svg(W, H, "Tobias Vorwachs. Backend developer, founder of Mumcord, based in Bremen.", body, style)


# ── section headings ─────────────────────────────────────────────────────────

def section(num, title, caption):
    def build(t):
        W, H = 1200, 170
        body = (f'<rect x="0" y="34" width="{W}" height="4" fill="{t["ink"]}"/>'
                + text(0, 84, num, 20, t["honey"], MONO, 700, spacing=2)
                + text(-4, 152, escape(title), 76, t["ink"], SANS, 800, spacing=-3)
                + text(W, 84, escape(caption.upper()), 15, t["muted"], MONO, anchor="end", spacing=2))
        return svg(W, H, f"{num} {title}", body)
    return build


# ── project cards ────────────────────────────────────────────────────────────

def card(idx, owner, name, desc, tag, meta):
    def build(t):
        W, H = 400, 240
        lines = wrap(desc, 44)[:3]
        body = (f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="none" stroke="{t["rule"]}" stroke-width="2"/>'
                f'<rect x="0" y="0" width="{W}" height="5" fill="{t["ink"]}"/>'
                + text(28, 46, idx, 14, t["honey"], MONO, 700, spacing=1.5)
                + text(W - 28, 46, escape(tag.upper()), 13, t["muted"], MONO, anchor="end", spacing=2)
                + text(26, 90, escape(name), 30 if len(name) < 17 else 26, t["ink"], SANS, 800, spacing=-1)
                + "".join(text(28, 124 + i * 22, escape(l), 15.5, t["muted"]) for i, l in enumerate(lines))
                + f'<rect x="28" y="{H - 54}" width="{W - 56}" height="1.5" fill="{t["rule"]}"/>'
                + text(28, H - 24, escape(meta), 13.5, t["ink"], MONO, spacing=.5)
                + text(W - 28, H - 24, escape(owner) + f' <tspan fill="{t["honey"]}">↗</tspan>', 13.5, t["muted"], MONO, anchor="end"))
        return svg(W, H, f"{owner}/{name}: {desc}", body)
    return build


def more_card(t):
    W, H = 400, 240
    body = (f'<rect width="{W}" height="{H}" fill="{t["honey"]}"/>'
            + text(28, 46, "+", 18, t["on_honey"], MONO, 700)
            + text(26, 120, "Everything", 34, t["on_honey"], SANS, 800, spacing=-1.5)
            + text(26, 158, "else is here.", 34, t["on_honey"], SANS, 800, spacing=-1.5)
            + f'<rect x="28" y="{H - 54}" width="{W - 56}" height="1.5" fill="{t["on_honey"]}" fill-opacity=".35"/>'
            + text(28, H - 24, "fuewa.systems/open-source", 13.5, t["on_honey"], MONO, 700)
            + text(W - 28, H - 24, "↗", 16, t["on_honey"], MONO, 700, anchor="end"))
    return svg(W, H, "All projects on fuewa.systems/open-source", body)


# ── toolbox + footer ─────────────────────────────────────────────────────────

TOOLS = [["PHP", "Symfony", "Rust", "Tauri", "TypeScript"],
         ["Docker", "MySQL", "Redis", "Nginx", "Linux", "Git"]]


def toolbox(t):
    W, H, size = 1200, 190, 54
    slash = f'<tspan fill="{t["honey"]}" font-weight="300"> / </tspan>'
    rows = "".join(text(0, 64 + r * 82, slash.join(row), size, t["ink"], SANS, 800, spacing=-1.5)
                   for r, row in enumerate(TOOLS))
    return svg(W, H, "Toolbox: " + ", ".join(sum(TOOLS, [])), rows)


def footer(t):
    W, H = 1200, 110
    body = (f'<rect x="0" y="20" width="{W}" height="4" fill="{t["ink"]}"/>'
            f'<polygon points="{hexagon(12, 72, 12)}" fill="{t["honey"]}"/>'
            + text(38, 78, "TOBIAS VORWACHS  ·  BREMEN", 15, t["ink"], MONO, 700, spacing=2)
            + text(W, 78, "fuewa.systems   mumcord.app   github.com/ToBee94", 15, t["muted"], MONO, anchor="end", spacing=1))
    return svg(W, H, "Tobias Vorwachs, Bremen. fuewa.systems, mumcord.app", body)


CARDS = {
    "mumbot": ("01", "Mumcord", "mumbot", "Bots for any Mumble server: a webhook bot for alerts and CI, plus a scripted test bot.", "Bot", "Rust · AGPL-3.0"),
    "mumpeer": ("02", "Mumcord", "mumpeer", "Relay for Mumcord's peer-to-peer features like screen sharing. Hides IPs, verified users only.", "Relay", "Coming soon"),
    "shellock": ("01", "ToBee94", "Shellock", "Multi-tenant SSH key management with central control, role-based access and audit logging.", "Security", "PHP · Symfony · Docker"),
    "cloudns": ("02", "ToBee94", "cloudns-api-php", "PHP SDK for the ClouDNS API. DNS zones and records without the boilerplate.", "SDK", "PHP · MIT"),
    "acinfinity": ("03", "ToBee94", "ac-infinity-php", "PHP SDK for the AC Infinity API. Typed access to controllers and sensors.", "SDK", "PHP · MIT"),
    "phpass": ("04", "ToBee94", "phpass", "Openwall's phpass password hashing, with namespaces and Composer. Based on 0.3.", "Crypto", "PHP"),
    "growdata-hub": ("05", "unserioes24", "growdata-hub", "Open, structured data on grow lights, tents, filters, fans, controllers and compatible ecosystems.", "Open data", "JavaScript · MIT"),
    "wordpress-api": ("06", "Die PARTEI", "wordpress-api", "PHP SDK for the WordPress REST API. Posts, pages, menus, search, settings, Polylang.", "SDK", "PHP · MIT"),
    "headless-mode": ("07", "Die PARTEI", "headless-mode", "Turns WordPress into a headless CMS: frontend off, view links redirected, signed previews.", "WordPress", "PHP · GPL-2.0"),
    "block-manager": ("08", "Die PARTEI", "block-manager", "Switch individual Gutenberg blocks on or off through a simple settings dialog.", "WordPress", "PHP · GPL-2.0"),
    "eu-captcha": ("09", "Die PARTEI", "EU-Politics-CAPTCHA", "A CAPTCHA built from memes and scandals of the European Parliament.", "Satire", "JavaScript · MIT"),
}


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    write("header", header)
    write("s1-mumcord", section("01", "Mumcord", "Voice & chat for any Mumble server"))
    write("s2-open-source", section("02", "Open source", "SDKs, plugins, tools"))
    write("s3-toolbox", section("03", "Toolbox", "What I reach for"))
    write("toolbox", toolbox)
    write("footer", footer)
    write("card-more", more_card)
    for slug, args in CARDS.items():
        write(f"card-{slug}", card(*args))
    print(len(list(OUT.glob("*.svg"))), "SVGs written to", OUT)
