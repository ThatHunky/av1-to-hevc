#!/bin/bash
# AV1 to HEVC Converter - Unix Shell Script
# Usage: ./convert.sh [directory] [options]

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the Python script with all arguments passed to this script
python3 "$SCRIPT_DIR/av1_to_hevc.py" "$@" 