"""
AV1 to HEVC Video Converter

A high-performance command-line tool for converting AV1 videos to HEVC (H.265) 
with GPU acceleration, HDR preservation, and batch processing capabilities.
"""

__version__ = "1.0.0"
__author__ = "AV1 to HEVC Converter Team"
__license__ = "MIT"

from .config import Config
from .converter import VideoConverter, BatchConverter, ConversionProgress
from .utils import VideoUtils, setup_logging

__all__ = [
    "Config",
    "VideoConverter", 
    "BatchConverter",
    "ConversionProgress",
    "VideoUtils",
    "setup_logging"
] 