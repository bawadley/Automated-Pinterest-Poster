#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=============================================="
echo " Pinterest Automation - macOS Setup"
echo "=============================================="
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 was not found. Install Python 3 with Tkinter support."
    echo "Recommended: https://www.python.org/downloads/macos/"
    read -r -p "Press Return to close..." _
    exit 1
fi

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    echo "This Python installation does not include Tkinter."
    echo "Install the macOS Python from python.org, then try again."
    read -r -p "Press Return to close..." _
    exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
    echo "Creating the Mac-specific Python environment..."
    python3 -m venv .venv
fi

echo "Installing Python dependencies..."
".venv/bin/python" -m pip install -r requirements.txt

if [ ! -d "/Applications/Google Chrome.app" ] && \
   [ ! -d "$HOME/Applications/Google Chrome.app" ]; then
    echo
    echo "NOTE: This project uses Playwright's Google Chrome channel."
    echo "Install Google Chrome for macOS before publishing."
    echo "https://www.google.com/chrome/"
fi

echo
echo "Setup complete."
echo "Copy your existing .env configuration into this project folder."
echo "Log in to Pinterest using the GUI's Pinterest Login button."
echo "Run 'Pinterest Automation Mac.command' to open the app."
echo
read -r -p "Press Return to close..." _
