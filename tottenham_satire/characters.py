"""인물 도트 캐리커처(얼굴 초상화 + 2등신 전신)와 상대팀 마스코트.

얼굴은 사진이 아니라 각 인물의 알려진 특징(머리 모양·색, 수염 등)을 살린 도트 캐리커처다.
선수 유니폼은 토트넘 2026/27 나이키 홈 킷을 따른다:
  흰색(릴리화이트) 바탕 + 1980년대 험멜풍 은은한 사선 무늬, 네이비 칼라·소매 끝·옆구리 패널,
  네이비 스우시·엠블럼, 빨간 AIA 로고, 네이비(Binary Blue) 반바지, 흰 양말.
"""
import math

from PIL import Image, ImageDraw

from engine import (AIA_RED, BINARY, BLACK, CLARET, DRED, F16, GOLD, GRAY, NAVY, RED,
                    WHITE, YELLOW, add_outline)

TONAL = (226, 228, 240)   # 홈 킷 사선 무늬(톤온톤)
TRACK = (22, 32, 78)      # 감독 트레이닝복

# 인물 사양 --------------------------------------------------------------------
PEOPLE = {
    # 감독
    "frank":   dict(name="토마스 프랑크", short="프랑크", skin=(240, 192, 162), hair="bald",
                    hc=(176, 164, 150), beard="stubble", bc=(170, 150, 135), brow=(150, 130, 110),
                    outfit="track", mood="grin"),
    "tudor":   dict(name="이고르 투도르", short="투도르", skin=(226, 178, 144), hair="short",
                    hc=(70, 62, 58), beard="stubble", bc=(90, 80, 72), brow=(50, 42, 38),
                    outfit="track", mood="frown", thick=True),
    "dezerbi": dict(name="로베르토 데 제르비", short="데 제르비", skin=(226, 178, 144), hair="wavy",
                    hc=(34, 28, 24), beard="full", bc=(34, 28, 24), brow=(30, 24, 20),
                    outfit="track", mood="smile", thick=True),
    # 선수 (등번호는 2026/27 구단 발표 기준)
    "fernandes": dict(name="마테우스 페르난데스", short="페르난데스", num=18, skin=(214, 166, 128),
                      hair="curly", hc=(40, 30, 26), beard="none", brow=(40, 30, 26), outfit="kit"),
    "tonali":    dict(name="산드로 토날리", short="토날리", num=16, skin=(230, 182, 148), hair="long",
                      hc=(48, 36, 28), beard="full", bc=(48, 36, 28), brow=(40, 30, 24), outfit="kit"),
    "robertson": dict(name="앤디 로버트슨", short="로버트슨", num=3, skin=(244, 200, 176), hair="short",
                      hc=(118, 78, 48), beard="full", bc=(150, 92, 52), brow=(110, 72, 44), outfit="kit"),
    "vanhecke":  dict(name="얀 폴 반 헤케", short="반 헤케", num=6, skin=(222, 176, 146), hair="short",
                      hc=(52, 40, 32), beard="stubble", bc=(80, 64, 52), brow=(50, 38, 30), outfit="kit"),
    "senesi":    dict(name="마르코스 세네시", short="세네시", num=5, skin=(232, 186, 152), hair="short",
                      hc=(36, 28, 24), beard="full", bc=(36, 28, 24), brow=(36, 28, 24), outfit="kit"),
    "mudryk":    dict(name="미하일로 무드리크", short="무드리크", num=27, skin=(246, 206, 182), hair="blonde",
                      hc=(242, 222, 150), beard="none", brow=(180, 150, 100), outfit="kit"),
    "adarabioyo": dict(name="토신 아다라비오요", short="아다라비오요", num="?", skin=(118, 78, 54), hair="buzz",
                       hc=(24, 18, 16), beard="stubble", bc=(24, 18, 16), brow=(24, 18, 16), outfit="kit"),
    "gallagher": dict(name="코너 갤러거", short="갤러거", num=8, skin=(246, 202, 178), hair="short",
                      hc=(150, 108, 70), beard="none", brow=(130, 92, 60), outfit="kit"),
}


def _shade(c, k=0.82):
    return tuple(int(v * k) for v in c)


def _light(c, k=1.12):
    return tuple(min(255, int(v * k)) for v in c)


# 얼굴 초상화 (32x32 도트) ----------------------------------------------------------

def _portrait(key, mood=None):
    p = PEOPLE[key]
    mood = mood or p.get("mood", "smile")
    skin, sd, hc = p["skin"], _shade(p["skin"]), p["hc"]
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 어깨/옷
    if p["outfit"] == "kit":
        d.rectangle([3, 27, 28, 31], fill=WHITE)
        for x in range(3, 29):
            for y in range(27, 32):
                if (x + y) % 5 == 0:
                    d.point((x, y), fill=TONAL)
        d.rectangle([3, 29, 4, 31], fill=NAVY)
        d.rectangle([27, 29, 28, 31], fill=NAVY)
        d.polygon([(12, 27), (15, 30), (16, 30), (19, 27)], fill=NAVY)  # 네이비 칼라
        d.rectangle([8, 29, 9, 30], fill=NAVY)       # 엠블럼
        d.line([(22, 30), (23, 29)], fill=NAVY)      # 스우시
        d.rectangle([12, 31, 19, 31], fill=AIA_RED)  # AIA
    else:
        d.rectangle([3, 27, 28, 31], fill=TRACK)
        d.line([(15, 28), (15, 31)], fill=WHITE)
        d.line([(12, 27), (15, 28)], fill=WHITE)
        d.line([(19, 27), (16, 28)], fill=WHITE)
        d.point((22, 29), fill=WHITE)
    d.rectangle([13, 23, 18, 27], fill=sd)
    if p["hair"] == "long":
        d.rectangle([6, 8, 25, 28], fill=hc)
    d.rectangle([6, 14, 8, 19], fill=skin)
    d.rectangle([23, 14, 25, 19], fill=skin)
    d.point((7, 16), fill=sd)
    d.point((24, 16), fill=sd)
    d.ellipse([8, 4, 23, 26], fill=skin)
    # 머리카락
    h = p["hair"]
    if h == "bald":
        d.rectangle([8, 11, 9, 16], fill=hc)
        d.rectangle([22, 11, 23, 16], fill=hc)
        d.line([(12, 6), (14, 6)], fill=_light(skin, 1.08))
    elif h in ("short", "buzz"):
        d.chord([8, 3, 23, 17 if h == "short" else 13], 180, 360, fill=hc)
        d.rectangle([8, 9, 9, 15], fill=hc)
        d.rectangle([22, 9, 23, 15], fill=hc)
        if h == "short":
            d.line([(11, 5), (19, 5)], fill=_light(hc, 1.3))
    elif h == "curly":
        d.chord([7, 1, 24, 19], 180, 360, fill=hc)
        d.rectangle([7, 8, 9, 14], fill=hc)
        d.rectangle([22, 8, 24, 14], fill=hc)
        for (x, y) in ((10, 3), (13, 2), (16, 3), (19, 2), (21, 5), (9, 6), (12, 5), (15, 5), (18, 6)):
            d.point((x, y), fill=_light(hc, 1.6))
    elif h == "wavy":
        d.chord([7, 1, 24, 19], 180, 360, fill=hc)
        d.ellipse([9, 0, 16, 6], fill=hc)
        d.ellipse([15, 0, 23, 6], fill=hc)
        d.rectangle([7, 8, 9, 15], fill=hc)
        d.rectangle([22, 8, 24, 15], fill=hc)
        d.line([(12, 3), (18, 2)], fill=_light(hc, 2.2))
    elif h == "long":
        d.chord([7, 2, 24, 18], 180, 360, fill=hc)
        d.rectangle([7, 8, 9, 24], fill=hc)
        d.rectangle([22, 8, 24, 24], fill=hc)
        d.line([(15, 3), (15, 6)], fill=_shade(hc, 0.6))
    elif h == "blonde":
        d.chord([8, 2, 23, 17], 180, 360, fill=hc)
        d.ellipse([11, 0, 22, 7], fill=hc)
        d.rectangle([8, 9, 9, 13], fill=_shade(hc, 0.7))
        d.rectangle([22, 9, 23, 13], fill=_shade(hc, 0.7))
        d.line([(13, 2), (19, 2)], fill=_light(hc, 1.1))
    # 수염
    b = p.get("beard", "none")
    if b == "full":
        bc = p["bc"]
        d.chord([8, 8, 23, 27], 15, 165, fill=bc)
        d.rectangle([8, 17, 9, 21], fill=bc)
        d.rectangle([22, 17, 23, 21], fill=bc)
        d.rectangle([12, 19, 19, 20], fill=bc)
    elif b == "stubble":
        for y in range(19, 26):
            for x in range(9, 23):
                if (x * 3 + y * 5) % 7 == 0 and im.getpixel((x, y))[:3] == skin:
                    d.point((x, y), fill=_shade(skin, 0.86))
    # 눈썹/눈
    brow = p["brow"]
    thick = p.get("thick", False)
    if mood in ("angry", "frown"):
        d.line([(10, 11), (13, 13)], fill=brow, width=2 if thick else 1)
        d.line([(18, 13), (21, 11)], fill=brow, width=2 if thick else 1)
    elif mood in ("sweat", "shock"):
        d.line([(10, 12), (13, 11)], fill=brow, width=2 if thick else 1)
        d.line([(18, 11), (21, 12)], fill=brow, width=2 if thick else 1)
    else:
        d.rectangle([10, 12, 13, 12 + (1 if thick else 0)], fill=brow)
        d.rectangle([18, 12, 21, 12 + (1 if thick else 0)], fill=brow)
    if mood == "shock":
        d.rectangle([10, 14, 13, 17], fill=WHITE)
        d.rectangle([18, 14, 21, 17], fill=WHITE)
        d.point((11, 15), fill=BLACK)
        d.point((20, 15), fill=BLACK)
    else:
        d.rectangle([10, 15, 12, 16], fill=WHITE)
        d.rectangle([11, 15, 12, 16], fill=BLACK)
        d.rectangle([19, 15, 21, 16], fill=WHITE)
        d.rectangle([19, 15, 20, 16], fill=BLACK)
    # 코
    d.rectangle([15, 16, 16, 19], fill=sd)
    d.point((14, 19), fill=sd)
    # 입
    mouth = (120, 40, 40)
    if mood == "grin":
        d.rectangle([12, 21, 19, 23], fill=mouth)
        d.rectangle([13, 21, 18, 22], fill=WHITE)
    elif mood == "smile":
        d.line([(13, 22), (18, 22)], fill=mouth)
        d.point((12, 21), fill=mouth)
        d.point((19, 21), fill=mouth)
    elif mood in ("frown", "angry", "sweat"):
        d.line([(13, 22), (18, 22)], fill=mouth)
        d.point((12, 23), fill=mouth)
        d.point((19, 23), fill=mouth)
    elif mood == "shock":
        d.rectangle([14, 21, 17, 24], fill=mouth)
    else:
        d.line([(13, 22), (18, 22)], fill=mouth)
    if mood in ("sweat", "shock"):
        blue = (110, 190, 255)
        d.rectangle([25, 6, 26, 9], fill=blue)
        d.point((25, 5), fill=blue)
        if mood == "shock":
            d.rectangle([4, 9, 5, 12], fill=blue)
            d.point((5, 8), fill=blue)
            for y in (7, 9):   # 창백해진 이마
                d.line([(12, y), (19, y)], fill=(150, 150, 210))
    return add_outline(im)


_pcache = {}


def portrait(key, mood=None):
    k = (key, mood)
    if k not in _pcache:
        _pcache[k] = _portrait(key, mood)
    return _pcache[k]


# 2등신 전신 스프라이트 (16x32 도트) ---------------------------------------------------

def _chibi(key, frame=0):
    p = PEOPLE[key]
    skin, sd, hc = p["skin"], _shade(p["skin"]), p["hc"]
    im = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    h = p["hair"]
    if h == "long":
        d.rectangle([2, 5, 13, 17], fill=hc)
    d.ellipse([2, 3, 13, 14], fill=skin)
    d.point((1, 9), fill=skin)
    d.point((14, 9), fill=skin)
    if h == "bald":
        d.rectangle([2, 7, 2, 9], fill=hc)
        d.rectangle([13, 7, 13, 9], fill=hc)
        d.line([(5, 4), (6, 4)], fill=_light(skin, 1.1))
    elif h in ("short", "buzz"):
        d.chord([2, 2, 13, 11 if h == "short" else 9], 180, 360, fill=hc)
        d.rectangle([2, 6, 2, 8], fill=hc)
        d.rectangle([13, 6, 13, 8], fill=hc)
    elif h == "curly":
        d.chord([1, 1, 14, 12], 180, 360, fill=hc)
        for x in (3, 6, 9, 12):
            d.point((x, 2), fill=_light(hc, 1.6))
    elif h == "wavy":
        d.chord([1, 1, 14, 12], 180, 360, fill=hc)
        d.ellipse([3, 0, 8, 4], fill=hc)
        d.ellipse([7, 0, 13, 4], fill=hc)
        d.rectangle([1, 6, 2, 9], fill=hc)
        d.rectangle([13, 6, 14, 9], fill=hc)
    elif h == "long":
        d.chord([1, 1, 14, 12], 180, 360, fill=hc)
        d.rectangle([1, 6, 2, 15], fill=hc)
        d.rectangle([13, 6, 14, 15], fill=hc)
    elif h == "blonde":
        d.chord([2, 1, 13, 11], 180, 360, fill=hc)
        d.ellipse([5, -1, 13, 4], fill=hc)
    b = p.get("beard", "none")
    if b == "full":
        d.chord([2, 5, 13, 16], 20, 160, fill=p["bc"])
        d.rectangle([5, 11, 10, 11], fill=p["bc"])
    elif b == "stubble":
        for x in range(4, 12):
            for y in range(11, 14):
                if (x * 3 + y) % 4 == 0 and im.getpixel((x, y))[:3] == skin:
                    d.point((x, y), fill=_shade(skin, 0.86))
    d.rectangle([5, 8, 5, 9], fill=BLACK)
    d.rectangle([10, 8, 10, 9], fill=BLACK)
    d.line([(4, 7), (5, 7)], fill=p["brow"])
    d.line([(10, 7), (11, 7)], fill=p["brow"])
    d.line([(7, 12), (8, 12)], fill=(120, 40, 40))
    if p["outfit"] == "kit":
        d.rectangle([4, 15, 11, 22], fill=WHITE)
        for x in range(4, 12):
            for y in range(15, 23):
                if (x + y) % 4 == 0:
                    d.point((x, y), fill=TONAL)
        d.rectangle([4, 18, 4, 22], fill=NAVY)
        d.rectangle([11, 18, 11, 22], fill=NAVY)
        d.point((6, 15), fill=NAVY)
        d.point((9, 15), fill=NAVY)
        d.line([(7, 16), (8, 16)], fill=NAVY)
        d.point((5, 17), fill=NAVY)
        d.point((10, 17), fill=NAVY)
        d.line([(6, 19), (9, 19)], fill=AIA_RED)
        for ax in (2, 13):
            d.rectangle([ax, 15, ax + (1 if ax == 2 else 0), 18], fill=WHITE)
        d.rectangle([2, 15, 3, 18], fill=WHITE)
        d.rectangle([12, 15, 13, 18], fill=WHITE)
        d.line([(2, 19), (3, 19)], fill=NAVY)
        d.line([(12, 19), (13, 19)], fill=NAVY)
        d.line([(2, 20), (3, 20)], fill=skin)
        d.line([(12, 20), (13, 20)], fill=skin)
        d.rectangle([4, 23, 11, 25], fill=BINARY)
        d.point((7, 25), fill=(0, 0, 0, 0))
        d.point((8, 25), fill=(0, 0, 0, 0))
        sock, leg = WHITE, skin
    else:
        d.rectangle([4, 15, 11, 23], fill=TRACK)
        d.line([(7, 16), (7, 23)], fill=WHITE)
        d.point((6, 15), fill=WHITE)
        d.point((9, 15), fill=WHITE)
        d.point((10, 17), fill=WHITE)
        d.rectangle([2, 15, 3, 20], fill=TRACK)
        d.rectangle([12, 15, 13, 20], fill=TRACK)
        d.line([(2, 21), (3, 21)], fill=skin)
        d.line([(12, 21), (13, 21)], fill=skin)
        d.rectangle([4, 24, 11, 25], fill=TRACK)
        sock, leg = TRACK, TRACK
    boot = BLACK
    if frame == 0:
        d.rectangle([5, 26, 6, 26], fill=leg)
        d.rectangle([9, 26, 10, 26], fill=leg)
        d.rectangle([5, 27, 6, 29], fill=sock)
        d.rectangle([9, 27, 10, 29], fill=sock)
        d.line([(4, 30), (6, 30)], fill=boot)
        d.line([(9, 30), (11, 30)], fill=boot)
    else:
        d.rectangle([4, 26, 5, 26], fill=leg)
        d.rectangle([3, 27, 4, 29], fill=sock)
        d.line([(2, 30), (4, 30)], fill=boot)
        d.rectangle([10, 26, 11, 26], fill=leg)
        d.rectangle([11, 27, 12, 28], fill=sock)
        d.line([(12, 29), (14, 29)], fill=boot)
    return add_outline(im)


_ccache = {}


def chibi(key, frame=0):
    k = (key, frame)
    if k not in _ccache:
        _ccache[k] = _chibi(key, frame)
    return _ccache[k]


# 상대팀 마스코트 ---------------------------------------------------------------------

def draw_hammer(d, x, y, t):
    """웨스트햄 망치."""
    x, y = int(x), int(y)
    d.rectangle([x + 7, y + 11, x + 12, y + 25], fill=CLARET, outline=BLACK)
    d.rectangle([x, y, x + 20, y + 11], fill=(160, 160, 176), outline=BLACK)
    d.rectangle([x + 4, y + 4, x + 6, y + 6], fill=BLACK)
    d.rectangle([x + 13, y + 4, x + 15, y + 6], fill=BLACK)
    d.line([(x + 7, y + 9), (x + 13, y + 9)], fill=BLACK)
    step = int(t * 12) % 2
    lx = (x + 6, x + 14) if step else (x + 8, x + 12)
    for lxx in lx:
        d.line([(lxx, y + 26), (lxx, y + 30)], fill=(27, 177, 231), width=2)


_MON = {}


def monster(kind, t, flash=False):
    """마스코트를 80x80 캔버스에 그려 2배 확대한 RGBA를 돌려준다."""
    im = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    _draw_monster(d, kind, 40, 44, t, flash)
    return im.resize((160, 160), Image.NEAREST)


def _draw_monster(d, kind, cx, cy, t, flash=False):
    cx, cy = int(cx), int(cy)
    ol = BLACK
    if kind == "bee":  # Brentford
        flap = -2 if int(t * 14) % 2 else 1
        wing = (208, 240, 255) if not flash else WHITE
        d.ellipse([cx - 16, cy - 30 + flap, cx - 2, cy - 10], fill=wing, outline=ol)
        d.ellipse([cx + 2, cy - 32 - flap, cx + 18, cy - 10], fill=wing, outline=ol)
        d.polygon([(cx - 22, cy - 3), (cx - 34, cy + 2), (cx - 22, cy + 5)], fill=BLACK)
        body = YELLOW if not flash else WHITE
        d.ellipse([cx - 22, cy - 14, cx + 22, cy + 14], fill=body, outline=ol)
        d.rectangle([cx - 9, cy - 13, cx - 4, cy + 13], fill=BLACK)
        d.rectangle([cx + 3, cy - 12, cx + 8, cy + 12], fill=BLACK)
        d.ellipse([cx + 11, cy - 9, cx + 19, cy - 1], fill=WHITE, outline=ol)
        d.rectangle([cx + 15, cy - 6, cx + 17, cy - 3], fill=BLACK)
        d.line([(cx + 10, cy - 12), (cx + 19, cy - 9)], fill=BLACK, width=2)
        d.line([(cx + 12, cy + 6), (cx + 18, cy + 4)], fill=BLACK)
        d.rectangle([cx - 4, cy + 11, cx + 12, cy + 15], fill=RED)  # red scarf
    elif kind == "magpie":  # Newcastle
        d.polygon([(cx - 14, cy + 4), (cx - 40, cy + 20), (cx - 36, cy + 26), (cx - 10, cy + 12)],
                  fill=BLACK, outline=(60, 60, 90))
        body = BLACK if not flash else WHITE
        d.ellipse([cx - 20, cy - 14, cx + 14, cy + 16], fill=body, outline=(60, 60, 90))
        d.ellipse([cx - 6, cy - 2, cx + 12, cy + 14], fill=WHITE)
        d.ellipse([cx - 16, cy - 8, cx - 2, cy + 4], fill=WHITE)
        d.ellipse([cx + 2, cy - 30, cx + 24, cy - 8], fill=body, outline=(60, 60, 90))
        d.polygon([(cx + 22, cy - 22), (cx + 34, cy - 18), (cx + 22, cy - 15)], fill=GRAY, outline=ol)
        d.ellipse([cx + 12, cy - 25, cx + 19, cy - 18], fill=WHITE)
        d.rectangle([cx + 15, cy - 23, cx + 17, cy - 20], fill=BLACK)
        d.line([(cx - 2, cy + 16), (cx - 2, cy + 22)], fill=GRAY, width=2)
        d.line([(cx + 6, cy + 16), (cx + 6, cy + 22)], fill=GRAY, width=2)
    elif kind == "toffee":  # Everton
        blue = (40, 80, 200)
        d.polygon([(cx - 16, cy), (cx - 34, cy - 14), (cx - 34, cy + 14)], fill=blue, outline=ol)
        d.polygon([(cx + 16, cy), (cx + 34, cy - 14), (cx + 34, cy + 14)], fill=blue, outline=ol)
        d.line([(cx - 28, cy - 10), (cx - 28, cy + 10)], fill=WHITE)
        d.line([(cx + 28, cy - 10), (cx + 28, cy + 10)], fill=WHITE)
        body = (190, 110, 40) if not flash else WHITE
        d.ellipse([cx - 18, cy - 14, cx + 18, cy + 14], fill=body, outline=ol)
        d.line([(cx - 9, cy - 3), (cx - 3, cy - 3)], fill=BLACK, width=2)
        d.line([(cx + 3, cy - 3), (cx + 9, cy - 3)], fill=BLACK, width=2)
        d.line([(cx - 3, cy + 6), (cx + 3, cy + 6)], fill=BLACK)
        zy = cy - 22 - int((t * 10) % 12)
        d.text((cx + 16, zy), "z", font=F16, fill=blue)
        d.text((cx + 24, zy - 10), "Z", font=F16, fill=blue)
    elif kind == "lion":  # Aston Villa
        mane = CLARET if not flash else WHITE
        for a in range(0, 360, 30):
            rx = cx + int(26 * math.cos(math.radians(a)))
            ry = cy + int(26 * math.sin(math.radians(a)))
            d.ellipse([rx - 8, ry - 8, rx + 8, ry + 8], fill=mane, outline=ol)
        d.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=mane)
        face = GOLD if not flash else WHITE
        d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=face, outline=ol)
        d.ellipse([cx - 9, cy - 7, cx - 3, cy - 1], fill=WHITE, outline=ol)
        d.ellipse([cx + 3, cy - 7, cx + 9, cy - 1], fill=WHITE, outline=ol)
        d.rectangle([cx - 6, cy - 5, cx - 5, cy - 3], fill=BLACK)
        d.rectangle([cx + 5, cy - 5, cx + 6, cy - 3], fill=BLACK)
        d.line([(cx - 11, cy - 11), (cx - 3, cy - 8)], fill=BLACK, width=2)
        d.line([(cx + 3, cy - 8), (cx + 11, cy - 11)], fill=BLACK, width=2)
        d.polygon([(cx - 3, cy + 2), (cx + 3, cy + 2), (cx, cy + 5)], fill=BLACK)
        d.polygon([(cx - 7, cy + 8), (cx + 7, cy + 8), (cx, cy + 13)], fill=DRED)
        d.polygon([(cx - 5, cy + 8), (cx - 3, cy + 11), (cx - 1, cy + 8)], fill=WHITE)
        d.polygon([(cx + 1, cy + 8), (cx + 3, cy + 11), (cx + 5, cy + 8)], fill=WHITE)
        d.rectangle([cx - 20, cy + 20, cx + 20, cy + 24], fill=(149, 191, 229))


