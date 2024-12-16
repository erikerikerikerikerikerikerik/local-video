# Video Gallery Web App

This is a simple Flask-based web application that allows users to browse and view videos from a specified directory structure.

## Features:
- **Thumbnail Generation**: Automatically generates video thumbnails from videos located in subdirectories.
- **Gallery View**: Displays video thumbnails in a grid layout, with options to change the number of items per row (3, 5, or 10).
- **Video Playback**: Clicking on a video thumbnail opens the video in a new window.
- **Dark Mode UI**: The app has a dark, modern look with hover effects and a floating control panel for layout changes.

## Requirements:
- Python 3.x
- Flask
- FFmpeg

## Setup:
1. Clone the repository:
   git clone <repository-url>
   cd <repository-directory>

2. Install the required dependencies:
   pip install -r requirements.txt

3. Make sure `ffmpeg` is installed on your system. If not, install it via your package manager:
   - On Ubuntu/Debian:
     sudo apt-get install ffmpeg
   - On macOS (with Homebrew):
     brew install ffmpeg

4. Run the Flask app:
   python app.py

5. Open your browser and visit:
   http://localhost:5000

## Directory Structure:
- **`app.py`**: Main Flask application.
- **`templates/`**: HTML templates, including the gallery page.
- **`thumbnails/`**: Folder where video thumbnails are stored.

## Customization:
- To change the directory for videos, update the `video_dir` variable in `app.py`.
- You can control the number of items per row by using the floating buttons on the page (3, 5, or 10 per row).

## License:
MIT License