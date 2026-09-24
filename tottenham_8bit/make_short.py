#!/usr/bin/env python3
"""토트넘 대모험 26/27 ─ 1분 쇼츠 편집본.

8비트 게임 패러디를 1분 이내로 압축한 빠른 버전. 한글 위주, BGM은 새로 작곡한 칩튠 게임 음악.

    pip install pillow numpy imageio-ffmpeg
    python3 make_short.py             # -> tottenham_short.mp4 (1920x1080)
"""
import math
import os
import random
import subprocess
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

from engine import (BLACK, BROWN, CREAM, DGREEN, DRED, F16, F32, F64, FPS, GOLD, GRAY, GREEN, H, LGRAY, NAVY,
                    NAVY2, ORANGE, RED, SCALE, SKIN, SKIN_D, SKY, SR, W, WHITE, YELLOW, Mixer, blink, blit, box,
                    ctext, draw_flames, draw_stars, drum, make_stamp, noise, text, tw)
from sprites import COCK, COCK_CRY, PEOPLE, chibi, draw_hammer, kit_icon, monster, portrait

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tottenham_short.mp4")
CPS = 40
PURPLE = (150, 90, 255)
PINK = (255, 70, 170)
STAMP = make_stamp("경질!")

# ------------------------------------------------------------------ 칩튠 BGM (전부 새로 작곡)
TITLE = ("C5 - E5 G5 C6 - B5 G5 A5 - F5 A5 G5 - - . E5 - G5 C6 E6 - D6 C6 B5 - G5 A5 C6 - - .",
         "C3 . C3 . G2 . G2 . F2 . F2 . G2 . G2 . A2 . A2 . E2 . E2 . F2 . G2 . C3 . C3 .")
STAGE = ("G5 . D5 G5 . B5 A5 G5 E5 . C5 E5 G5 - . . F#5 . D5 F#5 . A5 G5 F#5 G5 - - - . . . .",
         "G2 . D3 . G2 . D3 . C3 . G2 . C3 . G2 . D3 . A2 . D3 . A2 . G2 . D3 . G2 . D3 .")
SHOP = ("F5 . A5 . C6 . A5 . Bb5 . G5 . E5 . C5 . F5 . A5 . C6 . F6 . E6 . C6 . F6 - - .",
        "F3 . C3 . F3 . C3 . Bb2 . F3 . C3 . G3 . F3 . C3 . A2 . A3 . C3 . C3 . F3 . C3 .")
BATTLE = ("E5 . E5 G5 . E5 A5 . G5 . F#5 . D5 . B4 . E5 . E5 G5 . E5 B5 . A5 . G5 . F#5 . G5 A5",
          "E2 E3 E2 E3 E2 E3 E2 E3 D2 D3 D2 D3 B1 B2 B1 B2")
SAD = ("A4 - C5 - E5 - D5 C5 B4 - - - G#4 - B4 - A4 - - - - - - -", "A2 - - - E2 - - - F2 - - - E2 - - -")
ANGRY = ("A4 A4 C5 A4 D5 A4 C5 A4 G4 G4 B4 G4 E5 D5 C5 B4", "A2 A2 A2 A2 G2 G2 G2 G2 F2 F2 F2 F2 E2 E2 E2 E2")
HAPPY = ("C5 E5 G5 E5 A4 C5 E5 C5 F4 A4 C5 A4 G4 B4 D5 B4", "C3 . A2 . F2 . G2 .")


def play(m, t0, dur, song, bpm, drums="k h s h", duty=0.25, vol=0.08, spb=2):
    lead, bass = song
    m.seq(t0, dur, lead, bpm, spb, "sq", vol, duty)
    m.seq(t0, dur, bass, bpm, spb, "tri", 0.2)
    if drums:
        m.seq(t0, dur, drums, bpm, spb, "drum")


def reveal(s, since):
    return "" if since < 0 else s[: int(since * CPS)]


def blips(m, t0, s):
    for k, ch in enumerate(s):
        if ch != " " and k % 3 == 0:
            m.sfx(t0 + k / CPS, "blip")


def say(d, x, y, lines, since, col=WHITE, step=22, shadow=BLACK):
    for s in lines:
        text(d, x, y, reveal(s, since), col, shadow=shadow)
        since -= len(s) / CPS + 0.05
        y += step


def dialog(d, lines, since, col=WHITE, name=None, y0=206):
    box(d, 6, y0, 474, 266)
    if name:
        w = tw(name) + 16
        d.rectangle([14, y0 - 12, 14 + w, y0 + 6], fill=NAVY, outline=WHITE)
        text(d, 22, y0 - 11, name, GOLD)
    say(d, 18, y0 + 12, lines, since, col)


def banner(d, s, col=WHITE, y=26):
    w = tw(s)
    d.rectangle([W // 2 - w // 2 - 6, y, W // 2 + w // 2 + 6, y + 20], fill=BLACK)
    ctext(d, y + 2, s, col)


def trophy(d, x, y, col=GOLD):
    d.ellipse([x - 12, y + 2, x - 4, y + 12], outline=BLACK, width=2)
    d.ellipse([x + 4, y + 2, x + 12, y + 12], outline=BLACK, width=2)
    d.polygon([(x - 8, y), (x + 8, y), (x + 6, y + 14), (x, y + 18), (x - 6, y + 14)], fill=col, outline=BLACK)
    d.rectangle([x - 2, y + 18, x + 2, y + 22], fill=col, outline=BLACK)
    d.rectangle([x - 7, y + 22, x + 7, y + 26], fill=BROWN, outline=BLACK)


def pow_box(d, s, cx, cy, col=YELLOW, bg=RED, font=F32):
    w = tw(s, font) + 20
    h = 44 if font is F32 else 24
    pts = [(cx + math.cos(i / 20 * math.tau) * (w / 2 + 14) * (1.0 if i % 2 == 0 else 0.78),
            cy + math.sin(i / 20 * math.tau) * (h / 2 + 12) * (1.0 if i % 2 == 0 else 0.78)) for i in range(20)]
    d.polygon(pts, fill=bg, outline=BLACK)
    ctext(d, cy - (18 if font is F32 else 9), s, col, font, shadow=BLACK, cx=cx)


def confetti(d, t, seed=1, n=60):
    rng = random.Random(seed)
    for _ in range(n):
        x0, sp = rng.uniform(0, W), rng.uniform(60, 120)
        y = (rng.uniform(-H, 0) + t * sp) % (H + 10) - 5
        d.rectangle([x0, y, x0 + 2, y + 1], fill=rng.choice([RED, GOLD, NAVY2, WHITE, PINK]))


class Scene:
    dur = 1.0
    fade_in = 0.08
    fade_out = 0.08

    def draw(self, img, d, t):
        pass

    def audio(self, m, t0):
        pass


# ------------------------------------------------------------------ 1. 타이틀 (3.0s)

class Title(Scene):
    dur = 3.0
    fade_in = 0.0
    LINE = [("fernandes", "home"), ("tonali", "away"), ("vdv", "home"), ("dezerbi", None), ("gallagher", "away"),
            ("vanhecke", "home"), ("mudryk", "away")]

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=NAVY)
        draw_stars(d, t, 40)
        k = min(1.0, t / 0.4)
        y = int(-70 + 76 * k) + (int(4 * math.sin(min(1, (t - 0.4) / 0.3) * math.pi)) if t > 0.4 else 0)
        ctext(d, y, "토트넘 대모험", WHITE, F64, shadow=GOLD)
        if t > 0.5:
            ctext(d, 76, "26/27 ~ 강등권의 전설 ~", GOLD)
        d.rectangle([0, 170, W, 184], fill=(24, 120, 48))
        for i, (key, kit) in enumerate(self.LINE):
            if t > 0.7 + i * 0.08:
                bob = -2 if (int(t * 6) + i) % 2 else 0
                blit(img, chibi(key, kit=kit), 42 + i * 58, 104 + bob, 2)
        if t < 2.2:
            if blink(t, 3):
                ctext(d, 214, "▶ 시작 버튼을 누르세요", LGRAY)
        elif blink(t, 10):
            ctext(d, 214, "▶ 시작!", YELLOW)

    def audio(self, m, t0):
        m.sfx(t0 + 0.4, "land")
        play(m, t0 + 0.4, 1.8, TITLE, 180)
        m.sfx(t0 + 2.2, "start")


# ------------------------------------------------------------------ 2. 콜드 오픈 (3.6s)

class ColdOpen(Scene):
    dur = 3.6
    FREEZE = 0.8

    def draw(self, img, d, t):
        tt = min(t, self.FREEZE) if t < 3.0 else self.FREEZE - (t - 3.0) * 3
        d.rectangle([0, 0, W, H], fill=(40, 8, 8))
        for i in range(6):
            yy = 170 + i * 16
            pts = [(0, H)] + [(x, yy + int(3 * math.sin(x * 0.05 + tt * 3 + i))) for x in range(0, W + 8, 8)] + [(W, H)]
            d.polygon(pts, fill=(120 + i * 22, 20 + i * 18, 10))
        d.rectangle([150, 150, 330, 176], fill=(80, 60, 50), outline=BLACK)
        blit(img, chibi("dezerbi", mood="shock" if tt > 0.4 else "smile"), 190, 82, 2)
        blit(img, COCK, 260, 116, 2)
        d.rectangle([0, 0, W, 22], fill=BLACK)
        text(d, 8, 3, "현재 순위: 20위 (꼴찌)", RED)
        text(d, 300, 3, "승점 2 · 0승", WHITE)
        if self.FREEZE <= t < 3.0:
            a = np.asarray(img).astype(np.float32)
            a = a.mean(axis=2, keepdims=True) * np.array([1.05, 0.9, 0.7])
            img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
            text(d, 20, 40, "*끼익* (정지 화면)", WHITE)
            if t < 2.0:
                dialog(d, ["그렇다. 저게 우리 팀이다.", "리그 꼴찌, 강등권 한가운데."], t - self.FREEZE, GOLD, "해설")
            else:
                dialog(d, ["어쩌다 여기까지 왔냐고?", "처음부터 보자..."], t - 2.0, WHITE, "해설")
        if t >= 3.0:
            rng = random.Random(int(t * 30))
            for _ in range(8):
                y = rng.randint(0, H)
                d.rectangle([0, y, W, y + rng.randint(1, 3)], fill=WHITE)
            text(d, 20, 30, "◀◀ 되감기", WHITE, F32)

    def audio(self, m, t0):
        play(m, t0, 0.8, SAD, 120, drums=None, duty=0.5)
        m.sfx(t0 + self.FREEZE, "scratch")
        blips(m, t0 + self.FREEZE, "그렇다. 저게 우리 팀이다. 리그 꼴찌, 강등권 한가운데.")
        blips(m, t0 + 2.0, "어쩌다 여기까지 왔냐고? 처음부터 보자...")
        m.sfx(t0 + 3.0, "rewind")


# ------------------------------------------------------------------ 3. 플랫포머 (지난 시즌, 10.4s)

class Platformer(Scene):
    dur = 10.4
    INTRO = 0.7
    SPD = 120.0
    GROUND = 222
    HX = 110
    HERO_Y = GROUND - 67
    HITS = [1.3, 3.3, 5.3]
    SYMS = ["패", "패", "무"]
    WINLESS = [8, 12, 15]
    HIT_TXT = ["8경기 연속 무승", "구단 최초 6연패", "15경기 연속 무승"]
    HOOKS = [(1.9, "frank", "프랭크 경질! (8개월)"), (3.9, "tudor", "투도르 경질! (44일)")]
    DROPS = [(2.6, "tudor", "투도르 부임 (임시)"), (4.6, "dezerbi", "데 제르비 부임 (시즌 3번째!)")]
    PAUSES = [(1.9, 2.9), (3.9, 4.9)]
    CAM_STOP, WALK, JUMP, LAND = 5.8, 5.8, 6.2, 6.9
    HAMMER = 7.0
    SURV = 8.1
    ARS = 9.3

    def __init__(self):
        cf = self.cam(self.CAM_STOP)
        self.pit0 = int(round((cf + 232) / 16)) * 16
        self.pit1 = self.pit0 + 112
        self.ps = self.pit0 - cf

    def moving(self, t):
        t = min(t, self.CAM_STOP)
        mv = max(0.0, t - self.INTRO)
        for a, b in self.PAUSES:
            if t > a:
                mv -= min(t, b) - a
        return mv

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
            ctext(d, 70, "1스테이지: 지난 시즌 (2025-26)", WHITE)
            for i, k in enumerate(["frank", "tudor", "dezerbi"]):
                blit(img, chibi(k), 170 + i * 50, 112, 2)
            ctext(d, 196, "감독 × 3", GOLD)
            return
        if t >= self.ARS:
            k = t - self.ARS
            d.rectangle([0, 0, W, H], fill=(20, 20, 30))
            d.rectangle([90, 30, 390, 190], fill=(40, 40, 50), outline=LGRAY, width=3)
            d.rectangle([100, 40, 380, 180], fill=(200, 30, 40))
            confetti(d, k, 9, 40)
            trophy(d, 240, 60)
            ctext(d, 110, "속보: 아스날 리그 우승", WHITE)
            ctext(d, 140, "(같은 날...)", GOLD)
            blit(img, COCK_CRY, 216, 196, 2)
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
            ctext(d, 232, "2부 리그", RED, cx=px0 + 56, shadow=None)
            ctext(d, 250, "↓↓↓", DRED, cx=px0 + 56, shadow=None)
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
                if 0 <= k < 0.7:
                    iy = 78 - int(24 * min(1.0, k / 0.25))
                    d.rectangle([bx, iy, bx + 17, iy + 17], fill=RED if self.SYMS[i] == "패" else GRAY, outline=WHITE)
                    text(d, bx + 1, iy, self.SYMS[i], WHITE, shadow=None)
        hx, hy, air, show = self.HX, self.HERO_Y, False, True
        mgr = self.manager(t)
        hook = None
        for (ht, who, _), (dr, _, _) in zip(self.HOOKS, self.DROPS):
            k = t - ht
            if 0 <= k < 0.6:
                mgr = who
                if k < 0.22:
                    hook = -40 + (self.HX + 76) * (k / 0.22)
                else:
                    kk = k - 0.22
                    dx = -2400 * kk * kk - 300 * kk
                    hx += dx
                    hook = self.HX + 36 + dx
            elif ht + 0.6 <= t < dr:
                show = False
        for dr, who, _ in self.DROPS:
            k = t - dr
            if 0 <= k < 0.3:
                hy = -70 + (self.HERO_Y + 70) * (k / 0.3) ** 2
        if t < self.CAM_STOP:
            for ht in self.HITS:
                k = t - (ht - 0.22)
                if 0 <= k < 0.44:
                    hy -= 60 * 4 * (k / 0.44) * (1 - k / 0.44)
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
            if t < self.LAND + 0.6:
                hx += 1 if int(t * 16) % 2 else -1
        moving = (t < self.CAM_STOP and not any(a <= t < b for a, b in self.PAUSES)) or self.WALK <= t < self.JUMP
        frame = 1 if air or (moving and int(t * 10) % 2) else 0
        if show:
            blit(img, chibi(mgr, frame, mood="shock" if hook is not None else "smile"), hx, hy, 2)
        if hook is not None:
            y = self.HERO_Y + 24
            d.line([(-10, y), (hook, y)], fill=(150, 90, 40), width=5)
            d.arc([hook - 16, y, hook + 16, y + 32], 270, 90, fill=(150, 90, 40), width=5)
        for ht, who, _ in self.HOOKS:
            if 0.15 <= t - ht < 0.7:
                box(d, 150, 54, 330, 128)
                blit(img, portrait(who, "shock"), 160, 60, 2)
                text(d, 236, 72, "경질!", RED, F32)
        if t >= self.HAMMER:
            k = t - self.HAMMER
            wx = -30 + 420 * k
            wy = self.GROUND - 31
            edge = self.ps - 4
            if wx > edge:
                kf = (wx - edge) / 420
                wx = edge + 50 * kf
                wy += 0.5 * 900 * kf * kf
            if wy < H:
                draw_hammer(d, wx, wy, t, mood="shock" if wx >= edge else "happy")
        wl = 0
        for i, ht in enumerate(self.HITS):
            if t >= ht:
                wl = self.WINLESS[i]
        text(d, 10, 4, "토트넘", WHITE)
        text(d, 150, 4, f"무승 {wl:02d}", WHITE)
        text(d, 270, 4, f"감독: {PEOPLE[mgr]['short']}", WHITE)
        b = None
        for i, ht in enumerate(self.HITS):
            if 0 <= t - ht < 0.6:
                b = (self.HIT_TXT[i], RED)
        for ht, who, s in self.HOOKS:
            if 0 <= t - ht < 0.7:
                b = (s, RED)
        for dr, who, s in self.DROPS:
            if 0 <= t - dr < 0.9:
                b = (s, WHITE)
        if self.WALK <= t < self.LAND:
            b = ("최종전 vs 에버튼 ─ 지면 강등!", WHITE)
        elif self.LAND <= t < self.LAND + 0.7:
            b = ("팔리냐 결승골 1-0! 잔류!!", GOLD)
        elif self.LAND + 0.7 <= t < self.SURV:
            b = ("대신 웨스트햄이 강등...", LGRAY)
        if b:
            banner(d, *b)
        if t >= self.SURV:
            box(d, 90, 64, 390, 160)
            ctext(d, 72, "생존!", GOLD, F32)
            ctext(d, 112, "17위 · 승점 41", WHITE)
            ctext(d, 134, "(2시즌 연속 17위)", LGRAY)

    def audio(self, m, t0):
        for a, b in [(self.INTRO, 1.9), (2.9, 3.9), (4.9, self.CAM_STOP)]:
            play(m, t0 + a, b - a, STAGE, 200)
        for ht in self.HITS:
            m.sfx(t0 + ht - 0.22, "jump")
            m.sfx(t0 + ht, "bump")
        for ht, _, _ in self.HOOKS:
            m.sfx(t0 + ht, "hook")
            m.sfx(t0 + ht + 0.22, "yank")
            m.sfx(t0 + ht + 0.15, "stamp")
        for dr, _, _ in self.DROPS:
            m.sfx(t0 + dr, "fall")
            m.sfx(t0 + dr + 0.3, "land")
        for k in range(10):
            m.add(t0 + self.JUMP + k * 0.07, drum("h") * 2)
        m.sfx(t0 + self.JUMP, "jump")
        m.sfx(t0 + self.LAND, "land")
        m.notes(t0 + self.LAND + 0.05, "C6:0.08 E6:0.08 G6:0.2", vol=0.08, duty=0.25)
        m.sfx(t0 + self.LAND + 0.6, "fall")
        m.sfx(t0 + self.SURV, "fanfare")
        m.sfx(t0 + self.ARS, "sad")


# ------------------------------------------------------------------ 4. 이적시장 (6.8s)

class Shop(Scene):
    dur = 6.8
    ITEMS = [("fernandes", "18", "페르난데스", "£85M", "웨스트햄에서 · 구단 신기록"),
             ("tonali", "16", "토날리", "£92.5M", "뉴캐슬에서"),
             (None, "17", "사비뉴", "£75M", "맨시티에서"),
             ("vanhecke", "6", "반 헤케", "£52M", "브라이튼에서"),
             ("robertson", "3", "로버트슨", "무료", "리버풀에서"),
             ("senesi", "5", "세네시", "무료", "본머스에서"),
             ("mudryk", "27", "무드릭", "임대", "첼시에서"),
             (None, "22", "마르무시", "임대", "맨시티에서"),
             ("adarabioyo", "4", "아다라비오요", "영입", "첼시에서")]
    BUY0, GAP = 0.5, 0.36
    KITS, SQUAD, SPOIL = 3.9, 5.2, 6.0

    def draw(self, img, d, t):
        if t >= self.KITS:
            d.rectangle([0, 0, W, H], fill=(10, 10, 30))
            draw_stars(d, t, 10)
            d.rectangle([0, 170, W, 200], fill=(40, 40, 80))
            if t < self.SQUAD:
                blit(img, chibi("vdv", kit="home"), 150, 104, 2)
                blit(img, chibi("vdv", 1, kit="away"), 294, 104, 2)
                for x, kit in ((155, "home"), (299, "away")):
                    blit(img, kit_icon(kit), x, 56, 2)
                    for i in range(8):
                        a = i / 8 * math.tau + t * 3
                        cx = x + 20
                        d.line([(cx + math.cos(a) * 24, 76 + math.sin(a) * 24),
                                (cx + math.cos(a) * 36, 76 + math.sin(a) * 36)], fill=GOLD, width=2)
                dialog(d, ["아이템 획득! 26/27 홈·원정 유니폼", "(원정은 네온 번개 무늬!)"], t - self.KITS - 0.1, GOLD,
                       "새 주장 반 더 벤")
            else:
                squad = [("fernandes", "home"), ("tonali", "away"), ("robertson", "home"), ("vdv", "home"),
                         ("vanhecke", "away"), ("senesi", "home"), ("mudryk", "away"), ("adarabioyo", "home")]
                for i, (k, kit) in enumerate(squad):
                    bob = -3 if (int(t * 8) + i) % 2 else 0
                    blit(img, chibi(k, kit=kit), 20 + i * 56, 104 + bob, 2)
                if t < self.SPOIL:
                    dialog(d, ["올해는 진짜 우승이다!!"], t - self.SQUAD, GOLD, "팬들")
                else:
                    dialog(d, ["(스포: 아니었다)"], t - self.SPOIL, RED, "해설")
            return
        d.rectangle([0, 0, W, H], fill=(24, 16, 40))
        text(d, 10, 4, "★ 2026 여름 이적시장 ★", GOLD)
        n = sum(1 for i in range(len(self.ITEMS)) if t >= self.BUY0 + i * self.GAP)
        frac = max(0.04, 1 - n / len(self.ITEMS) * 0.96)
        text(d, 330, 4, "자금", WHITE)
        d.rectangle([368, 7, 470, 19], fill=BLACK, outline=WHITE)
        d.rectangle([370, 9, 370 + int(98 * frac), 17], fill=GREEN if frac > 0.3 else RED)
        box(d, 6, 26, 150, 198)
        if n:
            k, num, nm, price, note = self.ITEMS[n - 1]
            if k:
                blit(img, portrait(k), 44, 34, 2)
            else:
                d.rectangle([48, 38, 108, 102], fill=(30, 30, 60))
                ctext(d, 50, "?", WHITE, F32, cx=78)
            ctext(d, 110, nm, WHITE, cx=78)
            ctext(d, 132, price, GOLD, cx=78)
            ctext(d, 160, note.split(" · ")[0], LGRAY, cx=78)
            if " · " in note:
                ctext(d, 178, note.split(" · ")[1], RED, cx=78)
        box(d, 156, 26, 474, 198)
        for i, (k, num, nm, price, _) in enumerate(self.ITEMS):
            yy = 31 + i * 18
            sold = t >= self.BUY0 + i * self.GAP
            text(d, 176, yy, f"#{num}", GRAY if sold else WHITE)
            text(d, 212, yy, nm, GRAY if sold else WHITE)
            text(d, 466 - tw(price), yy, price, GRAY if sold else GOLD)
            if sold:
                text(d, 340, yy, "구매!", RED)
        dl = [(0.1, ["상인: 어서 오시오! 뭘 사겠소?"], WHITE),
              (0.6, ["상인: 강등팀 선수를 £85M에?!", "      구단 역대 최고액이오!"], GOLD),
              (2.3, ["상인: 더! 더 사시오!", "      (그 사이 주장 로메로는 아틀레티코로)"], WHITE)]
        cur = ([x for x in dl if t >= x[0]] or [dl[0]])[-1]
        box(d, 6, 204, 474, 266)
        say(d, 18, 214, cur[1], t - cur[0], cur[2])

    def audio(self, m, t0):
        play(m, t0, self.KITS, SHOP, 160)
        for i in range(len(self.ITEMS)):
            m.sfx(t0 + self.BUY0 + i * self.GAP, "cash")
        m.sfx(t0 + self.KITS, "itemget")
        m.sfx(t0 + self.SQUAD, "fanfare")
        m.sfx(t0 + self.SPOIL, "sad")


# ------------------------------------------------------------------ 5. 포켓몬 배틀 (16.6s)

class Battle(Scene):
    fade_in = 0.0
    B0 = 0.8
    FOES = [
        dict(kind="bee", name="브렌트포드", player="fernandes", kit="away", len=2.8,
             msgs=[(0.1, ["야생의 브렌트포드가 나타났다!"], BLACK), (0.9, ["£85M 페르난데스 출격!", "...효과가 없다!"], BLACK)],
             result=(1.9, "패", 0, "브렌트포드 3 : 0 토트넘"), dmg=[1.9]),
        dict(kind="magpie", name="뉴캐슬", player="tonali", kit="home", len=2.8,
             msgs=[(0.1, ["뉴캐슬이 나타났다! (토날리 친정팀)"], BLACK), (0.9, ["까치가 공을 훔쳐 갔다!"], RED)],
             result=(1.9, "패", 0, "토트넘 0 : 2 뉴캐슬"), dmg=[1.9]),
        dict(kind="tree", name="노팅엄 포레스트", player="gallagher", kit="away", len=2.6,
             msgs=[(0.1, ["노팅엄 포레스트가 나타났다!"], BLACK), (0.9, ["슈팅이 나무에 맞았다... 0-0", "시즌 첫 승점!"], BLACK)],
             result=(1.7, "무", 1, "포레스트 0 : 0 토트넘"), heal=1.7),
        dict(kind="toffee", name="에버튼", player="vanhecke", kit="home", len=2.5,
             msgs=[(0.1, ["에버튼이 나타났다!"], BLACK), (0.8, ["양 팀 모두 잠들었다... 0-0", "쿨쿨..."], BLACK)],
             result=(1.6, "무", 1, "토트넘 0 : 0 에버튼"), heal=1.6),
        dict(kind="lion", name="아스톤 빌라", player="robertson", kit="home", len=4.0,
             msgs=[(0.1, ["아스톤 빌라가 나타났다!"], BLACK), (0.7, ["로버트슨 걷어내기 실수!", "0-3까지 끌려갔다!"], RED),
                   (1.7, ["돌아와, 로버트슨! 가라, 갤러거!"], BLACK),
                   (2.4, ["갤러거·반 헤케 연속골! 2-3!", "...너무 늦었다. 패배!"], BLACK)],
             result=(3.2, "패", 0, "토트넘 2 : 3 아스톤 빌라"), dmg=[0.8, 3.2], hits=[2.5, 2.8],
             swap=(1.9, "gallagher")),
    ]
    MOODS = ["smile", "neutral", "sweat", "sweat", "sweat", "shock"]
    OUTRO = 2.2

    def __init__(self):
        self.starts = []
        acc = self.B0
        for f in self.FOES:
            self.starts.append(acc)
            acc += f["len"]
        self.end = acc
        self.dur = acc + self.OUTRO

    def draw(self, img, d, t):
        if t < self.B0:
            d.rectangle([0, 0, W, H], fill=WHITE if int(t * 14) % 2 else BLACK)
            ctext(d, 110, "3스테이지: 이번 시즌 (26-27)", GOLD if int(t * 14) % 2 == 0 else NAVY, F16)
            return None
        d.rectangle([0, 0, W, H], fill=CREAM)
        d.ellipse([296, 128, 464, 158], fill=(176, 208, 144), outline=(120, 150, 90))
        d.ellipse([100, 188, 218, 208], fill=(176, 208, 144), outline=(120, 150, 90))
        res = [f["result"] for f, s in zip(self.FOES, self.starts) if t >= s + f["result"][0]]
        pts = sum(r[2] for r in res)
        shake, msg, board = None, None, None
        idx = max([i for i, s in enumerate(self.starts) if t >= s], default=0)
        f, lt = self.FOES[idx], t - self.starts[idx]
        player = f["player"]
        if t < self.end:
            flash = any(0 <= lt - h < 0.2 and int(lt * 16) % 2 for h in f.get("hits", []))
            hp = 1.0 - 0.2 * sum(1 for h in f.get("hits", []) if lt >= h)
            ex = 300 + max(0, int((0.25 - lt) / 0.25 * 200))
            spr = monster(f["kind"], t, flash)
            img.paste(spr, (ex, -6 + (2 if int(t * 4) % 2 else 0)), spr)
            box(d, 8, 8, 236, 58, fill=WHITE, border=NAVY)
            text(d, 20, 14, f["name"], BLACK, shadow=None)
            text(d, 20, 34, "체력", GOLD, shadow=None)
            d.rectangle([56, 38, 226, 46], fill=BLACK)
            d.rectangle([58, 40, 58 + int(166 * hp), 44], fill=GREEN)
            for mt, ls, col in f["msgs"]:
                if lt >= mt:
                    msg = (ls, lt - mt, col)
            for dt in f.get("dmg", []):
                if 0 <= lt - dt < 0.3:
                    shake = (random.Random(int(t * 60)).randint(-5, 5), 0)
            if "heal" in f and 0 <= lt - f["heal"] < 0.7:
                rng = random.Random(int(t * 20))
                for _ in range(10):
                    d.text((rng.randint(110, 200), rng.randint(110, 196)), "✦", font=F16, fill=GOLD)
            if "swap" in f and lt >= f["swap"][0]:
                player = f["swap"][1]
            if 0 <= lt - f["result"][0] < 1.2:
                board = f["result"][3]
        else:
            lt2 = t - self.end
            msg = ((["토트넘은 눈앞이 캄캄해졌다..."], lt2, BLACK) if lt2 < 0.9 else
                   (["5경기 승점 2 · 2득점 8실점", "리그 20위 (꼴찌)"], lt2 - 0.9, RED))
        hurt = t < self.end and any(0 <= lt - dt < 0.4 for dt in f.get("dmg", []))
        if not (hurt and int(t * 16) % 2):
            blit(img, chibi(player, kit=f["kit"]), 130, 100, 3)
        if t < self.end and "swap" in f and 0 <= lt - f["swap"][0] < 0.25:
            rng = random.Random(int(t * 30))
            for _ in range(12):
                cx, cy, r = rng.randint(120, 190), rng.randint(100, 200), rng.randint(6, 14)
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=LGRAY)
        box(d, 8, 66, 100, 172, fill=WHITE, border=NAVY)
        ctext(d, 72, "데 제르비", BLACK, shadow=None, cx=54)
        blit(img, portrait("dezerbi", self.MOODS[min(len(res), 5)]), 20, 94, 2)
        box(d, 244, 140, 474, 205, fill=WHITE, border=NAVY)
        text(d, 254, 144, f"{PEOPLE[player]['short']} #{PEOPLE[player]['num']}", BLACK, shadow=None)
        text(d, 434, 144, "홈" if f["kit"] == "home" else "원정", NAVY if f["kit"] == "home" else PURPLE, shadow=None)
        text(d, 254, 164, "승점", BLACK, shadow=None)
        d.rectangle([292, 169, 420, 177], fill=BLACK)
        if pts:
            d.rectangle([294, 171, 294 + int(124 * pts / 15), 175], fill=RED)
        text(d, 428, 164, f"{pts}/15", BLACK, shadow=None)
        text(d, 254, 184, "전적", BLACK, shadow=None)
        for i, r in enumerate(res):
            x = 294 + i * 22
            d.rectangle([x, 184, x + 18, 200], fill=RED if r[1] == "패" else GRAY)
            text(d, x + 1, 184, r[1], WHITE, shadow=None)
        box(d, 6, 208, 474, 266, fill=WHITE, border=NAVY)
        if msg:
            say(d, 18, 216, msg[0], msg[1], msg[2], shadow=None)
        if board:
            d.rectangle([110, 66, 370, 100], fill=NAVY, outline=WHITE, width=2)
            text(d, 118, 75, "종료", GOLD)
            ctext(d, 75, board, WHITE, cx=258)
        if t > self.end + 0.4:
            k = min(1.0, (t - self.end - 0.4) / 1.4)
            a = np.asarray(img).astype(np.float32)
            a[:206] *= 1 - k
            img.paste(Image.fromarray(a.astype(np.uint8)))
        return {"shake": shake}

    def audio(self, m, t0):
        m.sfx(t0, "encounter")
        play(m, t0 + self.B0, self.end - self.B0, BATTLE, 190, drums="k h s h k k s h")
        sfx = {"bee": "buzz", "magpie": "caw", "tree": "bump", "toffee": "snore", "lion": "roar"}
        for f, s in zip(self.FOES, self.starts):
            m.sfx(t0 + s + 0.05, sfx[f["kind"]])
            for mt, ls, _ in f["msgs"]:
                blips(m, t0 + s + mt, " ".join(ls))
            for dt in f.get("dmg", []):
                m.sfx(t0 + s + dt, "damage")
            for h in f.get("hits", []):
                m.sfx(t0 + s + h, "hit")
            if "heal" in f:
                m.sfx(t0 + s + f["heal"], "heal")
            if "swap" in f:
                m.sfx(t0 + s + f["swap"][0], "poof")
        m.sfx(t0 + self.end + 0.05, "blackout")


# ------------------------------------------------------------------ 6. 카라바오컵 (2.4s)

class Carabao(Scene):
    dur = 2.4

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(20, 30, 70))
        ctext(d, 24, "한편, 카라바오컵...", GOLD)
        if t < 1.2:
            for i in range(6):
                kk = (t * 1.5 + i / 6) % 1
                x, y = 60 + i * 72, 100 - kk * 30
                for a in range(8):
                    ang = a / 8 * math.tau
                    d.point((x + math.cos(ang) * (6 + 24 * kk), y + math.sin(ang) * (6 + 24 * kk)),
                            fill=[GOLD, RED, WHITE][i % 3])
            ctext(d, 120, "찰튼전 5-1 승리!!", WHITE, F32, shadow=NAVY2)
            ctext(d, 170, "(올 시즌 유일한 승리)", LGRAY)
        else:
            ctext(d, 120, "리버풀 원정 1-3 탈락", (255, 110, 100), F32, shadow=DRED)
            blit(img, chibi("dezerbi", mood="sad"), 222, 176, 2)

    def audio(self, m, t0):
        m.sfx(t0 + 0.05, "fanfare")
        m.sfx(t0 + 1.2, "sad")


# ------------------------------------------------------------------ 7. 팬 시위 (3.4s)

class Protest(Scene):
    dur = 3.4
    B1 = "약속은 '변화', 결과는 '실패' ★ "
    B2 = "토트넘은 사랑, ENIC은 싫다 ★ "

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(8, 8, 40))
        ctext(d, 6, "팬들: \"레비는 떠났는데, 바뀐 게 없다\"", WHITE)
        ctext(d, 26, "(레비 前 회장은 2025년 9월 퇴장, 구단주 ENIC은 그대로)", LGRAY)
        d.rectangle([0, 56, W, 200], fill=(30, 30, 50))
        rng = random.Random(9)
        for row, y in enumerate(range(58, 198, 9)):
            for col, x in enumerate(range(2 + (row % 2) * 4, W, 8)):
                up = math.sin(t * 12 + col * 0.8 + row) > 0.3
                bob = -2 if up else 0
                c = rng.choice([SKIN, SKIN_D, (140, 90, 60), (90, 60, 40)])
                d.ellipse([x, y + bob, x + 5, y + 5 + bob], fill=c)
                if up and (col + row) % 7 == 0:
                    d.line([(x - 1, y + bob - 1), (x - 3, y + bob - 7)], fill=(120, 80, 40), width=2)
                    d.rectangle([x - 5, y + bob - 11, x - 2, y + bob - 8], fill=ORANGE)
        for y, s, sp in ((78, self.B1, 90), (140, self.B2, -80)):
            d.rectangle([0, y, W, y + 20], fill=WHITE, outline=NAVY)
            wfull = tw(s)
            off = (t * sp) % wfull
            text(d, -int(off) if sp > 0 else int(off) - wfull, y + 2, s * 6, NAVY, shadow=None)
        if blink(t, 3):
            pow_box(d, "ENIC 나가라!", 240, 116, YELLOW, RED, F16)
        box(d, 6, 206, 474, 266)
        text(d, 18, 214, "분노 게이지", WHITE)
        k = min(1.0, t / 1.6)
        d.rectangle([110, 217, 380, 229], fill=BLACK, outline=WHITE)
        d.rectangle([112, 219, 112 + int(266 * k), 227], fill=RED if k > 0.7 else ORANGE)
        if k >= 1.0 and blink(t, 4):
            text(d, 392, 214, "최대!!", RED)
        if t > 1.7:
            text(d, 18, 238, reveal("구단주 ENIC을 향한 분노 폭발", t - 1.7), GOLD)

    def audio(self, m, t0):
        play(m, t0, self.dur, ANGRY, 170, drums="k k s k", duty=0.5)
        for k in range(3):
            m.sfx(t0 + 0.2 + k * 1.1, "boo")


# ------------------------------------------------------------------ 8. 그 사이 (3.0s)

class Meanwhile(Scene):
    dur = 3.0

    def draw(self, img, d, t):
        d.rectangle([0, 0, 239, H], fill=(220, 40, 60))
        d.rectangle([240, 0, W, H], fill=(255, 190, 120))
        d.ellipse([330, 30, 410, 110], fill=(255, 230, 150))
        d.rectangle([240, 170, W, H], fill=(245, 214, 150))
        d.line([(240, 0), (240, H)], fill=BLACK, width=4)
        ctext(d, 6, "한편, 뮌헨의 케인", WHITE, cx=120)
        ctext(d, 6, "한편, LA의 쏘니", NAVY, shadow=WHITE, cx=360)
        blit(img, chibi("kane"), 93, 130, 3)
        wob = int(math.sin(t * 6) * 3)
        for i in range(3):
            trophy(d, 120 + wob * (i + 1), 102 - i * 26)
        ctext(d, 26, "드디어 트로피 수집 중", GOLD, cx=120)
        d.polygon([(290, 190), (430, 190), (410, 170), (310, 170)], fill=(80, 180, 200), outline=BLACK)
        blit(img, chibi("son", mood="smile"), 333, 90, 3)
        d.rectangle([346, 116, 382, 122], fill=BLACK)
        ctext(d, 26, "행복하게 잘 지내는 중", NAVY, shadow=WHITE, cx=360)
        if t > 1.5:
            y0 = int(270 - 90 * min(1.0, (t - 1.5) / 0.25))
            d.rectangle([110, y0, 370, y0 + 100], fill=(40, 40, 60), outline=WHITE, width=2)
            blit(img, COCK_CRY, 130, y0 + 20, 2)
            text(d, 180, y0 + 16, "토트넘 팬들:", GOLD)
            text(d, 180, y0 + 38, "우리 애들 잘 지내네...", WHITE)
            text(d, 180, y0 + 58, "ㅠㅠ", (110, 190, 255))

    def audio(self, m, t0):
        play(m, t0, 1.5, HAPPY, 150, drums="k . s .", duty=0.125, spb=4)
        m.sfx(t0 + 1.5, "sad")


# ------------------------------------------------------------------ 9. 컨티뉴 (4.2s)

class Continue(Scene):
    dur = 4.2
    COIN = 1.5

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        if t < 1.9:
            ctext(d, 12, "계속하시겠습니까?", RED, F32, shadow=DRED)
            ctext(d, 56, str(max(5, 9 - int(t / 0.3))), WHITE, F64, shadow=GRAY)
            if blink(t, 3):
                ctext(d, 236, "동전을 넣으세요", GOLD)
        d.rectangle([392, 130, 432, 180], fill=(40, 40, 40), outline=LGRAY)
        d.rectangle([408, 136, 414, 172], fill=BLACK)
        if self.COIN <= t < self.COIN + 0.35:
            k = (t - self.COIN) / 0.35
            cy = -16 + 150 * k * k
            d.ellipse([401, cy, 421, cy + 20], fill=GOLD, outline=BLACK)
            text(d, 407, cy + 2, "£", BROWN, shadow=None)
            text(d, 428, cy, "ENIC", LGRAY)
        k = t - 2.0
        if k >= 0:
            jy = -int(50 * 4 * (k / 0.4) * (1 - k / 0.4)) if k < 0.4 else 0
            blit(img, chibi("dezerbi"), 222, 150 + jy, 2)
        else:
            blit(img, chibi("dezerbi", mood="x"), 222, 150, 2, flip_v=True)
        if t >= 2.2:
            ctext(d, 18, "다음 스테이지 ▶ 맨유 원정", WHITE, F32, shadow=NAVY2)
            ctext(d, 60, "10월 10일 · 올드 트래포드", LGRAY)
        if t >= 2.9:
            text(d, 110, 92, "데 제르비의 목숨", RED)
            for i in range(3):
                col = RED if i == 0 else (70, 60, 70)
                x = 250 + i * 26
                d.polygon([(x, 94), (x + 10, 106), (x + 20, 94), (x + 15, 89), (x + 10, 94), (x + 5, 89)], fill=col)

    def audio(self, m, t0):
        for k in range(5):
            m.sfx(t0 + k * 0.3, "tick")
        m.sfx(t0 + self.COIN, "coin")
        m.sfx(t0 + 2.0, "jump")
        m.notes(t0 + 2.2, "G5:0.08 C6:0.08 E6:0.08 G6:0.25", vol=0.08, duty=0.25)
        m.sfx(t0 + 2.9, "gulp")


# ------------------------------------------------------------------ 10. 엔딩 (3.4s)

class Ending(Scene):
    dur = 3.6
    fade_out = 0.6
    WALKERS = [("dezerbi", None), ("vdv", "home"), ("fernandes", "away"), ("tonali", "home"), ("gallagher", "away")]

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        draw_stars(d, t, 6, n=40, seed=3)
        ctext(d, 10, "시청해 주셔서 감사합니다!", WHITE)
        ctext(d, 34, reveal("하지만 트로피는", t - 0.2), WHITE)
        if t > 0.6:
            ctext(d, 56, reveal("다른 성에 있습니다!", t - 0.6), GOLD, F32, shadow=DRED)
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
            blit(img, chibi(k, int(t * 6 + i) % 2, kit=kit), 10 + t * 26 + i * 46, 110, 2)
        if t > 1.4:
            ctext(d, 190, "가자, 토트넘!", GOLD, F32, shadow=NAVY2)
        ctext(d, 246, "※ 2026.09.24 기준 실제 결과 바탕의 풍자 패러디", GRAY)

    def audio(self, m, t0):
        play(m, t0, 3.0, TITLE, 190)
        for n in ("C4", "E4", "G4", "C5"):
            m.notes(t0 + 3.0, f"{n}:0.6", vol=0.05)


# -------------------------------------------------------------------------- main

def build():
    return [Title(), ColdOpen(), Platformer(), Shop(), Battle(), Carabao(), Protest(), Meanwhile(), Continue(),
            Ending()]


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
    wav_path = os.path.join(HERE, "_audio_short.wav")
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
    proc.stdin.close()
    proc.wait()
    os.remove(wav_path)
    print("wrote", OUT, f"({total:.1f}s)")


if __name__ == "__main__":
    main()
