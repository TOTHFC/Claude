#!/usr/bin/env python3
"""토트넘 대모험 ~강등권의 전설~ (최종판: 첫 영상 전개 + 26/27 고증)

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

from make_short import ANGRY, BATTLE, HAPPY, SAD, SHOP as SHOP_SONG, STAGE, TITLE, play
from engine import (BLACK, BROWN, CREAM, DGREEN, DRED, F16, F32, F64, FPS, GOLD, GRAY, GREEN, H, LGRAY, NAVY,
                    NAVY2, ORANGE, RED, SCALE, SKIN, SKIN_D, SKY, SR, W, WHITE, YELLOW, Mixer, blink, blit, box,
                    ctext, draw_flames, draw_stars, drum, make_stamp, noise, reveal, text, tw)
from sprites import (COCK, COCK_CRY, COCK_RUN, NEON, OBSIDIAN, PEOPLE, chibi, draw_hammer, kit_icon, monster,
                     portrait)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tottenham_final.mp4")
STAMP_SACKED = make_stamp("경질!")
SELECT_SONG = ("A4 C5 E5 C5 A4 C5 E5 C5 G4 B4 D5 B4 G4 B4 D5 B4 F4 A4 C5 A4 F4 A4 C5 A4 E4 G#4 B4 G#4 E4 G#4 B4 E5",
               "A2 - - - - - - - G2 - - - - - - - F2 - - - - - - - E2 - - - - - - -")
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
        ctext(d, y, "스퍼스보이", NAVY, F32, shadow=None)
        text(d, W // 2 + tw("스퍼스보이", F32) // 2 + 2, y - 4, "™", NAVY, shadow=None)
        if t > 2.3:
            ctext(d, 160, "구단주 ENIC 공식 라이선스", (60, 80, 60), shadow=None)

    def audio(self, m, t0):
        m.sfx(t0 + 2.05, "ding")


# ------------------------------------------------------------------ 1. 타이틀

class Title(Scene):
    dur = 10.0
    LINE = [("fernandes", "home"), ("tonali", "away"), ("vdv", "home"), ("gallagher", "away"),
            ("vanhecke", "home"), ("mudryk", "away")]
    XS = [22, 82, 142, 290, 350, 410]
    # (시각, 커서 위치)
    CURSOR = [(0.0, 0), (3.0, 1), (5.6, 0), (6.1, 1), (8.0, 0)]
    POP1 = (3.4, 5.6)
    POP2 = (6.4, 7.8)
    START = 8.5

    def cur(self, t):
        return [c for tt, c in self.CURSOR if t >= tt][-1]

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=NAVY)
        draw_stars(d, t, 25)
        ctext(d, 2, "토트넘 대모험", WHITE, F64, shadow=GOLD)
        ctext(d, 72, "~ 강등권의 전설 ~", GOLD)
        d.rectangle([0, 166, W, 180], fill=(24, 120, 48))
        for x in range(0, W, 32):
            d.rectangle([x, 166, x + 15, 180], fill=(32, 140, 60))
        for i, (k, kit) in enumerate(self.LINE):
            bob = -2 if (int(t * 4) + i) % 2 else 0
            blit(img, chibi(k, kit=kit), self.XS[i], 100 + bob, 2)
        hop = -4 if int(t * 3) % 2 else 0
        d.ellipse([214, 150, 266, 172], fill=WHITE, outline=BLACK)
        d.polygon([(234, 154), (246, 154), (249, 161), (240, 167), (231, 161)], fill=BLACK)
        blit(img, COCK, 212, 96 + hop, 3)
        cur = self.cur(t)
        flash = t >= self.START and blink(t, 6)
        for i, s in enumerate(["새 게임", "트로피 룸"]):
            if i == 0 and t >= self.START and not flash:
                continue
            text(d, 196, 188 + i * 20, s, WHITE)
        text(d, 178, 188 + cur * 20, "▶", GOLD)
        if t < 3.0 and blink(t, 1.5):
            ctext(d, 240, "시작 버튼을 누르세요", LGRAY)
        if self.POP1[0] <= t < self.POP1[1]:
            k = t - self.POP1[0]
            box(d, 90, 84, 390, 172)
            ctext(d, 92, "- 트로피 룸 -", GOLD)
            trophy(d, 122, 114)
            text(d, 146, 118, "2025 유로파리그 우승 ×1", WHITE)
            ctext(d, 146, reveal("...끝. 이게 전부다.", k - 0.8, 14), LGRAY)
            if k > 0.4:
                x = 380 - (k - 0.4) * 160
                d.ellipse([x, 150, x + 10, 160], outline=(170, 130, 80))
                d.line([(x + 2, 152), (x + 8, 158)], fill=(170, 130, 80))
        if self.POP2[0] <= t < self.POP2[1]:
            box(d, 120, 100, 360, 150)
            ctext(d, 116, reveal("...아까 봤잖아요.", t - self.POP2[0], 14), WHITE)

    def audio(self, m, t0):
        play(m, t0 + 0.2, 3.0, TITLE, 150)
        m.sfx(t0 + 3.0, "move")
        m.sfx(t0 + 3.4, "select")
        m.seq(t0 + 3.5, 2.0, "A4 - - - G4 - - - F4 - - - E4 - - -", 120, 2, "tri", 0.18)
        m.blips(t0 + 4.2, "...끝. 이게 전부다.", 14)
        m.sfx(t0 + 5.6, "move")
        m.sfx(t0 + 6.1, "move")
        m.sfx(t0 + 6.4, "select")
        m.blips(t0 + 6.4, "...아까 봤잖아요.", 14)
        m.sfx(t0 + 6.9, "sad")
        m.sfx(t0 + 8.0, "move")
        play(m, t0 + 8.0, 0.5, TITLE, 150, drums=None)
        m.sfx(t0 + self.START, "start")


# ------------------------------------------------------------------ 2. 콜드 오픈 (현재 20위)

# ------------------------------------------------------------------ 4. 감독 선택

class ManagerSelect(Scene):
    dur = 10.0
    KEYS = ["frank", "tudor", "dezerbi"]
    XS = [40, 189, 338]
    SEL = [0.8, 3.4, 6.0]
    STAMP = [2.5, 5.1]
    INFO = [
        ("토마스 프랭크: 8경기 연속 무승", "→ 부임 8개월 만에 경질!"),
        ("이고르 투도르: 부임 44일, 7경기", "→ 포레스트전 0-3 패배 후 경질!"),
        ("로베르토 데 제르비: 최종전 잔류 성공!", "→ ...그런데 올 시즌 5경기째 무승 (20위)"),
    ]

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(16, 16, 48))
        off = int(t * 8) % 16
        for x in range(-16, W, 16):
            d.line([(x + off, 0), (x + off, H)], fill=(28, 28, 72))
        for y in range(-16, H, 16):
            d.line([(0, y + off), (W, y + off)], fill=(28, 28, 72))
        ctext(d, 4, "감독을 선택하세요", GOLD)
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
                    ctext(d, 124, "가시방석!", RED, cx=x + 51)
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
        play(m, t0 + 0.2, 7.6, SELECT_SONG, 132, drums="k . h . s . h . k k h . s . h h", spb=4, vol=0.06)
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
    SYMS = ["패", "패", "패", "무"]
    WINLESS = [4, 8, 12, 15]
    BANNERS = ["2026년, 리그 승리 실종", "8경기 연속 무승...", "구단 최초 6연패", "리그 15경기 연속 무승"]
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
            ctext(d, 60, "월드 25-26", WHITE)
            ctext(d, 84, "지난 시즌", LGRAY)
            for i, k in enumerate(["frank", "tudor", "dezerbi"]):
                blit(img, chibi(k), 150 + i * 44, 112, 2)
            text(d, 288, 146, "× 3 (감독)", WHITE)
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
            ctext(d, 230, "2부 리그", RED, cx=px0 + 56, shadow=None)
            ctext(d, 248, "(챔피언십)", DRED, cx=px0 + 56, shadow=None)
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
                    col = RED if self.SYMS[i] == "패" else GRAY
                    d.rectangle([bx, iy, bx + 17, iy + 17], fill=col, outline=WHITE)
                    text(d, bx + 1, iy, self.SYMS[i], WHITE, shadow=None)
        rx, ry, air = self.HX, self.GROUND - 38, False     # 수탉 (주인공)
        mx, my, show = self.HX - 44, self.HERO_Y, True       # 뒤따르는 감독
        mgr = self.manager(t)
        hook = None
        for (ht, who), (dr, _) in zip(self.HOOKS, self.DROPS):
            k = t - ht
            if 0 <= k < 0.9:
                mgr = who
                if k < 0.35:
                    hook = -40 + (mx + 76) * (k / 0.35)
                else:
                    kk = k - 0.35
                    dx = -900 * kk * kk - 250 * kk
                    hook = mx + 36 + dx
                    mx += dx
            elif ht + 0.9 <= t < dr:
                show = False
        for dr, who in self.DROPS:
            k = t - dr
            if 0 <= k < 0.4:
                my = -70 + (self.HERO_Y + 70) * (k / 0.4) ** 2
        if t < self.CAM_STOP:
            for ht in self.HITS:
                k = t - (ht - 0.3)
                if 0 <= k < 0.6:
                    ry -= 70 * 4 * (k / 0.6) * (1 - k / 0.6)
                    air = True
        elif t < self.JUMP:
            rx = self.HX + (t - self.WALK) / (self.JUMP - self.WALK) * (200 - self.HX)
            mx = rx - 44
        elif t < self.LAND:
            k = (t - self.JUMP) / (self.LAND - self.JUMP)
            rx = 200 + (self.ps + 142 - 200) * k
            ry -= 70 * 4 * k * (1 - k)
            mx = 156 + (self.ps + 98 - 156) * k
            my -= 60 * 4 * k * (1 - k)
            air = True
        else:
            rx, mx = self.ps + 142, self.ps + 98
            if t < self.LAND + 1.4:
                mx += 1 if int(t * 16) % 2 else -1
                text(d, mx + 14, my - 20, "!", RED)
        moving = t < self.CAM_STOP and not any(a <= t < b for a, b in self.PAUSES)
        moving = moving or self.WALK <= t < self.JUMP
        frame = 1 if air or (moving and int(t * 8) % 2) else 0
        hooked = hook is not None
        if show:
            blit(img, chibi(mgr, frame, mood="shock" if hooked or (self.LAND <= t < self.LAND + 1.4) else "smile"),
                 mx, my, 2)
        blit(img, COCK_RUN if (air or (moving and int(t * 8) % 2)) else COCK, rx, ry, 2)
        if hooked:
            y = self.HERO_Y + 24
            d.line([(-10, y), (hook, y)], fill=(150, 90, 40), width=5)
            d.arc([hook - 16, y, hook + 16, y + 32], 270, 90, fill=(150, 90, 40), width=5)
            d.line([(hook, y + 30), (hook - 8, y + 30)], fill=(150, 90, 40), width=5)
        for ht, who in self.HOOKS:
            if 0.3 <= t - ht < 0.9:
                box(d, 150, 54, 330, 128)
                blit(img, portrait(who, "shock"), 160, 60, 2)
                text(d, 236, 70, "경질!", RED, F32)
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
        text(d, 10, 4, "토트넘", WHITE)
        text(d, 150, 4, f"무승 {wl:02d}", WHITE)
        text(d, 270, 4, f"감독: {PEOPLE[mgr]['short']}", WHITE)
        banner = None
        for i, ht in enumerate(self.HITS):
            if 0 <= t - ht < 1.0:
                banner = (self.BANNERS[i], RED)
        for ht, who in self.HOOKS:
            if 0 <= t - ht < 0.9:
                banner = (f"{PEOPLE[who]['name']} 경질!", RED)
        for dr, who in self.DROPS:
            if 0 <= t - dr < 1.2:
                extra = " (시즌 3번째!)" if who == "dezerbi" else " (임시)"
                banner = (f"{PEOPLE[who]['name']} 부임{extra}", WHITE)
        if self.WALK <= t < self.LAND:
            banner = ("최종전 vs 에버튼 ─ 지면 강등!", WHITE)
        elif self.LAND <= t < self.LAND + 1.3:
            banner = ("팔리냐 결승골 1-0!! 잔류다!! (감독은 아슬아슬)", GOLD)
        elif 13.5 <= t < 14.3:
            banner = ("대신 웨스트햄이 강등...", LGRAY)
        if banner:
            s, col = banner
            w = tw(s)
            d.rectangle([W // 2 - w // 2 - 6, 26, W // 2 + w // 2 + 6, 46], fill=BLACK)
            ctext(d, 28, s, col)
        if t >= 14.3:
            box(d, 90, 64, 390, 172)
            ctext(d, 72, "생존!", GOLD, F32)
            ctext(d, 112, "17위 · 승점 41 (2시즌 연속 17위)", WHITE)
            ctext(d, 138, "세계 9위 부자 구단의 성적표", LGRAY)

    def draw_arsenal(self, img, d, k):
        d.rectangle([0, 0, W, H], fill=(20, 20, 30))
        d.rectangle([90, 30, 390, 190], fill=(40, 40, 50), outline=LGRAY, width=3)
        d.rectangle([100, 40, 380, 180], fill=(200, 30, 40))
        pixel_confetti(d, k, 9, 40)
        trophy(d, 240, 70 + int(math.sin(k * 8) * 3))
        ctext(d, 120, "속보: 아스날", WHITE)
        ctext(d, 140, "2025-26 리그 우승", GOLD)
        blit(img, COCK_CRY if k > 1.2 else COCK, 216, 196, 2)
        if k > 1.2:
            for sgn in (-1, 1):
                for i in range(4):
                    kk = (k * 2 + i / 4) % 1
                    d.rectangle([248 + sgn * (10 + 40 * kk), 205 - 20 * kk + 60 * kk * kk,
                                 250 + sgn * (10 + 40 * kk), 207 - 20 * kk + 60 * kk * kk], fill=(110, 190, 255))
        dialog(d, ["같은 날, 북런던 라이벌은 우승...", "토트넘 팬들: (조용히 TV를 껐다)"], k - 0.3, WHITE, name="한편")

    def audio(self, m, t0):
        for a, b in [(self.INTRO, 4.5), (5.8, 8.1), (9.4, self.CAM_STOP)]:
            play(m, t0 + a, b - a, STAGE, 160)
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
        play(m, t0 + 14.3, 2.2, TITLE, 190)
        m.sfx(t0 + 14.3, "fanfare")
        m.sfx(t0 + self.ARSENAL, "fanfare")
        m.sfx(t0 + self.ARSENAL + 1.2, "sad")
        blip_lines(m, t0 + self.ARSENAL + 0.3, ["같은 날, 북런던 라이벌은 우승...", "토트넘 팬들: (조용히 TV를 껐다)"])


# ------------------------------------------------------------------ 6. 이적시장

class Shop(Scene):
    ITEMS = [  # (키, 등번호, 이름, 가격, 구매 시각)
        ("fernandes", "18", "페르난데스", "£85M", 2.0),
        ("tonali", "16", "토날리", "£92.5M", 4.6),
        (None, "17", "사비뉴", "£75M", 6.8),
        ("vanhecke", "6", "반 헤케", "£52M", 7.6),
        ("robertson", "3", "로버트슨", "무료", 9.2),
        ("senesi", "5", "세네시", "무료", 9.9),
        ("mudryk", "27", "무드릭", "임대", 11.4),
        (None, "22", "마르무시", "임대", 12.1),
        ("adarabioyo", "4", "아다라비오요", "영입", 13.6),
    ]
    LINES = [
        (0.3, ["어서 오시오, 수탉 손님!", "뭘 사겠소?"], WHITE),
        (2.0, ["페르난데스 £85M!", "강등팀 출신인데 구단 신기록이오!"], GOLD),
        (4.6, ["토날리 £92.5M!", "뉴캐슬에서 모셔 왔소!"], GOLD),
        (6.8, ["사비뉴 £75M, 반 헤케 £52M도", "얹어 드리지!"], GOLD),
        (9.2, ["로버트슨·세네시는", "공짜요, 공짜!"], WHITE),
        (11.4, ["무드릭·마르무시는", "빌려 드리지!"], WHITE),
        (13.6, ["아다라비오요까지!", "오늘 장사 끝!"], WHITE),
        (15.4, ["아, 그 사이 주장 로메로는", "아틀레티코로 떠났소."], LGRAY),
        (18.0, ["이 정도면 우승이지!", "하하하!"], GOLD),
    ]
    KITS, SQUAD, SPOIL = 20.4, 23.4, 26.2
    dur = 28.4

    def draw(self, img, d, t):
        if t >= self.KITS:
            return self.draw_after(img, d, t)
        d.rectangle([0, 0, W, H], fill=(24, 16, 40))
        text(d, 10, 4, "★ 2026 여름 이적시장 ★", GOLD)
        n = sum(1 for it in self.ITEMS if t >= it[4])
        frac = max(0.04, 1 - n / len(self.ITEMS) * 0.96)
        text(d, 330, 4, "자금", WHITE)
        d.rectangle([368, 7, 470, 19], fill=BLACK, outline=WHITE)
        d.rectangle([370, 9, 370 + int(98 * frac), 17], fill=GREEN if frac > 0.3 else RED)
        # 왼쪽: 상인(항상) + 손님 수탉
        box(d, 6, 26, 150, 198)
        cur = ([x for x in self.LINES if t >= x[0]] or [self.LINES[0]])[-1]
        talking = t - cur[0] < len("".join(cur[1])) / 24 + 0.1 and int(t * 8) % 2
        x, y = 44, 34
        d.ellipse([x + 8, y, x + 60, y + 52], fill=SKIN, outline=BLACK)
        d.chord([x + 8, y - 4, x + 60, y + 32], 180, 360, fill=(90, 60, 30))
        d.rectangle([x + 22, y + 22, x + 25, y + 25], fill=BLACK)
        d.rectangle([x + 43, y + 22, x + 46, y + 25], fill=BLACK)
        d.polygon([(x + 18, y + 35), (x + 34, y + 30), (x + 50, y + 35), (x + 34, y + 39)], fill=(60, 40, 20))
        if talking:
            d.ellipse([x + 28, y + 40, x + 40, y + 48], fill=(120, 40, 40))
        d.rectangle([x + 10, y + 54, x + 58, y + 86], fill=(40, 120, 60), outline=BLACK)
        text(d, x + 26, y + 58, "£", GOLD, shadow=None)
        ctext(d, 124, "상인", LGRAY, cx=78)
        d.rectangle([10, 146, 146, 150], fill=(120, 72, 32))
        blit(img, COCK, 14, 152, 2)
        if n:
            k = self.ITEMS[n - 1][0]
            if k and t - self.ITEMS[n - 1][4] < 1.6:
                blit(img, portrait(k), 90, 150, 1)
        # 오른쪽: 목록
        box(d, 156, 26, 474, 198)
        for i, (k, num, nm, price, bt) in enumerate(self.ITEMS):
            yy = 31 + i * 18
            sold = t >= bt
            col = GRAY if sold else WHITE
            text(d, 176, yy, f"#{num}", col)
            text(d, 212, yy, nm, col)
            text(d, 466 - tw(price), yy, price, GRAY if sold else GOLD)
            if sold:
                text(d, 336, yy, "구매!", RED)
                if t - bt < 0.4:
                    d.rectangle([172, yy, 470, yy + 17], outline=YELLOW)
        if n < len(self.ITEMS):
            text(d, 160, 31 + n * 18, "▶", GOLD)
        box(d, 6, 204, 474, 266)
        d.rectangle([14, 192, 62, 210], fill=NAVY, outline=WHITE)
        text(d, 22, 193, "상인", GOLD)
        lines_at(d, 18, 216, cur[1], t - cur[0], cur[2])

    def draw_after(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(10, 10, 30))
        draw_stars(d, t, 10)
        d.rectangle([0, 170, W, 200], fill=(40, 40, 80))
        if t < self.SQUAD:
            k = t - self.KITS
            blit(img, COCK, 222, 132, 2)
            for x, kit in ((150, "home"), (294, "away")):
                blit(img, kit_icon(kit), x, 60, 2)
                for i in range(8):
                    a = i / 8 * math.tau + t * 2
                    cx = x + 20
                    d.line([(cx + math.cos(a) * 24, 80 + math.sin(a) * 24),
                            (cx + math.cos(a) * 36, 80 + math.sin(a) * 36)], fill=GOLD, width=2)
            dialog(d, ["26/27 홈·원정 유니폼을 손에 넣었다!", "(원정은 네이비 + 네온 번개 무늬)"], k - 0.3, GOLD,
                   name="아이템 획득!")
        else:
            k = t - self.SQUAD
            squad = [("fernandes", "home"), ("tonali", "away"), ("robertson", "home"), ("vdv", "home"),
                     ("vanhecke", "away"), ("senesi", "home"), ("mudryk", "away"), ("adarabioyo", "home")]
            for i, (kk, kit) in enumerate(squad):
                bob = -3 if (int(t * 5) + i) % 2 else 0
                blit(img, chibi(kk, kit=kit), 12 + i * 58, 104 + bob, 2)
            ctext(d, 30, "새 스쿼드 완성! 새 주장: 반 더 벤", GOLD)
            if t < self.SPOIL:
                dialog(d, ["이 정도면 올해는 우승이지!!"], k - 0.2, GOLD, name="토트넘 팬들")
            else:
                dialog(d, ["(스포: 아니었다)"], t - self.SPOIL, RED, name="해설")

    def audio(self, m, t0):
        play(m, t0 + 0.1, self.KITS - 0.1, SHOP_SONG, 120, drums="k . h . s . h .", duty=0.5, vol=0.06)
        for st, ls, _ in self.LINES:
            blip_lines(m, t0 + st, ls)
        for it in self.ITEMS:
            m.sfx(t0 + it[4], "cash")
        m.sfx(t0 + self.KITS, "itemget")
        m.sfx(t0 + self.SQUAD, "fanfare")
        play(m, t0 + self.SQUAD + 0.6, self.SPOIL - self.SQUAD - 0.6, TITLE, 170)
        m.sfx(t0 + self.SPOIL, "sad")


# ------------------------------------------------------------------ 7. 포켓몬 배틀 (2026-27)

class Battle(Scene):
    fade_in = 0.0
    B0 = 1.0
    FOES = [
        dict(kind="bee", name="브렌트포드", player="fernandes", kit="away", len=5.2,
             msgs=[(0.2, ["야생의 브렌트포드가 나타났다! (원정)"], BLACK),
                   (1.5, ["토트넘은 £85M 페르난데스를 내보냈다!"], BLACK),
                   (2.9, ["벌떼의 쏘기 공격!", "효과는 굉장했다... 0-3 패배!"], RED)],
             result=(3.3, "패", 0, "브렌트포드 3 : 0 토트넘"), dmg=[3.3]),
        dict(kind="magpie", name="뉴캐슬", player="tonali", kit="home", len=5.3,
             msgs=[(0.2, ["뉴캐슬이 나타났다!", "(토날리의 친정팀이다)"], BLACK),
                   (1.6, ["토날리: 친정팀아 안녕~!"], BLACK),
                   (2.9, ["뉴캐슬은 토날리 이적료로 배가 부르다!", "0-2 패배!"], RED)],
             result=(3.4, "패", 0, "토트넘 0 : 2 뉴캐슬"), dmg=[3.4]),
        dict(kind="tree", name="노팅엄 포레스트", player="gallagher", kit="away", len=5.3,
             msgs=[(0.2, ["노팅엄 포레스트가 나타났다! (원정)", "(지난 시즌 투도르를 잘랐던 그 나무)"], BLACK),
                   (1.8, ["갤러거의 슈팅! 나무에 맞았다.", "또 맞았다. 또..."], BLACK),
                   (3.1, ["0-0 무승부! 시즌 첫 승점!"], BLACK)],
             result=(3.4, "무", 1, "포레스트 0 : 0 토트넘"), heal=3.4),
        dict(kind="toffee", name="에버튼", player="vanhecke", kit="home", len=5.1,
             msgs=[(0.2, ["에버튼이 나타났다!"], BLACK),
                   (1.4, ["에버튼은 잠자기를 썼다!", "토트넘도 잠자기를 썼다!"], BLACK),
                   (2.9, ["0-0 무승부. 승점 +1 (쿨쿨...)"], BLACK)],
             result=(3.2, "무", 1, "토트넘 0 : 0 에버튼"), heal=3.2),
        dict(kind="lion", name="아스톤 빌라", player="robertson", kit="home", len=9.2,
             msgs=[(0.2, ["아스톤 빌라가 나타났다!"], BLACK),
                   (1.4, ["로버트슨의 어설픈 걷어내기!", "빌라가 선제골을 넣었다!"], BLACK),
                   (3.0, ["...0-3까지 끌려갔다."], RED),
                   (4.3, ["돌아와, 로버트슨! 가라, 갤러거!"], BLACK),
                   (5.5, ["86분 갤러거 첫 골! 추가시간 반 헤케 골!", "희망이 차오른다!!"], BLACK),
                   (7.3, ["...하지만 희망은 효과가 없었다.", "2-3 패배!"], RED)],
             result=(7.7, "패", 0, "토트넘 2 : 3 아스톤 빌라"), dmg=[1.9, 3.2, 7.7], hits=[5.8, 6.4],
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
            text(d, 20, 34, "체력", GOLD, shadow=None)
            d.rectangle([56, 38, 226, 46], fill=BLACK)
            d.rectangle([58, 40, 58 + int(166 * hp), 44], fill=GREEN)
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
                msg = (["토트넘은 눈앞이 캄캄해졌다..."], lt2 - 0.1, BLACK)
            else:
                msg = (["5경기 승점 2 · 2득점 8실점", "리그 20위 (꼴찌)"], lt2 - 1.6, RED)
        hurt = t < self.end and any(0 <= lt - dt < 0.6 for dt in f.get("dmg", []))
        blit(img, chibi(player, kit=f["kit"]), 106, 128, 2)
        if not (hurt and int(t * 16) % 2):
            blit(img, COCK, 150, 146, 3)
        if t < self.end and "swap" in f and 0 <= lt - f["swap"][0] < 0.35:
            rng = random.Random(int(t * 30))
            for _ in range(12):
                cx, cy, r = rng.randint(100, 146), rng.randint(128, 196), rng.randint(6, 12)
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=LGRAY)
        box(d, 8, 66, 100, 172, fill=WHITE, border=NAVY)
        ctext(d, 72, "데 제르비", BLACK, shadow=None, cx=54)
        blit(img, portrait("dezerbi", self.MOODS[min(len(res), 5)]), 20, 94, 2)
        box(d, 244, 140, 474, 205, fill=WHITE, border=NAVY)
        kitlab = "홈" if f["kit"] == "home" else "원정"
        text(d, 254, 144, f"수탉 + {PEOPLE[player]['short']}", BLACK, shadow=None)
        text(d, 434, 144, kitlab, PURPLE if kitlab == "원정" else NAVY, shadow=None)
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
            lines_at(d, 18, 216, msg[0], msg[1], msg[2], shadow=None)
        if board:
            d.rectangle([108, 66, 372, 100], fill=NAVY, outline=WHITE, width=2)
            text(d, 116, 75, "종료", GOLD)
            ctext(d, 75, board, WHITE, cx=262)
        if t > self.end + 0.8:
            k = min(1.0, (t - self.end - 0.8) / 2.6)
            a = np.asarray(img).astype(np.float32)
            a[:206] *= 1 - k
            img.paste(Image.fromarray(a.astype(np.uint8)))
        return {"shake": shake}

    def audio(self, m, t0):
        m.sfx(t0, "encounter")
        play(m, t0 + self.B0, self.end - self.B0, BATTLE, 172, drums="k h s h k k s h", vol=0.07)
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
        m.sfx(t0 + self.end + 0.1, "blackout")
        blip_lines(m, t0 + self.end + 0.1, ["토트넘은 눈앞이 캄캄해졌다..."])
        blip_lines(m, t0 + self.end + 1.6, ["5경기 승점 2 · 2득점 8실점", "리그 20위 (꼴찌)"])


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
            ctext(d, Y0 + row * C - 18, "토트넘", WHITE, cx=X0 + 5 * C)
        text(d, 312, Y0 + 17 * C + 8, "◀ 강등권", RED)
        for y, label, val, col in ((15, "점수", "2 (승점)", WHITE), (75, "지운 줄", "0 (승리 수)", WHITE),
                                   (135, "레벨", "20위 (꼴찌)", RED)):
            box(d, 12, y, 168, y + 52)
            text(d, 24, y + 6, label, GOLD)
            text(d, 24, y + 28, val, col)
        box(d, 312, 15, 468, 95)
        text(d, 324, 21, "다음 상대", GOLD)
        text(d, 324, 43, "맨유 (원정)", WHITE)
        text(d, 324, 65, "10월 10일", LGRAY)
        box(d, 312, 103, 468, 163)
        text(d, 324, 111, "득점 2", WHITE)
        text(d, 324, 135, "실점 8", RED)
        text(d, 24, 238, "스퍼스트리스", NAVY2)
        if t >= 5.0 and blink(t, 2):
            d.rectangle([0, 112, W, 158], fill=RED)
            ctext(d, 119, "경고!! 강등권 진입", WHITE, F32, shadow=DRED)

    def audio(self, m, t0):
        kor = ("E5 - B4 C5 D5 - C5 B4 A4 - A4 C5 E5 - D5 C5 B4 - - C5 D5 - E5 - C5 - A4 - A4 - - - "
               ". D5 - F5 A5 - G5 F5 E5 - - C5 E5 - D5 C5 B4 - B4 C5 D5 - E5 - C5 - A4 - A4 - - -")
        m.seq(t0 + 0.3, 4.1, kor, 150, 2, "sq", 0.08, 0.5)  # 코로베이니키 (러시아 민요, 퍼블릭 도메인)
        m.seq(t0 + 0.3, 4.1, "E2 E3 E2 E3 A2 A3 A2 A3 G#2 G#3 G#2 G#3 A2 A3 B2 C3", 150, 2, "tri", 0.18)
        for k in range(1, self.LAND + 1):
            m.sfx(t0 + self.DROP0 + k / self.RATE, "tick")
        m.sfx(t0 + self.DROP0 + self.LAND / self.RATE + 0.02, "lock")
        for k in range(7):
            m.sfx(t0 + 5.0 + k * 0.5, "siren")


# ------------------------------------------------------------------ 10. 팬 시위

class Protest(Scene):
    dur = 10.0
    B1 = "£300M 쓰고 20위?! ★ "
    B2 = "바뀐 건 유니폼뿐! ★ "

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(8, 8, 40))
        for lx in (30, 450):
            d.polygon([(lx, 12), (lx - 80, 110), (lx + 80, 110)], fill=(24, 24, 64))
            d.ellipse([lx - 8, 4, lx + 8, 20], fill=WHITE)
        ctext(d, 6, "빌라전 직후, 팬들의 분노", WHITE)
        ctext(d, 26, "\"선수는 잔뜩 샀는데, 바뀐 게 없다!\"", LGRAY)
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
        for y, s_, sp in ((78, self.B1, 45), (132, self.B2, -40)):
            d.rectangle([0, y, W, y + 20], fill=WHITE, outline=NAVY)
            wfull = tw(s_)
            off = (t * sp) % wfull
            text(d, -int(off) if sp > 0 else int(off) - wfull, y + 2, s_ * 8, NAVY, shadow=None)
        if blink(t, 2):
            pow_box(d, "정신 차려!!", 240, 108, YELLOW, RED, F16)
        box(d, 6, 196, 474, 266)
        text(d, 18, 202, "분노 게이지", WHITE)
        k = min(1.0, max(0.0, (t - 0.8) / 4.0))
        d.rectangle([110, 207, 380, 219], fill=BLACK, outline=WHITE)
        d.rectangle([112, 209, 112 + int(266 * k), 217], fill=RED if k > 0.7 else ORANGE)
        if k >= 1.0 and blink(t, 3):
            text(d, 392, 204, "최대!!", RED)
        if t > 5.0:
            text(d, 18, 226, reveal("팬들: \"이번 시즌은 다르다며!!\"", t - 5.0), GOLD)
        if t > 7.4:
            text(d, 18, 248, reveal("수탉: ...(할 말 없음)", t - 7.4), WHITE)

    def audio(self, m, t0):
        play(m, t0 + 0.2, 9.6, ANGRY, 140, drums="k . k s", duty=0.5, vol=0.06)
        crowd = noise(9.8, 0.04, None, hold=1)
        crowd = np.convolve(crowd, np.ones(20) / 20, mode="same") * 3
        m.add(t0 + 0.1, crowd)
        for k in range(8):
            m.sfx(t0 + 0.4 + k * 1.1, "boo")
        m.blips(t0 + 5.0, "팬들: 이번 시즌은 다르다며!!")
        m.blips(t0 + 7.4, "수탉: (할 말 없음)")


# ------------------------------------------------------------------ 11. 그 사이 (뮌헨 / LA)

class Meanwhile(Scene):
    dur = 10.0

    def draw(self, img, d, t):
        d.rectangle([0, 0, 239, H], fill=(200, 30, 50))
        d.rectangle([240, 0, W, H], fill=(60, 60, 90))
        d.line([(240, 0), (240, H)], fill=BLACK, width=4)
        ctext(d, 6, "한편, 뮌헨의 케인", WHITE, cx=120)
        ctext(d, 6, "한편, LA의 쏘니", WHITE, cx=360)
        # 케인: 발롱도르 준비 완료
        blit(img, chibi("kane"), 93, 104, 3)
        trophy(d, 50, 150)
        trophy(d, 190, 150)
        if t > 0.6:
            k = min(1.0, (t - 0.6) / 0.5)
            ctext(d, 28, "발롱도르 준비 완료!", GOLD, cx=120)
            d.rectangle([30, 52, 210, 64], fill=BLACK, outline=WHITE)
            d.rectangle([32, 54, 32 + int(176 * k), 62], fill=GOLD)
            ctext(d, 68, "배당 1순위 · 시즌 72골", WHITE, cx=120)
            ctext(d, 86, "(분데스리가·포칼 우승)", LGRAY, cx=120)
        # 쏘니: 슬럼프
        blit(img, chibi("son", mood="sad"), 333, 104, 3)
        for i in range(3):
            kk = (t * 0.6 + i / 3) % 1
            d.ellipse([388 + i * 8, 118 - 20 * kk, 393 + i * 8, 123 - 20 * kk], outline=LGRAY)
        if t > 1.6:
            ctext(d, 28, "상태이상: 슬럼프...", (140, 190, 255), cx=360)
            ctext(d, 50, "최근 10경기 1골", LGRAY, cx=360)
            ctext(d, 68, "(미드필더로 기용 중)", LGRAY, cx=360)
        if t > 3.6:
            k = t - 3.6
            y0 = int(270 - 84 * min(1.0, k / 0.3))
            d.rectangle([60, y0, 420, y0 + 84], fill=(30, 30, 50), outline=WHITE, width=2)
            blit(img, COCK_CRY if t > 6.4 else COCK, 76, y0 + 16, 2)
            since = k - 0.3
            lines = ["토트넘을 떠나면 잘 된다?", "케인: O  /  쏘니: ...X"]
            if t > 6.4:
                lines = ["쏘니야... 우리 같이 힘내자...", "(토트넘도 20위다)"]
                since = t - 6.4
            lines_at(d, 124, y0 + 12, lines, since, WHITE)

    def audio(self, m, t0):
        play(m, t0, 1.6, TITLE, 170, drums="k h s h")
        m.sfx(t0 + 0.6, "fanfare")
        play(m, t0 + 1.6, 8.2, SAD, 110, drums=None, duty=0.5, vol=0.07)
        m.sfx(t0 + 1.6, "sad")
        blip_lines(m, t0 + 3.9, ["토트넘을 떠나면 잘 된다?", "케인: O  /  쏘니: ...X"])
        blip_lines(m, t0 + 6.4, ["쏘니야... 우리 같이 힘내자...", "(토트넘도 20위다)"])


# ------------------------------------------------------------------ 12. 컨티뉴

class Continue(Scene):
    dur = 10.5
    COUNT0, STEP = 0.3, 0.6
    COIN = 3.9

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        if t < 4.6:
            ctext(d, 12, "계속하시겠습니까?", RED, F32, shadow=DRED)
            n = 9 - int(max(0.0, t - self.COUNT0) / self.STEP)
            if t >= self.COUNT0:
                ctext(d, 56, str(max(n, 3)), WHITE, F64, shadow=GRAY)
            if 1.6 < t < 3.9 and blink(t, 2):
                ctext(d, 236, "동전을 넣으세요", GOLD)
        d.rectangle([392, 130, 432, 180], fill=(40, 40, 40), outline=LGRAY)
        d.rectangle([408, 136, 414, 172], fill=BLACK)
        if self.COIN <= t < self.COIN + 0.5:
            k = (t - self.COIN) / 0.5
            cy = -16 + 150 * k * k
            d.ellipse([401, cy, 421, cy + 20], fill=GOLD, outline=BLACK)
            text(d, 407, cy + 2, "£", BROWN, shadow=None)
            if cy < 100:
                text(d, 428, cy, "ENIC", LGRAY)
        if t >= self.COIN + 0.5:
            text(d, 360, 190, "크레딧 1", WHITE)
            if t < 6.2:
                text(d, 268, 210, "(ENIC이 또 지갑을 열었다)", LGRAY)
        k = t - 4.8
        if k >= 0:
            jy = -int(50 * 4 * (k / 0.5) * (1 - k / 0.5)) if k < 0.5 else 0
            blit(img, COCK_CRY if t > 7.2 else COCK, 222, 170 + jy, 2)
        else:
            blit(img, COCK_CRY, 222, 170, 2, flip_v=True)
        if t >= 5.4:
            ctext(d, 18, "다음 스테이지 ▶ 맨유 원정", WHITE, F32, shadow=NAVY2)
            ctext(d, 60, "10월 10일 · 올드 트래포드", LGRAY)
        if t >= 6.4:
            text(d, 120, 94, "데 제르비의 목숨", RED)
            for i in range(3):
                col = RED if i == 0 else (70, 60, 70)
                x = 250 + i * 26
                d.polygon([(x, 98), (x + 10, 110), (x + 20, 98), (x + 15, 93), (x + 10, 98), (x + 5, 93)], fill=col)
        if t >= 7.2:
            text(d, 262, 160, "수탉: 꿀꺽...", WHITE)

    def audio(self, m, t0):
        m.seq(t0 + 0.3, 3.6, "A3 - - - E3 - - - F3 - - - E3 - - -", 150, 2, "tri", 0.2)
        for k in range(7):
            m.sfx(t0 + self.COUNT0 + k * self.STEP, "tick")
        m.sfx(t0 + self.COIN, "coin")
        m.sfx(t0 + 4.4, "ding")
        m.sfx(t0 + 4.8, "jump")
        play(m, t0 + 5.4, 1.8, TITLE, 190)
        m.sfx(t0 + 7.2, "gulp")


# ------------------------------------------------------------------ 13. 엔딩

class Ending(Scene):
    dur = 10.0
    fade_out = 1.2
    WALKERS = [("dezerbi", None), ("vdv", "home"), ("fernandes", "away"), ("tonali", "home"),
               ("gallagher", "away")]

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        draw_stars(d, t, 6, n=40, seed=3)
        ctext(d, 8, "시청해 주셔서 감사합니다!", WHITE)
        blit(img, COCK_RUN if int(t * 5) % 2 else COCK, 14 + t * 16 + 5 * 44, 140, 2)
        if t > 1.0:
            ctext(d, 34, reveal("하지만 트로피는", t - 1.0, 12), WHITE)
        if t > 2.2:
            ctext(d, 56, reveal("다른 성에 있습니다!", t - 2.2, 10), GOLD, F32, shadow=DRED)
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
        if t > 4.2:
            ctext(d, 190, "가자, 토트넘!", GOLD, F32, shadow=NAVY2)
        if t > 5.0:
            ctext(d, 246, "※ 2026.09.24 기준 실제 결과 바탕의 풍자 패러디", GRAY)

    def audio(self, m, t0):
        mel = "C5:0.3 E5:0.3 G5:0.3 C6:0.6 B5:0.3 G5:0.3 A5:0.6 F5:0.3 D5:0.3 G5:0.9 E5:0.3 C5:0.3 D5:0.3 C5:1.2"
        m.notes(t0 + 0.3, mel, vol=0.08, duty=0.25)
        m.notes(t0 + 0.3, "C3:1.2 F2:1.2 G2:1.2 C3:1.2 G2:0.6 C3:1.2", kind="tri", vol=0.2)
        for n in ("C4", "E4", "G4"):
            m.notes(t0 + 7.2, f"{n}:1.6", vol=0.05)


# -------------------------------------------------------------------------- main

class ScaledMixer(Mixer):
    """t0 기준으로 시간을 k배 늘려서 원래 믹서에 기록."""

    def __init__(self, base, t0, k):
        self.base, self.t0, self.k = base, t0, k
        self.buf = base.buf

    def add(self, t, sig):
        Mixer.add(self.base, self.t0 + (t - self.t0) * self.k, sig)


class Slow(Scene):
    """장면 전체(대사·연출·효과음)를 k배 느리게 재생해 대사를 읽을 시간을 준다."""

    def __init__(self, inner, k):
        self.inner, self.k = inner, k
        self.dur = inner.dur * k
        self.fade_in, self.fade_out = inner.fade_in, inner.fade_out
        self.__class__ = type(type(inner).__name__, (Slow,), {})

    def draw(self, img, d, t):
        return self.inner.draw(img, d, t / self.k)

    def audio(self, m, t0):
        self.inner.audio(ScaledMixer(m, t0, self.k), t0)


def build():
    return [Slow(Title(), 1.3), Slow(ManagerSelect(), 1.4), Slow(Platformer(), 1.3), Shop(),
            Slow(Battle(), 1.4), Protest(), Tetris(), Slow(Meanwhile(), 1.4), Slow(Continue(), 1.3),
            Slow(Ending(), 1.2)]


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
    wav_path = os.path.join(HERE, "_audio_final.wav")
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
