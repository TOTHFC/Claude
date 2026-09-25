"""「힘내요! 데 제르비」 ─ 토트넘 상황을 한국 아동 애니메이션처럼 만든 풍자 영상.

주인공: 로베르토 데 제르비 감독. 해설·대사는 일레븐랩스 캐릭터 음성(없으면 edge-tts),
주제가는 Suno 로 만든 「힘내요! 데 제르비」(song/theme_suno.mp3)를 쓴다. 1920x1080, 24fps.

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
                     sparkle, sparkles, star_path, stroke, sweat, text, text_w, glow, vignette)
from script import LINES, SPOKEN
from voice import _decode, envelope, tts, tts_marks

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tottenham_kids.mp4")
GROUND = 610
SCALE = 1.5  # 1280x720 좌표로 그리고 1920x1080 으로 출력
SONG = os.path.join(HERE, "song", "theme_suno.mp3")
SONG_BPM, SONG_PHASE = 157.0, 0.06
SONG_BEAT = 60 / SONG_BPM

SPEAKER = {  # 자막 이름표: (이름, 색)
    "nar": ("해설", (255, 120, 160)), "dz": ("데 제르비", (60, 60, 80)), "koko": ("꼬꼬", (230, 60, 60)),
    "kids": ("어린이들", (255, 160, 40)),
    "villain": ("악당", (120, 40, 140)), "fan": ("마을 청년", (40, 70, 160)),
    "fan2": ("마을 할아버지", (90, 110, 60)), "fan3": ("마을 아주머니", (200, 80, 130)),
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
        self.cur = 0.0
        self.loops = []
        self.setup()

    def line(self, lid, gap=0.55, t=None, who=None, marks=False):
        """앞 대사가 끝나고 gap 초 쉰 뒤(또는 t 초에) 대사를 넣는다. (시작, 끝) 을 돌려준다."""
        st = self.cur + gap if t is None else t
        en = self.say(st, lid, who, marks)
        self.cur = max(self.cur, en)
        return st, en

    def cam(self, t):
        """(확대, 초점 x, 초점 y). 기본은 장면 내내 천천히 다가가기."""
        return 1.0 + 0.045 * ease(t / max(1.0, self.dur)), W / 2, H / 2

    def say(self, t, lid, who=None, marks=False):
        role, txt, *rest = LINES[lid]
        emo = rest[0] if rest else None
        spoken = SPOKEN.get(lid, txt)  # 자막은 txt, 소리는 spoken
        if marks:
            a, mk = tts_marks(spoken, role, emo)
        else:
            a, mk = tts(spoken, role, emotion=emo), None
        self.lines.append(dict(t=t, id=lid, role=role, who=who or role, a=a, env=envelope(a, FPS), txt=txt,
                               end=t + len(a) / SR, marks=mk))
        return t + len(a) / SR

    bgm = None       # (배경음악 이름, 음량) ─ 같은 곡이 이어지는 장면은 끊기지 않고 계속된다
    duck_song = True

    def sfx(self, t, name, vol=1.0):
        self.sfxs.append((t, name, vol))

    def sfx_loop(self, t0, t1, name, vol=1.0):
        """t0~t1 동안 효과음을 이어 붙여 계속 틀기(벌 날갯짓, 밤 귀뚜라미 등)."""
        self.loops.append((t0, t1, name, vol))

    def bed(self, t, arr, vol=1.0):
        """노래처럼 통째로 까는 음원(음악 버스)."""
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

    def audio(self, voice, fx, music, t0):
        for ln in self.lines:
            voice.add(t0 + ln["t"], ln["a"], 1.0)
        for t, n, v in self.sfxs:
            fx.add(t0 + t, sfx_audio(n), v)
        for a_, b_, n, v in self.loops:
            fx.add(t0 + a_, sfx_loop_audio(n, b_ - a_), v)
        for t, a, v in self.beds:
            music.add(t0 + t, a, v)

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
    """방송 자막: 반투명 어두운 띠에 흰 글씨, 말하는 사람 이름은 색 글씨로."""
    size = 36
    w = text_w(s, size)
    while w > W - 160:
        size -= 2
        w = text_w(s, size)
    y = H - 30
    al = int(255 * a)
    cv.drawPath(rrect(W / 2 - w / 2 - 28, y - size - 14, W / 2 + w / 2 + 28, y + 14, 22), fill((20, 16, 32), int(165 * a)))
    text(cv, s, W / 2, y, size, WHITE, align="center", a=al)
    nw = text_w(name, 22)
    x0 = W / 2 - w / 2 - 20
    cv.drawPath(rrect(x0, y - size - 42, x0 + nw + 26, y - size - 12, 15), fill(col, al))
    text(cv, name, x0 + 13, y - size - 19, 22, WHITE, a=al)


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


# ------------------------------------------------------------------ 소리 자원(일레븐랩스로 만든 효과음·배경음악)

import json  # noqa: E402

from kengine import SFX as SYNTH_SFX  # noqa: E402

_SND = {}


def _active(a, thr=0.01):
    env = np.convolve(np.abs(a), np.ones(441) / 441, "same")
    idx = np.where(env > thr)[0]
    return (idx[0], idx[-1]) if len(idx) else (0, len(a))


def sfx_audio(name):
    """sfx/<name>.mp3 를 앞 무음을 자르고 소리 크기를 맞춰 돌려준다. 없으면 합성 효과음."""
    if name in _SND:
        return _SND[name]
    path = os.path.join(HERE, "sfx", f"{name}.mp3")
    if os.path.exists(path):
        a = _decode(path)
        s0, s1 = _active(a)
        a = a[max(0, s0 - 200):min(len(a), s1 + 4410)].copy()
        rms = np.sqrt(np.mean(a[: max(1, len(a))] ** 2)) + 1e-9
        a *= min(0.2 / rms, 0.9 / (np.abs(a).max() + 1e-9))
        fo = min(len(a), 2205)
        a[-fo:] *= np.linspace(1, 0, fo)
    else:
        a = SYNTH_SFX(name)
    _SND[name] = a.astype(np.float32)
    return _SND[name]


def sfx_loop_audio(name, dur, xf=0.3):
    """효과음을 겹쳐 이어 붙여 dur 초 길이로(앞뒤는 부드럽게)."""
    a = sfx_audio(name)
    n, x = int(dur * SR), int(xf * SR)
    out = a.copy()
    while len(out) < n:
        ramp = np.linspace(0, 1, min(x, len(a), len(out)))
        k = len(ramp)
        out[-k:] = out[-k:] * (1 - ramp) + a[:k] * ramp
        out = np.concatenate([out, a[k:]])
    out = out[:n].copy()
    f = min(len(out) // 3, int(0.4 * SR))
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out


def bgm_track(name):
    key = "bgm:" + name
    if key not in _SND:
        a = _decode(os.path.join(HERE, "bgm", f"{name}.mp3"))
        s0, s1 = _active(a, 0.005)
        a = a[s0:s1].copy()
        rms = np.sqrt(np.mean(a ** 2)) + 1e-9
        a *= 0.12 / rms
        _SND[key] = a.astype(np.float32)
    return _SND[key]


def bgm_segment(name, offset, dur, fade_in=0.6, fade_out=0.8):
    """배경음악을 offset 초부터 dur 초 길이로. 짧으면 1.5초 겹치며 이어 붙여 반복한다."""
    tr = bgm_track(name)
    xf = int(1.5 * SR)
    need = int((offset + dur) * SR) + 10
    out = tr.copy()
    while len(out) < need:
        nxt = tr.copy()
        ramp = np.linspace(0, 1, xf)
        out[-xf:] = out[-xf:] * (1 - ramp) + nxt[:xf] * ramp
        out = np.concatenate([out, nxt[xf:]])
    seg = out[int(offset * SR):int(offset * SR) + int(dur * SR)].copy()
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    if fi:
        seg[:fi] *= np.linspace(0, 1, fi)
    if fo:
        seg[-fo:] *= np.linspace(1, 0, fo)
    return seg


# ------------------------------------------------------------------ 주제가(Suno)

_SONG_CACHE = {}


def song_audio():
    if "a" not in _SONG_CACHE:
        a = _decode(SONG)
        _SONG_CACHE["a"] = a * (0.16 / (np.sqrt(np.mean(a[int(8 * SR):int(31 * SR)] ** 2)) + 1e-9))
    return _SONG_CACHE["a"]


def song_clip(t0, t1, fade_in=0.3, fade_out=0.8):
    a = song_audio()[int(t0 * SR):int(t1 * SR)].copy()
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    a[:fi] *= np.linspace(0, 1, fi)
    a[-fo:] *= np.linspace(1, 0, fo)
    return a


def song_beat(ts):
    return (ts - SONG_PHASE) / SONG_BEAT


# 보컬만 분리한 음원에서 음이 시작되는 순간을 재서 맞춘 음절 시각(노래 파일 기준, 초)
LYRICS = json.load(open(os.path.join(HERE, "song", "theme_suno_lyrics.json")))


def karaoke(cv, ts):
    cur = None
    for ln in LYRICS:
        if ln["syllables"][0][1] - 0.5 <= ts < ln["end"] + 0.35:
            cur = ln
    if not cur:
        return
    words, syl, end = cur["text"], cur["syllables"], cur["end"]
    size = 50
    w = text_w(words, size)
    y = H - 42
    a = min(1.0, (ts - syl[0][1] + 0.5) / 0.25, max(0.0, (end + 0.35 - ts) / 0.2))
    cv.drawPath(rrect(W / 2 - w / 2 - 34, y - size - 16, W / 2 + w / 2 + 34, y + 20, 32), fill(WHITE, int(232 * a)))
    cv.drawPath(rrect(W / 2 - w / 2 - 34, y - size - 16, W / 2 + w / 2 + 34, y + 20, 32),
                stroke((255, 120, 160), 5, int(255 * a)))
    x0 = W / 2 - w / 2
    text(cv, words, x0, y, size, (150, 140, 160), a=int(255 * a))
    idx = [i for i, ch in enumerate(words) if ch != " "]
    fill_to = 0.0
    for k, (ch, st) in enumerate(syl):
        nx = syl[k + 1][1] if k + 1 < len(syl) else end
        dur = max(0.08, min(nx - st, 0.35))  # 한 음절은 부르기 시작해서 0.35초 안에 다 칠한다
        ci = idx[k]
        xa, xb = text_w(words[:ci], size), text_w(words[:ci + 1], size)
        if ts >= st + dur:
            fill_to = xb
        elif ts >= st:
            fill_to = xa + (xb - xa) * (ts - st) / dur
    cv.save()
    cv.clipRect(skia.Rect.MakeLTRB(x0 - 5, y - size - 20, x0 + fill_to, y + 24))
    text(cv, words, x0, y, size, (255, 70, 130), outline=WHITE, ow=4, a=int(255 * a))
    cv.restore()


def cast_row(cv, t, keys, y, s, beat, mood="happy", dance=True, x0=170, dx=188, skip=None):
    for i, k in enumerate(keys):
        x = x0 + i * dx
        if skip and skip(x):
            continue
        b = int(beat + i * 0.5)
        K.person(cv, k, x, y, s, mood=mood if b % 2 else "smile",
                 arms=((160, 25) if b % 2 else (25, 160)) if dance else (20, 20),
                 bob=bounce(beat + i * 0.25, 1, 10) if dance else 0)


def league_table(cv, x, y, rows, hi, k=1.0, danger=17):
    """순위표: rows=[(순위, 팀)], hi=강조할 순위, danger 아래는 강등권(빨간 선)."""
    if k <= 0:
        return
    cv.save()
    cv.translate(x, y)
    cv.scale(k, k)
    h = 46 * len(rows) + 60
    blob(cv, rrect(-230, 0, 230, h, 24), (255, 255, 255), 5, oc=(60, 70, 120))
    text(cv, "2025-26 리그 순위", 0, 40, 30, (60, 70, 120), align="center")
    for i, (rk, team) in enumerate(rows):
        yy = 60 + i * 46
        if rk == hi:
            cv.drawPath(rrect(-214, yy, 214, yy + 42, 12), fill((255, 230, 120)))
        if rk > danger:
            cv.drawPath(rrect(-214, yy, 214, yy + 42, 12), fill((255, 200, 200), 180))
        text(cv, f"{rk}", -180, yy + 32, 28, (70, 60, 90), align="center")
        text(cv, team, -140, yy + 32, 28, (70, 60, 90))
        if rk == danger:
            cv.drawLine(-214, yy + 44, 214, yy + 44, stroke(RED, 4))
    cv.restore()


# ------------------------------------------------------------------ 0. 오프닝 주제가

class Opening(Scene):
    fade = False
    S0, S1 = 4.6, 33.6  # 노래에서 쓰는 구간(보컬은 8.55초에 시작)

    def setup(self):
        self.bed(0, song_clip(self.S0, self.S1, 0.5, 1.2), 1.0)
        self.dur = self.S1 - self.S0

    def cam(self, t):
        ts = t + self.S0
        if ts < 8.5:
            return 1.12 - 0.12 * ease_out((ts - self.S0) / 4.0), W / 2, H / 2 - 20
        if ts < 11.5:
            return 1.0 + 0.06 * ease((ts - 8.5) / 3.0), 640, 420
        if ts < 14.6:
            return 1.08 - 0.08 * ease_out((ts - 11.5) / 1.2), 640, 330
        if 29.6 <= ts < 31.7:
            return 1.0 + 0.08 * ease_out((ts - 29.6) / 0.5), 640, 380
        return 1.0 + 0.02 * math.sin(t * 0.8), W / 2, H / 2

    def draw(self, cv, t):
        ts = t + self.S0
        beat = song_beat(ts)
        on = 1 - (beat % 1)
        if ts < 8.45:  # 전주: 로고와 친구들
            bg_rays(cv, t, ((255, 196, 120), (255, 230, 170)))
            glow(cv, oval(W / 2, 320, 380, 170), (255, 250, 220), 60, 160)
            sparkles(cv, t, W / 2, H / 2 - 20, 460, 22, seed=2)
            logo(cv, W / 2, 300, 1.0 + 0.03 * on, t, 0.2, 0.06)
            for key, x, y, sc, t0, is_koko in (("dezerbi", 250, GROUND + 70, 1.15, 0.9, False),
                                               ("koko", 1040, GROUND + 50, 1.2, 1.4, True)):
                k = pop(t, t0, 0.5)
                if k > 0:
                    cv.save()
                    cv.translate(x, y)
                    cv.scale(k, k)
                    if is_koko:
                        K.rooster(cv, 0, 0, sc, ball=True, flap=on, mood="happy")
                    else:
                        K.person(cv, key, 0, 0, sc, mood="happy", arms=(20, 165), bob=bounce(beat, 1, 8))
                    cv.restore()
            for i, key in enumerate(("fernandes", "tonali", "vdv", "gallagher")):
                k = pop(t, 1.9 + i * 0.25, 0.4)
                if k > 0:
                    cv.save()
                    cv.translate(470 + i * 115, GROUND + 90)
                    cv.scale(k, k)
                    K.person(cv, key, 0, 0, 0.62, mood="happy", arms=(20, 160) if int(beat + i) % 2 else (160, 20),
                             bob=bounce(beat + i * 0.3, 1, 8))
                    cv.restore()
        elif ts < 11.5:  # 여기는 토트넘 마을
            bg_village(cv, t, pan=(ts - 8.45) * 55)
            K.rooster(cv, 640, GROUND, 1.0, flap=on * 0.6, bob=bounce(beat, 1, 10), mood="happy")
        elif ts < 14.6:  # 까만 수염 감독님
            bg_polka(cv, t)
            glow(cv, oval(640, 400, 260, 260), (255, 255, 255), 50, 200)
            k = pop(ts, 11.5, 0.5)
            cv.save()
            cv.translate(640, GROUND + 40)
            cv.scale(k, k)
            K.person(cv, "dezerbi", 0, 0, 1.55, mood="happy" if (beat % 4) > 3 else "smile",
                     arms=(20, 150 + 10 * on), bob=bounce(beat, 1, 8))
            cv.restore()
            sparkles(cv, t, 640, 320, 330, 14, seed=5)
            tag(cv, "로베르토 데 제르비 감독", 640, 140, (60, 60, 90), 36, int(255 * min(1, k)))
        elif ts < 20.4:  # 패스 패스 또 패스 / 골키퍼까지 돌려요
            bg_pitch(cv, t)
            goal(cv, 110, GROUND - 10, 1.0)
            xs = [1080, 820, 560, 260]
            keys = ["fernandes", "tonali", "vdv", "kinsky"]
            passes = [14.72, 15.11, 16.41]  # "패"를 부를 때마다 한 명씩 뒤로
            bx, by, holder = xs[0] - 50, GROUND - 16, 0
            for i, p0 in enumerate(passes):
                p1 = p0 + 0.36
                if ts >= p1:
                    holder = i + 1
                elif ts >= p0:
                    k = (ts - p0) / (p1 - p0)
                    x0, x1 = xs[i] - 50, xs[i + 1] + 50
                    bx = x0 + (x1 - x0) * ease(k)
                    by = GROUND - 16 - math.sin(k * math.pi) * 110
                    holder = -1
            if holder >= 0:
                bx = xs[holder] - 50 if holder < 3 else xs[3] + 50
                by = GROUND - 16
            for i, (x, key) in enumerate(zip(xs, keys)):
                mood = "shock" if (key == "kinsky" and ts > 17.5) else "happy" if holder == i else "smile"
                K.person(cv, key, x, GROUND, 1.0, mood=mood, flip=True,
                         arms=(20, 20) if key != "kinsky" else (150, 150), bob=bounce(beat + i * 0.5, 1, 6))
            ball(cv, bx, by, 18, ts * 400)
            if ts > 18.85:  # "돌려요"
                k = pop(ts, 18.85, 0.4)
                cv.save()
                cv.translate(1150, GROUND + 40)
                cv.scale(k, k)
                K.person(cv, "dezerbi", 0, 0, 0.9, mood="happy", arms=(10, 170))
                cv.restore()
                tag(cv, "빌드업!", 1150, 300, (60, 60, 90), 32, int(255 * min(1, k)))
            if 17.52 < ts < 20.3:
                caption(cv, "?!", 260, 290, 60, YELLOW)
        elif ts < 31.7:  # 후렴
            bg_rays(cv, t, ((255, 170, 200), (255, 222, 236)), cy=420)
            draw_rainbow(cv, W / 2, 620, 560, 26, 210)
            cast_row(cv, t, ["fernandes", "tonali", "gallagher", "vdv", "tosin", "mudryk"], GROUND - 40, 0.72,
                     beat, skip=lambda x: abs(x - 640) < 120)
            K.rooster(cv, 200, GROUND + 40, 1.0, ball=True, flap=on, bob=bounce(beat, 1, 6), mood="happy")
            if ts >= 29.6:  # 강등만은 안 돼요!
                def sign(cv_, hands):
                    ex, ey = hands[1]
                    ex += 40
                    cv_.drawLine(ex - 40, ey, ex, ey - 70, stroke((150, 100, 60), 7))
                    blob(cv_, rrect(ex - 70, ey - 150, ex + 70, ey - 70, 16), WHITE, 5, oc=(200, 40, 50))
                    text(cv_, "강등", ex, ey - 94, 38, (60, 40, 50), align="center")
                    cv_.drawPath(oval(ex, ey - 110, 44, 44), stroke((230, 40, 50), 8))
                    cv_.drawLine(ex - 30, ey - 80, ex + 30, ey - 140, stroke((230, 40, 50), 8))
                K.person(cv, "dezerbi", 640, GROUND + 60, 1.35, mood="angry" if ts < 30.6 else "happy",
                         arms=(20, 125), bob=bounce(beat, 1, 6), prop=sign)
                if ts > 30.62:  # "안 돼요"
                    k = pop(ts, 30.62, 0.35)
                    cv.save()
                    cv.translate(1000, 250)
                    cv.scale(k, k)
                    burst(cv, 0, 0, 130, YELLOW, RED, 12, seed=4)
                    text(cv, "안 돼요!", 0, 16, 48, RED, TF_TITLE, align="center")
                    cv.restore()
            else:
                K.person(cv, "dezerbi", 640, GROUND + 60, 1.35, mood="happy" if int(beat) % 4 == 3 else "smile",
                         arms=(165, 20) if int(beat) % 2 else (20, 165), bob=bounce(beat, 1, 12))
            if 24.42 <= ts < 25.9:  # "힘을 내요"
                k = pop(ts, 24.42, 0.3)
                cv.save()
                cv.translate(1000, 220)
                cv.scale(k, k)
                burst(cv, 0, 0, 120, (255, 240, 120), (255, 120, 60), 12, seed=2)
                text(cv, "힘내요!", 0, 16, 46, (255, 90, 60), TF_TITLE, align="center")
                cv.restore()
            sparkles(cv, t, 640, 300, 560, 16, seed=9)
        else:  # 마무리: 로고
            bg_rays(cv, t, ((150, 210, 255), (210, 236, 255)))
            confetti(cv, t, t0=31.7 - self.S0)
            logo(cv, W / 2, 330, 1.0 + 0.05 * on, ts, 31.7, 0.035)
        karaoke(cv, ts)


# ------------------------------------------------------------------ 1. 에피소드 제목

class TitleCard(Scene):
    bgm = ("village", 0.8)

    def setup(self):
        self.sfx(0.1, "boing", 0.6)
        self.sfx(0.15, "twinkle", 0.8)
        self.sfx(0.8, "slide", 0.4)
        _, e = self.line("title", t=0.7)
        self.dur = e + 1.0

    def draw(self, cv, t):
        bg_polka(cv, t, (200, 235, 255), (228, 245, 255))
        glow(cv, oval(W / 2, 250, 230, 200), (255, 255, 230), 50, 200)
        k = pop(t, 0.1, 0.6)
        cv.save()
        cv.translate(W / 2, 250)
        cv.scale(k, k)
        cv.rotate(math.sin(t * 2.5) * 4)
        blob(cv, star_path(0, 0, 160, 86), (255, 210, 70), 6, oc=(230, 130, 40))
        text(cv, "제 1화", 0, 24, 64, WHITE, TF_TITLE, align="center", outline=(230, 120, 40), ow=12)
        cv.restore()
        sparkles(cv, t, W / 2, 250, 260, 10, seed=12)
        title = "비싼 친구들이 왔어요!"
        w = text_w(title, 78, TF_TITLE)
        x = W / 2 - w / 2
        for i, ch in enumerate(title):
            kk = pop(t, 0.8 + i * 0.05, 0.4)
            cw = text_w(ch, 78, TF_TITLE)
            if kk > 0 and ch != " ":
                cv.save()
                cv.translate(x + cw / 2, 520 + math.sin(t * 5 + i * 0.6) * 4)
                cv.scale(kk, kk)
                text(cv, ch, 0, 0, 78, (255, 100, 150), TF_TITLE, align="center", outline=WHITE, ow=16)
                cv.restore()
            x += cw
        peek = ease_out((t - 0.4) / 0.8) * 150
        K.person(cv, "dezerbi", 150, H + 260 - peek, 1.2, mood="happy", arms=(20, 160 + 10 * math.sin(t * 6)))
        K.rooster(cv, 1130, H + 150 - peek * 0.9, 1.0, flap=abs(math.sin(t * 8)), mood="happy")


# ------------------------------------------------------------------ 2. 마을 소개

TABLE = [(17, "토트넘 · 승점 41"), (18, "웨스트햄")]


class Intro(Scene):
    bgm = ("village", 0.8)

    def setup(self):
        self.t1, e = self.line("intro1", t=0.9)
        self.t2, e = self.line("intro2", gap=0.6)
        self.sfx(self.t2 + 0.2, "whoosh", 0.7)
        self.t_drop = self.t2 + 2.2
        self.sfx(self.t_drop, "stamp", 0.8)
        self.t_koko = 1e9
        self.dur = max(e, self.t_drop + 0.6) + 1.0

    def cam(self, t):
        if t < self.t2:
            return 1.0 + 0.05 * ease(t / self.t2), 640, 420
        return 1.0, W / 2, H / 2

    def draw(self, cv, t):
        bg_village(cv, t * 0.4, pan=30 + t * 10)
        # 감독님과 선수들(마을 축구단)
        K.person(cv, "vdv", 250, GROUND + 20, 0.72, mood="smile", arms=(20, 20))
        K.person(cv, "kinsky", 360, GROUND + 30, 0.72, mood="smile", arms=(20, 20))
        K.person(cv, "dezerbi", 520, GROUND + 60, 1.0, mood="happy" if t < self.t2 else "sweat",
                 arms=(20, 160) if t < self.t2 else (40, 40))
        K.rooster(cv, 680, GROUND + 50, 0.9, talk=self.talk("koko", t), mood="happy" if t >= self.t_koko else "smile",
                  flap=abs(math.sin(t * 8)) if t >= self.t_koko else 0)
        if t >= self.t2:  # 순위표가 들어온다
            k = ease_out((t - self.t2) / 0.6)
            league_table(cv, 1300 - 330 * k, 150, TABLE, 17, 1.0, danger=17)
            if t >= self.t_drop:  # 웨스트햄은 강등
                stamp(cv, "강등", 1120, 262, t, self.t_drop, RED, 0.45)
                caption(cv, "토트넘은 간신히 잔류!", 970, 350, 34, WHITE, (60, 140, 60),
                        a=int(255 * min(1.0, (t - self.t_drop) / 0.4)))
        if t >= self.t_koko:
            sweat(cv, 720, 470 + ((t - self.t_koko) * 60) % 40, 1.2)


# ------------------------------------------------------------------ 3. 여름: 새 친구 버스

NEW = [("fernandes", "£85M"), ("tonali", "£92.5M"), ("savinho", "£75M"), ("vanhecke", "£52M"),
       ("robertson", "공짜"), ("senesi", "공짜"), ("mudryk", "임대"), ("marmoush", "임대"), ("tosin", "영입")]


class Summer(Scene):
    bgm = ("village", 0.8)

    def setup(self):
        self.sfx(0.2, "bus_drive", 0.7)
        self.sfx(1.9, "bus_horn", 0.7)
        self.line("summer", t=0.6)
        self.t_names, e = self.line("names", gap=0.6, marks=True)
        mk = self.lines[-1]["marks"]
        first = [mk[i][1] for i in range(4)]
        rest0 = mk[3][2] + 0.2
        self.pops = [self.t_names + x for x in first] + [self.t_names + rest0 + i * 0.2 for i in range(5)]
        self.sfx(self.t_names - 0.45, "bus_door", 0.7)
        for p in self.pops:
            self.sfx(p, "pop", 0.6)
            self.sfx(p + 0.5, "land", 0.5)
        self.sfx(e, "coins", 0.7)
        self.t_win, e = self.line("win", gap=0.8)
        self.sfx(self.t_win, "fanfare", 0.5)
        self.sfx(self.t_win + 0.1, "popper", 0.6)
        self.t_kwin, e = self.line("win_koko", gap=0.2)
        self.t_romero = 1e9
        self.dur = e + 1.2

    def cam(self, t):
        if t < self.t_win:
            return 1.0 + 0.04 * ease(t / self.t_win), 700, 420
        if t < self.t_romero:
            return 1.04 + 0.06 * ease_out((t - self.t_win) / 0.5), 330, 560
        return 1.0, W / 2, H / 2

    def draw(self, cv, t):
        bg_sky(cv, (100, 200, 255), (205, 242, 255))
        sun(cv, 1130, 100, t, 70)
        for i, (cx, cy) in enumerate(((200, 150), (700, 90))):
            cloud(cv, (cx + t * 15) % 1400 - 100, cy, 0.9)
        cv.drawRect(skia.Rect.MakeLTRB(0, 430, W, H), fill((150, 215, 120)))
        cv.drawRect(skia.Rect.MakeLTRB(0, 470, W, 560), fill((200, 200, 212)))
        for x in range(0, W, 120):
            cv.drawRect(skia.Rect.MakeLTRB(x + 20, 510, x + 80, 518), fill(WHITE))
        caption(cv, "2026 여름 이적시장", 210, 70, 38, WHITE, (230, 120, 60))
        k = ease_out((t - 0.3) / 2.2)
        bx = 1500 - (1500 - 330) * k
        K.bus(cv, bx, 545, 1.0, t=-bx / 300, door=min(1, max(0, (t - self.t_names + 0.4) / 0.4)))
        won = t >= self.t_win
        for i, ((key, price), p) in enumerate(zip(NEW, self.pops)):
            if t < p:
                continue
            kk = min(1.0, (t - p) / 0.5)
            tx = 560 + (i % 5) * 150 - (0 if i < 5 else -75)
            ty = 430 if i < 5 else 600
            x = 230 + (tx - 230) * ease_out(kk)
            y = 520 + (ty - 520) * ease_out(kk) - math.sin(kk * math.pi) * 150
            K.person(cv, key, x, y, 0.62, mood="happy" if won else "smile", arms=(160, 160) if won else (20, 20),
                     bob=bounce(t + i * 0.2, 2, 6) if won and t < self.t_romero else 0)
            if kk >= 1:
                a = int(255 * min(1, (t - p - 0.5) / 0.2))
                tag(cv, price, x, y - 175, (255, 110, 150) if price.startswith("£") else (90, 170, 250), 22, a)
        if won:
            k = pop(t, self.t_win, 0.4)
            cv.save()
            cv.translate(170, 700)
            cv.scale(k, k)
            K.person(cv, "dezerbi", 0, 0, 0.85, mood="happy" if t < self.t_romero else "shock",
                     arms=(170, 170) if t < self.t_romero else (40, 40), talk=self.talk("dz", t),
                     bob=bounce(t, 2, 10) if t < self.t_romero else 0)
            cv.restore()
            K.rooster(cv, 330, 700, 0.75, talk=self.talk("koko", t), flap=abs(math.sin(t * 9)) if t < self.t_romero
                      else 0, mood="happy" if t < self.t_romero else "shock")
            if t < self.t_romero:
                sparkles(cv, t, 200, 520, 150, 8, seed=4)



def stamp(cv, s, x, y, t, t0, col=RED, sc=1.0):
    if t < t0:
        return
    k = (1 + 1.2 * max(0.0, 1 - (t - t0) / 0.18)) * sc
    cv.save()
    cv.translate(x, y)
    cv.rotate(-8)
    cv.scale(k, k)
    w = max(240, text_w(s, 60, TF_TITLE) + 60)
    blob(cv, rrect(-w / 2, -50, w / 2, 40, 18), WHITE, 7, oc=col, shade=False)
    text(cv, s, 0, 18, 60, col, TF_TITLE, align="center")
    cv.restore()


# ------------------------------------------------------------------ 4. 개막전: 빌드업 변신

class Match1(Scene):
    bgm = ("match", 0.75)

    def setup(self):
        _, e = self.line("m1", t=0.8)
        self.t_bee, e = self.line("bee", gap=0.4, who="bee")
        self.t_h, e = self.line("henshin", gap=0.6)
        self.t_tr = e + 0.1
        self.sfx(self.t_tr, "henshin", 0.9)
        self.line("henshin_kids", t=self.t_tr + 0.4)
        self.t_back = self.t_tr + 2.4
        self.cur = self.t_back
        self.line("back", t=self.t_back + 0.2)
        self.t_pass = self.t_back
        for i in range(3):
            self.sfx(self.t_pass + 0.2 + i * 0.7, "kick", 0.8)
        self.t_steal = self.t_back + 2.2
        self.sfx(self.t_steal, "whoosh", 0.7)
        self.line("thanks", t=self.t_steal + 0.1, who="bee")
        self.t_goal = self.t_steal + 1.2
        for i in range(3):
            self.sfx(self.t_goal + i * 0.55, "goal_net", 0.8)
        self.t_res = self.t_goal + 1.8
        self.sfx(self.t_res, "sad_trombone", 0.8)
        self.cur = self.t_res
        _, e = self.line("m1r", gap=0.3)
        self.dur = e + 1.0
        # 벌이 화면에 있는 동안 위잉~ 날갯짓 (변신 장면에서는 쉼)
        self.sfx_loop(1.2, self.t_tr, "bee_fly", 0.5)
        self.sfx_loop(self.t_back, self.t_res, "bee_fly", 0.45)
        self.sfx(self.t_tr + 1.25, "twinkle", 0.7)

    def cam(self, t):
        if self.t_tr <= t < self.t_back:
            return 1.0 + 0.05 * (t - self.t_tr) / 2.4, W / 2, H / 2
        if self.t_bee <= t < self.t_h:
            return 1.12, 800, 330
        if self.t_h <= t < self.t_tr:
            return 1.12, 1080, 470
        if self.t_goal <= t < self.t_res:
            return 1.06 + math.sin(t * 50) * 0.004, 400, 450
        return 1.0 + 0.03 * ease(t / self.dur), W / 2, H / 2

    def draw(self, cv, t):
        if self.t_tr <= t < self.t_back:
            self.draw_henshin(cv, t - self.t_tr)
            return
        bg_pitch(cv, t, (255, 200, 150))
        caption(cv, "개막전 · 브렌트포드 원정", 250, 70, 34, WHITE, (40, 40, 90))
        shake = math.sin(t * 60) * 6 if self.t_goal <= t < self.t_goal + 1.6 else 0
        goal(cv, 110, GROUND - 10, 1.0, shake=shake)
        xs = [1000, 780, 560, 300]
        keys = ["fernandes", "tonali", "vdv", "kinsky"]
        bx, by, holder = xs[0] - 40, GROUND - 16, 0
        if t >= self.t_pass:
            tb = t - self.t_pass
            for i in range(3):
                s0, s1 = 0.2 + i * 0.7, 0.75 + i * 0.7
                if tb >= s1:
                    holder = i + 1
                elif tb >= s0:
                    k = (tb - s0) / (s1 - s0)
                    x0, x1 = xs[i] - 40, xs[i + 1] + 40
                    bx = x0 + (x1 - x0) * ease(k)
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
            K.person(cv, key, x, GROUND, 0.9, mood=mood, flip=True, kit="away",
                     arms=(150, 150) if key == "kinsky" else (20, 20))
        if after:
            self.dz_hero(cv, 1180, GROUND + 60, 0.85, t, mood="happy" if t < self.t_steal else "shock")
        else:
            K.person(cv, "dezerbi", 1180, GROUND + 60, 0.85, mood="worry" if t < self.t_h else "happy",
                     talk=self.talk("dz", t), arms=(20, 20) if t < self.t_h else (170, 30), flip=True)
        if t < self.t_steal:
            if t < 3.0:
                bxx = 1500 - 700 * ease_out((t - 1.4) / 1.4)
            else:
                bxx = 800 + math.sin(t * 2) * 40
            if after:
                bxx = 650 - (t - self.t_back) * 110
            K.bee(cv, bxx, 250 + math.sin(t * 5) * 20, 0.9, t, talk=self.talk("bee", t))
        else:
            k = min(1.0, (t - self.t_steal) / 1.1)
            bxx = 340 - 200 * ease(k)
            byy = 420 + 120 * ease(k)
            K.bee(cv, bxx, byy, 0.9, t, talk=self.talk("bee", t), mood="evil")
            bx, by = bxx - 30, byy + 20
        if t < self.t_goal + 0.2 or t >= self.t_goal + 1.8:
            ball(cv, bx, by, 16, t * 300)
        if t >= self.t_goal:
            n = min(3, int((t - self.t_goal) / 0.55) + 1)
            for i in range(n):
                k = pop(t, self.t_goal + i * 0.55, 0.3)
                cv.save()
                cv.translate(420 + i * 130, 270 + (i % 2) * 40)
                cv.scale(k, k)
                burst(cv, 0, 0, 70, YELLOW, RED, 10, seed=i)
                text(cv, "골!", 0, 14, 40, RED, TF_TITLE, align="center")
                cv.restore()
        if t >= self.t_res:
            score_board(cv, 640, 140, "브렌트포드", "토트넘", 3, 0, pop(t, self.t_res, 0.4))

    def dz_hero(self, cv, x, y, s, t, mood="happy"):
        cv.save()
        cv.translate(x, y)
        cv.scale(s, s)
        wave = math.sin(t * 8) * 10
        blob(cv, smooth([(-34, -104), (34, -104), (60 + wave, -20), (0, -6), (-60 - wave, -20)]), (230, 40, 60), 4)
        cv.restore()
        K.person(cv, "dezerbi", x, y, s, mood=mood, talk=self.talk("dz", t), arms=(160, 30), flip=True)
        cv.save()
        cv.translate(x, y - 190 * s)
        cv.drawPath(rrect(-62 * s, -30 * s, 62 * s, -6 * s, 8), fill(YELLOW))
        text(cv, "빌드업", 0, -10 * s, 22 * s, RED, align="center")
        cv.restore()

    def draw_henshin(self, cv, k):
        bg_rays(cv, k * 3, ((255, 120, 180), (120, 200, 255)))
        glow(cv, oval(640, 400, 200 + k * 60, 200 + k * 60), (255, 255, 255), 60, int(120 + 100 * min(1, k)))
        for i in range(10):
            a = k * 5 + i * 0.63
            sparkle(cv, 640 + math.cos(a) * (220 + i * 18), 380 + math.sin(a) * (150 + i * 10), 22,
                    [WHITE, YELLOW, PINK][i % 3])
        spin = min(1.0, k / 1.2)
        cv.save()
        cv.translate(640, GROUND + 20)
        sx = math.cos(spin * math.pi * 4)
        cv.scale(sx if abs(sx) > 0.08 else 0.08, 1)
        cv.translate(-640, -(GROUND + 20))
        if k < 1.2:
            K.person(cv, "dezerbi", 640, GROUND + 20, 1.3, mood="happy", arms=(170, 170))
        else:
            self.dz_hero(cv, 640, GROUND + 20, 1.3, k)
        cv.restore()
        if k > 1.25:
            kk = pop(k, 1.25, 0.4)
            cv.save()
            cv.translate(640, 130)
            cv.scale(kk, kk)
            text(cv, "빌드업 모드!", 0, 0, 84, YELLOW, TF_TITLE, align="center", outline=(200, 40, 90), ow=16)
            cv.restore()


# ------------------------------------------------------------------ 5. 연패

class Montage(Scene):
    bgm = ("montage", 0.7)

    def setup(self):
        self.ta, e = self.line("mont_a", t=0.7)
        self.sfx(self.ta - 0.1, "wings", 0.7)
        self.sfx(self.ta + 0.3, "caw", 0.6)
        self.sa = e + 0.05
        self.sfx(self.sa, "stamp", 0.8)
        self.tb, e = self.line("mont_b", gap=0.9)
        self.sfx(self.tb - 0.5, "transition", 0.6)
        for i in range(2):
            self.sfx(self.tb + 0.1 + i * 0.7, "kick", 0.7)
            self.sfx(self.tb + 0.55 + i * 0.7, "boing", 0.9)
        self.sb = e + 0.35
        self.sfx(self.sb, "stamp", 0.8)
        self.tc, e = self.line("mont_c", gap=0.9)
        self.sfx(self.tc - 0.5, "transition", 0.6)
        self.sfx(self.tc + 0.2, "snore", 0.7)
        self.sc = e + 0.05
        self.sfx(self.sc, "stamp", 0.8)
        self.tv, e = self.line("mont2", gap=1.0)
        self.sfx(self.tv - 0.6, "transition", 0.6)
        self.sfx(self.tv, "roar", 0.7)
        self.g1, self.g2 = self.tv + 1.2, self.tv + 2.1
        self.sfx(self.g1 - 0.25, "kick", 0.7)
        self.sfx(self.g2 - 0.25, "kick", 0.7)
        self.sfx(self.g1, "goal_net", 0.7)
        self.sfx(self.g2, "goal_net", 0.7)
        self.t_more, e = self.line("more", gap=0.3)
        self.t_end = e + 0.5
        self.sfx(self.t_end, "whistle", 0.8)
        self.cur = self.t_end + 0.6
        _, e = self.line("mont3", gap=0.0)
        self.t_tab = e + 0.2
        self.sfx(self.t_tab, "sad_trombone", 0.6)
        self.dur = self.t_tab + 2.0

    def cam(self, t):
        for t0 in (self.ta, self.tb, self.tc):
            if t0 - 0.6 <= t < t0 + 3.4:
                return 1.0 + 0.05 * ease((t - t0 + 0.6) / 4.0), W / 2, H / 2
        if t >= self.t_end:
            return 1.0 + 0.05 * ease((t - self.t_end) / 2), 640, 360
        return 1.0 + 0.03 * math.sin(t * 0.5), W / 2, H / 2

    def slide(self, cv, t, t_in):
        k = ease_out((t - t_in) / 0.45)
        cv.translate((1 - k) * W, 0)

    def draw(self, cv, t):
        if t < self.tb - 0.5:
            self.vignette_a(cv, t)
        elif t < self.tc - 0.5:
            cv.save()
            self.slide(cv, t, self.tb - 0.5)
            self.vignette_b(cv, t)
            cv.restore()
        elif t < self.tv - 0.6:
            cv.save()
            self.slide(cv, t, self.tc - 0.5)
            self.vignette_c(cv, t)
            cv.restore()
        else:
            cv.save()
            self.slide(cv, t, self.tv - 0.6)
            self.villa(cv, t)
            cv.restore()

    def calendar(self, cv, t):  # "그다음 경기도 마찬가지였어요" ─ 달력이 넘어간다
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((236, 230, 252)))
        blob(cv, rrect(440, 150, 840, 560, 30), WHITE, 6, oc=(150, 130, 190))
        cv.drawRect(skia.Rect.MakeLTRB(446, 156, 834, 250), fill((255, 110, 150)))
        text(cv, "2026년 8~9월", 640, 222, 44, WHITE, TF_TITLE, align="center")
        for i in range(5):
            x = 500 + (i % 3) * 120
            y = 320 + (i // 3) * 120
            k = pop(t, 0.9 + i * 0.25, 0.3)
            if k > 0:
                cv.save()
                cv.translate(x + 40, y)
                cv.scale(k, k)
                text(cv, ["패", "패", "무", "무", "패"][i], 0, 16, 56, RED if i in (0, 1, 4) else (90, 90, 130),
                     TF_TITLE, align="center")
                cv.restore()
        K.person(cv, "dezerbi", 1040, GROUND + 60, 0.95, mood="sweat", arms=(40, 40))

    def vignette_a(self, cv, t):
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((236, 236, 242)))
        for i in range(0, W, 80):
            cv.drawRect(skia.Rect.MakeLTRB(i, 0, i + 40, H), fill((222, 222, 232)))
        caption(cv, "2라운드 · 뉴캐슬(홈)", 230, 70, 34, WHITE, (40, 40, 60))
        K.person(cv, "tonali", 360, GROUND + 30, 1.0, mood="sweat", arms=(60, 20))
        K.person(cv, "dezerbi", 150, GROUND + 50, 0.85, mood="worry")
        k = ease_out((t - self.ta) / 1.6)
        mx = 1300 - 480 * k + math.sin(t * 4) * 10
        my = 330 - 60 * math.sin(k * 3.1)
        K.magpie(cv, mx, my, 1.3, t, bag=True)
        if t > self.ta + 0.5:
            caption(cv, "토날리 이적료로 배부른 까치", mx, my - 190, 26, WHITE, (40, 40, 60))
        stamp(cv, "0 : 2", 640, 200, t, self.sa)

    def vignette_b(self, cv, t):
        bg_pitch(cv, t, (190, 230, 190))
        caption(cv, "3라운드 · 노팅엄 포레스트(원정)", 290, 70, 34, WHITE, (40, 90, 40))
        K.tree(cv, 1000, GROUND + 20, 1.1, t)
        K.person(cv, "fernandes", 380, GROUND, 0.95, mood="angry", kit="away", arms=(20, 60))
        K.person(cv, "mudryk", 200, GROUND, 0.85, mood="sweat", kit="away")
        for i in range(2):
            s0 = self.tb + 0.1 + i * 0.7
            if s0 <= t < s0 + 0.7:
                k = (t - s0) / 0.7
                x = 430 + (900 - 430) * min(1, k * 1.6) - max(0, k - 0.62) * 900
                y = GROUND - 30 - math.sin(min(1, k) * math.pi) * 180
                ball(cv, x, y, 16, t * 500)
                if 0.55 < k < 0.8:
                    burst(cv, 900, GROUND - 120, 40, YELLOW, ORANGE, 8, seed=i)
        stamp(cv, "0 : 0", 640, 200, t, self.sb, (60, 120, 60))

    def vignette_c(self, cv, t):
        bg_sky(cv, (150, 160, 230), (210, 215, 250))
        caption(cv, "4라운드 · 에버튼(홈)", 230, 70, 34, WHITE, (60, 60, 140))
        cv.drawRect(skia.Rect.MakeLTRB(0, 520, W, H), fill((120, 190, 110)))
        K.toffee(cv, 950, GROUND, 1.8, t)
        for i, key in enumerate(("vanhecke", "gallagher", "dezerbi")):
            x = 200 + i * 190
            K.person(cv, key, x, GROUND + (40 if key == "dezerbi" else 0), 0.85, mood="happy", blink=True,
                     tilt=8 + math.sin(t * 1.5 + i) * 3)
        for i in range(6):
            z = (t * 0.6 + i / 6) % 1
            text(cv, "Z", 300 + (i % 3) * 190 + z * 40, 360 - z * 140, 30 + z * 20, (90, 90, 160),
                 a=int(255 * (1 - z)))
            text(cv, "z", 900 + z * 50, 330 - z * 150, 26 + z * 20, (90, 90, 160), a=int(255 * (1 - z)))
        stamp(cv, "0 : 0", 640, 200, t, self.sc, (80, 80, 160))

    def villa(self, cv, t):
        bg_pitch(cv, t, (190, 170, 255))
        caption(cv, "5라운드 · 아스톤 빌라(홈)", 250, 70, 34, WHITE, (130, 30, 60))
        K.lion(cv, 980, GROUND, 1.5, t, talk=0.35 if t > self.t_end else 0.0)
        sl = (t >= self.g1) + (t >= self.g2)
        score_board(cv, 640, 150, "토트넘", "아스톤 빌라", sl, 3, 1.0)
        K.person(cv, "gallagher", 330, GROUND, 0.9, mood="happy" if t >= self.g1 else "sweat",
                 arms=(170, 170) if t >= self.g1 else (20, 20))
        K.person(cv, "vanhecke", 550, GROUND, 0.9, mood="happy" if t >= self.g2 else "sweat",
                 arms=(170, 170) if t >= self.g2 else (20, 20))
        for tg, x in ((self.g1, 330), (self.g2, 550)):
            if tg <= t < tg + 1.2:
                k = pop(t, tg, 0.3)
                cv.save()
                cv.translate(x, 300)
                cv.scale(k, k)
                burst(cv, 0, 0, 60, YELLOW, ORANGE, 10, seed=int(x))
                text(cv, "골!", 0, 12, 34, RED, TF_TITLE, align="center")
                cv.restore()
        K.person(cv, "dezerbi", 130, GROUND + 60, 0.85,
                 mood="cry" if t >= self.t_end else "happy" if t >= self.t_more else "sweat",
                 talk=self.talk("dz", t), arms=(170, 30) if self.t_more <= t < self.t_end else (20, 20))
        if t >= self.t_tab:
            k = pop(t, self.t_tab, 0.5)
            cv.save()
            cv.translate(640, 330)
            cv.scale(k, k)
            blob(cv, rrect(-300, -70, 300, 70, 30), (40, 30, 60), 6, oc=WHITE)
            text(cv, "5경기 승점 2 · 20위", 0, 18, 52, YELLOW, TF_TITLE, align="center")
            cv.restore()


# ------------------------------------------------------------------ 6. 퀴즈

class Quiz(Scene):
    bgm = ("quiz", 0.75)

    def setup(self):
        self.sfx(0.2, "slide", 0.6)
        self.line("quiz_kids", t=0.4)
        _, e = self.line("quiz", gap=0.5)
        self.t_opt = [e + 0.1, e + 0.5, e + 0.9]
        for x in self.t_opt:
            self.sfx(x, "pop", 0.7)
        self.t_tick = e + 1.25
        self.sfx(self.t_tick, "tick", 0.8)
        self.t_ans, e = self.line("quiz_ans_kids", t=self.t_tick + 1.3)
        self.t_ding = e + 0.35
        self.sfx(self.t_ding, "dingdong", 0.9)
        self.cur = self.t_ding + 0.5
        _, e = self.line("quiz_ans", gap=0.0)
        self.t_yay, e2 = self.line("quiz_yay", gap=0.3)
        self.sfx(self.t_yay, "cheer", 0.8)
        self.sfx(self.t_yay, "popper", 0.6)
        self.t_awk = e2 + 0.6
        self.sfx(self.t_awk, "crickets", 0.8)
        self.dur = self.t_awk + 1.5

    def cam(self, t):
        if self.t_ding <= t < self.t_yay:
            return 1.0 + 0.1 * ease_out((t - self.t_ding) / 0.4), 980, 390
        if t >= self.t_awk:
            return 1.0 + 0.08 * ease((t - self.t_awk) / 1.0), 640, 520
        return 1.0 + 0.02 * ease(t / self.dur), W / 2, H / 2

    def draw(self, cv, t):
        bg_rays(cv, t * 0.5, ((120, 210, 255), (180, 235, 255)), cy=900)
        k = pop(t, 0.2, 0.5)
        cv.save()
        cv.translate(640, 110)
        cv.scale(k, k)
        text(cv, "퀴즈 타임!", 0, 0, 90, YELLOW, TF_TITLE, align="center", outline=(40, 90, 200), ow=18)
        cv.restore()
        if t > 1.4:
            caption(cv, "지금 토트넘은 몇 등일까요?", 640, 220, 50, WHITE, (40, 90, 200))
        opts = [("①", "1등", (255, 150, 150)), ("②", "10등", (150, 220, 150)), ("③", "20등", (255, 210, 110))]
        for i, (n, s_, col) in enumerate(opts):
            if t < self.t_opt[i]:
                continue
            kk = pop(t, self.t_opt[i], 0.4)
            x = 300 + i * 340
            right = i == 2 and t >= self.t_ding
            cv.save()
            cv.translate(x, 390)
            sc = kk * (1.12 if right else 1)
            cv.scale(sc, sc)
            if right:
                glow(cv, rrect(-150, -90, 150, 90, 34), (255, 255, 180), 26, 220)
            blob(cv, rrect(-140, -80, 140, 80, 30), col, 6, oc=(90, 90, 140))
            text(cv, f"{n} {s_}", 0, 22, 64, (70, 60, 90), TF_TITLE, align="center")
            cv.restore()
            if right:
                cv.drawPath(oval(x, 390, 172, 112), stroke(RED, 12))
        if self.t_tick <= t < self.t_ans:
            text(cv, str(3 - int((t - self.t_tick) / 0.45)), 640, 600, 72, RED, TF_TITLE, align="center",
                 outline=WHITE, ow=12)
        for i in range(5):
            x = 180 + i * 230
            cheer = self.t_yay <= t < self.t_awk
            K.villager(cv, i, x, H + 150, 0.9, mood="happy" if cheer else ("sweat" if t >= self.t_awk else "smile"),
                       arms=(170, 170) if cheer or (self.t_ans <= t < self.t_ans + 0.8) else (20, 20),
                       bob=bounce(t + i * 0.3, 3, 10) if cheer else 0, t=t)
        if t >= self.t_awk:
            caption(cv, "…어?", 640, 560, 64, WHITE, (90, 90, 120), a=int(255 * min(1, (t - self.t_awk) / 0.3)))
        if self.t_yay <= t < self.t_awk + 0.5:
            confetti(cv, t, seed=11, n=40, t0=self.t_yay)


# ------------------------------------------------------------------ 7. 화난 마을 사람들

class Angry(Scene):
    bgm = ("angry", 0.7)
    # 말하는 마을 사람: (배역, 자리 번호). 청년·아주머니·할아버지가 차례로 따진다.
    LOOKS = {1: dict(hair="curly", hc=(60, 44, 40), skin="light", shirt=(255, 160, 190)),
             2: dict(hair="villager_a", hc=(220, 220, 225), skin="tan", beard="mustache", bc=(215, 215, 220),
                     brow=(200, 200, 205), shirt=(150, 200, 150))}
    SIGNS = ["우승이라며?!", "빌드업 그만!", "20등 실화?", "그래도 힘내라…"]
    XS = (170, 390, 890, 1110)

    def setup(self):
        self.sfx(0.05, "march", 0.7)
        self.sfx(0.6, "crowd_angry", 0.6)
        self.turns = []
        for lid, role, seat, gap in (("fans1", "fan", 0, None), ("fans2", "fan3", 1, 0.25), ("fans3", "fan2", 2, 0.25)):
            st, e = self.line(lid, t=1.3 if gap is None else None, gap=gap or 0.0)
            self.turns.append((st, e, role, seat))
        self.t_sorry, e = self.line("sorry", gap=0.7)
        self.dur = e + 1.3

    def speaker(self, t):
        for st, e, role, seat in self.turns:
            if st - 0.1 <= t < e + 0.2:
                return role, seat
        return None, None

    def cam(self, t):
        if t >= self.t_sorry - 0.2:
            return 1.0 + 0.14 * ease_out((t - self.t_sorry + 0.2) / 0.6), 640, 400
        _, seat = self.speaker(t)
        if seat is not None:  # 말하는 사람 쪽으로 살짝
            return 1.06, (self.XS[seat] + 640) / 2, 420
        return 1.0 + 0.03 * ease(t / 3), W / 2, H / 2

    def draw(self, cv, t):
        bg_village(cv, t * 0.2, pan=200)
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((255, 60, 40), 36))
        caption(cv, "빌라전이 끝나고…", 200, 70, 38, WHITE, (150, 40, 40))
        arrive = ease_out((t - 0.1) / 1.2)
        role_now, seat_now = self.speaker(t)
        for i, x in enumerate(self.XS):
            xx = x + (1 - arrive) * (-400 if x < 640 else 400)
            y = GROUND + 50
            talking = seat_now == i
            b = bounce(t + i * 0.3, 2.5, 14 if talking else 6)
            K.villager(cv, i, xx, y, 0.95, mood="angry" if i < 3 else "sad",
                       talk=self.talk(role_now, t) if talking else 0,
                       arms=(20, 175) if talking else ((20, 120) if i < 3 else (30, 30)), bob=b, t=t,
                       look=self.LOOKS.get(i))
            s_ = self.SIGNS[i]
            w = text_w(s_, 30)
            sy = y - 300 - b - (i % 2) * 56
            sx = min(max(xx, w / 2 + 110), W - w / 2 - 110)
            blob(cv, rrect(sx - w / 2 - 14, sy - 34, sx + w / 2 + 14, sy + 16, 10), WHITE, 4,
                 oc=(200, 60, 60) if i < 3 else (60, 90, 170), shade=False)
            text(cv, s_, sx, sy + 6, 30, (200, 40, 40) if i < 3 else (60, 90, 170), align="center")
        K.person(cv, "dezerbi", 640, GROUND + 70, 1.15, mood="sad" if t >= self.t_sorry else "sweat",
                 talk=self.talk("dz", t), arms=(60, 60), tilt=math.sin(t * 20) * 2 if t < self.t_sorry else 0,
                 look=((-4 if seat_now is not None and self.XS[seat_now] < 640 else 4), 0) if seat_now is not None
                 else (0, 0))
        if t < self.t_sorry:
            for i in range(3):
                sweat(cv, 560 + i * 80, 330 + ((t * 90 + i * 30) % 70), 1.2)


# ------------------------------------------------------------------ 8. 그날 밤: 꼬꼬의 응원과 깨달음

class Night(Scene):
    bgm = ("night", 0.8)

    def setup(self):
        self.line("night1", t=1.0)
        self.t_koko, e = self.line("koko_cheer", gap=0.6)
        self.t_real, e = self.line("dz_realize", gap=0.6)
        self.t_star = e + 0.3
        self.sfx(self.t_star, "shooting_star", 0.9)
        self.t_dz, e = self.line("dz_wish", t=self.t_star + 1.0)
        self.sfx(e + 0.1, "twinkle", 0.7)
        self.dur = e + 1.3
        self.sfx_loop(0.0, self.dur, "crickets", 0.22)

    def cam(self, t):
        if t < self.t_koko:
            return 1.0 + 0.06 * ease(t / self.t_koko), 560, 460
        if t < self.t_star:
            return 1.06 + 0.04 * ease((t - self.t_koko) / 3), 600, 470
        return 1.1 - 0.1 * ease((t - self.t_star) / 1.5), 600, 400

    def draw(self, cv, t):
        bg_sky(cv, (22, 24, 70), (86, 72, 150))
        rng = random.Random(4)
        for i in range(60):
            x, y = rng.uniform(0, W), rng.uniform(0, 420)
            sparkle(cv, x, y, 2 + 2.5 * (math.sin(t * 2 + i) + 1), WHITE, 200)
        glow(cv, oval(1080, 130, 70, 70), (255, 245, 200), 40, 120)
        blob(cv, oval(1080, 130, 52, 52), (255, 246, 205), 0)
        cv.drawPath(oval(1102, 116, 46, 46), fill((24, 26, 72)))
        if t >= self.t_star:
            k = (t - self.t_star) / 1.3
            if k < 1:
                x0, y0 = 300 + k * 600, 60 + k * 200
                cv.drawLine(x0 - 140, y0 - 46, x0, y0, stroke((255, 255, 220), 5, int(255 * (1 - k))))
                glow(cv, oval(x0, y0, 12, 12), (255, 255, 200), 12, int(255 * (1 - k)))
        cv.drawPath(smooth([(-100, 620), (300, 520), (700, 540), (1100, 600), (1400, 640), (1400, 800), (-100, 800)]),
                    fill((40, 60, 70)))
        stadium(cv, 1050, 610, 0.55)
        for i in range(8):
            fx = 200 + i * 140 + math.sin(t * 0.8 + i) * 30
            fy = 560 + math.sin(t * 1.3 + i * 2) * 25
            glow(cv, oval(fx, fy, 5, 5), (255, 240, 120), 6, int(150 + 100 * math.sin(t * 3 + i)))
        dz_mood = "sad" if t < self.t_dz else "happy"
        arms = (20, 20) if t < self.t_dz else (20, 170)
        K.person(cv, "dezerbi", 520, 600, 1.05, mood=dz_mood, talk=self.talk("dz", t), arms=arms,
                 look=(0, -3) if t < self.t_koko else (4, 0), bob=bounce(t, 1.5, 5) if t >= self.t_dz + 0.5 else 0)
        hop = bounce(t, 1.5, 8) if self.t_koko <= t < self.t_real else 0
        K.rooster(cv, 700, 598, 0.9, talk=self.talk("koko", t), flip=True, bob=hop,
                  flap=abs(math.sin(t * 7)) if self.t_koko <= t < self.t_real or t >= self.t_dz else 0.1,
                  mood="happy" if t >= self.t_dz else "smile")
        if t >= self.t_dz:
            for i in range(3):
                kk = ((t - self.t_dz) * 0.5 + i / 3) % 1
                h = heart_path(600 + (i - 1) * 50, 380 - kk * 120, 14)
                cv.drawPath(h, fill((255, 130, 160), int(255 * (1 - kk))))
            sparkles(cv, t, 560, 420, 200, 8, seed=21)


# ------------------------------------------------------------------ 9. 오늘의 교훈

class Lesson(Scene):
    bgm = ("lesson", 0.75)

    def setup(self):
        self.sfx(0.1, "chime", 0.9)
        self.t_l, e = self.line("lesson", t=0.9, marks=True)
        mk = self.lines[-1]["marks"]
        self.t_l2 = self.t_l + next(m[1] for m in mk if m[0].startswith("재미"))
        self.sfx(self.t_l2, "pop", 0.6)
        self.t_kids, e = self.line("lesson_kids", gap=0.6)
        self.sfx(self.t_kids, "cheer", 0.5)
        self.dur = e + 1.3

    def cam(self, t):
        if t >= self.t_l2:
            return 1.0 + 0.05 * ease_out((t - self.t_l2) / 0.6), 640, 380
        return 1.0, W / 2, H / 2

    def draw(self, cv, t):
        cv.drawRect(skia.Rect.MakeWH(W, H), fill((255, 240, 200)))
        glow(cv, rrect(120, 60, 1160, 640, 30), (180, 140, 90), 20, 90)
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
        if t > self.t_l + 1.0:
            text(cv, "비싼 장난감이 많다고", 640, 300, 64, (70, 60, 90), align="center",
                 a=int(255 * min(1, (t - self.t_l - 1.0) / 0.3)))
        if t > self.t_l2:
            k2 = pop(t, self.t_l2, 0.4)
            cv.save()
            cv.translate(640, 400)
            cv.scale(k2, k2)
            text(cv, "재미있게 놀 수는 없어요!", 0, 0, 72, RED, TF_TITLE, align="center", outline=WHITE, ow=12)
            cv.restore()
        # 친구들이 손잡고 한 팀
        for i, key in enumerate(("fernandes", "tonali", "dezerbi", "vdv", "gallagher")):
            x = 380 + i * 130
            K.person(cv, key, x, 640, 0.62 if key != "dezerbi" else 0.72, mood="happy",
                     arms=(95, 95), bob=bounce(t + i * 0.2, 1.2, 4) if t >= self.t_kids else 0)
        K.rooster(cv, 1060, 640, 0.7, mood="happy", flap=abs(math.sin(t * 6)) if t >= self.t_kids else 0)
        if t >= self.t_kids:
            caption(cv, "네에~!", 1060, 470, 50, YELLOW, (230, 120, 40))


# ------------------------------------------------------------------ 10. 다음 이야기

class Preview(Scene):
    bgm = ("preview", 0.75)

    def setup(self):
        self.sfx(0.1, "thunder", 0.8)
        self.line("next", t=0.8)
        _, e = self.line("next2", gap=0.5)
        self.t_gulp = e + 0.6
        self.sfx(self.t_gulp, "gulp", 0.9)
        self.cur = self.t_gulp
        _, e = self.line("gulp", gap=0.05)
        self.sfx(self.t_gulp + 0.9, "thunder", 0.6)
        self.dur = e + 1.2

    def cam(self, t):
        if t >= self.t_gulp - 0.2:
            return 1.0 + 0.2 * ease_out((t - self.t_gulp + 0.2) / 0.5), 330, 470
        return 1.0 + 0.04 * ease(t / 4), W / 2, H / 2

    def draw(self, cv, t):
        flash = 0.1 < t < 0.25 or self.t_gulp + 0.9 < t < self.t_gulp + 1.02
        bg_sky(cv, (60, 10, 20) if not flash else (255, 255, 255), (140, 30, 40))
        blob(cv, poly([(640, 520), (640, 300), (700, 250), (1260, 250), (1260, 520)]), (70, 20, 30), 5,
             oc=(30, 10, 10))
        for x in range(700, 1260, 80):
            cv.drawRect(skia.Rect.MakeLTRB(x, 230, x + 40, 260), fill((70, 20, 30)))
        glow(cv, oval(950, 330, 110, 150), (255, 60, 40), 40, 90)
        K.devil(cv, 950, 470, 1.2, t)
        text(cv, "올드 트래포드", 950, 222, 40, WHITE, align="center", outline=(120, 20, 30), ow=8)
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
                 talk=self.talk("dz", t), arms=(40, 40))


# ------------------------------------------------------------------ 11. 엔딩

class Ending(Scene):
    S0, S1 = 43.6, 54.3  # 노래 두 번째 후렴 끝 + 아우트로

    def setup(self):
        self.bed(0, song_clip(self.S0, self.S1, 0.6, 1.4), 0.9)
        self.t_bye, e = self.line("bye", t=6.4)
        self.line("bye_kids", gap=0.15)
        self.dur = self.S1 - self.S0

    def cam(self, t):
        return 1.06 - 0.06 * ease(t / 4), W / 2, H / 2

    def draw(self, cv, t):
        ts = t + self.S0
        beat = song_beat(ts)
        bg_sky(cv, (130, 210, 255), (225, 246, 255))
        glow(cv, oval(W / 2, 560, 520, 260), (255, 255, 230), 60, 150)
        draw_rainbow(cv, W / 2, 640, 600, 30)
        cv.drawPath(smooth([(-100, 600), (400, 520), (900, 540), (1400, 600), (1400, 800), (-100, 800)]),
                    fill(GRASS))
        cast = ["tonali", "fernandes", "vdv", "dezerbi", "gallagher", "tosin", "mudryk"]
        for i, k in enumerate(cast):
            x = 130 + i * 170
            main = k == "dezerbi"
            K.person(cv, k, x, 650 if not main else 680, 0.8 if not main else 1.0, mood="happy",
                     arms=(20, 150 + 20 * math.sin(t * 8 + i)), bob=bounce(beat + i * 0.3, 1, 8))
        K.rooster(cv, 1210, 640, 0.8, flap=abs(math.sin(t * 8)), mood="happy")
        logo(cv, W / 2, 150, 0.62, t, 0.2, 0.04)
        if t > 1.5:
            a = int(255 * min(1, (t - 1.5) / 0.6))
            text(cv, "제작 · 타튼햄", W / 2, 272, 30, (60, 60, 100), align="center", outline=WHITE, ow=6, a=a)
            text(cv, "주제가 「힘내요! 데 제르비」", W / 2, 312, 26, (60, 60, 100), align="center", outline=WHITE,
                 ow=6, a=a)
        if t > self.t_bye:
            caption(cv, "다음에 또 만나요!", 640, 396, 64, YELLOW, (255, 110, 150))


# ------------------------------------------------------------------ 조립 / 렌더

def build():
    return [Opening(), TitleCard(), Intro(), Summer(), Match1(), Montage(), Quiz(), Angry(), Night(), Lesson(),
            Preview(), Ending()]


def frame(scenes, starts, t, surf):
    cv = surf.getCanvas()
    si = max(i for i, s in enumerate(starts) if t >= s)
    sc = scenes[si]
    lt = t - starts[si]
    K.CLOCK = t
    cv.clear(C(WHITE))
    cv.save()
    cv.scale(SCALE, SCALE)
    z, fx, fy = sc.cam(lt)
    cv.save()
    cv.translate(fx, fy)
    cv.scale(z, z)
    cv.translate(-fx, -fy)
    sc.draw(cv, lt)
    cv.restore()
    vignette(cv, 60)
    if not isinstance(sc, Opening):
        sc.subtitles(cv, lt)
    if sc.fade and si > 0:
        star_iris(cv, lt / 0.5)
    if isinstance(sc, Opening) and lt > sc.dur - 0.5:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(WHITE, int(255 * min(1, (lt - sc.dur + 0.5) / 0.5))))
    if si == len(scenes) - 1 and lt > sc.dur - 0.8:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(BLACK, int(255 * min(1, (lt - sc.dur + 0.8) / 0.8))))
    cv.restore()
    img = surf.makeImageSnapshot().toarray()
    return img[..., [2, 1, 0]]


def mix_audio(scenes, starts, total):
    """대사·효과음·음악을 따로 모은 뒤, 대사가 나오는 동안 음악을 부드럽게 낮춘다(더킹)."""
    voice, fx, music = Mixer(total), Mixer(total), Mixer(total)
    prev, off = None, 0.0
    for i, (s, st) in enumerate(zip(scenes, starts)):
        s.audio(voice, fx, music, st)
        if s.fade and i > 0:
            fx.add(st, sfx_audio("transition"), 0.45)
        if not s.bgm:
            prev, off = None, 0.0
            continue
        name, vol = s.bgm
        same = prev == name
        off = off + scenes[i - 1].dur if same else 0.0
        nxt = scenes[i + 1] if i + 1 < len(scenes) else None
        cont = bool(nxt is not None and nxt.bgm and nxt.bgm[0] == name)
        seg = bgm_segment(name, off, s.dur + (0.0 if cont else 0.4), fade_in=0.0 if same else 0.5,
                          fade_out=0.0 if cont else 0.9)
        music.add(st, seg, vol)
        prev = name
    n = int(total * SR)
    v, f, m = voice.buf[:n], fx.buf[:n], music.buf[:n]
    hop = 441
    env = np.array([np.abs(v[i:i + hop]).max() if i < n else 0 for i in range(0, n, hop)])
    speaking = (env > 0.02).astype(np.float32)
    # 말하기 50ms 전부터 내리고, 끝나고 400ms 에 걸쳐 올린다
    g = np.ones_like(speaking)
    level = 1.0
    for i in range(len(speaking) - 1, -1, -1):  # 미리 내리기(앞쪽으로 번짐)
        if speaking[i]:
            level = 0.0
        else:
            level = min(1.0, level + 1 / 5)
        g[i] = level
    fwd = 1.0
    for i in range(len(g)):
        target = g[i]
        fwd = target if target < fwd else min(target, fwd + 1 / 40)
        g[i] = fwd
    gain = 1.0 - 0.6 * (1.0 - g)
    gain_s = np.repeat(gain, hop)[:n]
    out = v * 1.0 + f * 0.55 + m * gain_s
    out = np.tanh(out * 1.1) / np.tanh(1.1)
    return out / max(1e-9, np.max(np.abs(out))) * 0.89


def main():
    import imageio_ffmpeg
    scenes = build()
    starts, acc = [], 0.0
    for s in scenes:
        starts.append(acc)
        acc += s.dur
    total = acc
    print("total", round(total, 2), [(type(s).__name__, round(s.dur, 2)) for s in scenes])
    OW, OH = int(W * SCALE), int(H * SCALE)
    surf = skia.Surface(OW, OH)
    if "--preview" in sys.argv:
        from PIL import Image
        i_ = sys.argv.index("--preview")
        outdir = sys.argv[i_ + 1] if len(sys.argv) > i_ + 1 else os.path.join(HERE, "_preview")
        os.makedirs(outdir, exist_ok=True)
        for i, (s, st) in enumerate(zip(scenes, starts)):
            for f in (0.2, 0.5, 0.8):
                t = st + s.dur * f
                Image.fromarray(frame(scenes, starts, t, surf)).resize((960, 540)).save(
                    os.path.join(outdir, f"s{i:02d}_{f:.2f}.png"))
        return
    buf = mix_audio(scenes, starts, total)
    wav_path = os.path.join(HERE, "_audio_kids.wav")
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((buf * 32767).astype(np.int16).tobytes())
    if "--audio-only" in sys.argv:
        print("wrote", wav_path)
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen([ff, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}",
                             "-r", str(FPS), "-i", "-", "-i", wav_path, "-c:v", "libx264", "-preset", "slow",
                             "-crf", "24", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
                             "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for i in range(n):
        proc.stdin.write(np.ascontiguousarray(frame(scenes, starts, i / FPS, surf)).tobytes())
        if i % 480 == 0:
            print(f"frame {i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(wav_path)
    print(f"wrote {OUT} ({total:.1f}s)")


if __name__ == "__main__":
    main()
