from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

PARENT_DIR = os.path.abspath(os.path.dirname(__file__))
EXCLUDED_DIR = 'local-video'
SUPPORTED_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv')

def find_videos(parent_dir, excluded_dir):
    video_files = []
    for root, dirs, files in os.walk(parent_dir):
        if EXCLUDED_DIR in root:
            continue
        
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                relative_path = os.path.relpath(os.path.join(root, file), parent_dir)
                video_files.append(relative_path)
    return video_files

@app.route('/')
def index():
    videos = find_videos(PARENT_DIR, EXCLUDED_DIR)
    return render_template('index.html', videos=videos)

@app.route('/play/<path:filename>')
def play_video(filename):
    return render_template('video_player.html', video_path=filename)

@app.route('/video/<path:filename>')
def serve_video(filename):
    return send_from_directory(PARENT_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True)