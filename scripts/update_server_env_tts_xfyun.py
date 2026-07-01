from pathlib import Path

ENV_PATH = Path('/opt/EduMind/./.env')

updates = {
    'TTS_PROVIDER': 'edge',
    'FFMPEG_PATH': 'ffmpeg',
    'TTS_VOICE_EDGE': 'zh-CN-XiaoxiaoNeural',
    'TTS_VOICE_ALT_EDGE': 'zh-CN-YunyangNeural',
    'TTS_VOICE_EDGE_EN_US': 'en-US-AvaNeural',
    'TTS_VOICE_EDGE_EN_GB': 'en-GB-LibbyNeural',
    'TRANSCRIPTION_PROVIDER': 'openai',
    'XFYUN_APPID': 'a8cddcf9',
    'XFYUN_API_SECRET': 'MjM3YzdjODgzZTg5YzYyZGNkMjg1NzZj',
    'XFYUN_API_KEY': 'c6dd10823cdaf58c3d5d7683a5f1e3ab',
}

text = ENV_PATH.read_text(encoding='utf-8')
lines = text.splitlines()
seen = set()

for i, line in enumerate(lines):
    if not line or line.lstrip().startswith('#') or '=' not in line:
        continue
    key = line.split('=', 1)[0].strip()
    if key in updates:
        lines[i] = f"{key}={updates[key]}"
        seen.add(key)

for key, value in updates.items():
    if key not in seen and not any(l.startswith(f"{key}=") for l in lines):
        lines.append(f"{key}={value}")

ENV_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')

check_keys = [
    'TTS_PROVIDER',
    'FFMPEG_PATH',
    'TTS_VOICE_EDGE',
    'TTS_VOICE_ALT_EDGE',
    'TTS_VOICE_EDGE_EN_US',
    'TTS_VOICE_EDGE_EN_GB',
    'TRANSCRIPTION_PROVIDER',
    'XFYUN_APPID',
    'XFYUN_API_SECRET',
    'XFYUN_API_KEY',
]

print('updated keys:')
for key in check_keys:
    for line in lines:
        if line.startswith(f"{key}="):
            print(line)
            break
