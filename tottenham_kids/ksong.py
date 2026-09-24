"""주제가 「힘내요! 데 제르비」 ─ 작사·작곡·편곡·노래 합성.

F장조, 160 BPM. 실로폰·토이피아노·베이스·박수 반주에, 음성 합성 음절을 음표에 맞춰 부르게 한다.
"""
import numpy as np

from kengine import SR, drum, inst
from voice import sing_phrase, tts

BPM = 160
BEAT = 60 / BPM
BAR = BEAT * 4
KEY = -7  # C장조로 적고 F장조로 내려 부른다(합성 음성이 가장 또렷한 음역)

N = dict(C3=48, D3=50, E3=52, F3=53, G3=55, A3=57, B3=59, C4=60, D4=62, E4=64, F4=65, G4=67, A4=69, B4=71, C5=72,
         D5=74, E5=76)

# (가사, [(음 또는 None, 박)]) ─ 한 줄은 2마디(8박)
VERSE = [
    ("여기는 토트넘 마을", [("E4", .5), ("E4", .5), ("G4", 1), ("E4", .5), ("D4", .5), ("C4", 1), ("D4", .5),
                         ("E4", 2.5), (None, 1)]),
    ("까만 수염 감독님", [("E4", .5), ("E4", .5), ("G4", .5), ("G4", .5), ("A4", 1), ("A4", 1), ("G4", 2),
                       (None, 2)]),
    ("패스 패스 또 패스", [("F4", .5), ("F4", .5), ("A4", .5), ("A4", .5), ("G4", 1), ("E4", 1), ("D4", 2),
                        (None, 2)]),
    ("골키퍼까지 돌려요", [("D4", .5), ("D4", .5), ("E4", .5), ("F4", .5), ("G4", 1), ("G4", .5), ("A4", .5),
                        ("B4", 2), (None, 2)]),
]
CHORUS = [
    ("제르비 제르비 데 제르비", [("C5", .5), ("C5", .5), ("G4", 1), ("A4", .5), ("A4", .5), ("E4", 1), ("F4", .5),
                             ("G4", .5), ("A4", .5), ("G4", 1.5), (None, 1)]),
    ("오늘도 힘을 내요", [("E4", .5), ("F4", .5), ("G4", 1), ("C5", 1), ("B4", .5), ("A4", .5), ("G4", 2),
                       (None, 2)]),
    ("제르비 제르비 데 제르비", [("C5", .5), ("C5", .5), ("G4", 1), ("A4", .5), ("A4", .5), ("E4", 1), ("F4", .5),
                             ("G4", .5), ("A4", .5), ("G4", 1.5), (None, 1)]),
    ("강등만은 안 돼요", [("E4", .5), ("F4", .5), ("G4", 1), ("A4", 1), ("D5", 1), ("B4", 1), ("C5", 3)]),
]
# 마디별 화음(반 마디 단위 2개)
VERSE_CH = ["C", "C", "G", "G", "Am", "Am", "C", "C", "F", "F", "G", "G", "Dm", "G", "G", "G"]
CHORUS_CH = ["C", "Am", "F", "G", "C", "C", "G", "G", "C", "Am", "F", "G", "C", "F", "G", "C"]
CHORDS = {"C": [48, 52, 55], "G": [43, 47, 50], "Am": [45, 48, 52], "F": [41, 45, 48], "Dm": [38, 41, 45],
          "Em": [40, 43, 47]}


def _mono(x):
    return x.astype(np.float32)


def render(parts, shout=True):
    """parts: "intro", "verse", "chorus", "chorus2"(후렴 뒷부분), "outro" 의 나열.
    돌려주는 것: (음악 배열, 가사 타이밍 [(가사, 시작, 끝, [(음절, 시작, 끝)])], 길이)."""
    plan = []  # (종류, 시작 박)
    beat = 0.0
    for p in parts:
        n = {"intro": 4, "verse": 32, "chorus": 32, "chorus2": 16, "chorus_last": 8, "outro": 4}[p]
        plan.append((p, beat, n))
        beat += n
    total = beat * BEAT + 2.0
    mus = np.zeros(int(total * SR), np.float32)
    voc = np.zeros_like(mus)
    lyrics = []

    def put(buf, t, sig, vol=1.0):
        i = int(t * SR)
        if i < 0:
            sig, i = sig[-i:], 0
        j = min(len(buf), i + len(sig))
        if j > i:
            buf[i:j] += sig[: j - i] * vol

    for kind, b0, nb in plan:
        t0 = b0 * BEAT
        if kind in ("intro", "outro"):
            chs = ["C", "C"] if kind == "intro" else ["G", "C"]
            riff = [79, 76, 79, 84, 81, 79, 76, 72] if kind == "intro" else [72, 76, 79, 84]
            for i, m in enumerate(riff):
                put(mus, t0 + i * BEAT / (2 if kind == "intro" else 1), inst("bell", m + KEY, 0.8), 0.22)
        else:
            chs = VERSE_CH if kind == "verse" else CHORUS_CH
            if kind == "chorus2":
                chs = CHORUS_CH[8:]
            elif kind == "chorus_last":
                chs = CHORUS_CH[12:]
        chorus = kind.startswith("chorus")
        nbars = nb // 4
        for bar in range(nbars):
            for half in range(2):
                ch = chs[min(len(chs) - 1, bar * 2 + half)]
                notes = CHORDS[ch]
                tb = t0 + (bar * 4 + half * 2) * BEAT
                # 베이스: 근음-5음 통통
                root = notes[0] + KEY
                root += 12 if root < 36 else 0
                put(mus, tb, inst("bass", root, BEAT * 0.9), 0.34)
                put(mus, tb + BEAT, inst("bass", root + 7, BEAT * 0.9), 0.28)
                # 토이피아노 화음: 뒷박(절) / 매 박(후렴)
                for k in range(2):
                    if chorus or k == 1:
                        for m in notes:
                            put(mus, tb + k * BEAT, inst("piano", m + 12 + KEY, BEAT * 0.8), 0.07)
            for k in range(4):  # 드럼
                tk = t0 + (bar * 4 + k) * BEAT
                if kind == "intro" and k < 2:
                    continue
                if k % 2 == 0:
                    put(mus, tk, drum("k"), 0.5)
                else:
                    put(mus, tk, drum("c"), 0.32)
                    put(mus, tk, drum("s"), 0.12)
                for e in range(2):
                    put(mus, tk + e * BEAT / 2, drum("h"), 0.35 if e else 0.22)
                if chorus:
                    put(mus, tk + BEAT / 2, drum("t"), 0.25)
        if kind in ("verse", "chorus", "chorus2", "chorus_last"):
            lines = {"verse": VERSE, "chorus": CHORUS, "chorus2": CHORUS[2:], "chorus_last": CHORUS[3:]}[kind]
            for li, (words, notes) in enumerate(lines):
                lt = t0 + li * 8 * BEAT
                nts = [(None if n is None else N[n] + KEY, d * BEAT) for n, d in notes]
                y = sing_phrase(words, nts, role="sing", seed=li * 13 + (7 if chorus else 0))
                put(voc, lt - 0.03, y, 1.0)
                if chorus:  # 후렴은 남자 목소리 한 옥타브 아래로 겹쳐 '다 같이' 부르는 느낌
                    y2 = sing_phrase(words, [(None if m is None else m - 12, d) for m, d in nts], role="sing_m",
                                     seed=li * 17)
                    put(voc, lt - 0.02, y2, 0.42)
                # 멜로디를 실로폰으로 한 옥타브 위에서 살짝 따라간다
                syl = [ch for ch in words if "가" <= ch <= "힣"]
                tt, k, marks = lt, 0, []
                for (n, d), (m, dd) in zip(notes, nts):
                    if m is not None:
                        put(mus, tt, inst("xylo", m + 12, min(0.5, dd)), 0.08)
                        marks.append((syl[k], tt, tt + dd))
                        k += 1
                    tt += dd
                lyrics.append((words, lt, marks[-1][2] + 0.25, marks))
                if shout and words == "오늘도 힘을 내요":
                    s = tts("힘내요!", "kids")
                    put(voc, lt + 5.2 * BEAT, s, 0.9)
    vpk = np.max(np.abs(voc)) or 1
    mix = mus * 0.75 + voc / vpk * 0.8
    return mix.astype(np.float32), lyrics, beat * BEAT


def bars_to_sec(b):
    return b * BAR
