#!/usr/bin/env python3
"""SPURS QUEST 26/27 ~강등권의 전설~

2026년 9월 토트넘의 현실을 8비트 고전 게임 스타일로 풍자하는 패러디 영상 생성기.
BGM은 'When the Saints(Spurs) Go Marching In'(퍼블릭 도메인 전통곡)의 8비트 편곡이다.

    pip install pillow numpy imageio-ffmpeg
    python3 make_8bit.py              # -> spurs_quest_2627.mp4 (1920x1080)
"""
import math
import os
import random
import subprocess
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

import music
from engine import (BLACK, BROWN, CREAM, DGREEN, DRED, F16, F32, F64, FPS, GOLD, GRAY, GREEN, H, LGRAY, NAVY,
                    NAVY2, ORANGE, RED, SCALE, SKIN, SKIN_D, SKY, SR, W, WHITE, YELLOW, Mixer, blink, blit, box,
                    ctext, draw_flames, draw_stars, drum, make_stamp, noise, reveal, text, tw)
from sprites import (COCK, COCK_CRY, COCK_RUN, NEON, OBSIDIAN, PEOPLE, chibi, draw_hammer, kit_icon, monster,
                     portrait)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "spurs_quest_2627.mp4")
STAMP_SACKED = make_stamp("SACKED!")
PURPLE = (150, 90, 255)
PINK = (255, 70, 170)


class Scene:
    dur = 1.0
    fade_in = 0.25
    fade_out = 0.25

    def draw(self, img, d, t):
        pass

    def audio(self, m, t0):
        pass


def lines_at(d, x, y, lines, since, col, step=22, shadow=BLACK):
    for s in lines:
        text(d, x, y, reveal(s, since), col, shadow=shadow)
        since -= len(s) / 24 + 0.15
        y += step


def blip_lines(m, t0, lines):
    for s in lines:
        m.blips(t0, s)
        t0 += len(s) / 24 + 0.15


def dialog(d, lines, since, col=WHITE, y0=204, name=None):
    box(d, 6, y0, 474, 266)
    if name:
        w = tw(name) + 16
        d.rectangle([14, y0 - 12, 14 + w, y0 + 6], fill=NAVY, outline=WHITE)
        text(d, 22, y0 - 11, name, GOLD)
    lines_at(d, 18, y0 + 12, lines, since, col)


def trophy(d, x, y, col=GOLD):
    d.ellipse([x - 12, y + 2, x - 4, y + 12], outline=BLACK, width=2)
    d.ellipse([x + 4, y + 2, x + 12, y + 12], outline=BLACK, width=2)
    d.polygon([(x - 8, y), (x + 8, y), (x + 6, y + 14), (x, y + 18), (x - 6, y + 14)], fill=col, outline=BLACK)
    d.rectangle([x - 2, y + 18, x + 2, y + 22], fill=col, outline=BLACK)
    d.rectangle([x - 7, y + 22, x + 7, y + 26], fill=BROWN, outline=BLACK)
    d.point((x - 4, y + 3), fill=WHITE)


def pixel_confetti(d, t, seed=1, n=60):
    rng = random.Random(seed)
    for _ in range(n):
        x0, sp = rng.uniform(0, W), rng.uniform(40, 90)
        y = (rng.uniform(-H, 0) + t * sp) % (H + 10) - 5
        x = x0 + math.sin(t * 3 + x0) * 6
        c = rng.choice([RED, GOLD, NAVY2, WHITE, PINK])
        d.rectangle([x, y, x + 2, y + 1], fill=c)


def pow_box(d, s, cx, cy, col=YELLOW, bg=RED, font=F32):
    w = tw(s, font) + 20
    h = 44 if font is F32 else 24
    pts = []
    for i in range(20):
        a = i / 20 * math.tau
        r = 1.0 if i % 2 == 0 else 0.78
        pts.append((cx + math.cos(a) * (w / 2 + 14) * r, cy + math.sin(a) * (h / 2 + 12) * r))
    d.polygon(pts, fill=bg, outline=BLACK)
    ctext(d, cy - (18 if font is F32 else 9), s, col, font, shadow=BLACK, cx=cx)


def stage_banner(d, s):
    w = tw(s) + 16
    d.rectangle([4, 4, 4 + w, 22], fill=RED, outline=WHITE)
    text(d, 12, 5, s, WHITE)


# ------------------------------------------------------------------ 0. 부팅

class Boot(Scene):
    dur = 3.5
    fade_in = 0.0

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(196, 207, 161))
        y = min(96, int(-40 + t / 2.0 * 136))
        ctext(d, y, "SPURS BOY", NAVY, F32, shadow=None)
        text(d, W // 2 + tw("SPURS BOY", F32) // 2 + 2, y - 4, "™", NAVY, shadow=None)
        if t > 2.3:
            ctext(d, 150, "LICENSED BY ENIC", (60, 80, 60), shadow=None)
            ctext(d, 170, "(구단주 공식 라이선스)", (80, 100, 80), shadow=None)

    def audio(self, m, t0):
        m.sfx(t0 + 2.05, "ding")


# ------------------------------------------------------------------ 1. 타이틀

class Title(Scene):
    dur = 8.0
    LINE = [("fernandes", "home"), ("tonali", "away"), ("vdv", "home"), ("dezerbi", None), ("gallagher", "away"),
            ("vanhecke", "home"), ("mudryk", "away")]

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=NAVY)
        draw_stars(d, t, 25)
        ctext(d, 2, "SPURS QUEST", WHITE, F64, shadow=GOLD)
        ctext(d, 70, "토트넘 대모험 26/27 ~ 강등권의 전설 ~", GOLD)
        d.rectangle([0, 166, W, 180], fill=(24, 120, 48))
        for x in range(0, W, 32):
            d.rectangle([x, 166, x + 15, 180], fill=(32, 140, 60))
        for i, (k, kit) in enumerate(self.LINE):
            bob = -2 if (int(t * 4) + i) % 2 else 0
            blit(img, chibi(k, kit=kit), 42 + i * 58, 100 + bob, 2)
        cur = 1 if 3.2 <= t < 5.8 else 0
        flash = t >= 6.4 and blink(t, 6)
        for i, s in enumerate(["NEW GAME", "TROPHY ROOM (트로피 진열장)"]):
            if i == 0 and t >= 6.4 and not flash:
                continue
            text(d, 150, 188 + i * 20, s, WHITE)
        text(d, 132, 188 + cur * 20, "▶", GOLD)
        if t < 3.2 and blink(t, 1.5):
            ctext(d, 240, "PUSH START BUTTON", LGRAY)
        if 3.6 <= t < 5.8:
            box(d, 100, 86, 380, 170)
            ctext(d, 94, "- TROPHY ROOM -", GOLD)
            trophy(d, 128, 116)
            text(d, 150, 120, "2025 UEFA 유로파리그 ×1", WHITE)
            ctext(d, 146, reveal("...That's it. 이게 전부다.", t - 4.2, 14), LGRAY)

    def audio(self, m, t0):
        music.saints(m, t0 + 0.2, 6.2, bpm=150)
        m.sfx(t0 + 3.2, "move")
        m.sfx(t0 + 3.6, "select")
        m.blips(t0 + 4.2, "...That's it. 이게 전부다.", 14)
        m.sfx(t0 + 5.8, "move")
        m.sfx(t0 + 6.4, "start")


# ------------------------------------------------------------------ 2. 콜드 오픈 (현재 20위)

def lava_bg(d, t):
    d.rectangle([0, 0, W, H], fill=(40, 8, 8))
    for i in range(6):
        y = 170 + i * 16
        c = (120 + i * 22, 20 + i * 18, 10)
        pts = [(0, H)] + [(x, y + int(3 * math.sin(x * 0.05 + t * 3 + i))) for x in range(0, W + 8, 8)] + [(W, H)]
        d.polygon(pts, fill=c)
    rng = random.Random(5)
    for _ in range(10):
        x, ph = rng.uniform(0, W), rng.uniform(0, 1)
        k = (t * 0.7 + ph) % 1
        r = 2 + int(4 * k)
        d.ellipse([x - r, 250 - 70 * k - r, x + r, 250 - 70 * k + r], outline=ORANGE)


class ColdOpen(Scene):
    dur = 8.2
    FREEZE = 3.4

    def draw(self, img, d, t):
        tt = min(t, self.FREEZE)
        if t > 7.0:
            tt = self.FREEZE - (t - 7.0) * 3
        lava_bg(d, tt)
        d.rectangle([150, 150, 330, 176], fill=(80, 60, 50), outline=BLACK)
        d.rectangle([150, 150, 330, 154], fill=(120, 100, 80))
        shock = tt > 2.2
        blit(img, chibi("dezerbi", mood="shock" if shock else "smile"), 190, 82, 2)
        blit(img, COCK, 260, 116, 2)
        if shock:
            text(d, 206, 62, "!!", RED)
        d.rectangle([0, 0, W, 22], fill=BLACK)
        text(d, 8, 3, "STAGE 26/27", GOLD)
        text(d, 130, 3, "RANK 20/20", RED)
        text(d, 250, 3, "PTS 2", WHITE)
        text(d, 320, 3, "W0 D2 L3", WHITE)
        if self.FREEZE <= t < 7.0:
            a = np.asarray(img).astype(np.float32)
            gray = a.mean(axis=2, keepdims=True)
            a = gray * np.array([1.05, 0.9, 0.7])
            img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
            text(d, 20, 40, "*RECORD SCRATCH*", WHITE)
            text(d, 320, 40, "*FREEZE FRAME*", WHITE)
            if t < 5.4:
                dialog(d, ["Yep, that's us.", "리그 20위. 꼴찌. 강등권 한가운데."], t - self.FREEZE - 0.2, GOLD,
                       name="NARRATOR")
            else:
                dialog(d, ["어쩌다 여기까지 왔냐고?", "Let me explain..."], t - 5.4, WHITE, name="NARRATOR")
        if t >= 7.0:
            rng = random.Random(int(t * 30))
            for _ in range(8):
                y = rng.randint(0, H)
                d.rectangle([0, y, W, y + rng.randint(1, 3)], fill=(255, 255, 255))
            text(d, 20, 30, "◀◀ REWIND", WHITE, F32)

    def audio(self, m, t0):
        music.saints(m, t0 + 0.2, 3.2, bpm=90, minor=True, lead="tri", vol=0.12, drums="soft", harmony=False)
        m.sfx(t0 + 2.2, "select")
        m.sfx(t0 + self.FREEZE, "scratch")
        blip_lines(m, t0 + self.FREEZE + 0.2, ["Yep, that's us.", "리그 20위. 꼴찌. 강등권 한가운데."])
        blip_lines(m, t0 + 5.4, ["어쩌다 여기까지 왔냐고?", "Let me explain..."])
        m.sfx(t0 + 7.0, "rewind")


# ------------------------------------------------------------------ 3. 이전 줄거리

class Previously(Scene):
    dur = 12.6

    def draw(self, img, d, t):
        if t < 5.8:
            d.rectangle([0, 0, W, H], fill=(16, 20, 56))
            for i in range(8):
                x = i * 64 + 20
                d.polygon([(x - 6, 0), (x + 6, 0), (x + 40, 190), (x - 40, 190)], fill=(30, 36, 80))
            d.rectangle([0, 170, W, 204], fill=(40, 140, 60))
            if t < 3.8:
                pixel_confetti(d, t, 3)
                blit(img, chibi("ange"), 216, 90, 3)
                trophy(d, 243, 56 + int(math.sin(t * 12) * 2))
                dialog(d, ["I always win things in my second year, mate!", "2025.05 유로파리그 우승! 17년 만의 트로피!"],
                       t - 0.2, WHITE, name="안지 포스테코글루")
            else:
                k = t - 3.8
                if k < 0.5:
                    blit(img, chibi("ange", mood="shock"), 216, 90, 3)
                    img.paste(STAMP_SACKED, (190, 110), STAMP_SACKED)
                else:
                    kk = min(1.0, (k - 0.5) / 0.8)
                    x = 216 + 260 * kk
                    y = 90 - 160 * kk + 60 * kk * kk
                    spr = chibi("ange", mood="shock").rotate(-kk * 720, expand=True)
                    if kk < 1:
                        blit(img, spr, x, y, 3)
                    else:
                        r = int(8 * max(0, 1 - (k - 1.3) * 2))
                        if r > 0:
                            d.polygon([(460, 20 - r), (462, 18), (460 + r, 20), (462, 22), (460, 20 + r), (458, 22),
                                       (460 - r, 20), (458, 18)], fill=WHITE)
                    trophy(d, 243, 56 + int(min(1, k * 2) * 100))
                dialog(d, ["...그리고 16일 뒤.", "YOU'RE FIRED! (경질)"], k, RED, name="NARRATOR")
        elif t < 8.9:
            k = t - 5.8
            d.rectangle([0, 0, W, H], fill=(255, 150, 120))
            d.rectangle([0, 0, W, 70], fill=(255, 110, 130))
            d.ellipse([180, 60, 300, 180], fill=(255, 210, 120))
            d.rectangle([0, 160, W, 204], fill=(240, 200, 140))
            for x in (40, 420):
                d.rectangle([x, 80, x + 6, 160], fill=(100, 70, 40), outline=BLACK)
                for a in range(5):
                    ang = math.radians(200 + a * 35)
                    d.line([(x + 3, 80), (x + 3 + math.cos(ang) * 30, 84 + math.sin(ang) * 16)], fill=(40, 140, 60),
                           width=5)
            px = -60 + k * 220
            d.rectangle([px, 40, px + 60, 50], fill=WHITE, outline=BLACK)
            d.polygon([(px + 20, 45), (px + 34, 26), (px + 40, 26), (px + 32, 45)], fill=LGRAY, outline=BLACK)
            text(d, px + 8, 36, "LA", NAVY, shadow=None)
            blit(img, chibi("son", mood="smile"), 214, 96, 3)
            d.rectangle([272, 150, 294, 170], fill=RED, outline=BLACK)
            dialog(d, ["See you, Spurs! 안녕~!", "2025.08 손흥민, LAFC로 이적"], k - 0.2, WHITE, name="쏘니")
        else:
            k = t - 8.9
            d.rectangle([0, 0, W, H], fill=(236, 222, 190))
            d.rectangle([0, 170, W, 204], fill=(150, 110, 80))
            d.rectangle([60, 70, 130, 170], fill=(120, 80, 50), outline=BLACK)
            text(d, 64, 76, "CHAIRMAN", WHITE)
            x = 96 + k * 60
            blit(img, chibi("levy", frame=int(t * 6) % 2), x, 104, 2)
            d.rectangle([x + 4, 138, x + 32, 152], fill=(200, 160, 110), outline=BLACK)
            for i in range(6):
                j = abs(math.sin(t * 8 + i)) * 6
                blit(img, COCK, 300 + i * 26, 150 - j)
            if blink(t, 3):
                pow_box(d, "LEVY OUT!!", 380, 60, YELLOW, NAVY, F16)
            if k < 2.0:
                dialog(d, ["2025.09 레비 회장 퇴장!", "이제 다 잘 되겠지?"], k, WHITE, name="NARRATOR")
            else:
                dialog(d, ["...라고 생각했다."], k - 2.0, GOLD, name="NARRATOR")
        d.rectangle([0, 0, 250, 20], fill=BLACK)
        text(d, 6, 2, "PREVIOUSLY ON SPURS QUEST...", GOLD)

    def audio(self, m, t0):
        music.saints(m, t0 + 0.1, 3.7, bpm=160, echo=True)
        m.sfx(t0 + 0.1, "fanfare")
        blip_lines(m, t0 + 0.2, ["I always win things in my second year, mate!"])
        m.sfx(t0 + 3.8, "stamp")
        m.sfx(t0 + 4.3, "yank")
        m.sfx(t0 + 5.1, "ding")
        music.saints(m, t0 + 5.8, 3.1, bpm=120, transpose=2, lead="sq", duty=0.5, drums="soft")
        blip_lines(m, t0 + 5.6, ["See you, Spurs! 안녕~!"])
        music.saints_intro(m, t0 + 8.9, bpm=170)
        m.sfx(t0 + 9.2, "boo")
        blip_lines(m, t0 + 8.9, ["2025.09 레비 회장 퇴장!", "이제 다 잘 되겠지?"])
        m.sfx(t0 + 10.9, "sad")


# ------------------------------------------------------------------ 스테이지 카드

class StageCard(Scene):
    dur = 3.4

    def __init__(self, num, title, line, faces=()):
        self.num, self.title, self.line, self.faces = num, title, line, faces

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        ctext(d, 40, self.num, GOLD, F32, shadow=DRED)
        ctext(d, 86, self.title, WHITE, F32, shadow=NAVY2)
        d.line([(80, 130), (400, 130)], fill=GRAY)
        n = len(self.faces)
        for i, (k, kit) in enumerate(self.faces):
            if t > 0.4 + i * 0.12:
                blit(img, chibi(k, int(t * 4) % 2, kit=kit), W // 2 - n * 22 + i * 44 + 4, 140, 2)
        ctext(d, 222 if self.faces else 160, reveal(self.line, t - 0.8), LGRAY)

    def audio(self, m, t0):
        music.saints_intro(m, t0 + 0.1, bpm=200)
        m.blips(t0 + 0.8, self.line)


# ------------------------------------------------------------------ 4. 감독 선택

class ManagerSelect(Scene):
    dur = 10.0
    KEYS = ["frank", "tudor", "dezerbi"]
    XS = [40, 189, 338]
    SEL = [0.8, 3.4, 6.0]
    STAMP = [2.5, 5.1]
    INFO = [
        ("토마스 프랭크: 8 GAMES WITHOUT A WIN", "→ 부임 8개월 만에 SACKED!"),
        ("이고르 투도르: 44 DAYS, 7 GAMES", "→ 포레스트전 0-3 패배 후 SACKED!"),
        ("로베르토 데 제르비: 최종전 잔류 성공!", "→ ...그런데 올 시즌 5경기째 무승 (20위)"),
    ]

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(16, 16, 48))
        off = int(t * 8) % 16
        for x in range(-16, W, 16):
            d.line([(x + off, 0), (x + off, H)], fill=(28, 28, 72))
        for y in range(-16, H, 16):
            d.line([(0, y + off), (W, y + off)], fill=(28, 28, 72))
        ctext(d, 4, "SELECT YOUR MANAGER", GOLD)
        ctext(d, 22, "※ 2025-26 시즌에만 3명!", LGRAY)
        c = max([i for i, s in enumerate(self.SEL) if t >= s], default=-1)
        for i, (k, x) in enumerate(zip(self.KEYS, self.XS)):
            mood = None
            if i < 2 and t >= self.STAMP[i]:
                mood = "shock"
            if i == 2:
                mood = "sweat" if t > 7.8 else "smile"
            d.rectangle([x, 46, x + 101, 147], fill=(56, 64, 120))
            blit(img, portrait(k, mood), x, 46, 3)
            ctext(d, 154, PEOPLE[k]["name"], WHITE, cx=x + 51)
            if i == 2 and t > 7.8:
                draw_flames(d, x, x + 102, 147, t, 3, 26)
                if blink(t, 3):
                    ctext(d, 124, "HOT SEAT!", RED, cx=x + 51)
            if i < 2 and t >= self.STAMP[i]:
                st = STAMP_SACKED
                if t - self.STAMP[i] < 0.08:
                    st = st.resize((st.width * 2, st.height * 2), Image.NEAREST)
                img.paste(st, (x + 51 - st.width // 2, 100 - st.height // 2), st)
        if c >= 0 and (blink(t, 4) or t - self.SEL[c] < 0.4):
            x = self.XS[c]
            d.rectangle([x - 4, 42, x + 105, 151], outline=YELLOW, width=3)
        if c >= 0:
            box(d, 6, 180, 474, 264)
            l1, l2 = self.INFO[c]
            since = t - self.SEL[c] - 0.4
            text(d, 18, 196, reveal(l1, since), WHITE)
            text(d, 18, 226, reveal(l2, since - len(l1) / 24 - 0.2), RED if c == 2 else LGRAY)

    def audio(self, m, t0):
        music.saints(m, t0 + 0.2, 7.6, bpm=132, minor=True, lead="sq", duty=0.25, drums="march")
        m.seq(t0 + 7.8, 2.2, "E5 F5 E5 D#5", 240, 2, "sq", 0.07, 0.125)
        for i, s in enumerate(self.SEL):
            m.sfx(t0 + s, "move" if i else "select")
            l1, l2 = self.INFO[i]
            m.blips(t0 + s + 0.4, l1)
            m.blips(t0 + s + 0.4 + len(l1) / 24 + 0.2, l2)
        for s in self.STAMP:
            m.sfx(t0 + s, "stamp")


# ------------------------------------------------------------------ 5. 플랫포머 (2025-26)

class Platformer(Scene):
    dur = 19.6
    INTRO = 2.0
    SPD = 70.0
    CAM_STOP = 10.4
    GROUND = 222
    HX = 110
    HERO_Y = GROUND - 67
    HITS = [2.9, 3.9, 6.6, 7.5]
    SYMS = ["L", "L", "L", "D"]
    WINLESS = [4, 8, 12, 15]
    BANNERS = ["2026년, 리그 승리 실종", "8 GAMES WITHOUT A WIN", "구단 최초 6연패", "리그 15경기 연속 무승"]
    HOOKS = [(4.5, "frank"), (8.1, "tudor")]
    DROPS = [(5.4, "tudor"), (9.0, "dezerbi")]
    PAUSES = [(4.5, 5.8), (8.1, 9.4)]
    WALK, JUMP, LAND = 10.4, 11.2, 12.1
    HAMMER = 12.5
    ARSENAL = 16.6

    def __init__(self):
        cf = self.cam(self.CAM_STOP)
        self.pit0 = int(round((cf + 232) / 16)) * 16
        self.pit1 = self.pit0 + 112
        self.ps = self.pit0 - cf

    def moving(self, t):
        t = min(t, self.CAM_STOP)
        m = max(0.0, t - self.INTRO)
        for a, b in self.PAUSES:
            if t > a:
                m -= min(t, b) - a
        return m

    def cam(self, t):
        return self.SPD * self.moving(t)

    def manager(self, t):
        if t < self.DROPS[0][0]:
            return "frank"
        if t < self.DROPS[1][0]:
            return "tudor"
        return "dezerbi"

    def draw(self, img, d, t):
        if t < self.INTRO:
            d.rectangle([0, 0, W, H], fill=BLACK)
            ctext(d, 60, "WORLD 25-26", WHITE)
            ctext(d, 84, "지난 시즌", LGRAY)
            for i, k in enumerate(["frank", "tudor", "dezerbi"]):
                blit(img, chibi(k), 150 + i * 44, 112, 2)
            text(d, 288, 146, "× 3 (MANAGERS)", WHITE)
            return
        if t >= self.ARSENAL:
            self.draw_arsenal(img, d, t - self.ARSENAL)
            return
        cam = self.cam(t)
        d.rectangle([0, 0, W, H], fill=SKY)
        for wx, wy in ((40, 40), (220, 60), (380, 34), (560, 70)):
            sx = (wx - cam * 0.3) % 680 - 100
            for ox, oy, r in ((0, 4, 12), (14, 0, 15), (32, 4, 12)):
                d.ellipse([sx + ox - r, wy + oy - r // 2, sx + ox + r, wy + oy + r // 2 + 5], fill=WHITE)
        for wx in (0, 300, 600):
            sx = (wx - cam * 0.5) % 900 - 160
            d.ellipse([sx, 160, sx + 160, 270], fill=GREEN, outline=DGREEN)
        gx0 = int(cam // 16) * 16
        for wx in range(gx0, gx0 + W + 32, 16):
            if self.pit0 <= wx < self.pit1:
                continue
            sx = wx - cam
            for gy in (self.GROUND, self.GROUND + 16, self.GROUND + 32):
                d.rectangle([sx, gy, sx + 15, gy + 15], fill=BROWN)
                d.line([(sx, gy), (sx + 15, gy)], fill=(252, 188, 176))
                d.line([(sx, gy + 8), (sx + 15, gy + 8)], fill=BLACK)
                d.line([(sx, gy + 1), (sx, gy + 7)], fill=BLACK)
                d.line([(sx + 8, gy + 9), (sx + 8, gy + 15)], fill=BLACK)
        px0 = self.pit0 - cam
        if px0 < W:
            d.rectangle([px0, self.GROUND, px0 + 111, H], fill=(24, 0, 0))
            ctext(d, 230, "CHAMPIONSHIP", RED, cx=px0 + 56, shadow=None)
            ctext(d, 248, "(2부 리그)", DRED, cx=px0 + 56, shadow=None)
        for i, ht in enumerate(self.HITS):
            bx = self.HX + self.cam(ht) - cam
            if -24 < bx < W:
                by = 96 - (3 if 0 <= t - ht < 0.1 else 0)
                if t < ht:
                    d.rectangle([bx, by, bx + 17, by + 17], fill=GOLD, outline=BLACK)
                    text(d, bx + 5, by, "?", BROWN, shadow=None)
                else:
                    d.rectangle([bx, by, bx + 17, by + 17], fill=(150, 80, 40), outline=BLACK)
                k = t - ht
                if 0 <= k < 1.0:
                    iy = 78 - int(24 * min(1.0, k / 0.35))
                    col = RED if self.SYMS[i] == "L" else GRAY
                    d.rectangle([bx, iy, bx + 17, iy + 17], fill=col, outline=WHITE)
                    text(d, bx + 5, iy, self.SYMS[i], WHITE, shadow=None)
        hx, hy, air, show = self.HX, self.HERO_Y, False, True
        mgr = self.manager(t)
        hook = None
        for (ht, who), (dr, _) in zip(self.HOOKS, self.DROPS):
            k = t - ht
            if 0 <= k < 0.9:
                mgr = who
                if k < 0.35:
                    hook = -40 + (self.HX + 76) * (k / 0.35)
                else:
                    kk = k - 0.35
                    dx = -900 * kk * kk - 250 * kk
                    hx += dx
                    hook = self.HX + 36 + dx
            elif ht + 0.9 <= t < dr:
                show = False
        for dr, who in self.DROPS:
            k = t - dr
            if 0 <= k < 0.4:
                hy = -70 + (self.HERO_Y + 70) * (k / 0.4) ** 2
        if t < self.CAM_STOP:
            for ht in self.HITS:
                k = t - (ht - 0.3)
                if 0 <= k < 0.6:
                    hy -= 60 * 4 * (k / 0.6) * (1 - k / 0.6)
                    air = True
        elif t < self.JUMP:
            hx = self.HX + (t - self.WALK) / (self.JUMP - self.WALK) * (200 - self.HX)
        elif t < self.LAND:
            k = (t - self.JUMP) / (self.LAND - self.JUMP)
            hx = 200 + (self.ps + 94 - 200) * k
            hy -= 60 * 4 * k * (1 - k)
            air = True
        else:
            hx = self.ps + 94
            if t < self.LAND + 1.0:
                hx += 1 if int(t * 16) % 2 else -1
                text(d, hx + 14, hy - 20, "!", RED)
        moving = t < self.CAM_STOP and not any(a <= t < b for a, b in self.PAUSES)
        moving = moving or self.WALK <= t < self.JUMP
        frame = 1 if air or (moving and int(t * 8) % 2) else 0
        hooked = hook is not None
        if show:
            blit(img, chibi(mgr, frame, mood="shock" if hooked else "smile"), hx, hy, 2)
        if hooked:
            y = self.HERO_Y + 24
            d.line([(-10, y), (hook, y)], fill=(150, 90, 40), width=5)
            d.arc([hook - 16, y, hook + 16, y + 32], 270, 90, fill=(150, 90, 40), width=5)
            d.line([(hook, y + 30), (hook - 8, y + 30)], fill=(150, 90, 40), width=5)
        for ht, who in self.HOOKS:
            if 0.3 <= t - ht < 1.3:
                box(d, 150, 54, 330, 128)
                blit(img, portrait(who, "shock"), 160, 60, 2)
                text(d, 236, 66, "SACKED", RED, F32)
                text(d, 240, 104, "(경질!)", WHITE)
        if t >= self.HAMMER:
            k = t - self.HAMMER
            wx = -30 + 260 * k
            wy = self.GROUND - 31
            edge = self.ps - 4
            if wx > edge:
                kf = (wx - edge) / 260
                wx = edge + 50 * kf
                wy += 0.5 * 600 * kf * kf
            if wy < H:
                draw_hammer(d, wx, wy, t, mood="shock" if wx > edge - 1 else "happy")
        wl = 0
        for i, ht in enumerate(self.HITS):
            if t >= ht:
                wl = self.WINLESS[i]
        text(d, 10, 4, "SPURS", WHITE)
        text(d, 150, 4, f"무승 {wl:02d}", WHITE)
        text(d, 270, 4, f"MGR: {PEOPLE[mgr]['short']}", WHITE)
        banner = None
        for i, ht in enumerate(self.HITS):
            if 0 <= t - ht < 1.0:
                banner = (self.BANNERS[i], RED)
        for ht, who in self.HOOKS:
            if 0 <= t - ht < 0.9:
                banner = (f"{PEOPLE[who]['name']} OUT", RED)
        for dr, who in self.DROPS:
            if 0 <= t - dr < 1.2:
                extra = " (시즌 3번째!)" if who == "dezerbi" else " (임시)"
                banner = (f"NEW: {PEOPLE[who]['name']}{extra}", WHITE)
        if self.WALK <= t < self.LAND:
            banner = ("LAST DAY vs 에버튼 ─ 지면 강등!", WHITE)
        elif self.LAND <= t < self.LAND + 1.3:
            banner = ("팔리냐 1-0!! 잔류다!!", GOLD)
        elif 13.5 <= t < 14.3:
            banner = ("대신 웨스트햄이 강등...", LGRAY)
        if banner:
            s, col = banner
            w = tw(s)
            d.rectangle([W // 2 - w // 2 - 6, 26, W // 2 + w // 2 + 6, 46], fill=BLACK)
            ctext(d, 28, s, col)
        if t >= 14.3:
            box(d, 90, 64, 390, 172)
            ctext(d, 72, "SURVIVED!", GOLD, F32)
            ctext(d, 112, "17위 · 승점 41 (2시즌 연속 17위)", WHITE)
            ctext(d, 138, "세계 9위 부자 구단의 성적표", LGRAY)

    def draw_arsenal(self, img, d, k):
        d.rectangle([0, 0, W, H], fill=(20, 20, 30))
        d.rectangle([90, 30, 390, 190], fill=(40, 40, 50), outline=LGRAY, width=3)
        d.rectangle([100, 40, 380, 180], fill=(200, 30, 40))
        pixel_confetti(d, k, 9, 40)
        trophy(d, 240, 70 + int(math.sin(k * 8) * 3))
        ctext(d, 120, "NEWS: ARSENAL", WHITE)
        ctext(d, 140, "2025-26 CHAMPIONS", GOLD)
        blit(img, COCK_CRY if k > 1.2 else COCK, 216, 196, 2)
        if k > 1.2:
            for sgn in (-1, 1):
                for i in range(4):
                    kk = (k * 2 + i / 4) % 1
                    d.rectangle([248 + sgn * (10 + 40 * kk), 205 - 20 * kk + 60 * kk * kk,
                                 250 + sgn * (10 + 40 * kk), 207 - 20 * kk + 60 * kk * kk], fill=(110, 190, 255))
        dialog(d, ["같은 날, 북런던 라이벌은 우승...", "SPURS FANS: (TV를 껐다)"], k - 0.3, WHITE, name="MEANWHILE")

    def audio(self, m, t0):
        for a, b in [(self.INTRO, 4.5), (5.8, 8.1), (9.4, self.CAM_STOP)]:
            music.saints(m, t0 + a, b - a, bpm=190, drums="fast", start_bar=0 if a < 3 else 8)
        for ht in self.HITS:
            m.sfx(t0 + ht - 0.3, "jump")
            m.sfx(t0 + ht, "bump")
            m.sfx(t0 + ht + 0.05, "sad")
        for ht, _ in self.HOOKS:
            m.sfx(t0 + ht, "hook")
            m.sfx(t0 + ht + 0.35, "yank")
            m.sfx(t0 + ht + 0.4, "stamp")
        for dr, _ in self.DROPS:
            m.sfx(t0 + dr, "fall")
            m.sfx(t0 + dr + 0.4, "land")
        for k in range(18):
            m.add(t0 + self.JUMP + k * 0.05, drum("h") * 2)
        m.sfx(t0 + self.JUMP, "jump")
        m.sfx(t0 + self.LAND, "land")
        m.notes(t0 + self.LAND + 0.05, "C6:0.08 E6:0.08 G6:0.2", vol=0.08, duty=0.25)
        m.sfx(t0 + 13.45, "fall")
        music.saints(m, t0 + 14.3, 2.2, bpm=200, drums="roll", echo=True)
        m.sfx(t0 + 14.3, "fanfare")
        m.sfx(t0 + self.ARSENAL, "fanfare")
        m.sfx(t0 + self.ARSENAL + 1.2, "sad")
        blip_lines(m, t0 + self.ARSENAL + 0.3, ["같은 날, 북런던 라이벌은 우승...", "SPURS FANS: (TV를 껐다)"])


# ------------------------------------------------------------------ 6. 이적시장

class Shop(Scene):
    dur = 18.0
    ITEMS = [  # (키, 등번호, 이름, 가격, 설명 2줄)
        ("fernandes", "18", "페르난데스", "£85M", ("from 웨스트햄 (강등팀)", "구단 역대 최고액!")),
        ("tonali", "16", "토날리", "£92.5M", ("from 뉴캐슬", "(+옵션 £7.5M)")),
        (None, "17", "사비뉴", "£75M", ("from 맨시티", "NEW CHALLENGER!")),
        ("vanhecke", "6", "반 헤케", "£52M", ("from 브라이튼", "센터백")),
        ("robertson", "3", "로버트슨", "FREE", ("from 리버풀", "자유계약")),
        ("senesi", "5", "세네시", "FREE", ("from 본머스", "자유계약")),
        ("mudryk", "27", "무드릭", "LOAN", ("from 첼시", "임대")),
        (None, "22", "마르무시", "LOAN", ("from 맨시티", "임대")),
        ("adarabioyo", "4", "아다라비오요", "£££", ("from 첼시", "센터백")),
    ]
    BUY0, GAP = 0.9, 0.8
    LINES = [
        (0.2, ["상인: WELCOME! 뭘 사겠소?"], WHITE),
        (1.1, ["상인: 강등팀 선수를 £85M에?!", "      구단 역대 최고액이오! SOLD!"], GOLD),
        (3.4, ["상인: MORE! MORE! 더 사시오!"], WHITE),
        (6.0, ["상인: (그 사이 주장 로메로는 아틀레티코로 떠났소)"], LGRAY),
    ]
    ITEM1, ITEM2, BYE, CAPT = 8.6, 10.4, 12.2, 14.4

    def bought(self, t):
        return sum(1 for i in range(len(self.ITEMS)) if t >= self.BUY0 + i * self.GAP)

    def draw(self, img, d, t):
        if t >= self.ITEM1:
            return self.draw_after(img, d, t)
        d.rectangle([0, 0, W, H], fill=(24, 16, 40))
        text(d, 10, 4, "★ TRANSFER MARKET 2026 ★", GOLD)
        n = self.bought(t)
        frac = max(0.04, 1 - n / len(self.ITEMS) * 0.96)
        text(d, 330, 4, "자금", WHITE)
        d.rectangle([368, 7, 470, 19], fill=BLACK, outline=WHITE)
        d.rectangle([370, 9, 370 + int(98 * frac), 17], fill=GREEN if frac > 0.3 else RED)
        box(d, 6, 26, 150, 198)
        if n == 0:
            ctext(d, 90, "SHOP", LGRAY, F32, cx=78)
        else:
            k, num, nm, price, (c1, c2) = self.ITEMS[n - 1]
            since = t - (self.BUY0 + (n - 1) * self.GAP)
            dy = -6 if since < 0.15 else 0
            if k:
                blit(img, portrait(k), 44, 34 + dy, 2)
            else:
                d.rectangle([48, 38, 108, 102], fill=(30, 30, 60))
                ctext(d, 50, "?", WHITE, F32, cx=78)
            ctext(d, 108, nm, WHITE, cx=78)
            ctext(d, 126, price, GOLD, cx=78)
            ctext(d, 150, c1, WHITE, cx=78)
            ctext(d, 170, c2, LGRAY, cx=78)
        box(d, 156, 26, 474, 198)
        for i, (k, num, nm, price, _) in enumerate(self.ITEMS):
            yy = 31 + i * 18
            sold = t >= self.BUY0 + i * self.GAP
            col = GRAY if sold else WHITE
            text(d, 176, yy, f"#{num}", col)
            text(d, 212, yy, nm, col)
            text(d, 466 - tw(price), yy, price, GRAY if sold else GOLD)
            if sold:
                text(d, 340, yy, "SOLD", RED)
                if t - (self.BUY0 + i * self.GAP) < 0.25:
                    d.rectangle([172, yy, 470, yy + 17], outline=YELLOW)
        if n < len(self.ITEMS):
            text(d, 160, 31 + n * 18, "▶", GOLD)
        cur = None
        for st, ls, col in self.LINES:
            if t >= st:
                cur = (st, ls, col)
        box(d, 6, 204, 474, 266)
        if cur:
            lines_at(d, 18, 214, cur[1], t - cur[0], cur[2])

    def draw_after(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(10, 10, 30))
        draw_stars(d, t, 10)
        if t < self.BYE:
            item = "home" if t < self.ITEM2 else "away"
            k = t - (self.ITEM1 if item == "home" else self.ITEM2)
            d.rectangle([0, 170, W, 200], fill=(40, 40, 80))
            blit(img, chibi("vdv", kit=item), 216, 104, 2)
            for i in range(8):
                a = i / 8 * math.tau + t * 2
                d.line([(240 + math.cos(a) * 20, 76 + math.sin(a) * 20),
                        (240 + math.cos(a) * 40, 76 + math.sin(a) * 40)], fill=GOLD, width=2)
            blit(img, kit_icon(item), 221, 56, 2)
            name = "26/27 HOME KIT" if item == "home" else "26/27 AWAY KIT"
            desc = ("흰 바탕 + 험멜풍 사선 무늬, 빨간 AIA" if item == "home"
                    else "옵시디언 네이비 + 네온 번개 무늬!")
            dialog(d, [f"{name}을(를) 손에 넣었다!", desc], k - 0.3, GOLD, name="ITEM GET!")
        elif t < self.CAPT:
            k = t - self.BYE
            d.rectangle([0, 170, W, 200], fill=(40, 40, 80))
            d.rectangle([380, 70, 440, 170], fill=(60, 60, 70), outline=LGRAY)
            d.rectangle([374, 56, 446, 72], fill=(40, 160, 70), outline=BLACK)
            text(d, 380, 56, "EXIT→MAD", WHITE, shadow=None)
            x = 150 + min(1.0, k / 1.8) * 230
            if k < 1.9:
                blit(img, chibi("romero", int(t * 6) % 2), x, 104, 2)
            dialog(d, ["¡Adiós! 주장 로메로,", "아틀레티코 마드리드로 떠났다."], k - 0.2, WHITE, name="크리스티안 로메로")
        else:
            k = t - self.CAPT
            d.rectangle([0, 170, W, 200], fill=(40, 40, 80))
            squad = [("fernandes", "home"), ("tonali", "away"), ("robertson", "home"), ("vdv", "home"),
                     ("vanhecke", "away"), ("senesi", "home"), ("mudryk", "away"), ("adarabioyo", "home")]
            for i, (kk, kit) in enumerate(squad):
                bob = -3 if (int(t * 5) + i) % 2 else 0
                blit(img, chibi(kk, kit=kit), 20 + i * 56, 104 + bob, 2)
            if k < 0.6:
                x = -40 + k / 0.6 * 220
                for j in range(4):
                    d.line([(x - 10 - j * 12, 120 + j * 10), (x - 40 - j * 12, 120 + j * 10)], fill=WHITE, width=2)
            ctext(d, 30, "NEW CAPTAIN: 반 더 벤 (37)", GOLD)
            if k < 2.2:
                dialog(d, ["새 스쿼드 완성! 새 주장 반 더 벤!", "THIS IS OUR YEAR!!"], k - 0.2, GOLD, name="SPURS FANS")
            else:
                dialog(d, ["(스포: 아니었다)"], k - 2.2, RED, name="NARRATOR")

    def audio(self, m, t0):
        music.saints(m, t0 + 0.1, 8.4, bpm=140, transpose=2, lead="sq", duty=0.5, drums="soft")
        for st, ls, _ in self.LINES:
            blip_lines(m, t0 + st, ls)
        for i in range(len(self.ITEMS)):
            m.sfx(t0 + self.BUY0 + i * self.GAP, "cash")
        m.sfx(t0 + self.ITEM1, "itemget")
        m.sfx(t0 + self.ITEM2, "itemget")
        m.seq(t0 + self.BYE, 2.2, "D4 F#4 A4 D5 C#5 A4 F#4 E4", 110, 2, "sq", 0.08, 0.5)
        m.sfx(t0 + self.CAPT, "whoosh")
        music.saints(m, t0 + self.CAPT + 0.3, 1.9, bpm=200, echo=True)
        m.sfx(t0 + self.CAPT + 2.2, "sad")


# ------------------------------------------------------------------ 7. 포켓몬 배틀 (2026-27)

class Battle(Scene):
    fade_in = 0.0
    B0 = 1.0
    FOES = [
        dict(kind="bee", name="BRENTFORD", player="fernandes", kit="away", len=5.3,
             msgs=[(0.2, ["야생의 BRENTFORD가 나타났다! (AWAY)"], BLACK),
                   (1.5, ["SPURS는 £85M 페르난데스를 내보냈다!"], BLACK),
                   (2.9, ["It's not very effective...", "0-3 패배!"], RED)],
             result=(3.3, "L", 0, "BRE 3 : 0 TOT"), dmg=[3.3]),
        dict(kind="magpie", name="NEWCASTLE", player="tonali", kit="home", len=5.3,
             msgs=[(0.2, ["NEWCASTLE이 나타났다!", "(토날리의 친정팀이다)"], BLACK),
                   (1.8, ["토날리: Ciao, amici~! (반갑게 인사했다)"], BLACK),
                   (3.0, ["까치가 공을 훔쳐갔다!", "0-2 패배! 2경기 연속 무득점"], RED)],
             result=(3.3, "L", 0, "TOT 0 : 2 NEW"), dmg=[3.3]),
        dict(kind="tree", name="NOTTM FOREST", player="gallagher", kit="away", len=5.3,
             msgs=[(0.2, ["NOTTM FOREST가 나타났다! (AWAY)", "(지난 시즌 투도르를 잘랐던 그 나무)"], BLACK),
                   (1.8, ["갤러거의 슈팅! ...나무에 맞았다."], BLACK),
                   (3.0, ["0-0 무승부! 시즌 첫 승점 +1"], BLACK)],
             result=(3.3, "D", 1, "NFO 0 : 0 TOT"), heal=3.3),
        dict(kind="toffee", name="EVERTON", player="vanhecke", kit="home", len=5.0,
             msgs=[(0.2, ["EVERTON이 나타났다!"], BLACK),
                   (1.5, ["양 팀 모두 잠들었다... Zzz"], BLACK),
                   (2.8, ["0-0 무승부. 승점 +1 (...zzz)"], BLACK)],
             result=(3.1, "D", 1, "TOT 0 : 0 EVE"), heal=3.1),
        dict(kind="lion", name="ASTON VILLA", player="robertson", kit="home", len=8.8,
             msgs=[(0.2, ["ASTON VILLA가 나타났다!"], BLACK),
                   (1.4, ["로버트슨의 어설픈 걷어내기!", "VILLA가 선제골을 넣었다!"], BLACK),
                   (3.0, ["...0-3까지 끌려갔다."], RED),
                   (4.3, ["돌아와, 로버트슨! GO, 갤러거!"], BLACK),
                   (5.5, ["86' 갤러거 시즌 첫 골!", "90+' 반 헤케 헤더 골!"], BLACK),
                   (7.2, ["...but it's too late.", "2-3 패배! (희망고문 완성)"], RED)],
             result=(7.5, "L", 0, "TOT 2 : 3 AVL"), dmg=[1.9, 3.2, 7.5], hits=[5.8, 6.4],
             swap=(4.6, "gallagher")),
    ]
    MOODS = ["smile", "neutral", "sweat", "sweat", "sweat", "shock"]
    OUTRO = 4.4

    def __init__(self):
        self.starts = []
        acc = self.B0
        for f in self.FOES:
            self.starts.append(acc)
            acc += f["len"]
        self.end = acc
        self.dur = acc + self.OUTRO

    def results(self, t):
        return [f["result"] for f, s in zip(self.FOES, self.starts) if t >= s + f["result"][0]]

    def draw(self, img, d, t):
        if t < self.B0:
            d.rectangle([0, 0, W, H], fill=WHITE if (t < 0.9 and int(t * 11) % 2) else BLACK)
            k = max(0.0, (t - 0.55) / 0.45)
            for yy in range(0, H, 16):
                d.rectangle([0, yy, int(W * k), yy + 7], fill=BLACK)
                d.rectangle([W - int(W * k), yy + 8, W, yy + 15], fill=BLACK)
            return None
        d.rectangle([0, 0, W, H], fill=CREAM)
        d.ellipse([296, 128, 464, 158], fill=(176, 208, 144), outline=(120, 150, 90))
        d.ellipse([100, 188, 218, 208], fill=(176, 208, 144), outline=(120, 150, 90))
        res = self.results(t)
        pts = sum(r[2] for r in res)
        shake, msg, board = None, None, None
        idx = max([i for i, s in enumerate(self.starts) if t >= s], default=0)
        f, lt = self.FOES[idx], t - self.starts[idx]
        player = f["player"]
        if t < self.end:
            flash = any(0 <= lt - h < 0.3 and int(lt * 16) % 2 for h in f.get("hits", []))
            hp = 1.0 - 0.2 * sum(1 for h in f.get("hits", []) if lt >= h)
            ex = 300 + max(0, int((0.4 - lt) / 0.4 * 200))
            bob = 2 if int(t * 3) % 2 else 0
            spr = monster(f["kind"], t, flash)
            img.paste(spr, (ex, -6 + bob), spr)
            box(d, 8, 8, 236, 58, fill=WHITE, border=NAVY)
            text(d, 20, 14, f["name"], BLACK, shadow=None)
            text(d, 20, 34, "HP", GOLD, shadow=None)
            d.rectangle([48, 38, 226, 46], fill=BLACK)
            d.rectangle([50, 40, 50 + int(174 * hp), 44], fill=GREEN)
            for mt, ls, col in f["msgs"]:
                if lt >= mt:
                    msg = (ls, lt - mt, col)
            for dt in f.get("dmg", []):
                if 0 <= lt - dt < 0.4:
                    shake = (random.Random(int(t * 60)).randint(-5, 5), 0)
            if "heal" in f and 0 <= lt - f["heal"] < 0.9:
                rng = random.Random(int(t * 20))
                for _ in range(10):
                    d.text((rng.randint(110, 200), rng.randint(110, 196)), "✦", font=F16, fill=GOLD)
            if "swap" in f and lt >= f["swap"][0]:
                player = f["swap"][1]
            if 0 <= lt - f["result"][0] < 1.8:
                board = f["result"][3]
        else:
            lt2 = t - self.end
            if lt2 < 1.6:
                msg = (["SPURS는 눈앞이 캄캄해졌다..."], lt2 - 0.1, BLACK)
            else:
                msg = (["5경기 승점 2 · 2득 8실", "RANK 20/20 (꼴찌)"], lt2 - 1.6, RED)
        hurt = t < self.end and any(0 <= lt - dt < 0.6 for dt in f.get("dmg", []))
        if not (hurt and int(t * 16) % 2):
            blit(img, chibi(player, kit=f["kit"]), 130, 100, 3)
        if t < self.end and "swap" in f and 0 <= lt - f["swap"][0] < 0.35:
            rng = random.Random(int(t * 30))
            for _ in range(12):
                cx, cy, r = rng.randint(120, 190), rng.randint(100, 200), rng.randint(6, 14)
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=LGRAY)
        box(d, 8, 66, 100, 172, fill=WHITE, border=NAVY)
        ctext(d, 72, "DE ZERBI", BLACK, shadow=None, cx=54)
        blit(img, portrait("dezerbi", self.MOODS[min(len(res), 5)]), 20, 94, 2)
        box(d, 244, 140, 474, 205, fill=WHITE, border=NAVY)
        kitlab = "HOME" if f["kit"] == "home" else "AWAY"
        text(d, 254, 144, f"{PEOPLE[player]['short']} #{PEOPLE[player]['num']}", BLACK, shadow=None)
        text(d, 420, 144, kitlab, PURPLE if kitlab == "AWAY" else NAVY, shadow=None)
        text(d, 254, 164, "PTS", BLACK, shadow=None)
        d.rectangle([292, 169, 420, 177], fill=BLACK)
        if pts:
            d.rectangle([294, 171, 294 + int(124 * pts / 15), 175], fill=RED)
        text(d, 428, 164, f"{pts}/15", BLACK, shadow=None)
        text(d, 254, 184, "W-D-L", BLACK, shadow=None)
        for i, r in enumerate(res):
            x = 306 + i * 22
            d.rectangle([x, 184, x + 18, 200], fill=RED if r[1] == "L" else GRAY)
            text(d, x + 5, 184, r[1], WHITE, shadow=None)
        box(d, 6, 208, 474, 266, fill=WHITE, border=NAVY)
        if msg:
            lines_at(d, 18, 216, msg[0], msg[1], msg[2], shadow=None)
        if board:
            d.rectangle([126, 66, 354, 100], fill=NAVY, outline=WHITE, width=2)
            text(d, 134, 75, "FT", GOLD)
            ctext(d, 75, board, WHITE, cx=252)
        if t > self.end + 0.8:
            k = min(1.0, (t - self.end - 0.8) / 2.6)
            a = np.asarray(img).astype(np.float32)
            a[:206] *= 1 - k
            img.paste(Image.fromarray(a.astype(np.uint8)))
        return {"shake": shake}

    def audio(self, m, t0):
        m.sfx(t0, "encounter")
        music.saints(m, t0 + self.B0, self.end - self.B0, bpm=176, minor=True, lead="sq", duty=0.5, drums="roll",
                     vol=0.07)
        sfx = {"bee": "buzz", "magpie": "caw", "tree": "bump", "toffee": "snore", "lion": "roar"}
        for f, s in zip(self.FOES, self.starts):
            m.sfx(t0 + s + 0.1, sfx[f["kind"]])
            for mt, ls, _ in f["msgs"]:
                blip_lines(m, t0 + s + mt, ls)
            for dt in f.get("dmg", []):
                m.sfx(t0 + s + dt, "damage")
            for h in f.get("hits", []):
                m.sfx(t0 + s + h, "hit")
            if "heal" in f:
                m.sfx(t0 + s + f["heal"], "heal")
            if "swap" in f:
                m.sfx(t0 + s + f["swap"][0], "poof")
        music.saints_outro(m, t0 + self.end + 0.1)
        blip_lines(m, t0 + self.end + 0.1, ["SPURS는 눈앞이 캄캄해졌다..."])
        blip_lines(m, t0 + self.end + 1.6, ["5경기 승점 2 · 2득 8실", "RANK 20/20 (꼴찌)"])


# ------------------------------------------------------------------ 8. 카라바오컵

class Carabao(Scene):
    dur = 5.2

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(20, 30, 70))
        ctext(d, 20, "MEANWHILE... CARABAO CUP", GOLD)
        if t < 2.6:
            rng = random.Random(int(t * 8))
            for i in range(6):
                kk = (t * 1.2 + i / 6) % 1
                x, y = 60 + i * 72, 110 - kk * 30
                for a in range(8):
                    ang = a / 8 * math.tau
                    r = 6 + 24 * kk
                    d.point((x + math.cos(ang) * r, y + math.sin(ang) * r), fill=[GOLD, RED, WHITE][i % 3])
            ctext(d, 120, "vs 찰튼  5-1  WIN!!", WHITE, F32, shadow=NAVY2)
            ctext(d, 170, "(올 시즌 유일한 승리)", LGRAY)
        else:
            ctext(d, 110, "vs 리버풀 (A)  1-3", (255, 110, 100), F32, shadow=DRED)
            ctext(d, 160, "OUT. (탈락)", LGRAY)
            blit(img, chibi("dezerbi", mood="sad"), 222, 186, 2)

    def audio(self, m, t0):
        music.saints_intro(m, t0 + 0.2, bpm=190)
        m.sfx(t0 + 0.3, "fanfare")
        m.sfx(t0 + 2.6, "sad")


# ------------------------------------------------------------------ 9. 테트리스

class Tetris(Scene):
    dur = 8.5
    X0, Y0, C = 180, 15, 12
    DROP0, RATE = 0.8, 5.0
    LAND = 18

    def __init__(self):
        rng = random.Random(42)
        self.rows = {}
        for r in range(13, 20):
            holes = {4, 5, rng.choice([0, 1, 2, 7, 8, 9])}
            self.rows[r] = [c for c in range(10) if c not in holes]

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(8, 8, 24))
        for y in range(0, H, 8):
            for x in range((y // 8) % 2 * 8, W, 16):
                d.point((x, y), fill=(40, 40, 80))
        X0, Y0, C = self.X0, self.Y0, self.C
        danger = t >= 4.4 and blink(t, 3)
        d.rectangle([X0 - 3, Y0 - 3, X0 + 10 * C + 2, Y0 + 20 * C + 2], outline=LGRAY, width=2)
        d.rectangle([X0, Y0, X0 + 10 * C - 1, Y0 + 20 * C - 1], fill=BLACK)
        d.rectangle([X0, Y0 + 17 * C, X0 + 10 * C - 1, Y0 + 20 * C - 1],
                    fill=(100, 0, 0) if danger else (50, 0, 0))
        for r, cols in self.rows.items():
            for c in cols:
                x, y = X0 + c * C, Y0 + r * C
                d.rectangle([x, y, x + C - 1, y + C - 1], fill=GRAY, outline=(70, 70, 70))
                d.point((x + 2, y + 2), fill=LGRAY)
        row = min(self.LAND, max(0, int((t - self.DROP0) * self.RATE)))
        for dr in (0, 1):
            for dc in (4, 5):
                x, y = X0 + dc * C, Y0 + (row + dr) * C
                d.rectangle([x, y, x + C - 1, y + C - 1], fill=NAVY2, outline=WHITE)
        if t < 4.4:
            ctext(d, Y0 + row * C - 18, "SPURS", WHITE, cx=X0 + 5 * C)
        text(d, 312, Y0 + 17 * C + 8, "◀ 강등권", RED)
        for y, label, val, col in ((15, "SCORE", "2 (승점)", WHITE), (75, "LINES", "0 (승리 수)", WHITE),
                                   (135, "LEVEL", "20위 (꼴찌)", RED)):
            box(d, 12, y, 168, y + 52)
            text(d, 24, y + 6, label, GOLD)
            text(d, 24, y + 28, val, col)
        box(d, 312, 15, 468, 95)
        text(d, 324, 21, "NEXT", GOLD)
        text(d, 324, 43, "맨유 (AWAY)", WHITE)
        text(d, 324, 65, "10.10", LGRAY)
        box(d, 312, 103, 468, 163)
        text(d, 324, 111, "득점 GF 2", WHITE)
        text(d, 324, 135, "실점 GA 8", RED)
        text(d, 24, 238, "SPURS-TRIS", NAVY2)
        if t >= 5.0 and blink(t, 2):
            d.rectangle([0, 112, W, 158], fill=RED)
            ctext(d, 119, "WARNING!! 강등권", WHITE, F32, shadow=DRED)

    def audio(self, m, t0):
        music.saints(m, t0 + 0.3, 4.1, bpm=210, minor=True, lead="sq", duty=0.5, drums="fast", harmony=False)
        for k in range(1, self.LAND + 1):
            m.sfx(t0 + self.DROP0 + k / self.RATE, "tick")
        m.sfx(t0 + self.DROP0 + self.LAND / self.RATE + 0.02, "lock")
        for k in range(7):
            m.sfx(t0 + 5.0 + k * 0.5, "siren")


# ------------------------------------------------------------------ 10. 팬 시위

class Protest(Scene):
    dur = 8.4
    B1 = "PROMISED CHANGE, DELIVERED FAILURE ★ "
    B2 = "LOVE TOTTENHAM, HATE ENIC ★ "

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(8, 8, 40))
        for lx in (30, 450):
            d.polygon([(lx, 12), (lx - 80, 110), (lx + 80, 110)], fill=(24, 24, 64))
            d.ellipse([lx - 8, 4, lx + 8, 20], fill=WHITE)
        ctext(d, 4, "\"Levy has gone and nothing has changed\"", WHITE)
        ctext(d, 24, "(레비는 떠났는데 바뀐 게 없다 ─ 팬 단체)", LGRAY)
        d.rectangle([0, 56, W, 190], fill=(30, 30, 50))
        rng = random.Random(9)
        for row, y in enumerate(range(58, 188, 9)):
            for col, x in enumerate(range(2 + (row % 2) * 4, W, 8)):
                up = math.sin(t * 9 + col * 0.8 + row) > 0.3
                bob = -2 if up else 0
                c = rng.choice([SKIN, SKIN_D, (140, 90, 60), (90, 60, 40)])
                hat = rng.random()
                d.ellipse([x, y + bob, x + 5, y + 5 + bob], fill=c)
                if hat < 0.3:
                    d.rectangle([x, y + bob, x + 5, y + 1 + bob], fill=NAVY2 if hat < 0.15 else WHITE)
                if up and (col + row) % 5 == 0:
                    d.line([(x - 1, y + bob - 1), (x - 3, y + bob - 5)], fill=c, width=2)
                    if (col + row) % 10 == 0:
                        d.rectangle([x - 5, y + bob - 9, x - 2, y + bob - 6], fill=ORANGE)
        for y, s, sp in ((78, self.B1, 55), (132, self.B2, -48)):
            d.rectangle([0, y, W, y + 20], fill=WHITE, outline=NAVY)
            wfull = tw(s)
            off = (t * sp) % wfull
            text(d, -int(off) if sp > 0 else int(off) - wfull, y + 2, s * 5, NAVY, shadow=None)
        if blink(t, 2):
            pow_box(d, "ENIC OUT!", 240, 108, YELLOW, RED, F16)
        box(d, 6, 196, 474, 266)
        text(d, 18, 203, "\"약속은 CHANGE, 결과는 FAILURE\"", GOLD)
        text(d, 18, 223, "\"토트넘은 LOVE, ENIC(구단주)은 HATE\"", GOLD)
        text(d, 18, 244, "RAGE GAUGE", WHITE)
        k = min(1.0, max(0.0, (t - 0.8) / 4.5))
        d.rectangle([122, 247, 380, 259], fill=BLACK, outline=WHITE)
        d.rectangle([124, 249, 124 + int(254 * k), 257], fill=RED if k > 0.7 else ORANGE)
        if k >= 1.0 and blink(t, 3):
            text(d, 392, 244, "MAX!!", RED)

    def audio(self, m, t0):
        music.saints(m, t0 + 0.2, 7.8, bpm=120, minor=True, lead="sq", duty=0.25, drums="march", vol=0.07)
        crowd = noise(8.0, 0.04, None, hold=1)
        crowd = np.convolve(crowd, np.ones(20) / 20, mode="same") * 3
        m.add(t0 + 0.1, crowd)
        for k in range(8):
            m.sfx(t0 + 0.4 + k * 1.0, "boo")


# ------------------------------------------------------------------ 11. 그 사이 (뮌헨 / LA)

class Meanwhile(Scene):
    dur = 7.6

    def draw(self, img, d, t):
        d.rectangle([0, 0, 239, H], fill=(220, 40, 60))
        d.rectangle([240, 0, W, H], fill=(255, 190, 120))
        d.ellipse([330, 30, 410, 110], fill=(255, 230, 150))
        d.rectangle([240, 170, W, H], fill=(245, 214, 150))
        for i in range(3):
            y = 150 + i * 6
            d.line([(240, y), (W, y)], fill=(80, 170, 230), width=3)
        d.line([(240, 0), (240, H)], fill=BLACK, width=4)
        ctext(d, 6, "MEANWHILE IN MUNICH", WHITE, cx=120)
        ctext(d, 6, "MEANWHILE IN LA", NAVY, shadow=WHITE, cx=360)
        blit(img, chibi("kane"), 93, 130, 3)
        wob = int(math.sin(t * 5) * 3)
        for i in range(3):
            trophy(d, 120 + wob * (i + 1), 102 - i * 26)
        ctext(d, 26, "케인: 드디어 트로피 수집 중", GOLD, cx=120)
        d.polygon([(290, 190), (430, 190), (410, 170), (310, 170)], fill=(80, 180, 200), outline=BLACK)
        blit(img, chibi("son", mood="smile"), 333, 90, 3)
        d.rectangle([346, 116, 382, 122], fill=BLACK)
        ctext(d, 26, "쏘니: 행복 중 :)", NAVY, shadow=WHITE, cx=360)
        if t > 3.8:
            k = min(1.0, (t - 3.8) / 0.4)
            y0 = int(270 - 90 * k)
            d.rectangle([110, y0, 370, y0 + 100], fill=(40, 40, 60), outline=WHITE, width=2)
            blit(img, COCK_CRY, 130, y0 + 20, 2)
            text(d, 180, y0 + 16, "SPURS FANS:", GOLD)
            text(d, 180, y0 + 38, "우리 애들 잘 지내네...", WHITE)
            text(d, 180, y0 + 58, "ㅠㅠ (눈물)", (110, 190, 255))

    def audio(self, m, t0):
        music.saints(m, t0 + 0.1, 3.7, bpm=130, transpose=5, lead="sq", duty=0.125, drums="soft", vol=0.08)
        m.sfx(t0 + 3.8, "sad")


# ------------------------------------------------------------------ 12. 컨티뉴

class Continue(Scene):
    dur = 10.0
    COUNT0, STEP = 0.3, 0.7
    COIN = 4.5

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        if t < 5.2:
            ctext(d, 12, "CONTINUE?", RED, F32, shadow=DRED)
            n = 9 - int(max(0.0, t - self.COUNT0) / self.STEP)
            if t >= self.COUNT0:
                ctext(d, 56, str(max(n, 3)), WHITE, F64, shadow=GRAY)
            if 2.0 < t < 4.5 and blink(t, 2):
                ctext(d, 236, "INSERT COIN (동전을 넣으세요)", GOLD)
        d.rectangle([392, 130, 432, 180], fill=(40, 40, 40), outline=LGRAY)
        d.rectangle([408, 136, 414, 172], fill=BLACK)
        if self.COIN <= t < self.COIN + 0.5:
            k = (t - self.COIN) / 0.5
            cy = -16 + 150 * k * k
            d.ellipse([401, cy, 421, cy + 20], fill=GOLD, outline=BLACK)
            text(d, 407, cy + 2, "£", BROWN, shadow=None)
            if cy < 100:
                text(d, 428, cy, "ENIC", LGRAY)
        if t >= 5.0:
            text(d, 372, 190, "CREDIT 01", WHITE)
        k = t - 5.4
        if k >= 0:
            jy = -int(50 * 4 * (k / 0.5) * (1 - k / 0.5)) if k < 0.5 else 0
            blit(img, chibi("dezerbi"), 222, 150 + jy, 2)
        else:
            blit(img, chibi("dezerbi", mood="x"), 222, 150, 2, flip_v=True)
        if t >= 6.0:
            ctext(d, 20, "NEXT STAGE ▶ vs 맨유 (AWAY)", WHITE)
            ctext(d, 42, "10.10 @ 올드 트래포드", LGRAY)
        if t >= 7.0:
            text(d, 120, 88, "DE ZERBI LIFE", RED)
            for i in range(3):
                col = RED if i == 0 else (70, 60, 70)
                x = 250 + i * 26
                d.polygon([(x, 94), (x + 5, 89), (x + 10, 94), (x + 5, 104)], fill=col)
                d.polygon([(x + 10, 94), (x + 15, 89), (x + 20, 94), (x + 15, 104)], fill=col)
                d.rectangle([x + 5, 94, x + 15, 100], fill=col)
                d.polygon([(x, 94), (x + 10, 106), (x + 20, 94)], fill=col)

    def audio(self, m, t0):
        music.saints(m, t0 + 0.3, 4.2, bpm=80, minor=True, lead="tri", vol=0.12, drums=False, harmony=False)
        for k in range(7):
            m.sfx(t0 + self.COUNT0 + k * self.STEP, "tick")
        m.sfx(t0 + self.COIN, "coin")
        m.sfx(t0 + 5.0, "ding")
        m.sfx(t0 + 5.4, "jump")
        music.saints_intro(m, t0 + 6.0, bpm=180)
        m.sfx(t0 + 7.0, "gulp")


# ------------------------------------------------------------------ 13. 엔딩

class Ending(Scene):
    dur = 10.0
    fade_out = 1.4
    WALKERS = [("dezerbi", None), ("vdv", "home"), ("fernandes", "away"), ("tonali", "home"),
               ("gallagher", "away"), ("robertson", "home")]

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        draw_stars(d, t, 6, n=40, seed=3)
        ctext(d, 8, "THANK YOU, SPURS FANS!", WHITE)
        if t > 0.8:
            ctext(d, 32, reveal("BUT OUR TROPHY IS IN ANOTHER CASTLE!", t - 0.8, 18), GOLD)
        if t > 2.8:
            ctext(d, 54, reveal("하지만 트로피는 다른 성에 있습니다!", t - 2.8, 14), WHITE)
        cx, cy = 390, 136
        d.rectangle([cx, cy, cx + 60, cy + 42], fill=(150, 80, 40), outline=BLACK)
        for bx in range(cx, cx + 60, 12):
            d.rectangle([bx, cy - 8, bx + 6, cy], fill=(150, 80, 40), outline=BLACK)
        d.rectangle([cx + 22, cy + 18, cx + 38, cy + 42], fill=BLACK)
        d.line([(cx + 30, cy - 8), (cx + 30, cy - 30)], fill=LGRAY)
        d.polygon([(cx + 30, cy - 30), (cx + 46, cy - 25), (cx + 30, cy - 20)], fill=RED)
        text(d, cx + 26, cy + 1, "?", GOLD, shadow=None)
        d.line([(0, 178), (W, 178)], fill=GRAY)
        for i, (k, kit) in enumerate(self.WALKERS):
            x = -10 + t * 16 + i * 44
            blit(img, chibi(k, int(t * 5 + i) % 2, kit=kit), x, 110, 2)
        if t > 5.0:
            ctext(d, 188, "COME ON YOU SPURS!", GOLD, F32, shadow=NAVY2)
        if t > 5.6:
            ctext(d, 228, "※ 2026.09.24 기준 실제 결과 바탕 풍자 패러디", GRAY)
            ctext(d, 248, "인물은 캐리커처 · BGM: When the Saints Go Marching In", GRAY)

    def audio(self, m, t0):
        music.saints(m, t0 + 0.2, 8.6, bpm=150, echo=True, drums="march")
        for n in ("C4", "E4", "G4", "C5"):
            m.notes(t0 + 8.8, f"{n}:1.2", vol=0.05)


# -------------------------------------------------------------------------- main

def build():
    return [
        Boot(), Title(), ColdOpen(), Previously(),
        StageCard("STAGE 1", "2025-26 SEASON", "감독 3명, 강등 직전까지 간 시즌",
                  [("frank", None), ("tudor", None), ("dezerbi", None)]),
        ManagerSelect(), Platformer(),
        StageCard("STAGE 2", "TRANSFER MARKET", "겨우 살아남은 구단, 지갑을 활짝 열다",
                  [("fernandes", "home"), ("tonali", "away"), ("vanhecke", "home"), ("robertson", "away"),
                   ("senesi", "home"), ("mudryk", "away"), ("adarabioyo", "home")]),
        Shop(),
        StageCard("STAGE 3", "2026-27 SEASON", "큰돈 쓴 새 팀, 개막 5경기의 결과는?"),
        Battle(), Carabao(), Tetris(), Protest(), Meanwhile(), Continue(), Ending(),
    ]


def main():
    scenes = build()
    starts, acc = [], 0.0
    for s in scenes:
        starts.append(acc)
        acc += s.dur
    total = acc
    mix = Mixer(total)
    for s, st in zip(scenes, starts):
        s.audio(mix, st)
    buf = mix.buf[: int(total * SR)]
    buf = np.tanh(buf * 1.1)
    buf = buf / max(1e-9, np.max(np.abs(buf))) * 0.88
    wav_path = os.path.join(HERE, "_audio.wav")
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((buf * 32767).astype(np.int16).tobytes())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W * SCALE}x{H * SCALE}",
           "-r", str(FPS), "-i", "-", "-i", wav_path, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
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
        arr = np.asarray(img)
        if res.get("shake"):
            arr = np.roll(arr, res["shake"][0], axis=1)
        k = 1.0
        if sc.fade_in and lt < sc.fade_in:
            k = lt / sc.fade_in
        if sc.fade_out and lt > sc.dur - sc.fade_out:
            k = min(k, (sc.dur - lt) / sc.fade_out)
        if k < 1.0:
            arr = (arr * (round(max(0.0, k) * 4) / 4)).astype(np.uint8)
        big = arr.repeat(SCALE, 0).repeat(SCALE, 1)
        big[3::4] = (big[3::4] * 0.72).astype(np.uint8)
        proc.stdin.write(big.tobytes())
        if fi % 900 == 0:
            print(f"frame {fi}/{nframes}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(wav_path)
    print("wrote", OUT, f"({total:.1f}s)")


if __name__ == "__main__":
    main()
