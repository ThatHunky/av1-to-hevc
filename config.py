"""
Configuration module for AV1 to HEVC converter.
Handles encoding parameters, GPU detection, and quality settings.
"""

import subprocess
import logging
import json
from typing import Dict, List, Optional

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

# GPU encoder configurations
GPU_ENCODERS = {
    "nvidia": {
        "encoder": "hevc_nvenc",
        "preset": "p4",  # NVENC preset
        "rc": "vbr",     # Rate control
        "cq": 23,        # Constant quality
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
    }
}

# CPU fallback encoder
CPU_ENCODER = {
    "encoder": "libx265",
    "crf": DEFAULT_CRF,
    "preset": DEFAULT_PRESET,
    "x265_params": "hdr-opt=1:repeat-headers=1:colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc"
}


class Config:
    """Configuration class for video conversion settings."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gpu_type = self._detect_gpu()
        self.encoder_config = self._get_encoder_config()
        
    def _detect_gpu(self) -> Optional[str]:
        """Detect available GPU and return type (nvidia/amd/intel) or None."""
        try:
            # Check for NVIDIA GPU
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True, text=True, timeout=10
            )
            
            if "hevc_nvenc" in result.stdout:
                self.logger.info("NVIDIA GPU encoder detected")
                return "nvidia"
            elif "hevc_amf" in result.stdout:
                self.logger.info("AMD GPU encoder detected")
                return "amd"
            elif "hevc_qsv" in result.stdout:
                self.logger.info("Intel GPU encoder detected")
                return "intel"
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            self.logger.warning("Could not detect GPU encoders or FFmpeg not found")
            
        self.logger.info("Falling back to CPU encoder")
        return None
    
    def _get_encoder_config(self) -> Dict:
        """Get encoder configuration based on available hardware."""
        if self.gpu_type and self.gpu_type in GPU_ENCODERS:
            return GPU_ENCODERS[self.gpu_type].copy()
        return CPU_ENCODER.copy()
    
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
    
    def get_conversion_params(self, preserve_hdr: bool = True, 
                            quality: Optional[int] = None, 
                            input_path: Optional[str] = None) -> List[str]:
        """
        Get FFmpeg parameters for AV1 to HEVC conversion.
        
        Args:
            preserve_hdr: Whether to preserve HDR metadata
            quality: Override default quality setting
            input_path: Path to input file for HDR parameter detection
            
        Returns:
            List of FFmpeg parameters
        """
        params = []
        config = self.encoder_config.copy()
        
        # Set video codec
        params.extend(["-c:v", config["encoder"]])
        
        # Quality settings based on encoder type
        if self.gpu_type == "nvidia":
            params.extend(["-preset", config["preset"]])
            params.extend(["-rc", config["rc"]])
            if quality:
                params.extend(["-cq", str(quality)])
            else:
                params.extend(["-cq", str(config["cq"])])
            params.extend(["-b_ref_mode", config["b_ref_mode"]])
            params.extend(["-spatial_aq", str(config["spatial_aq"])])
            params.extend(["-temporal_aq", str(config["temporal_aq"])])
            
        elif self.gpu_type == "amd":
            params.extend(["-quality", config["quality"]])
            params.extend(["-rc", config["rc"]])
            qp_val = quality if quality else config["qp_i"]
            params.extend(["-qp_i", str(qp_val)])
            params.extend(["-qp_p", str(qp_val)])
            params.extend(["-qp_b", str(qp_val)])
            
        elif self.gpu_type == "intel":
            params.extend(["-preset", config["preset"]])
            gq_val = quality if quality else config["global_quality"]
            params.extend(["-global_quality", str(gq_val)])
            params.extend(["-look_ahead", str(config["look_ahead"])])
            
        else:  # CPU encoder
            params.extend(["-preset", config["preset"]])
            crf_val = quality if quality else config["crf"]
            params.extend(["-crf", str(crf_val)])
            params.extend(["-x265-params", config["x265_params"]])
        
        # HDR preservation
        if preserve_hdr:
            if self.gpu_type and input_path:
                # Hardware encoders don't support "copy" for color metadata
                # Detect and use actual HDR parameters from input
                hdr_params = self._detect_hdr_params(input_path)
                
                # Special handling for NVENC compatibility
                if self.gpu_type == "nvidia":
                    # NVENC has better support for HDR10 than HLG
                    if hdr_params['color_trc'] == 'arib-std-b67':
                        self.logger.warning("HLG content detected. NVENC has limited HLG support, using HDR10 parameters for better compatibility.")
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
                self.logger.info(f"Using HDR parameters for {self.gpu_type}: {hdr_params}")
            elif self.gpu_type:
                # Fallback HDR parameters for hardware encoders
                params.extend([
                    "-color_primaries", "bt2020",
                    "-color_trc", "smpte2084", 
                    "-colorspace", "bt2020nc",
                    "-color_range", "tv"
                ])
                self.logger.info("Using default HDR10 parameters for hardware encoder")
            else:
                # Software encoder can copy metadata
                params.extend([
                    "-color_primaries", "copy",
                    "-color_trc", "copy", 
                    "-colorspace", "copy",
                    "-color_range", "copy"
                ])
            
            # Additional HDR metadata preservation
            params.extend([
                "-map_metadata", "0"
            ])
            
            # Add container-specific HDR flags
            if not self.gpu_type:  # Only for software encoders
                params.extend(["-movflags", "+write_colr"])
        
        # Audio codec (copy without re-encoding)
        params.extend(["-c:a", "copy"])
        
        # For GPU encoders, be more conservative with stream mapping
        if self.gpu_type:
            # Only map video and audio streams for GPU encoders
            params.extend(["-map", "0:v:0"])  # First video stream
            params.extend(["-map", "0:a?"])   # Audio streams if present
        else:
            # CPU encoder can handle more complex mapping
            params.extend(["-c:s", "copy"])   # Copy subtitle streams
            params.extend(["-map", "0"])      # Copy all streams
        
        return params 