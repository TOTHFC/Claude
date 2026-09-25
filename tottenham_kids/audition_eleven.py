"""일레븐랩스 배역 오디션: 한국어 공유 목소리 라이브러리에서 배역별 후보를 골라 들어 보고
발음(음성 인식 일치도)이 가장 좋은 목소리를 eleven_voices.json 에 저장한다.

    키가 환경 변수(ELEVENLABS_API_KEY) 또는 클라우드 환경의 API credentials(api.elevenlabs.io,
    헤더 xi-api-key)로 등록된 상태에서:
    python3 audition_eleven.py     # _audition/el_*.mp3 + eleven_voices.json + eleven_audition.txt
    python3 make_kids.py           # 대사를 일레븐랩스로 새로 합성해 렌더링

공유 라이브러리 목소리를 API로 쓰려면 유료 요금제가 필요할 수 있다. 안 되면 기본(premade) 목소리로 고른다.
"""
import difflib
import json
import os
import re
import urllib.parse

from voice import EL_CAST_FILE, HERE, eleven_available, eleven_one, el_request

SAMPLE = {
    "nar": ("어린이 여러분, 지금 토트넘은 몇 등일까요?", "happy"),
    "dz": ("우와, 이 정도면 우승이야!", "happy"),
    "koko": ("꼬꼬댁, 17등으로 살았다!", "happy"),
    "kids": ("퀴즈 타임!", "happy"),
    "kane": ("난 잘 지내! 발롱도르도 받을 것 같아!", "happy"),
    "son": ("나는... 요즘 골이 잘 안 들어가.", "sad"),
    "villain": ("윙윙, 쏘아 주마!", "angry"),
    "fan": ("선수는 잔뜩 샀는데, 바뀐 게 하나도 없잖아!", "angry"),
}
CHILD = re.compile(r"child|kid|boy|girl|cute|cartoon|아이|어린|꼬마|귀여", re.I)
DEEP = re.compile(r"deep|villain|dark|evil|gruff|악당|굵은|중후", re.I)
BRIGHT = re.compile(r"bright|cheer|friendly|energetic|밝|상냥|발랄", re.I)


def want(role, v):
    """배역에 맞을수록 높은 점수."""
    g, age = v.get("gender", ""), v.get("age", "")
    txt = " ".join(str(v.get(k, "")) for k in ("name", "description", "descriptive", "use_case"))
    anim = 2 if "animation" in str(v.get("use_case", "")) or "character" in str(v.get("use_case", "")) else 0
    s = {
        "nar": (g == "female") * 3 + (age == "young") * 2 + bool(BRIGHT.search(txt)) * 2 + anim,
        "dz": (g == "male") * 3 + (age == "middle_aged") * 3 + anim,
        "koko": bool(CHILD.search(txt)) * 4 + anim * 2 + (age == "young"),
        "kids": bool(CHILD.search(txt)) * 5 + anim + (age == "young"),
        "kane": (g == "male") * 3 + (age == "young") * 2 + bool(BRIGHT.search(txt)),
        "son": (g == "male") * 3 + (age == "young") * 3,
        "villain": (g == "male") * 3 + bool(DEEP.search(txt)) * 3 + anim,
        "fan": (g == "male") * 3 + (age in ("young", "middle_aged")) + anim,
    }[role]
    return s + min(v.get("cloned_by_count", 0) or 0, 5000) / 5000  # 많이 쓰인 목소리를 조금 우대


def norm(t):
    return re.sub(r"[^가-힣0-9]", "", t)


def main():
    assert eleven_available(), "일레븐랩스 키가 없습니다(ELEVENLABS_API_KEY 또는 API credentials)"
    out = os.path.join(HERE, "_audition")
    os.makedirs(out, exist_ok=True)
    shared = json.loads(el_request("/v1/shared-voices?" + urllib.parse.urlencode(
        {"language": "ko", "page_size": 100})))["voices"]
    premade = [v for v in json.loads(el_request("/v1/voices"))["voices"]]
    print(f"한국어 공유 목소리 {len(shared)}개, 내 목소리 {len(premade)}개")
    try:
        from faster_whisper import WhisperModel
        asr = WhisperModel("small", device="cpu", compute_type="int8")
    except Exception:
        asr = None
    cast, report, used = {}, [], set()
    for role, (text, emo) in SAMPLE.items():
        cands = sorted(shared, key=lambda v: -want(role, v))[:4]
        results = []
        for v in cands:
            vid = v["voice_id"]
            try:  # 공유 목소리를 내 목소리에 추가해야 API로 쓸 수 있다
                el_request(f"/v1/voices/add/{v['public_owner_id']}/{vid}", {"new_name": f"{role}-{v['name']}"[:40]})
            except Exception as e:
                code = getattr(e, "code", "")
                if code not in (400, 409):  # 이미 추가된 경우는 괜찮다
                    print(f"  {role}: {v['name']} 추가 실패({code}) → 건너뜀")
                    continue
            results.append((v["name"], vid))
        if not results:  # 공유 목소리를 못 쓰면 기본 목소리
            labels = lambda v: v.get("labels", {}) or {}
            fb = sorted(premade, key=lambda v: -want(role, {**v, **labels(v)}))[:3]
            results = [(v["name"], v["voice_id"]) for v in fb]
        scored = []
        for name, vid in results:
            a = eleven_one(text, vid, emo)
            if a is None:
                continue
            heard = ""
            if asr:
                import wave

                import numpy as np
                wav = os.path.join(out, f"el_{role}_{norm(name) or vid[:6]}.wav")
                with wave.open(wav, "wb") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(44100)
                    w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
                heard = "".join(s.text for s in asr.transcribe(wav, language="ko")[0]).strip()
            score = difflib.SequenceMatcher(None, norm(text), norm(heard)).ratio() if asr else 0.5
            scored.append((score, name, vid, heard))
            line = f"{role:8s} {name[:24]:24s} 일치도 {score:.2f} | {heard}"
            print(line)
            report.append(line)
        scored.sort(key=lambda x: -x[0])
        n = 3 if role == "kids" else 1
        pick = [x for x in scored if x[2] not in used][:n] or scored[:n]
        cast[role] = [x[2] for x in pick]
        used.update(cast[role])
        report.append(f"  → {role}: {', '.join(x[1] for x in pick)}")
    json.dump(cast, open(EL_CAST_FILE, "w"), ensure_ascii=False, indent=1)
    open(os.path.join(HERE, "eleven_audition.txt"), "w").write("\n".join(report) + "\n")
    print("저장:", EL_CAST_FILE)


if __name__ == "__main__":
    main()
