"""
Utility module for video converter.
Handles file operations, validation, and helper functions.
"""

import os
import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from config import SUPPORTED_CODECS


class VideoUtils:
    """Utility class for video file operations and validation."""
    
    # Supported video file extensions
    VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.m4v', '.mov', '.avi', '.webm', '.mpg', '.mpeg', '.wmv', '.flv'}
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def find_videos_by_codec(directory: Path, target_codec: Optional[str] = None) -> List[Path]:
        """
        Find video files with specific codec in the given directory.
        
        Args:
            directory: Directory to search for videos
            target_codec: Target codec to filter by (None means all videos)
            
        Returns:
            List of Path objects for video files
        """
        videos = []
        
        for file_path in directory.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix.lower() in VideoUtils.VIDEO_EXTENSIONS):
                
                if target_codec:
                    codec = VideoUtils.get_video_codec(file_path)
                    if codec == target_codec:
                        videos.append(file_path)
                else:
                    videos.append(file_path)
        
        return sorted(videos)
    
    @staticmethod
    def find_av1_videos(directory: Path) -> List[Path]:
        """
        Find all AV1 video files in the given directory.
        Kept for backward compatibility.
        
        Args:
            directory: Directory to search for AV1 videos
            
        Returns:
            List of Path objects for AV1 video files
        """
        return VideoUtils.find_videos_by_codec(directory, 'av1')
    
    @staticmethod
    def get_video_codec(file_path: Path) -> Optional[str]:
        """
        Get the video codec of a file.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Codec name (av1, hevc, h264, vp9, etc.) or None if detection fails
        """
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', str(file_path)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        codec_name = stream.get('codec_name', '').lower()
                        
                        # Map FFmpeg codec names to our standard names
                        codec_mapping = {
                            'av1': 'av1',
                            'hevc': 'hevc',
                            'h265': 'hevc',
                            'h264': 'h264',
                            'avc': 'h264',
                            'vp9': 'vp9',
                            'vp8': 'vp8',
                            'mpeg2video': 'mpeg2',
                            'mpeg4': 'mpeg4',
                        }
                        
                        for key, value in codec_mapping.items():
                            if key in codec_name:
                                return value
                        
                        # Return original codec name if not in mapping
                        return codec_name
        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, 
                json.JSONDecodeError, FileNotFoundError):
            pass
        
        return None
    
    @staticmethod
    def is_av1_video(file_path: Path) -> bool:
        """
        Check if a video file contains AV1 codec.
        Kept for backward compatibility.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            True if the file contains AV1 video stream
        """
        return VideoUtils.get_video_codec(file_path) == 'av1'
    
    @staticmethod
    def get_video_info(file_path: Path) -> Optional[Dict]:
        """
        Get detailed video information using ffprobe.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Dictionary with video information or None if failed
        """
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', '-show_format', str(file_path)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, 
                json.JSONDecodeError, FileNotFoundError):
            pass
        
        return None
    
    @staticmethod
    def has_hdr_metadata(file_path: Path) -> bool:
        """
        Check if video file contains HDR metadata.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            True if HDR metadata is detected
        """
        info = VideoUtils.get_video_info(file_path)
        if not info:
            return False
        
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'video':
                # Check for HDR indicators
                color_transfer = stream.get('color_transfer')
                color_primaries = stream.get('color_primaries')
                
                # HDR10/HDR10+ indicators
                if (color_transfer in ['smpte2084', 'arib-std-b67'] or
                    color_primaries == 'bt2020'):
                    return True
                
                # Check for HDR side data
                side_data = stream.get('side_data_list', [])
                for data in side_data:
                    data_type = data.get('side_data_type')
                    if data_type in ['Mastering display metadata', 
                                   'Content light level metadata']:
                        return True
        
        return False
    
    @staticmethod
    def generate_output_path(input_path: Path, output_dir: Optional[Path] = None, 
                           output_codec: str = "hevc", suffix: Optional[str] = None) -> Path:
        """
        Generate output file path for converted video.
        
        Args:
            input_path: Path to input video file
            output_dir: Output directory (defaults to same as input)
            output_codec: Target codec for determining file extension
            suffix: Optional suffix to add to filename
            
        Returns:
            Path object for output file
        """
        if output_dir is None:
            output_dir = input_path.parent
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine file extension based on output codec
        codec_extensions = {
            'hevc': '.mkv',
            'h264': '.mp4',
            'av1': '.mkv',
            'vp9': '.webm',
        }
        extension = codec_extensions.get(output_codec, '.mkv')
        
        # Generate new filename
        stem = input_path.stem
        
        # Add codec info to suffix if not provided
        if suffix is None:
            input_codec = VideoUtils.get_video_codec(input_path)
            if input_codec and output_codec:
                suffix = f"_{input_codec}_to_{output_codec}"
            else:
                suffix = f"_{output_codec}"
        
        output_filename = f"{stem}{suffix}{extension}"
        return output_dir / output_filename
    
    @staticmethod
    def get_file_size_mb(file_path: Path) -> float:
        """Get file size in megabytes."""
        try:
            return file_path.stat().st_size / (1024 * 1024)
        except OSError:
            return 0.0
    
    @staticmethod
    def validate_ffmpeg() -> bool:
        """
        Validate that FFmpeg is available and working.
        
        Returns:
            True if FFmpeg is available
        """
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, 
                FileNotFoundError):
            return False
    
    @staticmethod
    def estimate_conversion_time(file_size_mb: float, gpu_available: bool = False) -> str:
        """
        Estimate conversion time based on file size and hardware.
        
        Args:
            file_size_mb: File size in megabytes
            gpu_available: Whether GPU acceleration is available
            
        Returns:
            Estimated time as a human-readable string
        """
        # Rough estimates based on typical performance
        # These are very approximate and depend on many factors
        if gpu_available:
            # GPU encoding is typically 3-5x faster
            minutes_per_gb = 2.0
        else:
            # CPU encoding
            minutes_per_gb = 8.0
        
        estimated_minutes = (file_size_mb / 1024) * minutes_per_gb
        
        if estimated_minutes < 1:
            return "< 1 minute"
        elif estimated_minutes < 60:
            return f"~{int(estimated_minutes)} minutes"
        else:
            hours = int(estimated_minutes // 60)
            mins = int(estimated_minutes % 60)
            return f"~{hours}h {mins}m"
    
    @staticmethod
    def get_codec_display_name(codec: str) -> str:
        """Get display name for a codec."""
        if codec in SUPPORTED_CODECS["input"]:
            return SUPPORTED_CODECS["input"][codec]["name"]
        elif codec in SUPPORTED_CODECS["output"]:
            return SUPPORTED_CODECS["output"][codec]["name"]
        return codec.upper()
    
    @staticmethod
    def is_video_file(file_path: Path) -> bool:
        """
        Check if a file is a video file based on extension and codec detection.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is a valid video file
        """
        # First check extension
        if file_path.suffix.lower() not in VideoUtils.VIDEO_EXTENSIONS:
            return False
        
        # Then try to detect codec
        codec = VideoUtils.get_video_codec(file_path)
        return codec is not None
    
    @staticmethod
    def find_video_files(directory: Path) -> List[Path]:
        """
        Find all video files in the given directory.
        
        Args:
            directory: Directory to search for videos
            
        Returns:
            List of Path objects for video files
        """
        return VideoUtils.find_videos_by_codec(directory, None)


def setup_logging(verbose: bool = False) -> None:
    """
    Set up logging configuration.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Suppress ffmpeg-python debug messages unless verbose
    if not verbose:
        logging.getLogger('ffmpeg').setLevel(logging.WARNING) 