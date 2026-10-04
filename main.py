import os
import asyncio
import requests
import edge_tts
import urllib.parse
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ভয়েস জেনারেশন ফাংশন (Edge-TTS)
async def generate_voice(text, gender, output_file):
    voice = "bn-BD-PradeepNeural" if gender == 'male' else "bn-BD-NabanitaNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# ভিডিও ব্রাউজারে ডাইরেক্ট অ্যাক্সেস করার রুট
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Server is running perfectly!"})

@app.route('/generate-video', methods=['GET', 'POST'])
def generate_video_api():
    m_clip = None
    f_clip = None
    video_clip = None
    final_audio = None
    
    try:
        data = request.json or {}
        scene_prompt = data.get('scene', 'A beautiful scenery')
        male_dialogue = data.get('male_text', '')
        female_dialogue = data.get('female_text', '')
        ratio = data.get('ratio', '16:9')

        audio_clips = []
        total_duration = 0.0

        # ১. অডিও ফাইল তৈরি
        if male_dialogue:
            run_async(generate_voice(male_dialogue, 'male', 'male_voice.mp3'))
            m_clip = AudioFileClip('male_voice.mp3')
            audio_clips.append(m_clip)
            total_duration += m_clip.duration

        if female_dialogue:
            run_async(generate_voice(female_dialogue, 'female', 'female_voice.mp3'))
            f_clip = AudioFileClip('female_voice.mp3')
            if audio_clips:
                f_clip = f_clip.set_start(total_duration)
            audio_clips.append(f_clip)
            total_duration += f_clip.duration

        if total_duration == 0:
            total_duration = 5.0

        # ২. AI ছবি ডাউনলোড
        encoded_prompt = urllib.parse.quote(scene_prompt)
        width, height = (720, 1280) if ratio == '9:16' else (1280, 720)
        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed=123&nologo=true"

        img_response = requests.get(img_url, timeout=15)
        img_path = "scene_bg.jpg"
        with open(img_path, "wb") as f:
            f.write(img_response.content)

        # ৩. MoviePy দিয়ে দ্রুত প্রসেসিং করা
        video_clip = ImageClip(img_path).set_duration(total_duration)

        if audio_clips:
            final_audio = CompositeAudioClip(audio_clips)
            video_clip = video_clip.set_audio(final_audio)

        output_filename = "final_output.mp4"
        
        # দ্রুত ও হালকা রেন্ডারিংয়ের জন্য অপটিমাইজড সেটিংস
        video_clip.write_videofile(
            output_filename,
            fps=15,
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast',
            threads=2,
            logger=None
        )

        host_url = request.host_url.rstrip('/')
        video_public_url = f"{host_url}/static/{output_filename}"

        return jsonify({
            "status": "success",
            "video_url": video_public_url,
            "ratio": ratio,
            "message": "Full Video generated and merged successfully!"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        # মেমোরি ক্লিনআপ (যাতে সার্ভার হ্যাং না হয়)
        try:
            if m_clip: m_clip.close()
            if f_clip: f_clip.close()
            if final_audio: final_audio.close()
            if video_clip: video_clip.close()
        except Exception:
            pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
