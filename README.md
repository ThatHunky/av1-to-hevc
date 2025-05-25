# Multi-Codec Video Converter

A high-performance video conversion tool for converting videos between different codecs with GPU acceleration, HDR preservation, and batch processing capabilities. Available in both command-line and graphical user interface versions.

## Features

- **Multi-Codec Support**: Convert between various video codecs:
  - **Input**: AV1, HEVC/H.265, H.264/AVC, VP9, VP8, MPEG-2, MPEG-4
  - **Output**: HEVC/H.265, H.264/AVC, AV1, VP9

- **GPU Acceleration**: Automatically detects and uses available GPU encoders:
  - NVIDIA NVENC (for HEVC, H.264, AV1)
  - AMD AMF (for HEVC, H.264)
  - Intel Quick Sync Video (for HEVC, H.264, AV1)
  - Falls back to CPU encoding if no GPU available

- **HDR Preservation**: Maintains HDR10, HDR10+, and HLG metadata (HEVC/AV1 only)
- **Batch Processing**: Convert entire directories with codec filtering
- **Quality Control**: Configurable quality settings adapted to each codec
- **Progress Tracking**: Real-time conversion progress with ETA
- **Smart Output**: Generates appropriate output filenames and container formats
- **Comprehensive Logging**: Detailed logging with verbose mode
- **Dry Run Mode**: Preview what will be converted without actually converting
- **Graphical Interface**: Modern GUI with codec selection and visual progress tracking
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
   git clone https://github.com/yourusername/video-converter.git
   cd video-converter
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
- Input/output codec selection with dropdown menus
- Real-time conversion progress with visual feedback
- Quality presets and advanced settings
- Codec filtering for batch operations
- System information and GPU detection
- HDR preservation options (for supported codecs)

### Command Line Interface

Convert videos with automatic codec detection:
```bash
# Convert all videos in a directory to HEVC
python av1_to_hevc.py -d /path/to/videos -c hevc

# Convert only AV1 videos to H.264
python av1_to_hevc.py -d /path/to/videos -i av1 -c h264

# Convert a single file to VP9
python av1_to_hevc.py convert input_video.mkv -c vp9
```

### Command Line Options

```bash
# Show help
python av1_to_hevc.py --help

# Convert directory with codec selection
python av1_to_hevc.py -d /videos -c hevc -q 20

# Filter by input codec
python av1_to_hevc.py -d /videos -i vp9 -c h264

# Custom output directory
python av1_to_hevc.py -d /input -o /output -c hevc

# Disable HDR preservation
python av1_to_hevc.py -d /videos --no-hdr -c hevc

# Dry run (show what would be converted)
python av1_to_hevc.py -d /videos -c av1 --dry-run

# Verbose logging
python av1_to_hevc.py -d /videos -c hevc -v
```

### Examples

**Convert AV1 videos to HEVC:**
```bash
python av1_to_hevc.py -d "C:\Videos\Movies" -i av1 -c hevc
```

**Convert all videos to H.264 for compatibility:**
```bash
python av1_to_hevc.py -d /movies -c h264 -q 23
```

**High quality HEVC conversion:**
```bash
python av1_to_hevc.py convert movie.mp4 -c hevc -q 18
```

**Convert VP9 videos to AV1:**
```bash
python av1_to_hevc.py -d /videos -i vp9 -c av1 -q 30
```

**Preview conversion without executing:**
```bash
python av1_to_hevc.py -d /videos -c hevc --dry-run
```

## Codec Support

### Input Codecs
- **AV1**: Modern codec with excellent compression
- **HEVC/H.265**: High efficiency video coding
- **H.264/AVC**: Most compatible codec
- **VP9**: Google's open video codec
- **VP8**: Older WebM video codec
- **MPEG-2**: Legacy broadcast/DVD codec
- **MPEG-4**: Older compression standard

### Output Codecs
- **HEVC/H.265**: Best quality/size ratio, HDR support
- **H.264/AVC**: Maximum compatibility
- **AV1**: Cutting-edge compression, HDR support
- **VP9**: Open codec for web streaming

### Container Formats
- **HEVC**: .mkv (Matroska)
- **H.264**: .mp4 (MPEG-4)
- **AV1**: .mkv (Matroska)
- **VP9**: .webm (WebM)

## Quality Settings

Quality parameters vary by codec:

### HEVC/H.264 (CRF 1-51)
- **1-18**: Very high quality (larger files)
- **19-23**: High quality (recommended)
- **24-28**: Medium quality
- **29-35**: Lower quality (smaller files)
- **36-51**: Very low quality

### AV1/VP9 (CRF 1-63)
- **1-20**: Very high quality
- **21-30**: High quality (recommended)
- **31-40**: Medium quality
- **41-50**: Lower quality
- **51-63**: Very low quality

**Recommended settings by use case:**
- **Archival**: 18-20 (HEVC/H.264) or 20-25 (AV1/VP9)
- **High quality viewing**: 21-23 (HEVC/H.264) or 28-32 (AV1/VP9)
- **Streaming**: 24-26 (HEVC/H.264) or 35-40 (AV1/VP9)
- **Mobile/Low bandwidth**: 27-30 (HEVC/H.264) or 40-45 (AV1/VP9)

## GPU Acceleration

The tool automatically detects and uses available hardware encoders:

### Codec Support by GPU

| GPU Type | HEVC | H.264 | AV1 | VP9 |
|----------|------|-------|-----|-----|
| NVIDIA   | ✓    | ✓     | ✓*  | ✗   |
| AMD      | ✓    | ✓     | ✗   | ✗   |
| Intel    | ✓    | ✓     | ✓** | ✗   |

*NVIDIA AV1 requires RTX 40 series or newer  
**Intel AV1 requires Arc GPU or 12th gen+ with iGPU

### Performance
- **GPU encoding**: 3-10x faster than CPU
- **Quality tradeoff**: GPU encoding is slightly lower quality than CPU at same settings
- **Power efficiency**: GPU encoding uses less power than CPU

## HDR Support

HDR metadata preservation is supported for:
- **HEVC**: Full HDR10, HDR10+, HLG support
- **AV1**: HDR10, HLG support
- **H.264**: Limited HDR support (not recommended)
- **VP9**: No HDR support

The converter intelligently handles HDR based on:
- Input content HDR metadata
- Output codec capabilities
- Encoder type (GPU vs CPU)

## File Format Support

**Input formats**:
- `.mkv` - Matroska Video
- `.mp4` - MPEG-4 Part 14
- `.m4v` - iTunes Video
- `.mov` - QuickTime Movie
- `.avi` - Audio Video Interleave
- `.webm` - WebM Video
- `.mpg/.mpeg` - MPEG Program Stream
- `.wmv` - Windows Media Video
- `.flv` - Flash Video

**Output formats** (by codec):
- HEVC: `.mkv`
- H.264: `.mp4`
- AV1: `.mkv`
- VP9: `.webm`

## Performance Tips

1. **Choose appropriate codec**: H.264 for compatibility, HEVC for quality/size, AV1 for best compression
2. **Use GPU acceleration** when available for speed
3. **Match quality to use case**: Don't over-compress for archival
4. **Consider source codec**: Avoid transcoding between similar codecs
5. **Use batch processing** for multiple files
6. **Monitor temperatures** during long conversions

## Troubleshooting

### Common Issues

**FFmpeg not found:**
- Install FFmpeg and ensure it's in your system PATH
- Test with `ffmpeg -version` in command line

**Unsupported codec:**
- Check if your FFmpeg build includes the required encoder
- Some codecs (like AV1) may need newer FFmpeg versions

**GPU encoder not detected:**
- Update GPU drivers to latest version
- Verify GPU model supports the target codec
- Check if GPU is being used by other applications

**HDR conversion issues:**
- HDR is only supported for HEVC and AV1 output
- Some GPU encoders have limited HDR support
- Try CPU encoding for better HDR compatibility

**Quality concerns:**
- GPU encoding trades quality for speed
- Use CPU encoding for maximum quality
- Adjust quality parameter based on codec

## Advanced Configuration

The converter uses modular configuration that can be customized:

### Custom Encoder Parameters
Edit `config.py` to modify:
- Encoder-specific settings
- Quality presets
- HDR handling parameters
- Container options

### Batch Processing Options
- Filter by multiple codecs
- Custom naming patterns
- Parallel processing (future feature)

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