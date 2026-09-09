import time
import threading
import pyaudio
import tkinter as tk
import os
import wave
import sounddevice
import os

from audio2action import RobotAgentSystem

class UI():
    def __init__(self):
        self.root = tk.Tk()
        self.root.resizable(False, False)
        self.root.title("录音")
        self.root.geometry("200x150+630+300")
        self.button = tk.Button(text="录音", font=("Helvetica", 14), width=15, height=5, command=self.click_handler)
        self.button.pack()
        self.label = tk.Label(text="00:00:00",font=("Helvetica", 14),width=10,height=3)
        self.label.pack()
        self.recording = False
        self.recognizing = False

        self.robot = RobotAgentSystem()
        self.root.mainloop()

    def click_handler(self):
        if self.recording:
            self.recording = False
            self.button.config(fg="black")
        else:
            self.recording = True
            self.button.config(fg="red")
            threading.Thread(target=self.record).start()

    def record(self):
        audio = pyaudio.PyAudio()
        # stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=512, input_device_index=11)
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=512)
        frames = []
        start = time.time()
        while self.recording:
            data = stream.read(512)
            frames.append(data)
            passed = time.time() - start
            seconds = passed % 60
            mins = passed // 60
            hours = mins // 60
            self.label.config(text=f"{int(hours):02d}:{int(mins):02d}:{int(seconds):02d}")
            self.root.update()

        stream.stop_stream()
        stream.close()
        audio.terminate()

        sound_file = wave.open(f"/home/win/Project/P05/audio/recording.wav", "wb")
        sound_file.setnchannels(1)
        sound_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        sound_file.setframerate(44100)
        sound_file.writeframes(b''.join(frames))
        sound_file.close()
        start_time = time.time()
        audio_path = '/home/win/Project/P05/audio/recording.wav'
        output_name = '/home/win/Project/P05/audio/recording1.wav'
        command = f'ffmpeg -i "{audio_path}" -ar 16000 -y "{output_name}"'
        os.system(command)
        self.robot.chat(output_name)
        end_time = time.time()
        print(f"总时长：{end_time - start_time:.2f}秒")

UI()