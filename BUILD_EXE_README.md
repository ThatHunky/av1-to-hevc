# Building AV1 to HEVC Converter Executables

This guide explains how to build standalone Windows executables (.exe files) for the AV1 to HEVC converter.

## Quick Build (Recommended)

1. **Install Python 3.8 or later** from [python.org](https://python.org)

2. **Double-click `quick_build.bat`**
   - This will automatically install PyInstaller and build both executables
   - The executables will be created in the `dist` folder

## Manual Build

If you prefer to build manually or customize the process:

```bash
# Install PyInstaller
pip install pyinstaller

# Build using the spec file
pyinstaller AV1toHEVC.spec --clean
```

## Build Options

### Method 1: Using the Spec File (Recommended)
The `AV1toHEVC.spec` file contains all build configurations:
- Edit this file to customize build options
- Run: `pyinstaller AV1toHEVC.spec`

### Method 2: Using the Build Script
For more advanced options, use the full build script:
```bash
python build_exe.py
```

This script:
- Creates an icon automatically
- Builds both GUI and console versions
- Generates an Inno Setup installer script
- Cleans up build artifacts

### Method 3: Manual PyInstaller Commands

Build GUI version (no console window):
```bash
pyinstaller --onefile --windowed --name AV1toHEVC-GUI gui_launcher.py
```

Build console version:
```bash
pyinstaller --onefile --console --name AV1toHEVC av1_to_hevc.py
```

## Output Files

After building, you'll find in the `dist` folder:

- **AV1toHEVC-GUI.exe** - Graphical interface (no console window)
  - Double-click to launch the GUI
  - Best for casual users
  
- **AV1toHEVC.exe** - Command-line interface
  - Run from command prompt or PowerShell
  - Supports all CLI features and batch processing

## File Sizes

The executables will be approximately:
- GUI version: 15-25 MB
- Console version: 12-20 MB

The size includes Python runtime and all dependencies.

## Important Notes

1. **FFmpeg Requirement**: The executables still require FFmpeg to be installed separately on the target system. FFmpeg is not bundled due to licensing and size considerations.

2. **Antivirus Warnings**: Some antivirus software may flag PyInstaller executables as suspicious. This is a false positive. You can:
   - Add an exception for the executables
   - Sign the executables with a code signing certificate
   - Build from source on the target machine

3. **Windows Only**: These build instructions create Windows executables. For other platforms:
   - macOS: Use `py2app` or create a `.app` bundle
   - Linux: Use `PyInstaller` on Linux or create an AppImage

## Creating an Installer

After building, you can create a Windows installer:

1. Install [Inno Setup](https://jrsoftware.org/isinfo.php)
2. The build script creates `installer.iss`
3. Open it in Inno Setup and compile

This creates a professional installer with:
- Start menu shortcuts
- Desktop icon (optional)
- Uninstaller
- File associations (optional)

## Troubleshooting

### PyInstaller not found
```
pip install --upgrade pyinstaller
```

### Build fails with import errors
Make sure all dependencies are installed:
```
pip install -r requirements.txt
```

### Executable doesn't run
- Check that all Python files are in the same directory
- Ensure no syntax errors: `python -m py_compile *.py`
- Try building with `--debug` flag for more information

### Large file size
To reduce size:
- Use UPX compression (already enabled)
- Exclude unnecessary modules in the spec file
- Consider using `--onedir` instead of `--onefile`

## Customization

### Adding an Icon
1. Create or download a `.ico` file
2. Name it `icon.ico` and place in the project directory
3. The build scripts will automatically use it

### Version Information
Edit `build_exe.py` to change:
- Application name
- Version number
- Author information
- Description

### Build Optimization
In `AV1toHEVC.spec`, you can:
- Add/remove hidden imports
- Exclude unnecessary modules
- Adjust compression settings
- Add version information

## Distribution

When distributing the executables:

1. **Include README**: Explain FFmpeg requirement
2. **System Requirements**: 
   - Windows 7 or later
   - FFmpeg installed and in PATH
   - 2GB RAM minimum
   - GPU with HEVC encoding support (optional)

3. **Create a Package**:
   ```
   AV1toHEVC-v1.0.0-Windows/
   ├── AV1toHEVC-GUI.exe
   ├── AV1toHEVC.exe
   ├── README.txt
   └── LICENSE.txt
   ```

## Security Considerations

For production distribution:
1. **Code Signing**: Sign executables with a certificate
2. **Virus Scanning**: Submit to VirusTotal before release
3. **Checksums**: Provide SHA256 hashes
4. **HTTPS**: Host on secure servers

## Support

If you encounter issues:
1. Check the [main README](README.md) for usage instructions
2. Ensure FFmpeg is properly installed
3. Try building with verbose output: `pyinstaller --debug all`
4. Report issues with full error messages and system details 