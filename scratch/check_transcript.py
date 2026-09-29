import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\shriy\.gemini\antigravity-ide\brain\7bfb2ee4-357e-49c4-b71d-182b73838159\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        idx = data.get('step_index', 0)
        if 2561 <= idx <= 2615:
            print(f"=== STEP {idx} ({data.get('type')}) ===")
            if 'content' in data:
                print(str(data['content'])[:500])
            if 'tool_calls' in data:
                print('Tool calls:', json.dumps(data['tool_calls'], indent=2)[:500])

