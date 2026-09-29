import requests
import base64

GATEWAY_URL = "http://localhost:3000"

def test_tts_stt_roundtrip():
    # 1. Synthesize Hindi speech
    tts_payload = {
        "text": "राजेश कुमार पाटिल",
        "language_code": "hi"
    }
    print("1. Synthesizing Hindi speech via TTS...")
    r = requests.post(f"{GATEWAY_URL}/api/dpr/audio/synthesize", json=tts_payload)
    print("TTS Status:", r.status_code)
    data = r.json()
    b64_audio = data.get("audio_base64")
    if not b64_audio and data.get("audios"):
        b64_audio = data["audios"][0]
    
    assert b64_audio, "No audio received from TTS"
    audio_bytes = base64.b64decode(b64_audio)
    print(f"Synthesized audio size: {len(audio_bytes)} bytes")

    # 2. Transcribe Hindi speech via STT endpoint
    print("2. Transcribing audio via Gateway STT /api/dpr/audio/transcribe?language_code=hi...")
    files = {
        'file': ('recording.wav', audio_bytes, 'audio/wav')
    }
    stt_res = requests.post(f"{GATEWAY_URL}/api/dpr/audio/transcribe?language_code=hi", files=files)
    print("STT Status:", stt_res.status_code)
    stt_data = stt_res.json()
    print("STT Result:", stt_data)
    assert stt_res.status_code == 200
    assert stt_data.get("success") == True
    print("[SUCCESS] STT transcription working end-to-end!")

if __name__ == "__main__":
    test_tts_stt_roundtrip()
