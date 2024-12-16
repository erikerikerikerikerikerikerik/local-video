import os
import ffmpeg
from flask import Flask, render_template, send_from_directory

app = Flask(__name__, static_folder='templates')

PROJECT_ROOT = os.path.abspath('.')
EXCLUDED_DIRS = ['templates', 'thumbnails']  
THUMBNAILS_DIR = os.path.join(PROJECT_ROOT, 'thumbnails')
SUPPORTED_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv')

if not os.path.exists(THUMBNAILS_DIR):
    os.makedirs(THUMBNAILS_DIR)

def generate_video_thumbnail(video_path):
    video_filename = os.path.basename(video_path)
    thumbnail_filename = os.path.splitext(video_filename)[0] + '.jpg'
    thumbnail_path = os.path.join(THUMBNAILS_DIR, thumbnail_filename)

    if os.path.exists(thumbnail_path):
        return thumbnail_filename

    try:
        ffmpeg.input(video_path, ss=1).output(thumbnail_path, vframes=1, vf="scale='if(gte(iw,ih),300,-1)':'if(gte(iw,ih),-1,300)'").run()
    except Exception as e:
        print(f"Error generating thumbnail for {video_filename}: {e}")
        return None
    
    return thumbnail_filename

def find_videos(root_dir, excluded_dirs):
    video_files = []
    for root, dirs, files in os.walk(root_dir):
        if any(excluded_dir in root for excluded_dir in excluded_dirs):
            continue
        
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                relative_path = os.path.relpath(os.path.join(root, file), root_dir)
                video_files.append(relative_path)
    return video_files

@app.route('/')
def index():
    videos = find_videos(PROJECT_ROOT, EXCLUDED_DIRS)
    video_thumbnails = {}

    for video in videos:
        video_path = os.path.join(PROJECT_ROOT, video)
        video_thumbnails[video] = generate_video_thumbnail(video_path)

    return render_template('index.html', videos=videos, thumbnails=video_thumbnails)

@app.route('/play/<path:filename>')
def play_video(filename):
    return render_template('video_player.html', video_path=filename)

@app.route('/video/<path:filename>')
def serve_video(filename):
    return send_from_directory(PROJECT_ROOT, filename)

@app.route('/thumbnail/<path:filename>')
def serve_thumbnail(filename):
    return send_from_directory(THUMBNAILS_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True)