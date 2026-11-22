#!/bin/bash
cd "$(dirname "$0")" || exit 1

if [ ! -x ".venv/bin/python" ]; then
    echo "Mac Python environment not found."
    echo "First double-click 'Setup Pinterest Automation Mac.command'."
    read -r -p "Press Return to close..." _
    exit 1
fi

echo "Starting Pinterest Automation for macOS..."
".venv/bin/python" gui_app.py
status=$?
if [ "$status" -ne 0 ]; then
    echo
    echo "The application exited with code $status."
    read -r -p "Press Return to close..." _
fi
exit "$status"
