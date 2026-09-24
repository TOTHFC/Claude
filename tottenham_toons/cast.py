"""등장인물(카툰 캐리커처)과 마스코트.

인물은 위키미디어 공용 사진을 참고해 특징(머리 모양·색, 수염, 얼굴형, 피부톤)을 과장한 캐리커처다.
선수는 토트넘 2026/27 나이키 홈 킷을 입는다:
흰 바탕 + 험멜풍 톤온톤 사선 무늬, 네이비 V칼라·소매 끝·옆구리 패널, 빨간 AIA, 네이비 반바지, 흰 양말.
"""
import math
from dataclasses import dataclass, field

import skia

from toon import (AIA, BINARY, INK, NAVY, RED, TF_TITLE, WHITE, YELLOW, C, fill, hose, mix, oval, poly,
                  rrect, shape, smooth, stroke, sweat, text)


def shade(c, k=0.82):
    return tuple(int(v * k) for v in c)


SKINS = {
    "fair": (250, 214, 186), "light": (240, 198, 164), "olive": (222, 176, 138),
    "tan": (205, 150, 110), "brown": (150, 98, 66), "dark": (104, 66, 46),
}

PEOPLE = {
    # 감독
    "frank": dict(name="토마스 프랭크", skin="light", hair="curly_mop", hc=(128, 86, 54), face=(54, 80, 0.45),
                  beard="stubble_light", brow=(110, 74, 46), nose="long", eyes=1.18, outfit="track"),
    "tudor": dict(name="이고르 투도르", skin="olive", hair="receding", hc=(62, 52, 46), face=(56, 80, 0.62),
                  beard="stubble", brow=(50, 40, 34), nose="long", eyes=0.95, outfit="track", brow_w=7),
    "dezerbi": dict(name="로베르토 데 제르비", skin="olive", hair="short", fringe="swept", hc=(34, 28, 26),
                    face=(58, 72, 0.6), beard="full", bc=(34, 28, 26), brow=(30, 24, 22), nose="bulb",
                    eyes=1.0, outfit="black", brow_w=7),
    "ange": dict(name="포스테코글루", skin="olive", hair="short", fringe="swept", hc=(170, 168, 165),
                 face=(62, 72, 0.7), beard="stubble", brow=(90, 86, 84), nose="bulb", eyes=0.9, outfit="suit"),
    "levy": dict(name="다니엘 레비", skin="light", hair="bald", hc=(200, 190, 180), face=(62, 70, 0.72),
                 beard="stubble_light", brow=(120, 110, 100), nose="bulb", eyes=0.95, outfit="polo"),
    # 선수
    "fernandes": dict(name="마테우스 페르난데스", num=18, skin="olive", hair="curly", hc=(30, 24, 22),
                      face=(56, 72, 0.55), beard="none", brow=(30, 24, 22), nose="bulb", eyes=1.0, outfit="kit",
                      brow_w=7),
    "tonali": dict(name="산드로 토날리", num=16, skin="light", hair="long_dark", hc=(44, 32, 26),
                   face=(56, 74, 0.5), beard="full", bc=(44, 32, 26), brow=(40, 30, 24), nose="long", eyes=1.0,
                   outfit="kit"),
    "robertson": dict(name="앤디 로버트슨", num=3, skin="fair", hair="short", fringe="side", hc=(70, 50, 36),
                      face=(58, 72, 0.6), beard="stubble", brow=(70, 50, 36), nose="bulb", eyes=1.05,
                      outfit="kit"),
    "vanhecke": dict(name="얀 폴 반 헤케", num=6, skin="fair", hair="short", fringe="spiky", hc=(236, 214, 150),
                     face=(56, 74, 0.55), beard="none", brow=(190, 160, 110), nose="bulb", eyes=0.95, outfit="kit"),
    "senesi": dict(name="마르코스 세네시", num=5, skin="light", hair="curly", hc=(46, 34, 28), face=(56, 74, 0.55),
                   beard="stubble", brow=(46, 34, 28), nose="long", eyes=1.0, outfit="kit"),
    "mudryk": dict(name="미하일로 무드릭", num=27, skin="fair", hair="blond_shag", hc=(246, 228, 170),
                   face=(54, 72, 0.5), beard="none", brow=(170, 140, 100), nose="bulb", eyes=1.0, outfit="kit",
                   tattoo=True),
    "adarabioyo": dict(name="토신 아다라비오요", num=4, skin="dark", hair="buzz", hc=(20, 16, 14),
                       face=(60, 76, 0.7), beard="short_full", bc=(20, 16, 14), brow=(20, 16, 14), nose="wide",
                       eyes=1.0, outfit="kit"),
    "gallagher": dict(name="코너 갤러거", num=8, skin="fair", hair="long_slick", hc=(222, 184, 116),
                      face=(56, 72, 0.55), beard="mustache", bc=(200, 160, 100), brow=(190, 150, 100), nose="bulb",
                      eyes=1.0, outfit="kit"),
    "vdv": dict(name="미키 반 더 벤", num=37, skin="fair", hair="short", fringe="swept", hc=(120, 88, 60),
                face=(56, 74, 0.5), beard="none", brow=(110, 80, 56), nose="bulb", eyes=0.95, outfit="kit",
                captain=True),
    "romero": dict(name="크리스티안 로메로", num=17, skin="tan", hair="short", fringe="flat", hc=(26, 22, 20),
                   face=(56, 72, 0.6), beard="stubble", brow=(26, 22, 20), nose="bulb", eyes=0.95, outfit="kit",
                   tattoo=True),
    "son": dict(name="손흥민", num=7, skin="light", hair="fringe", hc=(24, 20, 20), face=(58, 70, 0.55),
                beard="none", brow=(24, 20, 20), nose="bulb", eyes=0.9, outfit="lafc", smile_eyes=True),
    "kane": dict(name="해리 케인", num=9, skin="fair", hair="short", fringe="quiff", hc=(140, 100, 64),
                 face=(56, 76, 0.55), beard="stubble_light", brow=(130, 96, 62), nose="long", eyes=0.95,
                 outfit="bayern"),
}


@dataclass
class Pose:
    t: float = 0.0
    mood: str = "happy"
    look: tuple = (0.0, 0.0)
    talk: bool = False
    arms: object = "down"
    legs: str = "stand"
    phase: float = 0.0
    sx: float = 1.0
    sy: float = 1.0
    tilt: float = 0.0
    sweat: int = 0
    steam: bool = False
    tears: bool = False
    blush: bool = False
    eye_pop: float = 1.0
    jaw: float = 0.0
    blink: bool = True
    extra: dict = field(default_factory=dict)


HEAD_Y = -262


def head_path(rx, ry, jaw):
    p = skia.Path()
    p.moveTo(-rx, 0)
    p.cubicTo(-rx, -ry * 0.56, -rx * 0.56, -ry, 0, -ry)
    p.cubicTo(rx * 0.56, -ry, rx, -ry * 0.56, rx, 0)
    p.cubicTo(rx, ry * 0.5, rx * jaw, ry * 0.97, 0, ry)
    p.cubicTo(-rx * jaw, ry * 0.97, -rx, ry * 0.5, -rx, 0)
    p.close()
    return p


def merged_blobs(cv, circles, col, ow=5):
    """여러 원을 하나의 실루엣으로 (바깥 외곽선만)."""
    for (x, y, r) in circles:
        cv.drawCircle(x, y, r, stroke(INK, ow * 2))
    for (x, y, r) in circles:
        cv.drawCircle(x, y, r, fill(col))


# ------------------------------------------------------------------ 머리카락

def hair_back(cv, sp, rx, ry):
    h, hc = sp["hair"], sp["hc"]
    if h == "long_dark":
        p = smooth([(-rx - 8, -ry * 0.3), (-rx - 16, ry * 0.6), (-rx - 10, ry + 34), (-rx * 0.3, ry + 30),
                    (rx * 0.3, ry + 30), (rx + 10, ry + 34), (rx + 16, ry * 0.6), (rx + 8, -ry * 0.3), (0, -ry - 8)])
        shape(cv, p, hc, 5)
    elif h == "long_slick":
        shape(cv, oval(rx * 0.1, -ry - 8, 20, 17), hc, 5)
        cv.drawLine(rx * 0.1 - 14, -ry + 2, rx * 0.1 + 14, -ry + 2, stroke(shade(hc, 0.7), 4))
    elif h == "blond_shag":
        p = smooth([(-rx - 10, -ry * 0.2), (-rx - 12, ry * 0.35), (-rx + 4, ry * 0.55), (rx - 4, ry * 0.55),
                    (rx + 12, ry * 0.35), (rx + 10, -ry * 0.2), (0, -ry - 10)])
        shape(cv, p, hc, 5)


def hair_front(cv, sp, rx, ry, t):
    h, hc = sp["hair"], sp["hc"]
    dk = shade(hc, 0.72)
    if h == "curly_mop":
        cs = []
        for i in range(13):
            a = math.radians(170 + i * 200 / 12)
            cs.append((math.cos(a) * rx * 0.98, -ry * 0.18 + math.sin(a) * ry * 0.95, 21))
        cs = [(x, min(y, -ry * 0.62) if abs(x) < rx * 0.75 else y, r) for (x, y, r) in cs]
        cs += [(-rx * 0.95, -ry * 0.05, 18), (rx * 0.95, -ry * 0.05, 18), (-rx * 0.4, -ry * 0.85, 26),
               (rx * 0.4, -ry * 0.85, 26), (0, -ry * 0.92, 26)]
        merged_blobs(cv, cs, hc)
        for (x, y, r) in cs[::2]:
            cv.drawArc(skia.Rect.MakeLTRB(x - r * 0.6, y - r * 0.6, x + r * 0.6, y + r * 0.6), 200, 120, False,
                       stroke(dk, 3))
    elif h == "receding":
        for sgn in (-1, 1):
            p = smooth([(sgn * rx * 0.78, -ry * 0.55), (sgn * (rx + 5), -ry * 0.25), (sgn * (rx + 4), ry * 0.05),
                        (sgn * rx * 0.86, ry * 0.02), (sgn * rx * 0.8, -ry * 0.3)])
            shape(cv, p, hc, 4)
        cv.drawArc(skia.Rect.MakeLTRB(-rx * 0.5, -ry * 0.95, rx * 0.1, -ry * 0.55), 200, 70, False,
                   stroke(WHITE, 6, 170))
        for i in range(5):  # 앞머리 몇 가닥
            x = -12 + i * 6
            cv.drawLine(x, -ry * 0.93, x + 3, -ry * 0.82, stroke(hc, 3))
    elif h in ("short", "curly", "buzz"):
        fr = sp.get("fringe", "flat")
        top = -ry * 1.04
        line_y = -ry * (0.42 if h != "buzz" else 0.55)
        pts = [(-rx - 3, -ry * 0.05), (-rx * 0.98, -ry * 0.55), (-rx * 0.6, -ry * 0.95), (0, top),
               (rx * 0.6, -ry * 0.95), (rx * 0.98, -ry * 0.55), (rx + 3, -ry * 0.05), (rx * 0.82, -ry * 0.15)]
        if fr == "swept":
            pts += [(rx * 0.7, line_y + 4), (rx * 0.1, line_y - 6), (-rx * 0.5, line_y + 6), (-rx * 0.82, -ry * 0.15)]
        elif fr == "side":
            pts += [(rx * 0.6, line_y), (-rx * 0.2, line_y - 10), (-rx * 0.55, line_y + 14), (-rx * 0.82, -ry * 0.15)]
        elif fr == "spiky":
            pts += [(rx * 0.7, line_y), (rx * 0.45, line_y + 12), (rx * 0.2, line_y - 2), (0, line_y + 14),
                    (-rx * 0.25, line_y - 2), (-rx * 0.5, line_y + 12), (-rx * 0.82, -ry * 0.15)]
        elif fr == "quiff":
            pts[3] = (rx * 0.15, top - 16)
            pts += [(rx * 0.6, line_y), (-rx * 0.6, line_y), (-rx * 0.82, -ry * 0.15)]
        else:
            pts += [(rx * 0.6, line_y), (-rx * 0.6, line_y), (-rx * 0.82, -ry * 0.15)]
        if h == "buzz":
            pts = [(-rx * 0.96, -ry * 0.3), (-rx * 0.7, -ry * 0.88), (0, -ry * 1.01), (rx * 0.7, -ry * 0.88),
                   (rx * 0.96, -ry * 0.3), (rx * 0.6, line_y), (-rx * 0.6, line_y)]
        shape(cv, smooth(pts, tension=0.9), hc, 5)
        if h == "curly":
            cs = [(-rx * 0.6 + i * rx * 0.3, -ry * 0.9 + (i % 2) * 10, 17) for i in range(5)]
            cs += [(-rx * 0.8, -ry * 0.55, 15), (rx * 0.8, -ry * 0.55, 15), (-rx * 0.3, line_y - 4, 14),
                   (rx * 0.25, line_y - 2, 14)]
            merged_blobs(cv, cs, hc, 4)
            for (x, y, r) in cs:
                cv.drawArc(skia.Rect.MakeLTRB(x - r * 0.5, y - r * 0.5, x + r * 0.5, y + r * 0.5), 180, 150, False,
                           stroke(mix(hc, WHITE, 0.25), 3))
        elif h != "buzz":
            for i in range(3):
                x = -rx * 0.3 + i * rx * 0.3
                cv.drawLine(x, -ry * 0.92, x + 8, -ry * 0.62, stroke(mix(hc, WHITE, 0.3), 3))
    elif h == "long_dark":
        p = smooth([(-rx - 6, ry * 0.2), (-rx - 4, -ry * 0.55), (-rx * 0.5, -ry * 1.02), (0, -ry * 1.06),
                    (rx * 0.5, -ry * 1.02), (rx + 4, -ry * 0.55), (rx + 6, ry * 0.2), (rx * 0.78, ry * 0.1),
                    (rx * 0.72, -ry * 0.45), (rx * 0.2, -ry * 0.62), (0, -ry * 0.82), (-rx * 0.2, -ry * 0.62),
                    (-rx * 0.72, -ry * 0.45), (-rx * 0.78, ry * 0.1)], tension=0.9)
        shape(cv, p, hc, 5)
        cv.drawLine(0, -ry * 1.02, 0, -ry * 0.82, stroke(shade(hc, 0.6), 3))
    elif h == "long_slick":
        p = smooth([(-rx - 3, -ry * 0.1), (-rx * 0.95, -ry * 0.62), (-rx * 0.5, -ry * 1.0), (0, -ry * 1.06),
                    (rx * 0.5, -ry * 1.0), (rx * 0.95, -ry * 0.62), (rx + 3, -ry * 0.1), (rx * 0.8, -ry * 0.2),
                    (rx * 0.6, -ry * 0.6), (0, -ry * 0.68), (-rx * 0.6, -ry * 0.6), (-rx * 0.8, -ry * 0.2)], tension=0.9)
        shape(cv, p, hc, 5)
        for i in range(-2, 3):
            cv.drawLine(i * 12, -ry * 0.7, i * 16, -ry * 1.0, stroke(shade(hc, 0.8), 3))
    elif h == "blond_shag":
        p = smooth([(-rx - 6, -ry * 0.05), (-rx * 0.9, -ry * 0.7), (-rx * 0.4, -ry * 1.08), (rx * 0.3, -ry * 1.1),
                    (rx * 0.9, -ry * 0.72), (rx + 6, -ry * 0.05), (rx * 0.75, -ry * 0.25), (rx * 0.55, -ry * 0.35),
                    (rx * 0.35, -ry * 0.22), (rx * 0.1, -ry * 0.4), (-rx * 0.15, -ry * 0.24), (-rx * 0.4, -ry * 0.42),
                    (-rx * 0.6, -ry * 0.26), (-rx * 0.8, -ry * 0.3)], tension=0.8)
        shape(cv, p, hc, 5)
        cv.drawLine(-rx * 0.3, -ry * 1.0, -rx * 0.1, -ry * 0.55, stroke(mix(hc, (170, 130, 80), 0.5), 3))
    elif h == "fringe":
        pts = [(-rx - 3, -ry * 0.05), (-rx * 0.98, -ry * 0.6), (-rx * 0.55, -ry * 1.0), (0, -ry * 1.08),
               (rx * 0.55, -ry * 1.0), (rx * 0.98, -ry * 0.6), (rx + 3, -ry * 0.05), (rx * 0.8, -ry * 0.15)]
        for i in range(7):
            x = rx * 0.75 - i * rx * 0.25
            pts.append((x, -ry * (0.25 if i % 2 == 0 else 0.4)))
        pts.append((-rx * 0.8, -ry * 0.15))
        shape(cv, smooth(pts, tension=0.6), hc, 5)
    elif h == "bald":
        cv.drawArc(skia.Rect.MakeLTRB(-rx * 0.55, -ry * 0.98, rx * 0.05, -ry * 0.5), 200, 80, False,
                   stroke(WHITE, 7, 190))
        for sgn in (-1, 1):
            shape(cv, smooth([(sgn * rx * 0.95, -ry * 0.3), (sgn * (rx + 3), -ry * 0.05),
                              (sgn * rx * 0.88, -ry * 0.02)]), hc, 3)


# ------------------------------------------------------------------ 얼굴

def draw_eye(cv, x, y, rx, ry, pose, skin, sp, side):
    mood = pose.mood
    ep = pose.eye_pop
    rx, ry = rx * ep, ry * ep
    eye = oval(x, y, rx, ry)
    closed = pose.blink and (pose.t % 3.3) < 0.09 and mood not in ("shock",)
    if mood == "sleep" or closed or (mood == "happy" and sp.get("smile_eyes")):
        cv.drawArc(skia.Rect.MakeLTRB(x - rx * 0.8, y - ry * 0.4, x + rx * 0.8, y + ry * 0.6),
                   200 if mood != "sleep" else 20, 140, False, stroke(INK, 5))
        return
    shape(cv, eye, WHITE, 4.5)
    if mood == "dizzy":
        p = skia.Path()
        for i in range(40):
            a = i * 0.45 + pose.t * 8 * side
            r = i * 0.45
            q = (x + math.cos(a) * r, y + math.sin(a) * r)
            p.moveTo(*q) if i == 0 else p.lineTo(*q)
        cv.drawPath(p, stroke(INK, 3))
        return
    if mood == "x":
        for d in (-1, 1):
            cv.drawLine(x - 9, y - 9 * d, x + 9, y + 9 * d, stroke(INK, 5))
        return
    pr = 6.5 if mood not in ("shock",) else 3.5
    lx, ly = pose.look
    px, py = x + lx * rx * 0.45, y + ly * ry * 0.4
    cv.drawCircle(px, py, pr, fill(INK))
    cv.drawCircle(px - 2, py - 2, pr * 0.3, fill(WHITE))
    lid = {"sad": 0.45, "smug": 0.5, "tired": 0.55, "angry": 0.3, "cry": 0.4}.get(mood, 0)
    if lid:
        cv.save()
        cv.clipPath(eye, doAntiAlias=True)
        if mood == "angry":
            p = poly([(x - rx - 2, y - ry - 2), (x + rx + 2, y - ry - 2),
                      (x + rx + 2, y - ry + ry * 2 * lid + (-8 * side)), (x - rx - 2, y - ry + ry * 2 * lid + 8 * side)])
            cv.drawPath(p, fill(skin))
            cv.drawPath(p, stroke(INK, 4))
        else:
            cv.drawRect(skia.Rect.MakeLTRB(x - rx - 2, y - ry - 2, x + rx + 2, y - ry + ry * 2 * lid), fill(skin))
            cv.drawLine(x - rx, y - ry + ry * 2 * lid, x + rx, y - ry + ry * 2 * lid, stroke(INK, 4))
        cv.restore()
        cv.drawPath(eye, stroke(INK, 4.5))


def draw_mouth(cv, pose, rx, ry, skin):
    mood, t = pose.mood, pose.t
    my = ry * 0.52
    dark, tongue = (90, 20, 30), (230, 90, 100)
    talk_open = pose.talk and (int(t * 9) % 2 == 0)
    if pose.jaw > 0 or mood == "shock":
        j = max(pose.jaw, 0.6 if mood == "shock" else 0)
        h = 14 + 40 * j
        p = oval(0, my + h * 0.4, 14 + 6 * j, h * 0.6)
        shape(cv, p, dark, 4)
        cv.save()
        cv.clipPath(p, doAntiAlias=True)
        cv.drawCircle(0, my + h * 0.9, 14, fill(tongue))
        cv.restore()
        return
    if mood in ("grin", "happy_big") or (talk_open and mood in ("happy", "grin", "smug")):
        p = skia.Path()
        p.moveTo(-26, my - 4)
        p.quadTo(0, my + (34 if not talk_open else 40), 26, my - 4)
        p.close()
        shape(cv, p, dark, 4)
        cv.save()
        cv.clipPath(p, doAntiAlias=True)
        cv.drawRect(skia.Rect.MakeLTRB(-30, my - 8, 30, my + 5), fill(WHITE))
        cv.drawCircle(0, my + 30, 13, fill(tongue))
        cv.restore()
        cv.drawPath(p, stroke(INK, 4))
        return
    if mood in ("yell", "angry") and (talk_open or mood == "yell"):
        p = rrect(-22, my - 6, 22, my + 24, 10)
        shape(cv, p, dark, 4)
        cv.drawRect(skia.Rect.MakeLTRB(-18, my - 3, 18, my + 4), fill(WHITE))
        return
    if mood == "angry":
        p = rrect(-20, my - 4, 20, my + 10, 4)
        shape(cv, p, WHITE, 4)
        for x in (-10, 0, 10):
            cv.drawLine(x, my - 4, x, my + 10, stroke(INK, 2))
        return
    if talk_open:
        shape(cv, oval(0, my + 6, 15, 11), dark, 4)
        return
    if mood in ("happy", "smug"):
        p = skia.Path()
        p.moveTo(-22, my)
        p.quadTo(0, my + 20, 22 if mood == "happy" else 26, my - (0 if mood == "happy" else 8))
        cv.drawPath(p, stroke(INK, 5))
    elif mood in ("sad", "cry"):
        p = skia.Path()
        p.moveTo(-18, my + 12)
        p.quadTo(0, my - 6, 18, my + 12)
        cv.drawPath(p, stroke(INK, 5))
        if mood == "cry":
            shape(cv, oval(0, my + 6, 12, 8), dark, 4)
    elif mood in ("worried", "dizzy"):
        p = skia.Path()
        p.moveTo(-20, my + 4)
        for i in range(1, 9):
            p.lineTo(-20 + i * 5, my + 4 + (4 if i % 2 else -4))
        cv.drawPath(p, stroke(INK, 4))
    elif mood == "sleep":
        shape(cv, oval(0, my + 6, 7, 6), dark, 3)
    else:
        cv.drawLine(-16, my + 4, 16, my + 4, stroke(INK, 5))


def draw_head(cv, sp, pose):
    skin = SKINS[sp["skin"]]
    rx, ry, jaw = sp["face"]
    sd = shade(skin)
    hair_back(cv, sp, rx, ry)
    for sgn in (-1, 1):
        shape(cv, oval(sgn * (rx - 2), 4, 12, 17), skin, 4.5)
        cv.drawArc(skia.Rect.MakeLTRB(sgn * (rx - 2) - 6, -6, sgn * (rx - 2) + 6, 12), 90 - sgn * 90, 180, False,
                   stroke(sd, 3))
    hp = head_path(rx, ry, jaw)
    shape(cv, hp, skin, 5)
    b = sp.get("beard", "none")
    cv.save()
    cv.clipPath(hp, doAntiAlias=True)
    if b in ("full", "short_full"):
        top = ry * (0.22 if b == "full" else 0.38)
        p = smooth([(-rx - 5, -ry * 0.05), (-rx * 0.7, top), (-rx * 0.35, ry * 0.36), (0, ry * 0.3),
                    (rx * 0.35, ry * 0.36), (rx * 0.7, top), (rx + 5, -ry * 0.05), (rx + 5, ry + 5), (-rx - 5, ry + 5)],
                   tension=0.7)
        cv.drawPath(p, fill(sp["bc"]))
        for i in range(10):
            x = -rx * 0.7 + i * rx * 0.155
            cv.drawLine(x, ry * 0.55, x + 3, ry * 0.8, stroke(shade(sp["bc"], 1.6) if sp["bc"][0] < 80 else shade(sp["bc"]), 2))
    elif b in ("stubble", "stubble_light"):
        a = 70 if b == "stubble" else 38
        p = smooth([(-rx - 5, -ry * 0.02), (-rx * 0.6, ry * 0.25), (0, ry * 0.3), (rx * 0.6, ry * 0.25),
                    (rx + 5, -ry * 0.02), (rx + 5, ry + 5), (-rx - 5, ry + 5)], tension=0.7)
        cv.drawPath(p, fill((60, 60, 80), a))
    cv.restore()
    cv.drawPath(hp, stroke(INK, 5))
    if sp.get("tattoo"):
        pass
    es = sp.get("eyes", 1.0)
    ex, ey = 19 * es + 2, -ry * 0.12
    erx, ery = 18 * es, 22 * es
    for side in (-1, 1):
        draw_eye(cv, side * ex, ey, erx, ery, pose, skin, sp, side)
    # 눈썹
    bw = sp.get("brow_w", 5)
    for side in (-1, 1):
        bx = side * ex
        by = ey - ery * pose.eye_pop - 8
        m = pose.mood
        if m in ("angry", "yell"):
            y_in, y_out = by + 10, by - 6
        elif m in ("worried", "sad", "cry"):
            y_in, y_out = by - 10, by + 4
        elif m == "shock":
            y_in = y_out = by - 12
        elif m == "smug":
            y_in, y_out = (by, by - 8) if side > 0 else (by + 4, by + 2)
        else:
            y_in, y_out = by - 2, by - 2
        p = skia.Path()
        p.moveTo(bx - side * 16, y_in)
        p.quadTo(bx, min(y_in, y_out) - 6, bx + side * 16, y_out)
        cv.drawPath(p, stroke(sp["brow"], bw))
    # 코
    nose = sp.get("nose", "bulb")
    nx = pose.look[0] * 5
    if nose == "long":
        p = skia.Path()
        p.moveTo(nx - 4, ey + 6)
        p.cubicTo(nx - 6, ry * 0.28, nx + 16, ry * 0.36, nx + 2, ry * 0.36)
        cv.drawPath(p, stroke(INK, 4))
    elif nose == "wide":
        shape(cv, oval(nx, ry * 0.26, 15, 10), sd, 4)
    else:
        shape(cv, oval(nx, ry * 0.24, 10, 11), sd, 4)
    if sp.get("beard") == "mustache":
        p = smooth([(-26, ry * 0.46), (-12, ry * 0.36), (0, ry * 0.4), (12, ry * 0.36), (26, ry * 0.46),
                    (12, ry * 0.46), (0, ry * 0.44), (-12, ry * 0.46)], tension=0.8)
        shape(cv, p, sp["bc"], 3.5)
    draw_mouth(cv, pose, rx, ry, skin)
    if sp.get("beard") == "full":
        p = smooth([(-24, ry * 0.42), (0, ry * 0.36), (24, ry * 0.42), (0, ry * 0.46)], tension=0.8)
        cv.drawPath(p, fill(sp["bc"]))
    hair_front(cv, sp, rx, ry, pose.t)
    if pose.blush:
        for sgn in (-1, 1):
            cv.drawCircle(sgn * rx * 0.6, ry * 0.2, 12, fill((255, 120, 140), 120))
    return rx, ry


# ------------------------------------------------------------------ 몸

SHOULDER = (40, -182)
HIP_Y = -96


def arm_targets(arms, t, phase):
    """(왼손, 오른손, 왼bend, 오른bend). 화면 기준 왼쪽 = 캐릭터 오른팔."""
    L, R = (-40, -182), (40, -182)
    if isinstance(arms, tuple):
        return arms
    if arms == "down":
        sw = math.sin(phase) * 10
        return (-54 + sw, -104), (54 - sw, -104), 14, -14
    if arms == "hips":
        return (-34, -118), (34, -118), -40, 40
    if arms == "up":
        wig = math.sin(t * 14) * 8
        return (-72 + wig, -300), (72 - wig, -300), 20, -20
    if arms == "wave":
        wig = math.sin(t * 12) * 18
        return (-54, -104), (78 + wig, -280), 14, -26
    if arms == "point":
        return (-54, -104), (120, -200), 14, -8
    if arms == "shrug":
        return (-92, -196), (92, -196), -30, 30
    if arms == "face":
        return (-58, -242), (58, -242), 30, -30
    if arms == "hold":
        return (-34, -150), (34, -150), -24, 24
    if arms == "push":
        return (60, -150), (95, -150), -10, 10
    if arms == "run":
        a = math.sin(phase) * 50
        return (-60 - a * 0.3, -150 + a), (60 + a * 0.3, -150 - a), 30, -30
    if arms == "flail":
        return (-100 + math.sin(t * 25) * 20, -250 + math.cos(t * 25) * 30), \
               (100 + math.cos(t * 23) * 20, -250 + math.sin(t * 22) * 30), 30, -30
    if arms == "butt":
        return (-40, -96), (40, -96), 30, -30
    if arms == "chin":
        return (-54, -104), (16, -214), 14, -40
    return (-54, -104), (54, -104), 14, -14


def leg_targets(legs, t, phase):
    """(왼발, 오른발, bend) 로컬 좌표."""
    if legs == "walk":
        s = math.sin(phase)
        return (-18 + s * 26, -max(0, math.cos(phase)) * 14), (18 - s * 26, -max(0, -math.cos(phase)) * 14), 10
    if legs == "run":
        s = math.sin(phase)
        return (-14 + s * 44, -max(0, math.cos(phase)) * 34), (14 - s * 44, -max(0, -math.cos(phase)) * 34), 22
    if legs == "dangle":
        return (-22, 6), (22, 6), 0
    if legs == "jump":
        return (-34, -40), (34, -40), 26
    if legs == "sit":
        return (-30, -40), (30, -40), 36
    if legs == "kick":
        return (-18, 0), (70, -70), -10
    return (-22, 0), (22, 0), 0


def outfit_cols(sp):
    o = sp["outfit"]
    skin = SKINS[sp["skin"]]
    if o == "kit":
        return dict(shirt=WHITE, sleeve=WHITE, cuff=NAVY, arm=skin, shorts=BINARY, leg_top=skin, sock=WHITE,
                    boot=INK)
    if o == "track":
        return dict(shirt=(22, 32, 78), sleeve=(22, 32, 78), cuff=(22, 32, 78), arm=(22, 32, 78),
                    shorts=(16, 22, 54), leg_top=(16, 22, 54), sock=(16, 22, 54), boot=INK)
    if o == "black":
        return dict(shirt=(34, 34, 40), sleeve=(34, 34, 40), cuff=(34, 34, 40), arm=(34, 34, 40),
                    shorts=(22, 26, 48), leg_top=(22, 26, 48), sock=(22, 26, 48), boot=INK)
    if o == "suit":
        return dict(shirt=(30, 40, 70), sleeve=(30, 40, 70), cuff=(30, 40, 70), arm=(30, 40, 70),
                    shorts=(30, 40, 70), leg_top=(30, 40, 70), sock=(30, 40, 70), boot=INK)
    if o == "polo":
        return dict(shirt=WHITE, sleeve=WHITE, cuff=WHITE, arm=skin, shorts=(60, 60, 70), leg_top=(60, 60, 70),
                    sock=(60, 60, 70), boot=(90, 60, 40))
    if o == "lafc":
        return dict(shirt=(20, 20, 24), sleeve=(20, 20, 24), cuff=(200, 160, 70), arm=skin, shorts=(20, 20, 24),
                    leg_top=skin, sock=(20, 20, 24), boot=(200, 160, 70))
    if o == "bayern":
        return dict(shirt=(220, 20, 50), sleeve=(220, 20, 50), cuff=WHITE, arm=skin, shorts=(220, 20, 50),
                    leg_top=skin, sock=(220, 20, 50), boot=WHITE)
    return dict(shirt=WHITE, sleeve=WHITE, cuff=WHITE, arm=skin, shorts=NAVY, leg_top=skin, sock=WHITE, boot=INK)


def torso_path():
    return smooth([(-46, -176), (-32, -194), (0, -198), (32, -194), (46, -176), (42, -138), (38, -100),
                   (0, -96), (-38, -100), (-42, -138)], tension=0.7)


def draw_torso(cv, sp, oc):
    o = sp["outfit"]
    tp = torso_path()
    shape(cv, tp, oc["shirt"], 5)
    cv.save()
    cv.clipPath(tp, doAntiAlias=True)
    if o == "kit":
        for i in range(-10, 12):
            x = i * 16
            cv.drawLine(x - 60, -90, x + 60, -210, stroke((232, 235, 246), 7))
        cv.drawRect(skia.Rect.MakeLTRB(-50, -168, -35, -90), fill(NAVY))
        cv.drawRect(skia.Rect.MakeLTRB(35, -168, 50, -90), fill(NAVY))
    elif o in ("track",):
        cv.drawLine(0, -198, 0, -96, stroke(WHITE, 4))
        cv.drawRect(skia.Rect.MakeLTRB(-50, -168, -40, -90), fill(WHITE, 90))
        cv.drawRect(skia.Rect.MakeLTRB(40, -168, 50, -90), fill(WHITE, 90))
    elif o == "suit":
        cv.drawPath(poly([(-16, -198), (0, -150), (16, -198)]), fill(WHITE))
        cv.drawPath(poly([(-4, -190), (4, -190), (6, -130), (0, -120), (-6, -130)]), fill((230, 180, 40)))
        cv.drawPath(poly([(-24, -196), (0, -130), (-30, -150)]), fill(shade(oc["shirt"], 0.8)))
        cv.drawPath(poly([(24, -196), (0, -130), (30, -150)]), fill(shade(oc["shirt"], 0.8)))
    elif o == "lafc":
        cv.drawRect(skia.Rect.MakeLTRB(-50, -198, 50, -188), fill((200, 160, 70)))
    elif o == "bayern":
        cv.drawRect(skia.Rect.MakeLTRB(-6, -198, 6, -96), fill(WHITE, 200))
    cv.restore()
    cv.drawPath(tp, stroke(INK, 5))
    if o == "kit":
        shape(cv, poly([(-16, -196), (0, -176), (16, -196)]), NAVY, 3.5)
        shape(cv, poly([(-10, -196), (0, -184), (10, -196)]), WHITE, 0)
        # 엠블럼(공 위의 수탉)과 스우시, AIA
        cv.drawCircle(-22, -160, 5, fill(NAVY))
        cv.drawPath(poly([(-25, -166), (-22, -176), (-17, -170), (-19, -165)]), fill(NAVY))
        p = skia.Path()
        p.moveTo(14, -166)
        p.quadTo(18, -158, 30, -170)
        cv.drawPath(p, stroke(NAVY, 3))
        text(cv, "AIA", 0, -130, 24, AIA, TF_TITLE, oc=None)
        if sp.get("captain"):
            pass
    elif o == "polo":
        shape(cv, poly([(-18, -198), (0, -184), (18, -198), (8, -186), (0, -178), (-8, -186)]), WHITE, 3)
    elif o == "black":
        cv.drawArc(skia.Rect.MakeLTRB(-18, -206, 18, -186), 20, 140, False, stroke((60, 60, 70), 4))
    elif o in ("lafc", "bayern"):
        cv.drawCircle(-22, -162, 7, fill((200, 160, 70) if o == "lafc" else WHITE))


def draw_person(cv, key, x, y, s=1.0, pose=None, flip=False):
    sp = PEOPLE[key]
    pose = pose or Pose()
    skin = SKINS[sp["skin"]]
    oc = outfit_cols(sp)
    cv.save()
    cv.translate(x, y)
    cv.rotate(pose.tilt)
    cv.scale(s * pose.sx * (-1 if flip else 1), s * pose.sy)
    # 다리
    lf, rf, lb = leg_targets(pose.legs, pose.t, pose.phase)
    for (hx, (fx, fy), sgn) in ((-20, lf, -1), (20, rf, 1)):
        hip = (hx, HIP_Y + 8)
        knee = ((hx + fx) / 2 + sgn * lb * 0.3, (HIP_Y + fy) / 2 - lb)
        hose(cv, hip, knee, sgn * 4, oc["leg_top"], 17, 4)
        hose(cv, knee, (fx, fy - 6), -sgn * 4, oc["sock"], 17, 4)
        if sp["outfit"] == "kit":
            dx, dy = fx - knee[0], fy - 6 - knee[1]
            ln = math.hypot(dx, dy) or 1
            kx, ky = knee[0] + dx / ln * 6, knee[1] + dy / ln * 6
            cv.drawLine(kx - 8, ky, kx + 8, ky, stroke(NAVY, 3))
        bp = oval(fx + sgn * 10, fy - 4, 22, 11)
        shape(cv, bp, oc["boot"], 4)
    if pose.legs == "run":
        k = pose.phase
        cv.drawArc(skia.Rect.MakeLTRB(-60, -80, 60, 12), (k * 57) % 360, 250, False, stroke(INK, 3, 120))
    # 반바지
    sh = smooth([(-42, -110), (42, -110), (46, -72), (6, -70), (0, -84), (-6, -70), (-46, -72)], tension=0.4)
    shape(cv, sh, oc["shorts"], 5)
    if sp["outfit"] == "kit":
        text(cv, str(sp.get("num", "")), -26, -78, 16, WHITE, TF_TITLE, oc=None)
    # 목, 몸통
    shape(cv, rrect(-14, -214, 14, -186, 6), shade(skin), 4)
    draw_torso(cv, sp, oc)
    if sp.get("captain") and sp["outfit"] == "kit":
        pass
    # 머리
    cv.save()
    bob = math.sin(pose.t * 3) * 1.5
    cv.translate(0, HEAD_Y + bob)
    rx, ry = draw_head(cv, sp, pose)
    if pose.sweat:
        for i in range(pose.sweat):
            k = (pose.t * 1.5 + i * 0.37) % 1
            sweat(cv, (rx + 10) * (1 if i % 2 else -1) + (8 if i % 2 else -8) * k, -ry * 0.5 + k * 40, 1.0,
                  int(255 * (1 - k)))
    if pose.tears:
        for sgn in (-1, 1):
            for i in range(6):
                k = (pose.t * 2 + i / 6) % 1
                cv.drawCircle(sgn * (30 + 110 * k), -10 - 70 * k + 180 * k * k, 7, fill((120, 200, 255)))
    if pose.steam:
        for sgn in (-1, 1):
            for i in range(3):
                k = (pose.t * 1.3 + i / 3) % 1
                shape(cv, oval(sgn * (rx + 18 + 26 * k), -10 - 60 * k, 10 + 18 * k, 8 + 14 * k), (240, 240, 245),
                      3, a=int(230 * (1 - k)))
    if pose.mood == "sleep":
        k = (pose.t * 0.8) % 1
        text(cv, "Z", rx + 20 + 30 * k, -ry - 20 * k, 30 + 20 * k, WHITE, oc=INK, a=int(255 * (1 - k)))
    cv.restore()
    # 팔 (앞)
    lh, rh, lbend, rbend = arm_targets(pose.arms, pose.t, pose.phase)
    for sh_pt, hand, bend in (((-40, -182), lh, lbend), ((40, -182), rh, rbend)):
        hose(cv, sh_pt, hand, bend, oc["arm"], 16, 4)
        dx, dy = hand[0] - sh_pt[0], hand[1] - sh_pt[1]
        ln = math.hypot(dx, dy) or 1
        if sp["outfit"] in ("kit", "polo", "lafc", "bayern"):
            e = (sh_pt[0] + dx / ln * 30, sh_pt[1] + dy / ln * 30)
            cv.drawLine(*sh_pt, *e, stroke(INK, 34))
            cv.drawLine(*sh_pt, *e, stroke(oc["sleeve"], 26))
            c0 = (sh_pt[0] + dx / ln * 26, sh_pt[1] + dy / ln * 26)
            cv.drawLine(*c0, *e, stroke(oc["cuff"], 26))
        shape(cv, oval(hand[0], hand[1], 13, 13), skin, 4)
    if sp.get("captain") and sp["outfit"] == "kit":
        e = (-40 - 14, -170)
        cv.drawLine(-58, -178, -48, -160, stroke(INK, 14))
        cv.drawLine(-58, -178, -48, -160, stroke(YELLOW, 9))
    cv.restore()


def draw_face_only(cv, key, x, y, s=1.0, pose=None):
    """얼굴만 (리액션 인셋용)."""
    sp = PEOPLE[key]
    pose = pose or Pose()
    cv.save()
    cv.translate(x, y)
    cv.scale(s * pose.sx, s * pose.sy)
    rx, ry = draw_head(cv, sp, pose)
    if pose.sweat:
        for i in range(pose.sweat):
            k = (pose.t * 1.5 + i * 0.37) % 1
            sweat(cv, (rx + 10) * (1 if i % 2 else -1), -ry * 0.5 + k * 40, 1.0, int(255 * (1 - k)))
    if pose.steam:
        for sgn in (-1, 1):
            for i in range(3):
                k = (pose.t * 1.3 + i / 3) % 1
                shape(cv, oval(sgn * (rx + 18 + 26 * k), -10 - 60 * k, 10 + 18 * k, 8 + 14 * k), (240, 240, 245),
                      3, a=int(230 * (1 - k)))
    cv.restore()


# ------------------------------------------------------------------ 마스코트

def rooster(cv, x, y, s=1.0, t=0.0, mood="happy", flip=False, look=(0, 0), talk=False, jump=0.0):
    """토트넘 수탉 (사이드킥)."""
    cv.save()
    cv.translate(x, y - jump)
    cv.scale(s * (-1 if flip else 1), s)
    # 공
    shape(cv, oval(0, -20, 34, 22), WHITE, 5)
    cv.drawPath(poly([(-8, -30), (8, -30), (12, -18), (0, -10), (-12, -18)]), fill(INK))
    # 다리
    for sgn in (-1, 1):
        cv.drawLine(sgn * 10, -40, sgn * 12, -62, stroke(INK, 10))
        cv.drawLine(sgn * 10, -40, sgn * 12, -62, stroke((240, 170, 40), 5))
    # 꼬리
    for i, c in enumerate([NAVY, (40, 60, 140), NAVY]):
        p = smooth([(-30, -100), (-70 - i * 8, -150 + i * 22), (-86 - i * 4, -110 + i * 20), (-48, -80)], tension=0.9)
        shape(cv, p, c, 4)
    body = smooth([(-44, -90), (-20, -60), (26, -62), (44, -96), (34, -130), (6, -120), (-30, -124)], tension=0.9)
    shape(cv, body, WHITE, 5)
    cv.drawArc(skia.Rect.MakeLTRB(-26, -118, 16, -80), 30, 120, False, stroke((220, 224, 236), 5))
    # 머리
    shape(cv, oval(34, -150, 30, 32), WHITE, 5)
    for i in range(3):
        shape(cv, oval(20 + i * 12, -184 + (i == 1) * -6, 9, 12), RED, 4)
    shape(cv, poly([(60, -154), (84, -146), (60, -138)]), (250, 180, 40), 4)
    shape(cv, oval(56, -126, 7, 11), RED, 3)
    ep = 1.25 if mood == "shock" else 1.0
    for ex in (26, 48):
        shape(cv, oval(ex, -156, 10 * ep, 13 * ep), WHITE, 3.5)
        if mood == "sad" or mood == "cry":
            cv.drawLine(ex - 9, -160, ex + 9, -160, stroke(INK, 4))
        cv.drawCircle(ex + look[0] * 4, -154 + look[1] * 4, 4 if mood != "shock" else 2.5, fill(INK))
    if mood in ("sad", "cry"):
        cv.drawLine(20, -174, 34, -168, stroke(INK, 4))
        cv.drawLine(42, -168, 56, -174, stroke(INK, 4))
    if mood == "angry":
        cv.drawLine(16, -174, 34, -166, stroke(INK, 5))
        cv.drawLine(42, -166, 60, -174, stroke(INK, 5))
    if talk and int(t * 9) % 2 == 0:
        shape(cv, poly([(60, -146), (86, -136), (60, -130)]), (200, 120, 20), 3)
    if mood == "cry":
        for sgn in (-1, 1):
            for i in range(5):
                k = (t * 2 + i / 5) % 1
                cv.drawCircle(37 + sgn * (20 + 80 * k), -150 - 50 * k + 140 * k * k, 6, fill((120, 200, 255)))
    cv.restore()


def bee(cv, x, y, s=1.0, t=0.0, angry=True):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    fl = math.sin(t * 60) * 8
    for sgn in (-1, 1):
        shape(cv, oval(sgn * 10, -24 + fl * 0.3, 12, 18 + fl * 0.4), (220, 240, 255), 3, a=220)
    shape(cv, poly([(-34, 0), (-48, 4), (-34, 8)]), INK, 0)
    bp = oval(0, 2, 34, 22)
    shape(cv, bp, (255, 212, 40), 4)
    cv.save()
    cv.clipPath(bp, doAntiAlias=True)
    for xx in (-16, 0, 16):
        cv.drawRect(skia.Rect.MakeLTRB(xx - 5, -30, xx + 3, 30), fill(INK))
    cv.restore()
    cv.drawPath(bp, stroke(INK, 4))
    shape(cv, oval(26, -4, 9, 10), WHITE, 3)
    cv.drawCircle(29, -3, 4, fill(INK))
    if angry:
        cv.drawLine(18, -16, 34, -10, stroke(INK, 4))
    shape(cv, rrect(-8, 16, 20, 22, 3), RED, 2)  # 빨간 스카프 (브렌트포드)
    cv.restore()


def magpie(cv, x, y, s=1.0, t=0.0, holding=None):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    fl = math.sin(t * 20) * 16
    shape(cv, poly([(-10, -10), (-60, -30 + fl), (-40, 6)]), INK, 3)
    shape(cv, poly([(-30, 4), (-80, 14), (-70, 24), (-26, 14)]), INK, 3)
    shape(cv, oval(0, 0, 32, 22), INK, 3)
    shape(cv, oval(8, 6, 18, 12), WHITE, 3)
    shape(cv, oval(28, -18, 18, 16), INK, 3)
    shape(cv, poly([(42, -22), (62, -16), (42, -12)]), (70, 70, 80), 3)
    shape(cv, oval(32, -21, 6, 6), WHITE, 0)
    cv.drawCircle(33, -21, 3, fill(INK))
    shape(cv, poly([(-10, -12), (10, -2), (-6, 4)]), (90, 120, 200), 0)
    if holding == "ball":
        shape(cv, oval(56, -10, 13, 13), WHITE, 3)
    elif holding == "boot":
        shape(cv, oval(58, -10, 20, 9), INK, 3)
    cv.restore()


def tree(cv, x, y, s=1.0, t=0.0, mood="smug"):
    """노팅엄 포레스트 나무 (로빈 후드 모자)."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    for sgn in (-1, 1):
        cv.drawLine(sgn * 14, 0, sgn * 18, -60, stroke(INK, 22))
        cv.drawLine(sgn * 14, 0, sgn * 18, -60, stroke((130, 84, 50), 14))
    shape(cv, rrect(-26, -150, 26, -50, 14), (130, 84, 50), 5)
    cs = [(-50, -180, 44), (0, -210, 52), (50, -180, 44), (-30, -150, 36), (30, -150, 36)]
    merged_blobs(cv, cs, (60, 150, 60))
    shape(cv, oval(-12, -112, 10, 12), WHITE, 3)
    shape(cv, oval(12, -112, 10, 12), WHITE, 3)
    cv.drawCircle(-10, -110, 4, fill(INK))
    cv.drawCircle(14, -110, 4, fill(INK))
    p = skia.Path()
    p.moveTo(-14, -84)
    p.quadTo(0, -74, 16, -88)
    cv.drawPath(p, stroke(INK, 4))
    shape(cv, poly([(-40, -236), (50, -260), (20, -226)]), (40, 110, 40), 4)
    cv.drawLine(20, -250, 60, -290, stroke(RED, 5))
    cv.restore()


def toffee(cv, x, y, s=1.0, t=0.0, sleep=True):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    for sgn in (-1, 1):
        shape(cv, poly([(sgn * 40, 0), (sgn * 82, -30), (sgn * 76, 0), (sgn * 82, 30)]), (40, 80, 200), 4)
    shape(cv, oval(0, 0, 50, 36), (200, 120, 50), 5)
    cv.drawArc(skia.Rect.MakeLTRB(-30, -24, 10, 0), 200, 90, False, stroke((240, 180, 110), 5))
    if sleep:
        cv.drawLine(-22, -4, -8, -4, stroke(INK, 4))
        cv.drawLine(8, -4, 22, -4, stroke(INK, 4))
        shape(cv, oval(0, 14, 6, 5), (90, 20, 30), 3)
    cv.restore()


def lion(cv, x, y, s=1.0, t=0.0, roar=False):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    cs = [(math.cos(a) * 62, math.sin(a) * 62 - 10, 26) for a in [i / 12 * math.tau for i in range(12)]]
    merged_blobs(cv, cs, (128, 20, 52))
    shape(cv, oval(0, -10, 58, 58), (128, 20, 52), 0)
    shape(cv, oval(0, -6, 46, 44), (250, 196, 60), 5)
    for sgn in (-1, 1):
        shape(cv, oval(sgn * 18, -18, 9, 11), WHITE, 3)
        cv.drawCircle(sgn * 18, -16, 4, fill(INK))
        cv.drawLine(sgn * 8, -30, sgn * 30, -36, stroke(INK, 5))
    shape(cv, poly([(-8, 2), (8, 2), (0, 10)]), INK, 0)
    if roar:
        shape(cv, oval(0, 24, 22, 16 + 4 * math.sin(t * 30)), (90, 20, 30), 4)
        for sgn in (-1, 1):
            shape(cv, poly([(sgn * 14, 10), (sgn * 8, 22), (sgn * 4, 10)]), WHITE, 2)
    else:
        p = skia.Path()
        p.moveTo(-14, 18)
        p.quadTo(0, 28, 14, 18)
        cv.drawPath(p, stroke(INK, 4))
    shape(cv, rrect(-40, 40, 40, 50, 5), (149, 191, 229), 3)
    cv.restore()


def hammer(cv, x, y, s=1.0, t=0.0, mood="happy", legs=True):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    if legs:
        for sgn in (-1, 1):
            k = math.sin(t * 20) * 14 * sgn
            cv.drawLine(sgn * 8, -40, sgn * 8 + k, 0, stroke(INK, 10))
            cv.drawLine(sgn * 8, -40, sgn * 8 + k, 0, stroke((27, 177, 231), 6))
    shape(cv, rrect(-9, -110, 9, -36, 5), (124, 20, 52), 4)
    shape(cv, rrect(-46, -150, 46, -104, 10), (170, 170, 186), 5)
    for sgn in (-1, 1):
        shape(cv, oval(sgn * 14, -130, 9, 11 if mood != "shock" else 14), WHITE, 3)
        cv.drawCircle(sgn * 14, -128, 4 if mood != "shock" else 2.5, fill(INK))
    if mood == "shock":
        shape(cv, oval(0, -112, 8, 7), (90, 20, 30), 3)
    else:
        p = skia.Path()
        p.moveTo(-10, -114)
        p.quadTo(0, -108, 10, -114)
        cv.drawPath(p, stroke(INK, 3))
    cv.restore()


def cannon(cv, x, y, s=1.0, t=0.0, trophy=True):
    """아스날 대포 (우승 중)."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    for sgn in (-1, 1):
        shape(cv, oval(sgn * 30, -20, 24, 24), (120, 70, 40), 4)
        cv.drawCircle(sgn * 30, -20, 6, fill(INK))
    cv.save()
    cv.rotate(-25 + math.sin(t * 6) * 5)
    shape(cv, rrect(-60, -70, 70, -30, 16), (200, 30, 40), 5)
    shape(cv, oval(70, -50, 12, 22), (90, 20, 20), 4)
    shape(cv, oval(-10, -58, 8, 9), WHITE, 3)
    cv.drawCircle(-8, -57, 3.5, fill(INK))
    cv.restore()
    if trophy:
        cv.save()
        cv.translate(-10, -130 + math.sin(t * 8) * 6)
        trophy_icon(cv, 0, 0, 0.9)
        cv.restore()
    cv.restore()


def devil(cv, x, y, s=1.0, t=0.0):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    cv.drawLine(60, -10, 70, -200, stroke(INK, 10))
    cv.drawLine(60, -10, 70, -200, stroke((250, 200, 40), 5))
    for dx in (-14, 0, 14):
        cv.drawLine(70 + dx, -200, 70 + dx * 0.6, -236, stroke(INK, 7))
    body = smooth([(-40, 0), (-44, -80), (-30, -120), (30, -120), (44, -80), (40, 0)], tension=0.8)
    shape(cv, body, (220, 30, 30), 5)
    shape(cv, oval(0, -160, 44, 46), (220, 30, 30), 5)
    for sgn in (-1, 1):
        shape(cv, poly([(sgn * 20, -196), (sgn * 38, -238), (sgn * 38, -190)]), (250, 220, 120), 4)
        shape(cv, oval(sgn * 15, -168, 9, 10), YELLOW, 3)
        cv.drawCircle(sgn * 15, -167, 4, fill(INK))
        cv.drawLine(sgn * 6, -182, sgn * 26, -176, stroke(INK, 5))
    p = skia.Path()
    p.moveTo(-24, -140)
    p.quadTo(0, -118 + math.sin(t * 5) * 4, 24, -140)
    cv.drawPath(p, stroke(INK, 5))
    cv.drawRect(skia.Rect.MakeLTRB(-16, -140, 16, -134), fill(WHITE))
    cv.restore()


def wallet(cv, x, y, s=1.0, t=0.0, mood="smug", legs="stand", spit=False, phase=0.0):
    """ENIC 지갑 캐릭터."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    for sgn in (-1, 1):
        k = math.sin(phase) * 18 * sgn if legs == "run" else 0
        cv.drawLine(sgn * 20, -40, sgn * 22 + k, 0, stroke(INK, 7))
        shape(cv, oval(sgn * 26 + k, 0, 14, 7), INK, 0)
    shape(cv, rrect(-60, -130, 60, -36, 16), (90, 60, 40), 5)
    cv.drawLine(-60, -84, 60, -84, stroke((60, 40, 28), 4))
    text(cv, "ENIC", 0, -52, 24, GOLDISH, TF_TITLE, oc=INK, ow=4)
    shape(cv, rrect(-38, -176, 38, -130, 4), INK, 3)
    shape(cv, rrect(-54, -136, 54, -128, 3), INK, 3)
    ep = 1.3 if mood == "shock" else 1.0
    for sgn in (-1, 1):
        shape(cv, oval(sgn * 20, -106, 11 * ep, 13 * ep), WHITE, 3)
        cv.drawCircle(sgn * 20, -104, 4, fill(INK))
    if mood == "smug":
        cv.drawLine(8, -120, 32, -116, stroke(INK, 4))
        cv.drawLine(-32, -118, -8, -118, stroke(INK, 4))
    if spit:
        for i in range(4):
            k = (t * 2 + i / 4) % 1
            cv.save()
            cv.translate(40 + 120 * k, -90 - 60 * k + 120 * k * k)
            cv.rotate(k * 300)
            shape(cv, rrect(-18, -9, 18, 9, 3), (120, 190, 110), 2)
            text(cv, "£", 0, 6, 16, (40, 90, 40), oc=None)
            cv.restore()
    if mood == "shock":
        for i in range(3):
            k = (t * 1.5 + i / 3) % 1
            sweat(cv, 64 + 10 * k, -130 + 40 * k, 1.0, int(255 * (1 - k)))
    cv.restore()


GOLDISH = (255, 214, 90)


def trophy_icon(cv, x, y, s=1.0, col=(255, 200, 40)):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    for sgn in (-1, 1):
        cv.drawArc(skia.Rect.MakeLTRB(sgn * 30 - 18, -52, sgn * 30 + 18, -18), 0, 360, False, stroke(INK, 11))
        cv.drawArc(skia.Rect.MakeLTRB(sgn * 30 - 18, -52, sgn * 30 + 18, -18), 0, 360, False, stroke(col, 5))
    p = smooth([(-34, -60), (34, -60), (26, -20), (0, -6), (-26, -20)], tension=0.6)
    shape(cv, p, col, 5)
    shape(cv, rrect(-8, -8, 8, 14, 3), col, 4)
    shape(cv, rrect(-24, 12, 24, 24, 4), (120, 70, 40), 4)
    cv.drawArc(skia.Rect.MakeLTRB(-20, -56, 0, -30), 180, 90, False, stroke(WHITE, 4, 200))
    cv.restore()
