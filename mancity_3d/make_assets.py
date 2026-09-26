"""대사·효과음·배경음악을 만들고(일레븐랩스, 이미 있으면 건너뜀) 장면 타임라인과 오디오를 만든다.

    python3 make_assets.py        # -> web/timeline.json, _audio.wav
"""
import json
import os
import shutil
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KIDS = os.path.join(HERE, "..", "tottenham_kids")
sys.path.insert(0, KIDS)
import voice as V  # noqa: E402

from story import GAP, LINES, NAMES, POPS, SCENES, TEMPO, VOICES  # noqa: E402

V.CACHE = os.path.join(HERE, "voice_cache")
SR = V.SR
FPS = 30

SFX = {  # 이름: (설명, 길이 초)
    "doorbell": ("cartoon doorbell ding dong, bright, clean", 1.2),
    "thud": ("huge heavy stack of paper documents slamming down on a wooden desk, comedic big thud with paper rustle", 1.4),
    "impact": ("punchy cartoon title hit, whoosh into boom, comedic", 1.4),
    "creak": ("old metal balance scale tilting with a long creak, cartoon", 1.2),
    "vault": ("heavy bank vault door unlocking and swinging open, clunk and creak", 1.8),
    "poof": ("cartoon magic smoke poof, disguise transformation, comedic", 0.8),
    "gavel": ("judge gavel banging twice on wooden block, courtroom", 1.2),
    "scratch": ("vinyl record scratch, comedic stop", 0.8),
    "ding": ("game show correct bell ding, bright", 1.0),
    "knock": ("polite knocking on a wooden door three times", 1.2),
    "flip": ("single calendar page flipping quickly, paper flick", 0.5),
    "tiptoe": ("cartoon sneaky tiptoe footsteps, pizzicato-like comedic sneaking", 1.6),
    "pipe": ("cartoon pneumatic tube whoosh, object shooting through a pipe", 1.0),
    "bonk": ("cartoon bonk on the head, hollow comedic hit", 0.6),
    "wheel": ("prize wheel spinning, fast plastic clicker ticking, game show", 4.0),
    "screech": ("cartoon brake screech, sudden stop", 0.8),
    "paper": ("newspaper spinning in and landing, old movie newspaper headline effect", 1.2),
    "sigh": ("tired disappointed crowd sigh, comedic", 1.2),
    "boom": ("deep cinematic meme bass boom hit, huge low impact with short reverb tail", 1.6),
    "dun": ("dramatic suspense sting dun dun duuun, orchestral, comedic meme", 1.4),
    "rewind": ("VHS tape rewinding sound, fast whirring with pitch-shifted squeaky reversed audio", 1.6),
    "whip": ("very fast whip pan whoosh transition, airy and punchy", 0.5),
    "swish": ("short snappy cartoon text pop swoosh with a light click", 0.5),
    "slam": ("door slamming shut hard, cartoon", 0.7),
}
REUSE = ["whoosh", "boing", "stamp", "coins", "pop", "crickets", "popper", "tick", "sad_trombone", "chime"]
BGM = {
    "hype": ("Energetic funny meme background music for a fast YouTube explainer, instrumental, bouncy synth bass, "
             "punchy drums, playful pizzicato and brass stabs, 124 bpm, high energy, no vocals", 100),
    "sneaky": ("Comedic sneaky heist background music for a 3D animated explainer, instrumental, pizzicato strings, "
               "muted trumpet, walking upright bass, brushed snare, playful mischief, 110 bpm, no vocals", 75),
    "news": ("Retro newsreel documentary background music, instrumental, brisk strings, snare rolls, light brass, "
             "comedic seriousness, no vocals", 35),
    "court": ("Comedic courtroom drama background music, instrumental, low strings, timpani, suspenseful organ, "
              "overly dramatic but funny, no vocals", 40),
    "gameshow": ("Upbeat TV game show wheel of fortune background music, instrumental, funky bass, synth brass, "
                 "cheesy and exciting, no vocals", 35),
    "outro": ("Light comedic ending theme for an animated explainer, instrumental, ukulele, glockenspiel, whistling, "
              "slightly ironic, no vocals", 25),
}


def gen_sounds():
    for name in REUSE:
        dst = os.path.join(HERE, "sfx", f"{name}.mp3")
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(os.path.join(KIDS, "sfx", f"{name}.mp3"), dst)
    for folder, table, kind in (("sfx", SFX, "sfx"), ("bgm", BGM, "bgm")):
        os.makedirs(os.path.join(HERE, folder), exist_ok=True)
        for name, (desc, dur) in table.items():
            out = os.path.join(HERE, folder, f"{name}.mp3")
            if os.path.exists(out):
                continue
            if kind == "sfx":
                data = V.el_request("/v1/sound-generation",
                                    {"text": desc, "duration_seconds": dur, "prompt_influence": 0.6})
            else:
                data = V.el_request("/v1/music", {"prompt": desc, "music_length_ms": int(dur * 1000),
                                                  "force_instrumental": True})
            with open(out, "wb") as f:
                f.write(data)
            print(folder, name, len(data), flush=True)


def gen_voices():
    out = {}
    for lid, (spk, sub, spoken) in LINES.items():
        a = V.eleven_one(spoken, VOICES[spk], None)
        if a is None:
            raise SystemExit(f"voice failed: {lid}")
        a = V.trim_silence(a.astype(np.float32), 0.01, 0.03)
        out[lid] = stretch(a, TEMPO)
    return out


def stretch(a, k):
    """음높이를 유지한 채 k 배 빠르게(ffmpeg atempo)."""
    if abs(k - 1) < 1e-3:
        return a
    import subprocess
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    p = subprocess.run([ff, "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", f"atempo={k}",
                        "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"], input=a.astype(np.float32).tobytes(),
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()


def env30(a):
    hop = SR // FPS
    n = len(a) // hop + 1
    e = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2)) if len(a[i * hop:(i + 1) * hop]) else 0
                  for i in range(n)])
    m = np.percentile(e, 92) or 1
    return [round(float(x), 2) for x in np.clip(e / m, 0, 1)]


def build_timeline(audio):
    lines, marks, sfx, scenes = {}, {}, [], []
    t0 = 0.0
    for sc in SCENES:
        cur = 0.0
        for ev in sc["ev"]:
            k = ev[0]
            if k == "wait":
                cur += ev[1]
            elif k == "say":
                gap = ev[2] if len(ev) > 2 else GAP
                st = cur + gap
                d = len(audio[ev[1]]) / SR
                spk, sub, _ = LINES[ev[1]]
                lines[ev[1]] = {"t": round(t0 + st, 3), "end": round(t0 + st + d, 3), "spk": spk, "sub": sub,
                                "name": NAMES[spk], "env": env30(audio[ev[1]])}
                cur = st + d
            elif k == "mark":
                marks[ev[1]] = round(t0 + cur, 3)
            elif k == "markln":
                ln = lines[ev[2]]
                marks[ev[1]] = round(ln["t"] + (ln["end"] - ln["t"]) * ev[3], 3)
            elif k == "sfx":
                sfx.append((t0 + cur + (ev[3] if len(ev) > 3 else 0), ev[1], ev[2]))
        scenes.append({"name": sc["name"], "start": round(t0, 3), "dur": round(cur, 3), "music": sc["music"]})
        t0 += cur
    return {"scenes": scenes, "lines": lines, "marks": marks, "total": round(t0, 3), "fps": FPS}, sfx


def auto_sfx(tl):
    """애니메이션에 딸린 효과음(장면 전환, 도장, 달력 넘김 등)과 큰 글자."""
    m, out = tl["marks"], []
    for sc in tl["scenes"][1:]:
        out.append((sc["start"] - 0.22, "whip", 0.7))
    out += [(m["rewind"], "rewind", 0.9), (m["drop"] - 0.35, "whoosh", 0.6), (m["drop"] + 0.2, "thud", 1.0)]
    for i in range(5):
        out.append((m["buy"] + 0.25 + i * 0.4, "pop", 0.5))
    for k in ("sign1", "sign2", "sign3"):
        out.append((m[k], "pop", 0.6))
    out += [(m["walk"], "tiptoe", 0.7), (m["hop"], "boing", 0.5), (m["land"], "coins", 0.7),
            (m["balance"], "creak", 0.6), (m["stamp54"], "stamp", 1.0), (m["env1"], "pop", 0.6),
            (m["pipe"], "pipe", 0.8), (m["pipe"] + 0.75, "bonk", 0.9)]
    for k in ("st14", "st5", "st7"):
        out.append((m[k], "stamp", 1.0))
    out += [(m["knock"], "knock", 0.9), (m["slam"], "slam", 0.9)]
    t = m["years"]
    while t < m["yearsend"]:
        out.append((t, "flip", 0.45))
        t += 0.22
    for k in ("p2018", "p2020", "p2023", "p2024"):
        out.append((m[k], "pop", 0.6))
    out += [(m["p2018"] + 0.1, "paper", 0.6), (m["cas"], "stamp", 0.8), (m["snail"] + 0.3, "crickets", 0.6)]
    t, n, dt = m["stamps"], 0, 0.2
    while n < 24:
        out.append((t, "stamp", 0.45))
        t += dt
        dt = max(0.055, dt * 0.87)
        n += 1
    m["stampend"] = round(max(m["stampend"], t + 0.15), 3)
    out += [(m["cheer"], "popper", 0.7), (m["grab"], "screech", 0.8), (m["end"], "chime", 0.5)]
    for k in range(6):
        out.append((m["spin"] + k * 3.6, "wheel", 0.7 - k * 0.07))
    pops = []
    for mk, d, txt, col in POPS:
        tt = round(m[mk] + d, 3)
        pops.append({"t": tt, "text": txt, "color": col})
        out.append((tt, "swish", 0.6))
    tl["pops"] = pops
    return out, m["grab"]


def decode(path):
    return V._decode(path)


def norm_sfx(name):
    a = decode(os.path.join(HERE, "sfx", f"{name}.mp3"))
    env = np.convolve(np.abs(a), np.ones(441) / 441, "same")
    idx = np.where(env > 0.01)[0]
    if len(idx):
        a = a[max(0, idx[0] - 200):idx[-1] + 4410]
    rms = np.sqrt(np.mean(a ** 2)) + 1e-9
    a = a * min(0.18 / rms, 0.9 / (np.abs(a).max() + 1e-9))
    f = min(len(a), 2205)
    a[-f:] *= np.linspace(1, 0, f)
    return a.astype(np.float32)


def bgm(name, dur, offset=0.0, fade_in=0.6, fade_out=1.2):
    a = decode(os.path.join(HERE, "bgm", f"{name}.mp3"))
    env = np.convolve(np.abs(a), np.ones(441) / 441, "same")
    idx = np.where(env > 0.005)[0]
    a = a[idx[0]:idx[-1]]
    a = a * (0.11 / (np.sqrt(np.mean(a ** 2)) + 1e-9))
    xf = int(2.0 * SR)
    out = a.copy()
    need = int((offset + dur) * SR) + 10
    while len(out) < need:
        r = np.linspace(0, 1, xf)
        out[-xf:] = out[-xf:] * (1 - r) + a[:xf] * r
        out = np.concatenate([out, a[xf:]])
    seg = out[int(offset * SR):int(offset * SR) + int(dur * SR)].copy()
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    seg[:fi] *= np.linspace(0, 1, fi)
    seg[-fo:] *= np.linspace(1, 0, fo)
    return seg.astype(np.float32)


def mix(tl, audio, sfx, wheel_until):
    total = tl["total"]
    n = int((total + 2) * SR)
    voice, fx, music = (np.zeros(n, np.float32) for _ in range(3))

    def put(buf, t, a, v=1.0):
        i = max(0, int(t * SR))
        j = min(len(buf), i + len(a))
        if j > i:
            buf[i:j] += a[: j - i] * v

    for lid, ln in tl["lines"].items():
        put(voice, ln["t"], audio[lid])
    cache = {}
    for t, name, v in sfx:
        if name not in cache:
            cache[name] = norm_sfx(name)
        a = cache[name]
        if name == "wheel":  # 손으로 잡는 순간 끊는다
            a = a[:max(0, int((wheel_until - t) * SR))].copy()
            if len(a) > 2205:
                a[-2205:] *= np.linspace(1, 0, 2205)
        put(fx, t, a, v)
    # 배경음악: 같은 곡이 이어지는 장면은 끊지 않는다
    runs = []
    for sc in tl["scenes"]:
        if runs and runs[-1][0] == sc["music"]:
            runs[-1][2] = sc["start"] + sc["dur"]
        else:
            runs.append([sc["music"], sc["start"], sc["start"] + sc["dur"]])
    for name, a0, a1 in runs:
        put(music, a0, bgm(name, a1 - a0 + 0.6, 0.0, 0.4, 1.0))
    hop = 441
    env = np.array([np.abs(voice[i:i + hop]).max() for i in range(0, n, hop)])
    sp = env > 0.02
    g = np.ones(len(sp))
    lvl = 1.0
    for i in range(len(sp) - 1, -1, -1):
        lvl = 0.0 if sp[i] else min(1.0, lvl + 1 / 6)
        g[i] = lvl
    f = 1.0
    for i in range(len(g)):
        f = g[i] if g[i] < f else min(g[i], f + 1 / 50)
        g[i] = f
    gain = np.repeat(1.0 - 0.42 * (1.0 - g), hop)[:n]
    out = voice + fx * 0.55 + music * gain * 1.25
    out = np.tanh(out * 1.1) / np.tanh(1.1)
    return (out / (np.abs(out).max() + 1e-9) * 0.89)[: int(total * SR)]


def main():
    gen_sounds()
    audio = gen_voices()
    tl, sfx = build_timeline(audio)
    extra, wheel_until = auto_sfx(tl)
    buf = mix(tl, audio, sfx + extra, wheel_until)
    with open(os.path.join(HERE, "web", "timeline.json"), "w") as f:
        json.dump(tl, f, ensure_ascii=False)
    with wave.open(os.path.join(HERE, "_audio.wav"), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((buf * 32767).astype(np.int16).tobytes())
    print("total", tl["total"], [(s["name"], s["dur"]) for s in tl["scenes"]])


if __name__ == "__main__":
    main()
