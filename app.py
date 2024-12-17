"""
local-video app
**Designed and coded by erikerikerikerikerikerikerik - Erik Bruil**
"""

import os
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
    """generate video thumbnail"""
    video_filename = os.path.basename(video_path)
    thumbnail_filename = os.path.splitext(video_filename)[0] + '.jpg'
    thumbnail_path = os.path.join(THUMBNAILS_DIR, thumbnail_filename)

    if os.path.exists(thumbnail_path):
        return thumbnail_filename

    try:
        ffmpeg.input(video_path, ss=12).output(
            thumbnail_path, vframes=1, vf=(
                "scale="
                "'if(gt(iw,ih),300,-1)':"
                "'if(lt(iw,ih),300,-1)'"
            ), strict='unofficial'
        ).run(capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        print(f"Error generating thumbnail for {video_filename}: {e.stderr.decode('utf-8')}")
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

@app.route('/_thumbnails/<path:filename>')
def serve_thumbnail(filename):
    """serve thumbnail"""
    return send_from_directory(THUMBNAILS_DIR, filename)

def build_directory_tree(root_dir):
    """Build a directory tree"""
    directory_tree = {}
    for root, _, files in os.walk(root_dir):
        if any(excluded_dir in root for excluded_dir in EXCLUDED_DIRS):
            continue
        relative_dir = os.path.relpath(root, root_dir)
        video_files = [
            os.path.join(relative_dir, f)
            for f in files
            if f.lower().endswith(SUPPORTED_EXTENSIONS)
        ]
        if video_files:
            directory_tree[relative_dir] = video_files
    return directory_tree

@app.route('/directory/', defaults={'subdir': ''})
@app.route('/directory/<path:subdir>')
def directory(subdir):
    """Serve the directory structure and videos"""
    if subdir:
        dir_path = os.path.join(PROJECT_ROOT, subdir)
    else:
        dir_path = PROJECT_ROOT

    directory_tree = {}
    thumbnails = {}

    for root, _, files in os.walk(dir_path):
        relative_dir = os.path.relpath(root, PROJECT_ROOT)
        video_files = []
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                video_files.append(os.path.join(relative_dir, file))
                video_path = os.path.join(PROJECT_ROOT, file)
                thumbnail_filename = generate_video_thumbnail(video_path)
                if thumbnail_filename:
                    thumbnails[file] = thumbnail_filename

        if video_files:
            directory_tree[relative_dir] = video_files

    return render_template(
        'filter.html', 
        directory_tree=directory_tree,
        thumbnails=thumbnails,
        path_sep=os.path.sep
    )

if __name__ == '__main__':
    app.run(debug=True)
