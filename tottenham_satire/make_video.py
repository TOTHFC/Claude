#!/usr/bin/env python3
"""토트넘 대모험 ~강등권의 전설~

2026년 9월 토트넘 홋스퍼의 현실을 8비트 고전 게임 스타일로 풍자하는 패러디 영상 생성기.
그래픽(도트 캐리커처, 26/27 홈 킷), 칩튠 음악, 효과음을 모두 코드로 만든다.

    pip install pillow numpy imageio-ffmpeg
    python3 make_video.py            # -> tottenham_adventure.mp4 (1920x1080)
"""
import math
import os
import random
import subprocess
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

from characters import PEOPLE, chibi, draw_hammer, monster, portrait
from engine import (BLACK, BROWN, CREAM, DGREEN, DRED, F16, F32, F64, FPS, GOLD, GRAY, GREEN, H,
                    LGRAY, NAVY, NAVY2, ORANGE, RED, SCALE, SKIN, SKIN_D, SKY, SR, W, WHITE, YELLOW,
                    Mixer, blink, blit, box, ctext, draw_flames, draw_stars, drum, make_stamp,
                    noise, reveal, text, tw)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tottenham_adventure.mp4")
STAMP_SACKED = make_stamp("경질")


class Scene:
    dur = 1.0
    fade_in = 0.25
    fade_out = 0.25

    def draw(self, img, d, t):
        pass

    def audio(self, m, t0):
        pass


def lines_at(d, x, y, lines, since, col, step=22, shadow=BLACK):
    """여러 줄을 순서대로 타이핑 효과로 출력한다."""
    for s in lines:
        text(d, x, y, reveal(s, since), col, shadow=shadow)
        since -= len(s) / 24 + 0.15
        y += step


def blip_lines(m, t0, lines):
    for s in lines:
        m.blips(t0, s)
        t0 += len(s) / 24 + 0.15


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
    dur = 7.5
    LINE = ["fernandes", "tonali", "robertson", "dezerbi", "vanhecke", "gallagher", "mudryk"]

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=NAVY)
        draw_stars(d, t, 25)
        ctext(d, 4, "토트넘 대모험", WHITE, F64, shadow=GOLD)
        ctext(d, 74, "~ 강등권의 전설 ~", GOLD)
        d.rectangle([0, 164, W, 178], fill=(24, 120, 48))
        for x in range(0, W, 32):
            d.rectangle([x, 164, x + 15, 178], fill=(32, 140, 60))
        for i, k in enumerate(self.LINE):
            bob = -2 if (int(t * 4) + i) % 2 else 0
            blit(img, chibi(k), 42 + i * 58, 98 + bob, 2)
        cur = 1 if 3.0 <= t < 5.4 else 0
        flash = t >= 6.0 and blink(t, 6)
        for i, s in enumerate(["새 게임", "트로피 진열장"]):
            if i == 0 and t >= 6.0 and not flash:
                continue
            text(d, 190, 186 + i * 20, s, WHITE)
        text(d, 172, 186 + cur * 20, "▶", GOLD)
        if t < 3.0 and blink(t, 1.5):
            ctext(d, 240, "START 버튼을 누르세요", LGRAY)
        if 3.4 <= t < 5.4:
            box(d, 110, 88, 370, 168)
            ctext(d, 96, "- 트로피 진열장 -", GOLD)
            ctext(d, 118, "2025 유로파리그 우승 ×1", WHITE)
            ctext(d, 142, reveal("...끝. 이게 전부다.", t - 4.0, 14), LGRAY)

    def audio(self, m, t0):
        lead = ("C5 - E5 G5 C6 - B5 G5 A5 - F5 A5 G5 - - . "
                "E5 - G5 C6 E6 - D6 C6 B5 - G5 A5 C6 - - .")
        bass = "C3 . C3 . G2 . G2 . F2 . F2 . G2 . G2 . A2 . A2 . E2 . E2 . F2 . G2 . C3 . C3 ."
        m.seq(t0 + 0.2, 5.7, lead, 150, 2, "sq", 0.08, 0.25)
        m.seq(t0 + 0.2, 5.7, bass, 150, 2, "tri", 0.2)
        m.seq(t0 + 0.2, 5.7, "k h s h k k s h", 150, 2, "drum")
        m.sfx(t0 + 3.0, "move")
        m.sfx(t0 + 3.4, "select")
        m.blips(t0 + 4.0, "...끝. 이게 전부다.", 14)
        m.sfx(t0 + 5.4, "move")
        m.sfx(t0 + 6.0, "start")


# ------------------------------------------------------------------ 장 구분 카드

class Chapter(Scene):
    dur = 3.8

    def __init__(self, num, title, lines, faces=()):
        self.num, self.title, self.lines, self.faces = num, title, lines, faces

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        ctext(d, 34, self.num, GOLD, F32, shadow=DRED)
        ctext(d, 78, self.title, WHITE, F32, shadow=NAVY2)
        d.line([(80, 124), (400, 124)], fill=GRAY)
        n = len(self.faces)
        for i, k in enumerate(self.faces):
            if t > 0.4 + i * 0.15:
                blit(img, chibi(k, int(t * 4) % 2), W // 2 - n * 22 + i * 44 + 4, 130, 2)
        y0 = 206 if self.faces else 144
        for i, s in enumerate(self.lines):
            since = t - 0.9 - sum(len(x) / 24 + 0.2 for x in self.lines[:i])
            ctext(d, y0 + i * 24, reveal(s, since), LGRAY)

    def audio(self, m, t0):
        m.sfx(t0 + 0.1, "chapter")
        tt = t0 + 0.9
        for s in self.lines:
            m.blips(tt, s)
            tt += len(s) / 24 + 0.2


# ------------------------------------------------------------------ 2. 감독 선택

class ManagerSelect(Scene):
    dur = 9.8
    KEYS = ["frank", "tudor", "dezerbi"]
    XS = [40, 189, 338]
    SEL = [0.8, 3.4, 6.0]
    STAMP = [2.5, 5.1]
    INFO = [
        ("토마스 프랑크: 8경기 연속 무승", "→ 부임 8개월 만에 경질!"),
        ("이고르 투도르: 부임 44일, 7경기", "→ 리그 5경기 승점 1점. 경질!"),
        ("로베르토 데 제르비: 최종전에서 잔류 성공!", "→ 그런데 올 시즌 4경기째 승리가 없다..."),
    ]

    def cur(self, t):
        return max([i for i, s in enumerate(self.SEL) if t >= s], default=-1)

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(16, 16, 48))
        off = int(t * 8) % 16
        for x in range(-16, W, 16):
            d.line([(x + off, 0), (x + off, H)], fill=(28, 28, 72))
        for y in range(-16, H, 16):
            d.line([(0, y + off), (W, y + off)], fill=(28, 28, 72))
        ctext(d, 4, "감독을 선택하세요", GOLD)
        ctext(d, 22, "※ 지난 시즌에만 3명이 거쳐 갔다", LGRAY)
        c = self.cur(t)
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
        lead = ("A4 C5 E5 C5 A4 C5 E5 C5 G4 B4 D5 B4 G4 B4 D5 B4 "
                "F4 A4 C5 A4 F4 A4 C5 A4 E4 G#4 B4 G#4 E4 G#4 B4 E5")
        m.seq(t0 + 0.3, 7.5, lead, 132, 4, "sq", 0.06, 0.25)
        m.seq(t0 + 0.3, 7.5, "A2 - - - G2 - - - F2 - - - E2 - - -", 132, 1, "tri", 0.2)
        m.seq(t0 + 0.3, 7.5, "k . h . s . h . k k h . s . h h", 132, 4, "drum")
        m.seq(t0 + 7.8, 2.0, "E5 F5 E5 D#5", 240, 2, "sq", 0.07, 0.125)
        m.seq(t0 + 7.8, 2.0, "E2 E3", 240, 2, "tri", 0.2)
        for i, s in enumerate(self.SEL):
            m.sfx(t0 + s, "move" if i else "select")
            l1, l2 = self.INFO[i]
            m.blips(t0 + s + 0.4, l1)
            m.blips(t0 + s + 0.4 + len(l1) / 24 + 0.2, l2)
        for s in self.STAMP:
            m.sfx(t0 + s, "stamp")


# ------------------------------------------------------------------ 3. 플랫포머 (2025-26)

class Platformer(Scene):
    dur = 16.8
    INTRO = 2.0
    SPD = 70.0
    CAM_STOP = 10.4
    GROUND = 222
    HX = 110
    HERO_Y = GROUND - 67
    HITS = [2.9, 3.9, 6.6, 7.5]
    SYMS = ["패", "패", "패", "무"]
    WINLESS = [4, 8, 12, 15]
    BANNERS = ["2026년, 리그 승리가 사라졌다", "8경기 연속 무승...", "구단 최초 6연패", "리그 15경기 연속 무승"]
    HOOKS = [(4.5, "frank"), (8.1, "tudor")]
    DROPS = [(5.4, "tudor"), (9.0, "dezerbi")]
    PAUSES = [(4.5, 5.8), (8.1, 9.4)]
    WALK, JUMP, LAND = 10.4, 11.2, 12.1
    HAMMER = 12.5

    def __init__(self):
        cf = self.cam(self.CAM_STOP)
        self.pit0 = int(round((cf + 232) / 16)) * 16
        self.pit1 = self.pit0 + 112
        self.ps = self.pit0 - cf  # 정지 후 화면상 구덩이 x

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
            ctext(d, 84, "지난 시즌 (2025-26)", LGRAY)
            for i, k in enumerate(["frank", "tudor", "dezerbi"]):
                blit(img, chibi(k), 150 + i * 44, 112, 2)
            text(d, 288, 146, "× 3 (감독)", WHITE)
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
            d.rectangle([sx + 70, 180, sx + 72, 184], fill=DGREEN)
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
        # ? 블록
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
        # 주인공(감독)
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
        if show:
            blit(img, chibi(mgr, frame), hx, hy, 2)
        if hook is not None:
            y = self.HERO_Y + 24
            d.line([(-10, y), (hook, y)], fill=(150, 90, 40), width=5)
            d.arc([hook - 16, y, hook + 16, y + 32], 270, 90, fill=(150, 90, 40), width=5)
            d.line([(hook, y + 30), (hook - 8, y + 30)], fill=(150, 90, 40), width=5)
        for ht, who in self.HOOKS:
            if 0.3 <= t - ht < 1.3:
                box(d, 150, 54, 330, 128)
                blit(img, portrait(who, "shock"), 160, 60, 2)
                text(d, 238, 74, "경질!", RED, F32)
        # 웨스트햄
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
                draw_hammer(d, wx, wy, t)
        # HUD
        wl = 0
        for i, ht in enumerate(self.HITS):
            if t >= ht:
                wl = self.WINLESS[i]
        text(d, 10, 4, "토트넘", WHITE)
        text(d, 170, 4, f"무승 {wl:02d}", WHITE)
        text(d, 290, 4, f"감독: {PEOPLE[mgr]['short']}", WHITE)
        banner = None
        for i, ht in enumerate(self.HITS):
            if 0 <= t - ht < 1.0:
                banner = (self.BANNERS[i], RED)
        for ht, who in self.HOOKS:
            if 0 <= t - ht < 0.9:
                banner = (f"{PEOPLE[who]['name']} 감독 OUT", RED)
        for dr, who in self.DROPS:
            if 0 <= t - dr < 1.2:
                extra = " (시즌 3번째!)" if who == "dezerbi" else ""
                banner = (f"{PEOPLE[who]['name']} 감독 부임{extra}", WHITE)
        if self.WALK <= t < self.LAND:
            banner = ("최종전 vs 에버턴 ─ 지면 강등!", WHITE)
        elif self.LAND <= t < self.LAND + 1.3:
            banner = ("1-0 승리!! 잔류다!!", GOLD)
        elif 13.5 <= t < 14.3:
            banner = ("대신 웨스트햄이 강등...", LGRAY)
        if banner:
            s, col = banner
            w = tw(s)
            d.rectangle([W // 2 - w // 2 - 6, 26, W // 2 + w // 2 + 6, 46], fill=BLACK)
            ctext(d, 28, s, col)
        if t >= 14.3:
            box(d, 100, 64, 380, 172)
            ctext(d, 72, "생존!", GOLD, F32)
            ctext(d, 112, "최종 17위 · 승점 41", WHITE)
            ctext(d, 138, "(세계 9위 부자 구단의 성적표)", LGRAY)

    def audio(self, m, t0):
        lead = ("G5 . D5 G5 . B5 A5 G5 E5 . C5 E5 G5 - . . "
                "F#5 . D5 F#5 . A5 G5 F#5 G5 - - - . . . .")
        bass = "G2 . D3 . G2 . D3 . C3 . G2 . C3 . G2 . D3 . A2 . D3 . A2 . G2 . D3 . G2 . D3 ."
        for a, b in [(self.INTRO, 4.5), (5.8, 8.1), (9.4, self.CAM_STOP)]:
            m.seq(t0 + a, b - a, lead, 160, 2, "sq", 0.07, 0.25)
            m.seq(t0 + a, b - a, bass, 160, 2, "tri", 0.2)
            m.seq(t0 + a, b - a, "k h s h", 160, 2, "drum")
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
        m.seq(t0 + self.WALK, self.JUMP - self.WALK, "E3 . E3 .", 320, 2, "tri", 0.2)
        for k in range(18):
            m.add(t0 + self.JUMP + k * 0.05, drum("h") * 2)
        m.sfx(t0 + self.JUMP, "jump")
        m.sfx(t0 + self.LAND, "land")
        m.notes(t0 + self.LAND + 0.05, "C6:0.08 E6:0.08 G6:0.2", vol=0.08, duty=0.25)
        m.sfx(t0 + 13.45, "fall")
        m.sfx(t0 + 14.3, "fanfare")


# ------------------------------------------------------------------ 4. 이적시장 상점

class Shop(Scene):
    dur = 13.0
    fade_out = 0.0
    ITEMS = [  # (키, 가격, 설명 2줄)
        ("fernandes", "£85M", ("강등팀 웨스트햄 출신", "구단 역대 최고액!")),
        ("tonali", "£££", ("뉴캐슬 출신", "등번호 16")),
        ("robertson", "£££", ("등번호 3번", "(레들리 킹 존중)")),
        ("vanhecke", "£££", ("등번호 6", "센터백")),
        ("senesi", "£££", ("등번호 5", "센터백")),
        ("mudryk", "임대", ("임대 영입", "등번호 27")),
        ("adarabioyo", "£10M", ("첼시 출신", "£10M + 옵션 £2M")),
    ]
    BUY0, GAP = 1.0, 0.95
    LINES = [
        (0.2, ["상인: 어서 오시오! 뭘 사겠소?"], WHITE),
        (1.3, ["상인: 강등팀 선수를 £85M에?!", "      구단 역대 최고액이오! 좋소!"], GOLD),
        (4.0, ["상인: 더! 더 사시오!", "      (그 사이 주장 로메로는 아틀레티코로 떠났소)"], WHITE),
        (7.2, ["상인: 이 정도면 우승이지! 하하하!"], WHITE),
    ]
    SQUAD = ["fernandes", "tonali", "robertson", "vanhecke", "dezerbi", "senesi", "mudryk", "adarabioyo"]

    def bought(self, t):
        return sum(1 for i in range(len(self.ITEMS)) if t >= self.BUY0 + i * self.GAP)

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(24, 16, 40))
        text(d, 10, 4, "★ 2026 여름 이적시장 ★", GOLD)
        n = self.bought(t)
        frac = max(0.04, 1 - n / len(self.ITEMS) * 0.96)
        text(d, 330, 4, "자금", WHITE)
        d.rectangle([368, 7, 470, 19], fill=BLACK, outline=WHITE)
        d.rectangle([370, 9, 370 + int(98 * frac), 17], fill=GREEN if frac > 0.3 else RED)
        # 왼쪽: 방금 산 선수 / 상인
        box(d, 6, 26, 150, 198)
        if n == 0:
            x, y = 44, 44
            d.ellipse([x + 8, y, x + 60, y + 52], fill=SKIN, outline=BLACK)
            d.chord([x + 8, y - 4, x + 60, y + 32], 180, 360, fill=(90, 60, 30))
            d.rectangle([x + 22, y + 22, x + 25, y + 25], fill=BLACK)
            d.rectangle([x + 43, y + 22, x + 46, y + 25], fill=BLACK)
            d.polygon([(x + 18, y + 35), (x + 34, y + 30), (x + 50, y + 35), (x + 34, y + 39)], fill=(60, 40, 20))
            d.rectangle([x + 10, y + 54, x + 58, y + 90], fill=(40, 120, 60), outline=BLACK)
            ctext(d, 150, "이적시장 상인", LGRAY, cx=78)
        else:
            k, price, (c1, c2) = self.ITEMS[n - 1]
            since = t - (self.BUY0 + (n - 1) * self.GAP)
            dy = -6 if since < 0.15 else 0
            blit(img, portrait(k), 44, 34 + dy, 2)
            name = PEOPLE[k]["name"].rsplit(" ", 1)
            ctext(d, 106, name[0], WHITE, cx=78)
            ctext(d, 124, name[1], WHITE, cx=78)
            ctext(d, 150, c1, GOLD, cx=78)
            ctext(d, 170, c2, LGRAY, cx=78)
        # 오른쪽: 목록
        box(d, 156, 26, 474, 198)
        for i, (k, price, _) in enumerate(self.ITEMS):
            yy = 34 + i * 23
            sold = t >= self.BUY0 + i * self.GAP
            col = GRAY if sold else WHITE
            text(d, 178, yy, f"#{PEOPLE[k]['num']}", col)
            text(d, 214, yy, PEOPLE[k]["short"], col)
            text(d, 466 - tw(price), yy, price, GRAY if sold else GOLD)
            if sold:
                text(d, 348, yy, "영입!", RED)
                if t - (self.BUY0 + i * self.GAP) < 0.25:
                    d.rectangle([172, yy, 470, yy + 18], outline=YELLOW)
        if n < len(self.ITEMS):
            text(d, 162, 34 + n * 23, "▶", GOLD)
        # 대화창
        box(d, 6, 204, 474, 266)
        cur = None
        for st, ls, col in self.LINES:
            if t >= st:
                cur = (st, ls, col)
        if cur:
            lines_at(d, 18, 214, cur[1], t - cur[0], cur[2])
        # 새 스쿼드 완성
        if 8.4 <= t < 12.4:
            box(d, 20, 30, 460, 198)
            ctext(d, 38, "새 스쿼드 완성!", GOLD, F32)
            for i, k in enumerate(self.SQUAD):
                bob = -3 if (int(t * 5) + i) % 2 else 0
                blit(img, chibi(k), 32 + i * 53, 84 + bob, 2)
            ctext(d, 166, reveal("이 정도면 우승이지! ...진짜?", t - 9.4, 16), WHITE)
        if t >= 12.4:
            rng = random.Random(int(t * 30))
            for _ in range(20):
                yy = rng.randint(0, H)
                d.rectangle([0, yy, W, yy + rng.randint(1, 8)],
                            fill=rng.choice([WHITE, RED, NAVY2, BLACK, GOLD]))

    def audio(self, m, t0):
        lead = ("F5 . A5 . C6 . A5 . Bb5 . G5 . E5 . C5 . "
                "F5 . A5 . C6 . F6 . E6 . C6 . F6 - - .")
        bass = "F3 . C3 . F3 . C3 . Bb2 . F3 . C3 . G3 . F3 . C3 . A2 . A3 . C3 . C3 . F3 . C3 ."
        m.seq(t0 + 0.2, 12.2, lead, 116, 2, "sq", 0.07, 0.5, decay=0.25)
        m.seq(t0 + 0.2, 12.2, bass, 116, 2, "tri", 0.18)
        m.seq(t0 + 0.2, 12.2, "k . h . s . h .", 116, 2, "drum")
        for st, ls, _ in self.LINES:
            blip_lines(m, t0 + st, ls)
        for i in range(len(self.ITEMS)):
            m.sfx(t0 + self.BUY0 + i * self.GAP, "cash")
        m.sfx(t0 + 8.4, "fanfare")
        m.blips(t0 + 9.4, "이 정도면 우승이지! ...진짜?", 16)
        m.sfx(t0 + 12.4, "glitch")


# ------------------------------------------------------------------ 5. 포켓몬 배틀 (2026-27)

class Battle(Scene):
    fade_in = 0.0
    B0 = 1.0
    FOES = [
        dict(kind="bee", name="브렌트퍼드", player="fernandes", len=5.2,
             msgs=[(0.2, ["야생의 브렌트퍼드가 나타났다!"], BLACK),
                   (1.5, ["토트넘은 £85M 페르난데스를 내보냈다!"], BLACK),
                   (2.9, ["효과가 없는 것 같다...", "0-3 패배!"], RED)],
             result=(3.3, "패", 0, "토트넘 0 : 3 브렌트퍼드"), dmg=[3.3]),
        dict(kind="magpie", name="뉴캐슬", player="tonali", len=5.2,
             msgs=[(0.2, ["뉴캐슬이 나타났다!", "(토날리의 친정팀이다)"], BLACK),
                   (1.8, ["토날리는 옛 동료들과 반갑게 인사했다!"], BLACK),
                   (3.0, ["...그리고 졌다. 0-2 패배!", "개막 2경기 연속 무득점"], RED)],
             result=(3.3, "패", 0, "토트넘 0 : 2 뉴캐슬"), dmg=[3.3]),
        dict(kind="toffee", name="에버턴", player="vanhecke", len=5.0,
             msgs=[(0.2, ["에버턴이 나타났다!"], BLACK),
                   (1.5, ["양 팀 모두 아무것도 하지 않았다..."], BLACK),
                   (2.8, ["0-0 무승부! 승점 1 획득!", "(시즌 첫 승점)"], BLACK)],
             result=(3.1, "무", 1, "토트넘 0 : 0 에버턴"), heal=3.1),
        dict(kind="lion", name="아스톤 빌라", player="robertson", len=8.6,
             msgs=[(0.2, ["아스톤 빌라가 나타났다!"], BLACK),
                   (1.4, ["로버트슨의 어설픈 걷어내기!", "빌라가 선제골을 넣었다!"], BLACK),
                   (3.0, ["...0-3까지 끌려갔다."], RED),
                   (4.3, ["돌아와, 로버트슨! 가라, 갤러거!"], BLACK),
                   (5.5, ["86분 갤러거의 시즌 첫 골!", "추가시간 반 헤케의 헤더 골!"], BLACK),
                   (7.1, ["...그러나 너무 늦었다. 2-3 패배!"], RED)],
             result=(7.4, "패", 0, "토트넘 2 : 3 아스톤 빌라"), dmg=[1.9, 3.2, 7.4],
             hits=[5.8, 6.4], swap=(4.6, "gallagher")),
    ]
    MOODS = ["smile", "neutral", "sweat", "sweat", "shock"]
    OUTRO = 4.2

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
            rt = f["result"][0]
            if 0 <= lt - rt < 1.8:
                board = f["result"][3]
        else:
            lt2 = t - self.end
            if lt2 < 1.6:
                msg = (["토트넘은 눈앞이 캄캄해졌다..."], lt2 - 0.1, BLACK)
            else:
                msg = (["4경기 승점 1점 (3패 1무)", "강등권으로 추락!"], lt2 - 1.6, RED)
        # 우리 선수
        hurt = t < self.end and any(0 <= lt - dt < 0.6 for dt in f.get("dmg", []))
        if not (hurt and int(t * 16) % 2):
            blit(img, chibi(player), 130, 100, 3)
        if t < self.end and "swap" in f and 0 <= lt - f["swap"][0] < 0.35:
            rng = random.Random(int(t * 30))
            for _ in range(12):
                cx, cy, r = rng.randint(120, 190), rng.randint(100, 200), rng.randint(6, 14)
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=LGRAY)
        # 감독 얼굴
        box(d, 8, 66, 100, 172, fill=WHITE, border=NAVY)
        ctext(d, 72, "데 제르비", BLACK, shadow=None, cx=54)
        blit(img, portrait("dezerbi", self.MOODS[min(len(res), 4)]), 20, 94, 2)
        # 우리 상태창
        box(d, 244, 140, 474, 205, fill=WHITE, border=NAVY)
        text(d, 254, 144, f"{PEOPLE[player]['short']} #{PEOPLE[player]['num']}", BLACK, shadow=None)
        text(d, 254, 164, "승점", BLACK, shadow=None)
        d.rectangle([292, 169, 420, 177], fill=BLACK)
        if pts:
            d.rectangle([294, 171, 294 + int(124 * pts / 12), 175], fill=RED)
        text(d, 428, 164, f"{pts}/12", BLACK, shadow=None)
        text(d, 254, 184, "전적", BLACK, shadow=None)
        for i, r in enumerate(res):
            x = 294 + i * 22
            d.rectangle([x, 184, x + 18, 200], fill=RED if r[1] == "패" else GRAY)
            text(d, x + 1, 184, r[1], WHITE, shadow=None)
        # 대화창
        box(d, 6, 208, 474, 266, fill=WHITE, border=NAVY)
        if msg:
            lines_at(d, 18, 216, msg[0], msg[1], msg[2], shadow=None)
        if board:
            d.rectangle([116, 66, 364, 100], fill=NAVY, outline=WHITE, width=2)
            text(d, 124, 75, "FT", GOLD)
            ctext(d, 75, board, WHITE, cx=252)
        if t > self.end + 0.8:
            k = min(1.0, (t - self.end - 0.8) / 2.6)
            a = np.asarray(img).astype(np.float32)
            a[:206] *= 1 - k
            img.paste(Image.fromarray(a.astype(np.uint8)))
        return {"shake": shake}

    def audio(self, m, t0):
        m.sfx(t0, "encounter")
        lead = ("E5 . E5 G5 . E5 A5 . G5 . F#5 . D5 . B4 . "
                "E5 . E5 G5 . E5 B5 . A5 . G5 . F#5 . G5 A5")
        bass = "E2 E3 E2 E3 E2 E3 E2 E3 D2 D3 D2 D3 B1 B2 B1 B2"
        dur = self.end - self.B0
        m.seq(t0 + self.B0, dur, lead, 172, 2, "sq", 0.06, 0.25)
        m.seq(t0 + self.B0, dur, bass, 172, 2, "tri", 0.18)
        m.seq(t0 + self.B0, dur, "k h s h k k s h", 172, 2, "drum")
        for f, s in zip(self.FOES, self.starts):
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
        blip_lines(m, t0 + self.end + 1.6, ["4경기 승점 1점 (3패 1무)", "강등권으로 추락!"])


# ------------------------------------------------------------------ 6. 테트리스

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
        for y, label, val, col in ((15, "점수", "1 (승점)", WHITE), (75, "지운 줄", "0 (승리 수)", WHITE),
                                   (135, "레벨", "강등권", RED)):
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
        # 코로베이니키 (러시아 민요, 퍼블릭 도메인)
        a = ("E5 - B4 C5 D5 - C5 B4 A4 - A4 C5 E5 - D5 C5 B4 - - C5 D5 - E5 - C5 - A4 - A4 - - - "
             ". D5 - F5 A5 - G5 F5 E5 - - C5 E5 - D5 C5 B4 - B4 C5 D5 - E5 - C5 - A4 - A4 - - -")
        bass = "E2 E3 E2 E3 A2 A3 A2 A3 G#2 G#3 G#2 G#3 A2 A3 B2 C3"
        m.seq(t0 + 0.3, 4.1, a, 150, 2, "sq", 0.08, 0.5)
        m.seq(t0 + 0.3, 4.1, bass, 150, 2, "tri", 0.18)
        for k in range(1, self.LAND + 1):
            m.sfx(t0 + self.DROP0 + k / self.RATE, "tick")
        m.sfx(t0 + self.DROP0 + self.LAND / self.RATE + 0.02, "lock")
        for k in range(7):
            m.sfx(t0 + 5.0 + k * 0.5, "siren")


# ------------------------------------------------------------------ 7. 팬 시위

class Protest(Scene):
    dur = 8.0
    B1 = "PROMISED CHANGE, DELIVERED FAILURE ★ "
    B2 = "LOVE TOTTENHAM, HATE ENIC ★ "

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(8, 8, 40))
        for lx in (30, 450):
            d.polygon([(lx, 12), (lx - 80, 110), (lx + 80, 110)], fill=(24, 24, 64))
            d.ellipse([lx - 8, 4, lx + 8, 20], fill=WHITE)
        ctext(d, 26, "지난 시즌 최종전 직후, 팬들의 분노", WHITE)
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
        for y, s, sp in ((78, self.B1, 55), (132, self.B2, -48)):
            d.rectangle([0, y, W, y + 20], fill=WHITE, outline=NAVY)
            wfull = tw(s)
            off = (t * sp) % wfull
            text(d, -int(off) if sp > 0 else int(off) - wfull, y + 2, s * 5, NAVY, shadow=None)
        box(d, 6, 196, 474, 266)
        text(d, 18, 203, "\"약속은 '변화', 결과는 '실패'\"", GOLD)
        text(d, 18, 223, "\"토트넘은 사랑한다, ENIC(구단주)은 싫다\"", GOLD)
        text(d, 18, 244, "분노 게이지", WHITE)
        k = min(1.0, max(0.0, (t - 0.8) / 4.5))
        d.rectangle([110, 247, 380, 259], fill=BLACK, outline=WHITE)
        d.rectangle([112, 249, 112 + int(266 * k), 257], fill=RED if k > 0.7 else ORANGE)
        if k >= 1.0 and blink(t, 3):
            text(d, 392, 244, "MAX!!", RED)

    def audio(self, m, t0):
        m.seq(t0 + 0.2, 7.4, "k . c . k k c .", 124, 2, "drum")
        crowd = noise(7.6, 0.04, None, hold=1)
        crowd = np.convolve(crowd, np.ones(20) / 20, mode="same") * 3
        m.add(t0 + 0.1, crowd)
        for k in range(7):
            m.sfx(t0 + 0.4 + k * 0.97, "boo")


# ------------------------------------------------------------------ 8. 컨티뉴

class Continue(Scene):
    dur = 10.0
    COUNT0, STEP = 0.3, 0.7
    COIN = 4.5

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        if t < 5.2:
            ctext(d, 12, "계속하시겠습니까?", RED, F32, shadow=DRED)
            n = 9 - int(max(0.0, t - self.COUNT0) / self.STEP)
            if t >= self.COUNT0:
                ctext(d, 56, str(max(n, 3)), WHITE, F64, shadow=GRAY)
            if 2.0 < t < 4.5 and blink(t, 2):
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
        if t >= 5.0:
            text(d, 372, 190, "크레딧 01", WHITE)
        k = t - 5.4
        if 0 <= k:
            jy = -int(50 * 4 * (k / 0.5) * (1 - k / 0.5)) if k < 0.5 else 0
            blit(img, chibi("dezerbi"), 222, 150 + jy, 2)
        else:
            blit(img, chibi("dezerbi"), 222, 150, 2, flip_v=True)
        if t >= 6.0:
            ctext(d, 24, "다음 스테이지 ▶ 맨유 원정", WHITE)
            ctext(d, 46, "10월 10일 · 올드 트래퍼드", LGRAY)
        if t >= 7.0:
            ctext(d, 92, "데 제르비 감독의 남은 목숨: ♥♡♡", RED)

    def audio(self, m, t0):
        m.seq(t0 + 0.3, 4.4, "A3 - - - E3 - - - F3 - - - E3 - - -", 170, 2, "tri", 0.2)
        for k in range(7):
            m.sfx(t0 + self.COUNT0 + k * self.STEP, "tick")
        m.sfx(t0 + self.COIN, "coin")
        m.sfx(t0 + 5.0, "ding")
        m.sfx(t0 + 5.4, "jump")
        m.notes(t0 + 6.0, "G5:0.1 C6:0.1 E6:0.1 G6:0.3", vol=0.08, duty=0.25)
        m.sfx(t0 + 7.0, "sad")


# ------------------------------------------------------------------ 9. 엔딩

class Ending(Scene):
    dur = 8.0
    fade_out = 1.2
    WALKERS = ["dezerbi", "fernandes", "tonali", "gallagher", "robertson"]

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        draw_stars(d, t, 6, n=40, seed=3)
        ctext(d, 12, "시청해 주셔서 감사합니다!", WHITE)
        if t > 0.8:
            ctext(d, 40, reveal("하지만 트로피는", t - 0.8, 12), WHITE)
        if t > 2.0:
            ctext(d, 62, reveal("다른 성에 있습니다!", t - 2.0, 10), GOLD, F32, shadow=DRED)
        cx, cy = 390, 136
        d.rectangle([cx, cy, cx + 60, cy + 42], fill=(150, 80, 40), outline=BLACK)
        for bx in range(cx, cx + 60, 12):
            d.rectangle([bx, cy - 8, bx + 6, cy], fill=(150, 80, 40), outline=BLACK)
        d.rectangle([cx + 22, cy + 18, cx + 38, cy + 42], fill=BLACK)
        d.line([(cx + 30, cy - 8), (cx + 30, cy - 30)], fill=LGRAY)
        d.polygon([(cx + 30, cy - 30), (cx + 46, cy - 25), (cx + 30, cy - 20)], fill=RED)
        text(d, cx + 26, cy + 1, "?", GOLD, shadow=None)
        d.line([(0, 178), (W, 178)], fill=GRAY)
        for i, k in enumerate(self.WALKERS):
            x = 10 + t * 14 + i * 46
            blit(img, chibi(k, int(t * 5 + i) % 2), x, 110, 2)
        if t > 3.3:
            ctext(d, 190, "다음 화에 계속" + "." * (int(t * 2) % 4), LGRAY)
        if t > 4.0:
            ctext(d, 226, "※ 2026.09.24 기준 실제 경기 결과 바탕의 풍자 패러디", GRAY)
            ctext(d, 246, "※ 인물은 특징을 살린 도트 캐리커처입니다", GRAY)

    def audio(self, m, t0):
        mel = ("C5:0.3 E5:0.3 G5:0.3 C6:0.6 B5:0.3 G5:0.3 A5:0.6 F5:0.3 D5:0.3 "
               "G5:0.9 E5:0.3 C5:0.3 D5:0.3 C5:1.2")
        m.notes(t0 + 0.3, mel, vol=0.08, duty=0.25)
        m.notes(t0 + 0.3, "C3:1.2 F2:1.2 G2:1.2 C3:1.2 G2:0.6 C3:1.2", kind="tri", vol=0.2)
        for n in ("C4", "E4", "G4"):
            m.notes(t0 + 6.3, f"{n}:1.2", vol=0.05)


# -------------------------------------------------------------------------- main

def build_scenes():
    return [
        Boot(), Title(),
        Chapter("제1장", "지난 시즌 (2025-26)", ["감독이 3번 바뀌었고,", "강등 직전까지 갔다."],
                faces=["frank", "tudor", "dezerbi"]),
        ManagerSelect(), Platformer(),
        Chapter("제2장", "2026 여름 이적시장", ["겨우 살아남은 구단은", "지갑을 활짝 열었다."],
                faces=["fernandes", "tonali", "robertson", "vanhecke", "senesi", "mudryk", "adarabioyo"]),
        Shop(),
        Chapter("제3장", "이번 시즌 (2026-27)", ["큰돈을 쓴 새 팀,", "개막 4경기의 결과는?"]),
        Battle(), Tetris(), Protest(), Continue(), Ending(),
    ]


def main():
    scenes = build_scenes()
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
            arr = (arr * (round(max(0.0, k) * 4) / 4)).astype(np.uint8)  # NES식 계단형 페이드
        big = arr.repeat(SCALE, 0).repeat(SCALE, 1)
        big[3::4] = (big[3::4] * 0.72).astype(np.uint8)  # CRT 주사선
        proc.stdin.write(big.tobytes())
        if fi % 600 == 0:
            print(f"frame {fi}/{nframes}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(wav_path)
    print("wrote", OUT, f"({total:.1f}s)")


if __name__ == "__main__":
    main()
