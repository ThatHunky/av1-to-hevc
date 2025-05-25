@echo off
echo ===================================
echo Building AV1 to HEVC Converter EXE
echo ===================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from python.org
    pause
    exit /b 1
)

REM Install PyInstaller if not already installed
echo Installing/updating PyInstaller...
pip install --upgrade pyinstaller pillow

REM Run the build script
echo.
echo Starting build process...
python build_exe.py

echo.
echo Build process complete!
echo Check the 'dist' folder for the executables.
echo.
pause 