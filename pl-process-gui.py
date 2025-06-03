import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import sys
from io import StringIO
import os

class RedirectText(object):
    """Class to redirect stdout to a text widget"""
    def __init__(self, text_widget, tag):
        self.text_widget = text_widget
        self.tag = tag
        
    def write(self, string):
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, string, (self.tag,))
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")
        
    def flush(self):
        pass

class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Playlist Downloader")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f0f0")
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("Header.TLabel", font=("Arial", 11, "bold"))
        self.style.configure("Progress.Horizontal.TProgressbar", thickness=20)
        
        # Create main frames
        self.create_frames()
        
        # Initialize variables
        self.api_key = tk.StringVar()
        self.playlist_url = tk.StringVar()
        self.video_quality = tk.StringVar(value="720")
        self.audio_format = tk.StringVar(value="mp3")
        self.filename_style = tk.StringVar(value="pretty")
        
        # Set up UI components
        self.setup_settings_frame()
        self.setup_progress_frame()
        self.setup_console_frame()
        self.setup_log_frame()
        
        # Redirect stdout
        sys.stdout = RedirectText(self.console_output, "console")
        sys.stderr = RedirectText(self.log_output, "error")
        
        # Download control
        self.download_thread = None
        self.stop_flag = False
        
    def create_frames(self):
        """Create main application frames"""
        # Settings frame
        self.settings_frame = ttk.LabelFrame(self.root, text="Settings", padding=10)
        self.settings_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Progress frame
        self.progress_frame = ttk.Frame(self.root, padding=10)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Console frame
        self.console_frame = ttk.LabelFrame(self.root, text="Console Output", padding=10)
        self.console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Log frame
        self.log_frame = ttk.LabelFrame(self.root, text="Download Logs", padding=10)
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
    def setup_settings_frame(self):
        """Configure settings frame components"""
        # API Key
        ttk.Label(self.settings_frame, text="YouTube API Key:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        api_entry = ttk.Entry(self.settings_frame, textvariable=self.api_key, width=50)
        api_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        
        # Playlist URL
        ttk.Label(self.settings_frame, text="Playlist URL:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        url_entry = ttk.Entry(self.settings_frame, textvariable=self.playlist_url, width=50)
        url_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        
        # Quality options
        ttk.Label(self.settings_frame, text="Video Quality:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        quality_combo = ttk.Combobox(self.settings_frame, textvariable=self.video_quality, 
                                    values=["144", "240", "360", "480", "720", "1080"], width=8)
        quality_combo.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        
        # Audio format
        ttk.Label(self.settings_frame, text="Audio Format:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        audio_combo = ttk.Combobox(self.settings_frame, textvariable=self.audio_format, 
                                  values=["mp3", "wav", "ogg"], width=8)
        audio_combo.grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)
        
        # Filename style
        ttk.Label(self.settings_frame, text="Filename Style:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        filename_combo = ttk.Combobox(self.settings_frame, textvariable=self.filename_style, 
                                     values=["pretty", "basic", "nerdy"], width=8)
        filename_combo.grid(row=4, column=1, padx=5, pady=2, sticky=tk.W)
        
        # Button frame
        button_frame = ttk.Frame(self.settings_frame)
        button_frame.grid(row=0, column=2, rowspan=5, padx=10, sticky=tk.NSEW)
        
        # Action buttons
        ttk.Button(button_frame, text="Start Download", command=self.start_download).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Stop Download", command=self.stop_download).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Console", command=self.clear_console).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Logs", command=self.save_logs).pack(side=tk.LEFT, padx=5)
        
    def setup_progress_frame(self):
        """Configure progress frame components"""
        # Overall progress label
        ttk.Label(self.progress_frame, text="Overall Progress:", style="Header.TLabel").pack(anchor=tk.W)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            orient=tk.HORIZONTAL, 
            length=500, 
            mode='determinate',
            style="Progress.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Progress labels
        progress_text_frame = ttk.Frame(self.progress_frame)
        progress_text_frame.pack(fill=tk.X)
        
        self.progress_status = ttk.Label(progress_text_frame, text="Ready")
        self.progress_status.pack(side=tk.LEFT)
        
        self.progress_percent = ttk.Label(progress_text_frame, text="0%")
        self.progress_percent.pack(side=tk.RIGHT)
        
    def setup_console_frame(self):
        """Configure console output frame"""
        self.console_output = scrolledtext.ScrolledText(
            self.console_frame, 
            wrap=tk.WORD, 
            height=10,
            state="disabled"
        )
        self.console_output.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for coloring
        self.console_output.tag_configure("console", foreground="black")
        self.console_output.tag_configure("success", foreground="green")
        self.console_output.tag_configure("error", foreground="red")
        self.console_output.tag_configure("warning", foreground="orange")
        self.console_output.tag_configure("highlight", foreground="blue")
        
    def setup_log_frame(self):
        """Configure log frame"""
        self.log_output = scrolledtext.ScrolledText(
            self.log_frame, 
            wrap=tk.WORD, 
            height=8,
            state="disabled"
        )
        self.log_output.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for coloring
        self.log_output.tag_configure("info", foreground="black")
        self.log_output.tag_configure("error", foreground="red")
        self.log_output.tag_configure("debug", foreground="gray")
        
    def start_download(self):
        """Start the download process in a separate thread"""
        if not self.api_key.get() or not self.playlist_url.get():
            messagebox.showerror("Input Error", "API Key and Playlist URL are required!")
            return
            
        if self.download_thread and self.download_thread.is_alive():
            messagebox.showwarning("Already Running", "Download is already in progress!")
            return
            
        self.stop_flag = False
        self.clear_console()
        print("Starting download process...")
        
        # Update progress UI
        self.progress_bar["value"] = 0
        self.progress_status.config(text="Preparing download...")
        self.progress_percent.config(text="0%")
        
        # Start download in separate thread
        self.download_thread = threading.Thread(target=self.run_download, daemon=True)
        self.download_thread.start()
        
    def run_download(self):
        """Main download process (to be run in thread)"""
        try:
            # Get playlist data
            print(f"Retrieving playlist data from: {self.playlist_url.get()}")
            video_data = get_playlist_videos_info(
                self.api_key.get(), 
                self.playlist_url.get()
            )
            
            # Process videos
            if not isinstance(video_data, dict) or 'videos' not in video_data:
                print("❌ Invalid playlist data received", "error")
                return
                
            videos = video_data['videos']
            total_videos = len(videos)
            print(f"Found {total_videos} videos in playlist")
            
            # Update progress bar maximum
            self.progress_bar["maximum"] = total_videos
            
            # Process each video
            for i, video in enumerate(videos):
                if self.stop_flag:
                    print("Download stopped by user")
                    return
                    
                # Update progress
                progress = (i + 1) / total_videos * 100
                self.progress_bar["value"] = i + 1
                self.progress_status.config(text=f"Downloading video {i+1} of {total_videos}")
                self.progress_percent.config(text=f"{progress:.1f}%")
                
                # Download video
                title = video.get('title', 'Untitled')
                url = video.get('url', '')
                
                if not title or not url:
                    print(f"Skipping invalid video entry")
                    continue
                    
                print(f"\nProcessing: {title}")
                fn_getVid(title, url)
                
            # Final update
            self.progress_status.config(text="Download completed!")
            print("\n✅ All videos downloaded successfully!")
            
        except Exception as e:
            print(f"❌ Download failed: {str(e)}", "error")
            self.log_output.insert(tk.END, f"ERROR: {str(e)}\n", "error")
            
    def stop_download(self):
        """Stop the current download process"""
        if self.download_thread and self.download_thread.is_alive():
            self.stop_flag = True
            print("Stopping download after current video...")
            self.progress_status.config(text="Stopping...")
        else:
            messagebox.showinfo("Info", "No active download to stop")
            
    def clear_console(self):
        """Clear the console output"""
        self.console_output.configure(state="normal")
        self.console_output.delete(1.0, tk.END)
        self.console_output.configure(state="disabled")
        
    def save_logs(self):
        """Save logs to a file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not file_path:
            return
            
        try:
            with open(file_path, "w") as f:
                # Save console output
                f.write("===== CONSOLE OUTPUT =====\n")
                f.write(self.console_output.get(1.0, tk.END))
                
                # Save log output
                f.write("\n\n===== ERROR LOGS =====\n")
                f.write(self.log_output.get(1.0, tk.END))
                
            print(f"Logs saved to: {file_path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save logs: {str(e)}")
            
    def on_closing(self):
        """Handle window closing event"""
        if self.download_thread and self.download_thread.is_alive():
            if messagebox.askyesno("Confirm", "Download is in progress. Are you sure you want to quit?"):
                self.stop_flag = True
                self.root.destroy()
        else:
            self.root.destroy()

# Replace with your actual functions
def get_playlist_videos_info(api_key, playlist_url):
    """Mock function - replace with your actual implementation"""
    return {
        'videos': [
            {'title': 'Video 1', 'url': 'https://youtube.com/video1'},
            {'title': 'Video 2', 'url': 'https://youtube.com/video2'},
            {'title': 'Video 3', 'url': 'https://youtube.com/video3'},
        ]
    }

def fn_getVid(title, url):
    """Mock function - replace with your actual implementation"""
    print(f"Downloading {title} from {url}")
    # Simulate download progress
    for i in range(5):
        print(f"Progress: {i*20}%")
    print(f"✅ Finished downloading {title}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()