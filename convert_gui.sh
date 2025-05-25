#!/bin/bash
# AV1 to HEVC Converter - GUI Launcher (Unix)
# Run this script to launch the graphical interface

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Launch the GUI
python3 "$SCRIPT_DIR/gui_launcher.py" 