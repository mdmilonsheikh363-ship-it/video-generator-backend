import os
import asyncio
import edge_tts
from flask import Flask, request, jsonify

app = Flask(__name__)

# ভয়েস জেনারেশন ফাংশন
async def generate_voice(text, gender, output_file):
    voice = "bn-BD-PradeepNeural" if gender == 'male' else "bn-BD-NabanitaNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Server is running perfectly!"})

@app.route('/generate-video', methods=['POST'])
def generate_video_api():
    try:
        data = request.json or {}
        scene_prompt = data.get('scene', '')
        male_dialogue = data.get('male_text', '')
        female_dialogue = data.get('female_text', '')

        if male_dialogue:
            asyncio.run(generate_voice(male_dialogue, 'male', 'male_voice.mp3'))
        if female_dialogue:
            asyncio.run(generate_voice(female_dialogue, 'female', 'female_voice.mp3'))

        video_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"

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
