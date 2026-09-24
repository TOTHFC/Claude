"""'When the Saints Go Marching In'(=When the Spurs Go Marching In) 8비트 편곡.

원곡은 작자 미상의 미국 전통 가스펠(퍼블릭 도메인)이다. 토트넘 팬들은 "Saints"를 "Spurs"로 바꿔 부른다.
"""
import numpy as np

from engine import SR, drum, freq, noise, tone

# 16마디, 4분음표 단위. "."=쉼표, "-"=앞 음 유지
MELODY = (". C5 E5 F5 | G5 - - - | . C5 E5 F5 | G5 - - - | . C5 E5 F5 | G5 - E5 - | C5 - E5 - | D5 - - - | "
          ". E5 E5 D5 | C5 - - C5 | E5 - G5 G5 | F5 - - - | . E5 F5 G5 | E5 - C5 - | D5 - - - | C5 - - - ")
CHORDS = ["C", "C", "C", "C", "C", "C", "C", "G", "C", "C", "C7", "F", "C", "C", "G", "C"]

TRIADS = {"C": ["C", "E", "G"], "C7": ["C", "E", "Bb"], "F": ["F", "A", "C"], "G": ["G", "B", "D"],
          "Cm": ["C", "Eb", "G"], "Fm": ["F", "Ab", "C"]}
MINOR_MAP = {"E": "Eb", "A": "Ab", "B": "Bb"}


def _notes():
    toks = [x for x in MELODY.split() if x != "|"]
    ev, i = [], 0
    while i < len(toks):
        n = 1
        while i + n < len(toks) and toks[i + n] == "-":
            n += 1
        if toks[i] != ".":
            ev.append((i, n, toks[i]))
        i += n
    return ev, len(toks)


def _minorize(n):
    name = n[:-1]
    return (MINOR_MAP.get(name, name)) + n[-1] if name in MINOR_MAP else n


SCALE = ["C", "D", "E", "F", "G", "A", "B"]


def _third_below(n):
    """C장조 음계에서 3도 아래 음."""
    name, octv = n[:-1], int(n[-1])
    i = SCALE.index(name[0])
    j = i - 2
    if j < 0:
        j += 7
        octv -= 1
    return f"{SCALE[j]}{octv}"


def _f(n, transpose):
    return freq(n) * 2 ** (transpose / 12)


def saints(m, t0, dur, bpm=150, transpose=0, minor=False, lead="sq", duty=0.25, vol=0.085, harmony=True,
           bass=True, drums="march", start_bar=0, echo=False):
    """t0부터 dur초 동안 반복 재생."""
    beat = 60.0 / bpm
    ev, nbeats = _notes()
    loop = nbeats * beat
    base = -start_bar * 4 * beat
    while base < dur:
        for (si, n, note) in ev:
            st = base + si * beat
            if st < 0 or st >= dur:
                continue
            nn = _minorize(note) if minor else note
            ln = min(n * beat * 0.92, dur - st)
            m.add(t0 + st, tone(lead, _f(nn, transpose), ln, vol, duty, decay=None if lead != "tri" else 0.6))
            if echo:
                m.add(t0 + st + beat * 0.5, tone(lead, _f(nn, transpose), ln * 0.5, vol * 0.3, duty))
            if harmony and n >= 2:
                lo = _third_below(note)
                lo = _minorize(lo) if minor else lo
                m.add(t0 + st, tone("sq", _f(lo, transpose), ln, vol * 0.35, 0.125))
        for bar in range(nbeats // 4):
            bt = base + bar * 4 * beat
            if bt < 0 or bt >= dur:
                continue
            ch = CHORDS[bar]
            if minor:
                ch = {"C": "Cm", "C7": "Cm", "F": "Fm"}.get(ch, ch)
            tri = TRIADS[ch]
            root = tri[0]
            fifth = tri[2]
            if bass:
                for k, (nn, octv) in enumerate([(root, 2), (fifth, 2), (root, 2), (fifth, 1)]):
                    st = bt + k * beat
                    if st < dur:
                        m.add(t0 + st, tone("tri", _f(f"{nn}{octv + 1}", transpose), beat * 0.8, 0.2))
            if harmony:
                for k in (1, 3):
                    st = bt + k * beat
                    if st >= dur:
                        continue
                    for nn in tri[1:]:
                        m.add(t0 + st, tone("sq", _f(f"{nn}4", transpose), beat * 0.35, vol * 0.28, 0.5))
            if drums:
                pat = {"march": "k s k s", "fast": "k s k s", "roll": "k s s s", "soft": "k . k ."}[drums]
                for k, tk in enumerate(pat.split()):
                    st = bt + k * beat
                    if tk != "." and st < dur:
                        m.add(t0 + st, drum(tk) * (0.8 if drums != "soft" else 0.5))
                    if drums in ("march", "roll") and st + beat / 2 < dur:
                        m.add(t0 + st + beat / 2, drum("h"))
        base += loop


def saints_intro(m, t0, bpm=160, transpose=0, vol=0.09):
    """첫 소절(Oh when the Spurs)만 짧게 — 징글/팡파르용. 길이를 반환."""
    beat = 60.0 / bpm
    seq = [("C5", 1), ("E5", 1), ("F5", 1), ("G5", 3)]
    t = t0
    for n, b in seq:
        m.add(t, tone("sq", _f(n, transpose), b * beat * 0.9, vol, 0.25))
        m.add(t, tone("sq", _f(n, transpose - 5), b * beat * 0.9, vol * 0.5, 0.5))
        t += b * beat
    m.add(t0, tone("tri", _f("C3", transpose), 6 * beat * 0.9, 0.2))
    return t - t0


def saints_outro(m, t0, bpm=90, minor=True, vol=0.09):
    """마지막 소절(go marching in)을 느린 단조로 — 게임오버 징글."""
    beat = 60.0 / bpm
    seq = [("E5", 1), ("F5", 1), ("G5", 1), ("E5", 2), ("C5", 2), ("D5", 2), ("C5", 4)]
    t = t0
    for n, b in seq:
        nn = _minorize(n) if minor else n
        m.add(t, tone("sq", freq(nn), b * beat * 0.9, vol, 0.5, decay=1.2))
        t += b * beat
    m.add(t0, tone("tri", freq("C3"), (t - t0), 0.18))
    return t - t0
