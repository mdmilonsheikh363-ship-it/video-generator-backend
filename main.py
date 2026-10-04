import os
import asyncio
import edge_tts
import urllib.parse
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Server is running perfectly!"})

@app.route('/generate-video', methods=['GET', 'POST'])
def generate_video_api():
    try:
        data = request.json or {}
        scene_prompt = data.get('scene', 'A beautiful scenery')
        male_dialogue = data.get('male_text', '')
        female_dialogue = data.get('female_text', '')
        ratio = data.get('ratio', '16:9')

        # ভয়েস জেনারেশন
        if male_dialogue:
            run_async(generate_voice(male_dialogue, 'male', 'male_voice.mp3'))
        if female_dialogue:
            run_async(generate_voice(female_dialogue, 'female', 'female_voice.mp3'))

        # ইউআরএল নিরাপদ করা
        encoded_prompt = urllib.parse.quote(scene_prompt)

        # রেশিও অনুযায়ী সাইজ নির্ধারণ
        if ratio == '9:16':
            width, height = 720, 1280
        else:
            width, height = 1280, 720

        # আপনার দেওয়া প্রম্পট অনুযায়ী বাস্তব AI দৃশ্য (ভিজ্যুয়াল সোর্স)
        generated_media_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed=42&nologo=true"

        return jsonify({
            "status": "success",
            "video_url": generated_media_url,
            "ratio": ratio,
            "message": "AI Visuals and Voice processed successfully!"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
