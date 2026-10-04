import os
import asyncio
import requests
import edge_tts
import urllib.parse
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips

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

# জেনারেট হওয়া ফাইনাল ভিডিও ফাইল ব্রাউজারে ডাইরেক্ট প্লে করার জন্য এন্ডপয়েন্ট
@app.route('/static/<filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Server is running perfectly!"})

@app.route('/generate-video', methods=['GET', 'POST'])
def generate_video_api():
    try:
        data = request.json or {}
        scene_prompt = data.get('scene', 'A calm natural park view')
        male_dialogue = data.get('male_text', '')
        female_dialogue = data.get('female_text', '')
        ratio = data.get('ratio', '16:9')

        audio_clips = []
        total_duration = 0

        # ১. অডিও ফাইল তৈরি (ছেলে ও মেয়ে)
        if male_dialogue:
            run_async(generate_voice(male_dialogue, 'male', 'male_voice.mp3'))
            m_clip = AudioFileClip('male_voice.mp3')
            audio_clips.append(m_clip)
            total_duration += m_clip.duration

        if female_dialogue:
            run_async(generate_voice(female_dialogue, 'female', 'female_voice.mp3'))
            f_clip = AudioFileClip('female_voice.mp3')
            # যদি ছেলের ভয়েসও থাকে তবে একটার পর একটা সাজানো
            if audio_clips:
                f_clip = f_clip.set_start(total_duration)
            audio_clips.append(f_clip)
            total_duration += f_clip.duration

        # যদি কোনো ভয়েস না দেওয়া হয়, তবে ডিফল্ট ৫ সেকেন্ডের ভিডিও
        if total_duration == 0:
            total_duration = 5.0

        # ২. Pollinations AI দিয়ে টেক্সট প্রম্পট অনুযায়ী ছবি ডাউনলোড করা
        encoded_prompt = urllib.parse.quote(scene_prompt)
        width, height = (720, 1280) if ratio == '9:16' else (1280, 720)
        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed=123&nologo=true"

        img_response = requests.get(img_url)
        img_path = "scene_bg.jpg"
        with open(img_path, "wb") as f:
            f.write(img_response.content)

        # ৩. MoviePy দিয়ে ছবি ও ভয়েস যুক্ত করে ভিডিও বানানো
        video_clip = ImageClip(img_path).set_duration(total_duration)

        if audio_clips:
            final_audio = CompositeAudioClip(audio_clips)
            video_clip = video_clip.set_audio(final_audio)

        # ৪. ফাইনাল ভিডিও MP4 ফাইল রেন্ডার ও সেভ করা
        output_filename = "final_output.mp4"
        video_clip.write_videofile(
            output_filename,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            logger=None
        )

        # ভিডিওর ফুল পাবলিক লিংক তৈরি
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
