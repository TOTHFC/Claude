#!/usr/bin/env python3
"""TOTTENHAM TOONS ─ Ep. 26/27 「강등권의 전설」

2026년 9월 토트넘의 현실을 미국 카툰(루니툰즈·패밀리가이 풍) 스타일로 풍자하는 애니메이션 생성기.
그래픽·음악·효과음을 모두 코드로 만든다.

    pip install skia-python numpy imageio-ffmpeg pillow   (+ apt: libegl1 libgl1)
    python3 make_toons.py             # -> tottenham_toons.mp4 (1280x720, 24fps)
"""
import math
import os
import random
import subprocess
import wave

import imageio_ffmpeg
import numpy as np
import skia

from cast import (Pose, cannon, devil, draw_face_only, draw_person, hammer, lion, magpie, rooster, toffee,
                  trophy_icon, tree, wallet, bee)
from toon import (AIA, FPS, GOLD, GRASS, H, INK, NAVY, RED, SKY, SR, TF_COMIC, TF_KR, TF_TITLE, WHITE, YELLOW,
                  W, Mixer, bubble, burst, caption, confetti, dust, ease, ease_out_back, fill, iris, mix,
                  motion_lines, oval, poly, pow_text, rings_bg, rrect, shape, smooth, speed_lines, squash,
                  stars_circle, stroke, tag, text, text_w, vhs, bounce)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tottenham_toons.mp4")


def rect(x0, y0, x1, y1):
    return skia.Rect.MakeLTRB(x0, y0, x1, y1)


def between(t, a, b):
    return a <= t < b


def prog(t, a, b):
    return max(0.0, min(1.0, (t - a) / (b - a)))


def chapter_label(cv, s):
    w = text_w(s, 26, TF_TITLE) + 40
    shape(cv, rrect(20, 18, 20 + w, 62, 12), RED, 4)
    text(cv, s, 20 + w / 2, 50, 26, WHITE, TF_TITLE, oc=None)


def previously(cv, t):
    shape(cv, rrect(20, 18, 380, 66, 10), (20, 20, 20), 0)
    text(cv, "PREVIOUSLY ON", 110, 54, 34, YELLOW, TF_COMIC, oc=None)
    text(cv, "TOTTENHAM...", 280, 54, 34, WHITE, TF_COMIC, oc=None)
    if int(t * 2) % 2 == 0:
        cv.drawCircle(360, 42, 8, fill(RED))


class Scene:
    dur = 1.0
    fade_in = 0.15
    fade_out = 0.15

    def draw(self, cv, t):
        pass

    def audio(self, m, t0):
        pass


# ------------------------------------------------------------------ 배경

def bg_lava(cv, t):
    cv.drawRect(rect(0, 0, W, H), fill((60, 12, 10)))
    for i in range(8):
        y = 420 + i * 40
        c = mix((120, 20, 10), (255, 120, 20), i / 8)
        p = skia.Path()
        p.moveTo(0, y)
        for x in range(0, W + 40, 40):
            p.lineTo(x, y + math.sin(x * 0.02 + t * 2 + i) * 10)
        p.lineTo(W, H)
        p.lineTo(0, H)
        p.close()
        cv.drawPath(p, fill(c))
    rng = random.Random(3)
    for _ in range(14):
        x, ph = rng.uniform(0, W), rng.uniform(0, 5)
        k = (t * 0.6 + ph) % 1
        shape(cv, oval(x, 640 - k * 200, 8 + 10 * k, 8 + 10 * k), (255, 170, 40), 3, a=int(255 * (1 - k)))
    for x in (60, 1220):
        for i in range(3):
            k = (t * 1.3 + i / 3) % 1
            shape(cv, smooth([(x - 30, 440), (x - 10 - 20 * k, 380 - 60 * k), (x, 320 - 90 * k),
                              (x + 14 + 20 * k, 380 - 60 * k), (x + 30, 440)]), (255, 150 - 60 * k, 30), 4)


def bg_elevator(cv, t, open_k, floor):
    bg_lava(cv, t)
    shape(cv, rect(380, 110, 900, 600) and rrect(380, 110, 900, 600, 6), (150, 150, 160), 6)
    shape(cv, rrect(420, 170, 860, 600, 4), (80, 80, 90), 5)
    # 내부
    cv.drawRect(rect(424, 174, 856, 598), fill((196, 186, 150)))
    for x in range(424, 856, 48):
        cv.drawLine(x, 174, x, 598, stroke((170, 160, 128), 3))
    cv.drawRect(rect(424, 560, 856, 598), fill((120, 100, 80)))
    # 층수 표시
    shape(cv, rrect(560, 118, 720, 164, 8), (20, 20, 20), 4)
    text(cv, f"{floor}F", 640, 156, 38, (255, 90, 60), TF_TITLE, oc=None)
    return open_k


def elevator_doors(cv, open_k):
    w = 216 * (1 - ease(open_k))
    for sgn, x0 in ((-1, 424), (1, 856)):
        if w < 1:
            continue
        r = rect(x0, 174, x0 + w, 598) if sgn < 0 else rect(x0 - w, 174, x0, 598)
        cv.drawRect(r, fill((178, 180, 190)))
        cv.drawRect(r, stroke(INK, 5))
        for k in range(4):
            yy = 220 + k * 100
            if sgn < 0:
                cv.drawLine(x0 + 14, yy, x0 + w - 14, yy, stroke((210, 210, 220), 3))
            else:
                cv.drawLine(x0 - w + 14, yy, x0 - 14, yy, stroke((210, 210, 220), 3))


def bg_office(cv, t):
    cv.drawRect(rect(0, 0, W, H), fill((236, 222, 190)))
    for x in range(0, W, 80):
        cv.drawRect(rect(x, 0, x + 40, 560), fill((228, 212, 178)))
    cv.drawRect(rect(0, 560, W, H), fill((150, 110, 80)))
    for x in range(0, W, 120):
        cv.drawLine(x, 560, x - 60, H, stroke((130, 94, 68), 4))
    shape(cv, rrect(860, 110, 1180, 330, 8), SKY, 6)
    cv.drawRect(rect(870, 250, 1170, 320), fill(GRASS))
    shape(cv, rrect(900, 170, 1140, 260, 30), WHITE, 4)
    text(cv, "N17", 1020, 232, 34, NAVY, TF_TITLE, oc=None)
    cv.drawLine(1020, 110, 1020, 330, stroke(INK, 5))


def days_sign(cv, n, x=120, y=110):
    shape(cv, rrect(x, y, x + 300, y + 170, 10), (250, 246, 230), 5)
    text(cv, "DAYS WITHOUT", x + 150, y + 42, 30, INK, TF_COMIC, oc=None)
    text(cv, "A SACKING:", x + 150, y + 74, 30, INK, TF_COMIC, oc=None)
    shape(cv, rrect(x + 90, y + 88, x + 210, y + 156, 8), (30, 30, 30), 3)
    text(cv, str(n), x + 150, y + 142, 52, (255, 80, 60) if n < 10 else (90, 255, 90), TF_TITLE, oc=None)


def bg_desert(cv, t, cliff_x=720):
    cv.drawRect(rect(0, 0, W, H), fill((255, 170, 90)))
    cv.drawRect(rect(0, 0, W, 220), fill((255, 140, 80)))
    cv.drawCircle(1080, 170, 70, fill((255, 230, 140)))
    for (x, w, h) in ((900, 160, 180), (1150, 200, 230), (1000, 120, 120)):
        shape(cv, poly([(x - w / 2, 430), (x - w / 2 + 20, 430 - h), (x + w / 2 - 20, 430 - h), (x + w / 2, 430)]),
              (200, 100, 60), 4)
    cv.drawRect(rect(cliff_x, 430, W, H), fill((150, 70, 40)))
    shape(cv, poly([(cliff_x + 30, 430), (W, 430), (W, H), (cliff_x + 140, H)]), (120, 56, 34), 0)
    shape(cv, poly([(0, 420), (cliff_x, 420), (cliff_x + 30, 470), (cliff_x - 10, 560), (cliff_x + 20, H), (0, H)]),
          (214, 130, 70), 5)
    cv.drawRect(rect(0, 420, cliff_x, 432), fill((190, 110, 60)))
    for x in (120, 360, 560):
        shape(cv, rrect(x - 10, 330, x + 10, 420, 8), (60, 150, 70), 4)
        shape(cv, rrect(x - 34, 350, x - 10, 364, 6), (60, 150, 70), 3)
        shape(cv, rrect(x - 34, 330, x - 22, 364, 6), (60, 150, 70), 3)
    # 표지판
    cv.drawLine(cliff_x - 40, 420, cliff_x - 40, 330, stroke(INK, 8))
    cv.drawLine(cliff_x - 40, 420, cliff_x - 40, 330, stroke((140, 90, 50), 4))
    shape(cv, rrect(cliff_x - 150, 290, cliff_x + 70, 336, 6), (240, 220, 170), 4)
    text(cv, "PREMIER LEAGUE", cliff_x - 40, 324, 28, NAVY, TF_COMIC, oc=None)
    shape(cv, rrect(cliff_x + 260, 600, cliff_x + 520, 650, 6), (240, 220, 170), 4)
    text(cv, "↓ CHAMPIONSHIP (2부)", cliff_x + 390, 634, 22, RED, TF_KR, oc=None)


def bg_mart(cv, t):
    cv.drawRect(rect(0, 0, W, H), fill((240, 244, 250)))
    shape(cv, rrect(330, 20, 950, 96, 12), (230, 40, 50), 5)
    text(cv, "TRANSFER MART", 640, 78, 56, YELLOW, TF_COMIC, ow=8)
    for row in range(2):
        y = 190 + row * 150
        cv.drawRect(rect(0, y, W, y + 14), fill((170, 170, 190)))
        cv.drawRect(rect(0, y, W, y + 14), stroke(INK, 3))
    cv.drawRect(rect(0, 560, W, H), fill((210, 214, 224)))
    for x in range(0, W, 90):
        cv.drawLine(x, 560, x, H, stroke((190, 194, 206), 3))
    tag(cv, "SUMMER SALE?!", 150, 140, 30, YELLOW, rot=-8)
    tag(cv, "NO REFUNDS", 1130, 150, 26, (255, 150, 150), rot=6)


def bg_pitch(cv, t, goal_side=1):
    cv.drawRect(rect(0, 0, W, H), fill((40, 60, 90)))
    for i in range(24):
        x = i * 60 - (t * 10 % 60)
        cv.drawCircle(x, 120 + (i % 3) * 12, 14, fill((80, 90, 120)))
    cv.drawRect(rect(0, 150, W, 200), fill((30, 30, 50)))
    for i in range(10):
        cv.drawRect(rect(0, 200 + i * 52, W, 226 + i * 52), fill((70, 170, 70)))
        cv.drawRect(rect(0, 226 + i * 52, W, 252 + i * 52), fill((60, 155, 60)))
    cv.drawLine(0, 214, W, 214, stroke(WHITE, 4))
    gx = 1150 if goal_side > 0 else 130
    shape(cv, rrect(gx - 50, 330, gx + 50, 560, 4), None, 0)
    cv.drawRect(rect(gx - 60, 330, gx + 60, 540), stroke(WHITE, 10))
    for k in range(6):
        cv.drawLine(gx - 60 + k * 24, 330, gx - 60 + k * 24, 540, stroke((220, 220, 220), 2))
        cv.drawLine(gx - 60, 330 + k * 35, gx + 60, 330 + k * 35, stroke((220, 220, 220), 2))


def scorebug(cv, home, hs, away, as_, minute=None):
    shape(cv, rrect(20, 18, 470, 70, 10), (20, 22, 40), 3)
    text(cv, home, 120, 56, 30, WHITE, TF_KR, oc=None)
    shape(cv, rrect(200, 24, 290, 64, 6), WHITE, 0)
    text(cv, f"{hs} - {as_}", 245, 56, 32, INK, TF_TITLE, oc=None)
    text(cv, away, 380, 56, 30, WHITE, TF_KR, oc=None)
    if minute:
        shape(cv, rrect(480, 24, 560, 64, 6), RED, 0)
        text(cv, minute, 520, 54, 26, WHITE, TF_TITLE, oc=None)


def reaction(cv, t, mood, **kw):
    """오른쪽 아래 데 제르비 리액션 인셋."""
    shape(cv, oval(1160, 590, 100, 100), (250, 240, 220), 6)
    cv.save()
    cv.clipPath(oval(1160, 590, 97, 97), doAntiAlias=True)
    draw_face_only(cv, "dezerbi", 1160, 620, 1.0, Pose(t=t, mood=mood, **kw))
    cv.restore()
    cv.drawPath(oval(1160, 590, 100, 100), stroke(INK, 6))
    tag(cv, "DE ZERBI CAM", 1160, 480, 20, YELLOW, rot=-4)


def ball(cv, x, y, r=16, rot=0.0):
    shape(cv, oval(x, y, r, r), WHITE, 4)
    cv.save()
    cv.translate(x, y)
    cv.rotate(rot)
    cv.drawPath(poly([(-r * 0.35, -r * 0.3), (r * 0.35, -r * 0.3), (r * 0.5, r * 0.2), (0, r * 0.5),
                      (-r * 0.5, r * 0.2)]), fill(INK))
    cv.restore()


def heart(cv, x, y, s, full=True):
    p = skia.Path()
    p.moveTo(x, y + 12 * s)
    p.cubicTo(x - 30 * s, y - 8 * s, x - 14 * s, y - 30 * s, x, y - 14 * s)
    p.cubicTo(x + 14 * s, y - 30 * s, x + 30 * s, y - 8 * s, x, y + 12 * s)
    shape(cv, p, RED if full else (80, 70, 80), 5)


# ------------------------------------------------------------------ S0 엘리베이터 (현재)

class ElevatorOpen(Scene):
    dur = 8.2
    fade_in = 0.0
    FREEZE = 4.7

    def draw(self, cv, t):
        tt = min(t, self.FREEZE)
        if t > 7.0:
            tt = self.FREEZE - (t - 7.0) * 3  # 되감기
        floor = 17 + min(3, int(max(0, tt - 0.4) / 0.7))
        ok = prog(tt, 3.0, 3.6)
        bg_elevator(cv, tt, ok, floor)
        mood = "happy" if tt < 4.0 else "shock"
        pz = Pose(t=tt, mood=mood, arms="hold" if tt < 4.0 else "face", jaw=0.9 if tt >= 4.0 else 0,
                  eye_pop=1.35 if tt >= 4.0 else 1.0, look=(0.4, 0.3) if tt < 3.8 else (0, 0.4), sweat=3 if tt > 4.2 else 0)
        draw_person(cv, "dezerbi", 580, 590, 1.12, pz)
        rooster(cv, 760, 590, 0.95, tt, mood="shock" if tt >= 4.0 else "happy", look=(0, 0.5), jump=10 if tt >= 4.0 else 0)
        if tt < 3.4:
            for i in range(3):
                k = (tt * 0.8 + i / 3) % 1
                text(cv, "♪", 520 + i * 90 + 20 * math.sin(tt * 3 + i), 300 - 90 * k, 40, (80, 80, 90), oc=None,
                     a=int(255 * (1 - k)))
        elevator_doors(cv, ok)
        shape(cv, rrect(360, 36, 920, 100, 12), (30, 10, 10), 5)
        text(cv, "RELEGATION ZONE · 강등권", 640, 84, 40, (255, 120, 60), TF_TITLE, oc=None)
        if t >= self.FREEZE and t < 7.0:
            cv.drawRect(rect(0, 0, W, H), fill((255, 220, 150), 70))
            text(cv, "*record scratch*", 260, 160, 44, WHITE, TF_COMIC, ow=8)
            text(cv, "*freeze frame*", 1030, 160, 44, WHITE, TF_COMIC, ow=8)
            caption(cv, "Yep, that's us. 현재 리그 20위 (꼴찌).", 660, 40, YELLOW)
            if t > 5.8:
                caption(cv, "어쩌다 여기까지 왔냐고? Let me explain...", 600, 34)
        if t >= 7.0:
            vhs(cv, t, 160)
            cv.drawRect(rect(0, 0, W, H), fill((40, 40, 120), 60))
            text(cv, "◀◀ REWIND", 180, 90, 56, WHITE, TF_COMIC, ow=8)

    def audio(self, m, t0):
        m.seq(t0, 4.6, "F4+A4+C5 - - . E4+G4+C5 - - . D4+F4+A4 - - . E4+G4+Bb4 - - .", 100, 2, "organ", 0.07)
        m.seq(t0, 4.6, "F2 . C3 . C2 . G2 . D2 . A2 . C2 . G2 .", 100, 2, "bass", 0.15)
        m.seq(t0, 4.6, "h . b h h . b .", 100, 2, "drum")
        for k in range(3):
            m.sfx(t0 + 0.4 + (k + 1) * 0.7, "tick")
        m.sfx(t0 + 3.0, "elev_ding")
        m.sfx(t0 + 4.0, "gasp")
        m.sfx(t0 + self.FREEZE, "scratch")
        m.sfx(t0 + 7.0, "rewind")


# ------------------------------------------------------------------ S1 타이틀

class Title(Scene):
    dur = 5.6

    def draw(self, cv, t):
        rings_bg(cv, t)
        k = ease_out_back(prog(t, 0.2, 0.8))
        cv.save()
        cv.translate(640, 250)
        wob = 1 + math.sin(t * 6) * 0.02
        cv.scale(k * wob, k / wob)
        cv.rotate(-4 + math.sin(t * 3) * 2)
        shape(cv, rrect(-470, -110, 470, 60, 40), (250, 250, 255), 8)
        text(cv, "TOTTENHAM TOONS", 0, 30, 118, YELLOW, TF_COMIC, ow=14)
        cv.restore()
        if t > 0.9:
            k2 = ease_out_back(prog(t, 0.9, 1.3))
            cv.save()
            cv.translate(640, 380)
            cv.scale(k2, k2)
            text(cv, "토트넘 툰즈", 0, 0, 64, WHITE, TF_TITLE, ow=10)
            cv.restore()
        if t > 1.5:
            k3 = ease(prog(t, 1.5, 1.9))
            cv.save()
            cv.translate(640 + (1 - k3) * 900, 470)
            shape(cv, poly([(-330, -40), (330, -40), (300, 0), (330, 40), (-330, 40), (-300, 0)]), RED, 6)
            text(cv, "Ep. 26/27 「강등권의 전설」", 0, 16, 44, WHITE, TF_KR, oc=None)
            cv.restore()
        if t > 2.2:
            j = bounce(prog(t, 2.2, 2.8))
            rooster(cv, 1060, 720 - 170 * j, 1.0, t, mood="happy", talk=t > 2.6)
            if t > 2.7:
                bubble(cv, 920, 520, ["COYS!"], 44, tail=(1020, 570), shout=True)

    def audio(self, m, t0):
        m.sfx(t0 + 0.2, "zoom")
        m.sfx(t0 + 0.6, "boing")
        mel = "C5 E5 G5 A5 G5 E5 C5 D5 E5 - D5 C5 A4 - G4 - C5 E5 G5 A5 G5 E5 C5 D5 E5 - G5 - C6 - - ."
        m.seq(t0 + 0.8, 4.6, mel, 168, 2, "clar", 0.12)
        m.seq(t0 + 0.8, 4.6, "C3 G2 C3 G2 F2 C3 F2 C3 C3 G2 C3 G2 G2 D3 G2 B2", 168, 2, "tuba", 0.16)
        m.seq(t0 + 0.8, 4.6, "k b s b k b s b", 168, 2, "drum")
        m.sfx(t0 + 1.5, "whoosh")
        m.sfx(t0 + 2.4, "boing")


# ------------------------------------------------------------------ S2 이전 줄거리

class Previously(Scene):
    dur = 11.2

    def draw(self, cv, t):
        if t < 5.6:
            cv.drawRect(rect(0, 0, W, H), fill((20, 24, 60)))
            for i in range(9):
                x = i * 160 + 40
                cv.drawPath(poly([(x - 20, 0), (x + 20, 0), (x + 120, 560), (x - 120, 560)]), fill((255, 255, 200), 25))
            cv.drawRect(rect(0, 560, W, H), fill(GRASS))
            if t < 3.4:
                confetti(cv, t, 3)
                pz = Pose(t=t, mood="grin", arms="up", talk=True)
                draw_person(cv, "ange", 640, 660, 1.1, pz)
                trophy_icon(cv, 640, 250 + math.sin(t * 14) * 4, 1.3)
                bubble(cv, 330, 220, ["I always win things", "in my second year, mate!"], 32, tail=(560, 330))
                caption(cv, "2025.05 유로파리그 우승! 17년 만의 트로피", 690)
            else:
                k = prog(t, 3.5, 4.3)
                bx = -300 + 900 * ease(prog(t, 3.4, 3.7))
                if t < 3.9:
                    draw_person(cv, "ange", 640, 660, 1.1, Pose(t=t, mood="happy", arms="up"))
                    trophy_icon(cv, 640, 250, 1.3)
                else:
                    kk = prog(t, 3.9, 4.8)
                    draw_person(cv, "ange", 640 + 700 * kk, 660 - 900 * kk + 300 * kk * kk, 1.1 * (1 - kk * 0.8),
                                Pose(t=t, mood="shock", arms="flail", tilt=kk * 720))
                    trophy_icon(cv, 640, 250 + 400 * kk * kk, 1.3)
                    if t > 4.8:
                        burst(cv, 1180, 70, 6, 22 * (1 - prog(t, 4.8, 5.4)), 4, WHITE, ow=0)
                # 거대한 장화
                cv.save()
                cv.translate(bx, 520)
                cv.rotate(-20 * ease(prog(t, 3.7, 3.9)))
                shape(cv, rrect(-80, -360, 40, 0, 20), (110, 70, 40), 6)
                shape(cv, smooth([(-90, -40), (160, -60), (220, 0), (160, 50), (-90, 40)]), (110, 70, 40), 6)
                text(cv, "BOARD", -20, -180, 30, YELLOW, TF_COMIC, ow=5)
                cv.restore()
                if 3.8 < t < 4.6:
                    pow_text(cv, "KICK!", 820, 330, prog(t, 3.8, 4.4), YELLOW, RED, 110)
                caption(cv, "...그리고 16일 뒤, 경질.", 690)
        elif t < 8.4:
            k = t - 5.6
            cv.drawRect(rect(0, 0, W, H), fill((255, 150, 120)))
            cv.drawRect(rect(0, 0, W, 300), fill((255, 110, 130)))
            cv.drawCircle(640, 430, 160, fill((255, 210, 120)))
            for x in (160, 1100):
                cv.drawLine(x, 620, x + 30, 330, stroke((90, 60, 40), 22))
                for a in range(6):
                    ang = math.radians(200 + a * 28)
                    p = smooth([(x + 30, 330), (x + 30 + math.cos(ang) * 90, 330 + math.sin(ang) * 60),
                                (x + 30 + math.cos(ang) * 150, 360 + math.sin(ang) * 30)], closed=False)
                    cv.drawPath(p, stroke((40, 140, 60), 18))
            cv.drawRect(rect(0, 600, W, H), fill((240, 200, 140)))
            px = -200 + k * 700
            cv.save()
            cv.translate(px, 170)
            shape(cv, rrect(-120, -20, 120, 20, 20), WHITE, 5)
            shape(cv, poly([(-20, 0), (40, -70), (60, -70), (30, 0)]), (200, 200, 210), 4)
            text(cv, "TO LA", 20, 12, 22, NAVY, TF_COMIC, oc=None)
            cv.restore()
            draw_person(cv, "son", 640, 640, 1.1, Pose(t=t, mood="happy", arms="wave"))
            shape(cv, rrect(740, 520, 840, 640, 10), (200, 60, 60), 5)
            bubble(cv, 900, 250, ["See you, Spurs!", "안녕~!"], 34, tail=(700, 360))
            caption(cv, "2025.08 손흥민, LAFC로 이적", 690)
        else:
            k = t - 8.4
            bg_office(cv, t)
            shape(cv, rrect(160, 150, 360, 560, 6), (120, 80, 50), 6)
            text(cv, "CHAIRMAN", 260, 200, 28, WHITE, TF_COMIC, oc=INK)
            lx = 260 + k * 260
            draw_person(cv, "levy", lx, 640, 1.0, Pose(t=t, mood="neutral", arms="hold", legs="walk", phase=t * 8))
            shape(cv, rrect(lx - 60, 420, lx + 60, 500, 6), (200, 160, 110), 5)
            text(cv, "짐", lx, 474, 30, INK, oc=None)
            for i in range(5):
                fx = 850 + i * 80
                jump = abs(math.sin(t * 8 + i)) * 20
                rooster(cv, fx, 700 - jump, 0.45, t + i)
            pow_text(cv, "LEVY OUT!!", 1000, 260, prog(t, 8.6, 9.0), YELLOW, NAVY, 70, rot=6)
            if t < 10.0:
                caption(cv, "2025.09 레비 회장 퇴장. 이제 다 잘 풀리겠지?", 690)
            else:
                caption(cv, "...라고 생각했다.", 690, 44, YELLOW)
        previously(cv, t)

    def audio(self, m, t0):
        m.sfx(t0 + 0.1, "fanfare")
        m.sfx(t0 + 0.3, "cheer")
        m.seq(t0 + 0.4, 3.0, "C5 E5 G5 C6 G5 E5 C5 E5", 150, 2, "xylo", 0.1)
        m.sfx(t0 + 3.4, "whoosh")
        m.sfx(t0 + 3.85, "pow")
        m.sfx(t0 + 4.0, "slide_up")
        m.sfx(t0 + 4.8, "twinkle")
        m.seq(t0 + 5.6, 2.8, "G4 C5 E5 G5 E5 C5 D5 G4", 120, 2, "pluck", 0.12)
        m.sfx(t0 + 5.7, "plane")
        m.seq(t0 + 8.4, 1.6, "C5 D5 E5 G5", 120, 2, "clar", 0.1)
        m.sfx(t0 + 8.6, "cheer")
        m.sfx(t0 + 10.0, "sad_trombone")


# ------------------------------------------------------------------ S3 감독 회전문 (2025-26)

class Carousel(Scene):
    dur = 18.8

    def days(self, t):
        if t < 5.2:
            return int(min(243, t / 5.0 * 243))
        if t < 10.6:
            return int(max(0, (t - 6.4)) / 4.0 * 44)
        if t < 12.4:
            return 0
        return int((t - 12.4) * 12)

    def draw(self, cv, t):
        bg_office(cv, t)
        days_sign(cv, self.days(t))
        # TV
        shape(cv, rrect(470, 120, 790, 330, 12), (40, 40, 50), 6)
        cv.drawRect(rect(490, 138, 770, 312), fill((20, 40, 70)))
        if 2.6 <= t < 5.2:
            n = min(8, 1 + int((t - 2.6) / 0.3))
            text(cv, "리그 무승", 630, 200, 34, WHITE, oc=None)
            text(cv, f"{n}경기", 630, 270, 62, (255, 90, 80), TF_TITLE, oc=None)
        elif 8.0 <= t < 10.6:
            tree(cv, 690, 310, 0.55, t)
            text(cv, "토트넘 0-3", 560, 190, 30, WHITE, oc=None)
            text(cv, "포레스트", 560, 230, 30, WHITE, oc=None)
        elif t >= 15.4:
            text(cv, "강등 위기!!", 630, 250, 50, RED if int(t * 4) % 2 else YELLOW, TF_TITLE, oc=None)
        else:
            text(cv, "SPURS TV", 630, 245, 40, (120, 140, 200), TF_COMIC, oc=None)
        # 책상
        trap = between(t, 5.0, 6.4)
        shape(cv, rrect(820, 450, 1180, 600, 8), (130, 84, 50), 6)
        shape(cv, rrect(900, 420, 1100, 460, 6), (240, 220, 170), 4)
        text(cv, "HEAD COACH", 1000, 452, 26, NAVY, TF_COMIC, oc=None)
        if trap:
            cv.drawRect(rect(520, 600, 760, 640), fill((20, 12, 8)))
        # 의자
        chair_fire = t >= 13.6
        shape(cv, rrect(1000, 470, 1110, 560, 10), (70, 70, 90), 5)
        if chair_fire:
            for i in range(6):
                fx = 1010 + i * 18
                h = 40 + 20 * math.sin(t * 20 + i * 1.7)
                shape(cv, smooth([(fx - 12, 480), (fx, 480 - h), (fx + 12, 480)]), (255, 120 + i * 15, 30), 3)
            tag(cv, "HOT SEAT", 1055, 600, 26, (255, 120, 60), rot=-6)
        # 프랭크
        if t < 6.4:
            if t < 2.2:
                x = 100 + (t / 2.2) * 540
                pz = Pose(t=t, mood="grin", arms="down", legs="walk", phase=t * 9, talk=t > 1.2)
            else:
                x = 640
                mood = "grin" if t < 3.2 else ("worried" if t < 4.4 else "shock")
                pz = Pose(t=t, mood=mood, arms="wave" if t < 3.2 else ("chin" if t < 4.4 else "face"),
                          sweat=0 if t < 3.2 else 3, eye_pop=1.4 if t > 4.4 else 1.0, jaw=0.7 if t > 5.0 else 0)
            y = 620
            if t >= 5.4:
                y += 1400 * (t - 5.4) ** 2
            if y < 900:
                cv.save()
                cv.clipRect(rect(0, 0, W, 610 if t >= 5.4 else H))
                draw_person(cv, "frank", x, y, 1.0, pz)
                cv.restore()
            if 1.0 < t < 2.6:
                bubble(cv, 420, 300, ["Hej! 안녕하세요~!"], 34, tail=(560, 360))
            if 0.3 < t < 2.4:
                caption(cv, "2025.06 토마스 프랭크 부임 (from 브렌트포드)", 690)
            if 2.6 < t < 5.0:
                caption(cv, "2026년 들어 리그 승리 실종...", 690)
        if 5.3 < t < 6.6:
            pow_text(cv, "SACKED!", 330, 470, prog(t, 5.3, 5.8), WHITE, RED, 100)
        # 투도르
        if 6.4 <= t < 12.2:
            if t < 6.9:
                y = -200 + 820 * ease(prog(t, 6.4, 6.9))
            else:
                y = 620
            x = 640
            sx, sy = squash(6.9, t, 0.3)
            mood = "angry" if t < 8.0 else ("angry" if t < 10.4 else "shock")
            pz = Pose(t=t, mood=mood, arms="hips" if t < 10.4 else "flail", sx=sx, sy=sy, steam=8.6 < t < 10.4,
                      eye_pop=1.3 if t >= 10.4 else 1.0)
            if t >= 10.4:
                k = t - 10.75
                if k > 0:
                    x -= 2600 * k * k + 600 * k
            dust(cv, 640, 624, prog(t, 6.9, 7.5))
            draw_person(cv, "tudor", x, y, 1.0, pz)
            if 10.4 <= t < 11.3:
                hx = -400 + (x - 40 + 400) * ease(prog(t, 10.4, 10.75)) if t < 10.75 else x - 40
                p = skia.Path()
                p.moveTo(-50, 330)
                p.lineTo(hx, 330)
                p.arcTo(rect(hx - 30, 330, hx + 50, 410), 270, 180, False)
                cv.drawPath(p, stroke(INK, 22))
                cv.drawPath(p, stroke((190, 140, 70), 14))
            if 7.0 < t < 8.2:
                bubble(cv, 900, 300, ["......"], 40, tail=(700, 380))
            if 6.6 < t < 8.0:
                caption(cv, "이고르 투도르 (임시 감독)", 690)
            if 8.0 < t < 10.4:
                caption(cv, "부임 44일 만에...", 690)
                for i in range(6):
                    k = (t * 3 + i / 6) % 1
                    cv.save()
                    cv.translate(250 + i * 30 + 300 * k, 330 - 200 * k)
                    cv.rotate(k * 360)
                    shape(cv, rrect(-30, -24, 30, 24, 3), WHITE, 3)
                    text(cv, f"{int((t - 8) * 18 + i) % 44 + 1}", 0, 12, 26, RED, TF_TITLE, oc=None)
                    cv.restore()
            if 10.5 < t < 11.8:
                pow_text(cv, "44 DAYS!", 900, 470, prog(t, 10.5, 11.0), YELLOW, RED, 90)
        # 데 제르비
        if t >= 12.4:
            if t < 13.6:
                x = 100 + prog(t, 12.4, 13.4) * 850
                y = 620
                pz = Pose(t=t, mood="grin", legs="walk", phase=t * 9, arms="down", talk=True)
            elif t < 14.0:
                x, y = 1055, 590
                pz = Pose(t=t, mood="happy", legs="sit", arms="down")
            else:
                k = t - 14.0
                x = 1055 - 420 * min(1, k)
                y = 590 - 500 * math.sin(min(k, 1.2) / 1.2 * math.pi)
                pz = Pose(t=t, mood="shock", arms="butt", legs="jump", eye_pop=1.5, jaw=1.0, tilt=-15)
                if k > 1.2:
                    x, y = 635, 620 + 0
                    sx, sy = squash(15.2, t, 0.3)
                    pz = Pose(t=t, mood="worried", arms="butt", sweat=3, sx=sx, sy=sy)
                if k < 1.2:
                    for i in range(5):
                        shape(cv, oval(x + 20 + i * 10, y - 60 + i * 30, 16 + i * 4, 14 + i * 4), (180, 180, 190), 3,
                              a=200 - i * 30)
            draw_person(cv, "dezerbi", x, y, 1.0, pz)
            if 12.6 < t < 13.8:
                bubble(cv, 500, 300, ["Andiamo! 가자!"], 34, tail=(x + 30, 360))
            if 14.0 < t < 15.2:
                pow_text(cv, "MAMMA MIA!!", 330, 470, prog(t, 14.0, 14.4), YELLOW, RED, 80)
            if 12.6 < t < 15.4:
                caption(cv, "시즌 3번째 감독, 로베르토 데 제르비", 690)
        if t >= 15.4:
            for i, s in enumerate(["감독 3명", "리그 15경기 연속 무승", "구단 최초 6연패"]):
                if t > 15.5 + i * 0.6:
                    k = ease_out_back(prog(t, 15.5 + i * 0.6, 15.9 + i * 0.6))
                    cv.save()
                    cv.translate(260 + i * 380, 700 - 50)
                    cv.scale(k, k)
                    tag(cv, s, 0, 0, 34, YELLOW, rot=[-6, 3, -3][i])
                    cv.restore()
        chapter_label(cv, "CHAPTER 1 · 지난 시즌 (2025-26)")

    def audio(self, m, t0):
        sneak = "E3 . G3 . A3 . Bb3 A3 G3 . E3 . D3 . E3 . E3 . G3 . A3 . C4 B3 Bb3 . A3 . G3 . E3 ."
        m.seq(t0, 5.0, sneak, 132, 2, "pluck", 0.14)
        m.seq(t0, 5.0, "E2 . . . B1 . . . E2 . . . B1 . . .", 132, 2, "tuba", 0.14)
        m.seq(t0, 5.0, "k . w . k k w .", 132, 2, "drum")
        m.sfx(t0 + 1.2, "blip")
        for k in range(8):
            m.sfx(t0 + 2.6 + k * 0.3, "tick")
        m.sfx(t0 + 4.4, "gasp")
        m.sfx(t0 + 5.0, "trapdoor")
        m.sfx(t0 + 5.3, "fall_long")
        m.sfx(t0 + 5.35, "stamp")
        m.sfx(t0 + 6.4, "slide_down")
        m.sfx(t0 + 6.9, "thud")
        m.seq(t0 + 7.2, 3.2, "A2 . A2 . Bb2 . A2 . A2 . A2 . C3 . Bb2 .", 140, 2, "tuba", 0.16)
        m.seq(t0 + 7.2, 3.2, "k s k s", 140, 2, "drum")
        m.sfx(t0 + 8.6, "sizzle")
        m.sfx(t0 + 10.4, "hook")
        m.sfx(t0 + 10.75, "whoosh")
        m.sfx(t0 + 10.8, "yelp")
        m.sfx(t0 + 10.5, "stamp")
        m.seq(t0 + 12.4, 1.6, "C4 E4 G4 C5 G4 E4 C4 G3", 150, 2, "clar", 0.1)
        m.sfx(t0 + 13.6, "sizzle")
        m.sfx(t0 + 14.0, "slide_up")
        m.sfx(t0 + 14.05, "yelp")
        m.sfx(t0 + 15.2, "thud")
        for i in range(3):
            m.sfx(t0 + 15.5 + i * 0.6, "pop")
        m.seq(t0 + 15.5, 3.2, "E4 . E4 . F4 . F#4 . G4 - - .", 180, 2, "brass", 0.1)
        m.seq(t0 + 15.5, 3.2, "k k s .", 180, 2, "drum")


# ------------------------------------------------------------------ S4 절벽 최종전

class Cliff(Scene):
    dur = 17.4
    EDGE = 720

    def draw(self, cv, t):
        if t < 11.6:
            shake = (math.sin(t * 90) * 6) if 4.9 < t < 5.2 else 0
            cv.save()
            cv.translate(shake, 0)
            bg_desert(cv, t, self.EDGE)
            # 데 제르비 + 수탉
            if t < 2.8:
                x = -120 + t / 2.8 * 960
                y = 420
                pz = Pose(t=t, mood="angry", legs="run", arms="run", phase=t * 22, tilt=8)
                hx = x - 170
            elif t < 4.9:
                x, y = 840, 420
                look = (0, 1) if t < 3.6 else (1, 0)
                pz = Pose(t=t, mood="worried" if t < 3.6 else "shock", legs="dangle" if t > 3.2 else "run",
                          arms="flail" if t < 3.2 else "down", phase=t * 22, look=look, sweat=2 if t > 3.6 else 0,
                          eye_pop=1.3 if t > 3.6 else 1.0)
                hx = 680
            else:
                k = prog(t, 4.9, 5.6)
                x = 840 - 300 * ease(k)
                y = 420 - 240 * math.sin(k * math.pi)
                pz = Pose(t=t, mood="dizzy", legs="jump", arms="flail", tilt=-360 * ease(k))
                if t > 5.6:
                    x, y = 540, 420
                    sx, sy = squash(5.6, t, 0.35)
                    celebrate = t > 8.8
                    pz = Pose(t=t, mood="grin" if celebrate else "dizzy", arms="up" if celebrate else "down",
                              sx=sx, sy=sy, legs="jump" if celebrate and int(t * 4) % 2 else "stand")
                hx = 680
            draw_person(cv, "dezerbi", x, y, 0.72, pz)
            if t > 5.6 and t < 8.8:
                stars_circle(cv, 540, 200, t, 60, 14)
            # 웨스트햄 망치
            if t < 2.8:
                hammer(cv, hx, 420, 0.9, t)
            elif t < 6.2:
                hammer(cv, 700, 420 if t < 3.0 else 420, 0.9, t, "happy" if t < 3.6 else "shock", legs=True)
                if 3.4 < t < 6.2:
                    shape(cv, rrect(620, 190, 780, 240, 6), (240, 230, 200), 4)
                    text(cv, "uh-oh", 700, 228, 32, INK, TF_COMIC, oc=None)
            else:
                k = t - 6.2
                sc = max(0.08, 0.9 * (1 - k / 1.6))
                yy = 420 + 700 * min(1, k / 1.6) - 40
                if k < 1.6:
                    hammer(cv, 700 + 40 * k, yy, sc, t, "shock", legs=False)
                    if k < 1.1:
                        shape(cv, rrect(700 + 40 * k - 50 * sc / 0.9, yy - 190 * sc, 700 + 40 * k + 50 * sc / 0.9,
                                        yy - 150 * sc, 4), (240, 230, 200), 3)
                        text(cv, "HELP", 700 + 40 * k, yy - 158 * sc, max(8, 30 * sc / 0.9), RED, TF_COMIC, oc=None)
                else:
                    dust(cv, 820, 690, prog(t, 7.8, 8.8), 5)
            if 2.8 < t < 4.9:
                rooster(cv, 950, 400 if t > 3.2 else 420, 0.55, t, mood="shock" if t > 3.6 else "happy", look=(0, 1))
            elif t >= 4.9:
                rooster(cv, 620 if t > 5.6 else 950 - 330 * prog(t, 4.9, 5.6), 420, 0.55, t,
                        mood="happy" if t > 8.8 else "shock", jump=abs(math.sin(t * 8)) * 30 if t > 8.8 else 0)
            if 2.6 < t < 3.2:
                motion_lines(cv, 760, 300, 200, -1, 6, 160)
            # 공
            if 4.3 < t < 5.0:
                k = prog(t, 4.3, 4.95)
                ball(cv, 1400 - 560 * k, 150 + 120 * k, 26, t * 900)
                text(cv, "팔리냐 1-0", 1400 - 560 * k, 110 + 120 * k, 26, YELLOW, oc=INK)
            if 4.9 < t < 6.0:
                pow_text(cv, "BONK!", 780, 180, prog(t, 4.9, 5.3), YELLOW, RED, 100)
            if t > 8.8:
                confetti(cv, t, 7, 60)
                pow_text(cv, "SURVIVED!!", 900, 170, prog(t, 8.8, 9.3), YELLOW, NAVY, 90, rot=-4)
            cv.restore()
            if t < 4.9:
                caption(cv, "2026.05.24 최종전 vs 에버튼 ─ 지면 강등!", 690)
            elif t < 8.8:
                caption(cv, "팔리냐 1-0 결승골! 대신 웨스트햄이 추락...", 690)
            else:
                caption(cv, "17위 · 승점 41로 잔류! (2시즌 연속 17위)", 690, sub="세계 9위 부자 구단의 목표: 잔류")
        else:
            k = t - 11.6
            cv.drawRect(rect(0, 0, W, H), fill((200, 180, 220)))
            cv.drawRect(rect(0, 520, W, H), fill((130, 90, 70)))
            shape(cv, rrect(330, 90, 950, 470, 20), (40, 40, 50), 8)
            tv = rrect(360, 116, 920, 444, 10)
            cv.save()
            cv.clipPath(tv, doAntiAlias=True)
            if t < 16.0:
                cv.drawRect(rect(360, 116, 920, 444), fill((200, 30, 40)))
                confetti(cv, t, 9, 50)
                cannon(cv, 640, 420, 1.0, t)
                text(cv, "ARSENAL: CHAMPIONS 2025-26", 640, 170, 34, YELLOW, TF_COMIC, ow=6)
            else:
                cv.drawRect(rect(360, 116, 920, 444), fill((20, 20, 20)))
                rng = random.Random(int(t * 24))
                for _ in range(300):
                    x, y = rng.uniform(360, 920), rng.uniform(116, 444)
                    cv.drawRect(rect(x, y, x + 4, y + 4), fill((200, 200, 200)))
                p = poly([(560, 150), (640, 260), (600, 270), (700, 420)], closed=False)
                cv.drawPath(p, stroke(WHITE, 6))
            cv.restore()
            shape(cv, rrect(160, 480, 1120, 640, 30), (90, 110, 170), 6)
            twitch = (math.sin(t * 40) * 4) if t > 13.0 else 0
            mood = "happy" if t < 12.6 else ("angry" if t < 15.6 else "cry")
            rooster(cv, 640 + twitch, 600, 1.1, t, mood=mood, look=(0, -1))
            if 15.5 < t < 16.1:
                kk = prog(t, 15.5, 16.0)
                cv.save()
                cv.translate(700 - 60 * kk, 440 - 250 * kk + 200 * kk * kk)
                cv.rotate(kk * 600)
                shape(cv, rrect(-30, -12, 30, 12, 6), (40, 40, 40), 3)
                cv.restore()
            if t > 16.0:
                pow_text(cv, "CRASH!", 640, 300, prog(t, 16.0, 16.4), WHITE, RED, 100)
            caption(cv, "Meanwhile... 같은 날, 북런던 라이벌 아스날은 우승", 690)
        chapter_label(cv, "CHAPTER 1 · 지난 시즌 (2025-26)")

    def audio(self, m, t0):
        chase = "A4 A4 C5 A4 E5 A4 C5 A4 G4 G4 B4 G4 D5 G4 B4 G4 F4 F4 A4 F4 C5 F4 A4 F4 E4 G#4 B4 E5 D5 C5 B4 G#4"
        m.seq(t0, 2.9, chase, 176, 4, "clar", 0.1)
        m.seq(t0, 2.9, "A2 E2 A2 E2 G2 D2 G2 D2 F2 C2 F2 C2 E2 B1 E2 G#2", 176, 2, "tuba", 0.16)
        m.seq(t0, 2.9, "k h s h", 176, 2, "drum")
        m.sfx(t0 + 2.8, "zip")
        m.sfx(t0 + 3.6, "gasp")
        m.sfx(t0 + 4.3, "whoosh")
        m.sfx(t0 + 4.9, "bonk")
        m.sfx(t0 + 5.0, "boing")
        m.sfx(t0 + 5.6, "thud")
        m.sfx(t0 + 6.2, "fall_long")
        m.sfx(t0 + 7.9, "thud", 0.4)
        m.sfx(t0 + 8.8, "fanfare")
        m.sfx(t0 + 8.9, "cheer")
        m.seq(t0 + 9.0, 2.6, "C5 E5 G5 E5 F5 A5 C6 - G5 B5 D6 B5 C6 - - .", 176, 2, "xylo", 0.12)
        m.seq(t0 + 11.6, 4.0, "C5+E5+G5 - - - F5+A5+C6 - - - G5+B5+D6 - - - C6+E6+G6 - - -", 120, 2, "brass", 0.07)
        m.sfx(t0 + 11.7, "cheer")
        m.sfx(t0 + 15.5, "whoosh")
        m.sfx(t0 + 16.0, "crash")


# ------------------------------------------------------------------ S5 이적시장

class Shopping(Scene):
    dur = 17.4
    BUYS = [  # (시각, 키 또는 상자, 라벨, 가격 태그)
        (1.2, "fernandes", "£85M 구단 신기록! (강등된 웨스트햄 출신)"),
        (2.6, "tonali", "약 £100M (뉴캐슬에서)"),
        (4.0, "box:SÁVIO £75M", "사비뉴 £75M (맨시티에서)"),
        (5.2, "vanhecke", "£52M (브라이튼에서)"),
        (6.4, "robertson+senesi", "로버트슨·세네시: FREE! (자유계약)"),
        (7.8, "mudryk", "무드릭·마르무시: LOAN (임대)"),
        (9.0, "adarabioyo", "아다라비오요 (첼시에서)"),
    ]
    SLOTS = [(-70, -120), (0, -140), (70, -120), (-40, -210), (40, -210), (0, -290), (-60, -300), (60, -300)]

    def draw(self, cv, t):
        bg_mart(cv, t)
        cx = -200 + 700 * ease(prog(t, 0.0, 1.0))
        cy = 640
        # 선반 위 선수들 (아직 안 산)
        shelf_pos = {"fernandes": (160, 185), "tonali": (380, 185), "vanhecke": (820, 185),
                     "robertson": (1000, 335), "senesi": (1120, 335), "mudryk": (140, 335), "adarabioyo": (300, 335)}
        bought = {}
        slot = 0
        for (bt, key, label) in self.BUYS:
            keys = key.split("+") if not key.startswith("box") else [key]
            for kk in keys:
                bought[kk] = (bt, slot)
                slot += 1
        for key, (sx, sy) in shelf_pos.items():
            bt = bought[key][0]
            if t < bt:
                draw_person(cv, key, sx, sy, 0.4, Pose(t=t, mood="happy", arms="wave" if t > bt - 1 else "down"))
                tag(cv, "SALE", sx, sy - 150, 18, YELLOW, rot=8)
        # 카트 속 선수들
        wallet_y = cy - 210
        for key, (bt, sl) in sorted(bought.items(), key=lambda kv: kv[1][1], reverse=True):
            if t < bt:
                continue
            ox, oy = self.SLOTS[sl]
            tx, ty = cx + 20 + ox, cy - 70 + oy + 110
            k = prog(t, bt, bt + 0.45)
            if key.startswith("box"):
                sx0, sy0 = 640, 340
            else:
                sx0, sy0 = shelf_pos[key]
            x = sx0 + (tx - sx0) * k
            y = sy0 + (ty - sy0) * k - math.sin(k * math.pi) * 200
            if key.startswith("box"):
                cv.save()
                cv.translate(x, y - 60)
                cv.rotate(-10 + (1 - k) * 360)
                shape(cv, rrect(-50, -70, 50, 60, 6), (255, 210, 60), 5)
                text(cv, "SÁVIO", 0, -30, 26, RED, TF_COMIC, oc=None)
                text(cv, "-O's", 0, 0, 26, NAVY, TF_COMIC, oc=None)
                text(cv, "£75M", 0, 40, 26, INK, TF_TITLE, oc=None)
                cv.restore()
            else:
                draw_person(cv, key, x, y, 0.42, Pose(t=t, mood="grin" if k >= 1 else "shock", arms="up"))
        # 카트
        shape(cv, poly([(cx - 150, cy - 170), (cx + 180, cy - 170), (cx + 150, cy - 40), (cx - 120, cy - 40)]),
              (190, 200, 215), 6)
        for i in range(1, 7):
            xx = cx - 150 + i * 47
            cv.drawLine(xx, cy - 170, xx - 4, cy - 40, stroke((150, 160, 180), 4))
        cv.drawLine(cx - 150, cy - 170, cx - 210, cy - 230, stroke(INK, 10))
        for wx in (cx - 100, cx + 110):
            shape(cv, oval(wx, cy - 10, 20, 20), INK, 0)
        # ENIC 지갑 (아기 의자)
        wallet(cv, cx + 150, wallet_y + 60, 0.8, t, "smug" if t < 10.0 else "shock", spit=1.0 < t < 10.5)
        # 데 제르비가 카트를 밀기
        pz = Pose(t=t, mood="grin", arms=((-120, -150), (-60, -150), 10, 10), legs="walk" if t < 1.0 else "stand",
                  phase=t * 9, talk=10.2 < t < 11)
        draw_person(cv, "dezerbi", cx - 270, cy + 20, 0.78, pz)
        # 라벨
        for (bt, key, label) in self.BUYS:
            if bt <= t < bt + 1.35:
                k = ease_out_back(prog(t, bt, bt + 0.3))
                cv.save()
                cv.translate(640, 150)
                cv.scale(k, k)
                tag(cv, label, 0, 0, 34, YELLOW, rot=-3)
                cv.restore()
                pow_text(cv, "KA-CHING!", 1040, 470, prog(t, bt, bt + 0.4), YELLOW, (60, 170, 80), 60, rot=10)
        # 영수증
        if t > 10.2:
            ln = min(1400, (t - 10.2) * 900)
            p = skia.Path()
            p.moveTo(cx + 150, wallet_y + 30)
            p.lineTo(cx + 150 + ln * 0.25, wallet_y + 120)
            p.lineTo(cx + 150 + ln * 0.25 + ln * 0.75, 700)
            cv.drawPath(p, stroke(INK, 34))
            cv.drawPath(p, stroke(WHITE, 26))
            if t < 11.2:
                pow_text(cv, "£££££!!", 900, 400, prog(t, 10.2, 10.6), YELLOW, RED, 70)
        # 로메로 퇴장
        if 11.0 <= t < 14.2:
            k = prog(t, 11.0, 14.0)
            shape(cv, rrect(1090, 380, 1250, 620, 6), (60, 60, 70), 5)
            shape(cv, rrect(1080, 340, 1260, 380, 6), (40, 160, 70), 4)
            text(cv, "EXIT → ATLÉTICO", 1170, 370, 22, WHITE, TF_COMIC, oc=None)
            if k < 0.9:
                draw_person(cv, "romero", 900 + 270 * k, 640, 0.62,
                            Pose(t=t, mood="happy", arms="wave", legs="walk", phase=t * 9))
                bubble(cv, 900, 250, ["¡Adiós!"], 36, tail=(900 + 270 * k, 360))
            caption(cv, "한편, 주장 로메로는 아틀레티코로...", 690)
        # 반 더 벤 질주
        if t >= 14.2:
            k = prog(t, 14.2, 14.7)
            x = -200 + 900 * ease(k)
            if k < 1:
                speed_lines(cv, 640, 360, t, 30, 300)
                motion_lines(cv, x - 80, 520, 220, -1, 7, 300)
            draw_person(cv, "vdv", x, 640, 0.8, Pose(t=t, mood="grin", legs="run" if k < 1 else "stand",
                                                      arms="run" if k < 1 else "up", phase=t * 30))
            tag(cv, "ZOOOM!", 400, 300, 40, (120, 220, 255), rot=-10)
            if t > 15.0:
                bubble(cv, 980, 260, ["새 주장 반 더 벤!", "This is our year!!"], 34, tail=(760, 360))
            if t > 16.2:
                caption(cv, "(스포: 아니었다)", 690, 44, YELLOW)
        chapter_label(cv, "CHAPTER 2 · 2026 여름 이적시장")

    def audio(self, m, t0):
        jingle = "C5 E5 G5 E5 F5 A5 C6 A5 G5 E5 C5 E5 D5 - - . C5 E5 G5 E5 F5 A5 C6 A5 G5 B5 D6 B5 C6 - - ."
        m.seq(t0, 11.0, jingle, 128, 2, "xylo", 0.1)
        m.seq(t0, 11.0, "C3 G2 C3 G2 F2 C3 F2 C3 C3 G2 C3 G2 G2 D3 G2 D3", 128, 2, "bass", 0.14)
        m.seq(t0, 11.0, "k b s b", 128, 2, "drum")
        for (bt, _, _) in self.BUYS:
            m.sfx(t0 + bt, "kaching")
            m.sfx(t0 + bt + 0.05, "whoosh", 0.6)
        m.sfx(t0 + 10.2, "zip")
        m.sfx(t0 + 10.3, "kaching")
        m.seq(t0 + 11.0, 3.2, "D4 F#4 A4 D5 C#5 A4 F#4 E4", 110, 2, "pluck", 0.12)
        m.sfx(t0 + 14.2, "zoom")
        m.sfx(t0 + 14.3, "whoosh")
        m.sfx(t0 + 15.0, "fanfare")
        m.sfx(t0 + 16.2, "sad_trombone")


# ------------------------------------------------------------------ S6 개막 몽타주 (2026-27)

class Montage(Scene):
    dur = 41.0
    SEG = [(0.0, "card"), (2.4, "bre"), (8.9, "new"), (15.4, "for"), (21.9, "eve"), (28.4, "avl"), (37.0, "cup")]

    def seg(self, t):
        cur = self.SEG[0]
        for s in self.SEG:
            if t >= s[0]:
                cur = s
        return cur[1], t - cur[0]

    def draw(self, cv, t):
        name, k = self.seg(t)
        getattr(self, "d_" + name)(cv, k, t)

    def d_card(self, cv, k, t):
        rings_bg(cv, t, (190, 30, 40), (250, 240, 230))
        kk = ease_out_back(prog(k, 0.1, 0.6))
        cv.save()
        cv.translate(640, 330)
        cv.scale(kk, kk)
        shape(cv, rrect(-460, -110, 460, 110, 30), WHITE, 8)
        text(cv, "CHAPTER 3", 0, -30, 60, RED, TF_COMIC, oc=None)
        text(cv, "2026-27 시즌 개막! 결과는?", 0, 50, 54, NAVY, TF_TITLE, oc=None)
        cv.restore()

    def d_bre(self, cv, k, t):
        bg_pitch(cv, t, 1)
        x = 900 - k * 120
        pz = Pose(t=t, mood="shock" if k < 3 else "cry", legs="run", arms="flail", phase=t * 20,
                  eye_pop=1.3, tears=k > 3)
        draw_person(cv, "fernandes", x, 600, 0.9, pz)
        tag(cv, "£85M", x + 60, 380 + math.sin(t * 10) * 8, 28, YELLOW, rot=math.sin(t * 8) * 15)
        if k > 3:
            for i in range(4):
                shape(cv, oval(x - 30 + i * 22, 340 + (i % 2) * 20, 12, 12), (255, 110, 110), 3)
        for i in range(9):
            a = t * 3 + i * 0.7
            bee(cv, x + 180 + math.cos(a) * 160 - k * 10, 330 + math.sin(a * 1.3) * 110, 0.9, t)
        n = min(3, int(k / 1.3))
        scorebug(cv, "브렌트포드", n, "토트넘", 0, f"{min(90, int(k * 16))}'")
        if k > 1.3:
            pow_text(cv, "BZZZZT!", 760, 560, prog(k, 1.3, 1.6), YELLOW, (40, 40, 40), 70)
        reaction(cv, t, "worried", sweat=2)
        caption(cv, "1R 브렌트포드 원정 0-3 · 개막전부터 벌떼", 690)

    def d_new(self, cv, k, t):
        bg_pitch(cv, t, -1)
        barefoot = k > 3.2
        pz = Pose(t=t, mood="grin" if k < 2.0 else ("shock" if k < 3.2 else "sad"), arms="wave" if k < 2.0 else "face",
                  talk=k < 2.0, legs="stand" if not barefoot else "jump", eye_pop=1.3 if 2 < k < 3.2 else 1)
        draw_person(cv, "tonali", 520, 600, 0.95, pz)
        if k < 2.0:
            bubble(cv, 300, 260, ["Ciao, amici!", "(친정팀 안녕~)"], 32, tail=(470, 330))
        for i in range(3):
            if k < 1.8:
                mx, my = 900 + i * 110, 230 + i * 40 + math.sin(t * 5 + i) * 10
                hold = None
            else:
                kk = prog(k, 1.8 + i * 0.3, 3.0 + i * 0.3)
                mx = 520 + (1 - kk) * 300 + kk * (900 + i * 120)
                my = 560 - math.sin(kk * math.pi) * 300 + (1 - kk) * -300 + kk * (-420)
                mx = 900 + i * 110 - math.sin(kk * math.pi) * 420 + kk * 300
                my = 230 + i * 40 + math.sin(kk * math.pi) * 330 - kk * 200
                hold = "ball" if i == 0 else "boot"
            magpie(cv, mx, my, 1.1, t + i, hold)
        if barefoot:
            pow_text(cv, "SNATCH!", 900, 420, prog(k, 3.2, 3.6), WHITE, INK, 80)
        n = 0 if k < 2.4 else (1 if k < 4.2 else 2)
        scorebug(cv, "토트넘", 0, "뉴캐슬", n, f"{min(90, int(k * 16))}'")
        reaction(cv, t, "angry", steam=True)
        caption(cv, "2R 뉴캐슬 0-2 · 토날리 친정팀에게 털림", 690)

    def d_for(self, cv, k, t):
        bg_pitch(cv, t, 1)
        tree(cv, 1010, 560, 0.9, t)
        bx = 700 + (k % 1.6) / 1.6 * 380 if k < 3.2 else 1060
        if k < 3.2:
            ph = (k % 1.6) / 1.6
            bx = 600 + ph * 400 if ph < 0.8 else 920 - (ph - 0.8) * 5 * 300
            ball(cv, bx, 470 - math.sin(min(ph, 0.8) / 0.8 * math.pi) * 60, 18, t * 700)
            if 0.78 < ph < 0.9:
                pow_text(cv, "THUNK", 900, 330, 0.5, YELLOW, (60, 150, 60), 50)
        draw_person(cv, "gallagher", 500, 610, 0.85, Pose(t=t, mood="angry" if k < 3.4 else "sad", legs="kick"
                                                          if (k % 1.6) < 0.3 and k < 3.2 else "stand"))
        if k > 3.2:
            tw = 100 + (k - 3.2) * 400
            cv.save()
            cv.translate(tw, 600)
            cv.rotate(k * 300)
            cs = [(math.cos(a) * 30, math.sin(a) * 30) for a in [i / 10 * math.tau for i in range(10)]]
            for (x0, y0) in cs:
                cv.drawLine(0, 0, x0, y0, stroke((170, 130, 80), 5))
            cv.restore()
            rooster(cv, 820, 640, 0.6, t, mood="sad")
            if k > 4.0:
                cv.drawLine(880, 520, 940 + 20 * math.sin(t * 3), 530, stroke(RED, 6))
                text(cv, "pfffft...", 1000, 500, 30, WHITE, TF_COMIC)
        scorebug(cv, "포레스트", 0, "토트넘", 0, f"{min(90, int(k * 16))}'")
        reaction(cv, t, "tired")
        caption(cv, "3R 노팅엄 포레스트 원정 0-0 · 시즌 첫 승점! (투도르를 잘랐던 그 팀)", 690, 30)

    def d_eve(self, cv, k, t):
        bg_pitch(cv, t, 1)
        toffee(cv, 1000, 420, 1.3, t)
        for i, key in enumerate(["vanhecke", "senesi", "robertson"]):
            draw_person(cv, key, 260 + i * 200, 620, 0.7, Pose(t=t + i, mood="sleep", tilt=math.sin(t + i) * 4))
        for i in range(4):
            kk = (t * 0.5 + i / 4) % 1
            text(cv, "Z", 400 + i * 180 + kk * 40, 300 - kk * 120, 40 + kk * 30, WHITE, TF_COMIC, a=int(255 * (1 - kk)))
        tw = (k * 250) % 1600 - 200
        cv.save()
        cv.translate(tw, 610)
        cv.rotate(k * 200)
        for a in range(10):
            ang = a / 10 * math.tau
            cv.drawLine(0, 0, math.cos(ang) * 34, math.sin(ang) * 34, stroke((170, 130, 80), 5))
        cv.restore()
        scorebug(cv, "토트넘", 0, "에버튼", 0, f"{min(90, int(k * 16))}'")
        reaction(cv, t, "sleep")
        caption(cv, "4R 에버튼 0-0 · ...Zzz", 690)

    def d_avl(self, cv, k, t):
        bg_pitch(cv, t, -1)
        roar = k < 1.4
        lion(cv, 1000, 380, 1.4, t, roar=roar)
        if roar:
            for i in range(8):
                y = 240 + i * 40
                x0 = 850 - ((t * 900 + i * 80) % 700)
                cv.drawLine(x0, y, x0 - 120, y, stroke(WHITE, 5, 180))
            pow_text(cv, "ROAAAR!", 760, 190, prog(k, 0.0, 0.3), YELLOW, (128, 20, 52), 80)
        score = 0
        if k >= 1.4:
            score = 1
        if k >= 3.0:
            score = 2
        if k >= 3.5:
            score = 3
        spurs = 0
        if k >= 5.0:
            spurs = 1
        if k >= 6.0:
            spurs = 2
        # 로버트슨 부메랑 걷어내기
        if 1.4 <= k < 3.0:
            kk = prog(k, 1.4, 2.4)
            draw_person(cv, "robertson", 400, 610, 0.9, Pose(t=t, mood="happy" if kk < 0.6 else "shock",
                                                             legs="kick" if kk < 0.3 else "stand", eye_pop=1.3 if kk > 0.6 else 1))
            ang = kk * math.tau * 0.9
            bx = 460 + math.sin(ang) * 380
            by = 450 - math.sin(ang * 0.5) * 250
            if kk < 1:
                ball(cv, bx, by, 18, t * 800)
            else:
                ball(cv, 150, 480, 18)
                pow_text(cv, "BOING!", 260, 330, prog(k, 2.4, 2.7), YELLOW, RED, 80)
        elif k < 1.4:
            draw_person(cv, "robertson", 400, 610, 0.9, Pose(t=t, mood="shock", arms="face", sy=0.96))
        elif k < 5.0:
            draw_person(cv, "robertson", 400, 610, 0.9, Pose(t=t, mood="cry", tears=True))
            if k > 3.0:
                pow_text(cv, f"0-{score}", 640, 260, prog(k, 3.0 if score == 2 else 3.5, 3.3 if score == 2 else 3.8),
                         WHITE, RED, 100)
        else:
            hype = k < 7.2
            key = "gallagher" if k < 6.0 else "vanhecke"
            draw_person(cv, key, 520, 610, 0.95, Pose(t=t, mood="grin" if hype else "shock", arms="up" if hype else "face",
                                                     legs="jump" if hype and int(t * 6) % 2 else "stand",
                                                     jaw=0.8 if not hype else 0))
            rooster(cv, 800, 640 - (abs(math.sin(t * 8)) * 40 if hype else 0), 0.6, t,
                    mood="happy" if hype else "cry")
            if k < 6.0:
                pow_text(cv, "86' 갤러거 GOAL!", 640, 230, prog(k, 5.0, 5.3), YELLOW, NAVY, 60)
            elif k < 7.2:
                pow_text(cv, "90+' 반 헤케 GOAL!!", 640, 230, prog(k, 6.0, 6.3), YELLOW, NAVY, 60)
                bubble(cv, 1000, 560, ["It's the hope", "that kills you..."], 26, tail=(860, 580))
            else:
                confetti(cv, t, 11, 60, up=True)
                pow_text(cv, "FT 2-3", 640, 230, prog(k, 7.2, 7.5), WHITE, RED, 100)
        scorebug(cv, "토트넘", spurs, "빌라", score, f"{min(95, int(k * 12))}'")
        reaction(cv, t, "shock" if k > 7.2 else ("grin" if k > 5 else "worried"), sweat=3, eye_pop=1.3 if k > 7.2 else 1)
        caption(cv, "5R 아스톤 빌라 2-3 · 0-3에서 2골 추격... 희망고문 완성", 690)

    def d_cup(self, cv, k, t):
        cv.drawRect(rect(0, 0, W, H), fill((20, 30, 70)))
        if k < 2.0:
            for i in range(6):
                kk = (k * 1.2 + i / 6) % 1
                burst(cv, 200 + i * 180, 300 - kk * 100, 10, 40 + 60 * kk, 10, [YELLOW, RED, WHITE][i % 3], ow=0)
            text(cv, "Meanwhile, 카라바오컵...", 640, 180, 44, YELLOW, TF_KR)
            text(cv, "찰튼전 5-1 승리!!", 640, 330, 80, WHITE, TF_TITLE)
            text(cv, "(올 시즌 유일한 승리)", 640, 420, 40, (200, 200, 220), TF_KR)
        else:
            text(cv, "...그리고", 640, 200, 44, (200, 200, 220), TF_KR)
            text(cv, "리버풀 원정 1-3 탈락", 640, 340, 72, (255, 110, 100), TF_TITLE)
            draw_person(cv, "dezerbi", 640, 700, 0.6, Pose(t=t, mood="sad", arms="down"))

    def audio(self, m, t0):
        m.sfx(t0 + 0.1, "zoom")
        m.sfx(t0 + 0.4, "fanfare")
        # 중계 테마
        theme = "G4 C5 E5 G5 - E5 G5 A5 G5 E5 C5 D5 - - . . G4 C5 E5 G5 - E5 G5 C6 B5 G5 E5 D5 C5 - - ."
        for (st, name) in self.SEG[1:6]:
            m.seq(t0 + st, 1.4, theme, 150, 2, "brass", 0.08)
            m.seq(t0 + st, 1.4, "k s k s", 150, 2, "drum")
            m.sfx(t0 + st, "whistle")
        s = dict((n, st) for st, n in self.SEG)
        b = t0 + s["bre"]
        m.sfx(b + 0.2, "buzz")
        m.sfx(b + 1.8, "buzz")
        for i in range(3):
            m.sfx(b + 1.3 * (i + 1), "boo")
        m.sfx(b + 3.0, "yelp")
        n = t0 + s["new"]
        m.sfx(n + 0.3, "blip")
        m.sfx(n + 1.8, "caw")
        m.sfx(n + 2.4, "caw")
        m.sfx(n + 3.2, "pow")
        m.sfx(n + 2.4, "boo")
        m.sfx(n + 4.2, "boo")
        f = t0 + s["for"]
        for i in range(2):
            m.sfx(f + 1.3 + i * 1.6, "bonk")
        m.sfx(f + 3.2, "whoosh")
        m.sfx(f + 4.0, "party_horn")
        e = t0 + s["eve"]
        m.sfx(e + 0.5, "snore")
        m.sfx(e + 3.0, "snore")
        m.seq(e + 1.5, 4.5, "C5 - - - B4 - - - A4 - - - G4 - - -", 60, 2, "organ", 0.05)
        a = t0 + s["avl"]
        m.sfx(a + 0.1, "roar")
        m.sfx(a + 1.5, "bonk")
        m.sfx(a + 2.4, "boing")
        m.sfx(a + 2.5, "boo")
        m.sfx(a + 3.0, "pow")
        m.sfx(a + 3.5, "pow")
        m.sfx(a + 5.0, "cheer")
        m.sfx(a + 5.05, "fanfare")
        m.sfx(a + 6.0, "cheer")
        m.seq(a + 5.0, 2.2, "C5 E5 G5 C6 E5 G5 C6 E6", 200, 2, "clar", 0.1)
        m.sfx(a + 7.2, "whistle")
        m.sfx(a + 7.4, "sad_trombone")
        c = t0 + s["cup"]
        m.sfx(c + 0.1, "fanfare")
        m.sfx(c + 0.2, "cheer")
        m.sfx(c + 2.0, "sad_trombone")


# ------------------------------------------------------------------ S7 다시 엘리베이터

class BackToNow(Scene):
    dur = 8.0

    def draw(self, cv, t):
        bg_elevator(cv, t, 1.0, 20)
        draw_person(cv, "dezerbi", 560, 640, 1.0, Pose(t=t, mood="dizzy" if t < 4 else "sad", legs="sit", arms="down"))
        stars_circle(cv, 560, 300, t)
        rooster(cv, 780, 640, 0.9, t, mood="cry" if t > 4.5 else "sad", talk=4.0 < t < 6.0)
        shape(cv, rrect(840, 170, 1240, 470, 16), WHITE, 6)
        text(cv, "2026-27 성적표", 1040, 222, 38, NAVY, TF_TITLE, oc=None)
        rows = ["5경기 0승 2무 3패", "승점 2 · 2득점 8실점", "순위: 20위 (꼴찌)"]
        for i, s in enumerate(rows):
            if t > 0.5 + i * 0.6:
                text(cv, s, 1040, 290 + i * 60, 36, RED if i == 2 else INK, TF_KR, oc=None)
        if t > 4.0:
            bubble(cv, 700, 170, ["It's the hope", "that kills you..."], 34, tail=(780, 420))
        caption(cv, "...그렇게 우리는 여기에 왔다.", 690)

    def audio(self, m, t0):
        m.seq(t0, 8.0, "A4+C5+E5 - - . G4+B4+D5 - - . F4+A4+C5 - - . E4+G#4+B4 - - .", 90, 2, "organ", 0.06)
        for i in range(3):
            m.sfx(t0 + 0.5 + i * 0.6, "pop")
        m.sfx(t0 + 4.0, "sad_trombone")


# ------------------------------------------------------------------ S8 성난 군중

class Mob(Scene):
    dur = 9.0

    def draw(self, cv, t):
        cv.drawRect(rect(0, 0, W, H), fill((24, 20, 50)))
        cv.drawCircle(1100, 110, 50, fill((250, 240, 200)))
        shape(cv, smooth([(80, 420), (240, 180), (640, 140), (1040, 180), (1200, 420)], closed=False) and
              rrect(140, 170, 1140, 440, 60), (220, 224, 236), 6)
        for x in range(200, 1100, 70):
            cv.drawLine(x, 190, x, 430, stroke((180, 186, 204), 4))
        text(cv, "TOTTENHAM HOTSPUR STADIUM", 640, 250, 40, NAVY, TF_COMIC, oc=None)
        # 발코니의 ENIC
        if t < 5.5:
            wallet(cv, 640, 380, 0.9, t, "shock" if t > 2.0 else "smug")
        else:
            k = t - 5.5
            wallet(cv, 640 + 900 * k, 380, 0.9, t, "shock", legs="run", phase=t * 25)
            dust(cv, 600 + 900 * k - 60, 380, (k * 2) % 1)
        shape(cv, rrect(520, 380, 760, 400, 4), (120, 120, 140), 4)
        # 군중
        rng = random.Random(4)
        for row in range(3):
            for i in range(11):
                x = 40 + i * 120 + row * 40 + rng.uniform(-20, 20)
                y = 560 + row * 60
                jump = abs(math.sin(t * 7 + i + row)) * 16
                shape(cv, oval(x, y - 40 - jump, 30, 34), rng.choice([(250, 214, 186), (205, 150, 110), (150, 98, 66)]), 4)
                shape(cv, rrect(x - 34, y - 12 - jump, x + 34, y + 80, 16), rng.choice([NAVY, WHITE, NAVY]), 4)
                if (i + row) % 3 == 0:
                    cv.drawLine(x + 30, y - jump, x + 44, y - 110 - jump, stroke(INK, 8))
                    cv.drawLine(x + 30, y - jump, x + 44, y - 110 - jump, stroke((140, 90, 50), 4))
                    fl = math.sin(t * 20 + i) * 6
                    shape(cv, smooth([(x + 32, y - 110 - jump), (x + 44 + fl, y - 150 - jump), (x + 56, y - 110 - jump)]),
                          (255, 150, 40), 3)
                elif (i + row) % 3 == 1:
                    cv.drawLine(x - 30, y - jump, x - 40, y - 120 - jump, stroke(INK, 7))
                    for d in (-10, 0, 10):
                        cv.drawLine(x - 40 + d, y - 120 - jump, x - 40 + d, y - 140 - jump, stroke(INK, 5))
        # 배너
        for i, (s, x, y, r) in enumerate([("PROMISED CHANGE, DELIVERED FAILURE", 330, 470, -3),
                                          ("LOVE TOTTENHAM, HATE ENIC", 950, 480, 4)]):
            cv.save()
            cv.translate(x, y + math.sin(t * 5 + i) * 6)
            cv.rotate(r)
            w = text_w(s, 30, TF_COMIC) + 40
            shape(cv, rrect(-w / 2, -30, w / 2, 20, 4), WHITE, 5)
            text(cv, s, 0, 8, 30, NAVY, TF_COMIC, oc=None)
            cv.restore()
        k = (t * 1.6) % 1
        pow_text(cv, "ENIC OUT!", 640, 130, 0.3 + 0.7 * min(1, k * 3), YELLOW, RED, 80 + 10 * math.sin(t * 10), rot=-3)
        caption(cv, "\"Levy has gone and nothing has changed\"", 660, 30, sub="\"레비는 떠났는데, 바뀐 게 없다\" ─ 팬 단체 Change for Tottenham")

    def audio(self, m, t0):
        m.seq(t0, 9.0, "k . k . k k k .", 110, 2, "drum")
        m.sfx(t0, "cheer")
        for i in range(8):
            m.sfx(t0 + 0.2 + i * 1.1, "boo", 0.8)
        m.sfx(t0 + 2.0, "gasp")
        m.sfx(t0 + 5.5, "zip")
        m.sfx(t0 + 5.6, "whoosh")


# ------------------------------------------------------------------ S9 그 사이 (뮌헨, LA)

class Meanwhile(Scene):
    dur = 9.2

    def draw(self, cv, t):
        cv.drawRect(rect(0, 0, 640, H), fill((230, 60, 70)))
        cv.drawRect(rect(640, 0, W, H), fill((255, 190, 120)))
        cv.drawCircle(960, 200, 90, fill((255, 230, 150)))
        cv.drawRect(rect(640, 520, W, H), fill((245, 214, 150)))
        for i in range(3):
            y = 470 + i * 18
            p = skia.Path()
            p.moveTo(640, y)
            for x in range(640, W + 20, 20):
                p.lineTo(x, y + math.sin(x * 0.05 + t * 3 + i) * 5)
            cv.drawPath(p, stroke((80, 170, 230), 8))
        cv.drawLine(640, 0, 640, H, stroke(INK, 10))
        text(cv, "MEANWHILE IN MUNICH", 320, 70, 40, WHITE, TF_COMIC)
        text(cv, "MEANWHILE IN LA", 960, 70, 40, WHITE, TF_COMIC)
        wob = math.sin(t * 5) * 6
        draw_person(cv, "kane", 320, 640, 0.9, Pose(t=t, mood="grin", arms="up", tilt=wob * 0.3))
        for i in range(3):
            trophy_icon(cv, 320 + wob * (i + 1), 330 - i * 70, 0.9)
        text(cv, "케인: 뮌헨에서 드디어 트로피", 320, 150, 32, YELLOW, TF_KR)
        # LA 비치 의자
        shape(cv, poly([(840, 610), (1100, 610), (1060, 560), (880, 560)]), (80, 180, 200), 5)
        draw_person(cv, "son", 980, 640, 0.9, Pose(t=t, mood="happy", arms="wave"))
        shape(cv, rrect(930, 340, 1030, 372, 12), INK, 0)
        text(cv, "쏘니: 행복 중 :)", 960, 150, 32, NAVY, TF_KR)
        if t > 4.5:
            k = prog(t, 4.5, 5.0)
            cv.save()
            cv.translate(0, (1 - ease(k)) * 400)
            shape(cv, rrect(380, 440, 900, 720, 30), (60, 60, 80), 6)
            rooster(cv, 640, 720, 1.0, t, mood="cry")
            text(cv, "우리 애들 잘 지내네... ㅠㅠ", 640, 470, 34, WHITE, TF_KR)
            cv.restore()

    def audio(self, m, t0):
        uke = "C5 E5 G5 E5 A4 C5 E5 C5 F4 A4 C5 A4 G4 B4 D5 B4"
        m.seq(t0, 4.5, uke, 140, 4, "pluck", 0.12)
        m.seq(t0, 4.5, "C3 . A2 . F2 . G2 .", 140, 2, "bass", 0.12)
        m.sfx(t0 + 0.3, "twinkle")
        m.sfx(t0 + 4.5, "sad_trombone")


# ------------------------------------------------------------------ S10 다음 화 + 아웃트로

class NextTime(Scene):
    dur = 13.0
    fade_out = 0.0

    def draw(self, cv, t):
        if t < 8.2:
            cv.drawRect(rect(0, 0, W, H), fill((150, 10, 20)))
            speed_lines(cv, 640, 360, t, 24, 250, (255, 80, 80), 120)
            shape(cv, rrect(160, 30, 1120, 110, 20), (20, 20, 20), 5)
            text(cv, "NEXT TIME ON TOTTENHAM TOONS", 640, 90, 54, YELLOW, TF_COMIC, oc=None)
            devil(cv, 930, 640, 1.4, t)
            text(cv, "맨유 원정 @ 올드 트래포드", 400, 200, 44, WHITE, TF_TITLE)
            text(cv, "2026. 10. 10", 400, 250, 36, YELLOW, TF_TITLE)
            gulp = 2.0 < t < 2.6
            draw_person(cv, "dezerbi", 400, 700, 0.95,
                        Pose(t=t, mood="shock" if t > 1.6 else "worried", sweat=3, eye_pop=1.3 if gulp else 1.0,
                             arms="face" if t > 3.0 else "down", sy=0.97 if gulp else 1.0))
            if gulp:
                pow_text(cv, "GULP!", 560, 330, prog(t, 2.0, 2.3), WHITE, INK, 60)
            if t > 3.0:
                bubble(cv, 700, 330, ["...Mamma mia."], 34, tail=(480, 400))
            if t > 4.6:
                shape(cv, rrect(60, 290, 520, 400, 16), (20, 20, 20), 5)
                text(cv, "데 제르비 남은 목숨", 290, 335, 30, WHITE, TF_KR, oc=None)
                for i in range(3):
                    heart(cv, 210 + i * 80, 370, 1.0, full=(i == 0))
        else:
            k = t - 8.2
            rings_bg(cv, t)
            rooster(cv, 640, 470, 1.4, t, mood="happy", talk=k < 2.0)
            if k > 0.2:
                sc = ease_out_back(prog(k, 0.2, 0.7))
                cv.save()
                cv.translate(640, 590)
                cv.scale(sc, sc)
                text(cv, "That's all, Spurs fans!", 0, 0, 72, YELLOW, TF_COMIC, ow=10)
                cv.restore()
            if k > 0.9:
                text(cv, "COME ON YOU SPURS", 640, 670, 40, WHITE, TF_COMIC)
            text(cv, "※ 2026.09.24 기준 실제 결과 바탕의 풍자 패러디 · 인물은 캐리커처입니다", 640, 710, 20,
                 (230, 230, 240), TF_KR, ow=4)
            r = 1000 * (1 - ease(prog(k, 2.4, 4.3)))
            iris(cv, 640, 360, r)

    def audio(self, m, t0):
        m.seq(t0, 8.0, "D4 . . D4 F4 . D4 . Ab4 . G4 . F4 . D4 .", 120, 2, "tuba", 0.16)
        m.seq(t0, 8.0, "k . s . k k s .", 120, 2, "drum")
        m.sfx(t0 + 1.6, "gasp")
        m.sfx(t0 + 2.0, "gulp")
        m.sfx(t0 + 4.6, "pop")
        fin = "C5 E5 G5 C6 B5 A5 G5 E5 F5 A5 C6 F6 E6 D6 C6 - G5 G5 A5 B5 C6 - - ."
        m.seq(t0 + 8.2, 3.6, fin, 190, 2, "clar", 0.12)
        m.seq(t0 + 8.2, 3.6, "C3 G2 C3 G2 F2 C3 G2 D3 C3 G2 C3 G2", 190, 2, "tuba", 0.16)
        m.seq(t0 + 8.2, 3.6, "k b s b", 190, 2, "drum")
        m.seq(t0 + 11.8, 1.2, "C5+E5+G5+C6 - - -", 100, 2, "brass", 0.1)


# -------------------------------------------------------------------------- main

def build():
    return [ElevatorOpen(), Title(), Previously(), Carousel(), Cliff(), Shopping(), Montage(), BackToNow(), Mob(),
            Meanwhile(), NextTime()]


def main():
    scenes = build()
    starts, acc = [], 0.0
    for s in scenes:
        starts.append(acc)
        acc += s.dur
    total = acc
    mix_ = Mixer(total)
    for s, st in zip(scenes, starts):
        s.audio(mix_, st)
    buf = mix_.buf[: int(total * SR)]
    buf = np.tanh(buf * 1.2)
    buf = buf / max(1e-9, np.max(np.abs(buf))) * 0.9
    wav_path = os.path.join(HERE, "_audio.wav")
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((buf * 32767).astype(np.int16).tobytes())
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", wav_path, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    cv = surf.getCanvas()
    nframes = int(total * FPS)
    si = 0
    for fi in range(nframes):
        t = fi / FPS
        while si + 1 < len(scenes) and t >= starts[si + 1]:
            si += 1
        sc, lt = scenes[si], t - starts[si]
        cv.clear(skia.Color(0, 0, 0))
        cv.save()
        sc.draw(cv, lt)
        cv.restore()
        k = 1.0
        if sc.fade_in and lt < sc.fade_in:
            k = lt / sc.fade_in
        if sc.fade_out and lt > sc.dur - sc.fade_out:
            k = min(k, (sc.dur - lt) / sc.fade_out)
        if k < 1:
            cv.drawRect(rect(0, 0, W, H), fill((0, 0, 0), int(255 * (1 - max(0, k)))))
        proc.stdin.write(surf.makeImageSnapshot().toarray().tobytes())
        if fi % 480 == 0:
            print(f"frame {fi}/{nframes}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(wav_path)
    print("wrote", OUT, f"({total:.1f}s)")


if __name__ == "__main__":
    main()
