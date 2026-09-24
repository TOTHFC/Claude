"""「힘내요! 데 제르비」 ─ 토트넘 상황을 한국 아동 애니메이션처럼 만든 풍자 영상.

주인공: 로베르토 데 제르비 감독. 주제가·해설·대사는 모두 음성 합성(edge-tts)으로 만들고,
주제가는 음절을 음표에 맞춰 PSOLA로 늘이고 음높이를 바꿔 부르게 했다.

    python3 make_kids.py            # -> tottenham_kids.mp4
    python3 make_kids.py --preview  # 장면별 대표 프레임만 저장
"""
import math
import os
import random
import subprocess
import sys
import wave

import numpy as np
import skia

import kchars as K
from kengine import (AIA, BLACK, CHEEK, FPS, GOLD, GRASS, GRASS2, GRAY, H, INK, LGRAY, NAVY, NAVY2, ORANGE, PINK,
                     PURPLE, RED, SKY, SKY2, SR, W, WHITE, YELLOW, C, Mixer, TF_KR, TF_TITLE, arc, back_out, blob,
                     bounce, burst, cloud, confetti, darker, draw_rainbow, drum, ease, ease_out, elastic, fill,
                     heart_path, inst, lighter, linear, mix, oval, poly, pop, radial, rays, rrect, shadow, smooth,
                     sparkle, sparkles, star_path, stroke, sweat, text, text_w)
from ksong import BEAT, render as render_song
from script import LINES
from voice import envelope, tts, tts_marks

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tottenham_kids.mp4")
GROUND = 610

SPEAKER = {  # 자막 이름표: (이름, 색)
    "nar": ("해설", (255, 120, 160)), "dz": ("데 제르비", (60, 60, 80)), "koko": ("꼬꼬", (230, 60, 60)),
    "kids": ("어린이들", (255, 160, 40)), "kane": ("케인", (220, 20, 60)), "son": ("쏘니", (40, 40, 40)),
    "villain": ("악당", (120, 40, 140)), "fan": ("마을 사람들", (40, 70, 160)),
}


def blink(t, seed=0):
    ph = (t + seed * 0.37) % 3.1
    return ph < 0.12


# ------------------------------------------------------------------ 배경 음악

CH = {"F": [53, 57, 60], "Dm": [50, 53, 57], "Bb": [46, 50, 53], "C": [48, 52, 55], "Am": [45, 48, 52],
      "G": [43, 47, 50], "Em": [40, 43, 47], "Gm": [43, 46, 50], "A": [45, 49, 52], "E": [40, 44, 47],
      "D": [50, 54, 57]}


def bgm(style, dur, seed=0):
    rng = random.Random(seed)
    cfg = {
        "happy": (132, ["F", "Dm", "Bb", "C"], "xylo", 0.9),
        "summer": (140, ["C", "Am", "F", "G"], "xylo", 1.0),
        "villain": (120, ["Dm", "Dm", "Gm", "A"], "bass", 0.8),
        "quiz": (150, ["C", "F", "G", "C"], "xylo", 1.0),
        "sad": (72, ["Am", "F", "C", "G"], "piano", 0.6),
        "night": (84, ["F", "Dm", "Bb", "C"], "bell", 0.5),
        "angry": (128, ["Dm", "Bb", "Gm", "A"], "brass", 0.8),
        "tense": (96, ["Dm", "Dm", "Bb", "A"], "pad", 0.5),
    }[style]
    bpm, prog, lead, dens = cfg
    beat = 60 / bpm
    out = np.zeros(int((dur + 2) * SR), np.float32)

    def put(t, s, v):
        i = int(t * SR)
        j = min(len(out), i + len(s))
        if j > i:
            out[i:j] += s[: j - i] * v

    nbars = int(dur / (beat * 4)) + 1
    scale = [0, 2, 4, 7, 9]
    for b in range(nbars):
        ch = CH[prog[b % len(prog)]]
        tb = b * 4 * beat
        root = ch[0] - 12 if ch[0] > 45 else ch[0]
        if style == "tense":
            put(tb, inst("pad", root, beat * 4), 0.25)
            put(tb, inst("pad", root + 12, beat * 4), 0.12)
            continue
        for k in range(4):
            if style in ("sad", "night"):
                if k in (0, 2):
                    put(tb + k * beat, inst("bass" if style == "sad" else "piano", root + (0 if k == 0 else 7),
                                            beat * 2), 0.25 if style == "sad" else 0.08)
                for m_ in ch:
                    if k in (1, 3) and style == "sad":
                        put(tb + k * beat, inst("piano", m_ + 12, beat * 1.5), 0.05)
                if style == "night":
                    arp = [ch[0] + 24, ch[1] + 24, ch[2] + 24, ch[1] + 24]
                    put(tb + k * beat, inst("bell", arp[k], beat * 2), 0.07)
                continue
            put(tb + k * beat, inst("bass", root + (0 if k % 2 == 0 else 7), beat * 0.8), 0.28)
            if k % 2 == 1 or style == "quiz":
                for m_ in ch:
                    put(tb + k * beat, inst("piano", m_ + 12, beat * 0.6), 0.05)
            if style in ("happy", "summer", "quiz"):
                put(tb + k * beat, drum("h"), 0.3)
                if k % 2 == 1:
                    put(tb + k * beat, drum("c"), 0.12)
            if style in ("villain", "angry"):
                put(tb + k * beat, drum("k" if k % 2 == 0 else "s"), 0.25)
        # 멜로디
        if style in ("happy", "summer", "quiz", "villain", "angry"):
            base = ch[0] + 24 if style not in ("villain", "angry") else ch[0] + 12
            for e in range(8):
                if rng.random() < dens * 0.7:
                    deg = rng.choice(scale if style not in ("villain", "angry") else [0, 3, 5, 7, 10])
                    put(tb + e * beat / 2, inst(lead, base + deg, beat * 0.6), 0.06 if lead != "bass" else 0.2)
    return out[: int(dur * SR)]


# ------------------------------------------------------------------ 장면 틀

class Scene:
    fade = True

    def __init__(self):
        self.lines = []   # (시작, id, 배역, 화자키, 음성, 입모양)
        self.sfxs = []
        self.beds = []
        self.dur = 1.0
        self.setup()

    def say(self, t, lid, who=None, marks=False):
        role, txt, *rest = LINES[lid]
        emo = rest[0] if rest else None
        if marks:
            a, mk = tts_marks(txt, role, emo)
        else:
            a, mk = tts(txt, role, emotion=emo), None
        self.lines.append(dict(t=t, id=lid, role=role, who=who or role, a=a, env=envelope(a, FPS), txt=txt,
                               end=t + len(a) / SR, marks=mk))
        return t + len(a) / SR

    def sfx(self, t, name, vol=1.0):
        self.sfxs.append((t, name, vol))

    def bed(self, t, arr, vol=1.0):
        self.beds.append((t, arr, vol))

    def talk(self, who, t):
        for ln in self.lines:
            if ln["who"] == who and ln["t"] <= t < ln["end"]:
                i = int((t - ln["t"]) * FPS)
                return float(ln["env"][min(i, len(ln["env"]) - 1)])
        return 0.0

    def line_at(self, t):
        cur = None
        for ln in self.lines:
            if ln["t"] <= t < ln["end"] + 0.35:
                cur = ln
        return cur

    def audio(self, m, t0):
        for ln in self.lines:
            m.add(t0 + ln["t"], ln["a"], 1.0)
        for t, n, v in self.sfxs:
            m.sfx(t0 + t, n, v)
        for t, a, v in self.beds:
            m.add(t0 + t, a, v)

    def setup(self):
        pass

    def draw(self, cv, t):
        pass

    def subtitles(self, cv, t):
        ln = self.line_at(t)
        if not ln or ln["role"] == "kids" and len(ln["txt"]) < 3:
            return
        name, col = SPEAKER[ln["role"]]
        if ln["id"] in ("bee", "thanks"):
            name = "벌떼 악당"
        elif ln["id"] == "hammer":
            name = "웨스트햄"
        subtitle(cv, ln["txt"], name, col, min(1.0, (t - ln["t"]) / 0.15))


def subtitle(cv, s, name, col, a=1.0):
    size = 40
    w = text_w(s, size)
    while w > W - 120:
        size -= 2
        w = text_w(s, size)
    y = H - 34
    al = int(255 * a)
    cv.drawPath(rrect(W / 2 - w / 2 - 26, y - size - 12, W / 2 + w / 2 + 26, y + 16, 24), fill((255, 255, 255), int(215 * a)))
    cv.drawPath(rrect(W / 2 - w / 2 - 26, y - size - 12, W / 2 + w / 2 + 26, y + 16, 24), stroke(col, 4, al))
    text(cv, s, W / 2, y, size, (50, 40, 50), align="center", a=al)
    nw = text_w(name, 24)
    x0 = W / 2 - w / 2 - 16
    cv.drawPath(rrect(x0, y - size - 38, x0 + nw + 28, y - size - 6, 16), fill(col, al))
    text(cv, name, x0 + 14, y - size - 13, 24, WHITE, a=al)


# ------------------------------------------------------------------ 배경들

def bg_sky(cv, top=SKY, bot=SKY2):
    cv.drawRect(skia.Rect.MakeWH(W, H), linear(top, bot, 0, 0, 0, H))


def sun(cv, x, y, t, r=60):
    for i in range(12):
        a = math.radians(i * 30 + t * 20)
        cv.drawLine(x + math.cos(a) * (r + 10), y + math.sin(a) * (r + 10), x + math.cos(a) * (r + 34),
                    y + math.sin(a) * (r + 34), stroke((255, 210, 80), 10))
    blob(cv, oval(x, y, r, r), (255, 220, 90), 4)
    for sx in (-1, 1):
        arc(cv, x + sx * 18, y - 6, 8, 6, 200, 140, (150, 90, 40), 4)
    arc(cv, x, y + 10, 18, 12, 20, 140, (150, 90, 40), 4)
    cv.drawPath(oval(x - 34, y + 12, 9, 6), fill(CHEEK, 120))
    cv.drawPath(oval(x + 34, y + 12, 9, 6), fill(CHEEK, 120))


def house(cv, x, y, s=1.0, roof=NAVY2, wall=(255, 245, 225)):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    blob(cv, rrect(-60, -110, 60, 0, 14), wall, 4, oc=(170, 140, 110))
    blob(cv, poly([(-78, -100), (0, -170), (78, -100)]), roof, 4)
    blob(cv, rrect(-18, -60, 18, 0, 10), (190, 130, 80), 3)
    blob(cv, rrect(-48, -90, -24, -66, 6), (170, 220, 255), 3)
    blob(cv, rrect(24, -90, 48, -66, 6), (170, 220, 255), 3)
    cv.restore()


def stadium(cv, x, y, s=1.0):
    """토트넘 홋스퍼 스타디움(둥근 그릇 + 지붕 위 수탉)."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    blob(cv, smooth([(-220, 0), (-230, -70), (-180, -120), (0, -140), (180, -120), (230, -70), (220, 0)]),
         (245, 248, 255), 5, oc=(120, 130, 170))
    for i in range(-6, 7):
        cv.drawLine(i * 32, -128 + abs(i) * 4, i * 34, -10, stroke((200, 210, 235), 4))
    cv.drawRect(skia.Rect.MakeLTRB(-220, -40, 220, -26), fill(NAVY2))
    K.rooster(cv, 0, -134, 0.55, ball=True)
    cv.restore()


def bg_village(cv, t, pan=0.0):
    bg_sky(cv)
    sun(cv, 1120, 110, t)
    for i, (cx, cy, s) in enumerate(((120, 110, 1.0), (460, 70, 0.8), (820, 140, 0.9))):
        cloud(cv, (cx + t * 12 - pan * 0.2) % 1500 - 150, cy, s)
    cv.save()
    cv.translate(-pan * 0.5, 0)
    cv.drawPath(smooth([(-200, 500), (200, 380), (600, 440), (1000, 360), (1500, 430), (1700, 800), (-200, 800)]),
                fill((150, 215, 120)))
    stadium(cv, 900, 440, 0.9)
    cv.restore()
    cv.save()
    cv.translate(-pan, 0)
    cv.drawPath(smooth([(-200, 560), (300, 500), (700, 540), (1100, 490), (1600, 540), (1700, 800), (-200, 800)]),
                fill(GRASS))
    for i, x in enumerate((80, 300, 1180, 1420)):
        house(cv, x, 545 - (i % 2) * 12, 0.8, roof=[NAVY2, (230, 90, 90), (90, 150, 230), (250, 170, 60)][i])
    for x in range(-100, 1700, 90):
        fy = 640 + (x * 7 % 30)
        cv.drawLine(x, fy, x, fy - 18, stroke((80, 160, 70), 3))
        cv.drawPath(oval(x, fy - 22, 7, 7), fill([PINK, YELLOW, WHITE][x // 90 % 3]))
    cv.restore()
    cv.drawRect(skia.Rect.MakeLTRB(0, 620, W, H), fill(GRASS2))


def bg_pitch(cv, t, top=SKY):
    bg_sky(cv, top, SKY2)
    cv.drawRect(skia.Rect.MakeLTRB(0, 250, W, 330), fill((245, 245, 250)))
    for i in range(0, W, 20):  # 관중석
        for j in range(3):
            c = [(250, 120, 140), (120, 160, 250), (250, 210, 90), (140, 220, 140)][(i // 20 + j) % 4]
            cv.drawPath(oval(i + 10 + (j % 2) * 10, 268 + j * 20, 8, 8), fill(c))
    cv.drawRect(skia.Rect.MakeLTRB(0, 330, W, H), fill((120, 205, 100)))
    for i in range(8):
        cv.drawRect(skia.Rect.MakeLTRB(i * 170, 330, i * 170 + 85, H), fill((130, 215, 110)))
    cv.drawLine(0, 350, W, 350, stroke(WHITE, 5))


def goal(cv, x, y, s=1.0, shake=0.0):
    cv.save()
    cv.translate(x + shake, y)
    cv.scale(s, s)
    for i in range(0, 161, 20):
        cv.drawLine(-60 + i * 0.3, -150 + i * 0.1, -60 + i * 0.3, 0, stroke((230, 230, 240), 2))
    for j in range(0, 151, 20):
        cv.drawLine(-60, -j, 0, -j, stroke((230, 230, 240), 2))
    cv.drawLine(0, 0, 0, -150, stroke(WHITE, 9))
    cv.drawLine(0, -150, -60, -150, stroke(WHITE, 9))
    cv.restore()


def ball(cv, x, y, r=16, rot=0.0):
    cv.save()
    cv.translate(x, y)
    cv.rotate(rot)
    blob(cv, oval(0, 0, r, r), WHITE, 3, oc=(90, 90, 100))
    for a in range(0, 360, 72):
        rr = math.radians(a)
        cv.drawPath(oval(math.cos(rr) * r * 0.6, math.sin(rr) * r * 0.6, r * 0.22, r * 0.22), fill(NAVY))
    cv.drawPath(oval(0, 0, r * 0.25, r * 0.25), fill(NAVY))
    cv.restore()


def bg_rays(cv, t, cols=((255, 214, 120), (255, 236, 170)), cx=W / 2, cy=H / 2):
    cv.drawRect(skia.Rect.MakeWH(W, H), fill(cols[1]))
    rays(cv, cx, cy, t, cols, n=18, speed=0.4)


def bg_polka(cv, t, base=(255, 228, 236), dot=(255, 245, 250)):
    cv.drawRect(skia.Rect.MakeWH(W, H), fill(base))
    for j in range(-1, 9):
        for i in range(-1, 15):
            x = i * 100 + (j % 2) * 50 + (t * 20) % 100
            y = j * 90 + (t * 12) % 90
            cv.drawPath(oval(x, y, 18, 18), fill(dot))


def logo(cv, x, y, s, t, t0=0.0, per=0.06):
    """주제가 로고 「힘내요! 데 제르비」 ─ 글자마다 색이 다른 통통 튀는 글씨."""
    top = "힘내요!"
    main = "데 제르비"
    cols = [(255, 90, 110), (255, 160, 40), (255, 210, 40), (90, 200, 100), (80, 160, 255), (170, 110, 240)]
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    for row, (word, size, yy) in enumerate(((top, 60, -80), (main, 120, 40))):
        w = text_w(word, size, TF_TITLE)
        xx = -w / 2
        for i, ch in enumerate(word):
            k = pop(t, t0 + (i + row * 4) * per, 0.4)
            cw = text_w(ch, size, TF_TITLE)
            if k > 0 and ch != " ":
                dy = math.sin(t * 6 + i) * 4
                cv.save()
                cv.translate(xx + cw / 2, yy + dy)
                cv.scale(k, k)
                col = cols[(i + row * 3) % len(cols)]
                text(cv, ch, 0, 0, size, col, TF_TITLE, align="center", outline=(80, 40, 60), ow=22)
                text(cv, ch, 0, 0, size, col, TF_TITLE, align="center", outline=WHITE, ow=10)
                text(cv, ch, 0, 0, size, col, TF_TITLE, align="center", grad=(lighter(col, 0.4), col))
                cv.restore()
            xx += cw
    cv.restore()


def star_iris(cv, k, cx=W / 2, cy=H / 2):
    """별 모양 화면 전환: k=0 이면 검은 화면, 1 이면 다 열림."""
    if k >= 1:
        return
    r = 1500 * ease_out(k)
    p = skia.Path()
    p.addRect(skia.Rect.MakeWH(W, H))
    p.addPath(star_path(cx, cy, r, r * 0.55, rot=-90 + k * 60))
    p.setFillType(skia.PathFillType.kEvenOdd)
    cv.drawPath(p, fill((255, 150, 190)))


def caption(cv, s, x, y, size=34, col=WHITE, oc=(60, 40, 70), a=255, align="center"):
    text(cv, s, x, y, size, col, align=align, outline=oc, ow=9, a=a)


def tag(cv, s, x, y, col=(255, 120, 160), size=28, a=255):
    w = text_w(s, size)
    cv.drawPath(rrect(x - w / 2 - 16, y - size - 6, x + w / 2 + 16, y + 10, 18), fill(col, a))
    cv.drawPath(rrect(x - w / 2 - 16, y - size - 6, x + w / 2 + 16, y + 10, 18), stroke(WHITE, 4, a))
    text(cv, s, x, y, size, WHITE, align="center", a=a)


def score_board(cv, x, y, left, right, sl, sr, k=1.0):
    if k <= 0:
        return
    cv.save()
    cv.translate(x, y)
    cv.scale(k, k)
    blob(cv, rrect(-320, -50, 320, 50, 26), (40, 50, 90), 5, oc=WHITE)
    text(cv, left, -200, 12, 32, WHITE, align="center")
    text(cv, right, 200, 12, 32, WHITE, align="center")
    text(cv, f"{sl} : {sr}", 0, 20, 52, YELLOW, TF_TITLE, align="center")
    cv.restore()


# ------------------------------------------------------------------ 0. 오프닝 주제가

class Opening(Scene):
    fade = False

    def setup(self):
        mus, self.lyr, L = render_song(["intro", "verse", "chorus", "outro"])
        self.bed(0, mus, 1.0)
        self.L = L
        self.bar = BEAT * 4
        self.t_title = 17 * self.bar + 0.1
        self.sfx(self.t_title, "twinkle", 0.6)
        e = self.say(self.t_title + 0.2, "title")
        self.dur = max(L + 0.2, e + 0.5)

    def draw(self, cv, t):
        b = t / self.bar
        beat = t / BEAT
        on = 1 - (beat % 1)  # 박자마다 1→0
        if b < 1:  # 인트로: 로고
            bg_rays(cv, t, ((255, 200, 120), (255, 232, 170)))
            sparkles(cv, t, W / 2, H / 2 - 20, 420, 18, seed=2)
            logo(cv, W / 2, 330, 1.0 + 0.03 * on, t, 0.05, 0.05)
        elif b < 3:  # 여기는 토트넘 마을
            bg_village(cv, t, pan=(t - self.bar) * 60)
            K.rooster(cv, 640, GROUND, 1.0, flap=on * 0.6, bob=bounce(beat, 1, 10), mood="happy",
                      blink=blink(t))
            logo(cv, 210, 120, 0.45, t, -5)
        elif b < 5:  # 까만 수염 감독님
            bg_polka(cv, t)
            k = pop(t, 3 * self.bar, 0.5)
            cv.save()
            cv.translate(640, GROUND + 40)
            cv.scale(k, k)
            K.person(cv, "dezerbi", 0, 0, 1.55, mood="happy" if (beat % 4) > 3 else "smile",
                     arms=(20, 150 + 10 * on), bob=bounce(beat, 1, 8), blink=blink(t))
            cv.restore()
            sparkles(cv, t, 640, 320, 330, 12, seed=5)
            tag(cv, "로베르토 데 제르비 감독", 640, 150, (60, 60, 90), 36, int(255 * min(1, k)))
            logo(cv, 210, 120, 0.45, t, -5)
        elif b < 9:  # 패스 패스 또 패스 / 골키퍼까지 돌려요
            bg_pitch(cv, t)
            goal(cv, 110, GROUND - 10, 1.0)
            xs = [1080, 820, 560, 260]
            keys = ["fernandes", "tonali", "vdv", "kinsky"]
            tl = t - 5 * self.bar
            # 공: 박자 2개마다 한 명씩 뒤로
            seg = [(0.0, 0), (0.8, 1), (1.6, 2), (2.4, 3)]
            bx, by, holder = xs[0] - 50, GROUND - 16, 0
            for i in range(3):
                s0, s1 = i * 0.8 + 0.2, i * 0.8 + 0.75
                if tl >= s1:
                    holder = i + 1
                elif tl >= s0:
                    k = (tl - s0) / (s1 - s0)
                    x0, x1 = xs[i] - 50, xs[i + 1] + 50
                    bx = x0 + (x1 - x0) * k
                    by = GROUND - 16 - math.sin(k * math.pi) * 120
                    holder = -1
            if holder >= 0:
                bx = xs[holder] - 50 if holder < 3 else xs[3] + 50
                by = GROUND - 16
            for i, (x, key) in enumerate(zip(xs, keys)):
                mood = "shock" if (key == "kinsky" and tl > 2.3) else "happy" if holder == i else "smile"
                K.person(cv, key, x, GROUND, 1.0, mood=mood, flip=True, arms=(20, 20) if key != "kinsky" else (150, 150),
                         bob=bounce(beat + i * 0.5, 1, 6), blink=blink(t, i))
            ball(cv, bx, by, 18, tl * 400)
            if tl > 2 * self.bar + 0.1:  # 데 제르비 엄지척
                k = pop(t, 7 * self.bar + 0.2, 0.4)
                cv.save()
                cv.translate(1150, GROUND + 40)
                cv.scale(k, k)
                K.person(cv, "dezerbi", 0, 0, 0.9, mood="happy", arms=(10, 170))
                cv.restore()
                tag(cv, "빌드업!", 1150, 300, (60, 60, 90), 32, int(255 * min(1, k)))
            if 2.4 < tl < 2 * self.bar + 1.5:
                caption(cv, "?!", 260, 290, 60, YELLOW)
        elif b < 17:  # 후렴
            bg_rays(cv, t, ((255, 170, 200), (255, 220, 235)), cy=420)
            draw_rainbow(cv, W / 2, 620, 560, 26, 200)
            tl = t - 9 * self.bar
            back = ["fernandes", "tonali", "gallagher", "vdv", "tosin", "mudryk"]
            for i, k_ in enumerate(back):
                x = 170 + i * 188
                if abs(x - 640) < 120:
                    continue
                K.person(cv, k_, x, GROUND - 40, 0.72, mood="happy" if int(beat) % 2 else "smile",
                         arms=(160, 20) if int(beat + i) % 2 else (20, 160), bob=bounce(beat + i * 0.25, 1, 10),
                         blink=blink(t, i))
            K.rooster(cv, 200, GROUND + 40, 1.0, ball=True, flap=on, bob=bounce(beat, 1, 6), mood="happy")
            final = tl > 6 * self.bar
            if final:  # 강등만은 안 돼요!
                def sign(cv_, hands):
                    ex, ey = hands[1]
                    ex += 40
                    cv_.drawLine(ex - 40, ey, ex, ey - 70, stroke((150, 100, 60), 7))
                    blob(cv_, rrect(ex - 70, ey - 150, ex + 70, ey - 70, 16), WHITE, 5, oc=(200, 40, 50))
                    text(cv_, "강등", ex, ey - 94, 38, (60, 40, 50), align="center")
                    cv_.drawPath(oval(ex, ey - 110, 44, 44), stroke((230, 40, 50), 8))
                    cv_.drawLine(ex - 30, ey - 80, ex + 30, ey - 140, stroke((230, 40, 50), 8))
                K.person(cv, "dezerbi", 640, GROUND + 60, 1.35, mood="angry" if tl < 7 * self.bar else "happy",
                         arms=(20, 125), bob=bounce(beat, 1, 6), prop=sign)
                if tl > 7 * self.bar:
                    k = pop(t, 16 * self.bar, 0.4)
                    cv.save()
                    cv.translate(1000, 250)
                    cv.scale(k, k)
                    burst(cv, 0, 0, 130, YELLOW, RED, 12, seed=4)
                    text(cv, "안 돼요!", 0, 16, 48, RED, TF_TITLE, align="center")
                    cv.restore()
            else:
                K.person(cv, "dezerbi", 640, GROUND + 60, 1.35, mood="happy" if int(beat) % 4 == 3 else "smile",
                         arms=(165, 20) if int(beat) % 2 else (20, 165), bob=bounce(beat, 1, 12), blink=blink(t))
            if 2 * self.bar + 5 * BEAT < tl < 4 * self.bar:  # 힘내요!
                k = pop(t, 11 * self.bar + 5 * BEAT, 0.3)
                cv.save()
                cv.translate(1000, 220)
                cv.scale(k, k)
                burst(cv, 0, 0, 120, (255, 240, 120), (255, 120, 60), 12, seed=2)
                text(cv, "힘내요!", 0, 16, 46, (255, 90, 60), TF_TITLE, align="center")
                cv.restore()
            sparkles(cv, t, 640, 300, 560, 16, seed=9)
        else:  # 아우트로 = 에피소드 제목
            TitleCard.draw(self, cv, t - self.t_title)
            logo(cv, 1080, 90, 0.4, t, -5)
            self.subtitles(cv, t)
        self.karaoke(cv, t)

    def karaoke(self, cv, t):
        cur = None
        for words, st, en, marks in self.lyr:
            if st - 0.35 <= t < en + 0.2:
                cur = (words, st, en, marks)
        if not cur:
            return
        words, st, en, marks = cur
        size = 50
        w = text_w(words, size)
        y = H - 40
        cv.drawPath(rrect(W / 2 - w / 2 - 30, y - size - 14, W / 2 + w / 2 + 30, y + 18, 30), fill(WHITE, 225))
        cv.drawPath(rrect(W / 2 - w / 2 - 30, y - size - 14, W / 2 + w / 2 + 30, y + 18, 30),
                    stroke((255, 120, 160), 5))
        x0 = W / 2 - w / 2
        text(cv, words, x0, y, size, (120, 110, 130))
        # 부른 만큼 색칠
        chars = list(words)
        idx = [i for i, ch in enumerate(chars) if ch != " "]
        fill_to = 0.0
        for k, (syl, s0, s1) in enumerate(marks):
            ci = idx[k]
            a = text_w(words[:ci], size)
            b = text_w(words[:ci + 1], size)
            if t >= s1:
                fill_to = b
            elif t >= s0:
                fill_to = a + (b - a) * min(1, (t - s0) / max(0.12, min(0.35, s1 - s0)))
        cv.save()
        cv.clipRect(skia.Rect.MakeLTRB(x0 - 5, y - size - 20, x0 + fill_to, y + 20))
        text(cv, words, x0, y, size, (255, 80, 130), outline=WHITE, ow=4)
        cv.restore()


# ------------------------------------------------------------------ 1. 에피소드 제목

class TitleCard(Scene):
    def draw(self, cv, t):
        bg_polka(cv, t, (200, 235, 255), (230, 246, 255))
        k = pop(t, 0.1, 0.5)
        cv.save()
        cv.translate(W / 2, 250)
        cv.scale(k, k)
        cv.rotate(math.sin(t * 3) * 3)
        blob(cv, star_path(0, 0, 150, 80), (255, 210, 70), 6, oc=(230, 130, 40))
        text(cv, "제 1화", 0, 22, 60, WHITE, TF_TITLE, align="center", outline=(230, 120, 40), ow=12)
        cv.restore()
        k2 = pop(t, 0.9, 0.5)
        if k2 > 0:
            cv.save()
            cv.translate(W / 2, 520)
            cv.scale(k2, k2)
            text(cv, "비싼 친구들이 왔어요!", 0, 0, 76, (255, 110, 150), TF_TITLE, align="center",
                 outline=WHITE, ow=16)
            cv.restore()
        K.person(cv, "dezerbi", 150, H + 110, 1.2, mood="happy", arms=(20, 160), bob=bounce(t, 1.5, 8),
                 talk=0)
        K.rooster(cv, 1130, H - 60, 1.0, flap=abs(math.sin(t * 8)), mood="happy")


# ------------------------------------------------------------------ 2. 지난 시즌

class Recap(Scene):
    def setup(self):
        e = self.say(0.3, "recap1")
        self.t_fall = e - 1.2
        self.sfx(self.t_fall, "fall", 0.7)
        e = self.say(e - 0.35, "hammer", who="hammer")
        self.sfx(e, "thud", 0.6)
        self.t_ok = e + 0.1
        e = self.say(self.t_ok, "recap2")
        self.sfx(e, "twinkle", 0.6)
        self.t_koko = e + 0.15
        e = self.say(self.t_koko, "recap3")
        self.bed(0, bgm("happy", e + 1, 2), 0.35)
        self.dur = e + 0.5

    def draw(self, cv, t):
        bg_village(cv, t * 0.3, pan=40)
        # 강등 구덩이
        cv.drawPath(oval(430, 655, 250, 60), fill((80, 50, 40)))
        cv.drawPath(oval(430, 660, 220, 44), fill((30, 20, 20)))
        cv.drawLine(170, 640, 170, 540, stroke((150, 100, 60), 8))
        blob(cv, rrect(90, 490, 260, 560, 12), (255, 240, 120), 4, oc=(200, 120, 40))
        text(cv, "강등 구덩이", 175, 537, 30, (200, 60, 50), align="center")
        # 망치(웨스트햄)가 빠진다
        if t < self.t_fall + 1.0:
            k = max(0.0, (t - self.t_fall) / 0.9)
            x = 560 - 110 * min(1, k * 1.5)
            y = 560 + 260 * k * k
            if y < 700:
                K.hammer(cv, x, y, 1.5, rot=k * 200 + (math.sin(t * 12) * 8 if k == 0 else 0), mood="shock")
                if k == 0:
                    caption(cv, "웨스트햄", 560, 440, 30, WHITE, (130, 40, 70))
        # 데 제르비가 마을(집)을 붙잡고 있다
        worried = t < self.t_ok
        K.person(cv, "dezerbi", 780, GROUND + 30, 1.1, mood="sweat" if worried else "happy",
                 talk=self.talk("dz", t), arms=(100, 100) if worried else (20, 160), blink=blink(t),
                 tilt=-8 if worried else 0, bob=0 if worried else bounce(t, 1.5, 6))
        if worried:
            for i in range(2):
                sweat(cv, 700 + i * 150, 330 + ((t * 80 + i * 40) % 60), 1.2)
        if t > self.t_koko - 0.2:
            k = pop(t, self.t_koko - 0.2, 0.45)
            cv.save()
            cv.translate(1080, GROUND + 30)
            cv.scale(k, k)
            K.rooster(cv, 0, 0, 1.1, talk=self.talk("koko", t), flap=abs(math.sin(t * 9)), mood="happy")
            cv.restore()
            cv.save()
            cv.translate(1080, 250)
            cv.scale(k, k)
            burst(cv, 0, 0, 90, YELLOW, ORANGE, 10, seed=7)
            text(cv, "17위", 0, 16, 46, RED, TF_TITLE, align="center")
            cv.restore()
            caption(cv, "2025-26 시즌 · 마지막 날 1-0 승리로 잔류", 640, 90, 34, WHITE, (60, 60, 120))


# ------------------------------------------------------------------ 3. 여름: 새 친구 버스

NEW = [("fernandes", "£85M"), ("tonali", "£92.5M"), ("savinho", "£75M"), ("vanhecke", "£52M"),
       ("robertson", "공짜"), ("senesi", "공짜"), ("mudryk", "임대"), ("marmoush", "임대"), ("tosin", "영입")]


class Summer(Scene):
    def setup(self):
        self.sfx(0.3, "bus_horn", 0.6)
        e = self.say(0.2, "summer")
        self.t_names = e + 0.1
        e = self.say(self.t_names, "names", marks=True)
        mk = self.lines[-1]["marks"]
        first = [mk[0][1], mk[1][1], mk[2][1], mk[3][1]]  # 페르난데스·토날리·사비뉴·반 헤케
        rest0 = mk[3][2] + 0.15
        self.pops = [self.t_names + x for x in first] + [self.t_names + rest0 + i * 0.16 for i in range(5)]
        for p in self.pops:
            self.sfx(p, "pop", 0.6)
        self.sfx(e - 0.3, "coins", 0.6)
        self.t_win = e + 0.15
        e = self.say(self.t_win, "win")
        self.sfx(self.t_win, "fanfare", 0.4)
        self.t_romero = self.t_win + 0.2
        self.sfx(self.t_romero, "plane", 0.5)
        self.bed(0, bgm("summer", e + 1, 3), 0.33)
        self.dur = max(e + 0.5, self.t_romero + 2.0)

    def draw(self, cv, t):
        bg_sky(cv, (100, 200, 255), (200, 240, 255))
        sun(cv, 1130, 100, t, 70)
        cv.drawRect(skia.Rect.MakeLTRB(0, 430, W, H), fill((150, 215, 120)))
        cv.drawRect(skia.Rect.MakeLTRB(0, 470, W, 560), fill((200, 200, 210)))  # 길
        for x in range(0, W, 120):
            cv.drawRect(skia.Rect.MakeLTRB(x + 20, 510, x + 80, 518), fill(WHITE))
        caption(cv, "☀ 2026 여름 이적시장", 230, 70, 38, WHITE, (230, 120, 60))
        # 버스
        k = ease_out(t / 2.0)
        bx = 1500 - (1500 - 330) * k
        K.bus(cv, bx, 545, 1.0, t=-bx / 300, door=min(1, max(0, (t - self.t_names + 0.3) / 0.3)),
              talk=0)
        # 선수들이 한 명씩 튀어나와 줄 선다
        for i, ((key, price), p) in enumerate(zip(NEW, self.pops)):
            if t < p:
                continue
            kk = min(1.0, (t - p) / 0.45)
            tx = 560 + (i % 5) * 150 - (0 if i < 5 else -75)
            ty = 430 if i < 5 else 600
            x = 230 + (tx - 230) * ease_out(kk)
            y = 520 + (ty - 520) * ease_out(kk) - math.sin(kk * math.pi) * 140
            won = t >= self.t_win
            K.person(cv, key, x, y, 0.62, mood="happy" if won else "smile", arms=(160, 160) if won else (20, 20),
                     bob=bounce(t + i * 0.2, 2, 6) if won else 0, blink=blink(t, i))
            if kk >= 1:
                tag(cv, price, x, y - 175, (255, 110, 150) if price.startswith("£") else (90, 170, 250), 22)
        if t >= self.t_win:
            k = pop(t, self.t_win, 0.4)
            cv.save()
            cv.translate(420, 610)
            cv.scale(k, k)
            K.person(cv, "dezerbi", 0, 0, 0.85, mood="happy", arms=(170, 170), talk=self.talk("dz", t),
                     bob=bounce(t, 2, 10))
            cv.restore()
            sparkles(cv, t, 420, 450, 150, 8, seed=4)
        if t >= self.t_romero:  # 로메로는 비행기로 마드리드행
            k = (t - self.t_romero) / 1.9
            px = 1450 - k * 1700
            py = 150 + k * 40
            blob(cv, rrect(px - 90, py - 26, px + 90, py + 26, 26), WHITE, 4, oc=(120, 130, 170))
            blob(cv, poly([(px - 20, py), (px + 30, py + 60), (px + 50, py)]), (120, 160, 230), 3)
            blob(cv, poly([(px - 90, py - 10), (px - 110, py - 50), (px - 70, py - 16)]), (120, 160, 230), 3)
            cv.drawPath(oval(px + 40, py - 4, 16, 14), fill((200, 230, 255)))
            cv.save()
            cv.translate(px + 40, py + 8)
            cv.scale(0.28, 0.28)
            K.person(cv, "romero", 0, 0, 1.0, mood="smile", arms=(20, 170))
            cv.restore()
            caption(cv, "주장 로메로는 아틀레티코로 떠났어요", px + 60, py - 46, 26, WHITE, (200, 60, 60))


# ------------------------------------------------------------------ 4. 개막전: 빌드업 변신

class Match1(Scene):
    def setup(self):
        e = self.say(0.2, "m1")
        self.sfx(1.2, "buzz", 0.6)
        self.t_bee = e + 0.1
        e = self.say(self.t_bee, "bee", who="bee")
        self.t_h = e + 0.1
        e = self.say(self.t_h, "henshin")
        self.t_tr = e
        self.sfx(self.t_tr, "henshin", 0.8)
        self.say(self.t_tr + 0.1, "henshin_kids")
        self.t_back = self.t_tr + 2.1
        e = self.say(self.t_back, "back")
        self.t_steal = e + 0.05
        e = self.say(self.t_steal, "thanks", who="bee")
        self.t_goal = e + 0.1
        for i in range(3):
            self.sfx(self.t_goal + i * 0.45, "goal_net", 0.6)
        self.t_res = self.t_goal + 1.4
        self.sfx(self.t_res, "sad_trombone", 0.7)
        e = self.t_res + 1.5
        self.bed(0, bgm("villain", self.t_h, 4), 0.3)
        self.bed(self.t_back, bgm("villain", self.t_res - self.t_back, 5), 0.3)
        self.dur = e + 0.3

    def draw(self, cv, t):
        if self.t_tr <= t < self.t_back:  # 변신 장면
            self.draw_henshin(cv, t - self.t_tr)
            return
        bg_pitch(cv, t, (255, 200, 150))
        caption(cv, "개막전 · 브렌트포드 원정", 250, 70, 34, WHITE, (40, 40, 90))
        goal(cv, 110, GROUND - 10, 1.0, shake=(math.sin(t * 60) * 6 if self.t_goal <= t < self.t_goal + 1.4 else 0))
        xs = [1000, 780, 560, 300]
        keys = ["fernandes", "tonali", "vdv", "kinsky"]
        bx, by = xs[0] - 40, GROUND - 16
        holder = 0
        tb = t - self.t_back
        if t >= self.t_back:
            for i in range(3):
                s0, s1 = 0.1 + i * 0.6, 0.55 + i * 0.6
                if tb >= s1:
                    holder = i + 1
                elif tb >= s0:
                    k = (tb - s0) / (s1 - s0)
                    x0, x1 = xs[i] - 40, xs[i + 1] + 40
                    bx = x0 + (x1 - x0) * k
                    by = GROUND - 16 - math.sin(k * math.pi) * 90
                    holder = -1
            if holder >= 0:
                bx = xs[holder] - 40 if holder < 3 else xs[3] + 40
        after = t >= self.t_back
        for i, (x, key) in enumerate(zip(xs, keys)):
            mood = "smile"
            if t >= self.t_steal and key == "kinsky":
                mood = "shock"
            if t >= self.t_goal:
                mood = "cry"
            K.person(cv, key, x, GROUND, 0.9, mood=mood, flip=True, kit="away", blink=blink(t, i),
                     arms=(150, 150) if key == "kinsky" else (20, 20))
        # 데 제르비(변신 후엔 망토)
        if after:
            self.dz_hero(cv, 1180, GROUND + 60, 0.85, t, mood="happy" if t < self.t_steal else "shock")
        else:
            K.person(cv, "dezerbi", 1180, GROUND + 60, 0.85, mood="worry" if t < self.t_h else "angry",
                     talk=self.talk("dz", t), arms=(20, 20) if t < self.t_h else (170, 30), flip=True)
        # 벌
        if t < self.t_steal:
            bxx = 1500 - 700 * ease_out((t - 1.0) / 1.2) if t < 3.0 else 800 + math.sin(t * 2) * 40
            if after:
                bxx = 650 - tb * 90
            K.bee(cv, bxx, 250 + math.sin(t * 5) * 20, 0.9, t, talk=self.talk("bee", t))
        else:  # 공을 가로채 골문으로
            k = min(1.0, (t - self.t_steal) / 0.9)
            bxx = 340 - 200 * k
            byy = 420 + 120 * k
            K.bee(cv, bxx, byy, 0.9, t, talk=self.talk("bee", t), mood="evil")
            bx, by = bxx - 30, byy + 20
        if t < self.t_goal + 0.2 or t >= self.t_goal + 1.5:
            ball(cv, bx, by, 16, t * 300)
        if t >= self.t_goal:
            n = min(3, int((t - self.t_goal) / 0.45) + 1)
            for i in range(n):
                k = pop(t, self.t_goal + i * 0.45, 0.3)
                cv.save()
                cv.translate(420 + i * 130, 270 + (i % 2) * 40)
                cv.scale(k, k)
                burst(cv, 0, 0, 70, YELLOW, RED, 10, seed=i)
                text(cv, "골!", 0, 14, 40, RED, TF_TITLE, align="center")
                cv.restore()
        if t >= self.t_res:
            score_board(cv, 640, 140, "브렌트포드", "토트넘", 3, 0, pop(t, self.t_res, 0.4))

    def dz_hero(self, cv, x, y, s, t, mood="happy"):
        def cape(cv_, hands):
            pass
        cv.save()
        cv.translate(x, y)
        cv.scale(s, s)
        wave = math.sin(t * 8) * 10
        blob(cv, smooth([(-34, -104), (34, -104), (60 + wave, -20), (0, -6), (-60 - wave, -20)]), (230, 40, 60),
             4)
        cv.restore()
        K.person(cv, "dezerbi", x, y, s, mood=mood, talk=self.talk("dz", t), arms=(160, 30), flip=True,
                 blink=blink(t))
        cv.save()
        cv.translate(x, y - 190 * s)
        cv.drawPath(rrect(-62 * s, -30 * s, 62 * s, -6 * s, 8), fill(YELLOW))
        text(cv, "빌드업", 0, -10 * s, 22 * s, RED, align="center")
        cv.restore()

    def draw_henshin(self, cv, k):
        bg_rays(cv, k * 3, ((255, 120, 180), (120, 200, 255)))
        for i in range(8):
            a = k * 5 + i * 0.8
            sparkle(cv, 640 + math.cos(a) * (200 + i * 20), 360 + math.sin(a) * (140 + i * 10), 20,
                    [WHITE, YELLOW, PINK][i % 3])
        spin = min(1.0, k / 1.15)
        cv.save()
        cv.translate(640, GROUND + 20)
        sx = math.cos(spin * math.pi * 4)
        cv.scale(sx if abs(sx) > 0.08 else 0.08, 1)
        cv.translate(-640, -(GROUND + 20))
        if k < 1.15:
            K.person(cv, "dezerbi", 640, GROUND + 20, 1.3, mood="happy", arms=(170, 170))
        else:
            self.dz_hero(cv, 640, GROUND + 20, 1.3, k)
        cv.restore()
        if k > 1.2:
            kk = pop(k, 1.2, 0.4)
            cv.save()
            cv.translate(640, 130)
            cv.scale(kk, kk)
            text(cv, "빌드업 모드!", 0, 0, 84, YELLOW, TF_TITLE, align="center", outline=(200, 40, 90), ow=16)
            cv.restore()


# ------------------------------------------------------------------ 5. 연패 몽타주

class Montage(Scene):
    def setup(self):
        e = self.say(0.2, "mont1", marks=True)
        mk = self.lines[-1]["marks"]
        # 까치 / 나무 / 에버튼 단어가 나오는 순간 카드가 뜬다
        find = lambda w: next((m[1] for m in mk if m[0].startswith(w)), None)
        self.cards = [0.2 + find("까치에게"), 0.2 + find("나무와"), 0.2 + find("에버튼과도")]
        for c, n in zip(self.cards, ("caw", "thud", "snore")):
            self.sfx(c, n, 0.5)
        self.t_lion = e + 0.15
        self.sfx(self.t_lion, "roar", 0.5)
        e = self.say(self.t_lion, "mont2")
        self.t_g1 = self.t_lion + 1.5
        self.t_g2 = self.t_lion + 2.1
        self.sfx(self.t_g1, "goal_net", 0.4)
        self.sfx(self.t_g2, "goal_net", 0.4)
        self.t_more = e + 0.05
        e = self.say(self.t_more, "more")
        self.t_end = e + 0.1
        self.sfx(self.t_end, "buzzer", 0.5)
        e = self.say(self.t_end + 0.1, "mont3")
        self.bed(0, bgm("villain", e + 1, 6), 0.28)
        self.dur = e + 0.5

    def draw(self, cv, t):
        bg_polka(cv, t, (230, 225, 255), (244, 240, 255))
        if t < self.t_lion:
            specs = [("까치(뉴캐슬)", "홈 · 0:2", K.magpie, (255, 240, 240)),
                     ("나무(포레스트)", "원정 · 0:0", K.tree, (240, 255, 240)),
                     ("에버튼", "홈 · 0:0", K.toffee, (235, 245, 255))]
            for i, (c0, (name, sc, fn, col)) in enumerate(zip(self.cards, specs)):
                if t < c0:
                    continue
                k = pop(t, c0, 0.45)
                x = 240 + i * 400
                cv.save()
                cv.translate(x, 360)
                cv.scale(k, k)
                cv.rotate([-4, 3, -2][i])
                blob(cv, rrect(-170, -220, 170, 200, 30), col, 6, oc=(150, 130, 190))
                if fn is K.tree:
                    fn(cv, 0, 110, 0.75, t)
                elif fn is K.magpie:
                    fn(cv, 0, 100, 1.0, t)
                else:
                    fn(cv, 0, 90, 1.4, t)
                text(cv, name, 0, -180, 32, (80, 60, 110), align="center")
                blob(cv, rrect(-120, 128, 120, 184, 20), WHITE, 4, oc=(150, 130, 190))
                text(cv, sc, 0, 168, 36, RED if "2" in sc else (80, 80, 120), TF_TITLE, align="center")
                cv.restore()
            if t > self.cards[2] + 0.8:
                caption(cv, "승점 2점…", 640, 110, 44, WHITE, (120, 80, 160))
        else:
            # 사자와의 결투
            bg_pitch(cv, t, (190, 170, 255))
            caption(cv, "빌라전", 150, 70, 36, WHITE, (130, 30, 60))
            K.lion(cv, 950, GROUND, 1.5, t, talk=0.3 if t > self.t_end else 0.0)
            sl = 0 + (t >= self.t_g1) + (t >= self.t_g2)
            score_board(cv, 640, 140, "토트넘", "아스톤 빌라", sl, 3, 1.0)
            K.person(cv, "gallagher", 300, GROUND, 0.9, mood="happy" if t >= self.t_g1 else "sweat",
                     arms=(170, 170) if t >= self.t_g1 else (20, 20), blink=blink(t, 1))
            K.person(cv, "vanhecke", 520, GROUND, 0.9, mood="happy" if t >= self.t_g2 else "sweat",
                     arms=(170, 170) if t >= self.t_g2 else (20, 20), blink=blink(t, 2))
            for tg, x in ((self.t_g1, 300), (self.t_g2, 520)):
                if tg <= t < tg + 1.2:
                    k = pop(t, tg, 0.3)
                    cv.save()
                    cv.translate(x, 290)
                    cv.scale(k, k)
                    burst(cv, 0, 0, 60, YELLOW, ORANGE, 10, seed=int(x))
                    text(cv, "골!", 0, 12, 34, RED, TF_TITLE, align="center")
                    cv.restore()
            K.person(cv, "dezerbi", 120, GROUND + 60, 0.85,
                     mood="cry" if t >= self.t_end else "angry" if t >= self.t_more else "sweat",
                     talk=self.talk("dz", t), arms=(170, 30) if self.t_more <= t < self.t_end else (20, 20))
            if t >= self.t_end:
                caption(cv, "5경기 승점 2 · 20위", 640, 290, 48, WHITE, (200, 40, 60))


# ------------------------------------------------------------------ 6. 퀴즈

class Quiz(Scene):
    def setup(self):
        self.sfx(0.1, "slide_up", 0.6)
        self.say(0.2, "quiz_kids")
        e = self.say(1.1, "quiz")
        self.t_opt = [e - 1.4, e - 0.9, e - 0.4]
        for x in self.t_opt:
            self.sfx(x, "pop", 0.6)
        self.t_tick = e + 0.1
        for i in range(3):
            self.sfx(self.t_tick + i * 0.28, "tick", 0.8)
        self.t_ans = self.t_tick + 0.85
        e = self.say(self.t_ans, "quiz_ans_kids")
        self.t_ding = e + 0.1
        self.sfx(self.t_ding, "dingdong", 0.5)
        e = self.say(self.t_ding + 0.05, "quiz_ans")
        self.t_yay = e + 0.05
        self.say(self.t_yay, "quiz_yay")
        self.sfx(self.t_yay, "clap_many", 0.7)
        self.sfx(self.t_yay, "cheer", 0.5)
        self.t_awk = self.t_yay + 1.1
        self.bed(0, bgm("quiz", self.t_ans, 7), 0.3)
        self.dur = self.t_awk + 0.7

    def draw(self, cv, t):
        bg_rays(cv, t * 0.5, ((120, 210, 255), (180, 235, 255)), cy=900)
        k = pop(t, 0.1, 0.5)
        cv.save()
        cv.translate(640, 110)
        cv.scale(k, k)
        text(cv, "퀴즈 타임!", 0, 0, 90, YELLOW, TF_TITLE, align="center", outline=(40, 90, 200), ow=18)
        cv.restore()
        if t > 1.1:
            caption(cv, "지금 토트넘은 몇 등일까요?", 640, 220, 50, WHITE, (40, 90, 200))
        opts = [("①", "1등", (255, 150, 150)), ("②", "10등", (150, 220, 150)), ("③", "20등", (255, 210, 110))]
        for i, (n, s, col) in enumerate(opts):
            if t < self.t_opt[i]:
                continue
            kk = pop(t, self.t_opt[i], 0.4)
            x = 300 + i * 340
            right = i == 2 and t >= self.t_ding
            cv.save()
            cv.translate(x, 390)
            cv.scale(kk * (1.12 if right else 1), kk * (1.12 if right else 1))
            blob(cv, rrect(-140, -80, 140, 80, 30), col if (not right or int(t * 6) % 2) else WHITE, 6,
                 oc=(90, 90, 140))
            text(cv, f"{n} {s}", 0, 22, 64, (70, 60, 90), TF_TITLE, align="center")
            cv.restore()
            if right:
                cv.drawPath(oval(x, 390, 170, 110), stroke(RED, 12))
        if self.t_tick <= t < self.t_ans:
            text(cv, str(3 - int((t - self.t_tick) / 0.28)), 640, 600, 70, RED, TF_TITLE, align="center",
                 outline=WHITE, ow=12)
        # 어린이 관객
        for i in range(5):
            x = 180 + i * 230
            cheer = self.t_yay <= t < self.t_awk
            K.villager(cv, i, x, H + 150, 0.9, mood="happy" if cheer else ("sweat" if t >= self.t_awk else "smile"),
                       arms=(170, 170) if cheer or (self.t_ans <= t < self.t_ans + 0.6) else (20, 20),
                       bob=bounce(t + i * 0.3, 3, 10) if cheer else 0, t=t)
        if t >= self.t_awk:
            caption(cv, "…어?", 640, 560, 60, WHITE, (90, 90, 120))
        if t >= self.t_yay:
            confetti(cv, t, seed=11, n=40, t0=self.t_yay)


# ------------------------------------------------------------------ 7. 화난 마을 사람들

class Angry(Scene):
    def setup(self):
        self.sfx(0.1, "crowd_boo", 0.6)
        e = self.say(0.2, "fans")
        self.t_sorry = e + 0.1
        e = self.say(self.t_sorry, "sorry")
        self.bed(0, bgm("angry", e + 1, 8), 0.28)
        self.dur = e + 0.5

    def draw(self, cv, t):
        bg_village(cv, t * 0.2, pan=200)
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((255, 60, 40), 40))
        caption(cv, "빌라전이 끝나고…", 200, 70, 38, WHITE, (150, 40, 40))
        signs = ["선수는 잔뜩 샀는데?!", "바뀐 게 없잖아!", "이번 시즌은 다르다며!", "20등 실화?"]
        for i, x in enumerate((170, 390, 890, 1110)):
            y = GROUND + 50
            b = bounce(t + i * 0.3, 2.5, 12)
            K.villager(cv, i, x, y, 0.95, mood="angry", talk=self.talk("fan", t) if i == 1 else 0,
                       arms=(20, 175), bob=b, t=t)
            s_ = signs[i]
            w = text_w(s_, 30)
            sy = y - 300 - b - (i % 2) * 56
            sx = min(max(x, w / 2 + 24), W - w / 2 - 24)
            blob(cv, rrect(sx - w / 2 - 14, sy - 34, sx + w / 2 + 14, sy + 16, 10), WHITE, 4, oc=(200, 60, 60),
                 shade=False)
            text(cv, s_, sx, sy + 6, 30, (200, 40, 40), align="center")
        K.person(cv, "dezerbi", 640, GROUND + 70, 1.15, mood="sweat", talk=self.talk("dz", t), arms=(60, 60),
                 blink=blink(t), tilt=math.sin(t * 20) * 2)
        for i in range(3):
            sweat(cv, 560 + i * 80, 330 + ((t * 90 + i * 30) % 70), 1.2)


# ------------------------------------------------------------------ 8. 밤: 영상통화

class Call(Scene):
    def setup(self):
        self.sfx(0.2, "ring", 0.6)
        e = 1.4
        self.t_open = e - 0.3
        self.sfx(self.t_open, "pop", 0.5)
        self.t_kane = e + 0.15
        e = self.say(self.t_kane, "kane")
        self.sfx(self.t_kane + 2.2, "twinkle", 0.5)
        self.t_son = e + 0.2
        e = self.say(self.t_son, "son")
        self.t_dz = e + 0.2
        e = self.say(self.t_dz, "together")
        self.bed(0, bgm("night", e + 1, 9), 0.5)
        self.dur = e + 0.5

    def draw(self, cv, t):
        bg_sky(cv, (30, 30, 80), (80, 70, 140))
        for i in range(30):
            rng = random.Random(i)
            x, y = rng.uniform(0, W), rng.uniform(0, 330)
            sparkle(cv, x, y, 3 + 3 * (math.sin(t * 3 + i) + 1), WHITE, 200)
        blob(cv, oval(1120, 110, 50, 50), (255, 245, 200), 0)
        cv.drawPath(oval(1140, 100, 44, 44), fill((30, 30, 80)))
        cv.drawRect(skia.Rect.MakeLTRB(0, 560, W, H), fill((70, 60, 110)))
        blob(cv, rrect(40, 470, 520, 620, 40), (160, 110, 190), 5)  # 소파
        K.person(cv, "dezerbi", 200, 640, 0.95, mood="sad" if t < self.t_dz else "smile", talk=self.talk("dz", t),
                 arms=(60, 60), blink=blink(t))
        K.rooster(cv, 390, 600, 0.9, mood="smile", talk=0, blink=blink(t, 3))
        # 태블릿 화면
        k = pop(t, self.t_open, 0.5)
        caption(cv, "그날 밤…", 180, 70, 40, WHITE, (60, 50, 120))
        if k <= 0:
            text(cv, "따르릉… 따르릉…", 900, 360, 50, WHITE, align="center")
            return
        cv.save()
        cv.translate(880, 330)
        cv.scale(k, k)
        blob(cv, rrect(-360, -250, 360, 230, 30), (40, 40, 50), 6, oc=(20, 20, 26))
        # 왼쪽: 뮌헨의 케인
        cv.save()
        cv.clipRect(skia.Rect.MakeLTRB(-340, -230, -4, 210))
        cv.drawRect(skia.Rect.MakeLTRB(-340, -230, -4, 210), linear((230, 40, 70), (255, 150, 150), 0, -230, 0, 210))
        text(cv, "뮌헨", -172, -186, 30, WHITE, align="center")
        # 트로피들
        blob(cv, oval(-300, 100, 32, 32), (230, 230, 240), 4, oc=(150, 150, 170))  # 분데스리가 접시
        blob(cv, rrect(-80, 40, -40, 110, 10), GOLD, 3)  # 포칼
        blob(cv, oval(-60, 36, 26, 20), GOLD, 3)
        gb = 1.0 if t > self.t_kane + 2.2 else 0.0
        if gb:
            kk = pop(t, self.t_kane + 2.2, 0.5)
            blob(cv, oval(-90, -110, 36 * kk, 36 * kk), GOLD, 4)
            sparkles(cv, t, -90, -110, 60, 6, seed=3)
            text(cv, "발롱도르?", -90, -52, 24, WHITE, align="center", outline=(160, 110, 0), ow=6)
        K.person(cv, "kane", -190, 250, 1.05, mood="happy" if self.talk("kane", t) < 0.05 else "smile",
                 talk=self.talk("kane", t), arms=(20, 160), blink=blink(t, 2))
        cv.restore()
        # 오른쪽: LA의 쏘니
        cv.save()
        cv.clipRect(skia.Rect.MakeLTRB(4, -230, 340, 210))
        cv.drawRect(skia.Rect.MakeLTRB(4, -230, 340, 210), linear((255, 170, 110), (170, 120, 200), 0, -230, 0, 210))
        text(cv, "LA", 172, -186, 30, WHITE, align="center")
        for px in (60, 300):  # 야자수
            cv.drawLine(px, 210, px + 10, -60, stroke((120, 80, 50), 10))
            for a in range(0, 360, 60):
                r = math.radians(a)
                cv.drawLine(px + 10, -60, px + 10 + math.cos(r) * 60, -60 + math.sin(r) * 30 + 20,
                            stroke((70, 160, 80), 10))
        cloud(cv, 110, -120, 0.8, 255, (150, 150, 170))
        for i in range(8):
            ry = ((t * 300 + i * 50) % 200) - 100
            cv.drawLine(120 + i * 16, ry, 116 + i * 16, ry + 14, stroke((120, 170, 255), 3))
        K.person(cv, "son", 172, 250, 1.05, mood="sad", talk=self.talk("son", t), arms=(20, 20), blink=blink(t, 5))
        text(cv, "10경기 1골", 172, 180, 26, WHITE, align="center", outline=(90, 60, 120), ow=6)
        cv.restore()
        cv.restore()
        if t >= self.t_dz:
            for i in range(3):
                h = heart_path(620 + i * 40, 250 - ((t - self.t_dz) * 60 + i * 30) % 120, 16)
                cv.drawPath(h, fill((255, 120, 150)))


# ------------------------------------------------------------------ 9. 오늘의 교훈

class Lesson(Scene):
    def setup(self):
        self.sfx(0.1, "chime_lesson", 0.6)
        e = self.say(0.4, "lesson", marks=True)
        mk = self.lines[-1]["marks"]
        self.t_l2 = 0.4 + next(m[1] for m in mk if m[0].startswith("잘"))
        self.t_kids = e + 0.1
        e = self.say(self.t_kids, "lesson_kids")
        self.bed(0, bgm("happy", e + 1, 10), 0.3)
        self.dur = e + 0.6

    def draw(self, cv, t):
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((255, 240, 200)))
        blob(cv, rrect(120, 60, 1160, 640, 30), (255, 253, 245), 6, oc=(220, 170, 110))
        for y in range(190, 620, 56):
            cv.drawLine(160, y, 1120, y, stroke((200, 220, 250), 3))
        cv.drawLine(230, 70, 230, 630, stroke((255, 170, 170), 3))
        k = pop(t, 0.2, 0.5)
        cv.save()
        cv.translate(640, 150)
        cv.scale(k, k)
        blob(cv, star_path(-230, -14, 44, 22), YELLOW, 4)
        blob(cv, star_path(230, -14, 44, 22), YELLOW, 4)
        text(cv, "오늘의 교훈", 0, 10, 70, (255, 110, 150), TF_TITLE, align="center", outline=WHITE, ow=12)
        cv.restore()
        if t > 1.2:
            text(cv, "비싼 장난감이 많다고", 640, 300, 64, (70, 60, 90), align="center")
        if t > self.t_l2:
            k2 = pop(t, self.t_l2, 0.4)
            cv.save()
            cv.translate(640, 400)
            cv.scale(k2, k2)
            text(cv, "잘 노는 건 아니에요!", 0, 0, 72, RED, TF_TITLE, align="center", outline=WHITE, ow=12)
            cv.restore()
        # 비싼 장난감 상자
        blob(cv, rrect(300, 470, 560, 600, 16), (190, 140, 90), 5)
        text(cv, "£300M", 430, 555, 40, WHITE, TF_TITLE, align="center")
        for i, (x, col) in enumerate(((330, RED), (400, SKY), (470, YELLOW), (530, PURPLE))):
            blob(cv, oval(x, 470 - (i % 2) * 14, 30, 30), col, 4)
        K.person(cv, "dezerbi", 880, 660, 0.9, mood="cry" if t > self.t_l2 else "sweat", blink=blink(t))
        if t >= self.t_kids:
            caption(cv, "네에~!", 1060, 470, 50, YELLOW, (230, 120, 40))


# ------------------------------------------------------------------ 10. 다음 이야기

class Preview(Scene):
    def setup(self):
        self.sfx(0.1, "thunder", 0.7)
        e = self.say(0.3, "next")
        e = self.say(e + 0.1, "next2")
        self.t_gulp = e + 0.1
        self.sfx(self.t_gulp, "gulp", 0.7)
        e = self.say(self.t_gulp + 0.05, "gulp")
        self.bed(0, bgm("tense", e + 1, 11), 0.5)
        self.dur = max(e, self.t_gulp + 0.8) + 0.4

    def draw(self, cv, t):
        flash = 0.1 < t < 0.25
        bg_sky(cv, (60, 10, 20) if not flash else (255, 255, 255), (140, 30, 40))
        # 올드 트래포드 성
        blob(cv, poly([(640, 520), (640, 300), (700, 250), (1260, 250), (1260, 520)]), (70, 20, 30), 5,
             oc=(30, 10, 10))
        for x in range(700, 1260, 80):
            cv.drawRect(skia.Rect.MakeLTRB(x, 230, x + 40, 260), fill((70, 20, 30)))
        K.devil(cv, 950, 470, 1.2, t)
        text(cv, "올드 트래포드", 950, 230, 40, WHITE, align="center", outline=(120, 20, 30), ow=8)
        cv.drawRect(skia.Rect.MakeLTRB(0, 520, W, H), fill((40, 20, 30)))
        k = pop(t, 0.3, 0.5)
        cv.save()
        cv.translate(300, 130)
        cv.scale(k, k)
        text(cv, "다음 이야기", 0, 0, 70, YELLOW, TF_TITLE, align="center", outline=(120, 20, 30), ow=14)
        text(cv, "10월 10일 · 맨유 원정", 0, 70, 40, WHITE, align="center", outline=(120, 20, 30), ow=8)
        cv.restore()
        shake = math.sin(t * 40) * 3
        K.person(cv, "dezerbi", 330 + shake, 680, 1.1, mood="shock" if t >= self.t_gulp else "worry",
                 talk=self.talk("dz", t), arms=(40, 40), blink=blink(t))


# ------------------------------------------------------------------ 11. 엔딩

class Ending(Scene):
    def setup(self):
        mus, self.lyr, L = render_song(["chorus_last", "outro"], shout=False)
        self.bed(0, mus, 0.9)
        self.t_bye = L - 0.9
        e = self.say(self.t_bye, "bye")
        self.say(e + 0.05, "bye_kids")
        self.dur = e + 1.3
        self.L = L

    def draw(self, cv, t):
        bg_sky(cv, (130, 210, 255), (220, 245, 255))
        draw_rainbow(cv, W / 2, 640, 600, 30)
        cv.drawPath(smooth([(-100, 600), (400, 520), (900, 540), (1400, 600), (1400, 800), (-100, 800)]),
                    fill(GRASS))
        beat = t / BEAT
        cast = ["tonali", "fernandes", "vdv", "dezerbi", "gallagher", "tosin", "mudryk"]
        for i, k in enumerate(cast):
            x = 130 + i * 170
            main = k == "dezerbi"
            K.person(cv, k, x, 650 if not main else 680, 0.8 if not main else 1.0, mood="happy",
                     arms=(20, 150 + 20 * math.sin(t * 8 + i)), bob=bounce(beat + i * 0.3, 1, 8), blink=blink(t, i))
        K.rooster(cv, 1210, 640, 0.8, flap=abs(math.sin(t * 8)), mood="happy")
        logo(cv, W / 2, 140, 0.6, t, -5)
        Opening.karaoke(self, cv, t)
        if t > self.t_bye:
            caption(cv, "다음에 또 만나요!", 640, 330, 70, YELLOW, (255, 110, 150))
            text(cv, "※ 2026.09.24 기준 실제 결과를 바탕으로 한 풍자 패러디입니다", 640, 400, 26, (60, 60, 90),
                 align="center", outline=WHITE, ow=6)

    def subtitles(self, cv, t):
        if t < self.L - 1.0:
            return
        Scene.subtitles(self, cv, t)


# ------------------------------------------------------------------ 조립 / 렌더

def build():
    return [Opening(), Recap(), Summer(), Match1(), Montage(), Quiz(), Angry(), Call(), Lesson(), Preview(),
            Ending()]


def frame(scenes, starts, t, surf):
    cv = surf.getCanvas()
    si = max(i for i, s in enumerate(starts) if t >= s)
    sc = scenes[si]
    lt = t - starts[si]
    cv.clear(C(WHITE))
    sc.draw(cv, lt)
    if not isinstance(sc, Opening):
        sc.subtitles(cv, lt)
    if sc.fade and si > 0:
        star_iris(cv, lt / 0.45)
    if si == len(scenes) - 1 and lt > sc.dur - 0.6:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(BLACK, int(255 * min(1, (lt - sc.dur + 0.6) / 0.6))))
    img = surf.makeImageSnapshot().toarray()
    return img[..., [2, 1, 0]]


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
        outdir = sys.argv[sys.argv.index("--preview") + 1] if len(sys.argv) > sys.argv.index("--preview") + 1 \
            else os.path.join(HERE, "_preview")
        os.makedirs(outdir, exist_ok=True)
        for i, (s, st) in enumerate(zip(scenes, starts)):
            for f in (0.25, 0.55, 0.85):
                t = st + s.dur * f
                Image.fromarray(frame(scenes, starts, t, surf)).save(os.path.join(outdir, f"s{i:02d}_{f:.2f}.png"))
        return
    mix_ = Mixer(total)
    for s, st in zip(scenes, starts):
        s.audio(mix_, st)
    buf = mix_.buf[: int(total * SR)]
    buf = np.tanh(buf * 1.2) / np.tanh(1.2)
    buf = buf / max(1e-9, np.max(np.abs(buf))) * 0.84
    wav_path = os.path.join(HERE, "_audio_kids.wav")
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((buf * 32767).astype(np.int16).tobytes())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen([ff, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-i", wav_path, "-c:v", "libx264", "-preset", "medium",
                             "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest",
                             "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for i in range(n):
        proc.stdin.write(np.ascontiguousarray(frame(scenes, starts, i / FPS, surf)).tobytes())
        if i % 240 == 0:
            print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(wav_path)
    print(f"wrote {OUT} ({total:.1f}s)")


if __name__ == "__main__":
    main()
