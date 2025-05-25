#!/usr/bin/env python3
"""
GUI Launcher for AV1 to HEVC Video Converter

Direct launcher for the graphical user interface.
"""

if __name__ == "__main__":
    try:
        from gui import main
        main()
    except ImportError as e:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        
        messagebox.showerror(
            "Missing Dependencies",
            f"Could not launch GUI. Missing dependencies:\n{e}\n\n"
            "Please install required packages:\n"
            "pip install pillow"
        )
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        
        messagebox.showerror(
            "Error",
            f"Failed to launch GUI:\n{e}"
        ) 