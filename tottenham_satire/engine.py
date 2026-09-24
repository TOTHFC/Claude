"""공통 엔진: 화면 상수, 한글 도트 텍스트, UI 박스, 칩튠 오디오 믹서."""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, SCALE = 480, 270, 4  # 480x270 도트 → 1920x1080 출력
FPS = 30
SR = 44100

FONT_PATH = "/usr/share/fonts/opentype/unifont/unifont.otf"
F16 = ImageFont.truetype(FONT_PATH, 16)
F32 = ImageFont.truetype(FONT_PATH, 32)
F64 = ImageFont.truetype(FONT_PATH, 64)

BLACK = (0, 0, 0)
WHITE = (252, 252, 252)
NAVY = (19, 34, 87)         # 토트넘 네이비
BINARY = (24, 30, 64)       # 26/27 킷 반바지 'Binary Blue'
NAVY2 = (48, 72, 160)
GOLD = (248, 184, 0)
RED = (228, 40, 40)
AIA_RED = (214, 0, 28)
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


def tw(s, font=F16):
    return int(font.getlength(s))


def text(d, x, y, s, fill=WHITE, font=F16, shadow=BLACK):
    if shadow is not None:
        off = 1 if font is F16 else (2 if font is F32 else 4)
        d.text((x + off, y + off), s, font=font, fill=shadow)
    d.text((x, y), s, font=font, fill=fill)


def ctext(d, y, s, fill=WHITE, font=F16, shadow=BLACK, cx=W // 2):
    text(d, cx - tw(s, font) // 2, y, s, fill, font, shadow)


def box(d, x0, y0, x1, y1, fill=BLACK, border=WHITE):
    d.rectangle([x0, y0, x1, y1], fill=fill)
    d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], outline=border, width=2)


def reveal(s, since, cps=24):
    if since < 0:
        return ""
    return s[: int(since * cps)]


def blink(t, hz=2.0):
    return int(t * hz * 2) % 2 == 0


def add_outline(im, col=BLACK):
    """RGBA 이미지 둘레에 1px 외곽선을 두른다(1px 여백 추가)."""
    w, h = im.size
    out = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    out.paste(im, (1, 1))
    a = np.array(out.split()[3]) > 0
    grow = np.zeros_like(a)
    grow[1:, :] |= a[:-1, :]
    grow[:-1, :] |= a[1:, :]
    grow[:, 1:] |= a[:, :-1]
    grow[:, :-1] |= a[:, 1:]
    edge = grow & ~a
    arr = np.array(out)
    arr[edge] = col + (255,)
    return Image.fromarray(arr)


_scaled = {}


def blit(img, spr, x, y, scale=1, flip_v=False, flip_h=False):
    key = (id(spr), scale, flip_v, flip_h)
    if key not in _scaled:
        s = spr
        if flip_v:
            s = s.transpose(Image.FLIP_TOP_BOTTOM)
        if flip_h:
            s = s.transpose(Image.FLIP_LEFT_RIGHT)
        if scale != 1:
            s = s.resize((s.width * scale, s.height * scale), Image.NEAREST)
        _scaled[key] = (s, spr)  # spr 참조를 잡아둬 id 재사용을 막는다
    s = _scaled[key][0]
    img.paste(s, (int(x), int(y)), s)


def make_stamp(s, col=RED, font=F32):
    w, h = tw(s, font) + 16, (40 if font is F32 else 22)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.fontmode = "1"
    dd.rectangle([0, 0, w - 1, h - 1], fill=(252, 236, 236, 255), outline=col + (255,), width=3)
    dd.text((8, 3 if font is F32 else 2), s, font=font, fill=col + (255,))
    return im.rotate(14, expand=True, resample=Image.NEAREST)


def draw_flames(d, x0, x1, ybot, t, seed, hmax=20):
    rng = random.Random(seed * 1000 + int(t * 15))
    for x in range(x0, x1, 2):
        h = 6 + rng.randint(0, hmax)
        for k in range(h):
            f = k / h
            col = RED if f < 0.35 else (ORANGE if f < 0.7 else YELLOW)
            d.rectangle([x, ybot - k, x + 1, ybot - k], fill=col)


def draw_stars(d, t, speed=20, col=WHITE, n=60, seed=7):
    rng = random.Random(seed)
    for _ in range(n):
        sx, sy, sp = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.3, 1.0)
        x = (sx - t * speed * sp) % W
        d.point((x, sy), fill=col if sp > 0.6 else GRAY)


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
        elif name == "chapter":
            self.notes(t, "G4:0.08 C5:0.08 E5:0.08 G5:0.3", vol=0.09, duty=0.25)
            self.notes(t, "C3:0.24 C3:0.3", kind="tri", vol=0.2)
            a(t + 0.24, drum("s"))
        elif name == "hook":
            a(t, tone("sq", 300, 0.3, 0.1, duty=0.125, f1=1200))
        elif name == "yank":
            a(t, tone("sin", 900, 0.45, 0.15, f1=120))
            a(t, noise(0.2, 0.15, 0.06, hold=3))
        elif name == "poof":
            a(t, noise(0.25, 0.25, 0.08, hold=2))
            a(t, tone("sq", 600, 0.2, 0.08, duty=0.25, f1=1500))
        elif name == "boo":
            a(t, tone("sq", 110, 0.5, 0.05, duty=0.5, f1=90))
            a(t, tone("sq", 116, 0.5, 0.04, duty=0.5, f1=92))

    def blips(self, t0, s, cps=24):
        for k, ch in enumerate(s):
            if ch != " " and k % 2 == 0:
                self.sfx(t0 + k / cps, "blip")


