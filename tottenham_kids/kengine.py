"""아동 애니메이션 엔진: skia 드로잉 헬퍼(둥글둥글·그라데이션), 자막, 효과, 악기·효과음 합성."""
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
TF_FALLBACK = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/fonts-japanese-gothic.ttf")

INK = (70, 44, 40)          # 부드러운 갈색 외곽선 (아동 애니 느낌)
WHITE = (255, 255, 255)
BLACK = (30, 26, 34)
NAVY = (19, 34, 87)
NAVY2 = (34, 52, 120)
RED = (232, 52, 60)
AIA = (214, 0, 28)
PINK = (255, 150, 170)
CHEEK = (255, 128, 140)
GOLD = (255, 200, 40)
YELLOW = (255, 232, 80)
ORANGE = (255, 150, 50)
SKY = (120, 200, 255)
SKY2 = (190, 232, 255)
GRASS = (110, 200, 90)
GRASS2 = (80, 170, 70)
PURPLE = (150, 90, 220)
GRAY = (150, 150, 160)
LGRAY = (220, 220, 228)


def C(c, a=255):
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(a))


def mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def darker(c, k=0.72):
    return tuple(int(v * k) for v in c)


def lighter(c, k=0.35):
    return mix(c, WHITE, k)


def fill(c, a=255):
    return skia.Paint(AntiAlias=True, Color=C(c, a))


def stroke(c, w, a=255):
    return skia.Paint(AntiAlias=True, Color=C(c, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def radial(c, cx, cy, r, hi=0.35, lo=0.12):
    """왼쪽 위가 밝고 가장자리가 살짝 어두운 입체감 그라데이션."""
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(
        skia.Point(cx - r * 0.35, cy - r * 0.4), r * 1.5,
        [C(lighter(c, hi)), C(c), C(darker(c, 1 - lo))], [0.0, 0.55, 1.0]))
    return p


def linear(c0, c1, x0, y0, x1, y1, a=255):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], [C(c0, a), C(c1, a)]))
    return p


def blob(cv, path, col, ow=4, oc=None, shade=True, a=255):
    """둥근 도형: 그라데이션 채우기 + 같은 계열의 진한 외곽선."""
    if col is not None:
        if shade:
            b = path.getBounds()
            r = max(b.width(), b.height()) / 2
            p = radial(col, b.centerX(), b.centerY(), r)
            p.setAlphaf(a / 255)
            cv.drawPath(path, p)
        else:
            cv.drawPath(path, fill(col, a))
    if ow:
        cv.drawPath(path, stroke(oc or darker(col if col else INK, 0.55), ow, a))


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


def arc(cv, cx, cy, rx, ry, a0, sweep, col, w):
    p = skia.Path()
    p.addArc(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry), a0, sweep)
    cv.drawPath(p, stroke(col, w))


def star_path(cx, cy, r, r2=None, n=5, rot=-90):
    r2 = r2 or r * 0.45
    pts = []
    for i in range(n * 2):
        a = math.radians(rot + i * 180 / n)
        rr = r if i % 2 == 0 else r2
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return poly(pts)


def heart_path(cx, cy, s):
    p = skia.Path()
    p.moveTo(cx, cy + s * 0.9)
    p.cubicTo(cx - s * 1.4, cy - s * 0.1, cx - s * 0.7, cy - s * 1.1, cx, cy - s * 0.45)
    p.cubicTo(cx + s * 0.7, cy - s * 1.1, cx + s * 1.4, cy - s * 0.1, cx, cy + s * 0.9)
    p.close()
    return p


def shadow(cv, cx, cy, rx, a=60):
    """부드럽게 번진 바닥 그림자."""
    p = fill((0, 0, 0), a)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(2.0, rx * 0.12)))
    cv.drawPath(oval(cx, cy, rx, rx * 0.24), p)


def glow(cv, path, col, sigma=18, a=150):
    """경로 둘레에 은은한 빛."""
    p = fill(col, a)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma))
    cv.drawPath(path, p)


def vignette(cv, a=70):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * 0.75,
                                               [C((0, 0, 0), 0), C((0, 0, 0), 0), C((20, 10, 30), a)],
                                               [0.0, 0.62, 1.0]))
    cv.drawRect(skia.Rect.MakeWH(W, H), p)


# ------------------------------------------------------------------- 움직임

def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def ease_out(k):
    k = max(0.0, min(1.0, k))
    return 1 - (1 - k) ** 3


def back_out(k, s=1.9):
    k = max(0.0, min(1.0, k)) - 1
    return k * k * ((s + 1) * k + s) + 1


def elastic(k):
    k = max(0.0, min(1.0, k))
    if k in (0, 1):
        return k
    return 2 ** (-10 * k) * math.sin((k - 0.075) * 2 * math.pi / 0.3) + 1


def pop(t, t0, d=0.35):
    """t0 부터 통통 튀며 나타나는 크기(0→1)."""
    if t < t0:
        return 0.0
    return back_out((t - t0) / d)


def bounce(t, f=2.0, h=1.0):
    return abs(math.sin(t * math.pi * f)) * h


# ------------------------------------------------------------------- 텍스트

def font(tf, size):
    f = skia.Font(tf, size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def runs(s, tf):
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


def text(cv, s, x, y, size, col=WHITE, tf=TF_KR, align="left", outline=None, ow=8, a=255, grad=None):
    """y 는 글자 기준선. outline 이 있으면 두꺼운 테두리(아동 애니 자막 스타일)."""
    w = text_w(s, size, tf)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    for layer in ("out", "in"):
        if layer == "out" and not outline:
            continue
        xx = x
        for part, f in runs(s, tf):
            ft = font(f, size)
            if layer == "out":
                p = stroke(outline, ow, a)
            elif grad:
                p = linear(grad[0], grad[1], 0, y - size * 0.85, 0, y, a)
            else:
                p = fill(col, a)
            cv.drawString(part, xx, y, ft, p)
            xx += ft.measureText(part)
    return w


# ------------------------------------------------------------------- 효과

def sparkle(cv, x, y, s, col=WHITE, a=255):
    p = skia.Path()
    p.moveTo(x, y - s)
    p.quadTo(x, y, x + s, y)
    p.quadTo(x, y, x, y + s)
    p.quadTo(x, y, x - s, y)
    p.quadTo(x, y, x, y - s)
    p.close()
    cv.drawPath(p, fill(col, a))


def sparkles(cv, t, cx, cy, rad, n=10, seed=1, cols=(WHITE, YELLOW, PINK)):
    rng = random.Random(seed)
    for i in range(n):
        ang = rng.uniform(0, 6.28)
        rr = rng.uniform(0.3, 1.0) * rad
        ph = rng.uniform(0, 6.28)
        k = (math.sin(t * 6 + ph) + 1) / 2
        sparkle(cv, cx + math.cos(ang) * rr, cy + math.sin(ang) * rr * 0.7, 6 + 12 * k, cols[i % len(cols)],
                int(120 + 135 * k))


def rays(cv, cx, cy, t, cols, n=16, speed=0.3):
    for i in range(n):
        a0 = (i / n) * 360 + t * speed * 60
        p = skia.Path()
        p.moveTo(cx, cy)
        p.arcTo(skia.Rect.MakeLTRB(cx - 2000, cy - 2000, cx + 2000, cy + 2000), a0, 360 / n, False)
        p.close()
        cv.drawPath(p, fill(cols[i % len(cols)]))


def sweat(cv, x, y, s=1.0):
    p = skia.Path()
    p.moveTo(x, y - 12 * s)
    p.cubicTo(x + 8 * s, y, x + 7 * s, y + 9 * s, x, y + 9 * s)
    p.cubicTo(x - 7 * s, y + 9 * s, x - 8 * s, y, x, y - 12 * s)
    cv.drawPath(p, fill((150, 210, 255)))
    cv.drawPath(p, stroke((60, 120, 200), 2.5))
    cv.drawPath(oval(x - 2 * s, y + 2 * s, 2 * s, 3 * s), fill(WHITE))


def cloud(cv, x, y, s=1.0, a=255, col=WHITE):
    p = skia.Path()
    for dx, dy, r in ((0, 0, 34), (38, -14, 42), (80, 0, 32), (40, 12, 34), (-30, 8, 24), (108, 10, 22)):
        p.addCircle(x + dx * s, y + dy * s, r * s)
    p.setFillType(skia.PathFillType.kWinding)
    cv.drawPath(p, fill(col, a))


def burst(cv, cx, cy, r, col, oc=None, n=12, seed=0, wobble=0.25):
    rng = random.Random(seed)
    pts = []
    for i in range(n * 2):
        a = i / (n * 2) * 2 * math.pi
        rr = r * (1 if i % 2 == 0 else 0.62) * (1 + rng.uniform(-wobble, wobble) * 0.4)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    pth = poly(pts)
    cv.drawPath(pth, fill(col))
    cv.drawPath(pth, stroke(oc or darker(col, 0.6), 5))


def confetti(cv, t, seed=3, n=60, t0=0.0, cols=(RED, YELLOW, SKY, PINK, GRASS, PURPLE)):
    rng = random.Random(seed)
    for i in range(n):
        x0 = rng.uniform(0, W)
        sp = rng.uniform(120, 260)
        ph = rng.uniform(0, 6.28)
        y = -30 + (t - t0) * sp + rng.uniform(-300, 0)
        if y < -20 or y > H + 20:
            continue
        x = x0 + math.sin(t * 3 + ph) * 30
        cv.save()
        cv.translate(x, y)
        cv.rotate((t * 200 + ph * 57) % 360)
        cv.drawRect(skia.Rect.MakeXYWH(-6, -3, 12, 6), fill(cols[i % len(cols)]))
        cv.restore()


def draw_rainbow(cv, cx, cy, r, w=22, a=255):
    cols = [(255, 90, 90), (255, 170, 60), (255, 230, 80), (110, 210, 110), (90, 170, 255), (160, 110, 230)]
    for i, c in enumerate(cols):
        rr = r - i * w
        p = skia.Path()
        p.addArc(skia.Rect.MakeLTRB(cx - rr, cy - rr, cx + rr, cy + rr), 180, 180)
        cv.drawPath(p, stroke(c, w + 1, a))


# ------------------------------------------------------------------- 소리 합성

def env_adsr(n, a=0.005, d=0.1, s=0.6, r=0.05):
    t = np.arange(n) / SR
    L = n / SR
    e = np.ones(n) * s
    e[t < a] = t[t < a] / a
    m = (t >= a) & (t < a + d)
    e[m] = 1 - (1 - s) * (t[m] - a) / d
    rel = t > L - r
    e[rel] *= np.clip((L - t[rel]) / r, 0, 1)
    return e


def hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def inst(kind, midi, dur, vel=1.0):
    """간단한 악기들: 실로폰, 토이피아노, 베이스, 벨, 스트링 패드, 휘슬(멜로디 리드)."""
    f = hz(midi)
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "xylo":
        y = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 3.98 * t) * np.exp(-t * 30)
        y *= np.exp(-t * 7)
    elif kind == "piano":
        y = sum(np.sin(2 * np.pi * f * k * t * (1 + 0.0007 * k)) / k ** 1.3 for k in range(1, 7))
        y *= np.exp(-t * 3.2) * (1 - np.exp(-t * 400))
        y *= env_adsr(n, 0.002, 0.05, 1.0, 0.05)
    elif kind == "bass":
        y = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
        y *= np.exp(-t * 4) * 0.8 + 0.2
        y *= env_adsr(n, 0.004, 0.05, 1.0, 0.04)
    elif kind == "bell":
        y = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) + 0.25 * np.sin(2 * np.pi * f * 5.4 * t)
        y *= np.exp(-t * 4)
    elif kind == "pad":
        y = sum(np.sin(2 * np.pi * f * k * t + k) / k for k in range(1, 5))
        y *= env_adsr(n, 0.08, 0.2, 0.8, 0.2)
    elif kind == "lead":  # 리코더/휘슬 같은 부드러운 멜로디
        vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t * 4, 0, 1)
        ph = 2 * np.pi * f * np.cumsum(vib) / SR
        y = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
        y *= env_adsr(n, 0.02, 0.1, 0.8, 0.06)
    elif kind == "brass":
        ph = 2 * np.pi * f * t
        y = sum(np.sin(k * ph) * (0.7 ** k) for k in range(1, 8))
        y *= env_adsr(n, 0.03, 0.1, 0.8, 0.08)
    else:
        raise ValueError(kind)
    return (y * vel).astype(np.float32)


def drum(kind, vel=1.0):
    rng = np.random.default_rng({"k": 1, "s": 2, "h": 3, "c": 4, "t": 5}.get(kind, 0))
    if kind == "k":
        n = int(0.28 * SR)
        t = np.arange(n) / SR
        f = 55 + 110 * np.exp(-t * 28)
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10)
    elif kind == "s":  # 손뼉+스네어
        n = int(0.22 * SR)
        t = np.arange(n) / SR
        nz = rng.standard_normal(n)
        y = nz * np.exp(-t * 22) * 0.7 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.4
    elif kind == "c":  # 박수
        n = int(0.2 * SR)
        t = np.arange(n) / SR
        nz = rng.standard_normal(n)
        e = sum(np.exp(-np.clip(t - d, 0, None) * 60) * (t >= d) for d in (0, 0.012, 0.024))
        y = nz * e * 0.5
        y = np.diff(y, prepend=0) * 2
    elif kind == "h":  # 쉐이커
        n = int(0.07 * SR)
        t = np.arange(n) / SR
        y = np.diff(rng.standard_normal(n), prepend=0) * np.exp(-t * 60) * 0.25
    elif kind == "t":  # 탬버린
        n = int(0.18 * SR)
        t = np.arange(n) / SR
        y = np.diff(rng.standard_normal(n), prepend=0) * np.exp(-t * 25) * 0.35
        y *= 1 + 0.5 * np.sin(2 * np.pi * 70 * t)
    else:
        raise ValueError(kind)
    return (y * vel).astype(np.float32)


class Mixer:
    def __init__(self, dur):
        self.buf = np.zeros(int((dur + 3) * SR), np.float32)

    def add(self, t, sig, vol=1.0):
        if sig is None or not len(sig):
            return
        i = int(round(t * SR))
        if i < 0:
            sig = sig[-i:]
            i = 0
        j = min(len(self.buf), i + len(sig))
        if j > i:
            self.buf[i:j] += sig[: j - i] * vol

    def sfx(self, t, name, vol=1.0):
        self.add(t, SFX(name), vol)


_SFX = {}


def SFX(name):
    if name in _SFX:
        return _SFX[name]
    rng = np.random.default_rng(abs(hash(name)) % 2 ** 32)

    def tone_sweep(f0, f1, d, kind="sine", decay=3.0):
        n = int(d * SR)
        t = np.arange(n) / SR
        f = f0 * (f1 / f0) ** (t / d)
        ph = 2 * np.pi * np.cumsum(f) / SR
        y = np.sin(ph) if kind == "sine" else np.sign(np.sin(ph)) * 0.5
        return y * np.exp(-t * decay) * env_adsr(n, 0.005, 0.01, 1, 0.03)

    def seq(notes, kind="xylo", step=0.09, dur=0.4, vel=0.8):
        out = np.zeros(int((step * len(notes) + dur) * SR), np.float32)
        for i, m in enumerate(notes):
            s = inst(kind, m, dur, vel)
            a = int(i * step * SR)
            out[a:a + len(s)] += s
        return out

    if name == "pop":
        y = tone_sweep(300, 900, 0.12, decay=18) * 0.8
    elif name == "boing":
        n = int(0.5 * SR)
        t = np.arange(n) / SR
        f = 180 + 140 * np.sin(2 * np.pi * 7 * t) * np.exp(-t * 3) + 120 * t
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5) * 0.8
    elif name == "twinkle":
        y = seq([84, 88, 91, 96, 100], "bell", 0.06, 0.6, 0.35)
    elif name == "ding":
        y = seq([84, 91], "bell", 0.12, 0.9, 0.5)
    elif name == "dingdong":
        y = seq([79, 76, 72], "xylo", 0.2, 0.7, 0.7)  # 딩동댕
    elif name == "buzzer":
        n = int(0.5 * SR)
        t = np.arange(n) / SR
        y = np.sign(np.sin(2 * np.pi * 110 * t)) * 0.25 * env_adsr(n, 0.01, 0.05, 1, 0.05)
    elif name == "whoosh":
        n = int(0.4 * SR)
        t = np.arange(n) / SR
        nz = rng.standard_normal(n)
        y = np.convolve(nz, np.ones(12) / 12, "same") * np.sin(np.pi * t / 0.4) * 0.6
    elif name == "slide_up":
        y = tone_sweep(300, 1400, 0.35, decay=1.5) * 0.4
    elif name == "slide_down":
        y = tone_sweep(900, 150, 0.7, decay=1.0) * 0.45
    elif name == "sad_trombone":
        out = []
        for i, m in enumerate([55, 54, 53, 52]):
            d = 0.36 if i < 3 else 0.9
            s = inst("brass", m, d, 0.5)
            if i == 3:
                tt = np.arange(len(s)) / SR
                s = s * (1 + 0.3 * np.sin(2 * np.pi * 6 * tt))
            out.append(s)
        y = np.concatenate(out)
    elif name == "fanfare":
        y = seq([67, 72, 76, 79], "brass", 0.12, 0.35, 0.5)
        tail = inst("brass", 84, 0.9, 0.5)
        y = np.concatenate([y[: int(0.36 * SR)], tail])
    elif name == "henshin":
        out = np.zeros(int(2.4 * SR), np.float32)
        for i, m in enumerate(range(60, 96, 2)):
            s = inst("bell", m, 0.3, 0.25)
            a = int(i * 0.07 * SR)
            out[a:a + len(s)] += s
        sw = tone_sweep(200, 2000, 1.4, decay=0.3) * 0.15
        out[: len(sw)] += sw
        ch = sum(inst("brass", m, 1.0, 0.35) for m in (72, 76, 79))
        a = int(1.35 * SR)
        out[a:a + len(ch)] += ch
        y = out
    elif name == "buzz":  # 벌
        n = int(0.8 * SR)
        t = np.arange(n) / SR
        f = 210 + 20 * np.sin(2 * np.pi * 9 * t)
        ph = 2 * np.pi * np.cumsum(f) / SR
        y = (np.sign(np.sin(ph)) * 0.3 + np.sin(2 * ph) * 0.2) * env_adsr(n, 0.05, 0.1, 1, 0.2) * 0.5
    elif name == "kick_ball":
        y = drum("k", 0.8) + np.concatenate([tone_sweep(600, 300, 0.06, decay=30) * 0.3,
                                             np.zeros(len(drum("k")) - int(0.06 * SR))])[: len(drum("k"))]
    elif name == "goal_net":
        n = int(0.6 * SR)
        t = np.arange(n) / SR
        y = np.convolve(rng.standard_normal(n), np.ones(30) / 30, "same") * np.exp(-t * 6) * 1.5
    elif name == "crowd_boo":
        n = int(1.6 * SR)
        t = np.arange(n) / SR
        y = np.zeros(n)
        for k in range(8):
            f0 = rng.uniform(110, 190)
            y += np.sin(2 * np.pi * f0 * t * (1 - 0.05 * t)) * 0.12
        y *= env_adsr(n, 0.2, 0.2, 0.8, 0.5)
        y += np.convolve(rng.standard_normal(n), np.ones(40) / 40, "same") * 0.4 * env_adsr(n, 0.2, 0.2, 0.8, 0.5)
    elif name == "cheer":
        n = int(1.4 * SR)
        t = np.arange(n) / SR
        nz = np.convolve(rng.standard_normal(n), np.ones(6) / 6, "same")
        y = nz * env_adsr(n, 0.1, 0.3, 0.7, 0.6) * 0.5
    elif name == "clap_many":
        y = np.zeros(int(1.5 * SR), np.float32)
        for k in range(40):
            s = drum("c", rng.uniform(0.3, 0.7))
            a = int(rng.uniform(0, 1.2) * SR)
            y[a:a + len(s)] += s
    elif name == "ring":
        out = []
        for _ in range(2):
            n = int(0.5 * SR)
            t = np.arange(n) / SR
            out.append((np.sin(2 * np.pi * 880 * t) + np.sin(2 * np.pi * 1100 * t)) * 0.15 *
                       (np.sin(2 * np.pi * 20 * t) > 0) * env_adsr(n, 0.01, 0.01, 1, 0.02))
            out.append(np.zeros(int(0.25 * SR)))
        y = np.concatenate(out)
    elif name == "gulp":
        y = np.concatenate([tone_sweep(500, 160, 0.14, decay=10), tone_sweep(300, 90, 0.2, decay=10)]) * 0.6
    elif name == "thunder":
        n = int(1.4 * SR)
        t = np.arange(n) / SR
        y = np.convolve(rng.standard_normal(n), np.ones(80) / 80, "same") * np.exp(-t * 2.5) * 4
    elif name == "bus_horn":
        y = (inst("brass", 64, 0.25, 0.4) + inst("brass", 68, 0.25, 0.4))
        y = np.concatenate([y, np.zeros(int(0.06 * SR)), y])
    elif name == "plane":
        n = int(1.5 * SR)
        t = np.arange(n) / SR
        y = np.convolve(rng.standard_normal(n), np.ones(20) / 20, "same") * 0.4 * np.sin(np.pi * t / 1.5)
    elif name == "tick":
        y = tone_sweep(1800, 1700, 0.03, decay=80) * 0.4
    elif name == "fall":
        y = tone_sweep(1200, 200, 0.8, decay=0.5) * 0.35
    elif name == "thud":
        y = drum("k", 1.0)
    elif name == "snore":
        n = int(1.0 * SR)
        t = np.arange(n) / SR
        y = np.convolve(rng.standard_normal(n), np.ones(50) / 50, "same") * np.sin(np.pi * t) * 1.2
    elif name == "roar":
        n = int(0.9 * SR)
        t = np.arange(n) / SR
        f = 90 + 40 * np.sin(2 * np.pi * 3 * t)
        y = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.2 + np.convolve(
            rng.standard_normal(n), np.ones(10) / 10, "same") * 0.3
        y *= env_adsr(n, 0.05, 0.1, 1, 0.3)
    elif name == "caw":
        y = np.concatenate([tone_sweep(900, 600, 0.15, "sq", decay=5), np.zeros(int(0.05 * SR)),
                            tone_sweep(900, 600, 0.15, "sq", decay=5)]) * 0.4
    elif name == "coins":
        y = seq([88, 93, 88, 93, 96], "bell", 0.05, 0.4, 0.3)
    elif name == "chime_lesson":
        y = seq([72, 76, 79, 84], "bell", 0.16, 1.2, 0.45)
    else:
        raise KeyError(name)
    y = np.asarray(y, np.float32)
    _SFX[name] = y
    return y
