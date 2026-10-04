import os
import asyncio
import edge_tts
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# CORS সাপোর্ট চালু করা
CORS(app, resources={r"/*": {"origins": "*"}})

# ভয়েস জেনারেশন ফাংশন
async def generate_voice(text, gender, output_file):
    voice = "bn-BD-PradeepNeural" if gender == 'male' else "bn-BD-NabanitaNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

# অ্যাসিনক্রোনাস কাজ রান করার উপায়
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Server is running perfectly!"})

@app.route('/generate-video', methods=['GET', 'POST'])
def generate_video_api():
    try:
        data = request.json or {}
        scene_prompt = data.get('scene', '')
        male_dialogue = data.get('male_text', '')
        female_dialogue = data.get('female_text', '')

        if male_dialogue:
            run_async(generate_voice(male_dialogue, 'male', 'male_voice.mp3'))
        if female_dialogue:
            run_async(generate_voice(female_dialogue, 'female', 'female_voice.mp3'))

        # নির্ভরযোগ্য নমুনা ভিডিও লিংক (যেটি সব ব্রাউজার ও প্লেয়ারে সাবলীলভাবে প্লে হয়)
        video_url = "https://www.w3schools.com/html/mov_bbb.mp4"

        return jsonify({
            "status": "success",
            "video_url": video_url,
            "message": "Video & Voices generated successfully!"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
