# local-video

This is a simple Flask-based web application that allows users to browse and view videos from a specified directory structure.

###### Designed and coded by erikerikerikerikerikerikerik 

## Features
- **Thumbnail Generation**: Automatically generates video thumbnails from videos located in subdirectories.
- **Gallery View**: Displays video thumbnails in a grid layout, with options to change the number of items per row.
- **Video Playback**: Clicking on a video thumbnail opens the video in a new window.
- **Dark Mode UI**: The app has a dark, modern look with hover effects and a floating control panel for layout changes.

## Requirements
- Python 3.x
- Flask
- FFmpeg

## Settings
With the current settings only videos in the project directory and subdirectories will be processed. The supported formats are '.mp4', '.avi', '.mov' and '.mkv'.

## Execute
To run the app:

```bash
python3 app.py
```

It will spawn a webserver under localhost or 127.0.0.1 (depending on your system settings) on port 5000. 