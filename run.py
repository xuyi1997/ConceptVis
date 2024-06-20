from flask import Flask, request, render_template, jsonify, g
from flask_cors import CORS
from werkzeug.utils import secure_filename
import requests
import speech_recognition as sr
import pytesseract
import os
import subprocess
import whisper
import torch


app = Flask(__name__,
            static_folder = "./dist/static",
            template_folder = "./dist")
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

file_path = {}

@app.route('/api/uploadVideo', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video part in the request'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': 'No selected video'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_path['uploaded_file_path'] = filepath
        file.save(filepath)
        print("upload file: ", filepath)
        return jsonify({'message': 'Video uploaded successfully'}), 200
    
    return jsonify({'error': 'Failed to upload video'}), 500


@app.route('/api/extractText') 
def extract_text():
    ret = process_video()
    response = {
        'extractedText': ret
    }    
    print("extractedText: ", response)
    return jsonify(response)


def process_video():
    video_path = file_path.get('uploaded_file_path', None)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    if not video_path:
        return 'No file uploaded'
    # Define paths for the intermediate and final output files
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_audio_' + video_name + '.wav')

    if os.path.exists(audio_path):
        print(f'Audio file {audio_path} already exists')
    else :
    # Extract audio from video using ffmpeg
        try:
            command = ['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path]
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            return f'Error extracting audio: {e}'
    
    
    if torch.cuda.is_available():
        print(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
        gpu_model = whisper.load_model("base", device="cuda")
        result = gpu_model.transcribe(audio_path)
        return result["text"]
    else:
        print("CUDA is not available. Using CPU.")
        whisper_model = whisper.load_model("base")
        result = whisper_model.transcribe(audio_path)
        return result["text"]
    


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if app.debug:
        return requests.get('http://localhost:8080/{}'.format(path)).text
    return render_template("index.html")

if __name__ == '__main__':
    app.run()