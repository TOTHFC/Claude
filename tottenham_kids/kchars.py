"""등장인물(2.5등신 아동 애니 캐릭터), 수탉 꼬꼬, 악당들, 버스.

얼굴은 위키미디어 공용 사진을 참고해 머리 모양·색, 수염, 피부톤을 살렸다.
토트넘 2026/27 킷:
  홈  ─ 흰 바탕에 톤온톤 사선 무늬, 네이비 칼라·소매 끝·옆구리 패널, 빨간 AIA, 네이비 반바지, 흰 양말
  원정 ─ 옵시디언 네이비 바탕에 핑크·보라·주황·파랑 네온 사선, 흰 AIA
"""
import math

import skia

from kengine import (AIA, BLACK, CHEEK, GOLD, INK, NAVY, PINK, RED, WHITE, YELLOW, C, arc, blob, darker, fill,
                     lighter, linear, mix, oval, poly, radial, rrect, shadow, smooth, stroke, sweat, text)

SKINS = {
    "fair": (255, 222, 200), "light": (250, 210, 180), "olive": (236, 190, 150),
    "tan": (214, 160, 118), "brown": (170, 112, 76), "dark": (122, 78, 54),
}

PEOPLE = {
    "dezerbi": dict(name="데 제르비", skin="olive", hair="dz", hc=(40, 32, 30), beard="full", bc=(60, 50, 46),
                    brow=(36, 28, 26), brow_w=7.5, outfit="dz"),
    "fernandes": dict(name="페르난데스", num=18, skin="olive", hair="curly", hc=(34, 26, 24), beard=None,
                      brow=(34, 26, 24)),
    "tonali": dict(name="토날리", num=16, skin="light", hair="long", hc=(52, 38, 30), beard="full", bc=(58, 42, 32),
                   brow=(46, 34, 28)),
    "savinho": dict(name="사비뉴", num=17, skin="brown", hair="curly_short", hc=(28, 22, 20), beard="goatee",
                    bc=(40, 30, 26), brow=(30, 24, 22)),
    "vanhecke": dict(name="반 헤케", num=6, skin="fair", hair="blond_crop", hc=(236, 212, 150), beard=None,
                     brow=(200, 170, 110)),
    "robertson": dict(name="로버트슨", num=3, skin="fair", hair="side_part", hc=(92, 64, 44), beard="stubble",
                      bc=(120, 86, 60), brow=(82, 58, 40)),
    "senesi": dict(name="세네시", num=5, skin="light", hair="curly", hc=(56, 40, 30), beard="stubble",
                   bc=(70, 50, 38), brow=(50, 36, 28)),
    "mudryk": dict(name="무드릭", num=27, skin="fair", hair="blond_shag", hc=(246, 226, 160), beard=None,
                   brow=(190, 160, 110)),
    "marmoush": dict(name="마르무시", num=22, skin="tan", hair="curly", hc=(30, 24, 22), beard="short",
                     bc=(40, 30, 26), brow=(30, 24, 22)),
    "tosin": dict(name="토신", num=4, skin="dark", hair="buzz", hc=(24, 18, 16), beard="short", bc=(24, 18, 16),
                  brow=(24, 18, 16)),
    "gallagher": dict(name="갤러거", num=8, skin="fair", hair="slick_bun", hc=(214, 172, 110), beard="mustache",
                      bc=(190, 150, 96), brow=(170, 130, 86)),
    "vdv": dict(name="반 더 벤", num=37, skin="fair", hair="swept", hc=(130, 96, 66), beard=None,
                brow=(110, 80, 56), captain=True),
    "kinsky": dict(name="킨스키", num=31, skin="fair", hair="side_part", hc=(150, 116, 80), beard=None,
                   brow=(120, 92, 64), outfit="gk"),
    "romero": dict(name="로메로", num=17, skin="tan", hair="flat", hc=(30, 26, 24), beard="stubble",
                   bc=(40, 34, 30), brow=(30, 26, 24)),
    "kane": dict(name="케인", num=9, skin="fair", hair="quiff", hc=(150, 110, 70), beard="stubble",
                 bc=(150, 116, 80), brow=(130, 96, 62), outfit="bayern"),
    "son": dict(name="손흥민", num=7, skin="light", hair="fringe", hc=(26, 22, 22), beard=None,
                brow=(26, 22, 22), outfit="lafc", smile_eyes=True),
}

EYE = (44, 32, 40)

# 프레임마다 make_kids.frame() 이 전체 시간을 넣어 준다: 숨쉬기·자동 눈깜빡임·말할 때 고개 움직임에 쓴다.
CLOCK = 0.0


def _phase(key):
    return (sum(ord(c) for c in str(key)) % 97) / 97 * 6.28


def auto_blink(key, extra=0.0):
    ph = (CLOCK + _phase(key) * 0.5 + extra) % 3.4
    return ph < 0.11


# ------------------------------------------------------------------ 옷

def _shirt_cols(outfit, kit):
    if outfit == "dz":
        return (44, 42, 52), (30, 28, 36), (44, 42, 52)
    if outfit == "gk":
        return (190, 240, 60), (40, 60, 40), (30, 30, 30)
    if outfit == "bayern":
        return (220, 16, 50), (255, 255, 255), (220, 16, 50)
    if outfit == "lafc":
        return (30, 30, 34), (200, 164, 90), (30, 30, 34)
    if outfit == "villager":
        return kit, darker(kit), (70, 90, 150)
    if kit == "away":
        return (28, 30, 50), (28, 30, 50), (28, 30, 50)
    return (250, 250, 252), NAVY, NAVY


def _kit_details(cv, outfit, kit, torso, captain):
    """셔츠 무늬(클립 안에서)."""
    cv.save()
    cv.clipPath(torso, doAntiAlias=True)
    if outfit == "kit" and kit == "home":
        for i in range(-6, 8):  # 톤온톤 사선 무늬
            x = i * 14
            cv.drawLine(x - 40, -40, x + 40, -120, stroke((226, 230, 240), 5))
        cv.drawRect(skia.Rect.MakeLTRB(-40, -110, -27, -40), fill(NAVY))  # 옆구리 패널
        cv.drawRect(skia.Rect.MakeLTRB(27, -110, 40, -40), fill(NAVY))
    elif outfit == "kit" and kit == "away":
        cols = [(255, 80, 170), (160, 100, 255), (255, 150, 50), (70, 180, 255)]
        k = 0
        for i in range(-5, 6):
            for j in range(3):
                x = i * 16 + j * 7
                y = -60 - j * 22 - (i % 2) * 8
                cv.drawLine(x, y, x + 16, y - 16, stroke(cols[k % 4], 3.2))
                k += 1
    elif outfit == "bayern":
        cv.drawRect(skia.Rect.MakeLTRB(-3, -110, 3, -40), fill((255, 255, 255), 90))
    elif outfit == "lafc":
        cv.drawRect(skia.Rect.MakeLTRB(-40, -76, 40, -70), fill((200, 164, 90)))
    elif outfit == "dz":
        for i in range(-4, 5):  # 니트 결
            cv.drawLine(i * 9, -104, i * 9, -44, stroke((56, 54, 66), 2))
    cv.restore()
    if outfit == "kit":
        txt = AIA if kit == "home" else WHITE
        text(cv, "AIA", 0, -66, 17, txt, align="center")
        cv.drawPath(oval(-13, -88, 4, 5), fill(NAVY if kit == "home" else WHITE))  # 엠블럼
        p = skia.Path()  # 스우시
        p.moveTo(9, -88)
        p.quadTo(14, -84, 20, -91)
        cv.drawPath(p, stroke(NAVY if kit == "home" else WHITE, 2))
    elif outfit == "bayern":
        text(cv, "9", 0, -64, 20, WHITE, align="center")
    elif outfit == "lafc":
        text(cv, "7", 0, -62, 18, (200, 164, 90), align="center")
    elif outfit == "gk":
        text(cv, "31", 0, -64, 18, (40, 60, 40), align="center")


def _arm(cv, sx, sy, ang, length, sleeve, skin, glove=None, sleeve_len=0.45):
    """ang: 0=아래, 90=옆, 180=위 (도)."""
    side = 1 if sx > 0 else -1
    a = math.radians(ang)
    ex = sx + side * math.sin(a) * length
    ey = sy + math.cos(a) * length
    mx = sx + (ex - sx) * sleeve_len
    my = sy + (ey - sy) * sleeve_len
    cv.drawLine(sx, sy, ex, ey, stroke(darker(skin, 0.6), 19))
    cv.drawLine(sx, sy, ex, ey, stroke(skin, 14))
    cv.drawLine(sx, sy, mx, my, stroke(darker(sleeve, 0.6), 21))
    cv.drawLine(sx, sy, mx, my, stroke(sleeve, 16))
    hand = glove or skin
    blob(cv, oval(ex, ey, 10, 10), hand, 3)
    return ex, ey


# ------------------------------------------------------------------ 머리카락 / 수염

def _hair_back(cv, style, hc):
    if style == "long":
        blob(cv, smooth([(-64, -10), (-60, 50), (-40, 70), (40, 70), (60, 50), (64, -10), (0, -40)]), hc, 4)
    elif style == "slick_bun":
        blob(cv, oval(0, -64, 20, 16), hc, 4)
    elif style == "blond_shag":
        blob(cv, smooth([(-66, -10), (-64, 34), (-44, 44), (44, 44), (64, 34), (66, -10), (0, -40)]), hc, 4)


def _hair_front(cv, style, hc, t=0.0):
    hl = lighter(hc, 0.3)
    if style == "dz":  # 짧고 삐죽한 검은 머리, 옆은 짧게
        pts = [(-60, -2), (-62, -26), (-52, -48), (-40, -56), (-30, -70), (-18, -60), (-6, -74), (6, -62),
               (18, -74), (28, -60), (42, -66), (48, -50), (58, -38), (62, -18), (60, -2), (50, -30), (30, -40),
               (0, -42), (-30, -40), (-50, -28)]
        blob(cv, smooth(pts, tension=0.8), hc, 4, shade=False)
        cv.drawLine(-20, -58, -8, -48, stroke(hl, 3))
        cv.drawLine(12, -60, 20, -50, stroke(hl, 3))
    elif style in ("curly", "curly_short"):
        r = 13 if style == "curly" else 10
        top = -70 if style == "curly" else -62
        p = skia.Path()
        p.addOval(skia.Rect.MakeLTRB(-60, top + 8, 60, -18))
        for i in range(9):
            a = math.pi + i / 8 * math.pi
            p.addCircle(math.cos(a) * 52, -30 + math.sin(a) * (30 - top * -0.25) * 1.0 + 4, r)
        for x in range(-40, 50, 20):
            p.addCircle(x, top + 12, r)
        p.setFillType(skia.PathFillType.kWinding)
        blob(cv, p, hc, 4, shade=False)
        for x in range(-40, 50, 20):
            arc(cv, x, top + 12, r * 0.5, r * 0.5, 200, 120, hl, 2.5)
    elif style == "long":  # 가운데 가르마 긴 머리
        blob(cv, smooth([(-64, 10), (-62, -34), (-40, -58), (0, -62), (40, -58), (62, -34), (64, 10), (50, -16),
                         (20, -40), (0, -34), (-20, -40), (-50, -16)], tension=0.9), hc, 4, shade=False)
        cv.drawLine(0, -60, 0, -36, stroke(darker(hc, 0.7), 3))
    elif style == "blond_crop":
        blob(cv, smooth([(-60, -16), (-56, -46), (-30, -62), (10, -64), (44, -56), (60, -30), (60, -14), (44, -34),
                         (10, -42), (-30, -38)], tension=0.9), hc, 4, shade=False)
    elif style == "side_part":
        blob(cv, smooth([(-60, -8), (-60, -40), (-36, -62), (0, -66), (40, -60), (62, -36), (62, -10), (48, -34),
                         (14, -44), (-20, -44), (-44, -30)], tension=0.9), hc, 4, shade=False)
        cv.drawLine(-24, -60, -16, -44, stroke(darker(hc, 0.7), 3))
    elif style == "blond_shag":
        blob(cv, smooth([(-64, 4), (-62, -38), (-36, -64), (4, -68), (42, -60), (64, -36), (64, 4), (50, -14),
                         (40, -22), (26, -12), (12, -24), (-4, -12), (-18, -24), (-34, -12), (-50, -18)],
                        tension=0.9), hc, 4, shade=False)
    elif style == "buzz":
        blob(cv, smooth([(-60, -14), (-54, -44), (-26, -60), (26, -60), (54, -44), (60, -14), (40, -36),
                         (0, -44), (-40, -36)], tension=0.9), hc, 3, shade=False)
    elif style == "slick_bun":
        blob(cv, smooth([(-60, -8), (-58, -42), (-30, -62), (20, -64), (52, -50), (62, -24), (60, -6), (48, -30),
                         (20, -44), (-20, -42), (-46, -28)], tension=0.9), hc, 4, shade=False)
        for x in (-30, -10, 10, 30):
            cv.drawLine(x, -42, x + 6, -60, stroke(hl, 2.5))
    elif style == "swept":
        blob(cv, smooth([(-60, -8), (-58, -40), (-30, -64), (16, -66), (50, -54), (64, -28), (62, -8), (40, -26),
                         (10, -34), (-20, -44), (-44, -30)], tension=0.9), hc, 4, shade=False)
    elif style == "flat":
        blob(cv, smooth([(-60, -10), (-56, -44), (-24, -62), (24, -62), (56, -44), (60, -10), (40, -30),
                         (0, -36), (-40, -30)], tension=0.9), hc, 4, shade=False)
    elif style == "quiff":
        blob(cv, smooth([(-60, -10), (-58, -40), (-34, -60), (0, -76), (34, -70), (58, -44), (62, -10), (44, -32),
                         (10, -40), (-24, -40), (-46, -30)], tension=0.9), hc, 4, shade=False)
    elif style == "fringe":  # 손흥민 앞머리
        blob(cv, smooth([(-62, -4), (-60, -38), (-34, -62), (6, -66), (44, -58), (62, -34), (62, -4), (52, -16),
                         (36, -18), (20, -14), (4, -20), (-12, -14), (-28, -20), (-44, -14)], tension=0.9),
             hc, 4, shade=False)
    elif style == "villager_a":
        blob(cv, smooth([(-60, -10), (-56, -44), (-20, -64), (30, -62), (58, -40), (60, -10), (30, -34),
                         (-30, -34)], tension=0.9), hc, 4, shade=False)
    elif style == "villager_b":  # 양갈래
        blob(cv, smooth([(-60, 0), (-58, -40), (-20, -64), (30, -62), (58, -40), (60, 0), (30, -30),
                         (-30, -30)], tension=0.9), hc, 4, shade=False)
        blob(cv, oval(-66, 10, 12, 18), hc, 3)
        blob(cv, oval(66, 10, 12, 18), hc, 3)


def _beard(cv, style, bc, talk):
    if not style:
        return
    if style in ("full", "short"):
        thick = 1.0 if style == "full" else 0.7
        outer = [(-60, -4), (-58, 24), (-40, 48), (0, 60), (40, 48), (58, 24), (60, -4)]
        inner = [(50, 0), (44, 22), (26, 36 + 4 * (1 - thick)), (0, 42 + 4 * (1 - thick)),
                 (-26, 36 + 4 * (1 - thick)), (-44, 22), (-50, 0)]
        blob(cv, smooth(outer + inner, tension=0.7), bc, 2.5, oc=darker(bc, 0.7), shade=False)
        # 콧수염 + 입술 아래 수염
        blob(cv, smooth([(-20, 21), (-9, 16), (0, 18), (9, 16), (20, 21), (11, 24), (0, 22), (-11, 24)]),
             bc, 2, oc=darker(bc, 0.7), shade=False)
        cv.drawPath(oval(0, 44 + talk * 6, 7, 5), fill(bc))
        for x, y in ((-46, 26), (-30, 44), (30, 44), (46, 26), (-12, 52), (12, 52)):
            cv.drawLine(x, y, x + 2, y + 5, stroke(lighter(bc, 0.35), 2))
    elif style == "goatee":
        blob(cv, oval(0, 46, 12, 8), bc, 2, shade=False)
        cv.drawLine(-14, 20, 14, 20, stroke(bc, 3))
    elif style == "stubble":
        for i in range(26):
            a = math.pi * (0.1 + 0.8 * i / 25)
            x, y = math.cos(a) * 44, 24 + math.sin(a) * 26
            cv.drawPath(oval(x, y, 1.6, 1.6), fill(bc, 170))
    elif style == "mustache":
        blob(cv, smooth([(-20, 20), (-8, 14), (0, 16), (8, 14), (20, 20), (10, 23), (0, 21), (-10, 23)]),
             bc, 2, shade=False)


# ------------------------------------------------------------------ 얼굴

def face(cv, mood="smile", talk=0.0, blink=False, look=(0, 0), brow=(40, 30, 30), brow_w=6.0, smile_eyes=False,
         skin=(250, 210, 180), beard=None, bc=None):
    lx, ly = look
    # 볼터치
    cv.drawPath(oval(-36, 16, 11, 7), fill(CHEEK, 110))
    cv.drawPath(oval(36, 16, 11, 7), fill(CHEEK, 110))
    # 눈
    for sx in (-1, 1):
        ex, ey = sx * 22 + lx, -2 + ly
        if blink or mood in ("happy", "laugh") or (smile_eyes and mood in ("smile", "talk")):
            arc(cv, ex, ey + 3, 9, 7, 200, 140, EYE, 4)
        elif mood in ("cry",):
            arc(cv, ex, ey, 9, 6, 20, 140, EYE, 4)
            cv.drawPath(oval(ex, ey + 18, 4, 8), fill((140, 200, 255), 220))
        elif mood == "shock":
            cv.drawPath(oval(ex, ey, 11, 12), fill(WHITE))
            cv.drawPath(oval(ex, ey, 11, 12), stroke(EYE, 2.5))
            cv.drawPath(oval(ex, ey, 3.5, 3.5), fill(EYE))
        elif mood == "dizzy":
            cv.drawLine(ex - 7, ey - 7, ex + 7, ey + 7, stroke(EYE, 3.5))
            cv.drawLine(ex - 7, ey + 7, ex + 7, ey - 7, stroke(EYE, 3.5))
        else:
            cv.drawPath(oval(ex, ey, 8.5, 11), fill(EYE))
            cv.drawPath(oval(ex + 2.8, ey - 4.2, 3.4, 3.8), fill(WHITE))
            cv.drawPath(oval(ex - 2.6, ey + 4.2, 1.8, 1.8), fill(WHITE))
    # 눈썹: angry 는 안쪽이 내려가고, sad 계열은 안쪽이 올라간다
    tilt = {"angry": 6, "sad": -6, "cry": -6, "sweat": -4, "worry": -6, "shock": -3}.get(mood, 0)
    for sx in (-1, 1):
        by = -22 - (6 if mood == "shock" else 0)
        cv.drawLine(sx * 12 + lx, by + tilt, sx * 32 + lx, by - tilt * 0.5 - 2, stroke(brow, brow_w))
    # 코
    cv.drawPath(oval(0, 10, 4.5, 3.2), fill(darker(skin, 0.85)))
    # 수염(입 뒤)
    _beard(cv, beard, bc or brow, talk)
    # 입
    my = 30
    if talk > 0.08 or mood in ("shock", "laugh", "cheer"):
        o = max(talk, 0.55 if mood in ("shock", "laugh", "cheer") else 0)
        rx, ry = 9 + 3 * o, 3 + 10 * o
        cv.drawPath(oval(0, my, rx, ry), fill((150, 40, 50)))
        cv.drawPath(oval(0, my + ry * 0.45, rx * 0.6, ry * 0.4), fill((255, 120, 130)))
        cv.drawPath(oval(0, my, rx, ry), stroke((110, 40, 40), 2.5))
    elif mood in ("sad", "cry", "worry", "sweat"):
        arc(cv, 0, my + 8, 10, 7, 200, 140, (110, 40, 40), 3.5)
    elif mood == "angry":
        cv.drawLine(-9, my + 2, 9, my + 2, stroke((110, 40, 40), 3.5))
    else:
        arc(cv, 0, my - 5, 11, 9, 20, 140, (110, 40, 40), 3.5)


# ------------------------------------------------------------------ 사람

def person(cv, key, x, y, s=1.0, mood="smile", talk=0.0, blink=None, arms=(10, 10), kit="home", look=(0, 0),
           flip=False, bob=0.0, squash=0.0, tilt=0.0, walk=None, spec=None, prop=None):
    """발 가운데가 (x, y). arms=(왼팔각, 오른팔각). walk=걷기 위상.
    blink=None 이면 저절로 눈을 깜빡이고, 가만히 있어도 숨을 쉬며, 말할 때는 고개와 팔이 조금씩 움직인다."""
    sp = dict(spec or PEOPLE[key])
    ph = _phase(key or sp.get("hair", "") + str(sp.get("shirt", "")))
    if blink is None:
        blink = auto_blink(key or ph)
    breath = math.sin(CLOCK * 2.3 + ph)
    head_rot = math.sin(CLOCK * 1.1 + ph) * 1.5 + (math.sin(CLOCK * 9 + ph) * 3 * min(1, talk * 2) if talk > 0.05 else 0)
    if talk > 0.05:  # 말할 때 손짓
        g = math.sin(CLOCK * 5 + ph) * 8 * min(1, talk * 2)
        arms = (arms[0] + (g if arms[0] < 60 else 0), arms[1] + (-g if arms[1] < 60 else 0))
    outfit = sp.get("outfit", "kit")
    skin = SKINS[sp["skin"]]
    shirt, trim, shorts = _shirt_cols(outfit, sp.get("shirt", kit))
    cv.save()
    cv.translate(x, y)
    shadow(cv, 0, 0, 46 * s)
    cv.scale(s * (-1 if flip else 1), s)
    cv.translate(0, -bob)
    cv.scale(1 + squash * 0.12, 1 - squash * 0.12)
    cv.rotate(tilt)
    # 다리 (숨쉬기는 다리 위부터)
    lk = math.sin(walk * math.pi * 2) * 7 if walk is not None else 0
    sock = WHITE if outfit == "kit" and kit == "home" else (28, 30, 50) if outfit == "kit" else (
        (40, 40, 44) if outfit in ("dz", "lafc") else (230, 230, 230) if outfit != "villager" else (60, 60, 80))
    for sx, dy in ((-1, lk), (1, -lk)):
        lx = sx * 13
        leg = skin if outfit != "dz" else (36, 36, 44)
        cv.drawLine(lx, -40, lx, -12 + dy * 0.3 - max(0, dy), stroke(darker(leg, 0.6), 19))
        cv.drawLine(lx, -40, lx, -12 + dy * 0.3 - max(0, dy), stroke(leg, 14))
        if outfit != "dz":
            cv.drawLine(lx, -26, lx, -12 - max(0, dy), stroke(darker(sock, 0.7), 18))
            cv.drawLine(lx, -26, lx, -12 - max(0, dy), stroke(sock, 13))
            if outfit == "kit":
                cv.drawLine(lx - 6, -26, lx + 6, -26, stroke(NAVY if kit == "home" else (255, 80, 170), 3))
        shoe = (40, 40, 48) if outfit == "dz" else (255, 255, 255) if outfit == "villager" else (
            (250, 210, 60) if kit == "home" else (255, 90, 170))
        blob(cv, oval(lx + sx * 4, -6 - max(0, dy), 15, 8.5), shoe, 3)
    cv.save()
    cv.translate(0, -40)
    cv.scale(1, 1 + breath * 0.012)
    cv.translate(0, 40)
    # 반바지/바지
    blob(cv, rrect(-31, -60, 31, -32, 10), shorts, 3, shade=False)
    cv.drawLine(0, -46, 0, -32, stroke(darker(shorts, 0.7), 2))
    # 팔 뒤쪽 (오른팔)
    al, ar = arms
    # 몸통
    torso = smooth([(-28, -104), (-34, -80), (-35, -56), (0, -52), (35, -56), (34, -80), (28, -104), (0, -108)],
                   tension=0.8)
    blob(cv, torso, shirt, 4, oc=darker(shirt, 0.55) if shirt != (250, 250, 252) else (150, 156, 176))
    _kit_details(cv, outfit, sp.get("shirt", kit), torso, sp.get("captain"))
    if outfit in ("kit", "gk"):
        arc(cv, 0, -106, 14, 10, 20, 140, trim, 5)  # 칼라
    elif outfit == "dz":
        arc(cv, 0, -106, 15, 9, 10, 160, (26, 26, 32), 5)
    # 팔
    sleeve = shirt
    glove = (240, 250, 120) if outfit == "gk" else None
    hands = []
    for sx, ang in ((-1, al), (1, ar)):
        slen = 0.9 if outfit in ("dz", "gk") else 0.42
        hands.append(_arm(cv, sx * 30, -96, ang, 40, sleeve, skin, glove, slen))
    if sp.get("captain"):
        ex, ey = hands[0]
        cv.drawLine(-30 + (ex + 30) * 0.3, -96 + (ey + 96) * 0.3, -30 + (ex + 30) * 0.42, -96 + (ey + 96) * 0.42,
                    stroke((255, 190, 40), 9))
    if outfit == "dz":  # 팔찌
        ex, ey = hands[1]
        cv.drawPath(oval(30 + (ex - 30) * 0.85, -96 + (ey + 96) * 0.85, 7, 4), stroke((140, 110, 80), 3))
    if prop:
        prop(cv, hands)
    # 머리
    cv.save()
    cv.translate(0, -160 - breath * 1.2)
    cv.rotate(head_rot)
    hc = sp["hc"]
    _hair_back(cv, sp["hair"], hc)
    for sx in (-1, 1):
        blob(cv, oval(sx * 60, 4, 11, 13), skin, 3, oc=darker(skin, 0.62))
    head = smooth([(-62, -6), (-58, -40), (-30, -58), (0, -60), (30, -58), (58, -40), (62, -6), (58, 26),
                   (38, 50), (0, 58), (-38, 50), (-58, 26)], tension=0.95)
    blob(cv, head, skin, 4, oc=darker(skin, 0.62))
    face(cv, mood, talk, blink, look, sp.get("brow", (40, 30, 30)), sp.get("brow_w", 6.0),
         sp.get("smile_eyes", False), skin, sp.get("beard"), sp.get("bc"))
    _hair_front(cv, sp["hair"], hc)
    if mood in ("sweat", "worry", "shock"):
        sweat(cv, 58, -34, 1.1)
    cv.restore()
    cv.restore()
    cv.restore()


def villager(cv, i, x, y, s=1.0, mood="angry", talk=0.0, arms=(150, 150), bob=0.0, sign=None, t=0.0, look=None):
    """토트넘 마을 사람들(팬). 네이비·흰 목도리."""
    hairs = ["villager_a", "villager_b", "villager_a", "buzz", "villager_b", "curly"]
    hcs = [(90, 60, 40), (30, 24, 22), (220, 180, 100), (40, 30, 26), (160, 80, 50), (30, 24, 22)]
    skins = ["light", "fair", "tan", "dark", "light", "olive"]
    tops = [(120, 180, 250), (255, 170, 190), (140, 210, 140), (250, 200, 90), (200, 160, 240), (255, 150, 110)]
    sp = dict(name="팬", skin=skins[i % 6], hair=hairs[i % 6], hc=hcs[i % 6], beard=None, brow=darker(hcs[i % 6], 0.8),
              outfit="villager", shirt=tops[i % 6])
    if look:  # 할아버지(흰머리)·아주머니(뽀글 파마) 같은 모습 바꾸기
        sp.update(look)

    def scarf(cv, hands):
        cv.drawLine(-24, -104, 24, -104, stroke(NAVY, 12))
        for k in range(-2, 3):
            cv.drawLine(k * 10, -110, k * 10, -98, stroke(WHITE, 3))
        if sign:
            ex, ey = hands[1]
            cv.drawLine(ex, ey, ex, ey - 60, stroke((150, 100, 60), 6))
    person(cv, None, x, y, s, mood, talk, None, arms, "home", bob=bob, spec=sp, prop=scarf)


# ------------------------------------------------------------------ 수탉 꼬꼬

def rooster(cv, x, y, s=1.0, mood="smile", talk=0.0, flap=0.0, flip=False, bob=0.0, blink=None, ball=False,
            tilt=0.0):
    if blink is None:
        blink = auto_blink("koko")
    bob += (math.sin(CLOCK * 2.6) + 1) * 1.5
    if talk > 0.05:
        tilt += math.sin(CLOCK * 10) * 4 * min(1, talk * 2)
    cv.save()
    cv.translate(x, y)
    shadow(cv, 0, 0, 40 * s)
    cv.scale(s * (-1 if flip else 1), s)
    cv.translate(0, -bob)
    cv.rotate(tilt)
    if ball:
        blob(cv, oval(0, -26, 28, 28), WHITE, 3, oc=(80, 80, 90))
        for a in range(0, 360, 72):
            r = math.radians(a + 18)
            cv.drawPath(oval(math.cos(r) * 16, -26 + math.sin(r) * 16, 6, 6), fill(NAVY))
        cv.drawPath(oval(0, -26, 7, 7), fill(NAVY))
        cv.translate(0, -48)
    # 다리
    for sx in (-1, 1):
        cv.drawLine(sx * 12, -30, sx * 13, -4, stroke((230, 140, 40), 6))
        for d in (-8, 0, 8):
            cv.drawLine(sx * 13, -4, sx * 13 + d, 2, stroke((230, 140, 40), 4))
    # 꼬리(네이비)
    for i, (dx, dy, r) in enumerate(((-52, -92, 18), (-58, -72, 16), (-50, -56, 14))):
        blob(cv, smooth([(-30, -60), (dx - 6, dy - r), (dx - 16, dy + r * 0.2), (-34, -48)], tension=1.0),
             (40, 60, 130) if i != 1 else (60, 90, 170), 3)
    # 몸통
    blob(cv, oval(0, -58, 40, 34), WHITE, 4, oc=(170, 170, 190))
    # 날개
    cv.save()
    cv.translate(8, -60)
    cv.rotate(-flap * 45)
    blob(cv, smooth([(-18, -6), (4, -16), (26, -4), (18, 14), (-4, 16)]), (238, 240, 250), 3, oc=(170, 170, 190))
    cv.restore()
    # 머리
    blob(cv, oval(10, -104, 26, 26), WHITE, 4, oc=(170, 170, 190))
    # 볏
    blob(cv, smooth([(-6, -122), (-6, -140), (4, -134), (10, -148), (18, -134), (28, -142), (26, -122)],
                    tension=0.8), RED, 3)
    # 부리
    op = talk * 10
    blob(cv, poly([(32, -106 - op * 0.3), (50, -100), (32, -96)]), (255, 190, 40), 2.5)
    blob(cv, poly([(32, -96), (46, -94 + op), (32, -92)]), (240, 160, 30), 2.5)
    blob(cv, oval(34, -84, 6, 9), RED, 2.5)  # 턱볏
    # 눈
    if blink or mood in ("happy", "laugh"):
        arc(cv, 16, -106, 6, 5, 200, 140, EYE, 3.5)
    elif mood == "cry":
        arc(cv, 16, -106, 6, 4, 20, 140, EYE, 3.5)
        cv.drawPath(oval(18, -94, 3, 6), fill((140, 200, 255)))
    elif mood == "shock":
        cv.drawPath(oval(16, -106, 8, 9), fill(WHITE))
        cv.drawPath(oval(16, -106, 8, 9), stroke(EYE, 2))
        cv.drawPath(oval(16, -106, 2.5, 2.5), fill(EYE))
    else:
        cv.drawPath(oval(16, -106, 6, 8), fill(EYE))
        cv.drawPath(oval(18, -109, 2.4, 2.6), fill(WHITE))
    cv.drawPath(oval(20, -92, 6, 4), fill(CHEEK, 110))
    # 네이비 스카프
    cv.drawPath(smooth([(-10, -86), (14, -80), (34, -86), (30, -76), (8, -72), (-12, -78)]), fill(NAVY))
    cv.restore()


# ------------------------------------------------------------------ 악당들

def _villain_eyes(cv, x, y, gap, r, mood, blink=False):
    for sx in (-1, 1):
        ex = x + sx * gap
        if blink or mood == "sleep":
            arc(cv, ex, y, r, r * 0.6, 20, 140, EYE, 3.5)
            continue
        cv.drawPath(oval(ex, y, r, r * 1.15), fill(WHITE))
        cv.drawPath(oval(ex, y, r, r * 1.15), stroke(EYE, 2.5))
        cv.drawPath(oval(ex + sx * -2, y + 2, r * 0.5, r * 0.6), fill(EYE))
        cv.drawPath(oval(ex + sx * -2 + 2, y - 1, r * 0.18, r * 0.18), fill(WHITE))
        if mood in ("angry", "evil"):
            cv.drawLine(ex - r * 1.1 * sx * -1, y - r * 1.6, ex + r * 1.1 * sx * -1 * -1, y - r * 0.9 - 2,
                        stroke(EYE, 4))


def _grin(cv, x, y, w, talk, mood):
    if mood == "sleep":
        cv.drawPath(oval(x, y, 6, 4 + talk * 4), fill((120, 40, 50)))
        return
    p = skia.Path()
    p.moveTo(x - w, y - 2)
    p.quadTo(x, y + 14 + talk * 14, x + w, y - 2)
    p.quadTo(x, y + 4, x - w, y - 2)
    cv.drawPath(p, fill((120, 30, 40)))
    cv.drawPath(p, stroke(EYE, 2.5))
    for k in (-0.5, 0.5):  # 송곳니
        cv.drawPath(poly([(x + w * k - 4, y + 1), (x + w * k + 4, y + 1), (x + w * k, y + 9)]), fill(WHITE))


def bee(cv, x, y, s=1.0, t=0.0, mood="angry", talk=0.0, flip=False):
    """브렌트포드 벌: 빨강·흰 줄무늬 몸통."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s * (-1 if flip else 1), s)
    wing = math.sin(t * 60) * 0.5 + 0.5
    for sx in (-1, 1):
        cv.save()
        cv.translate(sx * 20, -60)
        cv.rotate(sx * (-20 - wing * 30))
        cv.drawPath(oval(sx * 28, -20, 30, 18), fill((220, 240, 255), 190))
        cv.drawPath(oval(sx * 28, -20, 30, 18), stroke((120, 160, 200), 2.5))
        cv.restore()
    body = oval(0, -30, 58, 44)
    blob(cv, body, (255, 255, 255), 4, oc=(150, 30, 40))
    cv.save()
    cv.clipPath(body, doAntiAlias=True)
    for k in (-26, 4, 34):
        cv.drawRect(skia.Rect.MakeLTRB(-70 + k * 0, -80, 70, -80), fill(RED))
        cv.drawRect(skia.Rect.MakeLTRB(k - 10, -80, k + 6, 20), fill((225, 30, 45)))
    cv.restore()
    blob(cv, poly([(52, -24), (82, -30), (54, -38)]), (60, 50, 60), 2)
    blob(cv, oval(-50, -64, 34, 32), (255, 214, 60), 4, oc=(160, 110, 20))  # 머리
    for sx in (-1, 1):
        cv.drawLine(-50 + sx * 12, -92, -50 + sx * 22, -114, stroke(BLACK, 3))
        cv.drawPath(oval(-50 + sx * 22, -116, 6, 6), fill(BLACK))
    _villain_eyes(cv, -52, -70, 13, 9, mood)
    _grin(cv, -52, -50, 14, talk, mood)
    cv.restore()


def magpie(cv, x, y, s=1.0, t=0.0, mood="evil", talk=0.0, flip=False, bag=True):
    """뉴캐슬 까치: 흑백. 돈주머니(토날리 이적료)를 끌어안음."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s * (-1 if flip else 1), s)
    blob(cv, smooth([(30, -60), (90, -40), (96, -24), (40, -40)]), (30, 30, 40), 3)  # 꼬리
    blob(cv, oval(0, -56, 46, 48), (36, 36, 46), 4, oc=(10, 10, 16))
    blob(cv, oval(4, -40, 28, 30), WHITE, 3, oc=(160, 160, 170))
    blob(cv, oval(-6, -118, 34, 32), (36, 36, 46), 4, oc=(10, 10, 16))
    blob(cv, poly([(-36, -118), (-62, -112), (-36, -104)]), (60, 60, 70), 2)
    _villain_eyes(cv, -8, -124, 12, 8, mood)
    if bag:
        blob(cv, smooth([(-20, -30), (-44, -20), (-50, 10), (-20, 20), (10, 10), (4, -20)]), (230, 190, 90), 4,
             oc=(150, 110, 40))
        text(cv, "£", -22, 4, 28, (150, 110, 40), align="center")
    for sx in (-1, 1):
        cv.drawLine(sx * 12, -10, sx * 14, 0, stroke((230, 140, 40), 5))
    cv.restore()


def tree(cv, x, y, s=1.0, t=0.0, mood="angry", talk=0.0):
    """노팅엄 포레스트 나무: 빨간 잎."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    blob(cv, rrect(-26, -120, 26, 0, 12), (150, 100, 60), 4)
    p = skia.Path()
    for dx, dy, r in ((0, -190, 70), (-60, -160, 50), (60, -160, 50), (-36, -220, 48), (36, -220, 48),
                      (0, -250, 40)):
        p.addCircle(dx, dy + math.sin(t * 3 + dx) * 2, r)
    p.setFillType(skia.PathFillType.kWinding)
    blob(cv, p, (220, 40, 50), 5, oc=(130, 20, 30))
    _villain_eyes(cv, 0, -80, 13, 9, mood)
    _grin(cv, 0, -52, 14, talk, mood)
    cv.restore()


def toffee(cv, x, y, s=1.0, t=0.0, mood="sleep", talk=0.0):
    """에버튼 잠꾸러기 사탕: 파란 포장지 + 수면 모자."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    for sx in (-1, 1):
        blob(cv, poly([(sx * 44, -50), (sx * 84, -76), (sx * 76, -50), (sx * 84, -24)]), (40, 90, 200), 3)
    blob(cv, oval(0, -50, 50, 40), (60, 120, 230), 4)
    cv.drawLine(-30, -80, 30, -20, stroke(WHITE, 5, 150))
    blob(cv, poly([(-30, -84), (26, -84), (40, -128)]), (250, 250, 255), 3, oc=(120, 120, 160))
    cv.drawPath(oval(40, -130, 8, 8), fill(WHITE))
    _villain_eyes(cv, 0, -54, 15, 9, mood)
    _grin(cv, 0, -32, 10, talk, mood)
    cv.restore()


def lion(cv, x, y, s=1.0, t=0.0, mood="evil", talk=0.0):
    """아스톤 빌라 사자: 클라렛 갈기."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    p = skia.Path()
    for i in range(14):
        a = i / 14 * 2 * math.pi
        p.addCircle(math.cos(a) * 62, -90 + math.sin(a) * 62, 26)
    p.setFillType(skia.PathFillType.kWinding)
    blob(cv, p, (130, 30, 60), 4)
    blob(cv, oval(0, -90, 60, 56), (255, 200, 90), 4)
    for sx in (-1, 1):
        blob(cv, oval(sx * 44, -138, 14, 14), (255, 200, 90), 3)
    _villain_eyes(cv, 0, -100, 20, 10, mood)
    blob(cv, oval(0, -76, 12, 8), (150, 80, 60), 2)
    _grin(cv, 0, -60, 20, talk, mood)
    blob(cv, rrect(-40, -40, 40, 0, 20), (140, 200, 250), 4)
    cv.restore()


def hammer(cv, x, y, s=1.0, rot=0.0, mood="shock"):
    """웨스트햄 망치."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    cv.rotate(rot)
    blob(cv, rrect(-8, -20, 8, 70, 6), (190, 140, 90), 3)
    blob(cv, rrect(-46, -56, 46, -16, 12), (130, 40, 70), 4)
    blob(cv, rrect(-46, -56, -30, -16, 6), (130, 190, 230), 3)
    blob(cv, rrect(30, -56, 46, -16, 6), (130, 190, 230), 3)
    for sx in (-1, 1):
        cv.drawPath(oval(sx * 10, -38, 6, 7), fill(WHITE))
        cv.drawPath(oval(sx * 10, -38, 2.5, 2.5), fill(EYE))
    cv.drawPath(oval(0, -24, 5, 5), fill((110, 30, 40)))
    cv.restore()


def devil(cv, x, y, s=1.0, t=0.0, a=255):
    """맨유 붉은 악마 실루엣."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    col = (200, 20, 30)
    blob(cv, smooth([(-40, 0), (-50, -80), (-30, -120), (30, -120), (50, -80), (40, 0)]), col, 4, a=a)
    blob(cv, oval(0, -150, 40, 38), col, 4, a=a)
    for sx in (-1, 1):
        blob(cv, poly([(sx * 20, -180), (sx * 40, -214), (sx * 36, -172)]), col, 3, a=a)
        cv.drawPath(oval(sx * 14, -154, 8, 5), fill(YELLOW, a))
    cv.drawLine(60, 20, 60, -170, stroke((60, 40, 40), 6, a))
    cv.drawPath(poly([(40, -170), (60, -210), (80, -170), (70, -180), (60, -168), (50, -180)]),
                fill((60, 40, 40), a))
    _grin(cv, 0, -132, 16, 0.2 + 0.2 * math.sin(t * 5), "evil")
    cv.restore()


# ------------------------------------------------------------------ 버스

def bus(cv, x, y, s=1.0, t=0.0, talk=0.0, door=0.0, mood="smile"):
    """꼬마버스 느낌의 '새 친구 버스'."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    shadow(cv, 0, 0, 180)
    blob(cv, rrect(-190, -190, 190, -30, 40), (80, 150, 240), 5, oc=(30, 60, 140))
    blob(cv, rrect(-190, -80, 190, -30, 20), (40, 90, 190), 0, shade=False)
    for i in range(3):  # 창문
        blob(cv, rrect(-40 + i * 74, -170, 20 + i * 74, -110, 14), (210, 240, 255), 4, oc=(30, 60, 140))
    # 문
    blob(cv, rrect(-150, -160, -80, -40, 10), (200, 230, 255), 4, oc=(30, 60, 140))
    if door > 0:
        cv.drawPath(rrect(-150, -160, -150 + 70 * door, -40, 10), fill((30, 40, 70)))
    # 얼굴(앞쪽 = 왼쪽)
    for sx in (-1, 1):
        ex = -175 + sx * 0
    cv.drawPath(oval(-172, -120, 14, 18), fill(WHITE))
    cv.drawPath(oval(-172, -120, 14, 18), stroke(EYE, 3))
    cv.drawPath(oval(-176, -118, 6, 8), fill(EYE))
    cv.drawPath(oval(-174, -122, 2, 2.5), fill(WHITE))
    arc(cv, -176, -86, 14, 10 + talk * 8, 30, 120, (110, 40, 40), 4)
    blob(cv, oval(-190, -60, 12, 12), YELLOW, 3)  # 전조등
    text(cv, "새 친구 버스", 36, -48, 24, WHITE, align="center", outline=(30, 60, 140), ow=6)
    for wx in (-110, 110):
        rot = t * 360
        cv.save()
        cv.translate(wx, -28)
        blob(cv, oval(0, 0, 30, 30), (50, 50, 60), 4)
        cv.drawPath(oval(0, 0, 12, 12), fill((200, 200, 210)))
        cv.rotate(rot)
        cv.drawLine(-10, 0, 10, 0, stroke((120, 120, 130), 3))
        cv.restore()
    cv.restore()
