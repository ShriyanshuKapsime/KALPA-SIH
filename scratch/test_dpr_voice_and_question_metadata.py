import os
import requests
import io
import wave
import struct

GATEWAY_URL = "http://localhost:3000"
AI_SERVICE_URL = "http://localhost:8000"

def generate_dummy_wav():
    # 0.5 sec 16kHz mono silence
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        num_samples = 8000
        raw = struct.pack('<' + 'h' * num_samples, *([0] * num_samples))
        wav.writeframes(raw)
    buf.seek(0)
    return buf.getvalue()

def run_tests():
    print("=== TEST 1: STT TRANSCRIBE ENDPOINT TESTS ===")
    wav_data = generate_dummy_wav()
    print(f"Generated dummy audio: {len(wav_data)} bytes")

    # A. Test Gateway with field name 'file' in Hindi
    print("\n--- A. Gateway /api/dpr/audio/transcribe?language_code=hi (field='file') ---")
    files = {'file': ('recording.webm', wav_data, 'audio/webm')}
    try:
        r = requests.post(f"{GATEWAY_URL}/api/dpr/audio/transcribe?language_code=hi", files=files)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert "transcript" in r.json() or "text" in r.json()
        print("[SUCCESS] Gateway transcribe with 'file' succeeded!")
    except Exception as e:
        print(f"FAILED: {e}")

    # B. Test Gateway with field name 'audio' fallback in Kannada
    print("\n--- B. Gateway /api/dpr/audio/transcribe?language_code=kn (field='audio') ---")
    files_audio = {'audio': ('recording.webm', wav_data, 'audio/webm')}
    try:
        r = requests.post(f"{GATEWAY_URL}/api/dpr/audio/transcribe?language_code=kn", files=files_audio)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        assert r.status_code == 200
        print("[SUCCESS] Gateway transcribe with fallback 'audio' succeeded!")
    except Exception as e:
        print(f"FAILED: {e}")

    # C. Test AI Service directly missing file returns 422
    print("\n--- C. AI Service /api/v1/dpr/audio/transcribe with no file ---")
    try:
        r = requests.post(f"{AI_SERVICE_URL}/api/v1/dpr/audio/transcribe?language_code=en", data={"foo": "bar"})
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
        assert r.status_code in [422, 400], f"Expected 422 or 400, got {r.status_code}"
        print("[SUCCESS] Missing file correctly rejected with validation error 422!")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\n=== TEST 2: DYNAMIC QUESTION METADATA TESTS ===")
    languages = ['en', 'hi', 'mr', 'kn', 'ta', 'te', 'gu']
    
    for lang in languages:
        print(f"\n--- Testing Language: {lang} ---")
        try:
            # Create a scenario
            r = requests.post(
                f"{AI_SERVICE_URL}/api/v1/dpr/new-scenario/test_biz_dairy",
                json={"user_language": lang}
            )
            scen_data = r.json()
            scen_id = scen_data.get("scenario_id")
            
            # Fetch next question
            qr = requests.get(
                f"{AI_SERVICE_URL}/api/v1/dpr/question/next/test_biz_dairy?language={lang}&scenario_id={scen_id}"
            )
            q_res = qr.json()
            if q_res.get("has_question"):
                q = q_res.get("question")
                field_id = q.get('field_id')
                title = q.get('title') or q.get('question')
                desc = q.get('description') or q.get('helper_text')
                example = q.get('example')
                hint = q.get('validationHint') or q.get('why_we_are_asking')

                print(f"Field ID: {field_id}")
                print(f"Title: {title}")
                print(f"Description: {desc}")
                print(f"Example: {example}")
                print(f"Validation Hint: {hint}")
                
                # Assertions
                assert title, "Missing question title!"
                assert desc, "Missing purpose description!"
                assert "Provide details so your project can be understood" not in str(desc), "Generic description detected!"
                print(f"[SUCCESS] Dynamic question metadata verified for {lang}!")
        except Exception as e:
            print(f"Error for {lang}: {e}")

if __name__ == "__main__":
    run_tests()
