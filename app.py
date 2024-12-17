"""
local-video app
**Designed and coded by erikerikerikerikerikerikerik - Erik Bruil**
"""

import os
import ffmpeg
from flask import Flask, render_template, send_from_directory
from flask import Response, request

app = Flask(__name__, static_folder='templates')

PROJECT_ROOT = os.path.abspath('.')
EXCLUDED_DIRS = ['templates', 'thumbnails']
THUMBNAILS_DIR = os.path.join(PROJECT_ROOT, 'thumbnails')
SUPPORTED_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv')

if not os.path.exists(THUMBNAILS_DIR):
    os.makedirs(THUMBNAILS_DIR)

def generate_video_thumbnail(video_path):
    """generate video thumbnail"""
    video_filename = os.path.basename(video_path)
    thumbnail_filename = os.path.splitext(video_filename)[0] + '.jpg'
    thumbnail_path = os.path.join(THUMBNAILS_DIR, thumbnail_filename)

    if os.path.exists(thumbnail_path):
        return thumbnail_filename

    try:
        ffmpeg.input(video_path, ss=1)\
            .output(thumbnail_path, vframes=1,\
                    vf="scale='if(gte(iw,ih),300,-1)':'if(gte(iw,ih),-1,300)'")\
            .run()
    except ValueError:
        print(f"Error generating thumbnail for {video_filename}")
        return None

    return thumbnail_filename

def find_videos(root_dir, excluded_dirs):
    """find videos"""
    video_files = []
    for root, _, files in os.walk(root_dir):
        if any(excluded_dir in root for excluded_dir in excluded_dirs):
            continue

        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                relative_path = os.path.relpath(os.path.join(root, file), root_dir)
                video_files.append(relative_path)
    return video_files

def get_video_stream(video_path):
    """stream video"""
    def generate():
        with open(video_path, 'rb') as f:
            while chunk := f.read(4096):
                yield chunk
    return generate

@app.route('/')
def index():
    """index /"""
    videos = find_videos(PROJECT_ROOT, EXCLUDED_DIRS)
    video_thumbnails = {}

    for video in videos:
        video_path = os.path.join(PROJECT_ROOT, video)
        video_thumbnails[video] = generate_video_thumbnail(video_path)

    return render_template('index.html', videos=videos, thumbnails=video_thumbnails)

@app.route('/play/<path:filename>')
def play_video(filename):
    """play video"""
    return render_template('video_player.html', video_path=filename)

@app.route('/video/<path:filename>')
def serve_video(filename):
    """serve video"""
    video_path = os.path.join(PROJECT_ROOT, filename)
    range_header = request.headers.get('Range', None)
    if not os.path.exists(video_path):
        return "File not found", 404

    if range_header:
        start, end = range_header.replace('bytes=', '').split('-')
        start = int(start)
        end = int(end) if end else os.path.getsize(video_path) - 1
        chunk_size = end - start + 1

        with open(video_path, 'rb') as f:
            f.seek(start)
            data = f.read(chunk_size)

        response = Response(data, status=206, mimetype='video/mp4')
        response.headers['Content-Range'] = f'bytes {start}-{end}/{os.path.getsize(video_path)}'
    else:
        response = Response(get_video_stream(video_path), mimetype='video/mp4')

    response.headers['Accept-Ranges'] = 'bytes'
    return response
    #return send_from_directory(PROJECT_ROOT, filename)

@app.route('/thumbnail/<path:filename>')
def serve_thumbnail(filename):
    """serve thumbnail"""
    return send_from_directory(THUMBNAILS_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True)
