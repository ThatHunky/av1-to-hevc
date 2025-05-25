"""
Configuration module for video converter.
Handles encoding parameters, GPU detection, and quality settings for multiple codecs.
"""

import subprocess
import logging
import json
from typing import Dict, List, Optional, Tuple

# Supported input and output codecs
SUPPORTED_CODECS = {
    "input": {
        "av1": {"name": "AV1", "ffmpeg_name": "av1"},
        "hevc": {"name": "HEVC/H.265", "ffmpeg_name": "hevc"},
        "h264": {"name": "H.264/AVC", "ffmpeg_name": "h264"},
        "vp9": {"name": "VP9", "ffmpeg_name": "vp9"},
        "vp8": {"name": "VP8", "ffmpeg_name": "vp8"},
        "mpeg2": {"name": "MPEG-2", "ffmpeg_name": "mpeg2video"},
        "mpeg4": {"name": "MPEG-4", "ffmpeg_name": "mpeg4"},
    },
    "output": {
        "hevc": {"name": "HEVC/H.265", "container": "mkv"},
        "h264": {"name": "H.264/AVC", "container": "mp4"},
        "av1": {"name": "AV1", "container": "mkv"},
        "vp9": {"name": "VP9", "container": "webm"},
    }
}

# Default encoding parameters
DEFAULT_CRF = 23  # Constant Rate Factor for quality (lower = better quality)
DEFAULT_PRESET = "medium"  # Encoding speed preset

# HDR parameters for different standards
HDR_PARAMS = {
    "hdr10": {
        "color_primaries": "bt2020",
        "color_trc": "smpte2084",
        "colorspace": "bt2020nc",
    },
    "hlg": {
        "color_primaries": "bt2020",
        "color_trc": "arib-std-b67",
        "colorspace": "bt2020nc",
    }
}

# Encoder configurations for different codecs
CODEC_ENCODERS = {
    "hevc": {
        "nvidia": {
            "encoder": "hevc_nvenc",
            "preset": "p4",
            "rc": "vbr",
            "cq": 23,
            "b_ref_mode": "middle",
            "spatial_aq": 1,
            "temporal_aq": 1,
        },
        "amd": {
            "encoder": "hevc_amf",
            "quality": "balanced",
            "rc": "cqp",
            "qp_i": 23,
            "qp_p": 23,
            "qp_b": 23,
        },
        "intel": {
            "encoder": "hevc_qsv",
            "preset": "medium",
            "global_quality": 23,
            "look_ahead": 1,
        },
        "cpu": {
            "encoder": "libx265",
            "crf": DEFAULT_CRF,
            "preset": DEFAULT_PRESET,
            "x265_params": "hdr-opt=1:repeat-headers=1:colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc"
        }
    },
    "h264": {
        "nvidia": {
            "encoder": "h264_nvenc",
            "preset": "p4",
            "rc": "vbr",
            "cq": 23,
            "b_ref_mode": "middle",
            "spatial_aq": 1,
            "temporal_aq": 1,
        },
        "amd": {
            "encoder": "h264_amf",
            "quality": "balanced",
            "rc": "cqp",
            "qp_i": 23,
            "qp_p": 23,
            "qp_b": 23,
        },
        "intel": {
            "encoder": "h264_qsv",
            "preset": "medium",
            "global_quality": 23,
            "look_ahead": 1,
        },
        "cpu": {
            "encoder": "libx264",
            "crf": DEFAULT_CRF,
            "preset": DEFAULT_PRESET,
        }
    },
    "av1": {
        "nvidia": {
            "encoder": "av1_nvenc",
            "preset": "p4",
            "rc": "vbr",
            "cq": 30,
        },
        "intel": {
            "encoder": "av1_qsv",
            "preset": "medium",
            "global_quality": 30,
        },
        "cpu": {
            "encoder": "libaom-av1",
            "crf": 30,
            "cpu-used": 4,
        }
    },
    "vp9": {
        "cpu": {
            "encoder": "libvpx-vp9",
            "crf": 30,
            "b:v": "0",
            "cpu-used": 4,
        }
    }
}


class Config:
    """Configuration class for video conversion settings."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gpu_type = self._detect_gpu()
        self.available_encoders = self._detect_available_encoders()
        
    def _detect_gpu(self) -> Optional[str]:
        """Detect available GPU and return type (nvidia/amd/intel) or None."""
        try:
            # Check for NVIDIA GPU
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True, text=True, timeout=10
            )
            
            if "hevc_nvenc" in result.stdout or "h264_nvenc" in result.stdout:
                self.logger.info("NVIDIA GPU encoder detected")
                return "nvidia"
            elif "hevc_amf" in result.stdout or "h264_amf" in result.stdout:
                self.logger.info("AMD GPU encoder detected")
                return "amd"
            elif "hevc_qsv" in result.stdout or "h264_qsv" in result.stdout:
                self.logger.info("Intel GPU encoder detected")
                return "intel"
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            self.logger.warning("Could not detect GPU encoders or FFmpeg not found")
            
        self.logger.info("No GPU encoder detected, will use CPU")
        return None
    
    def _detect_available_encoders(self) -> Dict[str, List[str]]:
        """Detect which encoders are available for each output codec."""
        available = {}
        
        try:
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True, text=True, timeout=10
            )
            
            encoders_output = result.stdout
            
            for codec, codec_configs in CODEC_ENCODERS.items():
                available[codec] = []
                
                # Check GPU encoders
                if self.gpu_type and self.gpu_type in codec_configs:
                    encoder_name = codec_configs[self.gpu_type]["encoder"]
                    if encoder_name in encoders_output:
                        available[codec].append(self.gpu_type)
                
                # Check CPU encoder
                if "cpu" in codec_configs:
                    encoder_name = codec_configs["cpu"]["encoder"]
                    if encoder_name in encoders_output:
                        available[codec].append("cpu")
            
        except Exception as e:
            self.logger.error(f"Error detecting available encoders: {e}")
            # Fallback to CPU encoders only
            for codec in CODEC_ENCODERS:
                available[codec] = ["cpu"]
        
        return available
    
    def get_encoder_config(self, output_codec: str, prefer_gpu: bool = True) -> Tuple[str, Dict]:
        """
        Get the best available encoder configuration for the given codec.
        
        Args:
            output_codec: Target codec (hevc, h264, av1, vp9)
            prefer_gpu: Whether to prefer GPU encoding if available
            
        Returns:
            Tuple of (encoder_type, config_dict)
        """
        if output_codec not in CODEC_ENCODERS:
            raise ValueError(f"Unsupported output codec: {output_codec}")
        
        available = self.available_encoders.get(output_codec, ["cpu"])
        
        # Select encoder type
        if prefer_gpu and self.gpu_type and self.gpu_type in available:
            encoder_type = self.gpu_type
        else:
            encoder_type = "cpu"
        
        # Get configuration
        if encoder_type in CODEC_ENCODERS[output_codec]:
            config = CODEC_ENCODERS[output_codec][encoder_type].copy()
        else:
            # Fallback to CPU if specific GPU encoder not configured
            encoder_type = "cpu"
            config = CODEC_ENCODERS[output_codec]["cpu"].copy()
        
        return encoder_type, config
    
    def _detect_hdr_params(self, input_path: str) -> Dict[str, str]:
        """
        Detect HDR parameters from input video file.
        
        Args:
            input_path: Path to input video file
            
        Returns:
            Dictionary with detected HDR parameters
        """
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', input_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        hdr_params = {}
                        
                        # Get color parameters
                        color_primaries = stream.get('color_primaries')
                        color_trc = stream.get('color_transfer')
                        color_space = stream.get('color_space')
                        color_range = stream.get('color_range')
                        
                        # Map to valid FFmpeg values with proper HDR type detection
                        detected_trc = color_trc or stream.get('color_transfer', '')
                        
                        # Determine HDR type first
                        is_hlg = any(x in str(detected_trc).lower() for x in ['arib-std-b67', 'hlg'])
                        is_hdr10 = any(x in str(detected_trc).lower() for x in ['smpte2084', 'pq'])
                        
                        if is_hlg:
                            # HLG (Hybrid Log-Gamma) parameters
                            hdr_params['color_primaries'] = 'bt2020'
                            hdr_params['color_trc'] = 'arib-std-b67'
                            hdr_params['colorspace'] = 'bt2020nc'
                            hdr_params['color_range'] = 'tv'
                        elif is_hdr10:
                            # HDR10 parameters
                            hdr_params['color_primaries'] = 'bt2020'
                            hdr_params['color_trc'] = 'smpte2084'
                            hdr_params['colorspace'] = 'bt2020nc'
                            hdr_params['color_range'] = 'tv'
                        else:
                            # Use detected values or defaults
                            hdr_params['color_primaries'] = color_primaries or 'bt2020'
                            hdr_params['color_trc'] = color_trc or 'smpte2084'
                            hdr_params['colorspace'] = color_space or 'bt2020nc'
                            hdr_params['color_range'] = color_range or 'tv'
                        
                        return hdr_params
        
        except Exception as e:
            self.logger.warning(f"Could not detect HDR parameters: {e}")
        
        # Return default HDR10 parameters
        return {
            'color_primaries': 'bt2020',
            'color_trc': 'smpte2084',
            'colorspace': 'bt2020nc',
            'color_range': 'tv'
        }
    
    def get_conversion_params(self, output_codec: str, preserve_hdr: bool = True, 
                            quality: Optional[int] = None, 
                            input_path: Optional[str] = None,
                            prefer_gpu: bool = True) -> List[str]:
        """
        Get FFmpeg parameters for video conversion.
        
        Args:
            output_codec: Target codec (hevc, h264, av1, vp9)
            preserve_hdr: Whether to preserve HDR metadata
            quality: Override default quality setting
            input_path: Path to input file for HDR parameter detection
            prefer_gpu: Whether to prefer GPU encoding
            
        Returns:
            List of FFmpeg parameters
        """
        params = []
        encoder_type, config = self.get_encoder_config(output_codec, prefer_gpu)
        
        # Set video codec
        params.extend(["-c:v", config["encoder"]])
        
        # Apply codec-specific parameters based on encoder type
        if output_codec == "hevc":
            params.extend(self._get_hevc_params(encoder_type, config, quality))
        elif output_codec == "h264":
            params.extend(self._get_h264_params(encoder_type, config, quality))
        elif output_codec == "av1":
            params.extend(self._get_av1_params(encoder_type, config, quality))
        elif output_codec == "vp9":
            params.extend(self._get_vp9_params(config, quality))
        
        # HDR preservation (if applicable)
        if preserve_hdr and output_codec in ["hevc", "av1"]:  # H.264 has limited HDR support
            params.extend(self._get_hdr_params(encoder_type, input_path))
        
        # Audio codec (copy without re-encoding)
        params.extend(["-c:a", "copy"])
        
        # Stream mapping
        if encoder_type != "cpu":
            # GPU encoders: conservative mapping
            params.extend(["-map", "0:v:0"])  # First video stream
            params.extend(["-map", "0:a?"])   # Audio streams if present
        else:
            # CPU encoder: copy all streams
            params.extend(["-c:s", "copy"])   # Copy subtitle streams
            params.extend(["-map", "0"])      # Copy all streams
        
        return params
    
    def _get_hevc_params(self, encoder_type: str, config: Dict, quality: Optional[int]) -> List[str]:
        """Get HEVC-specific encoding parameters."""
        params = []
        
        if encoder_type == "nvidia":
            params.extend(["-preset", config["preset"]])
            params.extend(["-rc", config["rc"]])
            params.extend(["-cq", str(quality if quality else config["cq"])])
            params.extend(["-b_ref_mode", config["b_ref_mode"]])
            params.extend(["-spatial_aq", str(config["spatial_aq"])])
            params.extend(["-temporal_aq", str(config["temporal_aq"])])
        elif encoder_type == "amd":
            params.extend(["-quality", config["quality"]])
            params.extend(["-rc", config["rc"]])
            qp_val = quality if quality else config["qp_i"]
            params.extend(["-qp_i", str(qp_val)])
            params.extend(["-qp_p", str(qp_val)])
            params.extend(["-qp_b", str(qp_val)])
        elif encoder_type == "intel":
            params.extend(["-preset", config["preset"]])
            params.extend(["-global_quality", str(quality if quality else config["global_quality"])])
            params.extend(["-look_ahead", str(config["look_ahead"])])
        else:  # CPU
            params.extend(["-preset", config["preset"]])
            params.extend(["-crf", str(quality if quality else config["crf"])])
            if "x265_params" in config:
                params.extend(["-x265-params", config["x265_params"]])
        
        return params
    
    def _get_h264_params(self, encoder_type: str, config: Dict, quality: Optional[int]) -> List[str]:
        """Get H.264-specific encoding parameters."""
        params = []
        
        if encoder_type == "nvidia":
            params.extend(["-preset", config["preset"]])
            params.extend(["-rc", config["rc"]])
            params.extend(["-cq", str(quality if quality else config["cq"])])
            params.extend(["-b_ref_mode", config["b_ref_mode"]])
            params.extend(["-spatial_aq", str(config["spatial_aq"])])
            params.extend(["-temporal_aq", str(config["temporal_aq"])])
        elif encoder_type == "amd":
            params.extend(["-quality", config["quality"]])
            params.extend(["-rc", config["rc"]])
            qp_val = quality if quality else config["qp_i"]
            params.extend(["-qp_i", str(qp_val)])
            params.extend(["-qp_p", str(qp_val)])
            params.extend(["-qp_b", str(qp_val)])
        elif encoder_type == "intel":
            params.extend(["-preset", config["preset"]])
            params.extend(["-global_quality", str(quality if quality else config["global_quality"])])
            params.extend(["-look_ahead", str(config["look_ahead"])])
        else:  # CPU
            params.extend(["-preset", config["preset"]])
            params.extend(["-crf", str(quality if quality else config["crf"])])
        
        return params
    
    def _get_av1_params(self, encoder_type: str, config: Dict, quality: Optional[int]) -> List[str]:
        """Get AV1-specific encoding parameters."""
        params = []
        
        if encoder_type == "nvidia":
            params.extend(["-preset", config["preset"]])
            params.extend(["-rc", config["rc"]])
            params.extend(["-cq", str(quality if quality else config["cq"])])
        elif encoder_type == "intel":
            params.extend(["-preset", config["preset"]])
            params.extend(["-global_quality", str(quality if quality else config["global_quality"])])
        else:  # CPU
            params.extend(["-crf", str(quality if quality else config["crf"])])
            params.extend(["-cpu-used", str(config["cpu-used"])])
        
        return params
    
    def _get_vp9_params(self, config: Dict, quality: Optional[int]) -> List[str]:
        """Get VP9-specific encoding parameters."""
        params = []
        params.extend(["-crf", str(quality if quality else config["crf"])])
        params.extend(["-b:v", config["b:v"]])
        params.extend(["-cpu-used", str(config["cpu-used"])])
        return params
    
    def _get_hdr_params(self, encoder_type: str, input_path: Optional[str]) -> List[str]:
        """Get HDR preservation parameters."""
        params = []
        
        if encoder_type != "cpu" and input_path:
            # Hardware encoders: use detected HDR parameters
            hdr_params = self._detect_hdr_params(input_path)
            
            # Special handling for NVENC
            if encoder_type == "nvidia" and hdr_params['color_trc'] == 'arib-std-b67':
                self.logger.warning("HLG content detected. Using HDR10 parameters for better compatibility.")
                hdr_params = {
                    'color_primaries': 'bt2020',
                    'color_trc': 'smpte2084',
                    'colorspace': 'bt2020nc',
                    'color_range': 'tv'
                }
            
            params.extend([
                "-color_primaries", hdr_params['color_primaries'],
                "-color_trc", hdr_params['color_trc'], 
                "-colorspace", hdr_params['colorspace'],
                "-color_range", hdr_params['color_range']
            ])
        else:
            # Software encoder: copy metadata
            params.extend([
                "-color_primaries", "copy",
                "-color_trc", "copy", 
                "-colorspace", "copy",
                "-color_range", "copy"
            ])
        
        # Additional metadata preservation
        params.extend(["-map_metadata", "0"])
        
        # Container-specific HDR flags for software encoders
        if encoder_type == "cpu":
            params.extend(["-movflags", "+write_colr"])
        
        return params 