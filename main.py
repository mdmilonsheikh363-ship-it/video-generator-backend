import os
import asyncio
import edge_tts
import replicate
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# আপনার Replicate API Key সেট করা হলো
os.environ["REPLICATE_API_TOKEN"] = "R8_YwlYqZZH7KTKphOmJf67zGvixGvWK004TNp9v"

# বাংলা ভয়েস জেনারেটর (Edge-TTS)
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

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "AI Video Generation Server is Live!"})

@app.route('/generate-video', methods=['GET', 'POST'])
def generate_video_api():
    try:
        data = request.json or {}
        scene_prompt = data.get('scene', 'A beautiful nature scene, hyper-realistic, cinematic motion')
        male_dialogue = data.get('male_text', '')
        female_dialogue = data.get('female_text', '')
        ratio = data.get('ratio', '16:9')

        # ১. অডিও ভয়েস জেনারেশন
        if male_dialogue:
            run_async(generate_voice(male_dialogue, 'male', 'male_voice.mp3'))
        if female_dialogue:
            run_async(generate_voice(female_dialogue, 'female', 'female_voice.mp3'))

        # ২. Replicate API দিয়ে আসল AI Video তৈরি
        # রেশিও কনফিগারেশন (16:9 বা 9:16)
        aspect_ratio = "16:9" if ratio == '16:9' else "9:16"

        # Replicate AI Video Model চালানো
        output = replicate.run(
            "stability-ai/stable-video-diffusion:3f045767b77d4084282e3827c191a3c631b15801c8a514d34f0e0108871032bf",
            input={
                "cond_aug": 0.02,
                "decoding_t": 14,
                "input_image": f"https://image.pollinations.ai/prompt/{scene_prompt}?width=1280&height=720&nologo=true",
                "video_length": "25_frames_with_svd_xt",
                "sizing_strategy": "maintain_aspect_ratio",
                "motion_bucket_id": 127,
                "frames_per_second": 6
            }
        )

        # ভিডিও ইউআরএল বের করা
        ai_video_url = str(output) if isinstance(output, str) else output[0] if isinstance(output, list) else str(output)

        return jsonify({
            "status": "success",
            "video_url": ai_video_url,
            "ratio": ratio,
            "message": "Real AI Video Generated Successfully!"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
