# local-video

The `local-video` app is a simple Flask-based web application designed to manage and display video files on your local machine. It allows users to view video files, generate thumbnails, and stream videos directly from a local server.

###### Designed and coded by erikerikerikerikerikerikerik

## Features

- Automatically indexes videos and generates thumbnails.
- Displays a gallery of videos with thumbnails.
- Switch to directory tree gallery view.
- Plays video files with a built-in video player.
- Supports common video formats (`.mp4`, `.avi`, `.mov`, `.mkv`).
- Customizable thumbnail and template directories.

## Requirements

- Python 3.x
- Flask
- FFmpeg

## Structure

```bash
local-video/
│
├── _templates/            # Contains HTML templates and static files (CSS, JS, etc.)
├── _thumbnails/           # Contains generated video thumbnails
└── app.py                 # Main Flask app
```

The app will index all videos located in the project directory and/or subdirectories (`_templates` and `_thumbnails` directories excluded from index).

## Usage

1. Run the Flask server:

    ```bash
    python3 app.py
    ```

2. Open your browser and navigate to:

    ```bash
    http://127.0.0.1:5000/
    ```

The main page will display a gallery of videos. Thumbnails are automatically
generated for each supported video file. You can click on a thumbnail to play the corresponding video.
Video player supports timeskip with arrow keys!

- Erik