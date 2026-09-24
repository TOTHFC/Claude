#!/usr/bin/env python3
"""토트넘 대모험 ─ 희망고문 에디션 (60초)

'좋아 보이는 건 전부 함정'인 트롤 게임(고양이 마리오류) 한 판으로 토트넘의 2026년 9월을 풍자한다.
세이브 파일(지난 시즌) → 월드 26-27 한 판(이적시장·개막 5경기·희망의 계단) → 지하 20층 → 컨티뉴.
BGM·효과음은 모두 새로 작곡·합성한 칩튠.

    python3 make_hope.py              # -> tottenham_hope.mp4 (1920x1080)
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
                    ctext, draw_stars, drum, make_stamp, noise, text, tone, tw)
from make_short import (STAGE, TITLE, banner, blips, confetti, dialog, play, pow_box, reveal, say, trophy)
from sprites import COCK, COCK_CRY, PEOPLE, chibi, draw_hammer, kit_icon, monster, portrait

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tottenham_hope.mp4")
STAMP = make_stamp("경질")
STAMP_S = make_stamp("경질", font=F16)
PURPLE = (150, 90, 255)
PINK = (255, 70, 170)

FILE = ("C5 G4 E5 G4 D5 G4 F5 G4 E5 G4 C5 G4 D5 B4 G4 B4", "C3 . . . G2 . . . A2 . . . G2 . . .")
UNDER = ("E4 . . G4 . . A4 . Bb4 . A4 . G4 . . . E4 . . G4 . . A4 . C5 . B4 . Bb4 . . .",
         "E2 E2 . E2 B1 . E2 . E2 E2 . E2 D2 . D2 .")


class Scene:
    dur = 1.0
    fade_in = 0.0
    fade_out = 0.0

    def draw(self, img, d, t):
        pass

    def audio(self, m, t0):
        pass


# ------------------------------------------------------------------ 1. 타이틀 (3.0s)

class Title(Scene):
    dur = 3.0

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=NAVY)
        draw_stars(d, t, 40)
        y = int(-70 + 78 * min(1.0, t / 0.35))
        ctext(d, y, "토트넘 대모험", WHITE, F64, shadow=GOLD)
        if t > 0.45:
            ctext(d, 82, "─ 희망고문 에디션 ─", RED, F32, shadow=DRED)
        if t > 0.9:
            ctext(d, 132, reveal("※ 이 게임은 당신의 희망을 먹고 자랍니다", t - 0.9), LGRAY)
        blit(img, COCK, 216, 160, 2)
        if t < 2.3:
            if blink(t, 3):
                ctext(d, 230, "▶ 시작 버튼을 누르세요", WHITE)
        elif blink(t, 10):
            ctext(d, 230, "▶ 시작!", YELLOW)

    def audio(self, m, t0):
        m.sfx(t0 + 0.35, "land")
        play(m, t0 + 0.35, 1.95, TITLE, 190)
        m.sfx(t0 + 2.3, "start")


# ------------------------------------------------------------------ 2. 세이브 파일 = 지난 시즌 요약 (3.6s)

class SaveFile(Scene):
    dur = 3.6

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=(16, 16, 48))
        ctext(d, 6, "세이브 파일 불러오기", GOLD)
        box(d, 12, 28, 468, 208)
        text(d, 24, 36, "파일 1 · 2025-26 시즌", WHITE)
        for i, (k, mood, lab, col) in enumerate([("frank", "shock", "경질", RED), ("tudor", "shock", "경질(44일)", RED),
                                                  ("dezerbi", "smile", "생존", GREEN)]):
            x = 22 + i * 78
            if t > 0.1 + i * 0.15:
                blit(img, portrait(k, mood), x, 60, 2)
                ctext(d, 132, lab, col, cx=x + 34)
                if lab != "생존":
                    img.paste(STAMP_S, (x + 34 - STAMP_S.width // 2, 94 - STAMP_S.height // 2), STAMP_S)
        lines = [("최종 17위 (2시즌 연속)", WHITE), ("트로피 0 · 감독 3명 소모", LGRAY),
                 ("최종전 팔리냐 1-0 → 잔류", GOLD), ("대신 웨스트햄 강등", LGRAY), ("같은 날 아스날은 우승", RED)]
        since = t - 0.5
        for i, (s, col) in enumerate(lines):
            text(d, 256, 58 + i * 22, reveal(s, since), col)
            since -= len(s) / 40 + 0.05
        if t > 2.6 and blink(t, 8):
            ctext(d, 228, "▶ 이어하기: 2026-27 시즌", YELLOW)
        elif t <= 2.6:
            ctext(d, 228, "  이어하기: 2026-27 시즌", GRAY)

    def audio(self, m, t0):
        play(m, t0, 2.6, FILE, 150, drums=None, duty=0.5, spb=4)
        blips(m, t0 + 0.5, "최종 17위 (2시즌 연속) 트로피 0 · 감독 3명 소모 최종전 팔리냐 1-0 → 잔류 대신 웨스트햄 강등 같은 날 아스날은 우승")
        m.sfx(t0 + 2.6, "select")


# ------------------------------------------------------------------ 3. 월드 카드 (1.4s)

class WorldCard(Scene):
    dur = 1.4

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        ctext(d, 70, "월드 26-27", WHITE, F32)
        blit(img, chibi("dezerbi"), 186, 120, 2)
        text(d, 232, 146, "× 1", WHITE)
        ctext(d, 204, "희망 × ∞", GOLD)

    def audio(self, m, t0):
        m.notes(t0, "G4:0.1 C5:0.1 E5:0.1 G5:0.1 E5:0.1 G5:0.5", vol=0.09, duty=0.25)


# ------------------------------------------------------------------ 4. 월드 26-27 (42s, 한 번도 안 끊김)

GROUND = 222
HERO_SX = 330
SPACING = 28


class World(Scene):
    dur = 42.0
    SEGS = [(0, 18.0, 100), (18.0, 19.6, 0), (19.6, 21.0, 100), (21.0, 24.5, 35), (24.5, 28.0, 100),
            (28.0, 31.0, 60), (31.0, 33.0, 0)]
    BUYS = [(0.9, "fernandes", "페르난데스 £85M (구단 신기록!)", 85), (1.8, "tonali", "토날리 £92.5M (뉴캐슬에서)", 92.5),
            (2.7, None, "사비뉴 £75M (맨시티에서)", 75), (3.6, "vanhecke", "반 헤케 £52M (브라이튼에서)", 52),
            (4.5, "robertson", "로버트슨 (무료!)", 0), (5.4, "senesi", "세네시 (무료!)", 0),
            (6.3, "mudryk", "무드릭 (임대)", 0), (7.2, "adarabioyo", "아다라비오요 (첼시에서)", 0)]
    ROMERO_OUT = 8.1
    CAPTAIN = 8.8
    KITBLOCK = 9.4
    AWAY = [(10.2, 14.0), (17.4, 21.0)]
    STAIRS = 27.2
    CLIMB0, CLIMB1 = 28.0, 31.0
    TRAP = 31.0
    FALL = 31.35
    UNDER = 33.0

    def x(self, t):
        return sum(sp * max(0.0, min(t, b) - a) for a, b, sp in self.SEGS)

    # --- 월드 좌표 기준 계단 높이
    def stairs_h(self, wx, t):
        if t < self.STAIRS:
            return 0
        x0 = self.x(self.CLIMB0)
        k = (wx - x0) / 30.0
        if k < 0:
            return 0
        return min(6, int(k) + 1) * 15 if k < 7.5 else 0

    def members(self, t):
        ms = ["vdv", "gallagher"]
        if t < self.ROMERO_OUT:
            ms.append("romero")
        for bt, k, _, _ in self.BUYS:
            if k and t >= bt + 0.25:
                ms.append(k)
        return ms

    def kit(self, t):
        return "away" if any(a <= t < b for a, b in self.AWAY) else "home"

    def jump_off(self, t):
        """히어로 점프 높이."""
        y = 0
        hits = [bt for bt, _, _, _ in self.BUYS] + [self.KITBLOCK]
        for ht in hits:
            k = t - (ht - 0.2)
            if 0 <= k < 0.4:
                y = max(y, 44 * 4 * (k / 0.4) * (1 - k / 0.4))
        k = t - 19.6
        if 0 <= k < 0.7:
            y = max(y, 80 * 4 * (k / 0.7) * (1 - k / 0.7))
        return y

    def draw(self, img, d, t):
        if t >= self.UNDER:
            return self.draw_under(img, d, t - self.UNDER)
        hx = self.x(t)
        cam = hx - HERO_SX
        slow = 21.0 <= t < 24.5
        # 하늘/배경
        d.rectangle([0, 0, W, H], fill=(70, 110, 190) if slow else SKY)
        for wx, wy in ((40, 50), (220, 70), (380, 44), (560, 80)):
            sx = (wx - cam * 0.3) % 680 - 100
            for ox, oy, r in ((0, 4, 12), (14, 0, 15), (32, 4, 12)):
                d.ellipse([sx + ox - r, wy + oy - r // 2, sx + ox + r, wy + oy + r // 2 + 5], fill=WHITE)
        for wx in (0, 300, 600):
            sx = (wx - cam * 0.5) % 900 - 160
            d.ellipse([sx, 160, sx + 160, 270], fill=GREEN, outline=DGREEN)
        # 표지판
        for (wx, s, col) in ((self.x(0) + 200, "여름 이적시장 ▶", GOLD), (self.x(10.0) + 150, "리그 개막 ▶", WHITE),
                             (self.x(24.5) + 130, "5R 빌라 ▶", WHITE)):
            sx = wx - cam
            if -120 < sx < W:
                d.rectangle([sx + 40, GROUND - 40, sx + 44, GROUND], fill=BROWN)
                w = tw(s) + 10
                d.rectangle([sx, GROUND - 60, sx + w, GROUND - 40], fill=(240, 220, 170), outline=BLACK)
                text(d, sx + 5, GROUND - 58, s, NAVY, shadow=None)
        # 땅 (함정 이후 계단 구간 붕괴)
        pit0, pit1 = self.x(self.CLIMB0) - 30, self.x(self.CLIMB1) + 400
        gx0 = int(cam // 16) * 16
        for wx in range(gx0, gx0 + W + 32, 16):
            sx = wx - cam
            drop = 0
            if t >= self.TRAP and pit0 <= wx < pit1:
                drop = 900 * (t - self.TRAP) ** 2
            if drop > 80:
                continue
            for gy in (GROUND, GROUND + 16, GROUND + 32):
                y = gy + drop
                d.rectangle([sx, y, sx + 15, y + 15], fill=BROWN)
                d.line([(sx, y), (sx + 15, y)], fill=(252, 188, 176))
                d.line([(sx, y + 8), (sx + 15, y + 8)], fill=BLACK)
                d.line([(sx, y + 1), (sx, y + 7)], fill=BLACK)
        # ? 블록
        for bt, k, label, fee in self.BUYS:
            bx = self.x(bt) - cam + 8
            if -24 < bx < W:
                used = t >= bt
                d.rectangle([bx, 96, bx + 17, 113], fill=(150, 80, 40) if used else GOLD, outline=BLACK)
                if not used:
                    text(d, bx + 5, 96, "?", BROWN, shadow=None)
                kk = t - bt
                if 0 <= kk < 0.6:
                    iy = 70 - int(30 * min(1, kk / 0.3))
                    d.ellipse([bx + 2, iy, bx + 15, iy + 13], fill=GOLD, outline=BLACK)
                    text(d, bx + 5, iy - 2, "£", BROWN, shadow=None)
                    if k and kk < 0.25:
                        blit(img, chibi(k, kit="home"), bx - 8, 96 - 68 * (kk / 0.25), 2)
        kb = self.x(self.KITBLOCK) - cam + 8
        if -24 < kb < W:
            d.rectangle([kb, 96, kb + 17, 113], fill=(150, 80, 40) if t >= self.KITBLOCK else PURPLE, outline=BLACK)
            if 0 <= t - self.KITBLOCK < 1.0:
                kk = t - self.KITBLOCK
                for j, kitname in enumerate(("home", "away")):
                    blit(img, kit_icon(kitname), kb - 22 + j * 30, 60 - 30 * min(1, kk / 0.3), 1)
        # 로메로 파이프
        px = self.x(self.ROMERO_OUT) - cam + 40
        if -40 < px < W:
            d.rectangle([px, GROUND - 40, px + 30, GROUND], fill=(40, 170, 60), outline=BLACK)
            d.rectangle([px - 4, GROUND - 48, px + 34, GROUND - 38], fill=(60, 200, 80), outline=BLACK)
            text(d, px - 10, GROUND - 68, "→마드리드", WHITE)
            kk = t - (self.ROMERO_OUT - 0.5)
            if 0 <= kk < 0.9:
                sy = GROUND - 67 - 60 * math.sin(min(kk, 0.5) / 0.5 * math.pi) if kk < 0.5 else GROUND - 116 + (kk - 0.5) * 160
                sxr = px - 60 + 60 * min(1, kk / 0.5)
                img_r = chibi("romero", kit="home")
                blit(img, img_r, sxr - 3, sy, 2)
                d.rectangle([px - 6, GROUND - 48, px + 36, GROUND - 38], fill=(60, 200, 80), outline=BLACK)
        # 적들
        self.draw_enemies(img, d, t, cam)
        # 계단
        if t >= self.STAIRS:
            x0 = self.x(self.CLIMB0)
            for i in range(7):
                sx = x0 + i * 30 - cam
                h = min(6, i + 1) * 15
                drop = 900 * max(0, t - self.TRAP - i * 0.04) ** 2 if t >= self.TRAP else 0
                glow = GOLD if int(t * 6 + i) % 2 else YELLOW
                d.rectangle([sx, GROUND - h + drop, sx + 29, GROUND + drop], fill=glow, outline=BROWN)
            fx = x0 + 7 * 30 - cam
            fy = GROUND - 90 - 60
            if t < self.TRAP:
                d.line([(fx, fy), (fx, GROUND - 90)], fill=LGRAY, width=2)
                d.polygon([(fx, fy), (fx + 34, fy + 8), (fx, fy + 16)], fill=GOLD, outline=BLACK)
                text(d, fx + 2, fy, "역전", RED, shadow=None)
            else:
                spr = monster("lion", t)
                img.paste(spr, (int(fx - 60), int(fy - 70)), spr)
                if blink(t, 4):
                    pow_box(d, "ㅋㅋㅋ", fx + 40, fy - 70, YELLOW, RED, F16)
        # 팀 (히어로 + 기차놀이)
        ms = self.members(t)
        kit = self.kit(t)
        hurt = any(0 <= t - h < 0.35 for h in self.hurt_times())
        for i in range(len(ms), -1, -1):
            wx = hx - i * SPACING
            ti = t - i * 0.08
            y = GROUND - 67 - self.stairs_h(wx, t)
            if i == 0:
                y -= self.jump_off(t)
            else:
                y -= self.jump_off(ti)
            if t >= self.FALL:
                y += 700 * max(0, t - self.FALL - i * 0.03) ** 2
            moving = any(a <= t < b and sp > 0 for a, b, sp in self.SEGS)
            fr = int(t * (4 if slow else 10) + i) % 2 if moving else 0
            sx = wx - cam
            if hurt and int(t * 16) % 2:
                continue
            mood = "shock" if t >= self.TRAP else ("sad" if slow else "smile")
            if i == 0:
                blit(img, chibi("dezerbi", fr, mood=mood), sx, y, 2)
            else:
                blit(img, chibi(ms[i - 1], fr, kit=kit, mood=mood), sx, y, 2)
            if slow and i % 2 == 0:
                kz = (t * 0.8 + i * 0.3) % 1
                text(d, sx + 30, y - 10 - 20 * kz, "z", WHITE)
        if 10.15 <= t < 10.5 or 17.35 <= t < 17.7:
            for j in range(10):
                a = j / 10 * math.tau + t * 8
                d.point((HERO_SX - 120 + math.cos(a) * 140, 170 + math.sin(a) * 40), fill=PINK)
        if self.CAPTAIN <= t < self.CAPTAIN + 0.9:
            vx = hx - SPACING - cam
            d.polygon([(vx + 10, 110), (vx + 18, 90), (vx + 26, 110)], fill=YELLOW, outline=BLACK)
        # 공 (드리블)
        if not (14.8 <= t < 17.6) and t < self.TRAP:
            bx = HERO_SX + 44 + (4 if int(t * 8) % 2 else 0)
            by = GROUND - 12 - abs(math.sin(t * 9)) * 6 - self.stairs_h(hx + 44, t)
            d.ellipse([bx, by, bx + 11, by + 11], fill=WHITE, outline=BLACK)
            d.rectangle([bx + 4, by + 4, bx + 6, by + 6], fill=BLACK)
        if slow:
            a = np.asarray(img).astype(np.float32)
            a = a * 0.8 + np.array([10, 10, 40])
            img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
            d = ImageDraw.Draw(img)
            d.fontmode = "1"
            ctext(d, 60, "( 슬 로 모 션 )", WHITE)
        if self.TRAP <= t < self.TRAP + 0.5:
            a = np.asarray(img).astype(np.float32)
            a = a.mean(axis=2, keepdims=True) * np.array([1.05, 0.9, 0.7])
            img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
            d = ImageDraw.Draw(img)
            d.fontmode = "1"
        self.draw_hud(d, t)
        b = self.banner(t)
        if b:
            banner(d, b[0], b[1], y=30)
        if 32.2 <= t:
            d.rectangle([0, 0, W, H], fill=BLACK)
            ctext(d, 110, "↓ 강등권으로 추락 ↓", RED, F32, shadow=DRED)
        return None

    def hurt_times(self):
        return [11.2, 11.8, 12.4, 16.0, 25.2, 25.8, 26.4]

    def draw_enemies(self, img, d, t, cam):
        # 1R 벌떼
        if 10.5 <= t < 13.6:
            k = t - 10.5
            for i in range(7):
                a = k * 4 + i * 0.9
                ex = HERO_SX - 60 + math.cos(a) * (120 - 20 * min(1, k)) + max(0, 1 - k) * 300
                ey = 120 + math.sin(a * 1.3) * 40
                spr = monster("bee", t + i)
                small = spr.resize((64, 64), Image.NEAREST)
                img.paste(small, (int(ex), int(ey)), small)
        # 2R 까치
        if 14.2 <= t < 17.6:
            k = t - 14.2
            if k < 0.6:
                mx, my = W - k / 0.6 * (W - HERO_SX - 30), 40 + k / 0.6 * 130
            else:
                mx, my = HERO_SX + 30 + (k - 0.6) * 260, 170 - (k - 0.6) * 150
            spr = monster("magpie", t).resize((96, 96), Image.NEAREST)
            img.paste(spr, (int(mx), int(my) - 40), spr)
            if k >= 0.6:
                d.ellipse([mx + 60, my + 4, mx + 71, my + 15], fill=WHITE, outline=BLACK)
            if k < 1.4:
                tx = HERO_SX - 4 * SPACING
                d.rectangle([tx - 10, 108, tx + 96, 128], fill=WHITE, outline=BLACK)
                text(d, tx - 6, 110, "친정팀 안녕~", BLACK, shadow=None)
        # 3R 나무
        if 17.0 <= t < 21.0:
            tx = self.x(18.0) + 70 - cam
            spr = monster("tree", t)
            img.paste(spr, (int(tx - 30), GROUND - 150), spr)
            if 18.0 <= t < 19.6 and int((t - 18.0) / 0.5 * 2) % 2 == 0:
                text(d, HERO_SX + 30, 120, "쿵!", WHITE, F32)
        # 4R 토피
        if 21.0 <= t < 24.5:
            ex = self.x(22.5) + 180 - cam
            spr = monster("toffee", t)
            img.paste(spr, (int(ex - 40), GROUND - 150), spr)
        # 5R 사자
        if 24.5 <= t < self.STAIRS + 0.8:
            k = t - 24.5
            ex = W - min(1.0, k / 0.6) * 116 + max(0, t - self.STAIRS) * 300
            spr = monster("lion", t, flash=False)
            img.paste(spr, (int(ex), GROUND - 150), spr)
            if k < 1.8:
                for i in range(6):
                    y = 100 + i * 18
                    x0 = ex - ((t * 500 + i * 60) % 260)
                    d.line([(x0, y), (x0 - 40, y)], fill=WHITE, width=2)
        # 불꽃놀이 (추격골)
        for ft in (28.8, 29.8):
            k = t - ft
            if 0 <= k < 0.8:
                for j in range(12):
                    a = j / 12 * math.tau
                    r = 10 + 50 * k
                    d.rectangle([240 + math.cos(a) * r, 80 + math.sin(a) * r, 242 + math.cos(a) * r,
                                 82 + math.sin(a) * r], fill=[GOLD, WHITE, PINK][j % 3])

    def hud_vals(self, t):
        spent = sum(fee for bt, _, _, fee in self.BUYS if t >= bt)
        pts = (1 if t >= 20.0 else 0) + (1 if t >= 23.0 else 0)
        rank = "-"
        for tt, r in ((12.6, 19), (16.0, 20), (20.0, 18), (23.0, 17), (31.8, 20)):
            if t >= tt:
                rank = r
        return spent, pts, rank

    def draw_hud(self, d, t):
        spent, pts, rank = self.hud_vals(t)
        d.rectangle([0, 0, W, 22], fill=BLACK)
        text(d, 8, 3, "토트넘", WHITE)
        text(d, 80, 3, f"지출 £{spent:g}M" + ("+" if spent else ""), GOLD)
        text(d, 250, 3, f"승점 {pts}", WHITE)
        text(d, 340, 3, f"순위 {rank}" + ("위" if rank != "-" else ""), RED if rank in (18, 19, 20) else WHITE)

    def banner(self, t):
        if t < 0.8:
            return ("여름 이적시장 개장!", GOLD)
        for bt, k, label, fee in self.BUYS:
            if bt <= t < bt + 0.85:
                return (label, GOLD if fee else WHITE)
        seq = [(self.ROMERO_OUT - 0.5, self.ROMERO_OUT + 0.3, "주장 로메로 → 아틀레티코 이적", LGRAY),
               (self.CAPTAIN, self.CAPTAIN + 0.6, "새 주장: 반 더 벤!", GOLD),
               (self.KITBLOCK, self.KITBLOCK + 0.8, "26/27 홈·원정 유니폼 획득!", GOLD),
               (10.2, 11.0, "1R 브렌트포드 원정 (원정 유니폼 장착)", WHITE),
               (11.0, 12.6, "벌떼 습격!", RED),
               (12.6, 14.2, "1R 브렌트포드 원정 0-3 패", RED),
               (14.2, 16.0, "2R 뉴캐슬 홈 · 까치가 공을 훔쳐 갔다!", WHITE),
               (16.0, 17.4, "2R 뉴캐슬 홈 0-2 패", RED),
               (17.4, 20.0, "3R 포레스트 원정 · 나무를 못 뚫는다", WHITE),
               (20.0, 21.0, "0-0 · 시즌 첫 승점!", GOLD),
               (21.0, 23.0, "4R 에버튼 홈 · 모두 졸고 있다...", WHITE),
               (23.0, 24.5, "0-0 · 승점 +1 (쿨쿨)", LGRAY),
               (24.5, 25.2, "5R 아스톤 빌라 홈", WHITE),
               (25.2, 27.2, "0-1... 0-2... 0-3...", RED),
               (27.2, 28.8, "희망의 계단 등장?!", GOLD),
               (28.8, 29.8, "86분 갤러거 골! 1-3", GOLD),
               (29.8, 30.5, "추가시간 반 헤케 골! 2-3", GOLD),
               (30.5, 31.0, "한 골만 더 넣으면...!", YELLOW),
               (31.0, 31.8, "희망고문 트랩 발동!", RED),
               (31.8, 32.2, "종료 2-3 패", RED)]
        for a, b, s, col in seq:
            if a <= t < b:
                return (s, col)
        return None

    # --- 지하 20층 (9s)
    def draw_under(self, img, d, k):
        cam = k * 140
        d.rectangle([0, 0, W, H], fill=(40, 8, 8))
        for i in range(5):
            yy = 200 + i * 14
            pts = [(0, H)] + [(x, yy + int(3 * math.sin(x * 0.05 + k * 3 + i))) for x in range(0, W + 8, 8)] + [(W, H)]
            d.polygon(pts, fill=(120 + i * 25, 20 + i * 20, 10))
        # 광고판
        boards = [(360, "board_cup"), (760, "kane"), (1120, "son"), (1480, "enic")]
        for bx0, kind in boards:
            bx = bx0 - cam
            if -200 < bx < W + 10:
                self.board(img, d, bx, kind, k)
        d.rectangle([0, 186, W, 200], fill=(80, 60, 50))
        ms = ["dezerbi"] + self.members(self.UNDER)
        for i, key in enumerate(ms):
            sx = HERO_SX - 60 - i * SPACING
            fr = int(k * 6 + i) % 2
            if key == "dezerbi":
                blit(img, chibi(key, fr, mood="sad"), sx, 118, 2)
            else:
                blit(img, chibi(key, fr, kit="home", mood="sad"), sx, 118, 2)
        d.rectangle([0, 0, W, 22], fill=BLACK)
        text(d, 8, 3, "지하 20층: 강등권", RED)
        text(d, 200, 3, "5경기 0승 2무 3패 · 승점 2 · 20위", WHITE)
        if k < 1.2:
            ctext(d, 244, reveal("여기가... 강등권?", k - 0.2), WHITE)

    def board(self, img, d, x, kind, k):
        d.rectangle([x, 34, x + 190, 160], fill=(30, 30, 50), outline=LGRAY, width=2)
        d.rectangle([x + 90, 160, x + 98, 186], fill=GRAY)
        if kind == "board_cup":
            text(d, x + 8, 40, "카라바오컵 속보", GOLD)
            text(d, x + 8, 66, "찰튼전 5-1 승리!", WHITE)
            text(d, x + 8, 86, "(시즌 유일한 승리)", LGRAY)
            text(d, x + 8, 116, "→ 리버풀 1-3 탈락", RED)
        elif kind == "kane":
            d.rectangle([x + 2, 36, x + 188, 158], fill=(200, 30, 50))
            text(d, x + 8, 40, "한편, 뮌헨의 케인", WHITE)
            blit(img, chibi("kane"), x + 20, 70, 2)
            trophy(d, x + 110, 80)
            trophy(d, x + 150, 90)
            text(d, x + 82, 126, "트로피 수집 중", GOLD)
        elif kind == "son":
            d.rectangle([x + 2, 36, x + 188, 158], fill=(255, 180, 110))
            text(d, x + 8, 40, "한편, LA의 쏘니", NAVY, shadow=WHITE)
            blit(img, chibi("son", mood="smile"), x + 20, 70, 2)
            text(d, x + 80, 96, "행복 중 :)", NAVY, shadow=WHITE)
        else:
            d.rectangle([x + 2, 36, x + 188, 158], fill=WHITE)
            text(d, x + 16, 44, "레비 OUT", NAVY, shadow=None)
            d.line([(x + 12, 52), (x + 90, 52)], fill=RED, width=3)
            text(d, x + 16, 70, "(레비는 떠났다)", GRAY, shadow=None)
            text(d, x + 16, 100, "ENIC OUT!!", RED, F32, shadow=None)
            text(d, x + 16, 136, "구단주는 그대로", NAVY, shadow=None)

    def audio(self, m, t0):
        # 필드 테마 (에버튼전 슬로모션 구간은 느리고 낮게)
        play(m, t0, 21.0, STAGE, 190)
        m.seq(t0 + 21.0, 3.5, STAGE[0], 80, 2, "sq", 0.06, 0.5)
        m.seq(t0 + 21.0, 3.5, STAGE[1], 80, 2, "tri", 0.18)
        play(m, t0 + 24.5, 2.7, STAGE, 200, drums="k s k s")
        # 희망 테마
        play(m, t0 + self.STAIRS, self.TRAP - self.STAIRS, TITLE, 210, drums="k h s h k k s h")
        m.sfx(t0 + self.STAIRS, "itemget")
        m.sfx(t0 + self.TRAP, "scratch")
        m.notes(t0 + self.TRAP + 0.3, "C5:0.12 A4:0.12 C5:0.12 A4:0.12 C5:0.12 A4:0.3", vol=0.08, duty=0.5)
        m.sfx(t0 + self.FALL, "fall")
        # 지하 테마
        play(m, t0 + self.UNDER, self.dur - self.UNDER, UNDER, 140, drums="k . k s", duty=0.5)
        # 효과음
        for bt, k, _, _ in self.BUYS:
            m.sfx(t0 + bt - 0.2, "jump")
            m.sfx(t0 + bt, "coin")
            if k:
                m.notes(t0 + bt + 0.08, "C5:0.05 G5:0.05 C6:0.1", vol=0.06, duty=0.25)
        m.sfx(t0 + self.ROMERO_OUT, "fall")
        m.sfx(t0 + self.CAPTAIN, "heal")
        m.sfx(t0 + self.KITBLOCK, "itemget")
        m.sfx(t0 + 10.2, "select")
        m.sfx(t0 + 17.4, "select")
        m.sfx(t0 + 10.6, "buzz")
        m.sfx(t0 + 14.6, "caw")
        for tt in (18.0, 18.5, 19.0):
            m.sfx(t0 + tt, "bump")
        m.sfx(t0 + 19.6, "jump")
        m.sfx(t0 + 20.0, "heal")
        m.sfx(t0 + 21.2, "snore")
        m.sfx(t0 + 23.0, "heal")
        m.sfx(t0 + 24.6, "roar")
        for tt in self.hurt_times():
            m.sfx(t0 + tt, "damage")
        for tt in (28.8, 29.8):
            m.sfx(t0 + tt, "fanfare")
            m.add(t0 + tt + 0.1, noise(0.4, 0.2, 0.15, hold=3))
        for k in range(3):
            m.sfx(t0 + self.UNDER + 1.2 + k * 2.6, "sad")


# ------------------------------------------------------------------ 5. 엔딩 (9.8s)

class Ending(Scene):
    dur = 9.8
    fade_out = 0.5

    def draw(self, img, d, t):
        d.rectangle([0, 0, W, H], fill=BLACK)
        if t < 3.2:
            if t < 2.0:
                ctext(d, 12, "계속하시겠습니까?", RED, F32, shadow=DRED)
                ctext(d, 56, str(max(6, 9 - int(t / 0.3))), WHITE, F64, shadow=GRAY)
                if blink(t, 3):
                    ctext(d, 236, "동전을 넣으세요", GOLD)
            d.rectangle([392, 130, 432, 180], fill=(40, 40, 40), outline=LGRAY)
            d.rectangle([408, 136, 414, 172], fill=BLACK)
            if 1.3 <= t < 1.7:
                kk = (t - 1.3) / 0.4
                cy = -16 + 150 * kk * kk
                d.ellipse([401, cy, 421, cy + 20], fill=GOLD, outline=BLACK)
                text(d, 407, cy + 2, "£", BROWN, shadow=None)
                text(d, 428, cy, "ENIC", LGRAY)
            if t >= 1.7:
                text(d, 372, 190, "크레딧 1", WHITE)
            k = t - 2.0
            if k >= 0:
                jy = -int(50 * 4 * (k / 0.4) * (1 - k / 0.4)) if k < 0.4 else 0
                blit(img, chibi("dezerbi"), 222, 150 + jy, 2)
                ctext(d, 30, "부활!", GOLD, F32)
            else:
                blit(img, chibi("dezerbi", mood="x"), 222, 150, 2, flip_v=True)
        elif t < 5.4:
            k = t - 3.2
            d.rectangle([0, 0, W, H], fill=(120, 10, 20))
            ctext(d, 16, "다음 스테이지", GOLD)
            ctext(d, 38, "맨유 원정", WHITE, F32, shadow=DRED)
            ctext(d, 80, "10월 10일 · 올드 트래포드", LGRAY)
            dx, dy = 330, 120
            d.polygon([(dx, dy + 20), (dx + 6, dy - 6), (dx + 14, dy + 14)], fill=(250, 220, 120), outline=BLACK)
            d.polygon([(dx + 46, dy + 20), (dx + 40, dy - 6), (dx + 32, dy + 14)], fill=(250, 220, 120), outline=BLACK)
            d.ellipse([dx, dy + 6, dx + 46, dy + 52], fill=(220, 30, 30), outline=BLACK)
            d.rectangle([dx + 12, dy + 22, dx + 17, dy + 27], fill=YELLOW)
            d.rectangle([dx + 29, dy + 22, dx + 34, dy + 27], fill=YELLOW)
            d.line([(dx + 12, dy + 38), (dx + 34, dy + 38)], fill=BLACK, width=2)
            d.rectangle([dx + 6, dy + 52, dx + 40, dy + 110], fill=(220, 30, 30), outline=BLACK)
            d.line([(dx + 56, dy + 120), (dx + 60, dy)], fill=GOLD, width=3)
            blit(img, chibi("dezerbi", mood="shock"), 120, 140, 2)
            if k > 0.5:
                text(d, 104, 116, "꿀꺽...", WHITE)
            if k > 1.0:
                text(d, 40, 236, "데 제르비의 목숨", RED)
                for i in range(3):
                    col = RED if i == 0 else (90, 40, 50)
                    x = 180 + i * 26
                    d.polygon([(x, 240), (x + 10, 252), (x + 20, 240), (x + 15, 235), (x + 10, 240), (x + 5, 235)],
                              fill=col)
        elif t < 8.2:
            k = t - 5.4
            ctext(d, 90, reveal("사람을 죽이는 건...", k - 0.1), LGRAY)
            if k > 0.9:
                ctext(d, 120, reveal("희망이다.", k - 0.9), WHITE, F32)
            if k > 1.8:
                ctext(d, 180, reveal("그래도 다음 주에 또 본다.", k - 1.8), GOLD)
        else:
            k = t - 8.2
            draw_stars(d, t, 8, n=40, seed=3)
            ctext(d, 50, "가자, 토트넘!", GOLD, F64, shadow=NAVY2)
            walkers = [("dezerbi", None), ("vdv", "home"), ("fernandes", "away"), ("tonali", "home"),
                       ("gallagher", "away"), ("vanhecke", "home")]
            for i, (key, kit) in enumerate(walkers):
                blit(img, chibi(key, int(t * 6 + i) % 2, kit=kit), 60 + i * 60, 140, 2)
            ctext(d, 246, "※ 2026.09.24 기준 실제 결과 바탕의 풍자 패러디", GRAY)

    def audio(self, m, t0):
        for k in range(4):
            m.sfx(t0 + k * 0.3, "tick")
        m.sfx(t0 + 1.3, "coin")
        m.sfx(t0 + 2.0, "jump")
        m.notes(t0 + 2.1, "G5:0.08 C6:0.08 E6:0.08 G6:0.25", vol=0.08, duty=0.25)
        m.seq(t0 + 3.2, 2.2, "D4 . . D4 F4 . D4 . Ab4 . G4 . F4 . D4 .", 150, 2, "sq", 0.08, 0.5)
        m.seq(t0 + 3.2, 2.2, "D2 D2 D2 D2", 150, 1, "tri", 0.2)
        m.sfx(t0 + 3.7, "gulp")
        m.notes(t0 + 5.5, "A3:1.0 F3:1.0 E3:1.4", kind="tri", vol=0.2)
        m.notes(t0 + 5.5, "C5:1.0 A4:1.0 G#4:1.4", vol=0.05, duty=0.5)
        blips(m, t0 + 5.5, "사람을 죽이는 건...")
        blips(m, t0 + 7.2, "그래도 다음 주에 또 본다.")
        play(m, t0 + 8.2, 1.3, TITLE, 190)
        for n in ("C4", "E4", "G4", "C5"):
            m.notes(t0 + 9.5, f"{n}:0.3", vol=0.05)


# -------------------------------------------------------------------------- main

def build():
    return [Title(), SaveFile(), WorldCard(), World(), Ending()]


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
    wav_path = os.path.join(HERE, "_audio_hope.wav")
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
        sc.draw(img, d, lt)
        arr = np.asarray(img)
        if sc.fade_out and lt > sc.dur - sc.fade_out:
            k = (sc.dur - lt) / sc.fade_out
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
