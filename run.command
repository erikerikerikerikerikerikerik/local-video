#!/bin/bash
# Change to the directory where the script is located
cd "$(dirname "$0")"

# Open a new terminal window and run python3 app.py
osascript <<EOF
tell application "Terminal"
    do script "cd '$(pwd)' && python3 app.py"
    activate
end tell
EOF