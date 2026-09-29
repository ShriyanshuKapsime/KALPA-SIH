import urllib.request
import io
import wave
import json

# Generate a small 1-second 16kHz mono WAV file
wav_io = io.BytesIO()
with wave.open(wav_io, 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    w.writeframes(b'\x00' * 32000)
wav_bytes = wav_io.getvalue()

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
part_header = (
    f'--{boundary}\r\n'
    'Content-Disposition: form-data; name="file"; filename="sample.wav"\r\n'
    'Content-Type: audio/wav\r\n\r\n'
).encode('latin1')
part_footer = f'\r\n--{boundary}--\r\n'.encode('latin1')

body = part_header + wav_bytes + part_footer

req = urllib.request.Request(
    'http://localhost:3000/api/dpr/audio/transcribe?language_code=en',
    data=body,
    headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Accept': 'application/json'
    },
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print('STT Status:', resp.status)
        print('STT Response:', data)
        print('STT Keys:', list(data.keys()))
except Exception as e:
    print('STT Test Error:', e)
