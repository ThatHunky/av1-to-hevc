@echo off
REM AV1 to HEVC Converter - Windows Batch Script
REM Usage: convert.bat [directory] [options]

python "%~dp0av1_to_hevc.py" %*
pause 