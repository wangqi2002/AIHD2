import json
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, render_template, request, redirect, url_for
import os
import wave
import pyaudio

from Scripts.audio2action import audio2action

executor = ThreadPoolExecutor(2)
a2a = audio2action()

robot_bp = Blueprint('robot', __name__)

@robot_bp.route('/')
def index():
    comment = request.values.get("question")
    print(comment)
    return "这里是机器人提供的答复"

@robot_bp.route('/text' ,methods=['GET'])
def text():
    # comment = request.form.get('file')
    comment = request.values.get('audio')
    print(comment)
    usr_input_text = a2a.audio_to_text(comment)
    print(usr_input_text)
    return "这里是语音转文字提供的答复"

# @robot_bp.route('/text1' ,methods=['POST'])
# def text1():
#     # 检查是否有文件字段
#     if 'audio' not in request.files:
#         return "未接收到语音"
#     print(request.files)
#     file = request.files['audio']
#     print(file)
#     usr_input_text = a2a.audio_to_text(file)
#     return usr_input_text

@robot_bp.route('/text1' ,methods=['POST'])
def text1():
    # 检查是否有文件字段
    if 'audio' not in request.files:
        return "未接收到语音"
    # print(request.files)
    file = request.files['audio']

    with wave.open(f"/home/win/Project/P03/Audio/recording.wav", "wb") as sound_file:
        sound_file.setnchannels(1)
        sound_file.setsampwidth(2)
        sound_file.setframerate(44100)
        sound_file.writeframes(b''.join(file))
    # sound_file = wave.open(f"/home/win/Project/P03/Audio/recording.wav", "wb")
    # sound_file.setnchannels(1)
    # sound_file.setsampwidth(16)
    # sound_file.setframerate(44100)
    # sound_file.writeframes(b''.join(file))
    # sound_file.close()
    audio_path = '/home/win/Project/P03/Audio/recording.wav'
    output_name = '/home/win/Project/P03/Audio/recording1.wav'
    command = f'ffmpeg -i "{audio_path}" -ar 16000 -y "{output_name}"'
    os.system(command)

    usr_input_text = a2a.audio_to_text(audio_path)
    print(usr_input_text)
    return usr_input_text

@robot_bp.route('/reply')
def reply():
    comment = request.values.get("question")
    print(comment)
    answer = a2a.action(comment)
    print(answer)
    if "好的，马上为您提供" in answer["response"]:
        value = answer['response'] +" "+answer['type']
        # executor.submit(ur_robot_fun, answer_json)
        return value
    # elif "请稍等，我正在为您准备" in answer:
    #     return "这里是机器人提供的答复"
    else :
        value = answer['response']
        return value

