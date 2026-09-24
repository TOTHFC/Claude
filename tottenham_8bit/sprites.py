"""8비트 인물 스프라이트(얼굴 초상화 32x32, 2등신 전신 16x32)와 마스코트.

얼굴은 위키미디어 공용 사진을 보고 특징(머리 모양·색, 수염, 피부톤)을 살린 도트 캐리커처다.
유니폼은 토트넘 2026/27 나이키 킷 사진을 참고했다.
  HOME: 흰 바탕 + 톤온톤 사선 무늬, 네이비 옆구리 패널·칼라·소매 끝, 빨간 AIA,
        네이비 스우시·엠블럼, 왼팔 보라색 Kraken, 네이비 반바지, 흰 양말
  AWAY: 옵시디언 네이비 바탕 + 가슴 아래 네온 사선 줄무늬(보라·분홍·주황·파랑),
        흰 AIA·스우시·엠블럼, 네이비 반바지·양말
"""
import math

from PIL import Image, ImageDraw

from engine import BLACK, CLARET, DRED, F16, GOLD, GRAY, NAVY, RED, WHITE, YELLOW, add_outline

AIA_RED = (214, 0, 28)
TONAL = (226, 228, 240)
KRAKEN = (120, 80, 220)
OBSIDIAN = (22, 30, 70)
NEON = [(255, 70, 170), (150, 90, 255), (255, 150, 60), (80, 150, 255)]
TRACK = (22, 32, 78)

PEOPLE = {
    # 감독 · 관계자
    "frank": dict(name="토마스 프랭크", short="프랭크", skin=(240, 196, 166), hair="curly_big", hc=(132, 90, 56),
                  beard="stubble", brow=(110, 74, 46), outfit="track", mood="grin"),
    "tudor": dict(name="이고르 투도르", short="투도르", skin=(222, 176, 140), hair="receding", hc=(66, 56, 50),
                  beard="stubble", brow=(50, 40, 34), outfit="track", mood="frown", thick=True),
    "dezerbi": dict(name="로베르토 데 제르비", short="데 제르비", skin=(222, 176, 140), hair="short", hc=(34, 28, 26),
                    beard="full", bc=(34, 28, 26), brow=(30, 24, 22), outfit="black", mood="smile", thick=True),
    "ange": dict(name="안지 포스테코글루", short="포스테코글루", skin=(222, 176, 140), hair="short", hc=(176, 172, 168),
                 beard="stubble", brow=(100, 96, 92), outfit="suit", mood="grin"),
    "levy": dict(name="다니엘 레비", short="레비", skin=(240, 196, 166), hair="bald", hc=(190, 180, 170),
                 beard="none", brow=(130, 120, 110), outfit="polo", mood="smile"),
    # 선수 (등번호: 2026/27 구단 발표)
    "fernandes": dict(name="마테우스 페르난데스", short="페르난데스", num=18, skin=(220, 172, 134), hair="curly",
                      hc=(32, 26, 24), beard="none", brow=(32, 26, 24), outfit="home", thick=True),
    "tonali": dict(name="산드로 토날리", short="토날리", num=16, skin=(238, 196, 166), hair="long", hc=(46, 34, 28),
                   beard="full", bc=(46, 34, 28), brow=(40, 30, 24), outfit="home"),
    "robertson": dict(name="앤디 로버트슨", short="로버트슨", num=3, skin=(246, 206, 182), hair="short", hc=(64, 46, 34),
                      beard="stubble", brow=(64, 46, 34), outfit="home"),
    "vanhecke": dict(name="얀 폴 반 헤케", short="반 헤케", num=6, skin=(246, 206, 182), hair="short",
                     hc=(232, 208, 146), beard="none", brow=(190, 160, 110), outfit="home"),
    "senesi": dict(name="마르코스 세네시", short="세네시", num=5, skin=(238, 194, 160), hair="curly", hc=(46, 34, 28),
                   beard="stubble", brow=(46, 34, 28), outfit="home"),
    "mudryk": dict(name="미하일로 무드릭", short="무드릭", num=27, skin=(246, 208, 184), hair="blonde_shag",
                   hc=(244, 226, 168), beard="none", brow=(170, 140, 100), outfit="home"),
    "adarabioyo": dict(name="토신 아다라비오요", short="아다라비오요", num=4, skin=(110, 72, 50), hair="buzz",
                       hc=(22, 16, 14), beard="full", bc=(22, 16, 14), brow=(22, 16, 14), outfit="home"),
    "gallagher": dict(name="코너 갤러거", short="갤러거", num=8, skin=(246, 206, 182), hair="slick_bun",
                      hc=(222, 186, 118), beard="mustache", bc=(196, 158, 100), brow=(186, 148, 98), outfit="home"),
    "vdv": dict(name="미키 반 더 벤", short="반 더 벤", num=37, skin=(244, 204, 180), hair="short", hc=(116, 86, 60),
                beard="none", brow=(110, 80, 56), outfit="home", captain=True),
    "romero": dict(name="크리스티안 로메로", short="로메로", num=17, skin=(206, 152, 112), hair="short", hc=(26, 22, 20),
                   beard="stubble", brow=(26, 22, 20), outfit="home"),
    "son": dict(name="손흥민", short="손흥민", num=7, skin=(238, 196, 160), hair="fringe", hc=(22, 18, 18),
                beard="none", brow=(22, 18, 18), outfit="lafc", mood="grin"),
    "kane": dict(name="해리 케인", short="케인", num=9, skin=(246, 206, 182), hair="short", hc=(136, 98, 62),
                 beard="stubble", brow=(130, 96, 62), outfit="bayern", mood="grin"),
}


def shade(c, k=0.82):
    return tuple(int(v * k) for v in c)


def light(c, k=1.15):
    return tuple(min(255, int(v * k)) for v in c)


# ------------------------------------------------------------------ 옷 (공통)

def _kit_top(d, x0, y0, x1, y1, kit, cx):
    """상의 직사각형 영역에 킷 무늬를 칠한다(초상화/전신 공용)."""
    if kit == "home":
        d.rectangle([x0, y0, x1, y1], fill=WHITE)
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                if (x + y) % 4 == 0:
                    d.point((x, y), fill=TONAL)
    elif kit == "away":
        d.rectangle([x0, y0, x1, y1], fill=OBSIDIAN)
        top = y0 + max(2, (y1 - y0) // 3)
        for x in range(x0, x1 + 1):
            for y in range(top, y1 + 1):
                k = (x * 2 - y * 1) % 7
                if k < 2:
                    d.point((x, y), fill=NEON[((x + y) // 5) % 4])


def kit_colors(p):
    o = p["outfit"]
    if o == "home":
        return dict(accent=NAVY, logo=AIA_RED, mark=NAVY, shorts=NAVY, sock=WHITE, sleeve=WHITE, arm=p["skin"],
                    leg=p["skin"])
    if o == "away":
        return dict(accent=OBSIDIAN, logo=WHITE, mark=WHITE, shorts=OBSIDIAN, sock=OBSIDIAN, sleeve=OBSIDIAN,
                    arm=p["skin"], leg=p["skin"])
    if o == "track":
        return dict(shirt=TRACK, shorts=TRACK, sock=TRACK, sleeve=TRACK, arm=TRACK, leg=TRACK, trim=WHITE)
    if o == "black":
        return dict(shirt=(34, 34, 40), shorts=(24, 28, 50), sock=(24, 28, 50), sleeve=(34, 34, 40),
                    arm=(34, 34, 40), leg=(24, 28, 50), trim=(70, 70, 80))
    if o == "suit":
        return dict(shirt=(30, 40, 72), shorts=(30, 40, 72), sock=(30, 40, 72), sleeve=(30, 40, 72),
                    arm=(30, 40, 72), leg=(30, 40, 72), trim=WHITE)
    if o == "polo":
        return dict(shirt=WHITE, shorts=(70, 70, 80), sock=(70, 70, 80), sleeve=WHITE, arm=p["skin"],
                    leg=(70, 70, 80), trim=WHITE)
    if o == "lafc":
        return dict(shirt=(20, 20, 24), shorts=(20, 20, 24), sock=(20, 20, 24), sleeve=(20, 20, 24),
                    arm=p["skin"], leg=p["skin"], trim=(206, 166, 76))
    if o == "bayern":
        return dict(shirt=(220, 20, 50), shorts=(220, 20, 50), sock=(220, 20, 50), sleeve=(220, 20, 50),
                    arm=p["skin"], leg=p["skin"], trim=WHITE)
    return {}


def with_kit(key, kit):
    p = dict(PEOPLE[key])
    p["outfit"] = kit
    return p


# ------------------------------------------------------------------ 얼굴 초상화 32x32

def _hair_portrait(d, p, back=False):
    h, hc = p["hair"], p["hc"]
    hl = light(hc, 1.4)
    if back:
        if h == "long":
            d.rectangle([6, 8, 25, 29], fill=hc)
        if h == "slick_bun":
            d.ellipse([12, 0, 19, 5], fill=hc)
        if h == "blonde_shag":
            d.rectangle([6, 8, 25, 22], fill=hc)
        return
    if h == "curly_big":
        for (x, y, r) in ((9, 7, 4), (13, 4, 4), (18, 4, 4), (22, 7, 4), (7, 12, 3), (24, 12, 3), (15, 3, 4),
                          (11, 8, 3), (20, 8, 3), (7, 16, 2), (24, 16, 2)):
            d.ellipse([x - r, y - r, x + r, y + r], fill=hc)
        for (x, y) in ((10, 5), (14, 3), (19, 4), (22, 8), (8, 11), (23, 12), (16, 6), (12, 9), (20, 9)):
            d.point((x, y), fill=hl)
    elif h == "receding":
        d.rectangle([8, 10, 9, 17], fill=hc)
        d.rectangle([22, 10, 23, 17], fill=hc)
        d.rectangle([9, 8, 10, 11], fill=hc)
        d.rectangle([21, 8, 22, 11], fill=hc)
        for x in (14, 16, 18):
            d.point((x, 5), fill=shade(p["skin"], 0.75))
        d.line([(11, 6), (13, 5)], fill=light(p["skin"], 1.08))
    elif h in ("short", "buzz"):
        d.chord([8, 3, 23, 17 if h == "short" else 13], 180, 360, fill=hc)
        d.rectangle([8, 9, 9, 15 if h == "short" else 12], fill=hc)
        d.rectangle([22, 9, 23, 15 if h == "short" else 12], fill=hc)
        if h == "short":
            d.line([(11, 5), (18, 5)], fill=hl)
            d.point((20, 9), fill=hc)
            d.point((19, 10), fill=hc)
    elif h == "curly":
        d.chord([7, 2, 24, 18], 180, 360, fill=hc)
        d.rectangle([7, 8, 9, 14], fill=hc)
        d.rectangle([22, 8, 24, 14], fill=hc)
        for (x, y, r) in ((10, 4, 2), (14, 3, 2), (18, 3, 2), (22, 5, 2), (9, 9, 2), (23, 9, 2), (12, 9, 1),
                          (16, 8, 2), (20, 9, 1)):
            d.ellipse([x - r, y - r, x + r, y + r], fill=hc)
        for (x, y) in ((10, 3), (14, 2), (18, 2), (21, 4), (13, 7), (17, 7)):
            d.point((x, y), fill=hl)
    elif h == "long":
        d.chord([7, 2, 24, 18], 180, 360, fill=hc)
        d.rectangle([7, 8, 9, 25], fill=hc)
        d.rectangle([22, 8, 24, 25], fill=hc)
        d.line([(15, 3), (15, 7)], fill=shade(hc, 0.6))
    elif h == "slick_bun":
        d.chord([8, 3, 23, 16], 180, 360, fill=hc)
        d.rectangle([8, 9, 9, 13], fill=hc)
        d.rectangle([22, 9, 23, 13], fill=hc)
        for x in (11, 14, 17, 20):
            d.line([(x, 5), (x + 1, 9)], fill=shade(hc, 0.8))
    elif h == "blonde_shag":
        d.chord([7, 1, 24, 18], 180, 360, fill=hc)
        d.rectangle([7, 8, 9, 18], fill=hc)
        d.rectangle([22, 8, 24, 18], fill=hc)
        for x in range(9, 23, 3):
            d.line([(x, 9), (x + 1, 12)], fill=hc)
        d.line([(12, 3), (16, 2)], fill=light(hc, 1.1))
    elif h == "fringe":
        d.chord([7, 2, 24, 18], 180, 360, fill=hc)
        d.rectangle([7, 8, 9, 14], fill=hc)
        d.rectangle([22, 8, 24, 14], fill=hc)
        for x in range(9, 23, 2):
            d.line([(x, 9), (x, 12 if x % 4 else 13)], fill=hc)
    elif h == "bald":
        d.rectangle([8, 12, 9, 16], fill=hc)
        d.rectangle([22, 12, 23, 16], fill=hc)
        d.line([(12, 5), (15, 5)], fill=light(p["skin"], 1.1))


def _portrait(key, mood=None, kit=None):
    p = with_kit(key, kit) if kit else PEOPLE[key]
    mood = mood or p.get("mood", "smile")
    skin, sd = p["skin"], shade(p["skin"])
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    o = p["outfit"]
    if o in ("home", "away"):
        kc = kit_colors(p)
        _kit_top(d, 3, 27, 28, 31, o, 15)
        if o == "home":
            d.rectangle([3, 29, 4, 31], fill=NAVY)
            d.rectangle([27, 29, 28, 31], fill=NAVY)
        d.polygon([(12, 27), (15, 29), (16, 29), (19, 27)], fill=NAVY if o == "home" else (40, 50, 100))
        d.line([(8, 30), (10, 29)], fill=kc["mark"])       # 스우시
        d.rectangle([21, 29, 22, 30], fill=kc["mark"])     # 엠블럼
        d.rectangle([12, 31, 19, 31], fill=kc["logo"])     # AIA
    else:
        kc = kit_colors(p)
        d.rectangle([3, 27, 28, 31], fill=kc["shirt"])
        if o == "suit":
            d.polygon([(12, 27), (16, 31), (19, 27)], fill=WHITE)
            d.line([(15, 28), (15, 31)], fill=GOLD)
            d.line([(16, 28), (16, 31)], fill=GOLD)
        elif o == "polo":
            d.polygon([(11, 27), (15, 29), (20, 27)], fill=(230, 230, 236))
        elif o in ("track",):
            d.line([(15, 28), (15, 31)], fill=WHITE)
            d.line([(12, 27), (15, 28)], fill=WHITE)
            d.line([(19, 27), (16, 28)], fill=WHITE)
        elif o == "lafc":
            d.line([(3, 27), (28, 27)], fill=kc["trim"])
            d.rectangle([21, 29, 22, 30], fill=kc["trim"])
        elif o == "bayern":
            d.line([(15, 27), (15, 31)], fill=WHITE)
    d.rectangle([13, 23, 18, 27], fill=sd)
    _hair_portrait(d, p, back=True)
    d.rectangle([6, 14, 8, 19], fill=skin)
    d.rectangle([23, 14, 25, 19], fill=skin)
    d.point((7, 16), fill=sd)
    d.point((24, 16), fill=sd)
    d.ellipse([8, 4, 23, 26], fill=skin)
    b = p.get("beard", "none")
    if b == "full":
        d.chord([8, 7, 23, 27], 12, 168, fill=p["bc"])
        d.rectangle([8, 16, 9, 21], fill=p["bc"])
        d.rectangle([22, 16, 23, 21], fill=p["bc"])
        d.rectangle([12, 19, 19, 20], fill=p["bc"])
    elif b == "stubble":
        for y in range(19, 26):
            for x in range(9, 23):
                if (x * 3 + y * 5) % 6 == 0 and im.getpixel((x, y))[:3] == skin:
                    d.point((x, y), fill=shade(skin, 0.84))
    _hair_portrait(d, p)
    brow, thick = p["brow"], p.get("thick", False)
    if mood in ("angry", "frown"):
        d.line([(10, 11), (13, 13)], fill=brow, width=2 if thick else 1)
        d.line([(18, 13), (21, 11)], fill=brow, width=2 if thick else 1)
    elif mood in ("sweat", "shock", "sad"):
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
    elif mood == "happy_eyes":
        d.line([(10, 16), (11, 15), (12, 16)], fill=BLACK)
        d.line([(19, 16), (20, 15), (21, 16)], fill=BLACK)
    else:
        d.rectangle([10, 15, 12, 16], fill=WHITE)
        d.rectangle([11, 15, 12, 16], fill=BLACK)
        d.rectangle([19, 15, 21, 16], fill=WHITE)
        d.rectangle([19, 15, 20, 16], fill=BLACK)
    d.rectangle([15, 16, 16, 19], fill=sd)
    d.point((14, 19), fill=sd)
    if b == "mustache":
        d.rectangle([12, 20, 19, 20], fill=p["bc"])
        d.point((11, 21), fill=p["bc"])
        d.point((20, 21), fill=p["bc"])
    mouth = (120, 40, 40)
    if mood == "grin":
        d.rectangle([12, 21, 19, 23], fill=mouth)
        d.rectangle([13, 21, 18, 22], fill=WHITE)
    elif mood in ("smile", "happy_eyes"):
        d.line([(13, 22), (18, 22)], fill=mouth)
        d.point((12, 21), fill=mouth)
        d.point((19, 21), fill=mouth)
    elif mood in ("frown", "angry", "sweat", "sad"):
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
    if mood == "sad":
        d.rectangle([11, 17, 11, 19], fill=(110, 190, 255))
    return add_outline(im)


_pc = {}


def portrait(key, mood=None, kit=None):
    k = (key, mood, kit)
    if k not in _pc:
        _pc[k] = _portrait(key, mood, kit)
    return _pc[k]


# ------------------------------------------------------------------ 2등신 전신 16x32

def _hair_chibi(d, p, back=False):
    h, hc = p["hair"], p["hc"]
    if back:
        if h == "long":
            d.rectangle([1, 5, 14, 17], fill=hc)
        if h == "slick_bun":
            d.ellipse([6, -1, 10, 3], fill=hc)
        if h == "blonde_shag":
            d.rectangle([1, 5, 14, 13], fill=hc)
        return
    if h == "curly_big":
        for (x, y, r) in ((3, 4, 3), (7, 1, 3), (11, 2, 3), (13, 5, 2), (2, 8, 2), (14, 8, 2), (8, 3, 2)):
            d.ellipse([x - r, y - r, x + r, y + r], fill=hc)
        for (x, y) in ((4, 3), (8, 1), (11, 1), (13, 4)):
            d.point((x, y), fill=light(hc, 1.4))
    elif h == "receding":
        d.rectangle([2, 6, 2, 9], fill=hc)
        d.rectangle([13, 6, 13, 9], fill=hc)
        d.point((3, 5), fill=hc)
        d.point((12, 5), fill=hc)
        d.point((5, 4), fill=light(p["skin"], 1.1))
    elif h in ("short", "buzz", "fringe"):
        d.chord([2, 2, 13, 11 if h != "buzz" else 9], 180, 360, fill=hc)
        d.rectangle([2, 6, 2, 8], fill=hc)
        d.rectangle([13, 6, 13, 8], fill=hc)
        if h == "fringe":
            d.line([(4, 6), (11, 6)], fill=hc)
    elif h == "curly":
        d.chord([1, 1, 14, 12], 180, 360, fill=hc)
        for x in (3, 6, 9, 12):
            d.point((x, 1), fill=hc)
            d.point((x, 3), fill=light(hc, 1.6))
    elif h == "long":
        d.chord([1, 1, 14, 12], 180, 360, fill=hc)
        d.rectangle([1, 6, 2, 15], fill=hc)
        d.rectangle([13, 6, 14, 15], fill=hc)
    elif h == "slick_bun":
        d.chord([2, 2, 13, 10], 180, 360, fill=hc)
        d.line([(5, 3), (5, 5)], fill=shade(hc))
        d.line([(9, 3), (9, 5)], fill=shade(hc))
    elif h == "blonde_shag":
        d.chord([1, 1, 14, 12], 180, 360, fill=hc)
        d.rectangle([1, 6, 2, 11], fill=hc)
        d.rectangle([13, 6, 14, 11], fill=hc)
        d.point((5, 7), fill=hc)
        d.point((9, 7), fill=hc)
    elif h == "bald":
        d.rectangle([2, 7, 2, 9], fill=hc)
        d.rectangle([13, 7, 13, 9], fill=hc)
        d.line([(5, 4), (6, 4)], fill=light(p["skin"], 1.1))


def _chibi(key, frame=0, kit=None, mood="smile"):
    p = with_kit(key, kit) if kit else PEOPLE[key]
    skin = p["skin"]
    im = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _hair_chibi(d, p, back=True)
    d.ellipse([2, 3, 13, 14], fill=skin)
    d.point((1, 9), fill=skin)
    d.point((14, 9), fill=skin)
    b = p.get("beard", "none")
    if b == "full":
        d.chord([2, 5, 13, 16], 20, 160, fill=p["bc"])
        d.rectangle([5, 11, 10, 11], fill=p["bc"])
    elif b == "stubble":
        for x in range(4, 12):
            for y in range(11, 14):
                if (x * 3 + y) % 4 == 0 and im.getpixel((x, y))[:3] == skin:
                    d.point((x, y), fill=shade(skin, 0.84))
    _hair_chibi(d, p)
    if mood == "shock":
        d.rectangle([4, 7, 5, 9], fill=WHITE)
        d.rectangle([10, 7, 11, 9], fill=WHITE)
        d.point((5, 8), fill=BLACK)
        d.point((10, 8), fill=BLACK)
    elif mood == "x":
        for ex in (4, 10):
            d.point((ex, 7), fill=BLACK)
            d.point((ex + 1, 8), fill=BLACK)
            d.point((ex, 9), fill=BLACK)
            d.point((ex + 1, 7), fill=BLACK)
            d.point((ex, 8), fill=BLACK)
    else:
        d.rectangle([5, 8, 5, 9], fill=BLACK)
        d.rectangle([10, 8, 10, 9], fill=BLACK)
    d.line([(4, 7), (5, 7)], fill=p["brow"])
    d.line([(10, 7), (11, 7)], fill=p["brow"])
    if b == "mustache":
        d.line([(6, 11), (9, 11)], fill=p["bc"])
    mc = (120, 40, 40)
    if mood == "shock":
        d.rectangle([7, 11, 8, 13], fill=mc)
    elif mood == "sad":
        d.line([(7, 12), (8, 12)], fill=mc)
        d.point((6, 13), fill=mc)
        d.point((9, 13), fill=mc)
    else:
        d.line([(7, 12), (8, 12)], fill=mc)
    o = p["outfit"]
    if o in ("home", "away"):
        kc = kit_colors(p)
        _kit_top(d, 4, 15, 11, 22, o, 7)
        if o == "home":
            d.rectangle([4, 18, 4, 22], fill=NAVY)
            d.rectangle([11, 18, 11, 22], fill=NAVY)
        d.point((6, 15), fill=NAVY if o == "home" else (60, 70, 120))
        d.point((9, 15), fill=NAVY if o == "home" else (60, 70, 120))
        d.line([(7, 16), (8, 16)], fill=NAVY if o == "home" else (60, 70, 120))
        d.point((5, 17), fill=kc["mark"])
        d.point((10, 17), fill=kc["mark"])
        d.line([(6, 19), (9, 19)], fill=kc["logo"])
        d.rectangle([2, 15, 3, 18], fill=kc["sleeve"])
        d.rectangle([12, 15, 13, 18], fill=kc["sleeve"])
        d.point((13, 16), fill=KRAKEN if o == "home" else WHITE)
        d.line([(2, 19), (3, 19)], fill=NAVY if o == "home" else NEON[1])
        d.line([(12, 19), (13, 19)], fill=NAVY if o == "home" else NEON[1])
        d.line([(2, 20), (3, 20)], fill=skin)
        d.line([(12, 20), (13, 20)], fill=skin)
        d.rectangle([4, 23, 11, 25], fill=kc["shorts"])
        d.point((5, 24), fill=WHITE)
        sock, leg = kc["sock"], skin
        if p.get("captain"):
            d.line([(2, 16), (3, 16)], fill=YELLOW)
    else:
        kc = kit_colors(p)
        d.rectangle([4, 15, 11, 23], fill=kc["shirt"])
        if o == "suit":
            d.polygon([(6, 15), (7, 18), (8, 18), (9, 15)], fill=WHITE)
            d.line([(7, 16), (7, 19)], fill=GOLD)
        elif o == "polo":
            d.line([(6, 15), (9, 15)], fill=(220, 220, 228))
        else:
            d.line([(7, 16), (7, 23)], fill=kc["trim"])
            d.point((6, 15), fill=kc["trim"])
            d.point((9, 15), fill=kc["trim"])
        d.rectangle([2, 15, 3, 20], fill=kc["sleeve"])
        d.rectangle([12, 15, 13, 20], fill=kc["sleeve"])
        if kc["arm"] != kc["sleeve"]:
            d.rectangle([2, 19, 3, 20], fill=kc["arm"])
            d.rectangle([12, 19, 13, 20], fill=kc["arm"])
        d.line([(2, 21), (3, 21)], fill=skin)
        d.line([(12, 21), (13, 21)], fill=skin)
        d.rectangle([4, 24, 11, 25], fill=kc["shorts"])
        sock, leg = kc["sock"], kc["leg"]
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


_cc = {}


def chibi(key, frame=0, kit=None, mood="smile"):
    k = (key, frame, kit, mood)
    if k not in _cc:
        _cc[k] = _chibi(key, frame, kit, mood)
    return _cc[k]


def kit_icon(kit):
    """아이템 획득용 유니폼 아이콘 (20x20)."""
    im = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    body = [(5, 2), (8, 1), (11, 1), (14, 2), (19, 6), (16, 9), (15, 8), (15, 19), (4, 19), (4, 8), (3, 9), (0, 6)]
    d.polygon(body, fill=WHITE if kit == "home" else OBSIDIAN)
    mask = Image.new("L", (20, 20), 0)
    ImageDraw.Draw(mask).polygon(body, fill=255)
    tmp = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    _kit_top(td, 0, 0, 19, 19, kit, 10)
    im.paste(tmp, (0, 0), mask)
    if kit == "home":
        d.rectangle([4, 10, 4, 18], fill=NAVY)
        d.rectangle([15, 10, 15, 18], fill=NAVY)
    d.polygon([(8, 1), (10, 3), (11, 1)], fill=NAVY if kit == "home" else (60, 70, 120))
    d.line([(7, 10), (12, 10)], fill=AIA_RED if kit == "home" else WHITE)
    d.line([(7, 11), (12, 11)], fill=AIA_RED if kit == "home" else WHITE)
    d.point((6, 6), fill=NAVY if kit == "home" else WHITE)
    d.rectangle([12, 5, 13, 6], fill=NAVY if kit == "home" else WHITE)
    d.point((17, 5), fill=KRAKEN if kit == "home" else WHITE)
    return add_outline(im)


# ------------------------------------------------------------------ 수탉 (마스코트)

def _sprite(rows, pal):
    h, w = len(rows), max(len(r) for r in rows)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != ".":
                px[x, y] = pal[c] + (255,)
    return add_outline(im)


COCK_PAL = {"R": RED, "W": WHITE, "K": BLACK, "Y": GOLD, "N": (48, 72, 160), "O": (230, 150, 0),
            "B": (110, 190, 255)}
_TOP = [
    "..........RR....",
    ".........RRRR...",
    "........WWWW....",
    ".......WWWKWY...",
    "N......WWWWWYY..",
    "NN.....WWWWR....",
    "NNN....WWWWR....",
    ".NNN..WWWWW.....",
    "..NNWWWWWWW.....",
    "..NWWWWWWWW.....",
    "...WWWWWWWW.....",
    "...WWWWWWWW.....",
    "....WWWWWW......",
    ".....WWWW.......",
]
COCK = _sprite(_TOP + ["......O..O......", "......O..O......", ".....OO.OO......"], COCK_PAL)
COCK_RUN = _sprite(_TOP + [".....O....O.....", "....O......O....", "...OO.....OO...."], COCK_PAL)
COCK_CRY = _sprite([r.replace("K", "B") for r in _TOP] + ["......O..O......", "......O..O......",
                                                          ".....OO.OO......"], COCK_PAL)


# ------------------------------------------------------------------ 상대팀 마스코트

def draw_hammer(d, x, y, t, legs=True, mood="happy"):
    x, y = int(x), int(y)
    d.rectangle([x + 7, y + 11, x + 12, y + 25], fill=CLARET, outline=BLACK)
    d.rectangle([x, y, x + 20, y + 11], fill=(160, 160, 176), outline=BLACK)
    if mood == "shock":
        d.rectangle([x + 3, y + 3, x + 7, y + 7], fill=WHITE, outline=BLACK)
        d.rectangle([x + 12, y + 3, x + 16, y + 7], fill=WHITE, outline=BLACK)
    else:
        d.rectangle([x + 4, y + 4, x + 6, y + 6], fill=BLACK)
        d.rectangle([x + 13, y + 4, x + 15, y + 6], fill=BLACK)
    d.line([(x + 7, y + 9), (x + 13, y + 9)], fill=BLACK)
    if legs:
        step = int(t * 12) % 2
        lx = (x + 6, x + 14) if step else (x + 8, x + 12)
        for lxx in lx:
            d.line([(lxx, y + 26), (lxx, y + 30)], fill=(27, 177, 231), width=2)


def monster(kind, t, flash=False):
    """마스코트를 80x80 캔버스에 그려 2배 확대한 RGBA."""
    im = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    _draw_monster(d, kind, 40, 44, t, flash)
    return im.resize((160, 160), Image.NEAREST)


def _draw_tree(d, cx, cy, t, flash):
    trunk = (130, 84, 50) if not flash else WHITE
    d.rectangle([cx - 7, cy - 4, cx + 7, cy + 26], fill=trunk, outline=BLACK)
    d.line([(cx - 6, cy + 26), (cx - 10, cy + 32)], fill=trunk, width=3)
    d.line([(cx + 6, cy + 26), (cx + 10, cy + 32)], fill=trunk, width=3)
    leaf = (60, 150, 60) if not flash else WHITE
    for (x, y, r) in ((-16, -14, 13), (0, -22, 15), (16, -14, 13), (-10, -2, 11), (10, -2, 11)):
        d.ellipse([cx + x - r, cy + y - r, cx + x + r, cy + y + r], fill=leaf, outline=BLACK)
    for (x, y, r) in ((-16, -14, 12), (0, -22, 14), (16, -14, 12), (-10, -2, 10), (10, -2, 10)):
        d.ellipse([cx + x - r, cy + y - r, cx + x + r, cy + y + r], fill=leaf)
    d.rectangle([cx - 5, cy + 4, cx - 2, cy + 7], fill=WHITE)
    d.rectangle([cx + 2, cy + 4, cx + 5, cy + 7], fill=WHITE)
    d.point((cx - 3, cy + 6), fill=BLACK)
    d.point((cx + 3, cy + 6), fill=BLACK)
    d.line([(cx - 4, cy + 12), (cx + 4, cy + 11)], fill=BLACK)
    d.polygon([(cx - 14, cy - 36), (cx + 16, cy - 42), (cx + 6, cy - 32)], fill=(30, 110, 40), outline=BLACK)
    d.line([(cx + 8, cy - 40), (cx + 18, cy - 50)], fill=RED, width=2)


def _draw_monster_base(d, kind, cx, cy, t, flash=False):
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




def _draw_monster(d, kind, cx, cy, t, flash=False):
    if kind == "tree":
        _draw_tree(d, cx, cy, t, flash)
    else:
        _draw_monster_base(d, kind, cx, cy, t, flash)
