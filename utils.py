"""
Utility module for AV1 to HEVC converter.
Handles file operations, validation, and helper functions.
"""

import os
import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class VideoUtils:
    """Utility class for video file operations and validation."""
    
    # Supported video file extensions
    VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.m4v', '.mov', '.avi', '.webm'}
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def find_av1_videos(directory: Path) -> List[Path]:
        """
        Find all AV1 video files in the given directory.
        
        Args:
            directory: Directory to search for AV1 videos
            
        Returns:
            List of Path objects for AV1 video files
        """
        av1_videos = []
        
        for file_path in directory.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix.lower() in VideoUtils.VIDEO_EXTENSIONS):
                
                if VideoUtils.is_av1_video(file_path):
                    av1_videos.append(file_path)
        
        return sorted(av1_videos)
    
    @staticmethod
    def is_av1_video(file_path: Path) -> bool:
        """
        Check if a video file contains AV1 codec.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            True if the file contains AV1 video stream
        """
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', str(file_path)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for stream in data.get('streams', []):
                    if (stream.get('codec_type') == 'video' and 
                        stream.get('codec_name') == 'av1'):
                        return True
        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, 
                json.JSONDecodeError, FileNotFoundError):
            pass
        
        return False
    
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
                           suffix: str = "_hevc") -> Path:
        """
        Generate output file path for converted video.
        
        Args:
            input_path: Path to input video file
            output_dir: Output directory (defaults to same as input)
            suffix: Suffix to add to filename
            
        Returns:
            Path object for output file
        """
        if output_dir is None:
            output_dir = input_path.parent
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate new filename
        stem = input_path.stem
        extension = '.mkv'  # Use MKV for maximum compatibility with HEVC
        
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