#!/bin/bash
cd "$(dirname "$0")"

osascript <<EOF
tell application "Terminal"
    do script "cd '$(pwd)' && python3 app.py"
    activate
end tell
EOF