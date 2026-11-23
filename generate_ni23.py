#!/usr/bin/env python3
"""news-image-20261123 generator — "Monday 23 November 2026" broadsheet.

Renders a 1024x1024 newspaper front page: 36 stories (3 illustrated leads,
10 illustrated cards, 23 briefs), six-number stat strip, UTC timeline
strip, six-segment region bar, dotted world map (navy block, cream dots)
with pins for the 13 pictured stories, and a full-width DATE CHECK box.

Formula (from the ni22 top-3 study + pixel dissection of the leaders):
  * newspaper front page, cream paper, navy + red, kicker
    "THE WORLD IN ONE DAY", huge date headline "Monday 23 November 2026";
  * 36 stories, every one dated Monday 23 November 2026 (it happened on
    Monday where it happened, or was first reported on Monday — any
    earlier timing is disclosed in the story body), source named beside
    each story, claim labels REPORTED / CLAIM / FORECAST on every story;
  * the world map is drawn from continent polygons as DOTS, 150 px tall,
    continents recognisable, every pin on land;
  * the strap sits between two rules with clear padding — no rule ever
    touches the strap text;
  * lead banners are 150 px tall, one scene each, with a consistent
    white stat chip top-right and red tag chip top-left;
  * every secondary uses the same chip format: a label, or a label plus
    one number that its headline explains — never a bare unexplained
    number;
  * DATE CHECK is a full-width box ("CHECKED, AND LEFT OUT ON PURPOSE");
  * every region with stories is a segment of the region bar;
  * the "also on" list is black text on the paper, roomy leading.

All artwork is drawn programmatically in this file (flat-vector style);
no photographs, no external assets beyond system fonts.

Usage: python3 generate_ni23.py
  -> output/entry.png (1024) + output/preview-300.png
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------ fonts
FONT_DIR = "/usr/share/fonts/truetype/noto"
SERIF_BLACK = f"{FONT_DIR}/NotoSerif-Black.ttf"
SERIF_BOLD = f"{FONT_DIR}/NotoSerif-Bold.ttf"
SERIF = f"{FONT_DIR}/NotoSerif-Regular.ttf"
SERIF_IT = f"{FONT_DIR}/NotoSerif-Italic.ttf"
SANS_BLACK = f"{FONT_DIR}/NotoSans-Black.ttf"
SANS_XB = f"{FONT_DIR}/NotoSans-ExtraBold.ttf"
SANS_BOLD = f"{FONT_DIR}/NotoSans-Bold.ttf"
SANS = f"{FONT_DIR}/NotoSans-Regular.ttf"

_font_cache = {}


def F(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


# ------------------------------------------------------------------ palette
PAPER = (248, 243, 228)
INK = (18, 18, 20)
NAVY = (22, 38, 76)
NAVY_DARK = (13, 22, 46)
RED = (178, 24, 32)
RED_DARK = (140, 16, 24)
GREY = (96, 96, 100)
RULE = (40, 40, 44)
CREAM_LINE = (214, 205, 182)
SKY_DAWN = (250, 196, 120)
SKY_DAY = (168, 205, 226)
SEA = (64, 110, 158)

W = H = 1024
M = 26                      # page margin
CW = W - 2 * M              # content width = 972

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img, "RGBA")

WARNINGS = []


# ------------------------------------------------------------------ helpers
def tw(s, f):
    return d.textlength(s, font=f)


def fit(s, path, start, max_w, min_size=7):
    """Largest font (<= start) whose rendering of s fits max_w."""
    size = start
    while size > min_size and tw(s, F(path, size)) > max_w:
        size -= 1
    if tw(s, F(path, size)) > max_w:
        WARNINGS.append(f"fit() could not fit {s!r} in {max_w}px")
    return F(path, size)


def wrap(s, f, max_w):
    words = s.split()
    lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if tw(t, f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def text_block(x, y, s, f, max_w, leading, fill=INK, max_lines=None):
    lines = wrap(s, f, max_w)
    if max_lines and len(lines) > max_lines:
        WARNINGS.append(f"text truncated to {max_lines} lines: {s[:40]!r}...")
        lines = lines[:max_lines]
    for i, ln in enumerate(lines):
        d.text((x, y + i * leading), ln, font=f, fill=fill)
    return y + len(lines) * leading


def centre(s, cx, y, f, fill=INK):
    d.text((cx - tw(s, f) / 2, y), s, font=f, fill=fill)


def chip(x, y, text, bg, fg=(255, 255, 255), font_size=9, pad_x=5, pad_y=2):
    f = F(SANS_BOLD, font_size)
    w_ = tw(text, f) + 2 * pad_x
    h_ = font_size + 2 * pad_y + 2
    d.rectangle([x, y, x + w_, y + h_], fill=bg)
    d.text((x + pad_x, y + pad_y), text, font=f, fill=fg)
    return w_, h_


def rule(x0, x1, y, fill=RULE, width=1):
    d.line([x0, y, x1, y], fill=fill, width=width)


def person(cx, cy, s, colour):
    """Tiny delegate/pedestrian figure: head + shoulders, s = height px."""
    r = s * 0.16
    d.ellipse([cx - r, cy - s, cx + r, cy - s + 2 * r], fill=colour)
    d.pieslice([cx - s * 0.30, cy - s + 2 * r - 2, cx + s * 0.30,
                cy + s * 0.35], 180, 360, fill=colour)


# ------------------------------------------------------------------ content
# Every story below is dated Monday 23 November 2026 (it happened on
# Monday where it happened, or was first reported / confirmed on Monday)
# and carries its source on the page. Labels: REPORTED = confirmed by the
# outlet named · CLAIM = one side's claim, unverified · FORECAST =
# scheduled, has not happened yet. See STORIES.md for the audit.

STRAP = ("COP31 ends with no deal · NATO meets over Poland missiles · "
         "Ukraine sinks a Russian warship off Libya")

STATS = [
    ("44h", "COP31 OVERTIME BEFORE NO DEAL"),
    ("7", "SEA DRONES SANK THE MERKURY"),
    ("22", "HORMUZ ATTACKS IN NOVEMBER"),
    ("99%", "OF GAZA AT CONTAMINATION RISK"),
    ("24", "DEAD IN CIKANDE FACTORY FIRE"),
    ("$61,300", "BITCOIN BACK ABOVE $60,000"),
]

# (name, count, colour) — counts are the true tally of the 36 stories.
# No Monday story is set in Oceania, so the bar has six segments.
REGIONS = [
    ("AMERICAS", 12, (104, 62, 140)),
    ("EUROPE", 11, (38, 84, 150)),
    ("ASIA-PACIFIC", 5, (44, 128, 74)),
    ("MIDDLE EAST", 3, (178, 24, 32)),
    ("AFRICA", 3, (196, 116, 30)),
    ("WORLD", 2, (13, 22, 46)),
]

UTC_STRIP = [
    ("04:07", "Two tankers mined"),
    ("05:28", "COP31 ends, no pact"),
    ("06:27", "Bitcoin $61,417"),
    ("08:57", "Dymer toll at 11"),
    ("09:01", "Hormuz: CRITICAL"),
    ("15:42", "States sue SpaceX"),
]

LEADS = [
    {
        "tag": "COP31: NO DEAL", "stat": "44 HRS",
        "kicker": "CLIMATE · ANTALYA", "label": "REPORTED",
        "headline": "COP31 ends with no deal — the longest summit ever",
        "body": ("Kurum concedes defeat at Sunday's closing plenary after "
                 "44 hours of overtime, as the EU and 130 nations reject "
                 "a text with no fossil-fuel language. Guterres speaks "
                 "on Monday."),
        "source": "UN NEWS / BBC · ANTALYA",
        "scene": "cop31",
    },
    {
        "tag": "NATO: EMERGENCY", "stat": "3 MISSILES",
        "kicker": "ALLIANCE · BRUSSELS", "label": "REPORTED",
        "headline": "NATO in emergency session over Poland",
        "body": ("The North Atlantic Council convenes in Brussels on "
                 "Monday over three Kh-101 cruise missiles that fell in "
                 "Poland on Friday. Warsaw wants stronger eastern-flank "
                 "air defences."),
        "source": "REUTERS / RMF24 · BRUSSELS",
        "scene": "nato",
    },
    {
        "tag": "LIBYA: SUNK", "stat": "7 DRONES",
        "kicker": "WAR AT SEA · BENGHAZI", "label": "REPORTED",
        "headline": "Ukraine sinks a Russian warship off Libya",
        "body": ("Zelenskyy announces on Monday that seven sea drones "
                 "sank the corvette Merkury in Benghazi on Sunday; the "
                 "cargo ship MV Angara was hit too. 2,400 km from the "
                 "front."),
        "source": "REUTERS / AP · KYIV",
        "scene": "libya",
    },
]

# Cards: (num, tag, stat, kicker place, label, headline, body, source, scene)
CARDS = [
    (4, "HORMUZ", "22 IN NOV", "STRAIT OF HORMUZ", "REPORTED",
     "Hormuz attacks hit a wartime high",
     "22 in November, 31 in October — the most since the war began.",
     "CNN / UKMTO", "tanker"),
    (5, "GAZA", "99% AT RISK", "GAZA", "REPORTED",
     "Gaza now a 'toxic wasteland', Oxfam warns",
     "Contamination indicators across over 99% of Gaza; 78% of land hit.",
     "OXFAM / CEOBS", "gaza"),
    (6, "CIKANDE", "24 DEAD", "INDONESIA", "REPORTED",
     "Cikande toll confirmed at 24; ~30 missing",
     "Fire broke out Saturday; search resumed Monday; DNA takes 2–3 weeks.",
     "REUTERS", "cikande"),
    (7, "GROK", "2 STATES SUE", "UNITED STATES", "REPORTED",
     "Two states sue SpaceX over Grok deepfakes",
     "Oregon and Virginia file Monday over Grok's sexualised deepfakes.",
     "REUTERS / WIRED", "grok"),
    (8, "SPUTNIK-S", "THIS YEAR", "SPACE", "CLAIM",
     "Russia 'ready to launch nuclear satellite'",
     "German media: NATO intel says Moscow plans a launch this year.",
     "NDR / WDR / SZ", "satellite"),
    (9, "DENMARK", "EU TALKS", "COPENHAGEN", "REPORTED",
     "Denmark takes Russian visa ban to EU",
     "Copenhagen puts EU-wide tourist-visa curbs to ambassadors on Monday.",
     "REUTERS", "denmark"),
    (10, "DYMER", "11 DEAD", "UKRAINE", "REPORTED",
     "Dymer toll reaches 11 as Kyiv region mourns",
     "A drone hit a five-storey block Sunday; a boy survived after 14 hours.",
     "AP / REUTERS", "dymer"),
    (11, "MARKETS", "+2.2% S&P", "WALL STREET", "REPORTED",
     "Markets rebound as Bitcoin retakes $60,000",
     "S&P futures +2.2%, Nasdaq +3% after Friday's rout; gold $3,620.",
     "MORNINGSTAR", "markets"),
    (12, "OVERSIGHT", "EO 14438", "WASHINGTON", "REPORTED",
     "White House tells agencies: clear Congress first",
     "Counsel tells agencies Monday: seek approval before Congress appearances.",
     "NPR / CNN", "whitehouse"),
    (13, "SEOUL", "1ST WOMAN", "SOUTH KOREA", "REPORTED",
     "Seoul: Lee names first woman spy chief",
     "Lee's reshuffle makes Kang Kum-sil the first woman to run the NIS.",
     "REUTERS", "seoul"),
]

# Briefs: (num, text, source, label-or-None) — REPORTED unless tagged.
BRIEFS = [
    (14, "Dhaka: Hasina jailed if she returns", "Reuters", None),
    (15, "Kryvyi Rih toll rises to 11", "AP", None),
    (16, "Kremlin accuses Kyiv of 'terrorist activity'", "Reuters", None),
    (17, "Bangkok: MP's royal-defamation verdict upheld", "AP", None),
    (18, "SEC probing Nvidia's accounting", "Reuters", None),
    (19, "Huang 'in contact' with China spies", "NYT", "CLAIM"),
    (20, "Anthropic shares rise after $81bn IPO", "Investopedia", None),
    (21, "Clayton to double as acting cyber chief", "Axios", None),
    (22, "Pentagon pressed over NSA deaths", "Legion", None),
    (23, "FedEx pilot of 1994 rescue dies at 82", "GEORGE", None),
    (24, "Zelenskyy: free paid-for Patriots", "Reuters", None),
    (25, "Warsaw: Poland will not invoke Article 4", "RMF24", None),
    (26, "Gripen held fire over Poland", "Reuters", None),
    (27, "MP: Iran stops 10 tankers a day", "IRNA", "CLAIM"),
    (28, "Libya: Merkury was refuelling under deal", "CNN", None),
    (29, "New reports detail Epstein's Russia links", "Nexus", None),
    (30, "Tokyo: Asia tech sell-off eases", "Morningstar", None),
    (31, "Zverev ends year as world No. 1 despite loss", "Times", None),
    (32, "NYC storm for Thanksgiving", "NOAA", "FORECAST"),
    (33, "California: high tides and rain hit Monday", "GEORGE", None),
    (34, "Bengals at Commanders tonight", "ESPN", "FORECAST"),
    (35, "Brentford v Everton", "Sportradar", "FORECAST"),
    (36, "Tripoli voices 'grave concern' over ports", "WSJ", None),
]

DATE_CHECK = (
    "Not Monday's news: Democrats' 258 House seats (Sunday) · the penny "
    "signed out (Friday) · Delta's 1,600-flight outage (Sunday) · Alcaraz "
    "wins in Turin (Sunday) · Liverpool 4–0 Man Utd (Sunday) · Hong Kong "
    "vote (Sunday) · Sparta II strike (Saturday) · Bolsonaro in ICU "
    "(Sunday) · El Chapo Isidro caught (Saturday) · Trump's Iran remarks "
    "(Friday) · Gaza truck strike (Saturday) · Riemann claim (Sunday)."
)

FOOTER = ("Every story here happened, or was first reported, on Monday "
          "23 November 2026. Claims are labelled as claimed; briefs are "
          "REPORTED unless tagged. Pictures and map: original, drawn in code.")


# ------------------------------------------------------------------ scenes
def scene_cop31(x, y, w, h):
    """Dawn sky, sun rising, long conference table with delegates —
    and an empty chair where the deal should be."""
    for i in range(h):
        t = i / h
        c = tuple(int(SKY_DAWN[j] * (1 - t) + SKY_DAY[j] * t) for j in range(3))
        d.line([x, y + i, x + w, y + i], fill=c)
    # sun low on the horizon, right of centre
    sx, sy, sr = x + w * 0.66, y + h * 0.52, h * 0.30
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 214, 90))
    d.ellipse([sx - sr * 0.72, sy - sr * 0.72, sx + sr * 0.72, sy + sr * 0.72],
              fill=(255, 228, 130))
    # distant headland + sea band
    d.polygon([(x, y + h * 0.62), (x + w * 0.2, y + h * 0.52),
               (x + w * 0.42, y + h * 0.62), (x + w, y + h * 0.62)],
              fill=(110, 130, 140))
    d.rectangle([x, y + h * 0.62, x + w, y + h * 0.70], fill=SEA)
    # conference table (perspective slab) and delegates
    ty = y + h * 0.82
    d.polygon([(x + w * 0.06, ty), (x + w * 0.94, ty),
               (x + w * 0.88, y + h), (x + w * 0.12, y + h)],
              fill=(96, 62, 34))
    d.rectangle([x + w * 0.06, ty - 3, x + w * 0.94, ty], fill=(70, 44, 22))
    cols = [(178, 24, 32), (22, 38, 76), (44, 128, 74), (196, 116, 30),
            (104, 62, 140), (30, 128, 128), (150, 60, 90), (70, 90, 160),
            (120, 120, 40), (160, 90, 40), (60, 130, 110)]
    for i, c in enumerate(cols):
        fx = x + w * (0.12 + 0.065 * i)
        person(fx, ty - 2, h * 0.34, c)
    # one empty chair at the head of the table — the missing deal
    ex = x + w * 0.88
    d.rectangle([ex - 7, ty - 26, ex + 7, ty - 2], outline=(60, 40, 24),
                width=2)
    d.line([ex - 7, ty - 14, ex + 7, ty - 14], fill=(60, 40, 24), width=2)
    # torn paper sheet on the table — the rejected text
    d.polygon([(x + w * 0.44, ty + 4), (x + w * 0.56, ty + 4),
               (x + w * 0.545, y + h - 4), (x + w * 0.455, y + h - 4)],
              fill=(252, 250, 240))
    d.line([x + w * 0.50, ty + 6, x + w * 0.50, y + h - 6],
           fill=(178, 24, 32), width=2)
    for k in range(3):
        ly = ty + 9 + k * 6
        d.line([x + w * 0.465, ly, x + w * 0.535, ly], fill=(150, 150, 150),
               width=1)


def scene_nato(x, y, w, h):
    """NATO council chamber: blue wall, compass-star emblem, long table
    with member flags and delegates, wall map with three red markers."""
    d.rectangle([x, y, x + w, y + h], fill=(28, 52, 96))
    # compass star emblem, centre-top: white circle, four-point star
    cx, cy, r = x + w * 0.50, y + h * 0.30, h * 0.24
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255),
              width=3)
    d.polygon([(cx, cy - r * 0.95), (cx + r * 0.16, cy - r * 0.16),
               (cx + r * 0.95, cy), (cx + r * 0.16, cy + r * 0.16),
               (cx, cy + r * 0.95), (cx - r * 0.16, cy + r * 0.16),
               (cx - r * 0.95, cy), (cx - r * 0.16, cy - r * 0.16)],
              fill=(255, 255, 255))
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(28, 52, 96))
    # wall map strip, left: simplified Poland outline with 3 red markers
    mx, my, mw, mh = x + w * 0.05, y + h * 0.10, w * 0.20, h * 0.34
    d.rectangle([mx, my, mx + mw, my + mh], fill=(16, 30, 62),
                outline=(120, 140, 180))
    d.polygon([(mx + 4, my + mh * 0.30), (mx + mw * 0.30, my + 4),
               (mx + mw - 4, my + mh * 0.25), (mx + mw * 0.85, my + mh * 0.55),
               (mx + mw * 0.60, my + mh - 4), (mx + mw * 0.25, my + mh * 0.80),
               (mx + 4, my + mh * 0.60)], fill=(70, 100, 140))
    for (px, py) in [(0.30, 0.35), (0.62, 0.55), (0.78, 0.30)]:
        d.ellipse([mx + mw * px - 3, my + mh * py - 3,
                   mx + mw * px + 3, my + mh * py + 3], fill=RED,
                  outline=(255, 255, 255))
    # long council table + flags + delegates
    ty = y + h * 0.78
    d.polygon([(x + w * 0.04, ty), (x + w * 0.96, ty),
               (x + w * 0.90, y + h), (x + w * 0.10, y + h)],
              fill=(84, 56, 32))
    d.rectangle([x + w * 0.04, ty - 3, x + w * 0.96, ty], fill=(58, 38, 20))
    flag_cols = [(178, 24, 32), (255, 255, 255), (22, 38, 76),
                 (44, 128, 74), (196, 116, 30), (104, 62, 140),
                 (30, 128, 128), (150, 60, 90), (70, 90, 160),
                 (120, 120, 40)]
    for i, c in enumerate(flag_cols):
        fx = x + w * (0.10 + 0.085 * i)
        d.rectangle([fx, ty - 16, fx + 12, ty - 6], fill=c,
                    outline=(200, 200, 200))
        d.line([fx + 2, ty - 16, fx + 2, ty - 2], fill=(200, 200, 200),
               width=1)
    cols = [(220, 220, 220), (200, 200, 210), (210, 210, 200),
            (230, 225, 215), (205, 205, 205)]
    for i, c in enumerate(cols):
        fx = x + w * (0.16 + 0.17 * i)
        person(fx, ty - 2, h * 0.30, c)


def scene_libya(x, y, w, h):
    """Night harbour at Benghazi: warship ablaze, drone boats closing in."""
    d.rectangle([x, y, x + w, y + h], fill=(14, 18, 40))
    # stars + moon
    for i in range(40):
        px = x + (i * 71) % int(w)
        py = y + (i * 41) % int(h * 0.45)
        d.point((px, py), fill=(220, 224, 240))
    d.ellipse([x + w * 0.86, y + h * 0.08, x + w * 0.93, y + h * 0.08 + w * 0.07],
              fill=(232, 232, 210))
    # sea with moonlight band
    d.rectangle([x, y + h * 0.66, x + w, y + h], fill=(24, 48, 84))
    d.rectangle([x + w * 0.80, y + h * 0.66, x + w * 0.96, y + h],
                fill=(60, 90, 130))
    # warship (Merkury) centre-right, listing, on fire
    sx = x + w * 0.52
    sy = y + h * 0.62
    d.polygon([(sx, sy), (sx + w * 0.34, sy), (sx + w * 0.30, sy + h * 0.10),
               (sx + w * 0.04, sy + h * 0.10)], fill=(52, 58, 66))
    d.rectangle([sx + w * 0.10, sy - h * 0.16, sx + w * 0.20, sy],
                fill=(70, 76, 84))
    d.rectangle([sx + w * 0.22, sy - h * 0.10, sx + w * 0.26, sy],
                fill=(70, 76, 84))
    d.line([sx + w * 0.15, sy - h * 0.16, sx + w * 0.15, sy - h * 0.26],
           fill=(90, 96, 104), width=2)
    # fireball + smoke over the ship
    fx, fy = sx + w * 0.16, sy - h * 0.22
    d.ellipse([fx - 16, fy - 12, fx + 16, fy + 12], fill=(255, 170, 50))
    d.ellipse([fx - 9, fy - 7, fx + 9, fy + 7], fill=(255, 220, 120))
    d.polygon([(fx - 10, fy - 8), (fx, fy - 26), (fx + 10, fy - 8)],
              fill=(240, 110, 36))
    for (ox, oy, orr) in [(0.10, 0.18, 10), (0.20, 0.12, 14), (0.28, 0.08, 18)]:
        d.ellipse([x + w * ox - orr, y + h * oy - orr * 0.6,
                   x + w * ox + orr, y + h * oy + orr * 0.6],
                  fill=(70, 64, 70, 170))
    # sea drones closing in from the left, with wakes
    for (dx, dy, s) in [(0.08, 0.74, 1.0), (0.20, 0.82, 0.8), (0.30, 0.70, 0.9)]:
        bx, by = x + w * dx, y + h * dy
        d.line([bx - 34 * s, by + 6, bx, by], fill=(200, 220, 240), width=2)
        d.polygon([(bx, by - 4), (bx + 18 * s, by), (bx, by + 4)],
                  fill=(16, 16, 20))
        d.ellipse([bx + 14 * s - 2, by - 2, bx + 14 * s + 2, by + 2],
                  fill=(255, 90, 60))


LEAD_SCENES = {"cop31": scene_cop31, "nato": scene_nato,
               "libya": scene_libya}


# ------------------------------------------------------- card mini-scenes
def mini_tanker(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(24, 34, 62))
    d.rectangle([x, y + h * 0.66, x + w, y + h], fill=SEA)
    hx = x + w * 0.12
    d.polygon([(hx, y + h * 0.60), (hx + w * 0.66, y + h * 0.60),
               (hx + w * 0.56, y + h * 0.78), (hx + w * 0.06, y + h * 0.78)],
              fill=(30, 30, 34))
    d.rectangle([hx + w * 0.08, y + h * 0.42, hx + w * 0.30, y + h * 0.60],
                fill=(150, 60, 50))
    d.rectangle([hx + w * 0.34, y + h * 0.48, hx + w * 0.52, y + h * 0.60],
                fill=(60, 90, 140))
    for fx in (0.50, 0.60):
        gx = hx + w * fx
        d.polygon([(gx - 6, y + h * 0.44), (gx, y + h * 0.20),
                   (gx + 6, y + h * 0.44)], fill=(240, 110, 36))
        d.polygon([(gx - 3, y + h * 0.44), (gx, y + h * 0.30),
                   (gx + 3, y + h * 0.44)], fill=(255, 190, 80))
    d.ellipse([x + w * 0.82, y + h * 0.12, x + w * 0.82 + 12,
               y + h * 0.12 + 12], fill=(255, 214, 90))


def mini_gaza(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(196, 178, 140))
    # rubble skyline: broken blocks, tilted slabs
    d.rectangle([x, y + h * 0.78, x + w, y + h], fill=(140, 124, 96))
    for (bx, bw, bh, tilt) in [(0.04, 0.20, 0.44, 0), (0.28, 0.16, 0.60, 1),
                               (0.48, 0.22, 0.36, 0), (0.72, 0.20, 0.52, 1)]:
        if tilt:
            d.polygon([(x + w * bx, y + h * 0.78),
                       (x + w * (bx + bw), y + h * 0.78 - h * 0.10),
                       (x + w * (bx + bw), y + h * 0.78),
                       (x + w * bx, y + h * 0.78)], fill=(110, 96, 74))
        d.rectangle([x + w * bx, y + h * (0.78 - bh), x + w * (bx + bw),
                     y + h * 0.78], fill=(126, 112, 88))
        for r in range(2):
            for cidx in range(2):
                d.rectangle([x + w * (bx + 0.03 + 0.07 * cidx),
                             y + h * (0.78 - bh + 0.08 + 0.14 * r),
                             x + w * (bx + 0.07 + 0.07 * cidx),
                             y + h * (0.78 - bh + 0.14 + 0.14 * r)],
                            fill=(60, 54, 46))
    # hazard triangle with exclamation, centre-right
    tx, ty, ts = x + w * 0.66, y + h * 0.12, 26
    d.polygon([(tx, ty), (tx + ts, ty + ts * 0.9), (tx - ts, ty + ts * 0.9)],
              fill=(255, 196, 0), outline=(20, 20, 20))
    d.rectangle([tx - 2, ty + 8, tx + 2, ty + 18], fill=(20, 20, 20))
    d.ellipse([tx - 2, ty + 20, tx + 2, ty + 24], fill=(20, 20, 20))


def mini_cikande(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(70, 62, 66))
    # factory block + chimney
    d.rectangle([x + w * 0.08, y + h * 0.42, x + w * 0.62, y + h * 0.86],
                fill=(52, 50, 56))
    d.polygon([(x + w * 0.08, y + h * 0.42), (x + w * 0.22, y + h * 0.30),
               (x + w * 0.36, y + h * 0.42), (x + w * 0.50, y + h * 0.30),
               (x + w * 0.62, y + h * 0.42)], fill=(40, 38, 44))
    d.rectangle([x + w * 0.70, y + h * 0.18, x + w * 0.78, y + h * 0.86],
                fill=(46, 44, 50))
    for r in range(2):
        for cidx in range(4):
            d.rectangle([x + w * (0.13 + 0.11 * cidx), y + h * (0.52 + 0.16 * r),
                         x + w * (0.19 + 0.11 * cidx),
                         y + h * (0.62 + 0.16 * r)], fill=(250, 196, 92))
    # flames along the roofline
    for fx in (0.16, 0.30, 0.44, 0.56):
        gx = x + w * fx
        d.polygon([(gx - 7, y + h * 0.34), (gx, y + h * 0.12),
                   (gx + 7, y + h * 0.34)], fill=(240, 110, 36))
        d.polygon([(gx - 3.5, y + h * 0.34), (gx, y + h * 0.22),
                   (gx + 3.5, y + h * 0.34)], fill=(255, 190, 80))
    # smoke
    for (sx, sy, sr) in [(0.70, 0.10, 9), (0.80, 0.06, 12)]:
        d.ellipse([x + w * sx - sr, y + h * sy - sr * 0.55,
                   x + w * sx + sr, y + h * sy + sr * 0.55],
                  fill=(96, 90, 96, 170))
    d.rectangle([x, y + h * 0.86, x + w, y + h], fill=(30, 28, 32))


def mini_grok(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(36, 40, 58))
    # smartphone with a photo silhouette, left
    px, py, pw, ph = x + w * 0.10, y + h * 0.14, w * 0.34, h * 0.72
    # int() the box: rounded_rectangle computes y0+width-1 in floats,
    # and 7.000000000000001+1-1 rounds DOWN to 7.0 < y0 -> ValueError
    d.rounded_rectangle([int(px), int(py), int(px + pw), int(py + ph)],
                        radius=6, fill=(16, 16, 20),
                        outline=(120, 124, 140))
    d.rectangle([px + 4, py + 8, px + pw - 4, py + ph - 8], fill=(168, 205, 226))
    d.ellipse([px + pw * 0.32, py + ph * 0.16, px + pw * 0.68,
               py + ph * 0.16 + pw * 0.36], fill=(240, 200, 170))
    d.pieslice([px + pw * 0.14, py + ph * 0.44, px + pw * 0.86,
                py + ph * 0.98], 180, 360, fill=(90, 60, 120))
    # red prohibition ring over the phone — small, inside the banner
    cx, cy, r = px + pw * 0.5, py + ph * 0.5, 16
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=RED, width=4)
    d.line([cx - r * 0.7, cy + r * 0.7, cx + r * 0.7, cy - r * 0.7],
           fill=RED, width=4)
    # gavel, right
    gx, gy = x + w * 0.62, y + h * 0.30
    d.rectangle([gx, gy, gx + w * 0.28, gy + 10], fill=(120, 84, 40))
    d.rectangle([gx + w * 0.06, gy - 6, gx + w * 0.22, gy - 2],
                fill=(150, 108, 54))
    d.line([gx + w * 0.14, gy + 10, gx + w * 0.10, gy + h * 0.34],
           fill=(120, 84, 40), width=4)
    d.rectangle([x + w * 0.58, y + h * 0.68, x + w * 0.92, y + h * 0.74],
                fill=(150, 108, 54))


def mini_satellite(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(8, 8, 18))
    for i in range(28):
        d.point((x + (i * 53) % int(w), y + (i * 29) % int(h)),
                fill=(225, 228, 240))
    # Earth arc along the bottom
    d.ellipse([x - w * 0.3, y + h * 0.78, x + w * 1.3, y + h * 1.7],
              fill=(44, 96, 160))
    d.ellipse([x + w * 0.18, y + h * 0.86, x + w * 0.44, y + h * 1.1],
              fill=(44, 128, 74))
    d.ellipse([x + w * 0.62, y + h * 0.90, x + w * 0.80, y + h * 1.06],
              fill=(44, 128, 74))
    # satellite body + panels, upper right
    sx, sy = x + w * 0.56, y + h * 0.22
    d.rectangle([sx, sy, sx + 34, sy + 20], fill=(210, 214, 220))
    d.polygon([(sx - 30, sy + 2), (sx, sy + 2), (sx, sy + 18),
               (sx - 30, sy + 18)], fill=(44, 68, 140))
    d.polygon([(sx + 34, sy + 2), (sx + 64, sy + 2), (sx + 64, sy + 18),
               (sx + 34, sy + 18)], fill=(44, 68, 140))
    for k in range(3):
        d.line([sx - 24 + k * 10, sy + 3, sx - 24 + k * 10, sy + 17],
               fill=(90, 120, 190), width=1)
        d.line([sx + 40 + k * 10, sy + 3, sx + 40 + k * 10, sy + 17],
               fill=(90, 120, 190), width=1)
    d.line([sx + 17, sy + 20, sx + 17, sy + 30], fill=(200, 200, 210),
           width=2)
    # radiation trefoil, left
    rx, ry, rr = x + w * 0.24, y + h * 0.34, 13
    d.ellipse([rx - rr, ry - rr, rx + rr, ry + rr], fill=(255, 206, 60))
    for a in (90, 210, 330):
        d.pieslice([rx - rr - 5, ry - rr - 5, rx + rr + 5, ry + rr + 5],
                   a - 28, a + 28, fill=(255, 206, 60))
    d.ellipse([rx - 3, ry - 3, rx + 3, ry + 3], fill=(8, 8, 18))


def mini_denmark(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(0, 32, 91))
    # circle of EU stars
    cx, cy, r = x + w * 0.30, y + h * 0.48, h * 0.30
    for k in range(12):
        a = math.radians(k * 30 - 90)
        sx, sy = cx + r * math.cos(a), cy + r * math.sin(a)
        d.ellipse([sx - 2.5, sy - 2.5, sx + 2.5, sy + 2.5],
                  fill=(255, 204, 0))
    # passport, right, with red DENIED stamp
    px, py, pw, ph = x + w * 0.58, y + h * 0.16, w * 0.34, h * 0.68
    d.rectangle([px, py, px + pw, py + ph], fill=(120, 20, 28),
                outline=(230, 200, 160))
    d.ellipse([px + pw * 0.30, py + ph * 0.14, px + pw * 0.70,
               py + ph * 0.14 + pw * 0.40], fill=(240, 200, 170))
    d.line([px + 6, py + ph * 0.52, px + pw - 6, py + ph * 0.52],
           fill=(230, 200, 160), width=2)
    d.line([px + 6, py + ph * 0.62, px + pw - 6, py + ph * 0.62],
           fill=(230, 200, 160), width=1)
    d.line([px + 4, py + ph * 0.78, px + pw * 0.72, py + ph * 0.30],
           fill=(255, 60, 60), width=3)
    d.line([px + 4, py + ph * 0.30, px + pw * 0.72, py + ph * 0.78],
           fill=(255, 60, 60), width=3)


def mini_dymer(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(58, 66, 84))
    # damaged apartment block: broken top edge, dark windows
    bx, by, bw, bh = x + w * 0.14, y + h * 0.30, w * 0.46, h * 0.56
    d.polygon([(bx, by + 10), (bx + bw * 0.25, by), (bx + bw * 0.45, by + 8),
               (bx + bw * 0.70, by + 2), (bx + bw, by + 12),
               (bx + bw, by + bh), (bx, by + bh)], fill=(150, 146, 138))
    for r in range(3):
        for cidx in range(3):
            d.rectangle([bx + 6 + cidx * (bw / 3.4),
                         by + 14 + r * (bh / 3.4),
                         bx + 6 + cidx * (bw / 3.4) + 8,
                         by + 14 + r * (bh / 3.4) + 9],
                        fill=(30, 28, 34) if (r + cidx) % 2 else (90, 86, 80))
    # fallen slab + rubble at the base
    d.polygon([(bx - 6, by + bh), (bx + bw * 0.4, by + bh - 12),
               (bx + bw * 0.7, by + bh), (bx + bw * 0.2, by + bh + 6)],
              fill=(110, 106, 98))
    # crane arm + hook, right
    d.line([x + w * 0.78, y + h * 0.10, x + w * 0.78, y + h * 0.86],
           fill=(240, 200, 60), width=3)
    d.line([x + w * 0.78, y + h * 0.10, x + w * 0.96, y + h * 0.22],
           fill=(240, 200, 60), width=3)
    d.line([x + w * 0.94, y + h * 0.22, x + w * 0.94, y + h * 0.40],
           fill=(200, 200, 210), width=1)
    d.rectangle([x + w * 0.92, y + h * 0.40, x + w * 0.96, y + h * 0.46],
                fill=(200, 60, 60))
    # searchlight beam
    d.polygon([(x + w * 0.78, y + h * 0.30), (bx + bw * 0.8, by + bh * 0.5),
               (bx + bw * 0.8, by + bh * 0.5 + 8)],
              fill=(255, 240, 180, 90))


def mini_markets(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(246, 244, 238))
    # grid lines
    for gy in (0.25, 0.5, 0.75):
        d.line([x + 4, y + h * gy, x + w - 4, y + h * gy],
               fill=(220, 216, 200), width=1)
    # candlesticks: red down, then green up
    candles = [(0.08, 0.55, 0.70, 0.62, (178, 24, 32)),
               (0.22, 0.48, 0.62, 0.55, (178, 24, 32)),
               (0.36, 0.42, 0.55, 0.48, (44, 128, 74)),
               (0.50, 0.34, 0.46, 0.40, (44, 128, 74)),
               (0.64, 0.26, 0.38, 0.32, (44, 128, 74)),
               (0.78, 0.16, 0.28, 0.22, (44, 128, 74))]
    for (cx0, top, bot, _, col) in candles:
        cx = x + w * cx0
        d.line([cx + 5, y + h * (top - 0.05), cx + 5, y + h * (bot + 0.05)],
               fill=col, width=1)
        d.rectangle([cx, y + h * top, cx + 10, y + h * bot], fill=col)
    # rising arrow
    d.line([x + w * 0.10, y + h * 0.62, x + w * 0.88, y + h * 0.16],
           fill=(22, 38, 76), width=3)
    d.polygon([(x + w * 0.88, y + h * 0.16), (x + w * 0.78, y + h * 0.16),
               (x + w * 0.88, y + h * 0.26)], fill=(22, 38, 76))
    # gold coin
    d.ellipse([x + w * 0.78, y + h * 0.60, x + w * 0.78 + 20,
               y + h * 0.60 + 20], fill=(255, 206, 60),
              outline=(180, 140, 20))
    d.text((x + w * 0.78 + 7, y + h * 0.60 + 4), "$", font=F(SANS_BLACK, 11),
           fill=(120, 90, 10))


def mini_whitehouse(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(168, 205, 226))
    # lawn
    d.rectangle([x, y + h * 0.78, x + w, y + h], fill=(86, 148, 74))
    # White House: central block + dome + wings
    bx, by, bw, bh = x + w * 0.22, y + h * 0.34, w * 0.56, h * 0.44
    d.rectangle([bx, by, bx + bw, by + bh], fill=(250, 250, 246),
                outline=(180, 180, 170))
    d.pieslice([bx + bw * 0.32, by - h * 0.24, bx + bw * 0.68, by + 2],
               180, 360, fill=(250, 250, 246), outline=(180, 180, 170))
    for i in range(5):
        cx = bx + bw * (0.12 + 0.19 * i)
        d.rectangle([cx, by + 6, cx + 6, by + bh - 6], fill=(210, 210, 200))
    d.rectangle([bx + bw * 0.42, by + bh * 0.55, bx + bw * 0.58,
                 by + bh], fill=(60, 60, 66))
    # document with red seal, front
    dx, dy = x + w * 0.68, y + h * 0.58
    d.rectangle([dx, dy, dx + 26, dy + 20], fill=(252, 250, 240),
                outline=(150, 150, 150))
    d.ellipse([dx + 17, dy + 11, dx + 25, dy + 19], fill=RED)
    for k in range(2):
        d.line([dx + 4, dy + 5 + k * 4, dx + 15, dy + 5 + k * 4],
               fill=(150, 150, 150), width=1)


def mini_seoul(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(168, 205, 226))
    # N Seoul Tower on Namsan, centre
    tx = x + w * 0.50
    d.polygon([(tx - 16, y + h * 0.86), (tx - 6, y + h * 0.30),
               (tx + 6, y + h * 0.30), (tx + 16, y + h * 0.86)],
              fill=(120, 130, 140))
    d.ellipse([tx - 12, y + h * 0.22, tx + 12, y + h * 0.22 + 12],
              fill=(200, 60, 60))
    d.line([tx, y + h * 0.10, tx, y + h * 0.22], fill=(200, 60, 60), width=2)
    # skyline blocks
    bx = x + 4
    for bw, bh in [(18, 0.34), (14, 0.46), (20, 0.30), (14, 0.40), (16, 0.32)]:
        d.rectangle([bx, y + h - h * bh - 4, bx + bw, y + h - 4],
                    fill=(70, 92, 118))
        bx += bw + 5
    d.rectangle([x, y + h - 4, x + w, y + h], fill=(90, 100, 112))
    # taegeuk swirl, small, bottom right
    sx, sy, sr = x + w * 0.84, y + h * 0.72, 8
    d.pieslice([sx - sr, sy - sr, sx + sr, sy + sr], 90, 270,
               fill=(178, 24, 32))
    d.pieslice([sx - sr, sy - sr, sx + sr, sy + sr], 270, 90,
               fill=(22, 38, 76))


CARD_SCENES = {"tanker": mini_tanker, "gaza": mini_gaza,
               "cikande": mini_cikande, "grok": mini_grok,
               "satellite": mini_satellite, "denmark": mini_denmark,
               "dymer": mini_dymer, "markets": mini_markets,
               "whitehouse": mini_whitehouse, "seoul": mini_seoul}


# ------------------------------------------------------------------ world map
# Coastline-free dotted continents: 12-px grid, land-test by polygon.
# Polygons drawn in lon/lat. Map height 150 px (was ~60 px on ni21),
# dots cream on navy so every pin and the dot pattern read at full size.
def point_in_poly(lon, lat, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > lat) != (yj > lat)) and \
           (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def lon_lat_to_xy(lon, lat, mx, my, mw, mh):
    px = mx + (lon + 180.0) / 360.0 * mw
    py = my + (90.0 - lat) / 180.0 * mh
    return px, py


def lon_lat_rect(lon0, lon1, lat0, lat1, mx, my, mw, mh):
    x0, y1 = lon_lat_to_xy(lon0, lat0, mx, my, mw, mh)
    x1, y0 = lon_lat_to_xy(lon1, lat1, mx, my, mw, mh)
    return x0, y0, x1, y1


# (lon, lat) — verified against a real world map for ni22.
CONTINENTS = [
    ([(-168, 66), (-156, 71), (-140, 70), (-130, 71), (-125, 62), (-125, 48),
      (-124, 40), (-118, 34), (-110, 23), (-97, 16), (-87, 13), (-83, 9),
      (-79, 9), (-81, 15), (-85, 16), (-90, 18), (-95, 19), (-97, 26),
      (-90, 30), (-82, 31), (-76, 35), (-75, 40), (-70, 43), (-66, 45),
      (-60, 47), (-55, 52), (-65, 60), (-68, 58), (-72, 62), (-78, 62),
      (-90, 66), (-95, 69), (-110, 68), (-125, 70), (-140, 70),
      (-155, 71), (-168, 66)], "NORTH AMERICA"),
    ([(-80, 10), (-79, 4), (-77, -4), (-81, -6), (-77, -12), (-71, -18),
      (-70, -23), (-70, -30), (-71, -35), (-73, -44), (-74, -50),
      (-70, -54), (-66, -55), (-66, -47), (-62, -41), (-58, -34),
      (-52, -32), (-48, -27), (-40, -22), (-35, -9), (-35, -6),
      (-41, -3), (-44, -2), (-50, 0), (-52, 4), (-57, 6), (-61, 9),
      (-65, 10), (-71, 12), (-75, 10), (-80, 10)], "SOUTH AMERICA"),
    ([(-10, 37), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (0, 50),
      (2, 51), (5, 53), (7, 54), (8, 57), (10, 59), (5, 60), (5, 62),
      (10, 64), (12, 66), (18, 69), (25, 71), (31, 70), (40, 68),
      (44, 66), (42, 60), (40, 56), (38, 54), (40, 50), (35, 46),
      (31, 46), (30, 46), (28, 45), (23, 40), (19, 42), (13, 44),
      (8, 44), (3, 42), (0, 39), (-2, 37), (-6, 36), (-10, 37)],
     "EUROPE"),
    ([(-6, 35), (0, 36), (10, 37), (11, 34), (19, 30), (20, 32),
      (25, 32), (30, 31), (32, 31), (35, 28), (39, 21), (43, 12),
      (48, 11), (51, 11), (56, 16), (58, 21), (55, 25), (52, 28),
      (48, 30), (44, 30), (38, 20), (35, 15), (33, 12), (32, 10),
      (30, 12), (26, 17), (21, 16), (15, 15), (12, 14), (9, 9),
      (9, 4), (6, 4), (3, 6), (-8, 4), (-13, 8), (-17, 12), (-17, 15),
      (-15, 20), (-15, 25), (-13, 28), (-10, 30), (-6, 35)],
     "AFRICA"),
    ([(26, 38), (30, 36), (36, 36), (36, 30), (39, 27), (41, 29),
      (44, 29), (47, 30), (50, 29), (54, 26), (57, 26), (58, 24),
      (61, 25), (66, 25), (70, 22), (73, 20), (76, 10), (80, 8),
      (81, 9), (84, 19), (88, 22), (91, 22), (93, 17), (95, 16),
      (98, 8), (100, 6), (101, 3), (104, 2), (105, 9), (107, 11),
      (109, 15), (106, 21), (110, 20), (113, 22), (116, 23),
      (120, 25), (122, 31), (120, 35), (122, 38), (127, 40),
      (130, 42), (133, 43), (136, 44), (140, 47), (142, 50),
      (142, 54), (140, 59), (142, 60), (158, 59), (162, 60),
      (170, 66), (178, 65), (180, 66), (180, 62), (170, 60),
      (162, 60), (158, 53), (150, 59), (142, 54), (142, 48),
      (138, 44), (132, 43), (128, 40), (124, 39), (121, 36),
      (116, 36), (113, 30), (110, 24), (108, 18), (104, 8),
      (100, 13), (96, 16), (92, 21), (89, 22), (86, 20), (82, 16),
      (77, 8), (73, 16), (68, 23), (62, 25), (57, 25), (53, 26),
      (48, 30), (44, 29), (41, 29), (36, 36), (33, 39), (26, 41),
      (26, 38)], "ASIA"),
    ([(114, -22), (114, -32), (115, -35), (118, -35), (124, -33),
      (130, -32), (133, -32), (137, -35), (140, -38), (145, -38),
      (150, -37), (153, -32), (153, -27), (150, -22), (146, -19),
      (142, -15), (142, -11), (136, -12), (132, -11), (127, -14),
      (122, -17), (118, -20), (114, -22)], "AUSTRALIA"),
]

# Pin positions (lon, lat) — all on land, verified against a real map.
PINS = [
    (1, 30.7, 36.9, RED),     # Antalya
    (2, 4.35, 50.85, RED),    # Brussels
    (3, 20.07, 32.12, RED),   # Benghazi
    (4, 56.5, 26.6, RED),     # Strait of Hormuz
    (5, 34.45, 31.5, RED),    # Gaza
    (6, 106.4, -6.2, RED),    # Cikande
    (7, -122.7, 45.5, RED),   # Oregon
    (8, 37.6, 55.75, RED),    # Moscow
    (9, 12.57, 55.68, RED),   # Copenhagen
    (10, 30.2, 50.8, RED),    # Dymer
    (11, -74.0, 40.7, RED),   # New York
    (12, -77.04, 38.9, RED),  # Washington DC
    (13, 126.98, 37.57, RED), # Seoul
]


# Map projection (equirectangular, cropped to the inhabited latitudes so
# continents read at 150 px tall): lon -168..192, lat 78..-57.
MAP_LON = (-168.0, 192.0)
MAP_LAT = (78.0, -57.0)


# Pins drawn with a pixel offset + leader line (their true spot is
# crowded by a neighbour's disc): 1 Antalya (crowded by 5 Gaza),
# 11 New York (crowded by 12 Washington DC).
PIN_OFFSETS = {1: (20, 6), 11: (14, -12)}


def draw_map(mx, my, mw, mh):
    d.rectangle([mx, my, mx + mw, my + mh], fill=NAVY_DARK)
    cols, rows = 118, 36
    cw_, ch_ = mw / cols, mh / rows
    for r in range(rows):
        lat = MAP_LAT[0] + (r + 0.5) * (MAP_LAT[1] - MAP_LAT[0]) / rows
        for c in range(cols):
            lon = MAP_LON[0] + (c + 0.5) * (MAP_LON[1] - MAP_LON[0]) / cols
            if any(point_in_poly(lon, lat, poly) for poly, _ in
                   CONTINENTS):
                cx = mx + (c + 0.5) * cw_
                cy = my + (r + 0.5) * ch_
                d.ellipse([cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5],
                          fill=(238, 232, 205))
    # equator / tropics graticule
    for lat in (0, 23.5, -23.5):
        gy = my + (MAP_LAT[0] - lat) / (MAP_LAT[0] - MAP_LAT[1]) * mh
        d.line([mx, gy, mx + mw, gy], fill=(110, 120, 160), width=1)
    # pins: number in a red disc, white ring (radius 7 — the European and
    # US east-coast clusters are tight; two pins use a leader line)
    for num, lon, lat, col in PINS:
        px = mx + (lon - MAP_LON[0]) / (MAP_LON[1] - MAP_LON[0]) * mw
        py = my + (MAP_LAT[0] - lat) / (MAP_LAT[0] - MAP_LAT[1]) * mh
        ox, oy = PIN_OFFSETS.get(num, (0, 0))
        if (ox, oy) != (0, 0):
            d.line([px, py, px + ox, py + oy], fill=(255, 255, 255),
                   width=1)
            px, py = px + ox, py + oy
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=col,
                  outline=(255, 255, 255), width=2)
        ns = str(num)
        f = F(SANS_BLACK, 8)
        d.text((px - tw(ns, f) / 2, py - 5), ns, font=f, fill=(255, 255, 255))
    # caption INSIDE the map, on a solid strip (Patagonia's dots reach
    # the bottom edge and would cross the text otherwise)
    d.rectangle([mx, my + mh - 16, mx + mw, my + mh], fill=NAVY_DARK)
    d.text((mx + 6, my + mh - 12),
           "WHERE THE NEWS IS  ·  13 PICTURED STORIES PINNED",
           font=F(SANS, 8), fill=(200, 204, 220))



# ------------------------------------------------------------------ page
# Vertical budget (proven on ni22): masthead 0–24 · headline 30–88 ·
# strap rules 100/138 · stats 146–192 · region bar 196–216 · UTC 224–238
# · leads 254–540 · cards 540/662 · bottom 794–960 · DATE CHECK 966–1008
# · footer 1012.
def header():
    d.rectangle([0, 0, W, 24], fill=NAVY_DARK)
    centre("THE WORLD IN ONE DAY · 36 STORIES · 6 REGIONS · EVERY ONE "
           "DATED MONDAY 23 NOVEMBER 2026", W / 2, 5, F(SANS_BOLD, 11),
           fill=(248, 243, 228))
    centre("Monday 23 November 2026", W / 2, 30,
           fit("Monday 23 November 2026", SERIF_BLACK, 58, CW))
    # strap: rules at 100 and 138, text between with clear padding
    rule(M, M + CW, 100, fill=INK, width=2)
    centre(STRAP, W / 2, 109, fit(STRAP, SERIF_IT, 16, CW), fill=RED)
    rule(M, M + CW, 138, fill=INK, width=1)


def stat_strip():
    y = 146
    colw = CW / 6
    for i, (num, lab) in enumerate(STATS):
        cx = M + colw * i + colw / 2
        centre(num, cx, y, fit(num, SANS_BLACK, 27, colw - 8), fill=RED)
        lf = F(SANS_BOLD, 8)
        lines = wrap(lab, lf, colw - 10)
        for j, ln in enumerate(lines[:2]):
            centre(ln, cx, y + 34 + j * 10, lf, fill=GREY)
        if i:
            d.line([M + colw * i, y + 2, M + colw * i, y + 46],
                   fill=CREAM_LINE, width=1)


def region_bar():
    y = 196
    total = sum(c for _, c, _ in REGIONS)
    assert total == 36, f"region tally {total} != 36"
    x = M
    f = F(SANS_BOLD, 10)
    spans = {}
    for name, count, colour in REGIONS:
        w_ = CW * count / total
        d.rectangle([x, y, x + w_, y + 20], fill=colour)
        spans[name] = (x, x + w_)
        if name in ("AMERICAS", "EUROPE", "ASIA-PACIFIC"):
            centre(f"{name} {count}", x + w_ / 2, y + 5, f,
                   fill=(255, 255, 255))
        x += w_
    # MIDDLE EAST 3, AFRICA 3 and WORLD 2 segments are too narrow for
    # separate labels — one joint label centred across all three.
    jx = (spans["MIDDLE EAST"][0] + spans["WORLD"][1]) / 2
    centre("MIDEAST 3 · AFRICA 3 · WORLD 2", jx, y + 5, f,
           fill=(255, 255, 255))


def utc_strip():
    y = 224
    lw, _ = chip(M, y, "THE DAY IN UTC", NAVY_DARK, font_size=10)
    x = M + lw + 10
    f_t, f_s = F(SANS_BLACK, 11), F(SANS, 10)
    for t, s in UTC_STRIP:
        d.text((x, y + 2), t, font=f_t, fill=RED)
        x += tw(t, f_t) + 4
        d.text((x, y + 3), s, font=f_s, fill=INK)
        x += tw(s, f_s) + 14
    if x - 14 > M + CW:
        WARNINGS.append(f"UTC strip overflows: ends at {x - 14}")


def draw_scene_clipped(scene_fn, x, y, w, h):
    """Render a scene on its own layer and paste it — nothing the scene
    draws (Earth arcs, smoke, rings) may spill past its banner box."""
    global d
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    old_d = d
    d = ImageDraw.Draw(layer, "RGBA")
    try:
        scene_fn(0, 0, w, h)
    finally:
        d = old_d
    img.paste(layer, (x, y), layer)


def lead_panel(i, x, y, lead):
    w = 317
    draw_scene_clipped(LEAD_SCENES[lead["scene"]], x, y, w, 150)
    d.rectangle([x, y, x + w, y + 150], outline=INK, width=1)
    chip(x + 8, y + 8, lead["tag"], RED, font_size=10)
    sf = F(SANS_BOLD, 10)
    sw = tw(lead["stat"], sf) + 10
    d.rectangle([x + w - sw - 8, y + 8, x + w - 8, y + 8 + 15],
                fill=(255, 255, 255))
    d.text((x + w - sw - 3, y + 10), lead["stat"], font=sf, fill=INK)
    ty = y + 158
    # number badge + kicker + label
    d.rectangle([x, ty, x + 19, ty + 15], fill=INK)
    nf = F(SANS_BOLD, 10)
    d.text((x + 9 - tw(str(i + 1), nf) / 2, ty + 2), str(i + 1), font=nf,
           fill=(255, 255, 255))
    kf = F(SANS_BOLD, 10)
    d.text((x + 25, ty + 2), lead["kicker"] + "  ·", font=kf, fill=NAVY)
    lx = x + 25 + tw(lead["kicker"] + "  ·", kf) + 4
    lc = RED if lead["label"] == "CLAIM" else (44, 128, 74)
    d.ellipse([lx, ty + 5, lx + 7, ty + 12], fill=lc)
    d.text((lx + 10, ty + 2), lead["label"], font=kf, fill=lc)
    hy = ty + 19
    # fixed 21 pt, wraps to two lines (fit() would shrink a 50-char
    # headline to one line — never use it on a wrapped headline)
    hy = text_block(x, hy, lead["headline"], F(SERIF_BOLD, 21), w, 24,
                    max_lines=2)
    by = text_block(x, hy + 2, lead["body"], F(SANS, 10), w, 13.5,
                    fill=(40, 40, 44), max_lines=3)
    d.text((x, by + 3), lead["source"], font=F(SANS_BOLD, 8), fill=GREY)
    return by + 14


def card(i, x, y, cnum, tag, stat, place, label, head, body, source, scene):
    w = 188
    draw_scene_clipped(CARD_SCENES[scene], x, y, w, 50)
    d.rectangle([x, y, x + w, y + 50], outline=INK, width=1)
    chip(x + 5, y + 5, tag, RED, font_size=8)
    sf = F(SANS_BOLD, 8)
    sw = tw(stat, sf) + 8
    d.rectangle([x + w - sw - 5, y + 5, x + w - 5, y + 5 + 13],
                fill=(255, 255, 255))
    d.text((x + w - sw - 1, y + 7), stat, font=sf, fill=INK)
    # source credit as a caption strip along the banner's bottom edge
    d.rectangle([x, y + 39, x + w, y + 50], fill=(12, 12, 16))
    d.text((x + 5, y + 41), source, font=F(SANS_BOLD, 7),
           fill=(235, 232, 220))
    ky = y + 54
    d.rectangle([x, ky, x + 15, ky + 12], fill=INK)
    nf = F(SANS_BOLD, 8)
    d.text((x + 7 - tw(str(cnum), nf) / 2, ky + 2), str(cnum), font=nf,
           fill=(255, 255, 255))
    kf = F(SANS_BOLD, 8)
    d.text((x + 19, ky + 2), place + " ·", font=kf, fill=NAVY)
    lx = x + 19 + tw(place + " ·", kf) + 3
    lc = RED if label == "CLAIM" else (44, 128, 74)
    d.ellipse([lx, ky + 3, lx + 6, ky + 9], fill=lc)
    d.text((lx + 8, ky + 2), label, font=kf, fill=lc)
    hy = text_block(x, ky + 14, head, F(SERIF_BOLD, 13), w, 14.5,
                    max_lines=2)
    text_block(x, hy + 1, body, F(SANS, 9), w, 11, fill=(40, 40, 44),
               max_lines=2)


def bottom():
    y = 794
    d.text((M, y), "WHERE IT HAPPENED", font=F(SANS_BLACK, 11), fill=NAVY)
    mw = tw("WHERE IT HAPPENED", F(SANS_BLACK, 11))
    d.text((M + mw + 8, y + 2), "pins match story numbers",
           font=F(SANS, 9), fill=GREY)
    draw_map(M, y + 16, 474, 150)
    # also-on list (black text on the paper, roomy leading)
    ax = M + 486
    d.text((ax, y), "ALSO ON MONDAY 23 NOVEMBER", font=F(SANS_BLACK, 11),
           fill=RED)
    aw = tw("ALSO ON MONDAY 23 NOVEMBER", F(SANS_BLACK, 11))
    d.text((ax + aw + 8, y + 2), "— 23 more stories", font=F(SANS, 9),
           fill=GREY)
    nf, tf, gf = F(SANS_BOLD, 9), F(SANS, 9), F(SANS, 8)
    col_w = (W - M - ax - 12) / 2
    for j, (num, text, source, label) in enumerate(BRIEFS):
        col = 0 if j < 12 else 1
        row = j if j < 12 else j - 12
        bx = ax + col * (col_w + 12)
        by = y + 18 + row * 12.5
        d.text((bx, by), f"{num}", font=nf, fill=RED)
        tx = bx + tw(f"{num}", nf) + 5
        suffix = f" ({source}" + (f" · {label})" if label else ")")
        full = text + suffix
        if tw(full, tf) > col_w - (tx - bx):
            WARNINGS.append(f"brief {num} too wide: {tw(full, tf):.0f}px "
                            f"> {col_w - (tx - bx):.0f}px")
        d.text((tx, by), text, font=tf, fill=INK)
        d.text((tx + tw(text, tf), by), suffix, font=gf, fill=GREY)


def date_check():
    y = 966
    d.rectangle([M, y, M + CW, 1008], outline=RED, width=2)
    d.text((M + 10, y + 6), "DATE CHECK — CHECKED, AND LEFT OUT ON PURPOSE",
           font=F(SANS_BLACK, 11), fill=RED)
    text_block(M + 10, y + 21, DATE_CHECK, F(SANS, 9), CW - 20, 10.5,
               fill=(40, 40, 44), max_lines=2)


def main():
    header()
    stat_strip()
    region_bar()
    utc_strip()
    ends = []
    for i, lead in enumerate(LEADS):
        ends.append(lead_panel(i, M + i * 327, 254, lead))
    for j, c in enumerate(CARDS):
        row, col = divmod(j, 5)
        card(j, M + col * 196, 540 + row * 122, *c)
    bottom()
    date_check()
    # footer: one short line squeezed under the date-check box
    centre(FOOTER, W / 2, 1012, fit(FOOTER, SANS, 8, CW), fill=GREY)
    if max(ends) > 540:
        WARNINGS.append(f"lead text ends at {max(ends)} > 540")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "output")
    os.makedirs(out, exist_ok=True)
    img.save(os.path.join(out, "entry.png"))
    img.resize((300, 300), Image.LANCZOS).save(
        os.path.join(out, "preview-300.png"))
    for wn in WARNINGS:
        print("WARNING:", wn)
    print("wrote output/entry.png + output/preview-300.png")


if __name__ == "__main__":
    main()
