from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

PROJECT_ROOT = os.path.abspath('.')
EXCLUDED_DIR = 'templates'
SUPPORTED_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv')

def find_videos(root_dir, excluded_dir):
    video_files = []
    for root, dirs, files in os.walk(root_dir):
        if excluded_dir in root:
            continue
        
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                relative_path = os.path.relpath(os.path.join(root, file), root_dir)
                video_files.append(relative_path)
    return video_files

@app.route('/')
def index():
    videos = find_videos(PROJECT_ROOT, EXCLUDED_DIR)
    print(f"Found videos: {videos}") 
    return render_template('index.html', videos=videos)

@app.route('/play/<path:filename>')
def play_video(filename):
    return render_template('video_player.html', video_path=filename)

@app.route('/video/<path:filename>')
def serve_video(filename):
    return send_from_directory(PROJECT_ROOT, filename)

if __name__ == '__main__':
    app.run(debug=True)