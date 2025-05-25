#!/usr/bin/env python3
"""
Build script for creating Windows executables using PyInstaller.
Creates both GUI and console versions of the AV1 to HEVC converter.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Build configuration
APP_NAME = "AV1toHEVC"
VERSION = "1.0.0"
AUTHOR = "AV1toHEVC Developers"
DESCRIPTION = "Convert AV1 videos to HEVC with GPU acceleration"

# PyInstaller options
COMMON_OPTIONS = [
    '--noconfirm',
    '--clean',
    '--onefile',
    f'--name={APP_NAME}',
    '--add-data=README.md;.',
    '--add-data=LICENSE;.',
    '--collect-all=ffmpeg',
    '--collect-all=tqdm',
    '--collect-all=colorama',
    '--hidden-import=tkinter',
    '--hidden-import=click',
]

def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} found")
        return True
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        return True

def create_icon():
    """Create a simple icon file if it doesn't exist."""
    icon_path = Path("icon.ico")
    if not icon_path.exists():
        print("Creating default icon...")
        # Create a simple icon using Pillow if available
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a 256x256 image with gradient background
            img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw gradient background
            for i in range(256):
                color = int(255 * (1 - i / 256))
                draw.rectangle([0, i, 256, i+1], fill=(0, color, 255, 255))
            
            # Draw text
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            text = "AV1\n→\nHEVC"
            draw.multiline_text((128, 128), text, fill=(255, 255, 255), 
                               font=font, anchor="mm", align="center")
            
            # Save as ICO
            img.save(icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print(f"✓ Created {icon_path}")
            return str(icon_path)
        except ImportError:
            print("Pillow not installed, skipping icon creation")
            return None
    else:
        print(f"✓ Using existing {icon_path}")
        return str(icon_path)

def build_gui_exe():
    """Build the GUI version of the application."""
    print("\n=== Building GUI executable ===")
    
    options = COMMON_OPTIONS.copy()
    options.extend([
        '--windowed',  # No console window
        '--name=AV1toHEVC-GUI',
        'gui_launcher.py'
    ])
    
    # Add icon if available
    icon = create_icon()
    if icon:
        options.insert(0, f'--icon={icon}')
    
    # Run PyInstaller
    print("Running PyInstaller for GUI version...")
    subprocess.check_call(['pyinstaller'] + options)
    
    print("✓ GUI executable built successfully")

def build_console_exe():
    """Build the console version of the application."""
    print("\n=== Building Console executable ===")
    
    options = COMMON_OPTIONS.copy()
    options.extend([
        '--console',  # Show console window
        '--name=AV1toHEVC-Console',
        'av1_to_hevc.py'
    ])
    
    # Add icon if available
    icon = create_icon()
    if icon:
        options.insert(0, f'--icon={icon}')
    
    # Run PyInstaller
    print("Running PyInstaller for Console version...")
    subprocess.check_call(['pyinstaller'] + options)
    
    print("✓ Console executable built successfully")

def create_installer_script():
    """Create an Inno Setup script for creating an installer."""
    iss_content = f"""#define MyAppName "{APP_NAME}"
#define MyAppVersion "{VERSION}"
#define MyAppPublisher "{AUTHOR}"
#define MyAppURL "https://github.com/yourusername/av1-to-hevc"
#define MyAppExeName "AV1toHEVC-GUI.exe"

[Setup]
AppId={{{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DisableProgramGroupPage=yes
LicenseFile=LICENSE
OutputDir=installer
OutputBaseFilename=AV1toHEVC-Setup-{{#MyAppVersion}}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
Source: "dist\\AV1toHEVC-GUI.exe"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "dist\\AV1toHEVC-Console.exe"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{autoprograms}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent
"""
    
    with open("installer.iss", "w") as f:
        f.write(iss_content)
    
    print("✓ Created Inno Setup script: installer.iss")

def clean_build():
    """Clean build artifacts."""
    print("\n=== Cleaning build artifacts ===")
    
    dirs_to_remove = ['build', '__pycache__', '.pytest_cache']
    files_to_remove = ['*.spec']
    
    for dir_name in dirs_to_remove:
        for path in Path('.').rglob(dir_name):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"✓ Removed {path}")
    
    for pattern in files_to_remove:
        for path in Path('.').glob(pattern):
            path.unlink()
            print(f"✓ Removed {path}")

def main():
    """Main build process."""
    print(f"=== Building {APP_NAME} v{VERSION} ===\n")
    
    # Check dependencies
    if not check_pyinstaller():
        print("Failed to install PyInstaller")
        sys.exit(1)
    
    # Clean previous builds
    clean_build()
    
    # Create output directory
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    # Build executables
    try:
        build_gui_exe()
        build_console_exe()
        
        # Create installer script (optional)
        create_installer_script()
        
        print(f"\n=== Build Complete ===")
        print(f"Executables created in: {dist_dir.absolute()}")
        print(f"- AV1toHEVC-GUI.exe (Graphical interface)")
        print(f"- AV1toHEVC-Console.exe (Command-line interface)")
        
        # Show file sizes
        for exe in dist_dir.glob("*.exe"):
            size_mb = exe.stat().st_size / (1024 * 1024)
            print(f"  {exe.name}: {size_mb:.1f} MB")
        
        print("\nNote: FFmpeg must still be installed separately on target systems.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 