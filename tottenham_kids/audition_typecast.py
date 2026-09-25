"""배역별 타입캐스트 후보 목소리를 들어 보고 고르는 도구.

    타입캐스트 키가 환경 변수(TYPECAST_API_KEY) 또는 클라우드 환경의 API credentials 로 등록된 상태에서:
    python3 audition_typecast.py            # _audition/ 에 배역별 후보 wav 저장 + 발음 인식 결과·음높이 출력

고른 목소리는 voice.py 의 CAST 맨 앞 이름으로 바꾸면 된다.
"""
import json
import os
import wave

import numpy as np

from voice import HERE, SR, trim_silence, typecast_available, typecast_one

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


def main():
    assert typecast_available(), "타입캐스트 키가 없습니다(TYPECAST_API_KEY 또는 API credentials)"
    out = os.path.join(HERE, "_audition")
    os.makedirs(out, exist_ok=True)
    cands = json.load(open(os.path.join(HERE, "typecast_voices.json")))
    try:
        from faster_whisper import WhisperModel
        asr = WhisperModel("small", device="cpu", compute_type="int8")
    except Exception:
        asr = None
    import parselmouth
    for role, (text, emo) in SAMPLE.items():
        for c in cands[role]:
            a = trim_silence(typecast_one(text, c["name"], emo))
            f = os.path.join(out, f"{role}_{c['name']}.wav")
            with wave.open(f, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(SR)
                w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())
            p = parselmouth.Sound(a.astype(np.float64), SR).to_pitch(0.01, 70, 700).selected_array["frequency"]
            p = p[p > 0]
            st = 12 * np.log2(p / np.median(p)) if len(p) else np.zeros(1)
            heard = "".join(s.text for s in asr.transcribe(f, language="ko")[0]).strip() if asr else ""
            print(f"{role:8s} {c['name']:10s} {len(a) / SR:4.1f}s  f0 {np.median(p) if len(p) else 0:5.0f}Hz  "
                  f"억양폭 {np.percentile(st, 95) - np.percentile(st, 5):4.1f}반음 | {heard}")


if __name__ == "__main__":
    main()
