from config import config

print("tts_provider:", config.tts_provider)
print("tts_voice_edge:", config.tts_voice_edge)
print("tts_voice_alt_edge:", config.tts_voice_alt_edge)
print("tts_voice_edge_en_us:", config.tts_voice_edge_en_us)
print("tts_voice_edge_en_gb:", config.tts_voice_edge_en_gb)
print("transcription_provider:", config.transcription_provider)
print("xfyun_appid:", bool(config.xfyun_appid))
print("xfyun_api_secret:", bool(config.xfyun_api_secret))
print("xfyun_api_key:", bool(config.xfyun_api_key))
