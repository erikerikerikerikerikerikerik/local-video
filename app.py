"""
local-video app
**Designed and coded by erikerikerikerikerikerikerik - Erik Bruil**
"""

import os
import webbrowser
from threading import Timer, Thread
import json
import ffmpeg
from flask import Flask, render_template, send_from_directory
from flask import Response, request, jsonify, abort
from werkzeug.utils import safe_join

app = Flask(__name__, static_folder='_templates', template_folder='_templates')

PROJECT_ROOT = os.path.abspath('.')
VIDEO_ROOT = os.path.join(PROJECT_ROOT, 'video')
DATA_DIR = os.path.join(PROJECT_ROOT, '_data')
THUMBNAILS_DIR = os.path.join(PROJECT_ROOT, '_thumbnails')
FAVORITES_FILE = os.path.join(DATA_DIR, 'favorites.json')
TAGS_FILE = os.path.join(DATA_DIR, 'tags.json')
SUPPORTED_EXTENSIONS = ('.mp4')

MIN_PREVIEW_THUMBNAILS = 2
MAX_PREVIEW_THUMBNAILS = 20
MIN_THUMBNAIL_INTERVAL = 2
MAX_THUMBNAIL_INTERVAL = 5

for directory in [VIDEO_ROOT, DATA_DIR, THUMBNAILS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

if not os.path.exists(FAVORITES_FILE):
    old_favorites_file = os.path.join(PROJECT_ROOT, 'favorites.json')
    if os.path.exists(old_favorites_file):
        with open(old_favorites_file, 'r', encoding='utf-8') as old_file:
            favorites = json.load(old_file)
    else:
        favorites = {}
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(favorites, f, indent=2, ensure_ascii=False)

if not os.path.exists(TAGS_FILE):
    with open(TAGS_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=2, ensure_ascii=False)


def resolve_video_path(relative_path):
    """resolve a relative video path safely within VIDEO_ROOT"""
    resolved_path = safe_join(VIDEO_ROOT, relative_path)
    if not resolved_path:
        abort(404)
    return resolved_path


def load_tags():
    """load video tags"""
    with open(TAGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_tags(tags):
    """save video tags"""
    with open(TAGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tags, f, indent=2, ensure_ascii=False)


def normalize_tag(tag):
    """normalize tag text"""
    return " ".join(str(tag).strip().lower().split())


def get_all_tags(tags):
    """return all tags that are assigned to at least one video"""
    assigned_tags = set()
    for video_tags in tags.values():
        for tag in video_tags:
            assigned_tags.add(tag)
    return sorted(assigned_tags)


def generate_poster_thumbnail(video_path):
    """generate a single poster thumbnail if missing"""
    relative_video_path = os.path.relpath(video_path, VIDEO_ROOT)
    base_name = os.path.splitext(relative_video_path)[0]
    thumbnail_dir = os.path.join(THUMBNAILS_DIR, base_name)
    os.makedirs(thumbnail_dir, exist_ok=True)
    poster_filename = "poster.jpg"
    poster_path = os.path.join(thumbnail_dir, poster_filename)
    poster_relative_path = os.path.join(base_name, poster_filename)
    if os.path.exists(poster_path):
        return poster_relative_path
    try:
        ffmpeg.input(video_path, ss=20).output(
            poster_path, vframes=1, vf=(
                "scale='if(gt(iw,ih),300,-1)':'if(lt(iw,ih),300,-1)'"
            ), strict='unofficial'
        ).run(capture_stdout=True, capture_stderr=True)
        print(f"Generated poster thumbnail: {poster_path}")
    except ffmpeg.Error as e:
        print(f"Error generating poster thumbnail for {relative_video_path}: {e}")
        return None
    return poster_relative_path


def generate_preview_thumbnails_background(video_path):
    """generate preview thumbnails in the background"""
    thread = Thread(target=generate_video_thumbnail, args=(video_path,), daemon=True)
    thread.start()


def calculate_thumbnail_timestamps(video_duration):
    """calculate thumbnail timestamps spread over the video duration"""
    if video_duration <= 0:
        return []
    usable_duration = max(0, video_duration - 2)
    if usable_duration <= 0:
        return [0]
    thumbnail_count = int(usable_duration // MAX_THUMBNAIL_INTERVAL) + 1
    thumbnail_count = max(MIN_PREVIEW_THUMBNAILS, thumbnail_count)
    thumbnail_count = min(MAX_PREVIEW_THUMBNAILS, thumbnail_count)
    if thumbnail_count == 1:
        return [min(1, usable_duration)]
    interval = usable_duration / (thumbnail_count - 1)
    if interval < MIN_THUMBNAIL_INTERVAL:
        thumbnail_count = int(usable_duration // MIN_THUMBNAIL_INTERVAL) + 1
        thumbnail_count = max(1, thumbnail_count)
        thumbnail_count = min(MAX_PREVIEW_THUMBNAILS, thumbnail_count)
    if thumbnail_count == 1:
        return [min(1, usable_duration)]
    interval = usable_duration / (thumbnail_count - 1)
    return [round(index * interval, 2) for index in range(thumbnail_count)]


def generate_video_thumbnail(video_path):
    """generate preview thumbnails"""
    relative_video_path = os.path.relpath(video_path, VIDEO_ROOT)
    base_name = os.path.splitext(relative_video_path)[0]
    thumbnail_dir = os.path.join(THUMBNAILS_DIR, base_name)
    os.makedirs(thumbnail_dir, exist_ok=True)
    generated_thumbnails = []
    video_duration = get_video_duration(video_path)
    timestamps = calculate_thumbnail_timestamps(video_duration)
    expected_thumbnails = [
        os.path.join(base_name, f"thumb_{index:02d}.jpg")
        for index in range(len(timestamps))
    ]
    expected_paths = [
        os.path.join(thumbnail_dir, f"thumb_{index:02d}.jpg")
        for index in range(len(timestamps))
    ]
    if timestamps and all(os.path.exists(path) for path in expected_paths):
        return expected_thumbnails
    for idx, time in enumerate(timestamps):
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
                print(f"Generated preview thumbnail: {thumbnail_path}")
            except ffmpeg.Error as e:
                print(f"Error generating preview thumbnail for {relative_video_path}: {e}")
                continue
        generated_thumbnails.append(os.path.join(base_name, thumbnail_filename))
    return generated_thumbnails


def get_video_duration(video_path):
    """video duration"""
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
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                yield chunk
    return generate()


@app.route('/')
def index():
    """index /"""
    videos = find_videos(VIDEO_ROOT, [])
    video_thumbnails = {}
    for video in videos:
        video_path = resolve_video_path(video)
        poster = generate_poster_thumbnail(video_path)
        if poster:
            video_thumbnails[video] = [poster]
            generate_preview_thumbnails_background(video_path)
    tags = load_tags()
    return render_template(
        'index.html',
        videos=videos,
        video_thumbnails=video_thumbnails,
        video_count=len(videos),
        tags=tags,
        all_tags=get_all_tags(tags),
    )


@app.route('/play/<path:filename>')
def play_video(filename):
    """play video"""
    return render_template('video_player.html', video_path=filename)


@app.route('/video/<path:filename>')
def serve_video(filename):
    """serve video"""
    video_path = resolve_video_path(filename)
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
    """serve directory"""
    if subdir:
        dir_path = resolve_video_path(subdir)
    else:
        dir_path = VIDEO_ROOT
    directory_tree = {}
    video_thumbnails = {}
    for root, _, files in os.walk(dir_path):
        relative_dir = os.path.relpath(root, VIDEO_ROOT)
        video_files = []
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                video_files.append(os.path.join(relative_dir, file))
        if video_files:
            directory_tree[relative_dir] = video_files
        for video in video_files:
            video_path = resolve_video_path(video)
            poster = generate_poster_thumbnail(video_path)
            if poster:
                video_thumbnails[video] = [poster]
                generate_preview_thumbnails_background(video_path)
    return render_template(
        'filter.html',
        directory_tree=directory_tree,
        video_thumbnails=video_thumbnails,
        path_sep=os.path.sep,
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


@app.route('/api/tags', methods=['GET'])
def get_tags():
    """get all tags"""
    tags = load_tags()
    return jsonify({
        'videos': tags,
        'tags': get_all_tags(tags),
    })


@app.route('/api/video-tags', methods=['POST'])
def set_video_tag():
    """add or remove a tag for one video"""
    data = request.get_json()
    filename = data.get('filename', '')
    tag = normalize_tag(data.get('tag', ''))
    enabled = bool(data.get('enabled', True))
    if not filename or not tag:
        return jsonify(success=False, error='Missing filename or tag'), 400
    resolve_video_path(filename)
    tags = load_tags()
    video_tags = set(tags.get(filename, []))
    if enabled:
        video_tags.add(tag)
    else:
        video_tags.discard(tag)
    if video_tags:
        tags[filename] = sorted(video_tags)
    else:
        tags.pop(filename, None)
    save_tags(tags)
    return jsonify(success=True, tags=tags.get(filename, []), all_tags=get_all_tags(tags))


if __name__ == '__main__':
    Timer(1, lambda: webbrowser.open_new('http://127.0.0.1:5000')).start()
    app.run(debug=True, use_reloader=False)
