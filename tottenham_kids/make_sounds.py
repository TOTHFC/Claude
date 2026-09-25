"""효과음·배경음악을 일레븐랩스(Sound Effects / Music)로 만들어 sfx/, bgm/ 에 저장한다.

한 번 만든 파일은 다시 만들지 않는다(저장소에 들어 있으므로 렌더링에는 키가 필요 없다).
키는 환경 변수 ELEVENLABS_API_KEY 또는 클라우드 환경의 API credentials 로 준다.

    python3 make_sounds.py
"""
import json
import os
import sys

from voice import HERE, el_request

SFX = {  # 이름: (설명, 길이 초)
    "pop": ("cute cartoon pop, bubbly, short, clean", 0.6),
    "twinkle": ("magical sparkle twinkle chime, children's cartoon, bright and short", 1.2),
    "bus_horn": ("cute cartoon bus horn honk twice, toy-like, cheerful", 1.2),
    "fanfare": ("short cheerful cartoon victory fanfare with trumpets, kids show", 2.0),
    "buzz": ("cartoon bee buzzing flying by, playful, not scary", 2.0),
    "henshin": ("magical transformation sequence sound for a kids anime, rising sparkles, whoosh and shimmering chime ending", 2.4),
    "whoosh": ("quick cartoon whoosh swipe transition", 0.6),
    "goal_net": ("soccer ball hitting the goal net, swish, with small crowd reaction", 1.2),
    "sad_trombone": ("sad trombone wah wah wah waaah, comedic failure", 2.6),
    "caw": ("cartoon magpie bird cackling caw caw, mischievous", 1.2),
    "boing": ("cartoon boing bounce, ball bouncing off a tree trunk", 0.7),
    "snore": ("cartoon snoring, cute, zzz, sleepy", 2.0),
    "roar": ("cartoon lion roar, funny, not too scary, kids animation", 1.6),
    "whistle": ("referee whistle, long final whistle, soccer", 1.4),
    "tick": ("clock ticking three times, quiz show countdown", 1.5),
    "dingdong": ("quiz show correct answer ding dong dang chime, xylophone, bright", 1.4),
    "wrong": ("quiz show wrong answer buzzer, comedic", 1.0),
    "cheer": ("group of kids cheering yay and clapping, excited, short", 2.2),
    "crickets": ("awkward silence, crickets chirping, comedic", 2.0),
    "crowd_angry": ("cartoon crowd of villagers grumbling and complaining, booing, comedic", 2.4),
    "chime": ("bright bell chime, lesson of the day jingle in a kids show, short", 1.6),
    "thunder": ("dramatic thunder crack and rumble, cartoon villain reveal", 2.0),
    "gulp": ("cartoon nervous gulp swallow", 0.8),
    "plane": ("small cartoon airplane flying by overhead", 2.4),
    "coins": ("cash register ka-ching with coins, cartoon", 1.2),
    "stamp": ("big rubber stamp thump, comedic impact", 0.6),
    "slide": ("cartoon slide whistle going up", 0.9),
    "shooting_star": ("gentle magical shooting star shimmer across the sky", 1.8),
}

BGM = {  # 이름: (설명, 길이 초)
    "village": ("Cheerful Korean children's TV animation background music, instrumental, ukulele, glockenspiel, "
                "light claps, whistling melody, bouncy and warm, major key, 118 bpm, no vocals", 30),
    "match": ("Playful sneaky cartoon soccer match background music for a kids animation, instrumental, pizzicato "
              "strings, bassoon, snare drum, light tension but comedic, no vocals", 30),
    "montage": ("Comedic sad cartoon background music for a losing streak montage in a kids show, instrumental, tuba, "
                "clarinet, slow oom-pah, gently silly, no vocals", 30),
    "quiz": ("Bright quiz show background music for a children's TV program, instrumental, marimba, synth bells, "
             "ticking rhythm, playful anticipation, no vocals", 15),
    "angry": ("Comedic tense cartoon background music, grumpy villagers marching, instrumental, low brass, timpani, "
              "staccato strings, no vocals", 15),
    "night": ("Gentle lullaby for a kids animation night scene, instrumental, music box, soft piano, warm strings, "
              "tender and hopeful, no vocals", 25),
    "lesson": ("Warm heartwarming ending background music for a children's TV episode, instrumental, acoustic guitar, "
               "glockenspiel, soft and positive, no vocals", 15),
    "preview": ("Dramatic cartoon villain theme for a next episode preview in a kids show, instrumental, organ, low "
                "brass, timpani, spooky but funny, no vocals", 15),
}


def main():
    only = set(sys.argv[1:])
    for folder, table, kind in (("sfx", SFX, "sfx"), ("bgm", BGM, "bgm")):
        os.makedirs(os.path.join(HERE, folder), exist_ok=True)
        for name, (desc, dur) in table.items():
            if only and name not in only:
                continue
            out = os.path.join(HERE, folder, f"{name}.mp3")
            if os.path.exists(out) and not only:
                continue
            if kind == "sfx":
                data = el_request("/v1/sound-generation",
                                  {"text": desc, "duration_seconds": dur, "prompt_influence": 0.6})
            else:
                data = el_request("/v1/music", {"prompt": desc, "music_length_ms": int(dur * 1000),
                                                "force_instrumental": True})
            with open(out, "wb") as f:
                f.write(data)
            print(folder, name, len(data))
    with open(os.path.join(HERE, "sounds.json"), "w") as f:
        json.dump({"sfx": SFX, "bgm": BGM}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
