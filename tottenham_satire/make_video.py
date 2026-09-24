#!/usr/bin/env python3
"""SPURS QUEST ~강등권의 전설~

2026년 9월 토트넘 홋스퍼의 현실(2025-26 시즌 17위 간신히 잔류, 감독 3명,
2026-27 시즌 4경기 1점으로 강등권)을 8비트 고전 게임 스타일로 풍자하는
패러디 영상을 생성한다. 그래픽·음악·효과음 모두 코드로 직접 만든다.

    pip install pillow numpy imageio-ffmpeg
    python3 make_video.py            # -> spurs_quest.mp4
"""
import math
import os
import random
import subprocess
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, SCALE = 320, 180, 4
FPS = 30
SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "spurs_quest.mp4")

FONT_PATH = "/usr/share/fonts/opentype/unifont/unifont.otf"
F16 = ImageFont.truetype(FONT_PATH, 16)
F32 = ImageFont.truetype(FONT_PATH, 32)
F64 = ImageFont.truetype(FONT_PATH, 64)

BLACK = (0, 0, 0)
WHITE = (252, 252, 252)
NAVY = (19, 34, 87)
NAVY2 = (48, 72, 160)
GOLD = (248, 184, 0)
RED = (228, 40, 40)
DRED = (120, 0, 0)
GRAY = (124, 124, 124)
LGRAY = (188, 188, 188)
SKY = (92, 148, 252)
GREEN = (0, 168, 0)
DGREEN = (0, 96, 0)
BROWN = (200, 76, 12)
ORANGE = (252, 152, 56)
YELLOW = (252, 224, 60)
SKIN = (252, 196, 140)
SKIN_D = (220, 160, 110)
CLARET = (124, 20, 52)
CREAM = (248, 248, 232)


# ---------------------------------------------------------------- drawing utils

def tw(s, font=F16):
    return int(font.getlength(s))


def text(d, x, y, s, fill=WHITE, font=F16, shadow=BLACK):
    if shadow is not None:
        off = 2 if font is not F16 else 1
        d.text((x + off, y + off), s, font=font, fill=shadow)
    d.text((x, y), s, font=font, fill=fill)


def ctext(d, y, s, fill=WHITE, font=F16, shadow=BLACK, cx=W // 2):
    text(d, cx - tw(s, font) // 2, y, s, fill, font, shadow)


def box(d, x0, y0, x1, y1, fill=BLACK, border=WHITE):
    d.rectangle([x0, y0, x1, y1], fill=fill)
    d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], outline=border, width=2)


def reveal(s, since, cps=28):
    if since < 0:
        return ""
    return s[: int(since * cps)]


def blink(t, hz=2.0):
    return int(t * hz * 2) % 2 == 0


def make_sprite(rows, pal, outline=BLACK):
    h = len(rows)
    w = max(len(r) for r in rows)
    im = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    px = im.load()
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != ".":
                px[x + 1, y + 1] = pal[c] + (255,)
    if outline:
        src = im.copy()
        sp = src.load()
        for y in range(h + 2):
            for x in range(w + 2):
                if sp[x, y][3]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w + 2 and 0 <= ny < h + 2 and sp[nx, ny][3]:
                        px[x, y] = outline + (255,)
                        break
    return im


_scaled = {}


def blit(img, spr, x, y, scale=1, flip_v=False):
    key = (id(spr), scale, flip_v)
    if key not in _scaled:
        s = spr
        if flip_v:
            s = s.transpose(Image.FLIP_TOP_BOTTOM)
        if scale != 1:
            s = s.resize((s.width * scale, s.height * scale), Image.NEAREST)
        _scaled[key] = s
    s = _scaled[key]
    img.paste(s, (int(x), int(y)), s)


# ---------------------------------------------------------------------- sprites

COCK_PAL = {"R": RED, "W": WHITE, "K": BLACK, "Y": GOLD, "N": NAVY2, "O": (230, 150, 0)}
COCK_TOP = [
    "..........RR....",
    ".........RRRR...",
    "........WWWW....",
    ".......WWWKWY...",
    "N......WWWWWYY..",
    "NN.....WWWWR....",
    "NNN....WWWWR....",
    ".NNN..WWWWW.....",
    "..NNWWWWWWW.....",
    "..NWWWWWWWW.....",
    "...WWWWWWWW.....",
    "...WWWWWWWW.....",
    "....WWWWWW......",
    ".....WWWW.......",
]
LEGS_A = ["......O..O......", "......O..O......", ".....OO.OO......"]
LEGS_B = [".....O....O.....", "....O......O....", "...OO.....OO...."]
COCK_A = make_sprite(COCK_TOP + LEGS_A, COCK_PAL)
COCK_B = make_sprite(COCK_TOP + LEGS_B, COCK_PAL)
COCK_DEAD = make_sprite(
    [r.replace("K", "X") for r in COCK_TOP] + LEGS_A, dict(COCK_PAL, X=RED)
)


def draw_hammer(d, x, y, t):
    """West Ham 망치 캐릭터."""
    x, y = int(x), int(y)
    d.rectangle([x + 5, y + 8, x + 9, y + 18], fill=CLARET, outline=BLACK)
    d.rectangle([x, y, x + 14, y + 8], fill=(160, 160, 176), outline=BLACK)
    d.rectangle([x + 3, y + 3, x + 4, y + 4], fill=BLACK)
    d.rectangle([x + 9, y + 3, x + 10, y + 4], fill=BLACK)
    step = int(t * 12) % 2
    lx = (x + 4, x + 10) if step else (x + 6, x + 8)
    for lxx in lx:
        d.line([(lxx, y + 19), (lxx, y + 22)], fill=(27, 177, 231), width=2)


def draw_monster(d, kind, cx, cy, t, flash=False):
    cx, cy = int(cx), int(cy)
    ol = BLACK
    if kind == "bee":  # Brentford
        flap = -2 if int(t * 14) % 2 else 1
        wing = (208, 240, 255) if not flash else WHITE
        d.ellipse([cx - 16, cy - 30 + flap, cx - 2, cy - 10], fill=wing, outline=ol)
        d.ellipse([cx + 2, cy - 32 - flap, cx + 18, cy - 10], fill=wing, outline=ol)
        d.polygon([(cx - 22, cy - 3), (cx - 34, cy + 2), (cx - 22, cy + 5)], fill=BLACK)
        body = YELLOW if not flash else WHITE
        d.ellipse([cx - 22, cy - 14, cx + 22, cy + 14], fill=body, outline=ol)
        d.rectangle([cx - 9, cy - 13, cx - 4, cy + 13], fill=BLACK)
        d.rectangle([cx + 3, cy - 12, cx + 8, cy + 12], fill=BLACK)
        d.ellipse([cx + 11, cy - 9, cx + 19, cy - 1], fill=WHITE, outline=ol)
        d.rectangle([cx + 15, cy - 6, cx + 17, cy - 3], fill=BLACK)
        d.line([(cx + 10, cy - 12), (cx + 19, cy - 9)], fill=BLACK, width=2)
        d.line([(cx + 12, cy + 6), (cx + 18, cy + 4)], fill=BLACK)
        d.rectangle([cx - 4, cy + 11, cx + 12, cy + 15], fill=RED)  # red scarf
    elif kind == "magpie":  # Newcastle
        d.polygon([(cx - 14, cy + 4), (cx - 40, cy + 20), (cx - 36, cy + 26), (cx - 10, cy + 12)],
                  fill=BLACK, outline=(60, 60, 90))
        body = BLACK if not flash else WHITE
        d.ellipse([cx - 20, cy - 14, cx + 14, cy + 16], fill=body, outline=(60, 60, 90))
        d.ellipse([cx - 6, cy - 2, cx + 12, cy + 14], fill=WHITE)
        d.ellipse([cx - 16, cy - 8, cx - 2, cy + 4], fill=WHITE)
        d.ellipse([cx + 2, cy - 30, cx + 24, cy - 8], fill=body, outline=(60, 60, 90))
        d.polygon([(cx + 22, cy - 22), (cx + 34, cy - 18), (cx + 22, cy - 15)], fill=GRAY, outline=ol)
        d.ellipse([cx + 12, cy - 25, cx + 19, cy - 18], fill=WHITE)
        d.rectangle([cx + 15, cy - 23, cx + 17, cy - 20], fill=BLACK)
        d.line([(cx - 2, cy + 16), (cx - 2, cy + 22)], fill=GRAY, width=2)
        d.line([(cx + 6, cy + 16), (cx + 6, cy + 22)], fill=GRAY, width=2)
    elif kind == "toffee":  # Everton
        blue = (40, 80, 200)
        d.polygon([(cx - 16, cy), (cx - 34, cy - 14), (cx - 34, cy + 14)], fill=blue, outline=ol)
        d.polygon([(cx + 16, cy), (cx + 34, cy - 14), (cx + 34, cy + 14)], fill=blue, outline=ol)
        d.line([(cx - 28, cy - 10), (cx - 28, cy + 10)], fill=WHITE)
        d.line([(cx + 28, cy - 10), (cx + 28, cy + 10)], fill=WHITE)
        body = (190, 110, 40) if not flash else WHITE
        d.ellipse([cx - 18, cy - 14, cx + 18, cy + 14], fill=body, outline=ol)
        d.line([(cx - 9, cy - 3), (cx - 3, cy - 3)], fill=BLACK, width=2)
        d.line([(cx + 3, cy - 3), (cx + 9, cy - 3)], fill=BLACK, width=2)
        d.line([(cx - 3, cy + 6), (cx + 3, cy + 6)], fill=BLACK)
        zy = cy - 22 - int((t * 10) % 12)
        d.text((cx + 16, zy), "z", font=F16, fill=blue)
        d.text((cx + 24, zy - 10), "Z", font=F16, fill=blue)
    elif kind == "lion":  # Aston Villa
        mane = CLARET if not flash else WHITE
        for a in range(0, 360, 30):
            rx = cx + int(26 * math.cos(math.radians(a)))
            ry = cy + int(26 * math.sin(math.radians(a)))
            d.ellipse([rx - 8, ry - 8, rx + 8, ry + 8], fill=mane, outline=ol)
        d.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=mane)
        face = GOLD if not flash else WHITE
        d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=face, outline=ol)
        d.ellipse([cx - 9, cy - 7, cx - 3, cy - 1], fill=WHITE, outline=ol)
        d.ellipse([cx + 3, cy - 7, cx + 9, cy - 1], fill=WHITE, outline=ol)
        d.rectangle([cx - 6, cy - 5, cx - 5, cy - 3], fill=BLACK)
        d.rectangle([cx + 5, cy - 5, cx + 6, cy - 3], fill=BLACK)
        d.line([(cx - 11, cy - 11), (cx - 3, cy - 8)], fill=BLACK, width=2)
        d.line([(cx + 3, cy - 8), (cx + 11, cy - 11)], fill=BLACK, width=2)
        d.polygon([(cx - 3, cy + 2), (cx + 3, cy + 2), (cx, cy + 5)], fill=BLACK)
        d.polygon([(cx - 7, cy + 8), (cx + 7, cy + 8), (cx, cy + 13)], fill=DRED)
        d.polygon([(cx - 5, cy + 8), (cx - 3, cy + 11), (cx - 1, cy + 8)], fill=WHITE)
        d.polygon([(cx + 1, cy + 8), (cx + 3, cy + 11), (cx + 5, cy + 8)], fill=WHITE)
        d.rectangle([cx - 20, cy + 20, cx + 20, cy + 24], fill=(149, 191, 229))


def draw_manager(d, x, y, kind):
    """시즌 중 거쳐간 감독들(캐리커처가 아닌 범용 도트 아바타)."""
    d.rectangle([x, y, x + 55, y + 63], fill=(60, 70, 120))
    d.polygon([(x + 4, y + 63), (x + 10, y + 49), (x + 46, y + 49), (x + 52, y + 63)], fill=NAVY)
    d.polygon([(x + 21, y + 49), (x + 28, y + 60), (x + 35, y + 49)], fill=WHITE)
    d.line([(x + 28, y + 51), (x + 28, y + 58)], fill=NAVY2, width=2)
    d.rectangle([x + 23, y + 42, x + 33, y + 50], fill=SKIN_D)
    d.ellipse([x + 11, y + 25, x + 17, y + 34], fill=SKIN, outline=BLACK)
    d.ellipse([x + 39, y + 25, x + 45, y + 34], fill=SKIN, outline=BLACK)
    d.ellipse([x + 14, y + 11, x + 42, y + 47], fill=SKIN, outline=BLACK)
    if kind == 0:
        d.chord([x + 14, y + 9, x + 42, y + 36], 185, 355, fill=(150, 110, 60))
        d.rectangle([x + 18, y + 26, x + 25, y + 32], outline=BLACK)
        d.rectangle([x + 31, y + 26, x + 38, y + 32], outline=BLACK)
        d.line([(x + 25, y + 28), (x + 31, y + 28)], fill=BLACK)
        d.rectangle([x + 21, y + 28, x + 22, y + 30], fill=BLACK)
        d.rectangle([x + 34, y + 28, x + 35, y + 30], fill=BLACK)
        d.line([(x + 23, y + 39), (x + 33, y + 39)], fill=BLACK)
    elif kind == 1:
        d.chord([x + 13, y + 8, x + 43, y + 38], 180, 360, fill=(40, 30, 25))
        d.rectangle([x + 15, y + 12, x + 41, y + 18], fill=(40, 30, 25))
        d.line([(x + 18, y + 25), (x + 25, y + 27)], fill=BLACK, width=2)
        d.line([(x + 31, y + 27), (x + 38, y + 25)], fill=BLACK, width=2)
        d.rectangle([x + 21, y + 29, x + 22, y + 31], fill=BLACK)
        d.rectangle([x + 34, y + 29, x + 35, y + 31], fill=BLACK)
        d.arc([x + 22, y + 38, x + 34, y + 46], 200, 340, fill=BLACK)
    else:
        hair = (30, 22, 18)
        d.chord([x + 12, y + 6, x + 44, y + 38], 180, 360, fill=hair)
        d.ellipse([x + 20, y + 4, x + 44, y + 16], fill=hair)
        for sy in range(y + 36, y + 46, 2):
            for sx in range(x + 18, x + 39, 2):
                if (sx + sy) % 4 == 0:
                    d.point((sx, sy), fill=(110, 90, 80))
        d.line([(x + 18, y + 24), (x + 25, y + 26)], fill=BLACK, width=2)
        d.line([(x + 31, y + 26), (x + 38, y + 24)], fill=BLACK, width=2)
        d.rectangle([x + 21, y + 28, x + 23, y + 31], fill=BLACK)
        d.rectangle([x + 33, y + 28, x + 35, y + 31], fill=BLACK)
        d.line([(x + 23, y + 40), (x + 33, y + 40)], fill=BLACK)


def make_stamp(s, col=RED):
    w = tw(s) + 12
    im = Image.new("RGBA", (w, 22), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.fontmode = "1"
    dd.rectangle([0, 0, w - 1, 21], fill=(252, 236, 236, 255), outline=col + (255,), width=2)
    dd.text((6, 2), s, font=F16, fill=col + (255,))
    return im.rotate(14, expand=True, resample=Image.NEAREST)


STAMP_SACKED = make_stamp("SACKED")


def draw_flames(d, x0, x1, ybot, t, seed):
    rng = random.Random(seed * 1000 + int(t * 15))
    for x in range(x0, x1, 2):
        h = 6 + rng.randint(0, 14)
        for k in range(h):
            f = k / h
            col = RED if f < 0.35 else (ORANGE if f < 0.7 else YELLOW)
            d.rectangle([x, ybot - k, x + 1, ybot - k], fill=col)


def draw_stars(d, t, speed=20, col=WHITE, n=40, seed=7):
    rng = random.Random(seed)
    for _ in range(n):
        sx, sy, sp = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.3, 1.0)
        x = (sx - t * speed * sp) % W
        c = col if sp > 0.6 else GRAY
        d.point((x, sy), fill=c)


# ------------------------------------------------------------------------ audio

_NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def freq(n):
    i, acc = 1, 0
    if n[1] in "#b":
        acc = 1 if n[1] == "#" else -1
        i = 2
    m = 12 * (int(n[i:]) + 1) + _NOTE[n[0]] + acc
    return 440.0 * 2 ** ((m - 69) / 12)


def tone(kind, f0, dur, vol=0.2, duty=0.5, f1=None, decay=None, release=0.015):
    n = max(1, int(dur * SR))
    f = np.full(n, f0) if f1 is None else np.geomspace(f0, f1, n)
    ph = np.cumsum(f) / SR % 1.0
    if kind == "sq":
        w = np.where(ph < duty, 1.0, -1.0)
    elif kind == "tri":
        w = 4 * np.abs(ph - 0.5) - 1
    else:
        w = np.sin(2 * np.pi * ph)
    env = np.ones(n)
    a = min(n, int(0.003 * SR))
    env[:a] = np.linspace(0, 1, a)
    r = min(n, int(release * SR))
    env[n - r:] *= np.linspace(1, 0, r)
    if decay:
        env *= np.exp(-np.arange(n) / SR / decay)
    return w * env * vol


_nrng = np.random.default_rng(2026)


def noise(dur, vol=0.2, decay=0.08, hold=1):
    n = max(1, int(dur * SR))
    w = _nrng.uniform(-1, 1, n // hold + 1).repeat(hold)[:n]
    env = np.exp(-np.arange(n) / SR / decay) if decay else np.ones(n)
    return w * env * vol


def drum(tok):
    if tok == "k":
        return tone("sin", 160, 0.14, 0.5, f1=40, decay=0.06)
    if tok == "s":
        sig = noise(0.12, 0.28, 0.04, hold=2)
        body = tone("tri", 190, 0.06, 0.15, decay=0.03)
        sig[: len(body)] += body
        return sig
    if tok == "h":
        return noise(0.03, 0.09, 0.01)
    if tok == "c":  # clap
        return noise(0.1, 0.3, 0.03, hold=3)
    return np.zeros(1)


class Mixer:
    def __init__(self, dur):
        self.buf = np.zeros(int(dur * SR) + SR, dtype=np.float64)

    def add(self, t, sig):
        i = int(t * SR)
        if i < 0 or i >= len(self.buf):
            return
        n = min(len(sig), len(self.buf) - i)
        self.buf[i:i + n] += sig[:n]

    def seq(self, t0, dur, pattern, bpm, spb=2, kind="sq", vol=0.1, duty=0.5, decay=None, gate=0.9):
        toks = pattern.split()
        step = 60.0 / bpm / spb
        events, i = [], 0
        while i < len(toks):
            n = 1
            while i + n < len(toks) and toks[i + n] == "-":
                n += 1
            if toks[i] not in (".", "-"):
                events.append((i, n, toks[i]))
            i += n
        loop = len(toks) * step
        base = 0.0
        while base < dur:
            for si, n, tk in events:
                st = base + si * step
                if st >= dur:
                    break
                if kind == "drum":
                    self.add(t0 + st, drum(tk))
                else:
                    ln = min(n * step * gate, dur - st)
                    self.add(t0 + st, tone(kind, freq(tk), ln, vol, duty, decay=decay))
            base += loop

    def notes(self, t0, spec, kind="sq", vol=0.12, duty=0.5, decay=None):
        """spec: 'C5:0.1 E5:0.1 ...' — 순차 재생."""
        t = t0
        for tok in spec.split():
            n, d = tok.split(":")
            d = float(d)
            if n != "R":
                self.add(t, tone(kind, freq(n), d * 0.95, vol, duty, decay=decay))
            t += d

    def sfx(self, t, name):
        a = self.add
        if name == "blip":
            a(t, tone("sq", 1250, 0.025, 0.05, duty=0.25))
        elif name == "move":
            a(t, tone("sq", 880, 0.05, 0.1, duty=0.25))
        elif name == "select":
            a(t, tone("sq", 440, 0.12, 0.12, duty=0.25, f1=1760))
        elif name == "start":
            self.notes(t, "C6:0.06 E6:0.06 G6:0.06 C7:0.2", vol=0.1, duty=0.25)
        elif name == "stamp":
            a(t, noise(0.25, 0.4, 0.06, hold=4))
            a(t, tone("sq", 90, 0.2, 0.2, f1=50, decay=0.08))
        elif name == "bump":
            a(t, tone("sq", 180, 0.08, 0.2, f1=120))
            a(t, noise(0.06, 0.15, 0.03, hold=6))
        elif name == "sad":
            self.notes(t + 0.05, "G4:0.12 Eb4:0.12 B3:0.25", vol=0.1, duty=0.25)
        elif name == "jump":
            a(t, tone("sq", 280, 0.16, 0.1, duty=0.25, f1=950))
        elif name == "land":
            a(t, tone("sin", 120, 0.1, 0.4, f1=50, decay=0.05))
        elif name == "fall":
            a(t, tone("sin", 1400, 0.9, 0.16, f1=90))
        elif name == "cash":
            self.notes(t, "E6:0.05 A6:0.18", vol=0.09, duty=0.25, decay=0.15)
            a(t + 0.02, noise(0.08, 0.07, 0.03))
        elif name == "damage":
            a(t, noise(0.35, 0.35, 0.1, hold=5))
            a(t, tone("sq", 400, 0.35, 0.15, f1=60))
        elif name == "hit":
            a(t, noise(0.12, 0.3, 0.04, hold=2))
            a(t, tone("sq", 900, 0.1, 0.1, f1=300))
        elif name == "heal":
            self.notes(t, "C6:0.06 E6:0.06 G6:0.06 C7:0.06 E7:0.2", vol=0.07, duty=0.25)
        elif name == "siren":
            for k in range(2):
                a(t + k * 0.25, tone("sq", 880 if k == 0 else 660, 0.24, 0.08, duty=0.5))
        elif name == "ding":
            a(t, tone("sq", freq("C6"), 0.08, 0.12, duty=0.5))
            a(t + 0.08, tone("sq", freq("C7"), 0.9, 0.12, duty=0.5, decay=0.3))
        elif name == "tick":
            a(t, tone("sq", 1000, 0.04, 0.09, duty=0.25))
        elif name == "lock":
            a(t, noise(0.15, 0.3, 0.05, hold=8))
            a(t, tone("sq", 110, 0.12, 0.2, decay=0.05))
        elif name == "coin":
            self.notes(t, "C6:0.07 G6:0.35", vol=0.1, duty=0.25, decay=0.2)
        elif name == "encounter":
            for k in range(10):
                a(t + k * 0.09, tone("sq", 1400 if k % 2 else 700, 0.08, 0.08, duty=0.25))
        elif name == "glitch":
            a(t, noise(0.6, 0.18, None, hold=40))
        elif name == "fanfare":
            self.notes(t, "C5:0.1 E5:0.1 G5:0.1 C6:0.3 G5:0.1 C6:0.5", vol=0.11, duty=0.25)
            self.notes(t, "E4:0.1 G4:0.1 C5:0.1 E5:0.3 C5:0.1 E5:0.5", vol=0.06, duty=0.5)
            self.notes(t, "C3:0.3 G2:0.3 C3:0.6", kind="tri", vol=0.2)
        elif name == "blackout":
            self.notes(t, "E5:0.25 Eb5:0.25 D5:0.25 Db5:0.9", vol=0.1, duty=0.25)
            self.notes(t, "C3:0.25 B2:0.25 Bb2:0.25 A2:0.9", kind="tri", vol=0.2)
        elif name == "boo":
            a(t, tone("sq", 110, 0.5, 0.05, duty=0.5, f1=90))
            a(t, tone("sq", 116, 0.5, 0.04, duty=0.5, f1=92))

    def blips(self, t0, s, cps=28):
        for k, ch in enumerate(s):
            if ch != " " and k % 2 == 0:
                self.sfx(t0 + k / cps, "blip")


# ----------------------------------------------------------------------- scenes

class Scene:
    dur = 1.0
    fade_in = 0.25
    fade_out = 0.25

    def draw(self, img, d, t):
        pass

    def audio(self, m, t0):
        pass


class Boot(Scene):
    dur = 4.0
    fade_in = 0.0

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(196, 207, 161))
        y = min(64, int(-34 + t / 2.2 * 98))
        ctext(d, y, "SPURS BOY", NAVY, F32, shadow=None)
        text(d, 237, y - 2, "™", NAVY, shadow=None)
        if t > 2.4:
            ctext(d, 112, "LICENSED BY ENIC", (60, 80, 60), shadow=None)
        if t > 2.9:
            ctext(d, 132, "SINCE 2001", (60, 80, 60), shadow=None)

    def audio(self, m, t0):
        m.sfx(t0 + 2.25, "ding")


class Title(Scene):
    dur = 7.0

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=NAVY)
        draw_stars(d, t, 25)
        ctext(d, 10, "SPURS QUEST", WHITE, F32, shadow=GOLD)
        ctext(d, 46, "~ 강등권의 전설 ~", GOLD)
        bob = -1 if int(t * 4) % 2 else 0
        blit(img, COCK_A, 143, 66 + bob, 2)
        d.ellipse([146, 102, 174, 116], fill=WHITE, outline=BLACK)
        d.polygon([(157, 105), (163, 105), (165, 110), (160, 113), (155, 110)], fill=BLACK)
        cur = 1 if 2.8 <= t < 5.0 else 0
        flash = t >= 5.6 and blink(t, 6)
        items = ["새 감독 영입", "트로피 룸"]
        for i, s in enumerate(items):
            if i == 0 and t >= 5.6 and not flash:
                continue
            text(d, 112, 122 + i * 17, s, WHITE)
        text(d, 98, 122 + cur * 17, "▶", GOLD)
        if t < 2.8 and blink(t, 1.5):
            ctext(d, 160, "PUSH START BUTTON", LGRAY)
        if 3.3 <= t < 5.0:
            box(d, 60, 58, 260, 118)
            ctext(d, 64, "- 트로피 룸 -", GOLD)
            ctext(d, 82, "2025 UEFA 유로파리그 ×1", WHITE)
            ctext(d, 99, reveal("...이게 전부다.", t - 3.9, 14), LGRAY)

    def audio(self, m, t0):
        lead = ("C5 - E5 G5 C6 - B5 G5 A5 - F5 A5 G5 - - . "
                "E5 - G5 C6 E6 - D6 C6 B5 - G5 A5 C6 - - .")
        bass = "C3 . C3 . G2 . G2 . F2 . F2 . G2 . G2 . A2 . A2 . E2 . E2 . F2 . G2 . C3 . C3 ."
        m.seq(t0 + 0.2, 5.3, lead, 150, 2, "sq", 0.08, 0.25)
        m.seq(t0 + 0.2, 5.3, bass, 150, 2, "tri", 0.2)
        m.seq(t0 + 0.2, 5.3, "k h s h k k s h", 150, 2, "drum")
        m.sfx(t0 + 2.8, "move")
        m.sfx(t0 + 3.3, "select")
        m.blips(t0 + 3.9, "...이게 전부다.", 14)
        m.sfx(t0 + 5.0, "move")
        m.sfx(t0 + 5.6, "start")


class ManagerSelect(Scene):
    dur = 10.5
    XS = [28, 132, 236]
    NAMES = ["T.FRANK", "I.TUDOR", "DE ZERBI"]
    SEL = [0.8, 3.4, 6.0]
    INFO = [
        ("T.FRANK  8경기 무승", "8개월 만에 경질"),
        ("I.TUDOR  단 44일·7경기", "5경기 승점 1 → 경질"),
        ("DE ZERBI  잔류 성공!", "...그런데 올시즌 4경기 무승"),
    ]
    STAMP = [2.4, 5.0]

    def cur(self, t):
        c = -1
        for i, s in enumerate(self.SEL):
            if t >= s:
                c = i
        return c

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(16, 16, 48))
        off = int(t * 8) % 16
        for x in range(-16, W, 16):
            d.line([(x + off, 0), (x + off, H)], fill=(28, 28, 72))
        for y in range(-16, H, 16):
            d.line([(0, y + off), (W, y + off)], fill=(28, 28, 72))
        ctext(d, 2, "SELECT YOUR MANAGER", GOLD)
        ctext(d, 20, "25-26 시즌에만 감독 3명!", WHITE)
        c = self.cur(t)
        for i, x in enumerate(self.XS):
            draw_manager(d, x, 42, i)
            ctext(d, 110, self.NAMES[i], WHITE, cx=x + 28)
            if i == 2 and t > 7.6:
                draw_flames(d, x, x + 56, 105, t, 3)
                if blink(t, 3):
                    ctext(d, 88, "HOT SEAT", RED, cx=x + 28)
            if i < 2 and t >= self.STAMP[i]:
                k = t - self.STAMP[i]
                sc = 2 if k < 0.08 else 1
                st = STAMP_SACKED
                if sc != 1:
                    st = st.resize((st.width * 2, st.height * 2), Image.NEAREST)
                img.paste(st, (x + 28 - st.width // 2, 70 - st.height // 2), st)
        if c >= 0 and (blink(t, 4) or t - self.SEL[c] < 0.4):
            x = self.XS[c]
            d.rectangle([x - 3, 39, x + 58, 108], outline=YELLOW, width=2)
        if c >= 0:
            box(d, 4, 132, 316, 178)
            l1, l2 = self.INFO[c]
            since = t - self.SEL[c] - 0.4
            text(d, 14, 138, reveal(l1, since), WHITE)
            text(d, 14, 157, reveal(l2, since - len(l1) / 28 - 0.2), RED if c == 2 else LGRAY)

    def audio(self, m, t0):
        lead = ("A4 C5 E5 C5 A4 C5 E5 C5 G4 B4 D5 B4 G4 B4 D5 B4 "
                "F4 A4 C5 A4 F4 A4 C5 A4 E4 G#4 B4 G#4 E4 G#4 B4 E5")
        m.seq(t0 + 0.3, 7.3, lead, 132, 4, "sq", 0.06, 0.25)
        m.seq(t0 + 0.3, 7.3, "A2 - - - G2 - - - F2 - - - E2 - - -", 132, 1, "tri", 0.2)
        m.seq(t0 + 0.3, 7.3, "k . h . s . h . k k h . s . h h", 132, 4, "drum")
        m.seq(t0 + 7.6, 2.9, "E5 F5 E5 D#5", 240, 2, "sq", 0.07, 0.125)
        m.seq(t0 + 7.6, 2.9, "E2 E3", 240, 2, "tri", 0.2)
        for i, s in enumerate(self.SEL):
            m.sfx(t0 + s, "move" if i else "select")
            l1, l2 = self.INFO[i]
            m.blips(t0 + s + 0.4, l1)
            m.blips(t0 + s + 0.4 + len(l1) / 28 + 0.2, l2)
        for s in self.STAMP:
            m.sfx(t0 + s, "stamp")


class Platformer(Scene):
    dur = 14.5
    INTRO = 1.8
    SPD = 60.0
    CAM_STOP = 9.5
    GROUND = 148
    HITS = [2.6, 3.6, 4.6, 5.6, 6.6, 7.6]
    DROPS = ["L", "L", "L", "L", "D", "L"]
    WINLESS = [2, 4, 7, 10, 15, 15]
    BANNERS = [
        "2026년, 리그 승리가 사라졌다",
        "T.FRANK 경질",
        "구단 최초 6연패",
        "리그 15경기 연속 무승",
        "I.TUDOR 44일 만에 경질",
        "DE ZERBI 부임 (3번째 감독)",
    ]
    PIT = (612, 708)
    HERO_Y = GROUND - 18

    def cam(self, t):
        return max(0.0, min(t, self.CAM_STOP) - self.INTRO) * self.SPD

    def draw(self, img, d, t):
        if t < self.INTRO:
            d.rectangle([0, 0, W, H], fill=BLACK)
            ctext(d, 56, "WORLD 25-26", WHITE)
            blit(img, COCK_A, 128, 84)
            text(d, 152, 86, "× 3 (감독)", WHITE)
            return
        cam = self.cam(t)
        d.rectangle([0, 0, W, H], fill=SKY)
        for wx, wy in ((40, 30), (200, 44), (330, 26), (470, 50)):
            sx = (wx - cam * 0.3) % 480 - 80
            for ox, oy, r in ((0, 4, 10), (12, 0, 12), (26, 4, 10)):
                d.ellipse([sx + ox - r, wy + oy - r // 2, sx + ox + r, wy + oy + r // 2 + 4], fill=WHITE)
        for wx in (0, 260, 520):
            sx = (wx - cam * 0.5) % 780 - 140
            d.ellipse([sx, 108, sx + 120, 188], fill=GREEN, outline=DGREEN)
            d.rectangle([sx + 50, 124, sx + 52, 128], fill=DGREEN)
        # ground
        gx0 = int(cam // 16) * 16
        for wx in range(gx0, gx0 + W + 32, 16):
            if self.PIT[0] <= wx < self.PIT[1]:
                continue
            sx = wx - cam
            for gy in (self.GROUND, self.GROUND + 16):
                d.rectangle([sx, gy, sx + 15, gy + 15], fill=BROWN)
                d.line([(sx, gy), (sx + 15, gy)], fill=(252, 188, 176))
                d.line([(sx, gy + 8), (sx + 15, gy + 8)], fill=BLACK)
                d.line([(sx, gy + 1), (sx, gy + 7)], fill=BLACK)
                d.line([(sx + 8, gy + 9), (sx + 8, gy + 15)], fill=BLACK)
        px0 = self.PIT[0] - cam
        if px0 < W:
            d.rectangle([px0, self.GROUND, px0 + 95, H], fill=(20, 0, 0))
            text(d, px0, 158, "CHAMPIONSHIP", RED, shadow=None)
        # ? blocks
        for i, ht in enumerate(self.HITS):
            bx = 80 + (ht - self.INTRO) * self.SPD - cam + 1
            if -20 < bx < W:
                by = 79 - (3 if 0 <= t - ht < 0.1 else 0)
                if t < ht:
                    d.rectangle([bx, by, bx + 15, by + 15], fill=GOLD, outline=BLACK)
                    text(d, bx + 4, by - 1, "?", BROWN, shadow=None)
                else:
                    d.rectangle([bx, by, bx + 15, by + 15], fill=(150, 80, 40), outline=BLACK)
                k = t - ht
                if 0 <= k < 1.0:
                    iy = 79 - 16 - int(22 * min(1.0, k / 0.35))
                    col = RED if self.DROPS[i] == "L" else GRAY
                    d.rectangle([bx + 1, iy, bx + 14, iy + 15], fill=col, outline=WHITE)
                    text(d, bx + 4, iy - 1, self.DROPS[i], WHITE, shadow=None)
        # hero
        hx, hy, airborne = 80, self.HERO_Y, False
        if t < self.CAM_STOP:
            for ht in self.HITS:
                k = t - (ht - 0.3)
                if 0 <= k < 0.6:
                    hy -= 35 * 4 * (k / 0.6) * (1 - k / 0.6)
                    airborne = True
        elif t < 10.3:
            hx = 80 + (t - 9.5) * 62
        elif t < 11.2:
            k = (t - 10.3) / 0.9
            hx = 130 + 108 * k
            hy -= 50 * 4 * k * (1 - k)
            airborne = True
        else:
            hx = 238
            if t < 12.2:
                hx += 1 if int(t * 16) % 2 else -1
                text(d, hx + 5, hy - 18, "!", RED)
        running = t < self.CAM_STOP or 9.5 <= t < 10.3
        spr = COCK_B if airborne or (running and int(t * 8) % 2) else COCK_A
        blit(img, spr, hx - 1, hy)
        # west ham
        if t >= 11.3:
            k = t - 11.3
            wx = -20 + 200 * k
            wy = self.GROUND - 23
            edge = self.PIT[0] - cam - 2
            if wx > edge:
                kf = (wx - edge) / 200
                wx = edge + 40 * kf
                wy += 0.5 * 500 * kf * kf
            if wy < H:
                draw_hammer(d, wx, wy, t)
        # HUD
        wl = 0
        for i, ht in enumerate(self.HITS):
            if t >= ht:
                wl = self.WINLESS[i]
        text(d, 8, 2, "SPURS", WHITE)
        text(d, 110, 2, f"무승 {wl:02d}", WHITE)
        text(d, 226, 2, "WORLD 25-26", WHITE)
        banner = None
        for i, ht in enumerate(self.HITS):
            if 0 <= t - ht < 1.0:
                banner = (self.BANNERS[i], RED)
        if 9.5 <= t < 11.2:
            banner = ("최종전 vs EVERTON", WHITE)
        elif 11.2 <= t < 12.3:
            banner = ("1-0 승리!! 잔류다!!", GOLD)
        elif 12.3 <= t < 12.9:
            banner = ("WEST HAM 강등...", LGRAY)
        if banner:
            s, col = banner
            w = tw(s)
            d.rectangle([W // 2 - w // 2 - 4, 21, W // 2 + w // 2 + 4, 39], fill=BLACK)
            ctext(d, 22, s, col)
        if t >= 12.9:
            box(d, 60, 50, 260, 132)
            ctext(d, 54, "SURVIVED!", GOLD, F32)
            ctext(d, 90, "17위 · 승점 41", WHITE)
            ctext(d, 108, "(세계 9위 부자 구단)", LGRAY)

    def audio(self, m, t0):
        lead = ("G5 . D5 G5 . B5 A5 G5 E5 . C5 E5 G5 - . . "
                "F#5 . D5 F#5 . A5 G5 F#5 G5 - - - . . . .")
        bass = "G2 . D3 . G2 . D3 . C3 . G2 . C3 . G2 . D3 . A2 . D3 . A2 . G2 . D3 . G2 . D3 ."
        dur = self.CAM_STOP - self.INTRO
        m.seq(t0 + self.INTRO, dur, lead, 160, 2, "sq", 0.07, 0.25)
        m.seq(t0 + self.INTRO, dur, bass, 160, 2, "tri", 0.2)
        m.seq(t0 + self.INTRO, dur, "k h s h", 160, 2, "drum")
        for ht in self.HITS:
            m.sfx(t0 + ht - 0.3, "jump")
            m.sfx(t0 + ht, "bump")
            m.sfx(t0 + ht + 0.05, "sad")
        m.seq(t0 + 9.6, 0.7, "E3 . E3 .", 320, 2, "tri", 0.2)
        for k in range(18):
            m.add(t0 + 10.3 + k * 0.05, drum("h") * 2)
        m.sfx(t0 + 10.3, "jump")
        m.sfx(t0 + 11.2, "land")
        m.notes(t0 + 11.25, "C6:0.08 E6:0.08 G6:0.2", vol=0.08, duty=0.25)
        m.sfx(t0 + 12.15, "fall")
        m.sfx(t0 + 12.9, "fanfare")


class Shop(Scene):
    dur = 10.0
    fade_out = 0.0
    ITEMS = [("M.FERNANDES", "£85M"), ("S.TONALI", "£££"), ("A.ROBERTSON", "£££"),
             ("VAN HECKE", "£££"), ("M.SENESI", "£££"), ("MUDRYK", "임대"), ("ADARABIOYO", "£10M")]
    BUY0, GAP = 1.2, 0.8
    LINES = [(0.3, "상인: 어서오시오! 뭘 사겠소?", WHITE),
             (1.4, "상인: £85M! 구단 신기록이오!", GOLD),
             (3.2, "상인: 더! 더 사시오!", WHITE),
             (7.0, "상인: 이 정도면 우승이지! 하하!", WHITE)]

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(24, 16, 40))
        ctext(d, 2, "★ 2026 여름 이적시장 SHOP ★", GOLD)
        # shopkeeper
        x, y = 22, 34
        d.rectangle([x - 12, y + 60, x + 60, y + 78], fill=(120, 72, 32), outline=BLACK)
        d.ellipse([x + 8, y, x + 40, y + 34], fill=SKIN, outline=BLACK)
        d.chord([x + 8, y - 2, x + 40, y + 22], 180, 360, fill=(90, 60, 30))
        d.rectangle([x + 16, y + 14, x + 18, y + 16], fill=BLACK)
        d.rectangle([x + 30, y + 14, x + 32, y + 16], fill=BLACK)
        d.polygon([(x + 14, y + 23), (x + 24, y + 20), (x + 34, y + 23), (x + 24, y + 26)], fill=(60, 40, 20))
        smile = 2 if int(t * 3) % 2 else 0
        d.arc([x + 18, y + 22, x + 30, y + 30 + smile], 20, 160, fill=BLACK)
        d.rectangle([x + 4, y + 34, x + 44, y + 60], fill=(40, 120, 60), outline=BLACK)
        d.rectangle([x + 16, y + 38, x + 32, y + 60], fill=WHITE, outline=BLACK)
        text(d, x + 20, y + 40, "£", GOLD, shadow=None)
        # budget
        bought = sum(1 for i in range(len(self.ITEMS)) if t >= self.BUY0 + i * self.GAP)
        text(d, 6, 116, "자금", WHITE)
        frac = max(0.04, 1 - bought / len(self.ITEMS) * 0.96)
        d.rectangle([40, 120, 82, 128], fill=BLACK, outline=WHITE)
        d.rectangle([41, 121, 41 + int(40 * frac), 127], fill=GREEN if frac > 0.3 else RED)
        # item list
        box(d, 88, 20, 316, 134)
        cur = min(bought, len(self.ITEMS) - 1)
        for i, (name, price) in enumerate(self.ITEMS):
            yy = 24 + i * 15
            sold = t >= self.BUY0 + i * self.GAP
            col = GRAY if sold else WHITE
            text(d, 104, yy, name, col)
            text(d, 310 - tw(price), yy, price, GOLD if not sold else GRAY)
            if sold and t - (self.BUY0 + i * self.GAP) < 0.25:
                d.rectangle([100, yy + 1, 312, yy + 16], outline=YELLOW)
            if sold:
                text(d, 196, yy, "SOLD", RED)
        if t < self.BUY0 + len(self.ITEMS) * self.GAP:
            text(d, 92, 24 + cur * 15, "▶", GOLD)
        # dialog
        box(d, 4, 140, 316, 178)
        line = None
        for st, s, col in self.LINES:
            if t >= st:
                line = (st, s, col)
        if line:
            st, s, col = line
            text(d, 14, 151, reveal(s, t - st), col)
        if t >= 9.4:
            rng = random.Random(int(t * 30))
            for _ in range(14):
                yy = rng.randint(0, H)
                d.rectangle([0, yy, W, yy + rng.randint(1, 6)],
                            fill=rng.choice([WHITE, RED, NAVY2, BLACK, GOLD]))

    def audio(self, m, t0):
        lead = ("F5 . A5 . C6 . A5 . Bb5 . G5 . E5 . C5 . "
                "F5 . A5 . C6 . F6 . E6 . C6 . F6 - - .")
        bass = "F3 . C3 . F3 . C3 . Bb2 . F3 . C3 . G3 . F3 . C3 . A2 . A3 . C3 . C3 . F3 . C3 ."
        m.seq(t0 + 0.2, 9.2, lead, 116, 2, "sq", 0.07, 0.5, decay=0.25)
        m.seq(t0 + 0.2, 9.2, bass, 116, 2, "tri", 0.18)
        m.seq(t0 + 0.2, 9.2, "k . h . s . h .", 116, 2, "drum")
        for st, s, _ in self.LINES:
            m.blips(t0 + st, s)
        for i in range(len(self.ITEMS)):
            m.sfx(t0 + self.BUY0 + i * self.GAP, "cash")
        m.sfx(t0 + 9.4, "glitch")


class Battle(Scene):
    dur = 21.4
    fade_in = 0.0
    B0, BLEN = 1.0, 4.4
    FOES = [
        ("bee", "BRENTFORD", ["야생의 BRENTFORD가 나타났다!", "SPURS의 £85M 신입생 공격!",
                             "효과가 없는 것 같다... 0-3 패!"], "damage", 0),
        ("magpie", "NEWCASTLE", ["NEWCASTLE이 나타났다!", "SPURS는 슈팅을 시도했다!",
                                "그러나 빗나갔다! 0-2 패!"], "damage", 0),
        ("toffee", "EVERTON", ["EVERTON이 나타났다!", "SPURS는 몸을 웅크렸다...",
                              "아무 일도 없었다. 0-0 (승점+1)"], "heal", 1),
        ("lion", "ASTON VILLA", ["ASTON VILLA가 나타났다!", "드디어 SPURS의 첫 골! 2골!!",
                                "그러나 VILLA는 3골! 2-3 패!"], "damage", 0),
    ]
    MSG_T = [0.2, 1.5, 2.8]
    END = B0 + 4 * BLEN

    def state(self, t):
        pts, games = 0, 0
        for i, f in enumerate(self.FOES):
            if t >= self.B0 + i * self.BLEN + 2.8:
                pts += f[4]
                games += 1
        return pts, games

    def draw(self, img, d, t):
        if t < self.B0:
            if t < 0.9 and int(t * 11) % 2:
                d.rectangle([0, 0, W, H], fill=WHITE)
            else:
                d.rectangle([0, 0, W, H], fill=BLACK)
            k = max(0.0, (t - 0.55) / 0.45)
            for yy in range(0, H, 12):
                d.rectangle([0, yy, int(W * k), yy + 5], fill=BLACK)
                d.rectangle([W - int(W * k), yy + 6, W, yy + 11], fill=BLACK)
            return None
        d.rectangle([0, 0, W, H], fill=CREAM)
        d.ellipse([190, 66, 290, 86], fill=(176, 208, 144), outline=(120, 150, 90))
        d.ellipse([20, 114, 110, 130], fill=(176, 208, 144), outline=(120, 150, 90))
        shake = None
        pts, games = self.state(t)
        i = min(3, int((t - self.B0) // self.BLEN))
        lt = t - self.B0 - i * self.BLEN
        msg = None
        if t < self.END:
            kind, name, msgs, eff, _ = self.FOES[i]
            ex = 240 + max(0, int((0.4 - lt) / 0.4 * 120))
            flash = (i == 3 and 2.1 <= lt < 2.5 and int(lt * 16) % 2)
            bob = 1 if int(t * 3) % 2 else 0
            draw_monster(d, kind, ex, 50 + bob, t, flash)
            box(d, 4, 4, 150, 40, fill=WHITE, border=NAVY)
            text(d, 12, 7, name, BLACK, shadow=None)
            hp = 0.6 if (i == 3 and lt >= 2.1) else 1.0
            d.rectangle([40, 27, 140, 32], fill=BLACK)
            d.rectangle([41, 28, 41 + int(98 * hp), 31], fill=GREEN)
            text(d, 12, 22, "HP", GOLD, shadow=None)
            for k, mt in enumerate(self.MSG_T):
                if lt >= mt:
                    msg = (msgs[k], lt - mt, RED if k == 2 and eff == "damage" else BLACK)
            if eff == "damage" and 2.8 <= lt < 3.2:
                shake = (random.Random(int(t * 60)).randint(-4, 4), 0)
            if eff == "heal" and 2.8 <= lt < 3.6:
                rng = random.Random(int(t * 20))
                for _ in range(8):
                    sx, sy = rng.randint(36, 90), rng.randint(80, 124)
                    d.text((sx, sy), "✦", font=F16, fill=GOLD)
        else:
            lt2 = t - self.END
            first = "SPURS는 눈앞이 캄캄해졌다..."
            msg = (first, lt2 - 0.1, BLACK) if lt2 < 1.6 else ("4경기 승점 1 · 강등권 추락!", lt2 - 1.6, RED)
        # player
        hurt = msg is not None and i < 4 and t < self.END and self.FOES[i][3] == "damage" and 2.8 <= lt < 3.4
        if not (hurt and int(t * 16) % 2):
            blit(img, COCK_A, 44, 84, 2)
        box(d, 166, 88, 316, 128, fill=WHITE, border=NAVY)
        text(d, 174, 91, "SPURS", BLACK, shadow=None)
        text(d, 250, 91, f"{games}경기", BLACK, shadow=None)
        text(d, 174, 108, "승점", BLACK, shadow=None)
        d.rectangle([210, 112, 306, 119], fill=BLACK)
        if pts:
            d.rectangle([211, 113, 211 + int(94 * pts / 12), 118], fill=RED)
        box(d, 4, 132, 316, 178, fill=WHITE, border=NAVY)
        if msg:
            s, since, col = msg
            text(d, 14, 147, reveal(s, since), col, shadow=None)
        if t > self.END + 0.7:
            k = min(1.0, (t - self.END - 0.7) / 2.4)
            a = np.asarray(img).astype(np.float32)
            a[:130] *= 1 - k
            img.paste(Image.fromarray(a.astype(np.uint8)))
        return {"shake": shake}

    def audio(self, m, t0):
        m.sfx(t0, "encounter")
        lead = ("E5 . E5 G5 . E5 A5 . G5 . F#5 . D5 . B4 . "
                "E5 . E5 G5 . E5 B5 . A5 . G5 . F#5 . G5 A5")
        bass = "E2 E3 E2 E3 E2 E3 E2 E3 D2 D3 D2 D3 B1 B2 B1 B2"
        m.seq(t0 + self.B0, self.END - self.B0, lead, 172, 2, "sq", 0.06, 0.25)
        m.seq(t0 + self.B0, self.END - self.B0, bass, 172, 2, "tri", 0.18)
        m.seq(t0 + self.B0, self.END - self.B0, "k h s h k k s h", 172, 2, "drum")
        for i, (_, _, msgs, eff, _) in enumerate(self.FOES):
            bt = t0 + self.B0 + i * self.BLEN
            for k, mt in enumerate(self.MSG_T):
                m.blips(bt + mt, msgs[k])
            if i == 3:
                m.sfx(bt + 2.1, "hit")
                m.sfx(bt + 2.3, "hit")
            m.sfx(bt + 2.8, eff)
        m.sfx(t0 + self.END + 0.1, "blackout")
        m.blips(t0 + self.END + 0.1, "SPURS는 눈앞이 캄캄해졌다...")
        m.blips(t0 + self.END + 1.6, "4경기 승점 1 · 강등권 추락!")


class Tetris(Scene):
    dur = 9.0
    X0, Y0, C = 110, 10, 10
    DROP0, RATE = 0.8, 4.0
    LAND_ROW = 14

    def garbage(self):
        rows = {}
        rng = random.Random(42)
        for r in range(9, 16):
            holes = {4, 5} | {rng.choice([0, 1, 2, 7, 8, 9])}
            rows[r] = [c for c in range(10) if c not in holes]
        return rows

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(8, 8, 24))
        for y in range(0, H, 8):
            for x in range((y // 8) % 2 * 8, W, 16):
                d.point((x, y), fill=(40, 40, 80))
        X0, Y0, C = self.X0, self.Y0, self.C
        danger = t >= 4.3 and blink(t, 3)
        d.rectangle([X0 - 3, Y0 - 3, X0 + 10 * C + 2, Y0 + 16 * C + 2], outline=LGRAY, width=2)
        d.rectangle([X0, Y0, X0 + 10 * C - 1, Y0 + 16 * C - 1], fill=BLACK)
        zone = (90, 0, 0) if danger else (50, 0, 0)
        d.rectangle([X0, Y0 + 13 * C, X0 + 10 * C - 1, Y0 + 16 * C - 1], fill=zone)
        for r, cols in self.garbage().items():
            for c in cols:
                x, y = X0 + c * C, Y0 + r * C
                d.rectangle([x, y, x + C - 1, y + C - 1], fill=GRAY, outline=(70, 70, 70))
                d.point((x + 2, y + 2), fill=LGRAY)
        row = min(self.LAND_ROW, max(0, int((t - self.DROP0) * self.RATE)))
        if t >= self.DROP0 - 0.3:
            for dr in (0, 1):
                for dc in (4, 5):
                    x, y = X0 + dc * C, Y0 + (row + dr) * C
                    d.rectangle([x, y, x + C - 1, y + C - 1], fill=NAVY2, outline=WHITE)
        text(d, X0 + 10 * C + 6, Y0 + 13 * C + 4, "강등권", RED)
        # side panels
        for (y, label, val, col) in ((6, "SCORE", "1 (승점)", WHITE), (48, "LINES", "0 (승리)", WHITE),
                                     (90, "LEVEL", "강등권", RED)):
            box(d, 4, y, 104, y + 38)
            text(d, 12, y + 3, label, GOLD)
            text(d, 12, y + 19, val, col)
        box(d, 216, 6, 316, 62)
        text(d, 224, 9, "NEXT", GOLD)
        text(d, 224, 26, "MAN UTD", WHITE)
        text(d, 224, 43, "10.10", LGRAY)
        box(d, 216, 68, 316, 108)
        text(d, 224, 71, "득점 2", WHITE)
        text(d, 224, 88, "실점 8", RED)
        text(d, 8, 136, "SPURS-TRIS", NAVY2)
        if t >= 5.0 and blink(t, 2):
            d.rectangle([0, 70, W, 108], fill=RED)
            ctext(d, 73, "WARNING!!", WHITE, F32, shadow=DRED)

    def audio(self, m, t0):
        # 코로베이니키 (러시아 민요, 퍼블릭 도메인)
        a = ("E5 - B4 C5 D5 - C5 B4 A4 - A4 C5 E5 - D5 C5 B4 - - C5 D5 - E5 - C5 - A4 - A4 - - - "
             ". D5 - F5 A5 - G5 F5 E5 - - C5 E5 - D5 C5 B4 - B4 C5 D5 - E5 - C5 - A4 - A4 - - -")
        bass = "E2 E3 E2 E3 A2 A3 A2 A3 G#2 G#3 G#2 G#3 A2 A3 B2 C3"
        m.seq(t0 + 0.3, 4.0, a, 150, 2, "sq", 0.08, 0.5)
        m.seq(t0 + 0.3, 4.0, bass, 150, 2, "tri", 0.18)
        for k in range(1, self.LAND_ROW + 1):
            m.sfx(t0 + self.DROP0 + k / self.RATE, "tick")
        m.sfx(t0 + self.DROP0 + self.LAND_ROW / self.RATE + 0.02, "lock")
        for k in range(8):
            m.sfx(t0 + 5.0 + k * 0.5, "siren")


class Protest(Scene):
    dur = 8.0
    B1 = "PROMISED CHANGE, DELIVERED FAILURE ★ "
    B2 = "LOVE TOTTENHAM, HATE ENIC ★ "

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(8, 8, 40))
        for lx in (20, 300):
            d.polygon([(lx, 10), (lx - 60, 90), (lx + 60, 90)], fill=(24, 24, 64))
            d.ellipse([lx - 6, 4, lx + 6, 16], fill=WHITE)
        ctext(d, 22, "시즌 최종전 후, 팬들은 분노했다", WHITE)
        d.rectangle([0, 56, W, 150], fill=(30, 30, 50))
        rng = random.Random(9)
        for row, y in enumerate(range(58, 148, 9)):
            for col, x in enumerate(range(2 + (row % 2) * 4, W, 8)):
                bob = -2 if math.sin(t * 9 + col * 0.8 + row) > 0.3 else 0
                c = rng.choice([SKIN, SKIN_D, (140, 90, 60), (90, 60, 40)])
                hat = rng.random() < 0.3
                d.ellipse([x, y + bob, x + 5, y + 5 + bob], fill=c)
                if hat:
                    d.rectangle([x, y + bob, x + 5, y + 1 + bob], fill=NAVY2 if rng.random() < 0.5 else WHITE)
                if math.sin(t * 9 + col * 0.8 + row) > 0.3 and (col + row) % 5 == 0:
                    d.line([(x - 1, y + bob - 1), (x - 3, y + bob - 5)], fill=c, width=2)
        for (y, s, sp) in ((70, self.B1, 55), (110, self.B2, -48)):
            d.rectangle([0, y, W, y + 20], fill=WHITE, outline=NAVY)
            full = s * 4
            wfull = tw(s)
            off = (t * sp) % wfull
            text(d, -int(off) if sp > 0 else int(off) - wfull, y + 2, full, NAVY, shadow=None)
        box(d, 4, 152, 316, 178)
        text(d, 14, 157, "분노 게이지", WHITE)
        k = min(1.0, max(0.0, (t - 0.8) / 4.5))
        d.rectangle([108, 160, 250, 170], fill=BLACK, outline=WHITE)
        d.rectangle([109, 161, 109 + int(140 * k), 169], fill=RED if k > 0.7 else ORANGE)
        if k >= 1.0 and blink(t, 3):
            text(d, 258, 157, "MAX!!", RED)

    def audio(self, m, t0):
        m.seq(t0 + 0.2, 7.4, "k . c . k k c .", 124, 2, "drum")
        crowd = noise(7.6, 0.04, None, hold=1)
        crowd = np.convolve(crowd, np.ones(20) / 20, mode="same") * 3
        m.add(t0 + 0.1, crowd)
        for k in range(0, 7):
            m.sfx(t0 + 0.4 + k * 0.97, "boo")


class Continue(Scene):
    dur = 9.5
    COUNT0, STEP = 0.3, 0.7
    COIN = 4.5

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        if t < 5.2:
            ctext(d, 8, "CONTINUE?", RED, F32, shadow=DRED)
            n = 9 - int(max(0.0, t - self.COUNT0) / self.STEP)
            if t >= self.COUNT0:
                ctext(d, 44, str(max(n, 3)), WHITE, F64, shadow=GRAY)
            blit(img, COCK_DEAD, 144, 126, 2, flip_v=True)
            if 2.0 < t < 4.5 and blink(t, 2):
                ctext(d, 162, "INSERT COIN", GOLD)
        # coin slot + coin
        d.rectangle([262, 96, 290, 124], fill=(40, 40, 40), outline=LGRAY)
        d.rectangle([274, 100, 278, 120], fill=BLACK)
        if self.COIN <= t < self.COIN + 0.5:
            k = (t - self.COIN) / 0.5
            cy = -10 + 110 * k * k
            d.ellipse([268, cy, 284, cy + 16], fill=GOLD, outline=BLACK)
            text(d, 272, cy, "£", BROWN, shadow=None)
            if cy < 70:
                text(d, 260, 80, "ENIC", LGRAY)
        if t >= 5.0:
            text(d, 232, 130, "CREDIT 01", WHITE)
        if t >= 5.2:
            k = t - 5.4
            jy = 0
            if 0 <= k < 0.5:
                jy = -int(40 * 4 * (k / 0.5) * (1 - k / 0.5))
            blit(img, COCK_A if t >= 5.4 else COCK_DEAD, 144, 118 + jy, 2)
        if t >= 6.0:
            ctext(d, 16, "NEXT STAGE ▶ vs MAN UTD", WHITE)
            ctext(d, 36, "10월 10일", LGRAY)
        if t >= 7.0:
            ctext(d, 66, "팬들의 인내심: ♥♡♡", RED)

    def audio(self, m, t0):
        m.seq(t0 + 0.3, 4.4, "A3 - - - E3 - - - F3 - - - E3 - - -", 170, 2, "tri", 0.2)
        for k in range(7):
            m.sfx(t0 + self.COUNT0 + k * self.STEP, "tick")
        m.sfx(t0 + self.COIN, "coin")
        m.sfx(t0 + 5.0, "ding")
        m.sfx(t0 + 5.4, "jump")
        m.notes(t0 + 6.0, "G5:0.1 C6:0.1 E6:0.1 G6:0.3", vol=0.08, duty=0.25)


class Ending(Scene):
    dur = 7.5
    fade_out = 1.2

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        draw_stars(d, t, 6, n=30, seed=3)
        ctext(d, 12, "THANK YOU SPURS FANS!", WHITE)
        if t > 1.0:
            ctext(d, 40, reveal("하지만 트로피는", t - 1.0, 12), WHITE)
        if t > 2.2:
            ctext(d, 60, reveal("다른 성에 있습니다!", t - 2.2, 12), GOLD)
        # castle
        cx, cy = 240, 88
        d.rectangle([cx, cy, cx + 48, cy + 36], fill=(150, 80, 40), outline=BLACK)
        for bx in range(cx, cx + 48, 12):
            d.rectangle([bx, cy - 6, bx + 6, cy], fill=(150, 80, 40), outline=BLACK)
        d.rectangle([cx + 18, cy + 16, cx + 30, cy + 36], fill=BLACK)
        d.line([(cx + 24, cy - 6), (cx + 24, cy - 24)], fill=LGRAY)
        d.polygon([(cx + 24, cy - 24), (cx + 38, cy - 20), (cx + 24, cy - 16)], fill=RED)
        text(d, cx + 20, cy + 2, "?", GOLD, shadow=None)
        blit(img, COCK_A if int(t * 3) % 2 else COCK_B, 40, 104, 2)
        if t > 3.5:
            ctext(d, 118, "TO BE CONTINUED" + "." * (int(t * 2) % 4), LGRAY)
        if t > 4.2:
            ctext(d, 144, "※ 2026.09.24 기준 실제 경기 결과를", GRAY)
            ctext(d, 161, "바탕으로 만든 풍자 패러디입니다", GRAY)

    def audio(self, m, t0):
        mel = ("C5:0.3 E5:0.3 G5:0.3 C6:0.6 B5:0.3 G5:0.3 A5:0.6 F5:0.3 D5:0.3 "
               "G5:0.9 E5:0.3 C5:0.3 D5:0.3 C5:1.2")
        m.notes(t0 + 0.3, mel, vol=0.08, duty=0.25)
        m.notes(t0 + 0.3, "C3:1.2 F2:1.2 G2:1.2 C3:1.2 G2:0.6 C3:1.2", kind="tri", vol=0.2)
        m.notes(t0 + 6.0, "C4:1.0", vol=0.05)
        m.notes(t0 + 6.0, "E4:1.0", vol=0.05)
        m.notes(t0 + 6.0, "G4:1.0", vol=0.05)


# -------------------------------------------------------------------------- main

def main():
    scenes = [Boot(), Title(), ManagerSelect(), Platformer(), Shop(), Battle(),
              Tetris(), Protest(), Continue(), Ending()]
    starts, acc = [], 0.0
    for s in scenes:
        starts.append(acc)
        acc += s.dur
    total = acc

    mix = Mixer(total)
    for s, st in zip(scenes, starts):
        s.audio(mix, st)
    buf = mix.buf[: int(total * SR)]
    buf = buf / max(1e-9, np.max(np.abs(buf))) * 0.85
    wav_path = os.path.join(HERE, "_audio.wav")
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((buf * 32767).astype(np.int16).tobytes())

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W * SCALE}x{H * SCALE}", "-r", str(FPS), "-i", "-",
           "-i", wav_path, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    scan = np.ones((H * SCALE, 1, 1), dtype=np.float32)
    scan[3::4] = 0.72
    nframes = int(total * FPS)
    si = 0
    for fi in range(nframes):
        t = fi / FPS
        while si + 1 < len(scenes) and t >= starts[si + 1]:
            si += 1
        sc, lt = scenes[si], t - starts[si]
        img = Image.new("RGB", (W, H), BLACK)
        d = ImageDraw.Draw(img)
        d.fontmode = "1"
        res = sc.draw(img, d, lt) or {}
        arr = np.asarray(img).astype(np.float32)
        if res.get("shake"):
            arr = np.roll(arr, res["shake"][0], axis=1)
        k = 1.0
        if sc.fade_in and lt < sc.fade_in:
            k = lt / sc.fade_in
        if sc.fade_out and lt > sc.dur - sc.fade_out:
            k = min(k, (sc.dur - lt) / sc.fade_out)
        if k < 1.0:
            arr *= round(max(0.0, k) * 4) / 4  # NES식 계단형 페이드
        big = arr.repeat(SCALE, 0).repeat(SCALE, 1) * scan
        proc.stdin.write(big.astype(np.uint8).tobytes())
        if fi % 300 == 0:
            print(f"frame {fi}/{nframes}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(wav_path)
    print("wrote", OUT, f"({total:.1f}s)")


if __name__ == "__main__":
    main()
