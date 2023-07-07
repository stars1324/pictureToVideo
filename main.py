import math
import os
import re
import shutil
import subprocess

from gtts import gTTS
from moviepy.editor import *
from pydub import AudioSegment
from PIL import Image


def text_to_voice():
    try:
        shutil.rmtree('./tts')
        os.mkdir('./tts')
    except:
        pass

    voice = []
    content = open('content.txt').read()

    contents = re.split(r'[。！？？,，]', content)

    for content in contents:
        content = content.strip()
        if not len(content):
            continue

        filename = './tts/%s.mp3' % content
        # 转语音
        g_tts = gTTS(content, lang='zh-CN')
        g_tts.save(filename)

        # 调整语速 为 1.2 倍速
        sound = AudioSegment.from_mp3(filename)
        duration = int(sound.duration_seconds)
        update_speed_filename = './tts/%s_duration_%f.mp3' % (content, math.ceil(duration * 0.85))
        cmd = "ffmpeg -y -i %s -filter_complex \"atempo=tempo=%s\" %s" % (filename, '1.2', update_speed_filename)
        res = subprocess.call(cmd, shell=True)
        if res == 0:
            os.remove(filename)
        voice.append(update_speed_filename)

        print(update_speed_filename)
    return voice


def get_all_files(path):
    files = []
    for root, dirs, filenames in os.walk(path):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files


def handle_movie(voice = []):
    # voice = get_all_files('./tts')
    # 计算所有语音的长度，得出需要视频的长度
    duration_clips, text_clips = [], []
    for item in voice:
        filename = str(item.split('/')[-1])
        tmp = filename.split('_')
        text_clips.append(tmp[0])
        duration_clips.append(float(tmp[-1].replace('.mp3', '')))

    duration = sum(duration_clips)

    # 背景音乐
    bg_music = AudioFileClip("./bgm/1.MP3").set_duration(duration).volumex(0.3)

    # 解说 + 字幕
    voice_clips, txt_clips = [], []

    for idx, item in enumerate(text_clips):
        start = sum(duration_clips[:idx])
        end = start + duration_clips[idx]
        voice_clips.append(
            AudioFileClip(voice[idx]).set_start(start).volumex(0.8))

        txt_clip = TextClip(text_clips[idx], fontsize=40, color='white',  font='兰亭黑-简-中黑', stroke_color='black', stroke_width=0.8)
        txt_clip = txt_clip.set_pos('bottom').set_duration(duration_clips[idx]).crossfadein(1).crossfadeout(1)
        txt_clip = txt_clip.set_start(start).set_end(end)
        txt_clips.append(txt_clip)


    picture_path = './pictures'
    # 定义每张图片的剪辑，并添加淡入淡出效果
    images = get_all_files(picture_path)

    # 将图片格式化
    for image in images:
        # 将图片变成 16:9  高度787.5 ，宽度1400
        resize_images(image)


    image_num = len(images)
    image_duration = duration / image_num
    image_clips = []

    # 镜头焦点效果
    def resize_func(t):
        return 1 + 0.005 * t

    # screensize = (640, 360)
    for image_path in get_all_files('./pictures'):
        image_clip = ImageClip(image_path).set_duration(image_duration).resize(resize_func).set_position(('center', 'center')).set_fps(25)
        image_clip = image_clip.crossfadein(1).crossfadeout(1)
        image_clips.append(image_clip)

        # image_clips.append(ImageClip('path_to_image.jpg').resize(resize_func).set_position(('center', 'center')).set_duration(image_duration).set_fps(25))

    # 将所有图片剪辑合并为一个剪辑
    image_clip = concatenate_videoclips(image_clips)

    # 将图像、字幕和音频剪辑合并为一个剪辑，并添加淡入淡出效果
    # video_clip = CompositeVideoClip([image_clip])
    video_clip = CompositeVideoClip([image_clip] + txt_clips)
    audio_clip = CompositeAudioClip([bg_music] + voice_clips)
    video_clip = video_clip.set_audio(audio_clip)
    video_clip = video_clip.crossfadein(1).crossfadeout(1)

    # 导出视频剪辑
    video_clip.write_videofile("output.mp4", fps=24)

def resize_images(image_path):
    # 打开图片
    image = Image.open(image_path)
    width = 1400  # 固定宽度
    height = 787  # 固定高度

    # 计算缩放比例
    original_width, original_height = image.size
    scale = min(width / original_width, height / original_height)

    # 计算缩放后的大小
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)

    # 缩放图片
    image = image.resize((new_width, new_height))

    # 创建新的画布
    canvas = Image.new('RGB', (width, height), (0, 0, 0))

    # 计算居中位置
    x = (width - new_width) // 2
    y = (height - new_height) // 2

    # 将缩放后的图片粘贴到画布上
    canvas.paste(image, (x, y))

    # 保存图片
    canvas.save(image_path)

voice = text_to_voice()
handle_movie(voice)
