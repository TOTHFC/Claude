"""「숫자로 보는 맨체스터 시티」 ─ 2026년 9월 26일 기준 맨시티 현황 인포그래픽 영상.

    python3 make_assets.py      # (일레븐랩스 키 필요) 내레이션·효과음·배경음악 ─ 이미 있으면 건너뜀
    python3 make_info.py        # -> mancity_info.mp4
    python3 make_info.py --preview DIR
"""
import math
import os
import subprocess
import sys
import wave

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tottenham_kids"))
import voice as V  # noqa: E402

from narration import LINES, NARRATOR  # noqa: E402

V.CACHE = os.path.join(HERE, "voice_cache")
OUT = os.path.join(HERE, "mancity_info.mp4")
W, H, FPS, SR = 1920, 1080, 30, 44100

# ------------------------------------------------------------------ 색 (dataviz 기준 팔레트, 어두운 남색 바탕에서 검증)
BG1, BG2 = (11, 21, 48), (19, 38, 82)
CARD, CARD_LINE = (22, 38, 74), (38, 57, 106)
TEXT, TEXT2, MUTED = (255, 255, 255), (185, 198, 224), (124, 139, 176)
SKY = (108, 171, 221)            # 구단 상징색(제목·강조용, 데이터 색으로는 쓰지 않음)
BLUE, RED = (57, 135, 229), (230, 103, 103)   # 들어옴 / 나감
GOOD, CRIT = (12, 163, 12), (208, 59, 59)     # 승 / 패 (항상 글자와 함께)
CATS = [(57, 135, 229), (217, 89, 38), (25, 158, 112), (201, 133, 0), (213, 81, 129)]
GOLD = (227, 179, 65)


def C(c, a=255):
    return skia.Color(int(c[0]), int(c[1]), int(c[2]), int(max(0, min(255, a))))


def fill(c, a=255):
    return skia.Paint(AntiAlias=True, Color=C(c, a))


def stroke(c, w, a=255):
    return skia.Paint(AntiAlias=True, Color=C(c, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeCap=skia.Paint.kRound_Cap)


FONTS = {w: skia.Typeface.MakeFromFile(os.path.join(HERE, "fonts", f"Pretendard-{w}.otf"))
         for w in ("Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black")}


def font(size, weight="Bold"):
    f = skia.Font(FONTS[weight], size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def tw(s, size, weight="Bold"):
    return font(size, weight).measureText(s)


def text(cv, s, x, y, size, col=TEXT, weight="Bold", align="left", a=255):
    w = tw(s, size, weight)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    cv.drawString(s, x, y, font(size, weight), fill(col, a))
    return w


def rrect(x0, y0, x1, y1, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r))
    return p


def card(cv, x0, y0, x1, y1, a=255, col=CARD, line=CARD_LINE, r=22):
    sh = fill((0, 0, 0), int(70 * a / 255))
    sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
    cv.drawPath(rrect(x0, y0 + 8, x1, y1 + 8, r), sh)
    cv.drawPath(rrect(x0, y0, x1, y1, r), fill(col, a))
    cv.drawPath(rrect(x0, y0, x1, y1, r), stroke(line, 2, a))


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def ease_out(k):
    k = max(0.0, min(1.0, k))
    return 1 - (1 - k) ** 3


def back_out(k, s=1.6):
    k = max(0.0, min(1.0, k)) - 1
    return k * k * ((s + 1) * k + s) + 1


def appear(t, t0, d=0.45):
    return ease_out((t - t0) / d)


def bar_h(cv, x, y, w, h, col, a=255, right=True):
    """가로 막대: 기준선 쪽은 각지고 끝만 4px 둥글게."""
    if w <= 0.5:
        return
    r = min(4, w / 2, h / 2)
    p = skia.Path()
    if right:
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x, y, x + w, y + h), r, r))
        cv.drawPath(p, fill(col, a))
        cv.drawRect(skia.Rect.MakeLTRB(x, y, x + min(w, r + 1), y + h), fill(col, a))
    else:
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - w, y, x, y + h), r, r))
        cv.drawPath(p, fill(col, a))
        cv.drawRect(skia.Rect.MakeLTRB(x - min(w, r + 1), y, x, y + h), fill(col, a))


def background(cv, t):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(W, H)], [C(BG1), C(BG2)]))
    cv.drawRect(skia.Rect.MakeWH(W, H), p)
    for gx in range(0, W + 1, 60):  # 은은한 점 격자
        for gy in range(0, H + 1, 60):
            cv.drawCircle(gx + (t * 6) % 60, gy, 1.4, fill(SKY, 22))
    g = fill(SKY, 26)
    g.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 160))
    cv.drawCircle(W * 0.85 + math.sin(t * 0.2) * 60, H * 0.1, 300, g)


# ------------------------------------------------------------------ 소리

def decode(path):
    return V._decode(path)


def norm_sfx(name):
    a = decode(os.path.join(HERE, "sfx", f"{name}.mp3"))
    env = np.convolve(np.abs(a), np.ones(441) / 441, "same")
    idx = np.where(env > 0.01)[0]
    if len(idx):
        a = a[max(0, idx[0] - 200):idx[-1] + 4410]
    rms = np.sqrt(np.mean(a ** 2)) + 1e-9
    a = a * min(0.18 / rms, 0.9 / (np.abs(a).max() + 1e-9))
    f = min(len(a), 2205)
    a[-f:] *= np.linspace(1, 0, f)
    return a.astype(np.float32)


def bgm(name, dur, offset=0.0, fade_in=1.0, fade_out=1.5):
    a = decode(os.path.join(HERE, "bgm", f"{name}.mp3"))
    env = np.convolve(np.abs(a), np.ones(441) / 441, "same")
    idx = np.where(env > 0.005)[0]
    a = a[idx[0]:idx[-1]]
    a = a * (0.11 / (np.sqrt(np.mean(a ** 2)) + 1e-9))
    xf = int(2.0 * SR)
    out = a.copy()
    need = int((offset + dur) * SR) + 10
    while len(out) < need:
        r = np.linspace(0, 1, xf)
        out[-xf:] = out[-xf:] * (1 - r) + a[:xf] * r
        out = np.concatenate([out, a[xf:]])
    seg = out[int(offset * SR):int(offset * SR) + int(dur * SR)].copy()
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    seg[:fi] *= np.linspace(0, 1, fi)
    seg[-fo:] *= np.linspace(1, 0, fo)
    return seg.astype(np.float32)


# ------------------------------------------------------------------ 장면 틀

LINE = {lid: (sub, spoken) for lid, sub, spoken in LINES}


class Scene:
    chapter = ""
    music = "main"

    def __init__(self):
        self.lines, self.sfxs, self.dur, self.cur = [], [], 1.0, 0.0
        self.setup()

    def say(self, lid, t=None, gap=0.45):
        sub, spoken = LINE[lid]
        a = V.eleven_one(spoken, NARRATOR, None)
        a = V.trim_silence(a)
        st = self.cur + gap if t is None else t
        self.lines.append(dict(id=lid, t=st, end=st + len(a) / SR, a=a, sub=sub))
        self.cur = st + len(a) / SR
        return st, self.cur

    def sfx(self, t, name, vol=1.0):
        self.sfxs.append((t, name, vol))

    def setup(self):
        pass

    def draw(self, cv, t):
        pass

    def at(self, lid, frac=0.0):
        """대사 lid 가 frac 만큼 진행된 시각."""
        ln = next(l for l in self.lines if l["id"] == lid)
        return ln["t"] + (ln["end"] - ln["t"]) * frac


def subtitle(cv, s, a):
    if not s:
        return
    size = 36
    parts = [s]
    if tw(s, size, "SemiBold") > W - 360:  # 두 줄로
        words, best = s.split(" "), None
        for i in range(1, len(words)):
            l1, l2 = " ".join(words[:i]), " ".join(words[i:])
            d = abs(tw(l1, size, "SemiBold") - tw(l2, size, "SemiBold"))
            if best is None or d < best[0]:
                best = (d, [l1, l2])
        parts = best[1]
    y0 = H - 70 - (len(parts) - 1) * 48
    wmax = max(tw(p, size, "SemiBold") for p in parts)
    cv.drawPath(rrect(W / 2 - wmax / 2 - 30, y0 - 46, W / 2 + wmax / 2 + 30, H - 52, 16), fill((5, 10, 24), int(175 * a)))
    for i, p in enumerate(parts):
        text(cv, p, W / 2, y0 + i * 48, size, TEXT, "SemiBold", "center", int(255 * a))


def header(cv, sc, t, idx, total):
    a = int(255 * appear(t, 0.1))
    text(cv, f"{idx:02d}", 80, 92, 26, SKY, "Black", a=a)
    text(cv, sc.chapter, 130, 92, 26, TEXT2, "SemiBold", a=a)
    text(cv, "2026.09.26 기준", W - 80, 92, 22, MUTED, "Medium", "right", a)
    cv.drawLine(80, 112, W - 80, 112, stroke(CARD_LINE, 2, a))


def title_big(cv, s, t, t0=0.15, y=190, size=64, col=TEXT):
    k = appear(t, t0, 0.5)
    text(cv, s, 80, y + (1 - k) * 20, size, col, "Black", a=int(255 * k))


def countup(v, k, fmt="{:.0f}"):
    return fmt.format(v * ease_out(k))


# ------------------------------------------------------------------ 0. 제목

class Title(Scene):
    chapter = "숫자로 보는 맨체스터 시티"

    def setup(self):
        self.sfx(0.2, "whoosh", 0.8)
        self.say("title", t=1.4)
        self.sfx(0.9, "chime", 0.6)
        self.dur = self.cur + 1.0

    def draw(self, cv, t):
        cx, cy = W / 2, 430
        for i, (r, sp, a0) in enumerate(((250, 0.35, 0), (200, -0.5, 1), (300, 0.2, 2))):
            k = appear(t, 0.1 + i * 0.15, 0.9)
            p = skia.Path()
            p.addArc(skia.Rect.MakeLTRB(cx - r, cy - r, cx + r, cy + r), t * sp * 60 + a0 * 90, 260 * k)
            cv.drawPath(p, stroke(SKY if i != 1 else BLUE, 5 if i != 1 else 3, 200))
        k = appear(t, 0.4, 0.7)
        text(cv, "MANCHESTER CITY", cx, cy + 30 + (1 - k) * 30, 118, SKY, "Black", "center", int(255 * k))
        k2 = appear(t, 0.8, 0.6)
        text(cv, "숫자로 보는 맨시티 · 2026년 9월", cx, cy + 120, 52, TEXT, "Bold", "center", int(255 * k2))
        k3 = appear(t, 1.1, 0.5)
        w = tw("2026.09.26 기준", 28, "SemiBold")
        cv.drawPath(rrect(cx - w / 2 - 24, cy + 160, cx + w / 2 + 24, cy + 210, 25), fill(SKY, int(60 * k3)))
        text(cv, "2026.09.26 기준", cx, cy + 196, 28, SKY, "SemiBold", "center", int(255 * k3))


# ------------------------------------------------------------------ 1. 한눈에

class KPI(Scene):
    chapter = "한눈에 보기"

    def setup(self):
        self.say("kpi", t=0.7)
        self.tiles_t = [self.at("kpi", f) for f in (0.12, 0.42, 0.56, 0.78)]
        for x in self.tiles_t:
            self.sfx(x, "pop", 0.7)
            self.sfx(x + 0.05, "tick", 0.35)
        self.dur = self.cur + 1.2

    def draw(self, cv, t):
        title_big(cv, "지금 맨시티, 리그 선두", t)
        tiles = [("프리미어리그 순위", 1, "{:.0f}위", "5라운드 종료 · 9월 20일"),
                 ("리그 5경기", 5, "{:.0f}전 전승", "5승 0무 0패"),
                 ("승점", 15, "{:.0f}점", "2위 아스날 12점"),
                 ("공식전 8경기", 7, "{:.0f}승 1패", "커뮤니티 실드만 패배")]
        for i, ((lab, v, fmt, sub), t0) in enumerate(zip(tiles, self.tiles_t)):
            k = appear(t, t0, 0.5)
            if k <= 0:
                continue
            x0 = 80 + i * 450
            y0 = 300 + (1 - k) * 40
            card(cv, x0, y0, x0 + 420, y0 + 330, int(255 * k))
            text(cv, lab, x0 + 36, y0 + 64, 30, TEXT2, "SemiBold", a=int(255 * k))
            text(cv, countup(v, (t - t0) / 0.9, fmt), x0 + 36, y0 + 200, 96, TEXT if i else SKY, "Black",
                 a=int(255 * k))
            text(cv, sub, x0 + 36, y0 + 280, 26, MUTED, "Medium", a=int(255 * k))
        k = appear(t, self.tiles_t[-1] + 0.6, 0.5)
        if k > 0:
            items = [("리그 득점", "13"), ("리그 실점", "5"), ("득실차", "+8"), ("공식전 득점", "20"), ("공식전 실점", "8")]
            x = 80
            for lab, v in items:
                wv = text(cv, v, x, 760, 44, TEXT, "Black", a=int(255 * k))
                wl = text(cv, lab, x + wv + 12, 760, 26, TEXT2, "Medium", a=int(255 * k))
                x += wv + wl + 70


# ------------------------------------------------------------------ 2. 시대 교체

class Era(Scene):
    chapter = "과르디올라 시대의 끝"

    def setup(self):
        self.say("era1", t=0.6)
        self.say("era2", gap=0.6)
        self.t_trophy = self.at("era1", 0.25)
        for i in range(20):
            self.sfx(self.t_trophy + i * 0.07, "blip", 0.25)
        self.t_mar = self.at("era1", 0.68)
        self.sfx(self.t_mar, "slide", 0.7)
        self.t_rec = self.at("era2", 0.1)
        for i in range(5):
            self.sfx(self.t_rec + i * 0.35, "pop", 0.6)
        self.dur = self.cur + 1.4

    def draw(self, cv, t):
        title_big(cv, "10년, 트로피 20개 그리고 새 감독", t)
        # 타임라인 2016 → 2026
        x0, x1, y = 120, 1800, 285
        k = appear(t, 0.3, 1.2)
        cv.drawLine(x0, y, x0 + (x1 - x0) * k, y, stroke(CARD_LINE, 4))
        for i, yr in enumerate(range(2016, 2027)):
            x = x0 + (x1 - x0) * i / 10
            if (x - x0) / (x1 - x0) <= k:
                cv.drawCircle(x, y, 7, fill(SKY))
                text(cv, str(yr), x, y + 44, 24, TEXT2, "SemiBold", "center")
        # 트로피 20개가 쌓인다
        n = int(max(0, min(20, (t - self.t_trophy) / 0.07))) if t > self.t_trophy else 0
        for i in range(n):
            cx = 140 + (i % 10) * 64
            cy = 460 + (i // 10) * 70
            cup(cv, cx, cy, 22)
        if n:
            text(cv, f"{n}", 820, 520, 96, GOLD, "Black")
            text(cv, "메이저 트로피", 820, 560, 26, TEXT2, "SemiBold")
        # 두 감독 카드
        k1 = appear(t, 0.8, 0.5)
        card(cv, 80, 640, 900, 860, int(255 * k1))
        text(cv, "펩 과르디올라", 116, 704, 40, TEXT, "Black", a=int(255 * k1))
        text(cv, "2016 – 2026 · 10시즌 · 5월 22일 사임 발표", 116, 752, 26, TEXT2, "Medium", a=int(255 * k1))
        text(cv, "현재 시티 풋볼 그룹 글로벌 앰배서더", 116, 800, 24, MUTED, "Medium", a=int(255 * k1))
        k2 = appear(t, self.t_mar, 0.5)
        if k2 > 0:
            cv.drawLine(920, 750, 920 + 80 * k2, 750, stroke(SKY, 5))
            cv.drawPath(tri(1000, 750, 16), fill(SKY, int(255 * k2)))
            card(cv, 1030, 640, 1840, 860, int(255 * k2), line=SKY)
            text(cv, "엔초 마레스카", 1066, 704, 40, SKY, "Black", a=int(255 * k2))
            text(cv, "2026년 6월 29일 부임 · 3년 계약", 1066, 752, 26, TEXT2, "Medium", a=int(255 * k2))
            text(cv, "주장 후벵 디아스 · 부주장 돈나룸마, 홀란", 1066, 800, 24, MUTED, "Medium", a=int(255 * k2))
        if t >= self.t_rec:  # 2025-26 마지막 시즌 성적
            for i, (lab, sub, col) in enumerate((("리그 2위", "우승 아스날", TEXT2), ("FA컵 우승", "결승 1–0 첼시", GOLD),
                                                  ("리그컵 우승", "결승 2–0 아스날", GOLD),
                                                  ("UCL 16강", "합계 1–5 레알", TEXT2),
                                                  ("홀란 38골", "공식전(리그 27)", SKY))):
                kk = appear(t, self.t_rec + i * 0.35, 0.4)
                if kk <= 0:
                    continue
                bx = 1060 + (i % 3) * 262
                by = 425 + (i // 3) * 106
                card(cv, bx, by, bx + 244, by + 94, int(255 * kk), r=16)
                text(cv, lab, bx + 20, by + 44, 28, col, "Black", a=int(255 * kk))
                text(cv, sub, bx + 20, by + 76, 21, MUTED, "Medium", a=int(255 * kk))
            text(cv, "2025-26 마지막 시즌", 1060, 405, 24, TEXT2, "SemiBold", a=int(255 * appear(t, self.t_rec, 0.4)))


def cup(cv, cx, cy, s):
    p = skia.Path()
    p.moveTo(cx - s * 0.8, cy - s)
    p.lineTo(cx + s * 0.8, cy - s)
    p.quadTo(cx + s * 0.8, cy + s * 0.2, cx, cy + s * 0.35)
    p.quadTo(cx - s * 0.8, cy + s * 0.2, cx - s * 0.8, cy - s)
    cv.drawPath(p, fill(GOLD))
    cv.drawRect(skia.Rect.MakeLTRB(cx - s * 0.12, cy + s * 0.3, cx + s * 0.12, cy + s * 0.75), fill(GOLD))
    cv.drawRect(skia.Rect.MakeLTRB(cx - s * 0.45, cy + s * 0.72, cx + s * 0.45, cy + s * 0.9), fill(GOLD))


def tri(x, y, s):
    p = skia.Path()
    p.moveTo(x, y)
    p.lineTo(x - s, y - s * 0.7)
    p.lineTo(x - s, y + s * 0.7)
    p.close()
    return p


# ------------------------------------------------------------------ 3. 이적시장

INS = [("엔조 페르난데스", "첼시", 125.0), ("엘리엇 앤더슨", "노팅엄 포레스트", 116.0), ("아이유브 부아디", "릴", 85.6),
       ("일리만 은디아예", "에버튼", 65.0), ("알랑", "파우메이라스", 32.0), ("마티스 데투르베", "트루아", 21.7),
       ("제레미 몽가", "레스터", 10.0), ("피어스 찰스", "셰필드 웬즈데이", 3.0), ("헤로니모 룰리", "마르세유", 1.7)]
OUTS = [("사비뉴", "토트넘", 75.0), ("로드리", "바르셀로나", 65.4), ("레인더르스", "알카드시아", 52.0),
        ("니코 곤살레스", "뉴캐슬", 48.0), ("제임스 트래포드", "리즈", 45.0), ("마누엘 아칸지", "인테르", 13.0),
        ("네이선 아케", "페네르바체", 7.0)]


class Transfers(Scene):
    chapter = "여름 이적시장"

    def setup(self):
        self.say("tr1", t=0.6)
        self.t_tot = [self.at("tr1", f) for f in (0.3, 0.72)]
        for x in self.t_tot:
            self.sfx(x, "tick", 0.5)
        self.t_bars = self.cur + 0.2
        self.say("tr2", gap=0.5)
        for i in range(9):
            self.sfx(self.t_bars + i * 0.12, "pop", 0.35)
        self.t_out = self.cur + 0.2
        self.say("tr3", gap=0.5)
        for i in range(7):
            self.sfx(self.t_out + i * 0.12, "pop", 0.35)
        self.t_free = self.at("tr3", 0.62)
        self.sfx(self.t_free, "slide", 0.6)
        self.dur = self.cur + 1.6

    def draw(self, cv, t):
        title_big(cv, "4억 5천만 파운드의 여름", t)
        tiles = [("영입 지출", 450.8, BLUE), ("판매 수입", 319.4, RED), ("순지출", 131.4, TEXT)]
        for i, (lab, v, col) in enumerate(tiles):
            t0 = self.t_tot[0] if i == 0 else self.t_tot[1] if i == 1 else self.t_tot[1] + 0.6
            k = appear(t, t0, 0.4)
            if k <= 0:
                continue
            x0 = 1050 + i * 280
            text(cv, lab, x0, 170, 24, TEXT2, "SemiBold", a=int(255 * k))
            text(cv, "£" + countup(v, (t - t0) / 0.9, "{:.1f}") + "M", x0, 222, 48, col, "Black", a=int(255 * k))
        # 막대 그래프: 가운데 기준선, 왼쪽 = 나간 선수(빨강), 오른쪽 = 온 선수(파랑). 축은 하나(£M)
        cx, top, rh, bh = 960, 322, 50, 30
        scale = 540 / 125.0
        ka = appear(t, self.t_bars - 0.3, 0.4)
        if ka > 0:
            cv.drawLine(cx, top - 20, cx, top + rh * 9, stroke(MUTED, 2, int(255 * ka)))
            text(cv, "온 선수 →", cx + 20, top - 30, 24, BLUE, "Bold", a=int(255 * ka))
            text(cv, "← 나간 선수", cx - 20, top - 30, 24, RED, "Bold", "right", int(255 * ka))
        focus_in = self.at("tr2", 0.0) <= t < self.t_out
        for i, (name, club, fee) in enumerate(INS):
            k = appear(t, self.t_bars + i * 0.12, 0.6)
            if k <= 0:
                continue
            y = top + i * rh
            dim = focus_in and i > 1
            a = 110 if dim else 255
            bar_h(cv, cx + 2, y, fee * scale * ease_out(k), bh, BLUE, a)
            x_end = cx + 2 + fee * scale * ease_out(k)
            label = f"{name} · {club}"
            lx = x_end + 14
            text(cv, f"£{fee:g}M", lx, y + bh - 5, 24, TEXT, "Black", a=a)
            text(cv, label, lx + tw(f"£{fee:g}M", 24, "Black") + 12, y + bh - 5, 22, TEXT2, "Medium", a=a)
        focus_out = self.at("tr3", 0.0) <= t < self.t_free
        for i, (name, club, fee) in enumerate(OUTS):
            k = appear(t, self.t_out + i * 0.12, 0.6)
            if k <= 0:
                continue
            y = top + i * rh
            a = 110 if (focus_out and i > 1) else 255
            bar_h(cv, cx - 2, y, fee * scale * ease_out(k), bh, RED, a, right=False)
            x_end = cx - 2 - fee * scale * ease_out(k)
            lab = f"£{fee:g}M"
            text(cv, lab, x_end - 14, y + bh - 5, 24, TEXT, "Black", "right", a)
            text(cv, f"{name} · {club}", x_end - 26 - tw(lab, 24, "Black"), y + bh - 5, 22, TEXT2, "Medium",
                 "right", a)
        k = appear(t, self.t_free, 0.5)
        if k > 0:
            y0 = 790 - (1 - k) * 20
            card(cv, 80, y0, 930, y0 + 90, int(255 * k), r=16)
            text(cv, "계약 만료로 이적", 110, y0 + 38, 22, TEXT2, "SemiBold", a=int(255 * k))
            text(cv, "베르나르두 실바 → 레알 마드리드 · 존 스톤스 → 인테르", 110, y0 + 72, 24, TEXT, "Bold",
                 a=int(255 * k))
            card(cv, 990, y0, 1840, y0 + 90, int(255 * k), r=16)
            text(cv, "임대", 1020, y0 + 38, 22, TEXT2, "SemiBold", a=int(255 * k))
            text(cv, "그릴리시 → 에버튼 · 마르무시 → 토트넘 · 필립스 → 셰필드 Utd", 1020, y0 + 72, 24, TEXT, "Bold",
                 a=int(255 * k))


# ------------------------------------------------------------------ 4. 경기 결과

MATCHES = [
    ("8.16", "커뮤니티 실드", "아스날", "중립", 0, 3, "상대 득점: 칼라피오리, 하베르츠, 외데고르"),
    ("8.23", "리그 1R", "본머스", "홈", 2, 1, "게히 84′, 그바르디올 90+′"),
    ("8.28", "리그 2R", "크리스털 팰리스", "원정", 4, 1, "홀란 2, 셰르키 2"),
    ("9.5", "리그 3R", "코번트리", "홈", 1, 0, "홀란 26′"),
    ("9.8", "UCL 1차전", "포르투", "원정", 2, 0, "홀란 47′, 90+1′"),
    ("9.13", "리그 4R · 더비", "맨유", "원정", 1, 0, "홀란 · 포든 23′ 퇴장"),
    ("9.17", "리그컵 3R", "노리치", "홈", 5, 0, "리그컵 첫 경기"),
    ("9.20", "리그 5R", "선덜랜드", "홈", 5, 3, "세메뇨 2, 엔조, 셰르키, 홀란"),
]


class Results(Scene):
    chapter = "경기 결과"

    def setup(self):
        self.say("res1", t=0.6)
        self.t_cards = [self.at("res1", 0.05)] + [self.at("res1", 0.62) + i * 0.3 for i in range(7)]
        for x in self.t_cards:
            self.sfx(x, "pop", 0.5)
        self.say("res2", gap=0.5)
        self.t_derby = self.at("res2", 0.0)
        self.sfx(self.t_derby, "chime", 0.5)
        self.dur = self.cur + 1.4

    def draw(self, cv, t):
        title_big(cv, "8경기 7승 1패", t)
        for i, (d, comp, opp, venue, gf, ga, note) in enumerate(MATCHES):
            k = appear(t, self.t_cards[i], 0.45)
            if k <= 0:
                continue
            x0 = 80 + (i % 4) * 445
            y0 = 290 + (i // 4) * 290 + (1 - k) * 30
            derby = i == 5 and t >= self.t_derby
            card(cv, x0, y0, x0 + 420, y0 + 260, int(255 * k), line=SKY if derby else CARD_LINE)
            a = int(255 * k)
            text(cv, f"{d} · {comp}", x0 + 28, y0 + 50, 23, TEXT2, "SemiBold", a=a)
            text(cv, f"vs {opp}", x0 + 28, y0 + 104, 34, TEXT, "Black", a=a)
            text(cv, venue, x0 + 28 + tw(f"vs {opp}", 34, "Black") + 12, y0 + 104, 22, MUTED, "Medium", a=a)
            text(cv, f"{gf} – {ga}", x0 + 28, y0 + 184, 64, TEXT, "Black", a=a)
            win = gf > ga
            chip = "승" if win else "패"
            col = GOOD if win else CRIT
            cv.drawPath(rrect(x0 + 330, y0 + 130, x0 + 392, y0 + 192, 14), fill(col, a))
            text(cv, chip, x0 + 361, y0 + 175, 34, TEXT, "Black", "center", a)
            text(cv, note, x0 + 28, y0 + 232, 20, MUTED, "Medium", a=a)
            if i == 5 and derby:  # 레드카드 표시
                cv.drawPath(rrect(x0 + 360, y0 + 26, x0 + 386, y0 + 62, 4), fill(CRIT, a))


# ------------------------------------------------------------------ 5. 순위표

TABLE = [(1, "맨체스터 시티", 5, 5, 0, 0, 8, 15), (2, "아스날", 5, 4, 0, 1, 4, 12),
         (3, "브라이턴", 5, 3, 1, 1, 11, 10), (4, "브렌트포드", 5, 2, 3, 0, 6, 9),
         (5, "리즈", 5, 2, 3, 0, 4, 9), (6, "리버풀", 5, 2, 3, 0, 3, 9)]


class Table(Scene):
    chapter = "리그 순위"

    def setup(self):
        self.say("tab", t=0.6)
        for i in range(6):
            self.sfx(0.5 + i * 0.12, "pop", 0.35)
        self.dur = self.cur + 1.6

    def draw(self, cv, t):
        title_big(cv, "3점 차 선두", t)
        text(cv, "프리미어리그 5라운드 종료(9월 20일) 기준", 80, 250, 24, MUTED, "Medium", a=int(255 * appear(t, 0.3)))
        cols = [("순위", 120), ("팀", 200), ("경기", 700), ("승", 790), ("무", 860), ("패", 930), ("득실", 1010),
                ("승점", 1120)]
        y0 = 330
        for lab, x in cols:
            text(cv, lab, x, y0, 22, MUTED, "SemiBold", "center" if lab not in ("팀",) else "left",
                 int(255 * appear(t, 0.4)))
        for i, (rk, team, p, w, d, l, gd, pts) in enumerate(TABLE):
            k = appear(t, 0.5 + i * 0.12, 0.45)
            if k <= 0:
                continue
            y = y0 + 30 + i * 96
            city = rk == 1
            cv.drawPath(rrect(80, y, 1840, y + 80, 16), fill((34, 58, 110) if city else CARD, int(255 * k)))
            if city:
                cv.drawPath(rrect(80, y, 1840, y + 80, 16), stroke(SKY, 3, int(255 * k)))
            a = int(255 * k)
            vals = [str(rk), team, str(p), str(w), str(d), str(l), f"{gd:+d}", str(pts)]
            for (lab, x), v in zip(cols, vals):
                text(cv, v, x, y + 53, 30 if lab != "팀" else 32, SKY if (city and lab in ("팀", "승점")) else TEXT,
                     "Black" if lab in ("팀", "승점") else "Bold", "left" if lab == "팀" else "center", a)
            bw = 560 * pts / 15 * ease_out((t - 0.7 - i * 0.12) / 0.8)
            bar_h(cv, 1200, y + 26, bw, 28, BLUE, a)
        k = appear(t, self.at("tab", 0.55), 0.5)
        if k > 0:
            text(cv, "승점 차 3", 1760, 290, 34, SKY, "Black", "right", int(255 * k))


# ------------------------------------------------------------------ 6. 득점

SCORERS = [("엘링 홀란", 5), ("라얀 셰르키", 3), ("앙투안 세메뇨", 2), ("엔조 페르난데스", 1), ("마크 게히", 1),
           ("요슈코 그바르디올", 1)]


class Scorers(Scene):
    chapter = "득점 분포"

    def setup(self):
        self.say("sc", t=0.6)
        for i in range(6):
            self.sfx(0.6 + i * 0.15, "pop", 0.4)
        self.t_hl = self.at("sc", 0.35)
        self.sfx(self.t_hl, "chime", 0.5)
        self.dur = self.cur + 1.4

    def draw(self, cv, t):
        title_big(cv, "리그 13골, 그중 5골이 홀란", t)
        text(cv, "리그 득점자(5라운드)", 80, 290, 24, TEXT2, "SemiBold", a=int(255 * appear(t, 0.4)))
        x0, y0, rh = 380, 330, 92
        scale = 700 / 5
        for i, (name, g) in enumerate(SCORERS):
            k = appear(t, 0.6 + i * 0.15, 0.7)
            if k <= 0:
                continue
            y = y0 + i * rh
            text(cv, name, x0 - 24, y + 44, 28, TEXT, "Bold", "right", int(255 * k))
            bar_h(cv, x0, y + 14, g * scale * ease_out(k), 44, BLUE, int(255 * k))
            text(cv, f"{g}", x0 + g * scale * ease_out(k) + 16, y + 48, 32, TEXT, "Black", a=int(255 * k))
        k = appear(t, self.t_hl, 0.5)
        if k > 0:
            card(cv, 1280, 330, 1840, 860, int(255 * k), line=SKY)
            a = int(255 * k)
            text(cv, "엘링 홀란", 1320, 400, 40, SKY, "Black", a=a)
            for j, (v, lab) in enumerate((("5", "리그 골 · 득점 1위"), ("7", "공식전 골"), ("38", "지난 시즌 공식전 골"))):
                text(cv, v, 1320, 520 + j * 120, 80, TEXT, "Black", a=a)
                text(cv, lab, 1320 + tw(v, 80, "Black") + 18, 520 + j * 120, 26, TEXT2, "SemiBold", a=a)
            text(cv, "리그 득점 2위: 이삭(리버풀) 4골", 1320, 830, 22, MUTED, "Medium", a=a)


# ------------------------------------------------------------------ 7. 115개 혐의

CHARGES = [("재무 정보 부정확", 54, "2009/10–2017/18"), ("선수·감독 보수 미공개", 14, "2009/10–2015/16"),
           ("UEFA 재정 규정 위반", 5, "2013/14–2017/18"), ("리그 수익성 규정(PSR) 위반", 7, "2015/16–2017/18"),
           ("조사 비협조", 35, "2018/19–2022/23")]


class Charges(Scene):
    chapter = "115개 혐의 판결"
    music = "tense"

    def setup(self):
        self.sfx(0.3, "impact", 0.9)
        self.say("ch1", t=1.0)
        self.t_num = self.at("ch1", 0.55)
        self.sfx(self.t_num, "tick", 0.6)
        self.say("ch2", gap=0.5)
        # 범주 강조 시각(대사 안 순서대로)
        fr = (0.02, 0.28, 0.46, 0.62, 0.8)
        self.t_cat = [self.at("ch2", f) for f in fr]
        for x in self.t_cat:
            self.sfx(x, "blip", 0.6)
        self.say("ch3", gap=0.5)
        self.t_sanc = self.at("ch3", 0.2)
        self.sfx(self.t_sanc, "slide", 0.7)
        self.dur = self.cur + 1.6

    def draw(self, cv, t):
        k = appear(t, 0.2, 0.3)
        cv.drawPath(rrect(80, 150, 250, 200, 10), fill(CRIT, int(255 * k)))
        text(cv, "속보", 165, 187, 28, TEXT, "Black", "center", int(255 * k))
        text(cv, "9월 25일 · 독립위원회 판결 (보도)", 275, 188, 30, TEXT, "Bold", a=int(255 * k))
        # 큰 숫자 114 / 115
        kn = appear(t, self.t_num, 0.5)
        if kn > 0:
            v = countup(114, (t - self.t_num) / 1.0)
            text(cv, v, 80, 390, 170, TEXT, "Black", a=int(255 * kn))
            text(cv, "/ 115", 80 + tw(v, 170, "Black") + 16, 390, 70, MUTED, "Black", a=int(255 * kn))
            text(cv, "건 인정", 80, 450, 36, TEXT2, "Bold", a=int(255 * kn))
            text(cv, "※ The Athletic·BBC 보도 기준 · 판결문 미공개 · 리그는 논평 거부", 80, 500, 22, MUTED,
                 "Medium", a=int(255 * kn))
        # 와플: 115칸을 범주별 색으로(한 칸 = 혐의 1건)
        gx, gy, cell, gap, cols = 920, 250, 30, 6, 23
        idx = 0
        for ci, (lab, n, yrs) in enumerate(CHARGES):
            for j in range(n):
                r, c = divmod(idx, cols)
                x = gx + c * (cell + gap)
                y = gy + r * (cell + gap)
                show = appear(t, 0.8 + idx * 0.012, 0.3)
                if show > 0:
                    lit = t < self.t_cat[0] or (self.t_cat[ci] <= t < (self.t_cat[ci + 1] if ci + 1 < 5 else 1e9)) \
                        or t >= self.t_sanc
                    cv.drawPath(rrect(x, y, x + cell, y + cell, 5), fill(CATS[ci], int(255 * show * (1 if lit else 0.3))))
                idx += 1
        # 범례(숫자와 함께)
        for ci, (lab, n, yrs) in enumerate(CHARGES):
            kk = appear(t, self.t_cat[ci], 0.4) if t >= self.t_cat[0] else appear(t, 1.8, 0.4)
            y = 480 + ci * 58
            active = self.t_cat[ci] <= t < (self.t_cat[ci + 1] if ci + 1 < 5 else self.t_sanc)
            a = int(255 * kk)
            cv.drawPath(rrect(920, y - 26, 950, y + 4, 5), fill(CATS[ci], a))
            text(cv, f"{n}", 970, y, 32, TEXT, "Black", a=a)
            text(cv, lab, 1030, y, 28, TEXT if active else TEXT2, "Bold" if active else "SemiBold", a=a)
            text(cv, yrs, 1840, y, 22, MUTED, "Medium", "right", a)
        # 징계 가능성
        ks = appear(t, self.t_sanc, 0.5)
        if ks > 0:
            y0 = 545
            card(cv, 80, y0, 860, y0 + 322, int(255 * ks), line=CRIT)
            a = int(255 * ks)
            text(cv, "징계: 미정", 116, y0 + 60, 36, TEXT, "Black", a=a)
            for j, s_ in enumerate(("승점 삭감", "벌금", "최악: 리그 퇴출")):
                bx = 116 + j * 238
                cv.drawPath(rrect(bx, y0 + 84, bx + 222, y0 + 136, 12), fill(CARD_LINE, a))
                text(cv, s_, bx + 111, y0 + 119, 24, TEXT, "Bold", "center", a)
            text(cv, "과거 승점 삭감 사례", 116, y0 + 176, 22, TEXT2, "SemiBold", a=a)
            for j, (lab, v) in enumerate((("에버튼 2023-24 (항소 후)", 6), ("더비 카운티 2021-22", 21))):
                yy = y0 + 190 + j * 42
                text(cv, lab, 116, yy + 26, 22, TEXT2, "Medium", a=a)
                bar_h(cv, 440, yy + 6, 16 * v * ease_out((t - self.t_sanc - 0.3) / 0.8), 26, BLUE, a)
                text(cv, f"−{v}점", 450 + 16 * v * ease_out((t - self.t_sanc - 0.3) / 0.8), yy + 28, 24, TEXT,
                     "Black", a=a)
            text(cv, "맨시티: \"항소하겠다\" · 항소 기한 14일", 116, y0 + 300, 22, SKY, "Bold", a=a)


# ------------------------------------------------------------------ 8. 다음 일정

class Next(Scene):
    chapter = "다음 일정"

    def setup(self):
        self.say("nx", t=0.6)
        self.t_c = [self.at("nx", 0.05), self.at("nx", 0.55)]
        for x in self.t_c:
            self.sfx(x, "slide", 0.6)
        self.dur = self.cur + 1.4

    def draw(self, cv, t):
        title_big(cv, "첫 번째 큰 시험", t)
        fx = [("10.11 (일)", "프리미어리그 6라운드", "리버풀 vs 맨체스터 시티", "안필드 · 15:30(영국)"),
              ("10.14 (수)", "챔피언스리그 리그 페이즈 2차전", "맨체스터 시티 vs 파리 생제르맹", "에티하드 스타디움")]
        for i, (d, comp, m, venue) in enumerate(fx):
            k = appear(t, self.t_c[i], 0.5)
            if k <= 0:
                continue
            y0 = 300 + i * 250 + (1 - k) * 30
            card(cv, 80, y0, 1840, y0 + 210, int(255 * k), line=SKY if i == 0 else CARD_LINE)
            a = int(255 * k)
            text(cv, d, 120, y0 + 90, 56, SKY, "Black", a=a)
            text(cv, comp, 520, y0 + 70, 26, TEXT2, "SemiBold", a=a)
            text(cv, m, 520, y0 + 128, 44, TEXT, "Black", a=a)
            text(cv, venue, 520, y0 + 176, 24, MUTED, "Medium", a=a)
        k = appear(t, self.t_c[1] + 1.2, 0.5)
        if k > 0:
            text(cv, "지켜볼 것: 징계 수위 발표 · 항소 절차 · 포든 퇴장 징계", 80, 870, 28, TEXT2, "Bold", a=int(255 * k))


# ------------------------------------------------------------------ 9. 마무리

class Outro(Scene):
    chapter = "정리"

    def setup(self):
        self.say("out", t=0.5)
        self.sfx(0.3, "whoosh", 0.6)
        self.dur = self.cur + 3.2

    def draw(self, cv, t):
        k1 = appear(t, 0.5, 0.5)
        card(cv, 80, 250, 940, 620, int(255 * k1), line=SKY)
        text(cv, "경기장 안", 120, 320, 30, TEXT2, "SemiBold", a=int(255 * k1))
        text(cv, "순항", 120, 440, 110, SKY, "Black", a=int(255 * k1))
        text(cv, "리그 5전 전승 · 1위 · 홀란 득점 선두", 120, 540, 26, TEXT, "Bold", a=int(255 * k1))
        k2 = appear(t, 1.4, 0.5)
        card(cv, 980, 250, 1840, 620, int(255 * k2), line=CRIT)
        text(cv, "경기장 밖", 1020, 320, 30, TEXT2, "SemiBold", a=int(255 * k2))
        text(cv, "폭풍", 1020, 440, 110, RED, "Black", a=int(255 * k2))
        text(cv, "115건 중 114건 인정(보도) · 징계 미정", 1020, 540, 26, TEXT, "Bold", a=int(255 * k2))
        k3 = appear(t, self.dur - 2.6, 0.6)
        if k3 > 0:
            a = int(255 * k3)
            text(cv, "출처", 80, 700, 22, TEXT2, "Bold", a=a)
            src = ["Wikipedia: 2026–27 Manchester City F.C. season · 2026–27 Premier League · 2025–26 Manchester City F.C. season",
                   "ESPN · Sky Sports · beIN SPORTS · Opta Analyst · NBC Sports · Man City 공식 홈페이지 (2026.09.26 조회)"]
            for j, s_ in enumerate(src):
                text(cv, s_, 80, 740 + j * 38, 22, MUTED, "Medium", a=a)


# ------------------------------------------------------------------ 조립

def build():
    return [Title(), KPI(), Era(), Transfers(), Results(), Table(), Scorers(), Charges(), Next(), Outro()]


def frame(scenes, starts, total, t, surf):
    cv = surf.getCanvas()
    si = max(i for i, s in enumerate(starts) if t >= s)
    sc = scenes[si]
    lt = t - starts[si]
    background(cv, t)
    # 장면 전환: 새 장면은 오른쪽에서 살짝 밀려 들어온다
    k = ease_out(lt / 0.6) if si > 0 else 1.0
    cv.save()
    cv.translate((1 - k) * 80, 0)
    if si > 0:
        header(cv, sc, lt, si, len(scenes) - 1)
    sc.draw(cv, lt)
    cv.restore()
    if k < 1:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(BG1, int(255 * (1 - k))))
    # 자막
    cur = None
    for ln in sc.lines:
        if ln["t"] - 0.1 <= lt < ln["end"] + 0.4:
            cur = ln
    if cur:
        subtitle(cv, cur["sub"], min(1.0, (lt - cur["t"] + 0.1) / 0.2, (cur["end"] + 0.4 - lt) / 0.2))
    # 진행 막대
    cv.drawRect(skia.Rect.MakeLTRB(0, H - 8, W, H), fill(CARD))
    cv.drawRect(skia.Rect.MakeLTRB(0, H - 8, W * t / total, H), fill(SKY))
    if t > total - 1.0:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((0, 0, 0), int(255 * (t - total + 1.0))))
    return surf.makeImageSnapshot().toarray()[..., [2, 1, 0]]


def mix(scenes, starts, total):
    n = int((total + 2) * SR)
    voice, fx, music = (np.zeros(n, np.float32) for _ in range(3))

    def put(buf, t, a, v=1.0):
        i = int(t * SR)
        j = min(len(buf), i + len(a))
        if j > i:
            buf[i:j] += a[: j - i] * v

    cache = {}
    for s, st in zip(scenes, starts):
        for ln in s.lines:
            put(voice, st + ln["t"], ln["a"])
        for t, name, v in s.sfxs:
            if name not in cache:
                cache[name] = norm_sfx(name)
            put(fx, st + t, cache[name], v)
        if st > 0:
            put(fx, st, cache.setdefault("whoosh", norm_sfx("whoosh")), 0.5)
    # 배경음악: 대부분 main, 혐의 장면만 tense
    i_ch = next(i for i, s in enumerate(scenes) if s.music == "tense")
    t_ch0, t_ch1 = starts[i_ch], starts[i_ch] + scenes[i_ch].dur
    put(music, 0, bgm("main", t_ch0 + 0.8, 0.0, 1.0, 1.2))
    put(music, t_ch0, bgm("tense", t_ch1 - t_ch0 + 0.8, 0.0, 0.6, 1.2))
    put(music, t_ch1, bgm("main", total - t_ch1, t_ch0, 1.0, 2.0))
    # 내레이션이 나오면 음악을 낮춘다
    hop = 441
    env = np.array([np.abs(voice[i:i + hop]).max() for i in range(0, n, hop)])
    sp = env > 0.02
    g = np.ones(len(sp))
    lvl = 1.0
    for i in range(len(sp) - 1, -1, -1):
        lvl = 0.0 if sp[i] else min(1.0, lvl + 1 / 6)
        g[i] = lvl
    f = 1.0
    for i in range(len(g)):
        f = g[i] if g[i] < f else min(g[i], f + 1 / 50)
        g[i] = f
    gain = np.repeat(1.0 - 0.55 * (1.0 - g), hop)[:n]
    out = voice + fx * 0.5 + music * gain
    out = np.tanh(out * 1.1) / np.tanh(1.1)
    return (out / (np.abs(out).max() + 1e-9) * 0.89)[: int(total * SR)]


def main():
    import imageio_ffmpeg
    scenes = build()
    starts, acc = [], 0.0
    for s in scenes:
        starts.append(acc)
        acc += s.dur
    total = acc
    print("total", round(total, 2), [(type(s).__name__, round(s.dur, 2)) for s in scenes])
    surf = skia.Surface(W, H)
    if "--preview" in sys.argv:
        from PIL import Image
        out = sys.argv[sys.argv.index("--preview") + 1]
        os.makedirs(out, exist_ok=True)
        for i, (s, st) in enumerate(zip(scenes, starts)):
            for f in (0.35, 0.95):
                Image.fromarray(frame(scenes, starts, total, st + s.dur * f, surf)).resize((960, 540)).save(
                    os.path.join(out, f"s{i:02d}_{f:.2f}.png"))
        return
    buf = mix(scenes, starts, total)
    wav = os.path.join(HERE, "_audio.wav")
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((buf * 32767).astype(np.int16).tobytes())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    p = subprocess.Popen([ff, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r",
                          str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "22",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags",
                          "+faststart", OUT], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for i in range(n):
        p.stdin.write(np.ascontiguousarray(frame(scenes, starts, total, i / FPS, surf)).tobytes())
        if i % 600 == 0:
            print(f"frame {i}/{n}", flush=True)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print("wrote", OUT, round(total, 1))


if __name__ == "__main__":
    main()
