"""카툰 엔진: skia 벡터 드로잉 헬퍼, 텍스트/말풍선, 만화 효과, 효과음·음악 합성."""
import math
import os
import random

import numpy as np
import skia

W, H = 1280, 720
FPS = 24
SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))

TF_KR = skia.Typeface.MakeFromFile(os.path.join(HERE, "fonts", "Jua-Regular.ttf"))
TF_TITLE = skia.Typeface.MakeFromFile(os.path.join(HERE, "fonts", "BlackHanSans-Regular.ttf"))
TF_COMIC = skia.Typeface.MakeFromFile(os.path.join(HERE, "fonts", "Bangers-Regular.ttf"))

INK = (28, 20, 30)
WHITE = (255, 255, 255)
NAVY = (19, 34, 87)
BINARY = (26, 32, 68)
RED = (226, 38, 46)
AIA = (214, 0, 28)
GOLD = (255, 196, 30)
YELLOW = (255, 226, 60)
SKY = (120, 196, 255)
GRASS = (70, 170, 70)


def C(c, a=255):
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(a))


def mix(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def fill(c, a=255):
    return skia.Paint(AntiAlias=True, Color=C(c, a))


def stroke(c, w, a=255):
    return skia.Paint(AntiAlias=True, Color=C(c, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def shape(cv, path, col, ow=5, oc=INK, a=255):
    if col is not None:
        cv.drawPath(path, fill(col, a))
    if ow:
        cv.drawPath(path, stroke(oc, ow, a))


def oval(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def rrect(x0, y0, x1, y1, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r))
    return p


def poly(pts, closed=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if closed:
        p.close()
    return p


def smooth(pts, closed=True, tension=1.0):
    """Catmull-Rom 스플라인 → 3차 베지어 경로."""
    p = skia.Path()
    n = len(pts)
    p.moveTo(*pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension, p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension, p2[1] - (p3[1] - p1[1]) / 6 * tension)
        p.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        p.close()
    return p


def hose(cv, p0, p1, bend, col, w, ow=5):
    """고무호스 팔/다리: p0→p1, bend 만큼 휜 곡선."""
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy) or 1
    cx, cy = mx - dy / ln * bend, my + dx / ln * bend
    p = skia.Path()
    p.moveTo(*p0)
    p.quadTo(cx, cy, *p1)
    cv.drawPath(p, stroke(INK, w + ow * 2))
    cv.drawPath(p, stroke(col, w))
    return p


# ------------------------------------------------------------------- 텍스트

TF_FALLBACK = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/fonts-japanese-gothic.ttf")


def font(tf, size):
    f = skia.Font(tf, size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def runs(s, tf):
    """글리프가 없는 글자는 다른 폰트로 넘겨 (문자열, 폰트) 구간으로 나눈다."""
    chain = [tf] + [f for f in (TF_TITLE, TF_KR, TF_FALLBACK) if f is not tf]
    out = []
    for ch in s:
        use = tf
        if ch != " ":
            for f in chain:
                if f.unicharToGlyph(ord(ch)):
                    use = f
                    break
        if out and out[-1][1] is use:
            out[-1][0] += ch
        else:
            out.append([ch, use])
    return out


def text_w(s, size, tf=TF_KR):
    return sum(font(f, size).measureText(part) for part, f in runs(s, tf))


def text(cv, s, x, y, size=40, col=WHITE, tf=TF_KR, align="center", oc=INK, ow=None, a=255):
    parts = [(part, font(f, size)) for part, f in runs(s, tf)]
    w = sum(fo.measureText(part) for part, fo in parts)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if oc is not None:
        xx = x
        sp = stroke(oc, ow if ow is not None else max(4, size * 0.16), a)
        for part, fo in parts:
            cv.drawString(part, xx, y, fo, sp)
            xx += fo.measureText(part)
    xx = x
    fp = fill(col, a)
    for part, fo in parts:
        cv.drawString(part, xx, y, fo, fp)
        xx += fo.measureText(part)
    return w


def bubble(cv, x, y, lines, size=34, tail=None, col=WHITE, tcol=INK, shout=False, pad=18, t=0.0):
    """말풍선. (x, y)는 풍선 중심. tail=(tx, ty) 꼬리 끝."""
    w = max(text_w(s, size) for s in lines) + pad * 2
    h = len(lines) * size * 1.2 + pad * 1.4
    x0, y0 = x - w / 2, y - h / 2
    if shout:
        pts = []
        n = 22
        for i in range(n):
            ang = i / n * math.tau
            r = 1.0 + (0.18 if i % 2 else 0)
            pts.append((x + math.cos(ang) * (w / 2 + 16) * r, y + math.sin(ang) * (h / 2 + 16) * r))
        body = poly(pts)
    else:
        body = rrect(x0, y0, x0 + w, y0 + h, min(h / 2, 34))
    if tail:
        tx, ty = tail
        bx = max(x0 + 30, min(x0 + w - 30, tx))
        by = y0 + h if ty > y else y0
        tp = poly([(bx - 16, by), (tx, ty), (bx + 16, by)])
        shape(cv, tp, col, 5)
    shape(cv, body, col, 5)
    if tail:
        cv.drawPath(poly([(bx - 13, by + (-3 if ty > y else 3)), (bx + 13, by + (-3 if ty > y else 3)),
                          (bx, by + (8 if ty > y else -8))]), fill(col))
    for i, s in enumerate(lines):
        text(cv, s, x, y0 + pad * 0.7 + size * (i + 0.95) * 1.2 - size * 0.18, size, tcol, oc=None)


def caption(cv, s, y=680, size=34, col=WHITE, bg=(20, 22, 40), a=230, sub=None):
    """하단 자막 바."""
    w = text_w(s, size) + 60
    cv.drawPath(rrect(W / 2 - w / 2, y - size - 6, W / 2 + w / 2, y + 14, 18), fill(bg, a))
    text(cv, s, W / 2, y, size, col, oc=None)
    if sub:
        text(cv, sub, W / 2, y + 40, 26, (220, 220, 230), oc=INK, ow=4)


def tag(cv, s, x, y, size=28, col=YELLOW, tcol=INK, rot=0):
    """삐뚤어진 노란 딱지 라벨."""
    cv.save()
    cv.translate(x, y)
    cv.rotate(rot)
    w = text_w(s, size) + 26
    shape(cv, rrect(-w / 2, -size * 0.75, w / 2, size * 0.55, 8), col, 4)
    text(cv, s, 0, size * 0.28, size, tcol, oc=None)
    cv.restore()


# ------------------------------------------------------------------- 효과

def burst(cv, cx, cy, r1, r2, n=14, col=YELLOW, rot=0.0, ow=5):
    pts = []
    for i in range(n * 2):
        ang = rot + i / (n * 2) * math.tau
        r = r2 if i % 2 == 0 else r1
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    shape(cv, poly(pts), col, ow)


def pow_text(cv, s, x, y, k=1.0, col=YELLOW, bcol=RED, size=90, rot=-8):
    """POW! 같은 효과 텍스트 (k: 0→1 팝업 진행도)."""
    if k <= 0:
        return
    sc = 1.35 - 0.35 * min(1, k * 3) if k < 0.33 else 1.0
    sc *= min(1.0, k * 4)
    cv.save()
    cv.translate(x, y)
    cv.rotate(rot)
    cv.scale(sc, sc)
    w = text_w(s, size, TF_COMIC)
    burst(cv, 0, -size * 0.3, w * 0.42, w * 0.62, 12, bcol)
    text(cv, s, 0, 0, size, col, TF_COMIC, ow=10)
    cv.restore()


def speed_lines(cv, cx, cy, t, n=40, r0=260, col=WHITE, a=200):
    rng = random.Random(int(t * 12))
    for _ in range(n):
        ang = rng.uniform(0, math.tau)
        r1 = r0 + rng.uniform(0, 80)
        r2 = r1 + rng.uniform(200, 700)
        p = poly([(cx + math.cos(ang) * r1, cy + math.sin(ang) * r1),
                  (cx + math.cos(ang + 0.012) * r2, cy + math.sin(ang + 0.012) * r2),
                  (cx + math.cos(ang - 0.012) * r2, cy + math.sin(ang - 0.012) * r2)])
        cv.drawPath(p, fill(col, a))


def motion_lines(cv, x, y, h, dirx=-1, n=5, length=120, col=INK, a=200):
    for i in range(n):
        yy = y - h / 2 + h * (i + 0.5) / n
        ln = length * (0.6 + 0.4 * ((i * 37) % 10) / 10)
        cv.drawLine(x, yy, x + dirx * ln, yy, stroke(col, 5, a))


def dust(cv, x, y, k, n=6, col=(230, 220, 200)):
    """먼지 구름 (k: 0→1)."""
    if not 0 <= k <= 1:
        return
    a = int(255 * (1 - k))
    for i in range(n):
        ang = math.pi + i / (n - 1) * math.pi
        r = 20 + 40 * k
        cx = x + math.cos(ang) * (30 + 90 * k)
        cy = y + math.sin(ang) * 20 * k - 10
        shape(cv, oval(cx, cy, r, r * 0.8), col, 4, a=a)


def stars_circle(cv, x, y, t, rx=70, ry=18, n=4):
    """머리 위 빙글빙글 별 (어지러움)."""
    for i in range(n):
        ang = t * 6 + i / n * math.tau
        sx, sy = x + math.cos(ang) * rx, y + math.sin(ang) * ry
        burst(cv, sx, sy, 7, 16, 5, YELLOW, ow=3)


def sweat(cv, x, y, s=1.0, a=255):
    p = skia.Path()
    p.moveTo(x, y - 18 * s)
    p.cubicTo(x + 14 * s, y, x + 10 * s, y + 14 * s, x, y + 14 * s)
    p.cubicTo(x - 10 * s, y + 14 * s, x - 14 * s, y, x, y - 18 * s)
    shape(cv, p, (140, 210, 255), 3, a=a)


def confetti(cv, t, seed=1, n=80, cols=((226, 38, 46), (255, 196, 30), (60, 140, 255), (80, 200, 90), WHITE),
             up=False):
    rng = random.Random(seed)
    for _ in range(n):
        x0, sp, ph = rng.uniform(0, W), rng.uniform(120, 260), rng.uniform(0, 10)
        c = rng.choice(cols)
        y = (rng.uniform(-H, 0) + t * sp) % (H + 60) - 30
        if up:
            y = H - y
        x = x0 + math.sin(t * 3 + ph) * 30
        cv.save()
        cv.translate(x, y)
        cv.rotate((t * 200 + ph * 50) % 360)
        cv.drawRect(skia.Rect.MakeLTRB(-6, -3, 6, 3), fill(c))
        cv.restore()


def rings_bg(cv, t, c1=NAVY, c2=(240, 240, 250), cx=W / 2, cy=H / 2):
    """루니툰즈풍 동심원 배경."""
    cv.drawRect(skia.Rect.MakeWH(W, H), fill(c1))
    step = 70
    off = (t * 120) % (step * 2)
    r = 1600 + off
    i = 0
    while r > 0:
        cv.drawCircle(cx, cy, r, fill(c1 if i % 2 else c2))
        r -= step
        i += 1


def iris(cv, cx, cy, r):
    """아이리스 아웃: 원 바깥을 검게."""
    p = skia.Path()
    p.addRect(skia.Rect.MakeWH(W, H))
    p.addCircle(cx, cy, max(0, r))
    p.setFillType(skia.PathFillType.kEvenOdd)
    cv.drawPath(p, fill((0, 0, 0)))


def vhs(cv, t, a=90):
    rng = random.Random(int(t * 24))
    for _ in range(6):
        y = rng.uniform(0, H)
        cv.drawRect(skia.Rect.MakeLTRB(0, y, W, y + rng.uniform(2, 10)), fill(WHITE, rng.randint(20, a)))


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def ease_out_back(k, s=1.7):
    k = max(0.0, min(1.0, k)) - 1
    return k * k * ((s + 1) * k + s) + 1


def bounce(k):
    """0→1 착지 후 통통 튀는 값(1에서 끝남)."""
    k = max(0.0, min(1.0, k))
    if k < 0.5:
        return (k / 0.5) ** 2
    k2 = (k - 0.5) / 0.5
    return 1 - 0.18 * math.sin(k2 * math.pi) * (1 - k2)


def squash(t0, t, amt=0.25, dur=0.35):
    """착지 스쿼시&스트레치: (sx, sy)."""
    k = t - t0
    if k < 0 or k > dur:
        return 1.0, 1.0
    v = math.sin(k / dur * math.pi * 2) * math.exp(-k / dur * 3) * amt
    return 1 + v, 1 - v


# ------------------------------------------------------------------- 오디오

_NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def freq(n):
    i, acc = 1, 0
    if n[1] in "#b":
        acc = 1 if n[1] == "#" else -1
        i = 2
    return 440.0 * 2 ** ((12 * (int(n[i:]) + 1) + _NOTE[n[0]] + acc - 69) / 12)


_nrng = np.random.default_rng(2627)


def osc(kind, f, n, duty=0.5, vib=0.0, vibf=5.5):
    tt = np.arange(n) / SR
    if vib:
        fr = f * (1 + vib * np.sin(2 * np.pi * vibf * tt))
    else:
        fr = np.full(n, f) if np.isscalar(f) else f
    ph = np.cumsum(fr) / SR % 1.0
    if kind == "sq":
        return np.where(ph < duty, 1.0, -1.0)
    if kind == "tri":
        return 4 * np.abs(ph - 0.5) - 1
    if kind == "saw":
        return 2 * ph - 1
    return np.sin(2 * np.pi * ph)


def env(n, a=0.005, d=None, r=0.02):
    e = np.ones(n)
    ai = min(n, int(a * SR))
    if ai:
        e[:ai] = np.linspace(0, 1, ai)
    if d:
        e *= np.exp(-np.arange(n) / SR / d)
    ri = min(n, int(r * SR))
    if ri:
        e[n - ri:] *= np.linspace(1, 0, ri)
    return e


def tone(kind, f0, dur, vol=0.2, f1=None, duty=0.5, vib=0.0, a=0.005, d=None, r=0.02, vibf=5.5):
    n = max(1, int(dur * SR))
    f = f0 if f1 is None else np.geomspace(f0, f1, n)
    return osc(kind, f, n, duty, vib, vibf) * env(n, a, d, r) * vol


def noise(dur, vol=0.2, d=0.08, smooth=1):
    n = max(1, int(dur * SR))
    w = _nrng.uniform(-1, 1, n)
    if smooth > 1:
        w = np.convolve(w, np.ones(smooth) / smooth, mode="same") * math.sqrt(smooth)
    return w * env(n, 0.002, d, 0.01) * vol


INSTR = {
    # 이름: (파형, duty, 감쇠, 비브라토, 볼륨배수)
    "piano": ("tri", 0.5, 0.35, 0.0, 1.0),
    "pluck": ("sq", 0.25, 0.18, 0.0, 0.5),
    "clar": ("sq", 0.3, None, 0.006, 0.45),
    "tuba": ("sq", 0.35, 0.5, 0.0, 0.7),
    "xylo": ("sin", 0.5, 0.12, 0.0, 1.0),
    "bass": ("tri", 0.5, 0.6, 0.0, 1.4),
    "organ": ("sin", 0.5, None, 0.004, 0.8),
    "brass": ("saw", 0.5, None, 0.004, 0.35),
}


class Mixer:
    def __init__(self, dur):
        self.buf = np.zeros(int(dur * SR) + SR * 2)

    def add(self, t, sig):
        i = int(t * SR)
        if i < 0 or i >= len(self.buf):
            return
        n = min(len(sig), len(self.buf) - i)
        self.buf[i:i + n] += sig[:n]

    def drum(self, t, k, vol=1.0):
        if k == "k":
            self.add(t, tone("sin", 150, 0.16, 0.55 * vol, f1=45, d=0.07))
        elif k == "s":
            self.add(t, noise(0.14, 0.3 * vol, 0.05))
            self.add(t, tone("tri", 200, 0.07, 0.15 * vol, d=0.03))
        elif k == "h":
            self.add(t, noise(0.03, 0.07 * vol, 0.012))
        elif k == "b":  # 브러시
            self.add(t, noise(0.12, 0.06 * vol, 0.06, smooth=3))
        elif k == "w":  # 우드블록
            self.add(t, tone("sin", 900, 0.06, 0.25 * vol, d=0.02))

    def seq(self, t0, dur, pattern, bpm, spb=2, inst="piano", vol=0.1, transpose=0, gate=0.92):
        toks = pattern.split()
        step = 60.0 / bpm / spb
        ev, i = [], 0
        while i < len(toks):
            n = 1
            while i + n < len(toks) and toks[i + n] == "-":
                n += 1
            if toks[i] not in (".", "-"):
                ev.append((i, n, toks[i]))
            i += n
        loop = len(toks) * step
        base = 0.0
        while base < dur - 1e-6:
            for si, n, tk in ev:
                st = base + si * step
                if st >= dur:
                    break
                if inst == "drum":
                    self.drum(t0 + st, tk)
                    continue
                kind, duty, dec, vib, vm = INSTR[inst]
                ln = min(n * step * gate, dur - st)
                for nt in tk.split("+"):
                    f = freq(nt) * 2 ** (transpose / 12)
                    self.add(t0 + st, tone(kind, f, ln, vol * vm, duty=duty, vib=vib, d=dec))
            base += loop

    def sfx(self, t, name, vol=1.0):
        a = lambda tt, s: self.add(tt, s * vol)
        if name == "boing":
            n = int(0.5 * SR)
            tt = np.arange(n) / SR
            f = 220 * (1 + 0.5 * np.sin(2 * np.pi * 14 * tt) * np.exp(-tt * 5)) * (1 + tt)
            a(t, osc("sin", f, n) * env(n, 0.002, 0.25) * 0.35)
        elif name == "slide_up":
            a(t, tone("sin", 300, 0.45, 0.22, f1=1600, vib=0.02))
        elif name == "slide_down":
            a(t, tone("sin", 1600, 0.9, 0.22, f1=200, vib=0.02))
        elif name == "fall_long":
            a(t, tone("sin", 1800, 1.6, 0.18, f1=250, vib=0.01))
        elif name == "bonk":
            a(t, tone("sin", 700, 0.12, 0.4, f1=500, d=0.04))
            a(t, noise(0.05, 0.2, 0.02))
        elif name == "pow":
            a(t, noise(0.35, 0.45, 0.12, smooth=2))
            a(t, tone("sin", 120, 0.3, 0.5, f1=40, d=0.1))
        elif name == "whoosh":
            a(t, noise(0.35, 0.25, None, smooth=8) * np.hanning(int(0.35 * SR)))
        elif name == "zip":
            a(t, tone("sq", 400, 0.18, 0.08, f1=2400, duty=0.2))
        elif name == "kaching":
            a(t, tone("sin", 2637, 0.5, 0.18, d=0.2))
            a(t, tone("sin", 3520, 0.5, 0.12, d=0.25))
            a(t + 0.02, noise(0.08, 0.12, 0.03))
        elif name == "ding":
            a(t, tone("sin", 1318, 1.2, 0.25, d=0.5))
            a(t, tone("sin", 2637, 0.8, 0.08, d=0.3))
        elif name == "elev_ding":
            a(t, tone("sin", 1046, 0.9, 0.22, d=0.4))
            a(t + 0.25, tone("sin", 784, 1.0, 0.22, d=0.45))
        elif name == "scratch":
            n = int(0.5 * SR)
            tt = np.arange(n) / SR
            f = 300 + 900 * np.abs(np.sin(2 * np.pi * 4 * tt))
            a(t, (osc("saw", f, n) * 0.3 + _nrng.uniform(-1, 1, n) * 0.4) * env(n, 0.002, 0.3) * 0.35)
        elif name == "rewind":
            a(t, tone("saw", 200, 1.0, 0.1, f1=1400, vib=0.1))
            a(t, noise(1.0, 0.08, None, smooth=4))
        elif name == "trapdoor":
            a(t, tone("sq", 180, 0.12, 0.2, d=0.05))
            a(t + 0.05, noise(0.1, 0.2, 0.04))
        elif name == "stamp":
            a(t, noise(0.2, 0.4, 0.05, smooth=3))
            a(t, tone("sin", 90, 0.2, 0.45, f1=50, d=0.08))
        elif name == "sizzle":
            a(t, noise(1.2, 0.12, 0.6, smooth=1))
        elif name == "yelp":
            a(t, tone("sq", 500, 0.35, 0.12, f1=1500, duty=0.3, vib=0.05))
        elif name == "buzz":
            a(t, tone("saw", 180, 1.6, 0.08, vib=0.03, vibf=30))
            a(t, tone("saw", 240, 1.6, 0.06, vib=0.04, vibf=23))
        elif name == "caw":
            for k in range(2):
                a(t + k * 0.3, tone("saw", 900, 0.2, 0.12, f1=600, vib=0.05, vibf=40))
        elif name == "roar":
            a(t, noise(1.0, 0.35, 0.5, smooth=12))
            a(t, tone("saw", 90, 1.0, 0.2, f1=70, vib=0.1, vibf=12, d=0.6))
        elif name == "snore":
            for k in range(2):
                a(t + k * 1.1, noise(0.6, 0.12, None, smooth=30) * np.hanning(int(0.6 * SR)))
                a(t + k * 1.1 + 0.65, tone("sin", 900, 0.3, 0.05, f1=1300))
        elif name == "whistle":
            a(t, tone("sin", 2900, 0.25, 0.14, vib=0.04, vibf=30))
            a(t + 0.32, tone("sin", 2900, 0.7, 0.14, vib=0.04, vibf=30))
        elif name == "cheer":
            n = int(2.2 * SR)
            sig = noise(2.2, 0.35, None, smooth=6) * np.concatenate([np.linspace(0, 1, n // 5), np.linspace(1, 0, n - n // 5)])
            a(t, sig)
        elif name == "boo":
            a(t, tone("saw", 130, 1.2, 0.1, f1=110, vib=0.03))
            a(t, tone("saw", 139, 1.2, 0.08, f1=112, vib=0.04))
            a(t, noise(1.2, 0.1, None, smooth=20))
        elif name == "gulp":
            a(t, tone("sin", 180, 0.12, 0.4, f1=90))
            a(t + 0.18, tone("sin", 150, 0.14, 0.4, f1=70))
        elif name == "sad_trombone":
            for k, n in enumerate(["G3", "F#3", "F3"]):
                a(t + k * 0.4, tone("saw", freq(n), 0.38, 0.12, vib=0.01, d=0.6))
            a(t + 1.2, tone("saw", freq("E3"), 1.2, 0.12, vib=0.05, vibf=6))
        elif name == "fanfare":
            for k, n in enumerate(["C5", "E5", "G5"]):
                a(t + k * 0.12, tone("saw", freq(n), 0.12, 0.1, vib=0.004))
            a(t + 0.36, tone("saw", freq("C6"), 0.7, 0.12, vib=0.01))
            a(t + 0.36, tone("saw", freq("E5"), 0.7, 0.08, vib=0.01))
        elif name == "party_horn":
            a(t, tone("sq", 400, 0.6, 0.1, duty=0.4, vib=0.08, vibf=18))
            a(t + 0.6, tone("sq", 300, 0.5, 0.07, f1=150, duty=0.4))
        elif name == "pop":
            a(t, tone("sin", 600, 0.08, 0.35, f1=1400, d=0.03))
        elif name == "thud":
            a(t, tone("sin", 90, 0.3, 0.6, f1=40, d=0.1))
            a(t, noise(0.15, 0.2, 0.05, smooth=6))
        elif name == "hook":
            a(t, tone("sq", 1200, 0.3, 0.08, f1=200, duty=0.15))
            a(t + 0.25, noise(0.3, 0.25, 0.1, smooth=4))
        elif name == "plane":
            a(t, noise(2.0, 0.12, None, smooth=40) * np.linspace(1, 0, int(2.0 * SR)))
        elif name == "tick":
            a(t, tone("sin", 1500, 0.03, 0.2, d=0.01))
        elif name == "blip":
            a(t, tone("sq", 900, 0.04, 0.04, duty=0.3))
        elif name == "twinkle":
            for k, n in enumerate(["E6", "G6", "C7"]):
                a(t + k * 0.07, tone("sin", freq(n), 0.25, 0.12, d=0.1))
        elif name == "zoom":
            a(t, tone("saw", 150, 0.3, 0.1, f1=900, vib=0.02) * np.linspace(1, 0.2, int(0.3 * SR)))
        elif name == "crash":
            a(t, noise(0.8, 0.45, 0.3, smooth=1))
            a(t, tone("sin", 70, 0.4, 0.4, d=0.15))
        elif name == "gasp":
            a(t, noise(0.4, 0.15, None, smooth=10) * np.linspace(0, 1, int(0.4 * SR)))
