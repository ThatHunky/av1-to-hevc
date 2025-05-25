"""
Video converter module for AV1 to HEVC conversion.
Handles the actual conversion process with progress tracking.
"""

import subprocess
import logging
import re
import time
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

from config import Config
from utils import VideoUtils


@dataclass
class ConversionProgress:
    """Data class for tracking conversion progress."""
    frame: int = 0
    fps: float = 0.0
    bitrate: str = ""
    size: str = ""
    time: str = ""
    speed: str = ""
    percentage: float = 0.0


class VideoConverter:
    """Handles AV1 to HEVC video conversion with progress tracking."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the video converter.
        
        Args:
            config: Configuration object (creates default if None)
        """
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)
        self._current_process = None
        
    def convert_video(self, input_path: Path, output_path: Path,
                     quality: Optional[int] = None,
                     preserve_hdr: bool = True,
                     progress_callback: Optional[Callable[[ConversionProgress], None]] = None) -> bool:
        """
        Convert a single AV1 video to HEVC.
        
        Args:
            input_path: Path to input AV1 video
            output_path: Path for output HEVC video
            quality: Quality setting override
            preserve_hdr: Whether to preserve HDR metadata
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # Validate input file
            if not input_path.exists():
                self.logger.error(f"Input file not found: {input_path}")
                return False
            
            # Check if it's actually an AV1 video
            if not VideoUtils.is_av1_video(input_path):
                self.logger.warning(f"File is not AV1 encoded: {input_path}")
                return False
            
            # Get video info for duration calculation
            video_info = VideoUtils.get_video_info(input_path)
            duration = self._get_duration(video_info)
            
            # Log conversion start
            file_size = VideoUtils.get_file_size_mb(input_path)
            hdr_status = "with HDR" if (preserve_hdr and VideoUtils.has_hdr_metadata(input_path)) else "SDR"
            estimated_time = VideoUtils.estimate_conversion_time(
                file_size, self.config.gpu_type is not None
            )
            
            self.logger.info(f"Converting {input_path.name} ({file_size:.1f} MB) {hdr_status}")
            self.logger.info(f"Using {self.config.encoder_config['encoder']} encoder")
            self.logger.info(f"Estimated time: {estimated_time}")
            
            # Prepare FFmpeg command
            cmd = self._build_ffmpeg_command(input_path, output_path, quality, preserve_hdr)
            
            # Start conversion
            success = self._run_conversion(cmd, duration, progress_callback)
            
            # If conversion failed and we're using GPU with HDR, try fallback
            if not success and self.config.gpu_type and preserve_hdr:
                self.logger.warning("Conversion failed with HDR parameters, trying fallback without HDR...")
                
                # Clean up failed output file
                if output_path.exists():
                    try:
                        output_path.unlink()
                    except OSError:
                        pass
                
                # Retry without HDR preservation
                cmd_fallback = self._build_ffmpeg_command(input_path, output_path, quality, False)
                success = self._run_conversion(cmd_fallback, duration, progress_callback)
                
                if success:
                    self.logger.info("Conversion succeeded with fallback (no HDR preservation)")
                else:
                    self.logger.error("Conversion failed even with fallback")
            
            if success:
                output_size = VideoUtils.get_file_size_mb(output_path)
                compression_ratio = (file_size - output_size) / file_size * 100
                self.logger.info(f"Conversion completed: {output_path.name}")
                self.logger.info(f"Size: {file_size:.1f} MB → {output_size:.1f} MB "
                               f"({compression_ratio:+.1f}%)")
            else:
                self.logger.error(f"Conversion failed: {input_path.name}")
                # Clean up failed output file
                if output_path.exists():
                    try:
                        output_path.unlink()
                    except OSError:
                        pass
            
            return success
            
        except Exception as e:
            self.logger.error(f"Unexpected error converting {input_path}: {e}")
            return False
    
    def _build_ffmpeg_command(self, input_path: Path, output_path: Path,
                             quality: Optional[int], preserve_hdr: bool) -> list:
        """Build the FFmpeg command for conversion."""
        cmd = ['ffmpeg', '-y']  # -y to overwrite output files
        
        # Input file
        cmd.extend(['-i', str(input_path)])
        
        # Get conversion parameters from config
        params = self.config.get_conversion_params(preserve_hdr, quality, str(input_path))
        cmd.extend(params)
        
        # No special progress reporting, we'll parse stderr
        
        # Output file
        cmd.append(str(output_path))
        
        return cmd
    
    def _run_conversion(self, cmd: list, duration: Optional[float],
                       progress_callback: Optional[Callable[[ConversionProgress], None]]) -> bool:
        """
        Run the FFmpeg conversion process with progress tracking.
        
        Args:
            cmd: FFmpeg command list
            duration: Video duration in seconds
            progress_callback: Optional progress callback
            
        Returns:
            True if successful, False otherwise
        """
        process = None
        try:
            # Log the FFmpeg command for debugging
            cmd_str = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in cmd)
            self.logger.info(f"Running FFmpeg command: {cmd_str}")
            
            # Start FFmpeg process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=0
            )
            
            # Store process reference for cancellation
            self._current_process = process
            
            progress = ConversionProgress()
            start_time = time.time()
            last_output_time = start_time
            
            # Monitor progress with timeout handling
            while True:
                try:
                    # Check if process is still running
                    if process.poll() is not None:
                        break
                    
                    # Read output with timeout
                    import sys
                    
                    if sys.platform != 'win32':
                        # Unix-like systems: use select
                        import select
                        ready, _, _ = select.select([process.stderr], [], [], 1.0)
                        if ready:
                            output = process.stderr.readline()
                        else:
                            output = ''
                    else:
                        # Windows: use non-blocking read with threading
                        import threading
                        import queue as thread_queue
                        
                        def read_output(process, q):
                            try:
                                line = process.stderr.readline()
                                q.put(line)
                            except:
                                q.put('')
                        
                        q = thread_queue.Queue()
                        t = threading.Thread(target=read_output, args=(process, q))
                        t.daemon = True
                        t.start()
                        
                        try:
                            output = q.get(timeout=1.0)
                        except thread_queue.Empty:
                            output = ''
                    
                    current_time = time.time()
                    
                    if output:
                        last_output_time = current_time
                        line = output.strip()
                        if line:
                            self.logger.debug(f"FFmpeg stderr: {line}")
                            # Only parse lines that look like progress updates
                            if 'frame=' in line and 'time=' in line:
                                self._parse_progress(line, progress, duration)
                                
                                # Call progress callback if provided
                                if progress_callback:
                                    progress_callback(progress)
                                    
                                self.logger.info(f"Progress: {progress.percentage:.1f}% - Frame {progress.frame} - {progress.fps:.1f} fps")
                    
                    # Check for timeout (no output for 30 seconds)
                    if current_time - last_output_time > 30:
                        self.logger.warning("FFmpeg process seems to be hanging (no output for 30s)")
                        break
                    
                    # Small delay to prevent excessive CPU usage
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.logger.error(f"Error reading FFmpeg output: {e}")
                    break
            
            # Wait for process to complete with timeout
            try:
                return_code = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.logger.error("FFmpeg process did not exit gracefully, terminating")
                process.terminate()
                try:
                    return_code = process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    return_code = process.wait()
            
            # Read any remaining stderr output
            stderr_output = ""
            try:
                # Since we've been reading from stderr, there might not be much left
                remaining_output = process.stderr.read()
                if remaining_output:
                    stderr_output = remaining_output
            except:
                pass
            
            if return_code != 0:
                self.logger.error(f"FFmpeg failed with return code {return_code}")
                
                # Check for specific error patterns
                invalid_arg_error = False
                if stderr_output:
                    # Log error output and check for specific issues
                    error_lines = stderr_output.strip().split('\n')[-10:]  # Show more lines for debugging
                    for line in error_lines:
                        if line.strip():
                            self.logger.error(f"FFmpeg: {line}")
                            if "Invalid argument" in line or "error code: -22" in line:
                                invalid_arg_error = True
                
                if invalid_arg_error:
                    self.logger.error("Detected 'Invalid argument' error - likely HDR parameter incompatibility with GPU encoder")
                
                return False
            
            # Log final timing
            elapsed_time = time.time() - start_time
            self.logger.info(f"Conversion took {elapsed_time:.1f} seconds")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during conversion: {e}")
            return False
        finally:
            # Clean up process reference
            self._current_process = None
            if process:
                try:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                except:
                    pass
    
    def _parse_progress(self, line: str, progress: ConversionProgress, 
                       duration: Optional[float]) -> None:
        """Parse FFmpeg stderr output and update progress object."""
        try:
            # Look for progress lines that contain frame, fps, time, etc.
            # Format: frame= 1234 fps= 25 q=28.0 size=    1024kB time=00:00:49.36 bitrate= 170.1kbits/s speed=1.0x
            if 'frame=' in line and 'time=' in line:
                import re
                
                # Extract frame number
                frame_match = re.search(r'frame=\s*(\d+)', line)
                if frame_match:
                    progress.frame = int(frame_match.group(1))
                
                # Extract fps
                fps_match = re.search(r'fps=\s*([\d.]+)', line)
                if fps_match:
                    progress.fps = float(fps_match.group(1))
                
                # Extract bitrate
                bitrate_match = re.search(r'bitrate=\s*([\d.]+\w*bits/s)', line)
                if bitrate_match:
                    progress.bitrate = bitrate_match.group(1)
                
                # Extract size
                size_match = re.search(r'size=\s*([\d.]+\w*B)', line)
                if size_match:
                    progress.size = size_match.group(1)
                
                # Extract time and calculate percentage
                time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})', line)
                if time_match:
                    hours = int(time_match.group(1))
                    minutes = int(time_match.group(2))
                    seconds = int(time_match.group(3))
                    centiseconds = int(time_match.group(4))
                    
                    total_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
                    progress.time = self._format_time(total_seconds)
                    
                    # Calculate percentage if we have duration
                    if duration and duration > 0:
                        progress.percentage = min((total_seconds / duration) * 100, 100)
                
                # Extract speed
                speed_match = re.search(r'speed=\s*([\d.]+x)', line)
                if speed_match:
                    progress.speed = speed_match.group(1)
        
        except (ValueError, IndexError, AttributeError):
            # Ignore parsing errors
            pass
    
    def _get_duration(self, video_info: Optional[Dict]) -> Optional[float]:
        """Extract video duration from video info."""
        if not video_info:
            return None
        
        # Try to get duration from format
        format_info = video_info.get('format', {})
        duration_str = format_info.get('duration')
        
        if duration_str:
            try:
                return float(duration_str)
            except ValueError:
                pass
        
        # Try to get duration from video stream
        for stream in video_info.get('streams', []):
            if stream.get('codec_type') == 'video':
                duration_str = stream.get('duration')
                if duration_str:
                    try:
                        return float(duration_str)
                    except ValueError:
                        pass
        
        return None
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds as HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def cancel_conversion(self):
        """Cancel the currently running conversion."""
        if self._current_process:
            try:
                self.logger.info("Cancelling conversion...")
                self._current_process.terminate()
                try:
                    self._current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.logger.warning("Process did not terminate gracefully, killing...")
                    self._current_process.kill()
                    self._current_process.wait()
                return True
            except Exception as e:
                self.logger.error(f"Error cancelling conversion: {e}")
                return False
        return False


class BatchConverter:
    """Handles batch conversion of multiple videos."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the batch converter.
        
        Args:
            config: Configuration object (creates default if None)
        """
        self.converter = VideoConverter(config)
        self.logger = logging.getLogger(__name__)
        self._cancelled = False
    
    def convert_directory(self, input_dir: Path, output_dir: Optional[Path] = None,
                         quality: Optional[int] = None, preserve_hdr: bool = True,
                         progress_callback: Optional[Callable[[str, int, int, ConversionProgress], None]] = None) -> Dict[str, Any]:
        """
        Convert all AV1 videos in a directory to HEVC.
        
        Args:
            input_dir: Directory containing AV1 videos
            output_dir: Output directory (defaults to same as input)
            quality: Quality setting override
            preserve_hdr: Whether to preserve HDR metadata
            progress_callback: Optional callback for progress updates (filename, current, total, progress)
            
        Returns:
            Dictionary with conversion results
        """
        results = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'files': []
        }
        
        # Reset cancellation flag
        self._cancelled = False
        
        # Find all AV1 videos
        av1_videos = VideoUtils.find_av1_videos(input_dir)
        results['total'] = len(av1_videos)
        
        if not av1_videos:
            self.logger.info(f"No AV1 videos found in {input_dir}")
            return results
        
        self.logger.info(f"Found {len(av1_videos)} AV1 video(s) to convert")
        
        # Convert each video
        for i, input_path in enumerate(av1_videos, 1):
            # Check for cancellation
            if self._cancelled:
                self.logger.info("Batch conversion cancelled by user")
                break
                
            try:
                # Generate output path
                output_path = VideoUtils.generate_output_path(input_path, output_dir)
                
                # Skip if output already exists
                if output_path.exists():
                    self.logger.info(f"Skipping {input_path.name} - output exists")
                    results['skipped'] += 1
                    results['files'].append({
                        'input': str(input_path),
                        'output': str(output_path),
                        'status': 'skipped'
                    })
                    continue
                
                # Create progress callback for this file
                def file_progress_callback(progress: ConversionProgress):
                    if progress_callback:
                        progress_callback(input_path.name, i, len(av1_videos), progress)
                
                # Convert the video
                success = self.converter.convert_video(
                    input_path, output_path, quality, preserve_hdr, file_progress_callback
                )
                
                if success:
                    results['successful'] += 1
                    status = 'success'
                else:
                    results['failed'] += 1
                    status = 'failed'
                
                results['files'].append({
                    'input': str(input_path),
                    'output': str(output_path),
                    'status': status
                })
                
            except Exception as e:
                self.logger.error(f"Error processing {input_path}: {e}")
                results['failed'] += 1
                results['files'].append({
                    'input': str(input_path),
                    'output': str(output_path) if 'output_path' in locals() else 'unknown',
                    'status': 'error',
                    'error': str(e)
                })
        
        # Log summary
        self.logger.info(f"Batch conversion completed:")
        self.logger.info(f"  Total: {results['total']}")
        self.logger.info(f"  Successful: {results['successful']}")
        self.logger.info(f"  Failed: {results['failed']}")
        self.logger.info(f"  Skipped: {results['skipped']}")
        
        return results
    
    def cancel_conversion(self):
        """Cancel the batch conversion."""
        self._cancelled = True
        return self.converter.cancel_conversion() 