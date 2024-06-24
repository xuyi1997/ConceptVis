import cv2
import os
import subprocess
import whisper
import torch

class AudioProcessor:
    def __init__(self, source_video_path, pts_list = []):
        self.source_video_path = source_video_path
        self.pts_list = pts_list
        self.result_dict = {}
        self.time_segments = []


    def split_audio_by_time_segments(self, source_audio_path):
        output_files = []
        if len(self.pts_list) == 0:
            return [source_audio_path]
        
        self.pts_list.insert(0, 0.0) 
        
        for i in range(len(self.pts_list)):
            if i < len(self.pts_list) - 1:
                self.time_segments.append((self.pts_list[i], self.pts_list[i + 1]))

        audio_base_name = os.path.splitext(os.path.basename(source_audio_path))[0]
    
        for i, (start_time, end_time) in enumerate(self.time_segments):
            file_name = audio_base_name + '_' + "{:.2f}".format(start_time) + '_' +  "{:.2f}".format(end_time)
            file_path = os.path.join('save', file_name + '.wav')
            if os.path.exists(file_path):
                print(f'Audio file {file_path} already exists')
                output_files.append(file_path)
                continue

            if i < len(self.time_segments) - 1:
                command = ['ffmpeg', '-i', source_audio_path, '-ss', str(start_time), '-to', str(end_time), '-q:a', '0', '-map', 'a', file_path]
            else:
                command = ['ffmpeg', '-i', source_audio_path, '-ss', str(start_time), '-q:a', '0', '-map', 'a', file_path]
            try:
                subprocess.run(command, check=True)
                output_files.append(file_path)
            except subprocess.CalledProcessError as e:
                return f'Error splitting audio: {e}'
        
        return output_files


    def process(self):
        video_name = os.path.splitext(os.path.basename(self.source_video_path))[0]
        audio_path = os.path.join('save', 'extracted_audio_' + video_name + '.wav')

        if os.path.exists(audio_path):
            print(f'Audio file {audio_path} already exists')
        else :
            # Extract audio from video using ffmpeg
            try:
                command = ['ffmpeg', '-i', self.source_video_path, '-q:a', '0', '-map', 'a', audio_path]
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError as e:
                return f'Error extracting audio: {e}'
            
        auido_files = []
            
        if len(self.pts_list) > 0 :
            auido_files = self.split_audio_by_time_segments(audio_path)
        else:
            auido_files.append(audio_path)

        result_dict = {}
        for index, audio_file in enumerate(auido_files):
            if torch.cuda.is_available():
                print(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
                gpu_model = whisper.load_model("base", device="cuda")
                result = gpu_model.transcribe(audio_file)
                window = "{:.2f}".format(self.time_segments[index][0]) + '-' + "{:.2f}".format(self.time_segments[index][1])
                self.result_dict[str(index)] = {'speech_text' : result["text"] , "time_window": window}
            else:
                print("CUDA is not available. Using CPU.")
                whisper_model = whisper.load_model("base")
                result = whisper_model.transcribe(audio_file)     
                window = "{:.2f}".format(self.time_segments[index][0]) + '-' + "{:.2f}".format(self.time_segments[index][1])
                self.result_dict[str(index)] = {'speech_text' : result["text"] , "time_window": window}

if __name__ == "__main__":
    video_path = 'uploads\index.mp4'
    processor = AudioProcessor(video_path)
    processor.process()
    print(processor.result_dict)