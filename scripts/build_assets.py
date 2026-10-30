#!/usr/bin/env python3
"""Generates assets/*.svg (light + dark) in the fuewa.systems look.

Fonts (SIL OFL, see scripts/fonts/) are subset per SVG and embedded, Mumcord
screenshots are fetched from the Mumcord repo and embedded as JPEG.

    python3 scripts/build_assets.py
"""
import base64
import io
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "assets"
CACHE = ROOT / ".cache"
SHOTS = "https://raw.githubusercontent.com/Mumcord/mumcord/main/docs/images/screenshots/"

FONTS = {
    "display": ("BricolageGrotesque", "Bricolage Grotesque", "ui-sans-serif,system-ui,sans-serif"),
    "sans": ("SchibstedGrotesk", "Schibsted Grotesk", "ui-sans-serif,system-ui,sans-serif"),
    "mono": ("JetBrainsMono", "JetBrains Mono", "ui-monospace,SFMono-Regular,monospace"),
}

# Tokens from fuewa.systems
THEMES = {
    "light": dict(bg="#f5f1ea", fg="#1a1814", muted="#5c564d", faint="#8d877d",
                  hair="#1a18141f", dot="#1a181426", grad=("#e9a400", "#e35a06", "#d81f73"),
                  accent="#ad4100", cta="#1a1814", cta_fg="#f5f1ea", cta_muted="#a7a197"),
    "dark": dict(bg="#0e0d0b", fg="#fff8ee", muted="#a7a197", faint="#6b6459",
                 hair="#fff8ee1f", dot="#fff8ee17", grad=("#fcb900", "#ff6a13", "#ee2c82"),
                 accent="#ff7a2b", cta="#161512", cta_fg="#fff8ee", cta_muted="#a7a197"),
}


# ── fonts ────────────────────────────────────────────────────────────────────

_metrics = {}


def advance(font, weight, ch):
    key = (font, weight)
    if key not in _metrics:
        tt = TTFont(ROOT / "fonts" / f"{FONTS[font][0]}.woff2")
        axis = tt["fvar"].axes[0]
        tt = instancer.instantiateVariableFont(tt, {"wght": max(axis.minValue, min(axis.maxValue, weight))})
        _metrics[key] = (tt.getBestCmap(), tt["hmtx"].metrics, tt["head"].unitsPerEm)
    cmap, hmtx, upm = _metrics[key]
    glyph = cmap.get(ord(ch))
    return (hmtx[glyph][0] if glyph else upm * 0.55) / upm


def measure(s, font, size, weight=400, spacing=0):
    return sum(advance(font, weight, c) * size + spacing for c in s)


def wrap(s, font, size, width, weight=400):
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if cur and measure(trial, font, size, weight) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def font_face(font, chars):
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga"]
    tt = TTFont(ROOT / "fonts" / f"{FONTS[font][0]}.woff2")
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(chars)))
    sub.subset(tt)
    buf = io.BytesIO()
    tt.flavor = "woff2"
    tt.save(buf)
    lo, hi = tt["fvar"].axes[0].minValue, tt["fvar"].axes[0].maxValue
    return (f'@font-face{{font-family:"{FONTS[font][1]}";font-weight:{lo:.0f} {hi:.0f};'
            f'src:url(data:font/woff2;base64,{base64.b64encode(buf.getvalue()).decode()}) format("woff2")}}')


class Doc:
    """Collects SVG markup and the characters used per font, for subsetting."""

    def __init__(self, w, h, t, label):
        self.w, self.h, self.t, self.label = w, h, t, label
        self.defs, self.body, self.css, self.chars = [], [], [], {}

    def text(self, x, y, s, font, size, fill, weight=400, anchor="start", spacing=0, attrs=""):
        self.chars.setdefault(font, set()).update(s)
        fam = f"'{FONTS[font][1]}',{FONTS[font][2]}"
        self.body.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" font-weight="{weight}" '
            f'letter-spacing="{spacing}" text-anchor="{anchor}" fill="{fill}" {attrs}>{escape(s)}</text>')

    def add(self, *parts):
        self.body.extend(parts)

    def svg(self):
        faces = "".join(font_face(f, c) for f, c in self.chars.items())
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.label)}">'
                f'<style>{faces}{"".join(self.css)}</style>'
                f'<defs>{"".join(self.defs)}</defs>{"".join(self.body)}</svg>')


# ── shared pieces ────────────────────────────────────────────────────────────

def gradient(d, gid, x0, x1, animate=False):
    a, b, c = d.t["grad"]
    anim = ('<animateTransform attributeName="gradientTransform" type="translate" '
            f'values="0 0;{(x1 - x0) * .35:.0f} 0;0 0" dur="9s" repeatCount="indefinite"/>') if animate else ""
    d.defs.append(
        f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x0:.0f}" y1="0" x2="{x1:.0f}" y2="0" '
        f'spreadMethod="reflect"><stop offset="0" stop-color="{a}"/><stop offset=".5" stop-color="{b}"/>'
        f'<stop offset="1" stop-color="{c}"/>{anim}</linearGradient>')


def panel(d, radius=22, fill=None):
    t = d.t
    d.defs.append(f'<clipPath id="panel"><rect width="{d.w}" height="{d.h}" rx="{radius}"/></clipPath>')
    d.defs.append(f'<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">'
                  f'<circle cx="12" cy="12" r="1.1" fill="{t["dot"]}"/></pattern>')
    gradient(d, "bar", 0, d.w)
    d.add(f'<g clip-path="url(#panel)"><rect width="{d.w}" height="{d.h}" fill="{fill or t["bg"]}"/>'
          f'<rect width="{d.w}" height="{d.h}" fill="url(#dots)"/>'
          f'<rect width="{d.w}" height="4" fill="url(#bar)"/></g>')


def panel_border(d, radius=22):
    d.add(f'<rect x=".75" y=".75" width="{d.w - 1.5}" height="{d.h - 1.5}" rx="{radius}" fill="none" '
          f'stroke="{d.t["hair"]}" stroke-width="1.5"/>')


def eyebrow(d, x, y, label, color=None):
    d.add(f'<rect x="{x}" y="{y - 5}" width="32" height="2" fill="{d.t["accent"]}"/>')
    d.text(x + 46, y, label.upper(), "mono", 14, color or d.t["muted"], 500, spacing=3.2)


def headline(d, x, y, s, size, fill, gid=None, reveal=0.0, weight=700):
    """Big display line; gradient lines get a left-to-right reveal like on fuewa.systems."""
    spacing = -size * 0.035
    w = measure(s, "display", size, weight, spacing)
    if gid:
        gradient(d, gid, x, x + w, animate=True)
        cid, k = f"clip-{gid}", reveal / (reveal + 1.1)
        d.defs.append(
            f'<clipPath id="{cid}"><rect x="{x - 10}" y="{y - size}" height="{size * 1.4}" width="{w + 30:.0f}">'
            f'<animate attributeName="width" values="0;0;{w + 30:.0f}" keyTimes="0;{k:.3f};1" dur="{reveal + 1.1}s" '
            f'fill="freeze" calcMode="spline" keySplines="0 0 1 1;.2 .7 .2 1"/></rect></clipPath>')
        d.text(x, y, s, "display", size, f"url(#{gid})", weight, spacing=spacing, attrs=f'clip-path="url(#{cid})"')
    else:
        d.text(x, y, s, "display", size, fill, weight, spacing=spacing)
    return w


def corners(d, x0, y0, x1, y1, size=9):
    for cx, cy in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
        d.add(f'<rect class="fade" x="{cx - size / 2:.1f}" y="{cy - size / 2:.1f}" width="{size}" height="{size}" '
              f'fill="none" stroke="{d.t["accent"]}" stroke-width="1.5"/>')


def swash(d, x0, x1, y, gid, begin=1.0):
    path = (f"M{x0:.0f} {y + 4:.0f} C {x0 + (x1 - x0) * .3:.0f} {y - 6:.0f}, "
            f"{x0 + (x1 - x0) * .7:.0f} {y + 10:.0f}, {x1:.0f} {y - 2:.0f}")
    length = (x1 - x0) * 1.05
    d.add(f'<path d="{path}" fill="none" stroke="url(#{gid})" stroke-width="6" stroke-linecap="round" '
          f'stroke-dasharray="{length:.0f}">'
          f'<animate attributeName="stroke-dashoffset" values="{length:.0f};{length:.0f};0" '
          f'keyTimes="0;{begin / (begin + .9):.3f};1" dur="{begin + .9}s" fill="freeze" calcMode="spline" '
          f'keySplines="0 0 1 1;.4 0 .2 1"/></path>')


def arrow(x, y, size, color, width=2.0, diagonal=True):
    """Arrow drawn as a path (the latin font subsets have no arrow glyphs)."""
    s = size / 2
    if diagonal:
        return (f'<path d="M{x - s:.1f} {y + s:.1f} L{x + s:.1f} {y - s:.1f} M{x - s * .3:.1f} {y - s:.1f} '
                f'H{x + s:.1f} V{y + s * .3:.1f}" fill="none" stroke="{color}" stroke-width="{width}" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')
    return (f'<path d="M{x - s:.1f} {y:.1f} H{x + s:.1f} M{x + s * .35:.1f} {y - s * .6:.1f} L{x + s:.1f} {y:.1f} '
            f'L{x + s * .35:.1f} {y + s * .6:.1f}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def button(d, x, y, label, solid, diagonal=False):
    t = d.t
    w = measure(label, "sans", 18, 600) + 74
    fg = t["bg"] if solid else t["fg"]
    d.add(f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="52" rx="8" fill="{t["fg"] if solid else "none"}" '
          f'stroke="{t["fg"] if solid else t["hair"]}" stroke-width="1.5"/>')
    d.text(x + 24, y + 32, label, "sans", 18, fg, 600)
    d.add(arrow(x + w - 30, y + 26, 13, fg, 2, diagonal))
    return w


# "both" fill keeps everything visible where animations don't run.
BASE_CSS = (".fade{animation:fade .6s ease-out 1.2s both}"
            "@keyframes fade{from{opacity:0}to{opacity:1}}"
            ".rise{animation:rise .9s cubic-bezier(.2,.7,.2,1) both}"
            "@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}")


def topline(d, left, right):
    d.text(64, 46, left, "mono", 13, d.t["muted"], 500, spacing=1.5)
    d.text(d.w - 64, 46, right, "mono", 13, d.t["muted"], 500, anchor="end", spacing=1.5)
    d.add(f'<rect x="0" y="70" width="{d.w}" height="1" fill="{d.t["hair"]}"/>')


# ── hero ─────────────────────────────────────────────────────────────────────

def hero(t):
    d = Doc(1200, 640, t, "Tobias Vorwachs. I build backends. And Mumcord.")
    d.css.append(BASE_CSS)
    panel(d)
    topline(d, "BACKEND ENGINEER  ·  FUEWA.SYSTEMS", "53.08° N  ·  8.80° E")
    d.add('<g class="rise">')
    eyebrow(d, 64, 150, "Tobias Vorwachs  —  @ToBee94")
    d.add('</g><g class="rise" style="animation-delay:.12s">')
    headline(d, 58, 282, "I build backends.", 118, t["fg"])
    d.add("</g>")
    x2 = 210
    w2 = headline(d, x2, 412, "And Mumcord.", 118, None, gid="g-hero", reveal=.45)
    corners(d, x2 - 18, 412 - 100, x2 + w2 + 18, 412 + 34)
    d.add('<g class="rise" style="animation-delay:.6s">')
    for i, line in enumerate(["Backend engineer in Bremen. PHP and Symfony",
                              "for clients, Rust for my own voice client."]):
        d.text(64, 528 + i * 32, line, "sans", 21, t["muted"])
    bx = 1136 - measure("mumcord.app", "sans", 18, 600) - 74
    button(d, bx, 518, "mumcord.app", False, diagonal=True)
    button(d, bx - 14 - measure("fuewa.systems", "sans", 18, 600) - 74, 518, "fuewa.systems", True)
    d.add("</g>")
    panel_border(d)
    return d.svg()


# ── mumcord showcase ─────────────────────────────────────────────────────────

SHOWCASE = ["main-dark", "theme-custom-synthwave", "theme-custom-lava", "screen-share-viewer",
            "theme-custom-toxic", "theme-deep-ocean-dark", "theme-custom-candy", "watch-party-widget"]


def shot(name):
    CACHE.mkdir(exist_ok=True)
    path = CACHE / f"{name}.jpg"
    if not path.exists():
        raw = urllib.request.urlopen(SHOTS + name + ".png").read()
        img = Image.open(io.BytesIO(raw)).convert("RGB").resize((720, 450), Image.LANCZOS)
        img.save(path, "JPEG", quality=80, optimize=True, progressive=True)
    return base64.b64encode(path.read_bytes()).decode()


def mumcord(t):
    W, H = 1200, 940
    d = Doc(W, H, t, "01 Mumcord. Voice chat, finally modern. A desktop client for any Mumble server.")
    d.css.append(BASE_CSS)
    panel(d)
    topline(d, "01  ·  MUMCORD", "RUST  ·  TAURI  ·  TYPESCRIPT")
    eyebrow(d, 64, 140, "Founder & maintainer")
    headline(d, 58, 254, "Voice chat,", 104, t["fg"])
    w = headline(d, 58, 368, "finally modern.", 104, None, gid="g-mc", reveal=.35)
    swash(d, 66, 58 + w - 10, 396, "g-mc", begin=1.2)

    desc = ("A desktop client for any standard Mumble server. Chat you'd actually use, "
            "push-to-talk on mouse buttons, several servers at once, no telemetry. "
            "Nothing to change on the server.")
    for i, line in enumerate(wrap(desc, "sans", 20, 560)):
        d.text(64, 466 + i * 31, line, "sans", 20, t["muted"])
    facts = [("PLATFORMS", "Windows · macOS · Linux"), ("SERVERS", "any Mumble 1.4+"),
             ("LICENSE", "AGPL-3.0"), ("PRIVACY", "no telemetry, TLS always")]
    for i, (k, v) in enumerate(facts):
        y = 462 + i * 30
        d.add(f'<rect x="740" y="{y + 10}" width="396" height="1" fill="{t["hair"]}"/>')
        d.text(740, y, k, "mono", 12.5, t["faint"], 500, spacing=2)
        d.text(1136, y, v, "sans", 17, t["fg"], 500, anchor="end")

    # Tilted, endlessly scrolling screenshot strip.
    cw, ch, gap, top = 400, 250, 34, 610
    d.defs.append('<filter id="shadow" x="-20%" y="-20%" width="140%" height="160%">'
                  '<feDropShadow dx="0" dy="14" stdDeviation="14" flood-color="#000" flood-opacity=".35"/></filter>'
                  '<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  '<stop offset=".08" stop-color="#fff"/><stop offset=".92" stop-color="#fff"/>'
                  '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                  f'<mask id="fade-x"><rect width="{W}" height="{H}" fill="url(#edge)"/></mask>'
                  f'<clipPath id="shot"><rect width="{cw}" height="{ch}" rx="12"/></clipPath>')
    for name in SHOWCASE:
        d.defs.append(f'<image id="s-{name}" width="{cw}" height="{ch}" preserveAspectRatio="xMidYMid slice" '
                      f'href="data:image/jpeg;base64,{shot(name)}"/>')
    period = len(SHOWCASE) * (cw + gap)
    d.css.append(f".strip{{animation:strip 48s linear infinite}}"
                 f"@keyframes strip{{to{{transform:translateX(-{period}px)}}}}")
    tilts = [-3, 2, -1.5, 3, -2.5, 1.5, -2, 2.5]
    cards = []
    for rep in range(2):
        for i, name in enumerate(SHOWCASE):
            x = (rep * len(SHOWCASE) + i) * (cw + gap)
            y = top + (14 if i % 2 else 0)
            cards.append(
                f'<g transform="translate({x} {y}) rotate({tilts[i]} {cw / 2} {ch / 2})" filter="url(#shadow)">'
                f'<use href="#s-{name}" clip-path="url(#shot)"/>'
                f'<rect x=".5" y=".5" width="{cw - 1}" height="{ch - 1}" rx="12" fill="none" '
                f'stroke="#fff" stroke-opacity=".12"/></g>')
    d.add(f'<g clip-path="url(#panel)"><g mask="url(#fade-x)"><g class="strip">{"".join(cards)}</g></g></g>')
    d.add(f'<rect x="0" y="{H - 52}" width="{W}" height="1" fill="{t["hair"]}"/>')
    d.text(64, H - 20, "MUMCORD.APP", "mono", 13, t["fg"], 600, spacing=2)
    d.text(W - 64, H - 20, "GITHUB.COM/MUMCORD", "mono", 13, t["muted"], 500, anchor="end", spacing=2)
    panel_border(d)
    return d.svg()


# ── open source list (transparent, sits on GitHub's page background) ────────

def os_header(t):
    d = Doc(1200, 330, t, "02 Open source. Giving back.")
    eyebrow(d, 4, 60, "02  ·  Open source")
    headline(d, 0, 170, "Giving back:", 92, t["fg"])
    w = headline(d, 0, 272, "Open source.", 92, None, gid="g-os", reveal=.3)
    swash(d, 6, w - 8, 298, "g-os", begin=1.1)
    for i, line in enumerate(wrap("Libraries, SDKs and plugins I publish on GitHub: on my own "
                                  "account, in the Mumcord org and for Die PARTEI.", "sans", 20, 360)):
        d.text(1196, 206 + i * 31, line, "sans", 20, t["muted"], anchor="end")
    return d.svg()


def os_row(num, owner, name, desc, lang, license_, last=False):
    def build(t):
        lines = wrap(desc, "sans", 19, 390)
        H = max(132, 44 + len(lines) * 28 + 22)
        d = Doc(1200, H, t, f"{owner}/{name}: {desc}")
        d.add(f'<rect width="1200" height="1.5" fill="{t["hair"]}"/>')
        if last:
            d.add(f'<rect y="{H - 1.5}" width="1200" height="1.5" fill="{t["hair"]}"/>')
        d.text(4, 56, num, "mono", 15, t["faint"], 500)
        d.text(84, 56, f"{owner} /", "mono", 15, t["muted"])
        size = 40 if measure(name, "display", 40, 650) < 440 else 34
        d.text(82, 100, name, "display", size, t["fg"], 650, spacing=-1)
        for i, line in enumerate(lines):
            d.text(580, 56 + i * 28, line, "sans", 19, t["muted"])
        d.text(1010, 54, lang.upper(), "mono", 13, t["muted"], 500, spacing=2.2)
        if license_:
            d.text(1010, 76, license_, "mono", 13, t["faint"], 500, spacing=1)
        d.add(f'<circle cx="1170" cy="48" r="25" fill="none" stroke="{t["hair"]}" stroke-width="1.5"/>'
              + arrow(1170, 48, 11, t["fg"], 1.8))
        return d.svg()
    return build


ROWS = [
    ("mumbot", "Mumcord", "mumbot", "Bots for any Mumble server: a webhook bot for alerts and CI, plus a scripted test bot.", "Rust", "AGPL-3.0"),
    ("mumpeer", "Mumcord", "mumpeer", "Relay for Mumcord's peer-to-peer features like screen sharing. Hides IPs, verified users only.", "Soon", ""),
    ("growdata-hub", "unserioes24", "growdata-hub", "Open, structured data on grow equipment: lights, tents, filters, fans, controllers and compatible ecosystems.", "JavaScript", "MIT"),
    ("shellock", "ToBee94", "Shellock", "Multi-tenant SSH key management with central control, role-based access, a Dockerized Symfony stack and audit logging.", "PHP", ""),
    ("cloudns", "ToBee94", "cloudns-api-php", "PHP SDK for the ClouDNS API.", "PHP", "MIT"),
    ("acinfinity", "ToBee94", "ac-infinity-php", "PHP SDK for the AC Infinity API.", "PHP", "MIT"),
    ("phpass", "ToBee94", "phpass", "Openwall's phpass, prepared for namespaces and Composer (based on release 0.3).", "PHP", ""),
    ("wordpress-api", "Die-PARTEI-in-Europa", "wordpress-api", "PHP SDK for the WordPress REST API: posts, pages, menus, search and settings, with pagination and Polylang support.", "PHP", "MIT"),
    ("headless-mode", "Die-PARTEI-in-Europa", "headless-mode", "Turns WordPress into a headless CMS: disables the frontend, redirects view links and adds a signed preview endpoint.", "PHP", "GPL-2.0"),
    ("block-manager", "Die-PARTEI-in-Europa", "block-manager", "Enable or disable individual Gutenberg blocks through a simple settings dialog. Works with any registered block.", "PHP", "GPL-2.0"),
    ("eu-captcha", "Die-PARTEI-in-Europa", "EU-Politics-CAPTCHA", "A simple CAPTCHA based on memes and scandals from the European Parliament.", "JavaScript", "MIT"),
]


# ── stack ticker ─────────────────────────────────────────────────────────────

STACK = ["PHP", "Symfony", "Rust", "Tauri", "TypeScript", "Docker", "MySQL", "Redis", "Nginx", "Linux", "Git"]


def ticker(t):
    W, H, size = 1200, 130, 58
    d = Doc(W, H, t, "Stack: " + ", ".join(STACK))
    gradient(d, "g-dot", 0, 20)
    items, x, period = [], 0.0, 0.0
    for rep in range(2):
        for word in STACK:
            d.chars.setdefault("display", set()).update(word)
            items.append(f'<text x="{x:.1f}" y="88" font-family="\'Bricolage Grotesque\',sans-serif" '
                         f'font-size="{size}" font-weight="650" letter-spacing="-1.5" fill="{t["fg"]}">{word}</text>')
            x += measure(word, "display", size, 650, -1.5) + 30
            items.append(f'<rect x="{x:.1f}" y="58" width="14" height="14" rx="3" fill="url(#g-dot)" '
                         f'transform="rotate(45 {x + 7:.1f} 65)"/>')
            x += 14 + 30
        if rep == 0:
            period = x
    d.defs.append('<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  '<stop offset=".1" stop-color="#fff"/><stop offset=".9" stop-color="#fff"/>'
                  '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                  f'<mask id="fade-x"><rect width="{W}" height="{H}" fill="url(#edge)"/></mask>')
    d.css.append(f".tick{{animation:tick 40s linear infinite}}@keyframes tick{{to{{transform:translateX(-{period:.1f}px)}}}}")
    d.add(f'<rect width="{W}" height="1.5" fill="{t["hair"]}"/><rect y="{H - 1.5}" width="{W}" height="1.5" fill="{t["hair"]}"/>'
          f'<g mask="url(#fade-x)"><g class="tick">{"".join(items)}</g></g>')
    return d.svg()


# ── closing panel ────────────────────────────────────────────────────────────

def cta(t):
    W, H = 1200, 420
    d = Doc(W, H, t, "Got a problem? Let's solve it. fuewa.systems")
    d.css.append(BASE_CSS)
    panel(d, fill=t["cta"])
    eyebrow(d, 64, 96, "03  ·  Get in touch", t["cta_muted"])
    headline(d, 58, 208, "Got a problem?", 96, t["cta_fg"])
    w = headline(d, 150, 312, "Let's solve it.", 96, None, gid="g-cta", reveal=.3)
    corners(d, 150 - 18, 312 - 82, 150 + w + 18, 312 + 30)
    d.text(64, 376, "FUEWA.SYSTEMS   ·   MUMCORD.APP   ·   GITHUB.COM/TOBEE94", "mono", 13, t["cta_muted"], 500, spacing=2)
    d.add('<circle cx="1100" cy="352" r="36" fill="url(#g-cta)"/>' + arrow(1100, 352, 18, "#0e0d0b", 2.6))
    panel_border(d)
    return d.svg()


def write(name, build):
    for mode, t in THEMES.items():
        (OUT / f"{name}-{mode}.svg").write_text(build(t))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    write("hero", hero)
    write("mumcord", mumcord)
    write("os-header", os_header)
    for i, (slug, *row) in enumerate(ROWS):
        write(f"os-{slug}", os_row(f"{i + 1:02d}", *row, last=i == len(ROWS) - 1))
    write("stack", ticker)
    write("cta", cta)
    total = sum(p.stat().st_size for p in OUT.glob("*.svg"))
    print(f"{len(list(OUT.glob('*.svg')))} SVGs, {total / 1024:.0f} KiB, in {OUT}")
