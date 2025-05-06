"""
local-video app
**Designed and coded by erikerikerikerikerikerikerik - Erik Bruil**
"""

import os
import webbrowser
from threading import Timer
import json
import ffmpeg
from flask import Flask, render_template, send_from_directory
from flask import Response, request, jsonify

app = Flask(__name__, static_folder='_templates', template_folder='_templates')

PROJECT_ROOT = os.path.abspath('.')
EXCLUDED_DIRS = ['_templates', '_thumbnails']
THUMBNAILS_DIR = os.path.join(PROJECT_ROOT, '_thumbnails')
FAVORITES_FILE = os.path.join(PROJECT_ROOT, 'favorites.json')
SUPPORTED_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv')

if not os.path.exists(THUMBNAILS_DIR):
    os.makedirs(THUMBNAILS_DIR)

if not os.path.exists(FAVORITES_FILE):
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)

def generate_video_thumbnail(video_path):
    """generate multiple thumbnails per video into a subfolder"""
    relative_video_path = os.path.relpath(video_path, PROJECT_ROOT)
    base_name = os.path.splitext(relative_video_path)[0]  # removes .mp4 etc
    thumbnail_dir = os.path.join(THUMBNAILS_DIR, base_name)
    os.makedirs(thumbnail_dir, exist_ok=True)

    stillframes = [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 40]
    generated_thumbnails = []

    video_duration = get_video_duration(video_path)

    for idx, time in enumerate(stillframes):
        if time > video_duration:
            continue

        thumbnail_filename = f"thumb_{idx:02d}.jpg"
        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)

        if not os.path.exists(thumbnail_path):
            try:
                ffmpeg.input(video_path, ss=time).output(
                    thumbnail_path, vframes=1, vf=(
                        "scale='if(gt(iw,ih),300,-1)':'if(lt(iw,ih),300,-1)'"
                    ), strict='unofficial'
                ).run(capture_stdout=True, capture_stderr=True)
                print(f"Generated thumbnail: {thumbnail_path}")
            except ffmpeg.Error as e:
                print(f"Error generating thumbnail: {e}")
                continue

        generated_thumbnails.append(os.path.join(base_name, thumbnail_filename))

    return generated_thumbnails

def get_video_duration(video_path):
    """duration of vid in seconds"""
    try:
        probe = ffmpeg.probe(video_path, v='error', select_streams='v:0', show_entries='format=duration')
        duration = float(probe['format']['duration'])
        return duration
    except ffmpeg.Error as e:
        print(f"Error getting video duration: {e}")
        return 0

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
        thumbnails = generate_video_thumbnail(video_path)
        video_thumbnails[video] = thumbnails

    return render_template('index.html', videos=videos, video_thumbnails=video_thumbnails)

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

@app.route('/_thumbnails/<path:filename>')
def serve_thumbnail(filename):
    """serve thumbnail"""
    return send_from_directory(THUMBNAILS_DIR, filename)

@app.route('/directory/', defaults={'subdir': ''})
@app.route('/directory/<path:subdir>')
def directory(subdir):
    """Serve the directory structure and videos"""
    if subdir:
        dir_path = os.path.join(PROJECT_ROOT, subdir)
    else:
        dir_path = PROJECT_ROOT

    directory_tree = {}
    video_thumbnails = {}

    for root, _, files in os.walk(dir_path):
        relative_dir = os.path.relpath(root, PROJECT_ROOT)
        video_files = []

        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                video_files.append(os.path.join(relative_dir, file))

        if video_files:
            directory_tree[relative_dir] = video_files

        for video in video_files:
            video_path = os.path.join(PROJECT_ROOT, video)
            thumbnails = generate_video_thumbnail(video_path)

            if thumbnails:
                video_thumbnails[video] = thumbnails

    return render_template(
        'filter.html', 
        directory_tree=directory_tree,
        video_thumbnails=video_thumbnails,
        path_sep=os.path.sep
    )

@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    """get favorite"""
    with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/api/favorite', methods=['POST'])
def set_favorite():
    """set favorite"""
    data = request.get_json()
    filename = data['filename']
    status = data['favorite']

    with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
        favorites = json.load(f)

    if status:
        favorites[filename] = True
    else:
        favorites.pop(filename, None)

    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(favorites, f, indent=2, ensure_ascii=False)

    return jsonify(success=True)

if __name__ == '__main__':
    Timer(1, lambda: webbrowser.open_new('http://127.0.0.1:5000')).start()
    app.run(debug=True, use_reloader=False)
