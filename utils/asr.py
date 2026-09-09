import time
import json

from funasr import AutoModel



class ASR():
    def __init__(self):

        self.asr_model = AutoModel(
        model="/home/win/.cache/modelscope/hub/FunAudioLLM/Fun-ASR-Nano-2512",
        trust_remote_code=True,
        remote_code="/home/win/Project/P03/Fun-ASR//model.py",
        device="cuda:0",
        disable_update=True
    )   
        
        print("语音识别模型加载完毕")

    def speech_text(self, audio_path):
        # start_time = time.time()
        res = self.asr_model.generate(
        input=[audio_path],
        cache={},
        batch_size=1,
        hotwords=["拿一杯", "可乐", "芬达", "雪碧",],
        language="中文",
        itn=True, # or False
    )
        text = res[0]["text"]
        print(text)
        return text

if __name__ == "__main__":
    audio_path = "/home/win/Project/P02/Fun-ASR/test.wav"
    asr = ASR()
    asr.speech_text(audio_path)