"""내레이션·효과음·배경음악을 일레븐랩스로 만들어 저장(이미 있으면 건너뜀)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tottenham_kids"))
import voice as V  # noqa: E402

from narration import LINES, NARRATOR  # noqa: E402

V.CACHE = os.path.join(HERE, "voice_cache")

SFX = {
    "blip": ("soft modern UI blip for infographic animation, clean, short", 0.5),
    "whoosh": ("smooth soft whoosh transition for motion graphics, clean", 0.8),
    "tick": ("fast number counter ticking up, digital, subtle", 1.2),
    "impact": ("deep cinematic impact hit with low boom, news breaking", 1.6),
    "chime": ("clean bright notification chime, positive", 1.0),
    "slide": ("paper card sliding in, soft swipe, motion graphics", 0.6),
    "pop": ("small clean pop for chart bars appearing", 0.5),
}
BGM = {
    "main": ("Modern minimal infographic news background music, instrumental, soft electronic pulse, light piano, "
             "subtle percussion, confident and clean, 100 bpm, no vocals", 60),
    "tense": ("Tense documentary underscore for breaking news, instrumental, low synth drone, ticking pulse, "
              "subtle strings, serious, no vocals", 30),
}


def main():
    for lid, sub, spoken in LINES:
        a = V.eleven_one(spoken, NARRATOR, None)
        print("line", lid, round(len(a) / V.SR, 2))
    for folder, table, kind in (("sfx", SFX, "sfx"), ("bgm", BGM, "bgm")):
        os.makedirs(os.path.join(HERE, folder), exist_ok=True)
        for name, (desc, dur) in table.items():
            out = os.path.join(HERE, folder, f"{name}.mp3")
            if os.path.exists(out):
                continue
            if kind == "sfx":
                data = V.el_request("/v1/sound-generation", {"text": desc, "duration_seconds": dur,
                                                             "prompt_influence": 0.6})
            else:
                data = V.el_request("/v1/music", {"prompt": desc, "music_length_ms": dur * 1000,
                                                  "force_instrumental": True})
            open(out, "wb").write(data)
            print(folder, name, len(data))


if __name__ == "__main__":
    main()
