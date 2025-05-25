#!/usr/bin/env python3
"""
Multi-Codec Video Converter

A command-line tool to convert videos between different codecs with GPU acceleration,
HDR preservation, and batch processing capabilities.

Supported codecs:
- Input: AV1, HEVC/H.265, H.264/AVC, VP9, VP8, MPEG-2, MPEG-4
- Output: HEVC/H.265, H.264/AVC, AV1, VP9
"""

import sys
import time
from pathlib import Path
from typing import Optional

import click
from colorama import init, Fore, Style
from tqdm import tqdm

from config import Config, SUPPORTED_CODECS, CODEC_ENCODERS
from converter import VideoConverter, BatchConverter, ConversionProgress
from utils import VideoUtils, setup_logging

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class ProgressDisplay:
    """Handles progress display for conversions."""
    
    def __init__(self):
        self.current_pbar: Optional[tqdm] = None
        self.batch_pbar: Optional[tqdm] = None
        
    def setup_batch_progress(self, total_files: int):
        """Set up progress bar for batch conversion."""
        self.batch_pbar = tqdm(
            total=total_files,
            desc="Converting files",
            unit="file",
            position=0,
            colour='green'
        )
    
    def setup_file_progress(self, filename: str):
        """Set up progress bar for single file conversion."""
        if self.current_pbar:
            self.current_pbar.close()
        
        self.current_pbar = tqdm(
            total=100,
            desc=f"Converting {filename}",
            unit="%",
            position=1 if self.batch_pbar else 0,
            colour='blue',
            leave=False
        )
    
    def update_file_progress(self, progress: ConversionProgress):
        """Update file conversion progress."""
        if self.current_pbar:
            # Update progress bar
            current_progress = int(progress.percentage)
            self.current_pbar.n = current_progress
            
            # Update description with detailed info
            desc_parts = [f"Converting"]
            if progress.fps > 0:
                desc_parts.append(f"{progress.fps:.1f} fps")
            if progress.speed:
                desc_parts.append(f"{progress.speed}")
            if progress.time:
                desc_parts.append(f"[{progress.time}]")
            
            self.current_pbar.set_description(" | ".join(desc_parts))
            self.current_pbar.refresh()
    
    def finish_file(self):
        """Finish current file progress."""
        if self.current_pbar:
            self.current_pbar.n = 100
            self.current_pbar.refresh()
            self.current_pbar.close()
            self.current_pbar = None
            
        if self.batch_pbar:
            self.batch_pbar.update(1)
    
    def finish_batch(self):
        """Finish batch progress."""
        if self.batch_pbar:
            self.batch_pbar.close()
            self.batch_pbar = None


# Custom click type for codec selection
class CodecChoice(click.Choice):
    """Custom choice type that maps codec names to keys."""
    
    def __init__(self, codec_type='output'):
        self.codec_type = codec_type
        codecs = SUPPORTED_CODECS[codec_type]
        self.name_to_key = {v['name'].lower(): k for k, v in codecs.items()}
        self.name_to_key.update({k: k for k in codecs.keys()})  # Also accept keys directly
        super().__init__(list(self.name_to_key.keys()))
    
    def convert(self, value, param, ctx):
        value = super().convert(value.lower(), param, ctx)
        return self.name_to_key[value]


@click.group(invoke_without_command=True)
@click.option('--directory', '-d', type=click.Path(exists=True, path_type=Path),
              help='Directory containing videos to convert')
@click.option('--input-codec', '-i', type=CodecChoice('input'),
              help='Filter input videos by codec (for batch mode)')
@click.option('--output-codec', '-c', type=CodecChoice('output'), default='hevc',
              help='Output codec (default: hevc)')
@click.option('--output', '-o', type=click.Path(path_type=Path),
              help='Output directory (defaults to same as input)')
@click.option('--quality', '-q', type=click.IntRange(1, 63), default=23,
              help='Quality setting (lower=better, default=23)')
@click.option('--no-hdr', is_flag=True,
              help='Disable HDR metadata preservation')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
@click.option('--dry-run', is_flag=True,
              help='Show what would be converted without actually converting')
@click.pass_context
def cli(ctx, directory, input_codec, output_codec, output, quality, no_hdr, verbose, dry_run):
    """
    Convert videos between different codecs with GPU acceleration and HDR preservation.
    
    This tool automatically detects available GPU encoders (NVIDIA NVENC, AMD AMF, Intel QSV)
    and falls back to CPU encoding if no GPU is available.
    
    Examples:
    \b
      # Convert a single file from AV1 to HEVC
      video-converter convert input.mkv -c hevc
    \b  
      # Convert all VP9 videos in a directory to H.264
      video-converter batch /path/to/videos -i vp9 -c h264
    \b
      # Convert with custom quality
      video-converter convert input.mp4 -c hevc -q 20
    """
    # Set up logging
    setup_logging(verbose)
    
    # If no subcommand and directory provided, run batch conversion
    if ctx.invoked_subcommand is None:
        if directory:
            ctx.invoke(batch, 
                      directory=directory,
                      input_codec=input_codec,
                      output_codec=output_codec,
                      output=output, 
                      quality=quality, 
                      no_hdr=no_hdr,
                      dry_run=dry_run)
        else:
            click.echo(ctx.get_help())
            sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option('--output-codec', '-c', type=CodecChoice('output'), default='hevc',
              help='Output codec (default: hevc)')
@click.option('--output', '-o', type=click.Path(path_type=Path),
              help='Output file path')
@click.option('--quality', '-q', type=click.IntRange(1, 63), default=23,
              help='Quality setting (lower=better, default=23)')
@click.option('--no-hdr', is_flag=True,
              help='Disable HDR metadata preservation')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
def convert(input_file, output_codec, output, quality, no_hdr, verbose):
    """Convert a single video file to a different codec."""
    setup_logging(verbose)
    
    # Validate FFmpeg
    if not VideoUtils.validate_ffmpeg():
        click.echo(f"{Fore.RED}Error: FFmpeg not found. Please install FFmpeg and add it to PATH.")
        sys.exit(1)
    
    # Check input codec
    input_codec = VideoUtils.get_video_codec(input_file)
    if not input_codec:
        click.echo(f"{Fore.RED}Error: Could not detect codec for {input_file.name}")
        sys.exit(1)
    
    # Check if conversion makes sense
    if input_codec == output_codec:
        click.echo(f"{Fore.YELLOW}Warning: Input and output codecs are the same ({input_codec})")
        if not click.confirm("Continue with re-encoding?"):
            sys.exit(0)
    
    # Generate output path if not provided
    if output is None:
        output = VideoUtils.generate_output_path(input_file, None, output_codec)
    
    # Check if output already exists
    if output.exists():
        if not click.confirm(f"Output file {output} already exists. Overwrite?"):
            click.echo("Conversion cancelled.")
            sys.exit(1)
    
    # Initialize converter and progress display
    config = Config()
    converter = VideoConverter(config)
    progress_display = ProgressDisplay()
    
    # Display conversion info
    file_size = VideoUtils.get_file_size_mb(input_file)
    has_hdr = VideoUtils.has_hdr_metadata(input_file)
    estimated_time = VideoUtils.estimate_conversion_time(file_size, config.gpu_type is not None)
    
    input_codec_name = VideoUtils.get_codec_display_name(input_codec)
    output_codec_name = VideoUtils.get_codec_display_name(output_codec)
    encoder_type, encoder_config = config.get_encoder_config(output_codec)
    
    click.echo(f"\n{Fore.CYAN}Converting: {Fore.WHITE}{input_file.name}")
    click.echo(f"{Fore.CYAN}Codec: {Fore.WHITE}{input_codec_name} → {output_codec_name}")
    click.echo(f"{Fore.CYAN}Size: {Fore.WHITE}{file_size:.1f} MB")
    
    if output_codec in ['hevc', 'av1']:
        click.echo(f"{Fore.CYAN}HDR: {Fore.WHITE}{'Yes' if has_hdr else 'No'}")
    
    click.echo(f"{Fore.CYAN}Encoder: {Fore.WHITE}{encoder_config['encoder']} ({encoder_type})")
    click.echo(f"{Fore.CYAN}Quality: {Fore.WHITE}{quality}")
    click.echo(f"{Fore.CYAN}Estimated time: {Fore.WHITE}{estimated_time}")
    click.echo()
    
    # Set up progress display
    progress_display.setup_file_progress(input_file.name)
    
    def progress_callback(progress: ConversionProgress):
        progress_display.update_file_progress(progress)
    
    # Start conversion
    success = converter.convert_video(
        input_file, output, output_codec, quality, not no_hdr, progress_callback
    )
    
    progress_display.finish_file()
    
    if success:
        output_size = VideoUtils.get_file_size_mb(output)
        compression_ratio = (file_size - output_size) / file_size * 100
        click.echo(f"\n{Fore.GREEN}✓ Conversion completed!")
        click.echo(f"{Fore.CYAN}Output: {Fore.WHITE}{output}")
        click.echo(f"{Fore.CYAN}Size change: {Fore.WHITE}{file_size:.1f} MB → {output_size:.1f} MB ({compression_ratio:+.1f}%)")
    else:
        click.echo(f"\n{Fore.RED}✗ Conversion failed!")
        sys.exit(1)


@cli.command()
@click.argument('directory', type=click.Path(exists=True, path_type=Path))
@click.option('--input-codec', '-i', type=CodecChoice('input'),
              help='Filter input videos by codec')
@click.option('--output-codec', '-c', type=CodecChoice('output'), default='hevc',
              help='Output codec (default: hevc)')
@click.option('--output', '-o', type=click.Path(path_type=Path),
              help='Output directory (defaults to same as input)')
@click.option('--quality', '-q', type=click.IntRange(1, 63), default=23,
              help='Quality setting (lower=better, default=23)')
@click.option('--no-hdr', is_flag=True,
              help='Disable HDR metadata preservation')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
@click.option('--dry-run', is_flag=True,
              help='Show what would be converted without actually converting')
def batch(directory, input_codec, output_codec, output, quality, no_hdr, verbose, dry_run):
    """Convert all videos in a directory to a different codec."""
    setup_logging(verbose)
    
    # Validate FFmpeg
    if not VideoUtils.validate_ffmpeg():
        click.echo(f"{Fore.RED}Error: FFmpeg not found. Please install FFmpeg and add it to PATH.")
        sys.exit(1)
    
    # Find videos
    videos = VideoUtils.find_videos_by_codec(directory, input_codec)
    
    if not videos:
        if input_codec:
            codec_name = VideoUtils.get_codec_display_name(input_codec)
            click.echo(f"{Fore.YELLOW}No {codec_name} videos found in {directory}")
        else:
            click.echo(f"{Fore.YELLOW}No videos found in {directory}")
        return
    
    # Filter out videos already in target codec
    videos_to_convert = []
    for video in videos:
        video_codec = VideoUtils.get_video_codec(video)
        if video_codec != output_codec:
            videos_to_convert.append(video)
    
    if not videos_to_convert:
        click.echo(f"{Fore.YELLOW}All videos are already in {output_codec.upper()} format")
        return
    
    # Display summary
    total_size = sum(VideoUtils.get_file_size_mb(f) for f in videos_to_convert)
    hdr_count = sum(1 for f in videos_to_convert if VideoUtils.has_hdr_metadata(f))
    
    output_codec_name = VideoUtils.get_codec_display_name(output_codec)
    
    click.echo(f"\n{Fore.CYAN}Found {Fore.WHITE}{len(videos_to_convert)} {Fore.CYAN}video(s) to convert")
    click.echo(f"{Fore.CYAN}Target codec: {Fore.WHITE}{output_codec_name}")
    click.echo(f"{Fore.CYAN}Total size: {Fore.WHITE}{total_size:.1f} MB")
    
    if output_codec in ['hevc', 'av1']:
        click.echo(f"{Fore.CYAN}HDR videos: {Fore.WHITE}{hdr_count}")
    
    if dry_run:
        click.echo(f"\n{Fore.YELLOW}Dry run - files that would be converted:")
        for video in videos_to_convert:
            video_codec = VideoUtils.get_video_codec(video)
            output_path = VideoUtils.generate_output_path(video, output, output_codec)
            size_mb = VideoUtils.get_file_size_mb(video)
            hdr_indicator = " [HDR]" if VideoUtils.has_hdr_metadata(video) else ""
            codec_info = f"[{VideoUtils.get_codec_display_name(video_codec)}]"
            click.echo(f"  {video.name} {codec_info} ({size_mb:.1f} MB){hdr_indicator} → {output_path.name}")
        return
    
    # Ask for confirmation
    if not click.confirm(f"\nProceed with batch conversion?"):
        click.echo("Conversion cancelled.")
        return
    
    # Initialize converter and progress display
    config = Config()
    batch_converter = BatchConverter(config)
    progress_display = ProgressDisplay()
    
    # Display encoder info
    encoder_type, encoder_config = config.get_encoder_config(output_codec)
    click.echo(f"\n{Fore.CYAN}Using encoder: {Fore.WHITE}{encoder_config['encoder']}")
    if encoder_type != 'cpu':
        click.echo(f"{Fore.CYAN}GPU acceleration: {Fore.GREEN}Enabled ({encoder_type})")
    else:
        click.echo(f"{Fore.CYAN}GPU acceleration: {Fore.YELLOW}Not available")
    click.echo()
    
    # Set up progress display
    progress_display.setup_batch_progress(len(videos_to_convert))
    
    def batch_progress_callback(filename: str, current: int, total: int, progress: ConversionProgress):
        if not progress_display.current_pbar or progress_display.current_pbar.desc != f"Converting {filename}":
            progress_display.setup_file_progress(filename)
        progress_display.update_file_progress(progress)
    
    # Start batch conversion
    start_time = time.time()
    results = batch_converter.convert_directory(
        directory, output, input_codec, output_codec, quality, not no_hdr, batch_progress_callback
    )
    
    # Clean up progress display
    progress_display.finish_file()
    progress_display.finish_batch()
    
    # Display results
    elapsed_time = time.time() - start_time
    click.echo(f"\n{Fore.CYAN}Batch conversion completed in {elapsed_time:.1f} seconds")
    click.echo(f"{Fore.GREEN}✓ Successful: {results['successful']}")
    if results['failed'] > 0:
        click.echo(f"{Fore.RED}✗ Failed: {results['failed']}")
    if results['skipped'] > 0:
        click.echo(f"{Fore.YELLOW}⊘ Skipped: {results['skipped']}")
    
    # Show failed conversions
    if results['failed'] > 0:
        click.echo(f"\n{Fore.RED}Failed conversions:")
        for file_info in results['files']:
            if file_info['status'] in ['failed', 'error']:
                click.echo(f"  {Path(file_info['input']).name}")


@cli.command()
def info():
    """Show system information and available encoders."""
    setup_logging(False)
    
    # Check FFmpeg
    ffmpeg_available = VideoUtils.validate_ffmpeg()
    click.echo(f"{Fore.CYAN}FFmpeg: {Fore.GREEN if ffmpeg_available else Fore.RED}{'Available' if ffmpeg_available else 'Not found'}")
    
    if not ffmpeg_available:
        click.echo(f"{Fore.RED}Please install FFmpeg and add it to PATH.")
        return
    
    # Initialize config to detect GPU
    config = Config()
    
    click.echo(f"\n{Fore.CYAN}Available Encoders:")
    for output_codec in SUPPORTED_CODECS['output']:
        codec_name = SUPPORTED_CODECS['output'][output_codec]['name']
        click.echo(f"\n  {Fore.WHITE}{codec_name}:")
        
        available_encoders = config.available_encoders.get(output_codec, [])
        for encoder_type in available_encoders:
            if encoder_type in config.available_encoders.get(output_codec, []):
                encoder_config = CODEC_ENCODERS[output_codec][encoder_type]
                click.echo(f"    {Fore.GREEN}✓ {encoder_config['encoder']} ({encoder_type})")
    
    click.echo(f"\n{Fore.CYAN}Supported input codecs:")
    for codec_key, codec_info in SUPPORTED_CODECS['input'].items():
        click.echo(f"  • {codec_info['name']}")
    
    click.echo(f"\n{Fore.CYAN}Supported output codecs:")
    for codec_key, codec_info in SUPPORTED_CODECS['output'].items():
        click.echo(f"  • {codec_info['name']}")


@cli.command()
def gui():
    """Launch the graphical user interface."""
    try:
        from gui import main as gui_main
        click.echo(f"{Fore.CYAN}Launching GUI...")
        gui_main()
    except ImportError as e:
        click.echo(f"{Fore.RED}Error: Could not launch GUI. Missing dependencies: {e}")
        click.echo(f"{Fore.YELLOW}Try installing additional dependencies with: pip install pillow")
    except Exception as e:
        click.echo(f"{Fore.RED}Error launching GUI: {e}")


if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo(f"\n{Fore.YELLOW}Conversion interrupted by user.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n{Fore.RED}Unexpected error: {e}")
        sys.exit(1) 