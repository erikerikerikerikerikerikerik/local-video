"""
local-video app
**Designed and coded by erikerikerikerikerikerikerik - Erik Bruil**
"""

import os
import webbrowser
from threading import Timer
import ffmpeg
from flask import Flask, render_template, send_from_directory
from flask import Response, request

app = Flask(__name__, static_folder='_templates', template_folder='_templates')

PROJECT_ROOT = os.path.abspath('.')
EXCLUDED_DIRS = ['_templates', '_thumbnails']
THUMBNAILS_DIR = os.path.join(PROJECT_ROOT, '_thumbnails')
SUPPORTED_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv')

if not os.path.exists(THUMBNAILS_DIR):
    os.makedirs(THUMBNAILS_DIR)

def generate_video_thumbnail(video_path):
    """generate multiple thumbnails"""
    video_filename = os.path.basename(video_path)
    base_filename = os.path.splitext(video_filename)[0]

    os.makedirs(THUMBNAILS_DIR, exist_ok=True)

    first_thumbnail = os.path.join(THUMBNAILS_DIR, f"{base_filename}_00.jpg")

    stillframes = [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
    generated_thumbnails = [f"{base_filename}_{i:02d}.jpg" for i in range(len(stillframes))]

    if os.path.exists(first_thumbnail):
        print(f"First thumbnail found for {video_path}. Skipping further generation.")
        return [thumb for thumb in generated_thumbnails if os.path.exists(os.path.join(THUMBNAILS_DIR, thumb))]

    thumb_number = 0
    video_duration = get_video_duration(video_path)

    for time in stillframes:
        if time > video_duration:
            print(f"skipping {time} of {base_filename}")
            continue

        thumbnail_filename = f"{base_filename}_{thumb_number:02d}.jpg"
        thumbnail_path = os.path.join(THUMBNAILS_DIR, thumbnail_filename)

        if os.path.exists(thumbnail_path):
            print(f"Thumbnail already exists: {thumbnail_filename}")
            generated_thumbnails.append(thumbnail_filename)
        else:
            ffmpeg.input(video_path, ss=time).output(
                thumbnail_path, vframes=1, vf=(
                    "scale="
                    "'if(gt(iw,ih),300,-1)':"
                    "'if(lt(iw,ih),300,-1)'"
                ), strict='unofficial'
            ).run(capture_stdout=True, capture_stderr=True)

            print(f"Thumbnail generated: {thumbnail_path}")
            generated_thumbnails.append(thumbnail_filename)

        thumb_number += 1

    return [thumb for thumb in generated_thumbnails if os.path.exists(os.path.join(THUMBNAILS_DIR, thumb))]

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

if __name__ == '__main__':
    Timer(1, lambda: webbrowser.open_new('http://127.0.0.1:5000')).start()
    app.run(debug=True, use_reloader=False)
