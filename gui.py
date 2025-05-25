#!/usr/bin/env python3
"""
GUI interface for Multi-Codec Video Converter

A modern tkinter-based graphical user interface for video codec conversion
with real-time progress tracking, batch processing, and system information.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import time
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from config import Config, SUPPORTED_CODECS
from converter import VideoConverter, BatchConverter, ConversionProgress
from utils import VideoUtils, setup_logging


class ToolTip:
    """Simple tooltip implementation for widgets."""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind('<Enter>', self.on_enter)
        self.widget.bind('<Leave>', self.on_leave)
    
    def on_enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.text, 
                        background="#ffffe0", relief="solid", borderwidth=1,
                        font=("Arial", 9))
        label.pack()
    
    def on_leave(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class ProgressWindow:
    """Dedicated window for showing conversion progress."""
    
    def __init__(self, parent, title="Converting Video"):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("600x400")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center the window
        self.window.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.cancelled = False
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the progress window UI."""
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Current file info
        self.file_label = ttk.Label(main_frame, text="Preparing conversion...", 
                                   font=("Arial", 12, "bold"))
        self.file_label.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Progress bars
        ttk.Label(main_frame, text="File Progress:").grid(row=1, column=0, sticky=tk.W)
        self.file_progress = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.file_progress.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        ttk.Label(main_frame, text="Batch Progress:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.batch_progress = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.batch_progress.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 0))
        
        # Stats frame
        stats_frame = ttk.LabelFrame(main_frame, text="Conversion Statistics", padding="10")
        stats_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        
        self.stats_text = tk.Text(stats_frame, height=8, width=60, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(stats_frame, orient="vertical", command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=scrollbar.set)
        
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.close_button = ttk.Button(button_frame, text="Close", command=self.close, state="disabled")
        self.close_button.pack(side=tk.LEFT)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(0, weight=1)
    
    def update_file_progress(self, filename: str, progress: ConversionProgress):
        """Update file conversion progress."""
        self.file_label.config(text=f"Converting: {filename}")
        self.file_progress['value'] = progress.percentage
        
        # Update stats
        stats = []
        if progress.fps > 0:
            stats.append(f"FPS: {progress.fps:.1f}")
        if progress.speed:
            stats.append(f"Speed: {progress.speed}")
        if progress.time:
            stats.append(f"Time: {progress.time}")
        if progress.bitrate:
            stats.append(f"Bitrate: {progress.bitrate}")
        
        if stats:
            stats_line = f"[{time.strftime('%H:%M:%S')}] " + " | ".join(stats) + "\n"
            self.stats_text.insert(tk.END, stats_line)
            self.stats_text.see(tk.END)
    
    def update_batch_progress(self, current: int, total: int):
        """Update batch progress."""
        if total > 0:
            percentage = (current / total) * 100
            self.batch_progress['value'] = percentage
            self.batch_progress.configure(maximum=100)
    
    def add_log(self, message: str):
        """Add a log message to the stats area."""
        log_line = f"[{time.strftime('%H:%M:%S')}] {message}\n"
        self.stats_text.insert(tk.END, log_line)
        self.stats_text.see(tk.END)
    
    def conversion_completed(self, success: bool, message: str = ""):
        """Mark conversion as completed."""
        self.cancel_button.config(state="disabled")
        self.close_button.config(state="normal")
        
        if success:
            self.file_label.config(text="✓ Conversion completed successfully!")
            self.add_log("Conversion completed successfully!")
        else:
            self.file_label.config(text="✗ Conversion failed!")
            self.add_log(f"Conversion failed: {message}")
        
        self.file_progress['value'] = 100 if success else 0
    
    def cancel(self):
        """Cancel the conversion."""
        self.cancelled = True
        self.cancel_button.config(state="disabled")
        self.add_log("Cancellation requested...")
    
    def close(self):
        """Close the progress window."""
        self.window.destroy()


class VideoConverterGUI:
    """Main GUI application for multi-codec video converter."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Codec Video Converter")
        self.root.geometry("850x650")
        self.root.minsize(750, 550)
        
        # Initialize converter components
        self.config = None
        self.converter = None
        self.batch_converter = None
        self.progress_window = None
        
        # Queue for thread communication
        self.message_queue = queue.Queue()
        
        # Setup logging to capture messages
        self.setup_logging()
        
        # Initialize components
        self.init_converter()
        
        # Setup UI
        self.setup_ui()
        self.setup_styles()
        
        # Start message processing
        self.process_messages()
        
        # Center window
        self.center_window()
    
    def setup_logging(self):
        """Setup logging to capture converter messages."""
        # Create a custom handler that sends messages to the queue
        class QueueHandler(logging.Handler):
            def __init__(self, queue):
                super().__init__()
                self.queue = queue
            
            def emit(self, record):
                self.queue.put(('log', self.format(record)))
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        queue_handler = QueueHandler(self.message_queue)
        queue_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        
        # Add to relevant loggers
        logging.getLogger('config').addHandler(queue_handler)
        logging.getLogger('converter').addHandler(queue_handler)
        logging.getLogger('utils').addHandler(queue_handler)
    
    def init_converter(self):
        """Initialize converter components."""
        try:
            self.config = Config()
            self.converter = VideoConverter(self.config)
            self.batch_converter = BatchConverter(self.config)
        except Exception as e:
            messagebox.showerror("Initialization Error", 
                               f"Failed to initialize converter: {e}")
    
    def setup_styles(self):
        """Setup modern styling for the interface."""
        style = ttk.Style()
        
        # Configure styles for better appearance
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green', font=('Arial', 10, 'bold'))
        style.configure('Error.TLabel', foreground='red', font=('Arial', 10, 'bold'))
        style.configure('Warning.TLabel', foreground='orange', font=('Arial', 10, 'bold'))
    
    def setup_ui(self):
        """Setup the main user interface."""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main conversion tab
        self.main_frame = ttk.Frame(notebook)
        notebook.add(self.main_frame, text="Convert Videos")
        self.setup_main_tab()
        
        # Settings tab
        self.settings_frame = ttk.Frame(notebook)
        notebook.add(self.settings_frame, text="Settings")
        self.setup_settings_tab()
        
        # System info tab
        self.info_frame = ttk.Frame(notebook)
        notebook.add(self.info_frame, text="System Info")
        self.setup_info_tab()
        
        # Status bar
        self.setup_status_bar()
    
    def setup_main_tab(self):
        """Setup the main conversion tab."""
        main_frame = ttk.Frame(self.main_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input selection
        input_frame = ttk.LabelFrame(main_frame, text="Input Selection", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Single file or directory choice
        self.conversion_mode = tk.StringVar(value="single")
        mode_frame = ttk.Frame(input_frame)
        mode_frame.pack(fill=tk.X)
        
        ttk.Radiobutton(mode_frame, text="Single File", variable=self.conversion_mode, 
                       value="single", command=self.on_mode_change).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Directory (Batch)", variable=self.conversion_mode, 
                       value="batch", command=self.on_mode_change).pack(side=tk.LEFT, padx=(20, 0))
        
        # Input codec filter (for batch mode)
        self.filter_frame = ttk.Frame(input_frame)
        self.filter_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(self.filter_frame, text="Filter by codec:").pack(side=tk.LEFT)
        self.input_codec_filter = tk.StringVar(value="all")
        codec_values = ["all"] + list(SUPPORTED_CODECS["input"].keys())
        codec_names = ["All codecs"] + [SUPPORTED_CODECS["input"][c]["name"] for c in codec_values[1:]]
        
        self.codec_filter_combo = ttk.Combobox(self.filter_frame, textvariable=self.input_codec_filter,
                                              values=codec_names, state="readonly", width=20)
        self.codec_filter_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.codec_filter_combo.current(0)
        
        # Initially hide filter frame
        self.filter_frame.pack_forget()
        
        # Input path
        input_path_frame = ttk.Frame(input_frame)
        input_path_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(input_path_frame, text="Input:").pack(side=tk.LEFT)
        self.input_path = tk.StringVar()
        self.input_entry = ttk.Entry(input_path_frame, textvariable=self.input_path, width=50)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        
        self.browse_input_btn = ttk.Button(input_path_frame, text="Browse...", 
                                          command=self.browse_input)
        self.browse_input_btn.pack(side=tk.RIGHT)
        
        # Output selection
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Codec selection
        codec_frame = ttk.Frame(output_frame)
        codec_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(codec_frame, text="Output codec:").pack(side=tk.LEFT)
        self.output_codec = tk.StringVar(value="hevc")
        output_codec_names = [SUPPORTED_CODECS["output"][c]["name"] for c in SUPPORTED_CODECS["output"]]
        output_codec_values = list(SUPPORTED_CODECS["output"].keys())
        
        self.codec_combo = ttk.Combobox(codec_frame, textvariable=self.output_codec,
                                       values=output_codec_names, state="readonly", width=20)
        self.codec_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.codec_combo.current(0)  # Default to HEVC
        
        # Bind codec selection change
        self.codec_combo.bind('<<ComboboxSelected>>', self.on_codec_change)
        
        # Output path
        output_path_frame = ttk.Frame(output_frame)
        output_path_frame.pack(fill=tk.X)
        
        ttk.Label(output_path_frame, text="Output:").pack(side=tk.LEFT)
        self.output_path = tk.StringVar()
        self.output_entry = ttk.Entry(output_path_frame, textvariable=self.output_path, width=50)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        
        self.browse_output_btn = ttk.Button(output_path_frame, text="Browse...", 
                                           command=self.browse_output)
        self.browse_output_btn.pack(side=tk.RIGHT)
        
        ttk.Label(output_frame, text="(Leave empty to use same directory as input)").pack(anchor=tk.W, pady=(5, 0))
        
        # Quality settings
        quality_frame = ttk.LabelFrame(main_frame, text="Quality Settings", padding="10")
        quality_frame.pack(fill=tk.X, pady=(0, 10))
        
        quality_slider_frame = ttk.Frame(quality_frame)
        quality_slider_frame.pack(fill=tk.X)
        
        ttk.Label(quality_slider_frame, text="Quality:").pack(side=tk.LEFT)
        self.quality_var = tk.IntVar(value=23)
        self.quality_slider = ttk.Scale(quality_slider_frame, from_=1, to=51, 
                                       variable=self.quality_var, orient=tk.HORIZONTAL,
                                       command=self.on_quality_change)
        self.quality_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        
        self.quality_label = ttk.Label(quality_slider_frame, text="23 (High Quality)")
        self.quality_label.pack(side=tk.RIGHT)
        
        # Quality description
        self.quality_desc = ttk.Label(quality_frame, 
                                     text="Lower values = better quality, larger files | Higher values = lower quality, smaller files")
        self.quality_desc.pack(anchor=tk.W, pady=(5, 0))
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Conversion Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.preserve_hdr = tk.BooleanVar(value=True)
        self.hdr_check = ttk.Checkbutton(options_frame, text="Preserve HDR metadata", 
                                        variable=self.preserve_hdr)
        self.hdr_check.pack(anchor=tk.W)
        ToolTip(self.hdr_check, "Preserve HDR10, HDR10+, and HLG metadata in the output file (HEVC/AV1 only)")
        
        self.overwrite_existing = tk.BooleanVar(value=False)
        overwrite_check = ttk.Checkbutton(options_frame, text="Overwrite existing files", 
                                         variable=self.overwrite_existing)
        overwrite_check.pack(anchor=tk.W)
        
        # Convert button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.convert_btn = ttk.Button(button_frame, text="Start Conversion", 
                                     command=self.start_conversion, style='Accent.TButton')
        self.convert_btn.pack(side=tk.LEFT)
        
        self.dry_run_btn = ttk.Button(button_frame, text="Dry Run (Preview)", 
                                     command=self.dry_run)
        self.dry_run_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # File info display
        self.info_frame_main = ttk.LabelFrame(main_frame, text="File Information", padding="10")
        self.info_frame_main.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.info_text = scrolledtext.ScrolledText(self.info_frame_main, height=8, 
                                                  font=("Consolas", 9))
        self.info_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_settings_tab(self):
        """Setup the settings tab."""
        settings_frame = ttk.Frame(self.settings_frame, padding="20")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Encoder settings
        encoder_frame = ttk.LabelFrame(settings_frame, text="Encoder Settings", padding="10")
        encoder_frame.pack(fill=tk.X, pady=(0, 10))
        
        if self.config:
            # Get current encoder info for default codec (HEVC)
            encoder_type, encoder_config = self.config.get_encoder_config('hevc')
            current_encoder = encoder_config.get('encoder', 'Unknown')
            gpu_type = encoder_type if encoder_type != 'cpu' else 'CPU'
            
            ttk.Label(encoder_frame, text=f"Current Encoder: {current_encoder}").pack(anchor=tk.W)
            ttk.Label(encoder_frame, text=f"Hardware Acceleration: {gpu_type.upper()}").pack(anchor=tk.W)
        
        # Quality presets
        presets_frame = ttk.LabelFrame(settings_frame, text="Quality Presets", padding="10")
        presets_frame.pack(fill=tk.X, pady=(0, 10))
        
        preset_buttons_frame = ttk.Frame(presets_frame)
        preset_buttons_frame.pack(fill=tk.X)
        
        presets = [
            ("Archive Quality", 18, "Best quality for long-term storage"),
            ("High Quality", 21, "Excellent quality for viewing"),
            ("Balanced", 23, "Good balance of quality and size"),
            ("Streaming", 26, "Optimized for streaming/sharing"),
            ("Small Size", 30, "Smaller files, lower quality")
        ]
        
        for i, (name, value, desc) in enumerate(presets):
            btn = ttk.Button(preset_buttons_frame, text=name, 
                           command=lambda v=value: self.set_quality_preset(v))
            btn.grid(row=0, column=i, padx=(0, 5), sticky=tk.W)
            ToolTip(btn, desc)
        
        # Advanced options
        advanced_frame = ttk.LabelFrame(settings_frame, text="Advanced Options", padding="10")
        advanced_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.verbose_logging = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Verbose logging", 
                       variable=self.verbose_logging).pack(anchor=tk.W)
        
        self.auto_detect_hdr = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Auto-detect HDR content", 
                       variable=self.auto_detect_hdr).pack(anchor=tk.W)
    
    def setup_info_tab(self):
        """Setup the system information tab."""
        info_frame = ttk.Frame(self.info_frame, padding="20")
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # System info
        system_frame = ttk.LabelFrame(info_frame, text="System Information", padding="10")
        system_frame.pack(fill=tk.X, pady=(0, 10))
        
        # FFmpeg status
        ffmpeg_available = VideoUtils.validate_ffmpeg()
        status_color = "Success.TLabel" if ffmpeg_available else "Error.TLabel"
        status_text = "Available ✓" if ffmpeg_available else "Not Found ✗"
        
        ttk.Label(system_frame, text="FFmpeg:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(system_frame, text=status_text, style=status_color).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # GPU acceleration
        if self.config:
            gpu_status = f"{self.config.gpu_type.upper()} ✓" if self.config.gpu_type else "Not Available"
            gpu_color = "Success.TLabel" if self.config.gpu_type else "Warning.TLabel"
            
            ttk.Label(system_frame, text="GPU Acceleration:").grid(row=1, column=0, sticky=tk.W)
            ttk.Label(system_frame, text=gpu_status, style=gpu_color).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Available encoders
        encoders_frame = ttk.LabelFrame(info_frame, text="Available Encoders", padding="10")
        encoders_frame.pack(fill=tk.X, pady=(0, 10))
        
        if self.config:
            row = 0
            for codec in SUPPORTED_CODECS['output']:
                codec_name = SUPPORTED_CODECS['output'][codec]['name']
                ttk.Label(encoders_frame, text=f"{codec_name}:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(5, 0))
                
                available = self.config.available_encoders.get(codec, [])
                if available:
                    encoder_type, encoder_config = self.config.get_encoder_config(codec)
                    encoder_name = encoder_config['encoder']
                    encoder_info = f"{encoder_name} ({encoder_type})"
                    ttk.Label(encoders_frame, text=encoder_info).grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
                else:
                    ttk.Label(encoders_frame, text="Not available", foreground="red").grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
                row += 1
        
        # Supported formats
        formats_frame = ttk.LabelFrame(info_frame, text="Supported Input Formats", padding="10")
        formats_frame.pack(fill=tk.X, pady=(0, 10))
        
        formats_text = ", ".join(sorted(VideoUtils.VIDEO_EXTENSIONS))
        ttk.Label(formats_frame, text=formats_text, wraplength=600).pack(anchor=tk.W)
        
        # Performance info
        perf_frame = ttk.LabelFrame(info_frame, text="Performance Information", padding="10")
        perf_frame.pack(fill=tk.X, pady=(0, 10))
        
        if self.config and self.config.gpu_type:
            perf_text = "Hardware acceleration is available. Expect 3-5x faster conversion speeds."
            perf_color = "Success.TLabel"
        else:
            perf_text = "Using CPU encoding. Consider updating GPU drivers for hardware acceleration."
            perf_color = "Warning.TLabel"
        
        ttk.Label(perf_frame, text=perf_text, style=perf_color, wraplength=600).pack(anchor=tk.W)
        
        # Refresh button
        ttk.Button(info_frame, text="Refresh System Info", 
                  command=self.refresh_system_info).pack(pady=(10, 0))
    
    def setup_status_bar(self):
        """Setup the status bar at the bottom."""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5), pady=(2, 2))
    
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_mode_change(self):
        """Handle conversion mode change."""
        mode = self.conversion_mode.get()
        if mode == "single":
            self.browse_input_btn.config(text="Browse File...")
            # Hide filter frame
            self.filter_frame.pack_forget()
        else:
            self.browse_input_btn.config(text="Browse Directory...")
            # Show filter frame
            self.filter_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Clear current paths
        self.input_path.set("")
        self.output_path.set("")
        self.update_file_info()
    
    def on_codec_change(self, event=None):
        """Handle output codec change."""
        # Get the selected codec name and find the corresponding key
        selected_name = self.codec_combo.get()
        for codec_key, codec_info in SUPPORTED_CODECS["output"].items():
            if codec_info["name"] == selected_name:
                self.output_codec.set(codec_key)
                break
        
        # Update HDR checkbox state based on codec support
        if self.output_codec.get() in ["hevc", "av1"]:
            self.hdr_check.config(state="normal")
        else:
            self.hdr_check.config(state="disabled")
            self.preserve_hdr.set(False)
        
        # Update quality range based on codec
        if self.output_codec.get() == "av1":
            self.quality_slider.configure(from_=1, to=63)
            self.quality_var.set(30)
        elif self.output_codec.get() == "vp9":
            self.quality_slider.configure(from_=1, to=63)
            self.quality_var.set(30)
        else:
            self.quality_slider.configure(from_=1, to=51)
            self.quality_var.set(23)
        
        self.on_quality_change(self.quality_var.get())
    
    def get_selected_input_codec(self) -> Optional[str]:
        """Get the selected input codec filter."""
        if self.input_codec_filter.get() == "all" or self.input_codec_filter.get() == "All codecs":
            return None
        
        # Find the codec key from the display name
        selected_name = self.codec_filter_combo.get()
        for codec_key, codec_info in SUPPORTED_CODECS["input"].items():
            if codec_info["name"] == selected_name:
                return codec_key
        return None
    
    def get_selected_output_codec(self) -> str:
        """Get the selected output codec."""
        # The output_codec variable already contains the key
        return self.output_codec.get()
    
    def on_quality_change(self, value):
        """Handle quality slider change."""
        quality = int(float(value))
        self.quality_var.set(quality)
        
        # Get codec-specific quality descriptions
        output_codec = self.output_codec.get()
        
        if output_codec in ["av1", "vp9"]:
            # AV1/VP9 use different quality scale
            if quality <= 20:
                desc = f"{quality} (Very High Quality)"
            elif quality <= 30:
                desc = f"{quality} (High Quality)"
            elif quality <= 40:
                desc = f"{quality} (Medium Quality)"
            elif quality <= 50:
                desc = f"{quality} (Lower Quality)"
            else:
                desc = f"{quality} (Very Low Quality)"
        else:
            # HEVC/H.264 quality scale
            if quality <= 18:
                desc = f"{quality} (Very High Quality)"
            elif quality <= 23:
                desc = f"{quality} (High Quality)"
            elif quality <= 28:
                desc = f"{quality} (Medium Quality)"
            elif quality <= 35:
                desc = f"{quality} (Lower Quality)"
            else:
                desc = f"{quality} (Very Low Quality)"
        
        self.quality_label.config(text=desc)
    
    def set_quality_preset(self, value):
        """Set quality to a preset value."""
        self.quality_var.set(value)
        self.quality_slider.set(value)
        self.on_quality_change(value)
    
    def browse_input(self):
        """Browse for input file or directory."""
        if self.conversion_mode.get() == "single":
            filename = filedialog.askopenfilename(
                title="Select Video File",
                filetypes=[
                    ("Video files", "*.mkv *.mp4 *.m4v *.mov *.avi *.webm"),
                    ("All files", "*.*")
                ]
            )
            if filename:
                self.input_path.set(filename)
        else:
            directory = filedialog.askdirectory(title="Select Directory with Videos")
            if directory:
                self.input_path.set(directory)
        
        self.update_file_info()
    
    def browse_output(self):
        """Browse for output directory."""
        if self.conversion_mode.get() == "single":
            filename = filedialog.asksaveasfilename(
                title="Save Video As",
                defaultextension=".mkv",
                filetypes=[
                    ("Matroska Video", "*.mkv"),
                    ("MP4 Video", "*.mp4"),
                    ("All files", "*.*")
                ]
            )
            if filename:
                self.output_path.set(filename)
        else:
            directory = filedialog.askdirectory(title="Select Output Directory")
            if directory:
                self.output_path.set(directory)
    
    def update_file_info(self):
        """Update the file information display."""
        self.info_text.delete(1.0, tk.END)
        
        input_path = self.input_path.get()
        if not input_path:
            self.info_text.insert(tk.END, "No input selected.\n")
            return
        
        path_obj = Path(input_path)
        
        if self.conversion_mode.get() == "single":
            if not path_obj.exists():
                self.info_text.insert(tk.END, "Selected file does not exist.\n")
                return
            
            if not path_obj.is_file():
                self.info_text.insert(tk.END, "Selected path is not a file.\n")
                return
            
            # Check if it's a video
            codec = VideoUtils.get_video_codec(path_obj)
            if codec:
                codec_name = VideoUtils.get_codec_display_name(codec)
                self.info_text.insert(tk.END, f"✓ Valid video file: {path_obj.name}\n")
                self.info_text.insert(tk.END, f"Codec: {codec_name}\n")
                
                # Get file info
                file_size = VideoUtils.get_file_size_mb(path_obj)
                has_hdr = VideoUtils.has_hdr_metadata(path_obj)
                
                self.info_text.insert(tk.END, f"File size: {file_size:.1f} MB\n")
                
                # Show HDR info only for codecs that support it
                if codec in ["hevc", "av1"]:
                    self.info_text.insert(tk.END, f"HDR metadata: {'Yes' if has_hdr else 'No'}\n")
                
                # Get detailed video info
                video_info = VideoUtils.get_video_info(path_obj)
                if video_info:
                    for stream in video_info.get('streams', []):
                        if stream.get('codec_type') == 'video':
                            width = stream.get('width', 'Unknown')
                            height = stream.get('height', 'Unknown')
                            self.info_text.insert(tk.END, f"Resolution: {width}x{height}\n")
                            
                            fps = stream.get('r_frame_rate', '').split('/')
                            if len(fps) == 2 and fps[1] != '0':
                                fps_val = float(fps[0]) / float(fps[1])
                                self.info_text.insert(tk.END, f"Frame rate: {fps_val:.2f} fps\n")
                            break
                
                # Estimate conversion time
                if self.config:
                    estimated_time = VideoUtils.estimate_conversion_time(
                        file_size, self.config.gpu_type is not None
                    )
                    self.info_text.insert(tk.END, f"Estimated conversion time: {estimated_time}\n")
            else:
                self.info_text.insert(tk.END, f"✗ Not a video file: {path_obj.name}\n")
                self.info_text.insert(tk.END, "Please select a valid video file.\n")
        
        else:  # Batch mode
            if not path_obj.exists():
                self.info_text.insert(tk.END, "Selected directory does not exist.\n")
                return
            
            if not path_obj.is_dir():
                self.info_text.insert(tk.END, "Selected path is not a directory.\n")
                return
            
            # Find video files
            video_files = VideoUtils.find_video_files(path_obj)
            
            if video_files:
                self.info_text.insert(tk.END, f"✓ Found {len(video_files)} video(s) in directory:\n\n")
                
                total_size = 0
                hdr_count = 0
                
                for video in video_files[:10]:  # Show first 10
                    file_size = VideoUtils.get_file_size_mb(video)
                    has_hdr = VideoUtils.has_hdr_metadata(video)
                    total_size += file_size
                    if has_hdr:
                        hdr_count += 1
                    
                    hdr_indicator = " [HDR]" if has_hdr else ""
                    self.info_text.insert(tk.END, f"  • {video.name} ({file_size:.1f} MB){hdr_indicator}\n")
                
                if len(video_files) > 10:
                    self.info_text.insert(tk.END, f"  ... and {len(video_files) - 10} more files\n")
                
                self.info_text.insert(tk.END, f"\nTotal size: {total_size:.1f} MB\n")
                self.info_text.insert(tk.END, f"Files with HDR: {hdr_count}\n")
                
                # Estimate total conversion time
                if self.config:
                    estimated_time = VideoUtils.estimate_conversion_time(
                        total_size, self.config.gpu_type is not None
                    )
                    self.info_text.insert(tk.END, f"Estimated total time: {estimated_time}\n")
            else:
                self.info_text.insert(tk.END, f"✗ No video files found in directory: {path_obj}\n")
                self.info_text.insert(tk.END, "The directory may be empty or contain no video files.\n")
    
    def dry_run(self):
        """Perform a dry run to show what would be converted."""
        if not self.validate_inputs():
            return
        
        input_path = Path(self.input_path.get())
        output_path = Path(self.output_path.get()) if self.output_path.get() else None
        output_codec = self.get_selected_output_codec()
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, "DRY RUN - Preview of conversion:\n\n")
        
        if self.conversion_mode.get() == "single":
            output_file = output_path or VideoUtils.generate_output_path(input_path, None, output_codec)
            
            # Ensure output file is a Path object with proper extension
            if not isinstance(output_file, Path):
                output_file = Path(output_file)
            
            # If it's a relative path or just a filename, make it relative to the input directory
            if not output_file.is_absolute():
                output_file = input_path.parent / output_file
            
            # Get proper extension for codec
            codec_extensions = {
                'hevc': '.mkv',
                'h264': '.mp4', 
                'av1': '.mkv',
                'vp9': '.webm'
            }
            
            if not output_file.suffix or output_file.suffix not in codec_extensions.values():
                output_file = output_file.with_suffix(codec_extensions.get(output_codec, '.mkv'))
                
            self.info_text.insert(tk.END, f"Input:  {input_path}\n")
            self.info_text.insert(tk.END, f"Output: {output_file}\n")
            
            # Show codec conversion
            input_codec = VideoUtils.get_video_codec(input_path)
            if input_codec:
                input_codec_name = VideoUtils.get_codec_display_name(input_codec)
                output_codec_name = VideoUtils.get_codec_display_name(output_codec)
                self.info_text.insert(tk.END, f"Codec:  {input_codec_name} → {output_codec_name}\n")
            
            file_size = VideoUtils.get_file_size_mb(input_path)
            has_hdr = VideoUtils.has_hdr_metadata(input_path)
            
            self.info_text.insert(tk.END, f"Size:   {file_size:.1f} MB\n")
            
            # Show HDR only if relevant
            if output_codec in ["hevc", "av1"] and has_hdr:
                self.info_text.insert(tk.END, f"HDR:    Yes (will be preserved)\n")
            elif has_hdr:
                self.info_text.insert(tk.END, f"HDR:    Yes (will be lost - {output_codec} doesn't support HDR)\n")
            
            self.info_text.insert(tk.END, f"Quality: {self.quality_var.get()}\n")
            
            if self.config:
                encoder_type, encoder_config = self.config.get_encoder_config(output_codec)
                self.info_text.insert(tk.END, f"Encoder: {encoder_config['encoder']} ({encoder_type})\n")
        
        else:  # Batch mode
            # Get filter codec if any
            input_codec_filter = self.get_selected_input_codec()
            video_files = VideoUtils.find_videos_by_codec(input_path, input_codec_filter)
            output_dir = output_path or input_path
            
            # Ensure output_dir is a Path object
            if not isinstance(output_dir, Path):
                output_dir = Path(output_dir)
            
            self.info_text.insert(tk.END, f"Input directory:  {input_path}\n")
            self.info_text.insert(tk.END, f"Output directory: {output_dir}\n")
            
            if input_codec_filter:
                filter_name = VideoUtils.get_codec_display_name(input_codec_filter)
                self.info_text.insert(tk.END, f"Input filter:     {filter_name} files only\n")
            
            output_codec_name = VideoUtils.get_codec_display_name(output_codec)
            self.info_text.insert(tk.END, f"Output codec:     {output_codec_name}\n")
            self.info_text.insert(tk.END, f"Files to convert: {len(video_files)}\n\n")
            
            for video in video_files[:10]:  # Show first 10
                input_codec = VideoUtils.get_video_codec(video)
                if input_codec == output_codec:
                    self.info_text.insert(tk.END, f"  [SKIP] {video.name} - already in {output_codec_name} format\n")
                else:
                    output_file = VideoUtils.generate_output_path(video, output_dir, output_codec)
                    file_size = VideoUtils.get_file_size_mb(video)
                    has_hdr = VideoUtils.has_hdr_metadata(video)
                    hdr_indicator = " [HDR]" if has_hdr else ""
                    
                    self.info_text.insert(tk.END, 
                        f"  {video.name} ({file_size:.1f} MB){hdr_indicator} → {output_file.name}\n")
            
            if len(video_files) > 10:
                self.info_text.insert(tk.END, f"  ... and {len(video_files) - 10} more files\n")
    
    def validate_inputs(self):
        """Validate user inputs before conversion."""
        if not self.input_path.get():
            messagebox.showerror("Input Error", "Please select an input file or directory.")
            return False
        
        input_path = Path(self.input_path.get())
        if not input_path.exists():
            messagebox.showerror("Input Error", "Selected input path does not exist.")
            return False
        
        if self.conversion_mode.get() == "single":
            if not VideoUtils.is_video_file(input_path):
                messagebox.showerror("Input Error", "Selected file is not a video.")
                return False
        else:
            video_files = VideoUtils.find_video_files(input_path)
            if not video_files:
                messagebox.showerror("Input Error", "No video files found in selected directory.")
                return False
        
        # Validate FFmpeg
        if not VideoUtils.validate_ffmpeg():
            messagebox.showerror("System Error", 
                               "FFmpeg not found. Please install FFmpeg and add it to PATH.")
            return False
        
        # Validate output path format (if specified)
        if self.output_path.get().strip():
            output_text = self.output_path.get().strip()
            if self.conversion_mode.get() == "single":
                # Check if it looks like a valid filename/path
                if output_text and not any(c in output_text for c in ['/', '\\', ':']):
                    # Just a filename, which is okay - we'll make it absolute later
                    pass
                elif output_text.count('.') > 1 and '/' not in output_text and '\\' not in output_text:
                    # Multiple dots but no path separators - might be malformed
                    result = messagebox.askyesno("Output Path", 
                        f"The output filename '{output_text}' looks unusual.\n\n"
                        "Would you like to continue anyway? The file will be saved with a .mkv extension.")
                    if not result:
                        return False
        
        return True
    
    def start_conversion(self):
        """Start the video conversion process."""
        if not self.validate_inputs():
            return
        
        # Disable convert button
        self.convert_btn.config(state="disabled")
        
        # Create and show progress window
        title = "Converting Video" if self.conversion_mode.get() == "single" else "Batch Converting Videos"
        self.progress_window = ProgressWindow(self.root, title)
        
        # Start conversion in separate thread
        conversion_thread = threading.Thread(target=self.run_conversion, daemon=True)
        conversion_thread.start()
    
    def run_conversion(self):
        """Run the actual conversion in a separate thread."""
        try:
            input_path = Path(self.input_path.get())
            output_path = Path(self.output_path.get()) if self.output_path.get() else None
            quality = self.quality_var.get()
            preserve_hdr = self.preserve_hdr.get()
            output_codec = self.get_selected_output_codec()
            
            if self.conversion_mode.get() == "single":
                # Single file conversion
                output_file = output_path or VideoUtils.generate_output_path(input_path, None, output_codec)
                
                # Ensure output file is a Path object with proper extension
                if not isinstance(output_file, Path):
                    output_file = Path(output_file)
                
                # If it's a relative path or just a filename, make it relative to the input directory
                if not output_file.is_absolute():
                    output_file = input_path.parent / output_file
                
                # Get proper extension for codec
                codec_extensions = {
                    'hevc': '.mkv',
                    'h264': '.mp4',
                    'av1': '.mkv',
                    'vp9': '.webm'
                }
                
                # Ensure the file has proper extension
                if not output_file.suffix or output_file.suffix not in codec_extensions.values():
                    output_file = output_file.with_suffix(codec_extensions.get(output_codec, '.mkv'))
                
                # Log the final output path for debugging
                self.message_queue.put(('log', f"Output file will be: {output_file}"))
                
                # Check if output exists and handle overwrite
                if output_file.exists() and not self.overwrite_existing.get():
                    self.message_queue.put(('error', f"Output file exists: {output_file}"))
                    return
                
                def progress_callback(progress: ConversionProgress):
                    if self.progress_window and self.progress_window.cancelled:
                        # Actually cancel the conversion
                        self.converter.cancel_conversion()
                        raise InterruptedError("Conversion cancelled by user")
                    self.message_queue.put(('file_progress', input_path.name, progress))
                
                self.message_queue.put(('log', f"Starting conversion of {input_path.name}"))
                success = self.converter.convert_video(
                    input_path, output_file, output_codec, quality, preserve_hdr, progress_callback
                )
                
                if success:
                    self.message_queue.put(('success', f"Conversion completed: {output_file.name}"))
                else:
                    self.message_queue.put(('error', "Conversion failed"))
            
            else:
                # Batch conversion
                output_dir = output_path or input_path
                
                # Ensure output_dir is a Path object
                if not isinstance(output_dir, Path):
                    output_dir = Path(output_dir)
                
                # Get input codec filter
                input_codec_filter = self.get_selected_input_codec()
                
                def batch_progress_callback(filename: str, current: int, total: int, progress: ConversionProgress):
                    if self.progress_window and self.progress_window.cancelled:
                        # Actually cancel the conversion
                        self.batch_converter.cancel_conversion()
                        raise InterruptedError("Conversion cancelled by user")
                    
                    self.message_queue.put(('batch_progress', current, total))
                    self.message_queue.put(('file_progress', filename, progress))
                
                self.message_queue.put(('log', f"Starting batch conversion in {input_path}"))
                results = self.batch_converter.convert_directory(
                    input_path, output_dir, input_codec_filter, output_codec, 
                    quality, preserve_hdr, batch_progress_callback
                )
                
                # Report results
                self.message_queue.put(('batch_complete', results))
        
        except InterruptedError:
            self.message_queue.put(('cancelled', "Conversion cancelled by user"))
        except Exception as e:
            self.message_queue.put(('error', f"Conversion error: {str(e)}"))
    
    def process_messages(self):
        """Process messages from the conversion thread."""
        try:
            while True:
                message = self.message_queue.get_nowait()
                msg_type = message[0]
                
                if msg_type == 'log':
                    self.status_label.config(text=message[1])
                    if self.progress_window:
                        self.progress_window.add_log(message[1])
                
                elif msg_type == 'file_progress':
                    if self.progress_window:
                        filename, progress = message[1], message[2]
                        self.progress_window.update_file_progress(filename, progress)
                
                elif msg_type == 'batch_progress':
                    if self.progress_window:
                        current, total = message[1], message[2]
                        self.progress_window.update_batch_progress(current, total)
                
                elif msg_type == 'success':
                    if self.progress_window:
                        self.progress_window.conversion_completed(True, message[1])
                    self.status_label.config(text=message[1])
                    self.convert_btn.config(state="normal")
                
                elif msg_type == 'error':
                    if self.progress_window:
                        self.progress_window.conversion_completed(False, message[1])
                    self.status_label.config(text=f"Error: {message[1]}")
                    self.convert_btn.config(state="normal")
                    messagebox.showerror("Conversion Error", message[1])
                
                elif msg_type == 'cancelled':
                    if self.progress_window:
                        self.progress_window.conversion_completed(False, message[1])
                    self.status_label.config(text=message[1])
                    self.convert_btn.config(state="normal")
                
                elif msg_type == 'batch_complete':
                    results = message[1]
                    success_msg = f"Batch conversion completed: {results['successful']} successful, {results['failed']} failed"
                    if self.progress_window:
                        self.progress_window.conversion_completed(results['failed'] == 0, success_msg)
                    self.status_label.config(text=success_msg)
                    self.convert_btn.config(state="normal")
        
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_messages)
    
    def refresh_system_info(self):
        """Refresh system information."""
        # Reinitialize converter to detect current system state
        self.init_converter()
        
        # Rebuild info tab
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        self.setup_info_tab()
        
        self.status_label.config(text="System information refreshed")
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for the GUI application."""
    # Check if FFmpeg is available
    if not VideoUtils.validate_ffmpeg():
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        result = messagebox.askyesno(
            "FFmpeg Not Found",
            "FFmpeg is required but not found in your system PATH.\n\n"
            "Would you like to continue anyway? (Some features may not work)",
            icon='warning'
        )
        
        if not result:
            return
    
    # Create and run the GUI
    app = VideoConverterGUI()
    app.run()


if __name__ == "__main__":
    main() 