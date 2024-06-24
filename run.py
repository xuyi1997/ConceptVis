from flask import Flask, request, render_template, jsonify, g, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import requests
import speech_recognition as sr
import pytesseract
import os
import subprocess
import whisper
import torch
from src.video_processor import VideoProcessor
from src.audio_processor import AudioProcessor
from src.concept.llm import LLMExtractor


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

@app.route('/image/<path:filename>')
def image(filename):
    print(filename)
    return send_from_directory('', filename)

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
    result = process_video()
    response = {
        'result_dict': result
    }   
    return jsonify(response)


def process_video():
    video_path = file_path.get('uploaded_file_path', None)
    video_processor = VideoProcessor(video_path)
    video_processor.process()
    slides_list = video_processor.result_dict
    pts_list = [slides_list[key]['pts'] for key in slides_list]
    audio_processor = AudioProcessor(video_path, pts_list)
    audio_processor.process()
    d_comb = {}
    for k in audio_processor.result_dict:
        d_comb[k] = audio_processor.result_dict[k].copy()
        d_comb[k].update(video_processor.result_dict[k])
    return d_comb
    

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if app.debug:
        return requests.get('http://localhost:8080/{}'.format(path)).text
    return render_template("index.html")

if __name__ == '__main__':
    app.run()