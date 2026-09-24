"""목소리: edge-tts 한국어 음성 합성(캐시) + 음절 단위 PSOLA로 노래 부르기."""
import asyncio
import hashlib
import json
import os
import ssl
import subprocess

import numpy as np

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "voice_cache")

VOICES = {  # 배역: (음성, 속도, 높낮이)
    "nar": ("ko-KR-SunHiNeural", "+12%", "+12Hz"),      # 해설 누나
    "dz": ("ko-KR-InJoonNeural", "+4%", "-4Hz"),        # 데 제르비
    "koko": ("ko-KR-SunHiNeural", "+14%", "+70Hz"),     # 꼬꼬(수탉)
    "kids": ("ko-KR-SunHiNeural", "+8%", "+90Hz"),      # 어린이 합창
    "kane": ("ko-KR-HyunsuMultilingualNeural", "+10%", "-12Hz"),
    "son": ("ko-KR-HyunsuMultilingualNeural", "-4%", "+14Hz"),
    "villain": ("ko-KR-InJoonNeural", "+4%", "-34Hz"),
    "fan": ("ko-KR-HyunsuMultilingualNeural", "+12%", "+4Hz"),
    "sing": ("ko-KR-SunHiNeural", "-22%", "+0Hz"),
    "sing_kid": ("ko-KR-SunHiNeural", "-22%", "+80Hz"),
    "sing_m": ("ko-KR-InJoonNeural", "-22%", "+0Hz"),
}


def _ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _synth(text, voice, rate, pitch, out, words=None):
    import edge_tts
    import edge_tts.communicate as comm
    ca = "/root/.ccr/ca-bundle.crt"
    if os.path.exists(ca):
        comm._SSL_CTX = ssl.create_default_context(cafile=ca)

    async def go():
        if words is None:
            await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(out)
            return
        c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
        marks = []
        with open(out, "wb") as f:
            async for ch in c.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    marks.append([ch["text"], ch["offset"] / 1e7, ch["duration"] / 1e7])
        with open(words, "w") as f:
            json.dump(marks, f, ensure_ascii=False)
    for _ in range(4):
        try:
            asyncio.run(go())
            if os.path.getsize(out) > 0:
                return
        except Exception as e:  # 네트워크 오류는 재시도
            err = e
    raise RuntimeError(f"TTS 실패: {text} ({err})")


def tts(text, role="nar", trim=True):
    """대사를 합성해 44.1kHz mono float32 배열로 돌려준다(voice_cache 에 mp3 캐시)."""
    voice, rate, pitch = VOICES[role]
    key = hashlib.md5(f"{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()[:16]
    mp3 = os.path.join(CACHE, f"{role}_{key}.mp3")
    if not os.path.exists(mp3) or os.path.getsize(mp3) == 0:
        os.makedirs(CACHE, exist_ok=True)
        _synth(text, voice, rate, pitch, mp3)
    raw = subprocess.run([_ffmpeg(), "-v", "error", "-i", mp3, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    if trim:
        a = trim_silence(a)
    return a


def tts_words(text, role="sing"):
    """문장을 합성하고 단어별 (단어, 시작, 길이) 표시를 함께 돌려준다(무음 자르지 않음)."""
    voice, rate, pitch = VOICES[role]
    key = hashlib.md5(f"W|{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()[:16]
    mp3 = os.path.join(CACHE, f"{role}_w_{key}.mp3")
    js = mp3[:-4] + ".json"
    if not (os.path.exists(mp3) and os.path.exists(js)):
        os.makedirs(CACHE, exist_ok=True)
        _synth(text, voice, rate, pitch, mp3, words=js)
    raw = subprocess.run([_ffmpeg(), "-v", "error", "-i", mp3, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy(), json.load(open(js))


def tts_marks(text, role="nar"):
    """대사 음성(앞뒤 무음 제거)과 단어별 [(단어, 시작, 끝)] 초 단위 표시."""
    a, marks = tts_words(text, role)
    env = np.convolve(np.abs(a), np.ones(256) / 256, "same")
    idx = np.where(env > 0.012)[0]
    s0 = max(0, idx[0] - int(0.02 * SR)) if len(idx) else 0
    e0 = min(len(a), idx[-1] + int(0.02 * SR)) if len(idx) else len(a)
    shift = idx[0] / SR - marks[0][1] if len(idx) and marks else 0.0
    out = [(w, st + shift - s0 / SR, st + du + shift - s0 / SR) for w, st, du in marks]
    return a[s0:e0], out


def trim_silence(a, thr=0.012, pad=0.02):
    env = np.convolve(np.abs(a), np.ones(256) / 256, "same")
    idx = np.where(env > thr)[0]
    if not len(idx):
        return a
    s = max(0, idx[0] - int(pad * SR))
    e = min(len(a), idx[-1] + int(pad * SR))
    return a[s:e]


def envelope(a, fps=24):
    """프레임별 입 벌림(0~1) ─ 립싱크용."""
    hop = SR // fps
    n = len(a) // hop + 1
    out = np.zeros(n)
    for i in range(n):
        seg = a[i * hop:(i + 1) * hop]
        if len(seg):
            out[i] = np.sqrt(np.mean(seg ** 2))
    m = np.percentile(out, 95) or 1
    return np.clip(out / m, 0, 1)


# ------------------------------------------------------------------ 노래

def midi_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def _intensity(a):
    import parselmouth
    it = parselmouth.Sound(a.astype(np.float64), SR).to_intensity(minimum_pitch=120, time_step=0.005)
    db = np.clip(it.values[0], 0, None)
    return it.xs(), np.convolve(db, np.ones(3) / 3, "same")


def split_syllables(a, n):
    """단어 음성을 음절 n개로 자른다: 모음(세기 봉우리) n개를 찾고 그 사이 골짜기에서 자른다."""
    from scipy.signal import find_peaks
    if n == 1:
        return [a]
    ts, db = _intensity(a)
    L = len(a) / SR
    pk, pr = find_peaks(db, distance=10, prominence=1.5)
    if len(pk) >= n:
        keep = np.sort(pk[np.argsort(pr["prominences"])[::-1][:n]])
        cuts = [0.0]
        for p0, p1 in zip(keep[:-1], keep[1:]):
            cuts.append(float(ts[p0 + np.argmin(db[p0:p1 + 1])]))
        cuts.append(L)
    else:  # 봉우리가 모자라면 균등 분할
        cuts = list(np.linspace(0, L, n + 1))
    return [a[int(cuts[i] * SR):int(cuts[i + 1] * SR)] for i in range(n)]


def sing_phrase(text, notes, role="sing", vib=True, seed=0, legato=0.5):
    """text 를 한 번에 읽힌 뒤 음절로 나눠 notes[(midi, 초)] 대로 부른다. 쉼표는 midi=None."""
    syls = [ch for ch in text if "가" <= ch <= "힣"]
    sung = [x for x in notes if x[0] is not None]
    assert len(syls) == len(sung), (text, len(syls), len(sung))
    audio, marks = tts_words(text, role)
    ts, db = _intensity(audio)
    onset = ts[np.argmax(db > 30)]
    shift = onset - marks[0][1]  # mp3 앞 여백만큼 표시가 앞당겨져 있다
    words = [w for w in text.split() if any("가" <= ch <= "힣" for ch in w)]
    assert len(marks) >= len(words), (text, marks)
    bounds = [m[1] + shift for m in marks[:len(words)]] + [marks[len(words) - 1][1] + marks[len(words) - 1][2] + shift + 0.06]
    chunks = []
    for wi, word in enumerate(words):
        ws = [ch for ch in word if "가" <= ch <= "힣"]
        seg = audio[int(max(0, bounds[wi] - 0.01) * SR):int(bounds[wi + 1] * SR)]
        chunks += split_syllables(seg, len(ws))
    out, k = [], 0
    for midi, dur in notes:
        if midi is None:
            out.append(np.zeros(int(dur * SR), np.float32))
            continue
        # 짧은 음은 통통 튀게(스타카토) 불러 늘어짐을 줄이고, 긴 음(0.5초 이상)만 끝까지 끈다
        nat = len(chunks[k]) / SR
        sing = dur if dur >= legato else min(dur * 0.95, max(nat * 1.15, dur * 0.7))
        y = sing_chunk(chunks[k], midi, sing, vib=vib, seed=seed + k)
        out.append(np.pad(y, (0, int(dur * SR) - len(y))))
        k += 1
    return np.concatenate(out)


def sing_syllable(syl, midi, dur, role="sing", vib=True, seed=0):
    return sing_chunk(tts(syl, role), midi, dur, vib=vib, seed=seed)


def sing_chunk(a, midi, dur, vib=True, seed=0):
    """음절 조각의 음높이를 고정하고 모음 구간을 늘려 dur 초로 만든다(PSOLA)."""
    import parselmouth
    from parselmouth.praat import call
    a = np.pad(a.astype(np.float64), (int(0.01 * SR), int(0.01 * SR)))
    snd = parselmouth.Sound(a, SR)
    f0 = midi_hz(midi)
    pitch = snd.to_pitch(time_step=0.01, pitch_floor=70, pitch_ceiling=500)
    freqs = pitch.selected_array["frequency"]
    times = pitch.xs()
    voiced = times[freqs > 0]
    L = snd.duration
    v0, v1 = (voiced[0], voiced[-1]) if len(voiced) > 2 else (L * 0.2, L * 0.8)
    a0 = min(v0 + 0.035, L * 0.5)          # 자음+모음 시작은 그대로
    a1 = max(a0 + 0.02, min(v1 - 0.03, L))  # 끝소리(받침)도 그대로
    fixed = a0 + (L - a1)
    target = max(dur, fixed + 0.04)
    k = (target - fixed) / max(1e-3, a1 - a0)
    manip = call(snd, "To Manipulation", 0.01, 70, 500)
    dt = call("Create DurationTier", "d", 0, L)
    for t_, v_ in ((0, 1.0), (a0 - 1e-3, 1.0), (a0, k), (a1, k), (a1 + 1e-3, 1.0), (L, 1.0)):
        call(dt, "Add point", max(0.0, min(L, t_)), v_)
    call([manip, dt], "Replace duration tier")
    pt = call("Create PitchTier", "p", 0, L)
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.28)
    for t_ in np.arange(0, L + 0.005, 0.005):
        # 원래 시간축 기준. 늘어난 구간에서 비브라토가 너무 느려지지 않게 k로 보정
        out_t = t_ if t_ < a0 else (a0 + (min(t_, a1) - a0) * k + max(0, t_ - a1))
        cents = 0.0
        if vib and out_t > 0.22:
            depth = min(1.0, (out_t - 0.22) / 0.2) * 32
            cents = depth * np.sin(2 * np.pi * 5.6 * out_t + ph)
        if out_t < 0.05:  # 살짝 아래에서 올려 부르기
            cents -= 60 * (1 - out_t / 0.05)
        call(pt, "Add point", t_, f0 * 2 ** (cents / 1200))
    call([manip, pt], "Replace pitch tier")
    out = call(manip, "Get resynthesis (overlap-add)")
    y = out.values[0].astype(np.float32)
    n = int(dur * SR)
    y = y[:n] if len(y) >= n else np.pad(y, (0, n - len(y)))
    fade = min(len(y), int(0.03 * SR))
    y[-fade:] *= np.linspace(1, 0, fade)
    y[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    return y
