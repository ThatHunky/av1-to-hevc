# AV1 to HEVC Video Converter

A high-performance video conversion tool for converting AV1 videos to HEVC (H.265) with GPU acceleration, HDR preservation, and batch processing capabilities. Available in both command-line and graphical user interface versions.

## Features

- **GPU Acceleration**: Automatically detects and uses available GPU encoders:
  - NVIDIA NVENC (hevc_nvenc)
  - AMD AMF (hevc_amf) 
  - Intel Quick Sync Video (hevc_qsv)
  - Falls back to CPU encoding (libx265) if no GPU available

- **HDR Preservation**: Maintains HDR10, HDR10+, and HLG metadata
- **Batch Processing**: Convert entire directories of AV1 videos
- **Quality Control**: Configurable quality settings (CRF/CQ/QP)
- **Progress Tracking**: Real-time conversion progress with ETA
- **Smart Output**: Generates appropriate output filenames and paths
- **Comprehensive Logging**: Detailed logging with verbose mode
- **Dry Run Mode**: Preview what will be converted without actually converting
- **Graphical Interface**: Modern GUI with drag-and-drop support and visual progress tracking
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Requirements

- **FFmpeg**: Must be installed and available in PATH
- **Python 3.8+**: Required for running the script
- **GPU Drivers**: Latest drivers for GPU acceleration (optional)

### FFmpeg Installation

**Windows:**
```bash
# Using winget
winget install Gyan.FFmpeg

# Using chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# CentOS/RHEL/Fedora
sudo dnf install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/av1-to-hevc.git
   cd av1-to-hevc
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   python av1_to_hevc.py info
   ```

## Usage

### Graphical User Interface (Recommended)

Launch the GUI for an intuitive interface:

**Windows:**
```bash
# Double-click convert_gui.bat, or run:
python gui_launcher.py
```

**macOS/Linux:**
```bash
# Run the GUI launcher:
./convert_gui.sh
# Or directly:
python3 gui_launcher.py
```

**Using the CLI:**
```bash
python av1_to_hevc.py gui
```

The GUI provides:
- Easy file and directory selection with browse dialogs
- Real-time conversion progress with visual feedback
- Quality presets and advanced settings
- System information and GPU detection
- Batch processing with progress tracking
- Drag-and-drop support (coming soon)

### Command Line Interface

Convert all AV1 videos in a directory:
```bash
python av1_to_hevc.py -d /path/to/videos
```

Convert a single file:
```bash
python av1_to_hevc.py convert input_video.mkv
```

### Command Line Options

```bash
# Show help
python av1_to_hevc.py --help

# Convert directory with custom quality
python av1_to_hevc.py -d /videos -q 20

# Convert with custom output directory
python av1_to_hevc.py -d /input -o /output

# Disable HDR preservation
python av1_to_hevc.py -d /videos --no-hdr

# Dry run (show what would be converted)
python av1_to_hevc.py -d /videos --dry-run

# Verbose logging
python av1_to_hevc.py -d /videos -v
```

### Examples

**Basic batch conversion:**
```bash
python av1_to_hevc.py -d "C:\Videos\AV1_Movies"
```

**High quality conversion:**
```bash
python av1_to_hevc.py -d /movies -q 18 -o /converted
```

**Convert single file with custom output:**
```bash
python av1_to_hevc.py convert movie.mkv -o movie_hevc.mkv -q 20
```

**Preview conversion without executing:**
```bash
python av1_to_hevc.py -d /videos --dry-run
```

## Quality Settings

The quality parameter (`-q`) controls the output quality:

- **1-18**: Very high quality (larger file sizes)
- **19-23**: High quality (recommended range)
- **24-28**: Medium quality 
- **29-35**: Lower quality (smaller file sizes)
- **36-51**: Very low quality

**Recommended settings:**
- **18-20**: For archival/reference quality
- **21-23**: For high quality viewing (default: 23)
- **24-26**: For standard quality/streaming
- **27-30**: For lower bitrate requirements

## GPU Acceleration

The tool automatically detects available GPU encoders:

### NVIDIA (NVENC)
- Requires GTX 1660/RTX 20 series or newer
- HEVC encoding support required
- Typically 3-5x faster than CPU

### AMD (AMF) 
- Requires RX 400 series or newer
- VCN (Video Core Next) support required
- Good quality and performance

### Intel (Quick Sync)
- Requires 7th gen Core processors or newer
- Built into Intel integrated graphics
- Lower quality than dedicated GPUs but very fast

### CPU Fallback
- Uses libx265 encoder
- Slower but highest quality
- Works on any system

## HDR Support

The converter preserves various HDR formats with intelligent handling for different encoder types:

- **HDR10**: Static metadata preservation
- **HDR10+**: Dynamic metadata support
- **HLG (Hybrid Log-Gamma)**: BBC/NHK standard
- **Dolby Vision**: Profile-dependent support

### HDR Handling by Encoder Type

**GPU Encoders (NVENC/AMF/QSV):**
- Automatically detects HDR parameters from input video
- Uses explicit color values (e.g., bt2020, smpte2084) instead of "copy"
- **NVENC**: Best support for HDR10, limited HLG support (auto-converts HLG to HDR10)
- **AMD AMF**: Good support for both HDR10 and HLG
- **Intel QSV**: Basic HDR support, varies by generation
- Automatic fallback to non-HDR if HDR parameters cause errors

**CPU Encoder (x265):**
- Uses FFmpeg's "copy" mode for perfect metadata preservation
- Maintains all original HDR metadata and side data
- Supports advanced HDR optimization parameters

HDR metadata includes:
- Color primaries (BT.2020)
- Transfer characteristics (PQ/HLG)
- Mastering display metadata
- Content light level information

## File Format Support

**Input formats** (AV1 video streams):
- `.mkv` - Matroska Video
- `.mp4` - MPEG-4 Part 14
- `.m4v` - iTunes Video
- `.mov` - QuickTime Movie
- `.avi` - Audio Video Interleave
- `.webm` - WebM Video

**Output format:**
- `.mkv` - Chosen for maximum compatibility with HEVC and HDR

## Performance Tips

1. **Use GPU acceleration** when available for 3-5x speed improvement
2. **Adjust quality settings** based on your needs (lower = faster)
3. **Process smaller batches** if memory is limited
4. **Use SSDs** for faster I/O during conversion
5. **Close other applications** to free up system resources

## Troubleshooting

### Common Issues

**FFmpeg not found:**
```
Error: FFmpeg not found. Please install FFmpeg and add it to PATH.
```
- Install FFmpeg and ensure it's in your system PATH
- Test with `ffmpeg -version` in command line

**No GPU encoder detected:**
- Update your GPU drivers to the latest version
- Verify GPU supports hardware encoding
- Check if GPU is being used by other applications

**Conversion failed:**
- Check input file is not corrupted
- Ensure sufficient disk space for output
- Try with different quality settings
- Enable verbose logging with `-v` for details

**HDR conversion issues:**
```
Error setting option color_primaries to value copy
```
- This error occurs with GPU encoders that don't support "copy" mode
- The converter now automatically detects HDR parameters and uses explicit values
- If issues persist, try disabling HDR preservation with `--no-hdr`

**NVENC HLG compatibility issues:**
```
Task finished with error code: -22 (Invalid argument)
```
- NVENC has limited support for HLG (Hybrid Log-Gamma) HDR content
- The converter automatically falls back to HDR10 parameters for better compatibility
- If conversion still fails, it will retry without HDR preservation
- For HLG content, consider using CPU encoding for better compatibility

**GUI conversion hangs:**
- Updated progress parsing to use FFmpeg's stderr output instead of progress pipe
- Added timeout handling (30 seconds with no output)
- Improved cancellation mechanism that properly terminates FFmpeg processes
- If conversion still hangs, check FFmpeg installation and try with verbose logging

**Permission errors:**
- Run with appropriate file permissions
- Check if files are in use by other applications
- Try running as administrator (Windows) or with sudo (Linux/macOS)

### Performance Issues

**Slow conversion speeds:**
- Enable GPU acceleration if available
- Lower quality settings for faster encoding
- Close other applications using GPU/CPU
- Check if thermal throttling is occurring

**High memory usage:**
- Process files individually instead of batch
- Restart the application periodically
- Check available system memory

## Advanced Configuration

The converter uses modular configuration that can be customized:

### Quality Presets
- Modify `config.py` to adjust encoder-specific parameters
- Add custom quality presets for different use cases
- Configure HDR metadata handling

### Encoder Settings
- NVIDIA NVENC: Spatial/temporal AQ, B-frame settings
- AMD AMF: Rate control modes, quality presets  
- Intel QSV: Look-ahead, target usage settings
- CPU x265: Advanced parameter tuning

## Contributing

Contributions are welcome! Please feel free to submit pull requests or create issues for bugs and feature requests.

### Development Setup

1. Fork the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Make your changes and test thoroughly
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FFmpeg team for the excellent multimedia framework
- GPU vendors (NVIDIA, AMD, Intel) for hardware acceleration APIs
- Python community for the great libraries used in this project 