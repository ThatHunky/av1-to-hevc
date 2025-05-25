@echo off
echo Building AV1 to HEVC Converter executables...
echo.

REM Install requirements if needed
pip install pyinstaller

REM Build using the spec file
pyinstaller AV1toHEVC.spec --clean

echo.
echo Build complete! Check the dist folder for:
echo - AV1toHEVC-GUI.exe (Graphical interface - no console window)
echo - AV1toHEVC.exe (Command-line interface)
echo.
pause 