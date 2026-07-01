from utils.tts import _pick_espeak_profile

seg = {"text": "我们先聊聊世界历史，这是中文测试。", "voice": "zh-CN-XiaoxiaoNeural", "speaker": "A"}
print(_pick_espeak_profile(seg))
