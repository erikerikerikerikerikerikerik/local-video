from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)
VIDEO_DIR = 'static/videos'
SUPPORTED_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv')

def find_videos(root_dir):
    video_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                relative_path = os.path.relpath(os.path.join(root, file), root_dir)
                video_files.append(relative_path)
    return video_files

@app.route('/')
def index():
    videos = find_videos(VIDEO_DIR)
    return render_template('index.html', videos=videos)

@app.route('/play/<path:filename>')
def play_video(filename):
    return render_template('video_player.html', video_path=filename)

@app.route('/static/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True)