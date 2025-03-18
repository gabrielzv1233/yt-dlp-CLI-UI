from tkinter import ttk, filedialog
import tkinter as tk
import threading
import tempfile
import shutil
import yt_dlp
import time
import os
import re

def search_youtube(query):
    print(f"\nSearching YouTube for: {query}...")
    ydl_opts = {'quiet': True, 'default_search': 'ytsearch1', 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(query, download=False)
        if 'entries' in search_results and search_results['entries']:
            return search_results['entries'][0]['webpage_url']
    print("No search results found.")
    return None

def get_available_formats(url):
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
    unique_formats = {}
    for fmt in info['formats']:
        if fmt['ext'] == 'mp4' and fmt.get('height') in [2160, 1440, 1080, 720, 144]:
            res_key = f"{fmt.get('height')}p"
            if res_key not in unique_formats:
                unique_formats[res_key] = {
                    'id': fmt['format_id'],
                    'resolution': res_key,
                    'ext': 'mp4'
                }
        elif fmt.get('acodec') != 'none':
            abr = fmt.get('abr', 0) or 0
            if 'Audio' not in unique_formats or abr > unique_formats['Audio'].get('abr', 0):
                unique_formats['Audio'] = {'id': fmt['format_id'], 'resolution': 'Audio', 'ext': 'mp3', 'abr': abr}
    return info['title'], list(unique_formats.values())

def download_to_temp(url, format_id, is_audio):
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, 'downloaded_file')
    ydl_opts = {
        'format': format_id,
        'outtmpl': temp_file,
        'quiet': True,
        'noplaylist': True,
        'postprocessors': [{ 
            'key': 'FFmpegExtractAudio', 
            'preferredcodec': 'mp3', 
            'preferredquality': '192',
        }] if is_audio else []
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return temp_file + (".mp3" if is_audio else "")

def update_file_metadata(file_path):
    current_time = time.time()
    os.utime(file_path, (current_time, current_time))
    if os.name == 'nt':
        try:
            import ctypes
            file_time = int(current_time * 10000000) + 116444736000000000
            ctime = ctypes.c_ulonglong(file_time)
            handle = ctypes.windll.kernel32.CreateFileW(file_path, 256, 0, None, 3, 128, None)
            if handle != -1:
                ctypes.windll.kernel32.SetFileTime(handle, ctypes.byref(ctime), ctypes.byref(ctime), ctypes.byref(ctime))
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception as e:
            print(f"Failed to update creation time: {e}")

def is_valid_youtube_url(url):
    youtube_regex = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+"
    return re.match(youtube_regex, url) is not None

def save_file_dialog(default_filename, file_extension, default_folder=None):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    if default_folder is None:
        default_folder = os.path.join(os.path.expanduser("~"), "Downloads")

    file_path = filedialog.asksaveasfilename(
        defaultextension=f".{file_extension}",
        filetypes=[(f"{file_extension.upper()} files", f"*.{file_extension}"), ("All Files", "*.*")],
        initialfile=default_filename,
        initialdir=default_folder,
        title="Save Downloaded File"
    )

    root.destroy()
    return file_path

class YouTubeDownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader")
        self.geometry("600x400")
        self.loaded_url = None
        self.formats_data = []
        self.create_widgets()

    def create_widgets(self):
        self.query_label = tk.Label(self, text="Enter YouTube URL or search query:")
        self.query_label.pack(pady=5)

        self.query_entry = tk.Entry(self, width=80)
        self.query_entry.pack(pady=5)
        self.query_entry.bind("<KeyRelease>", self.on_query_change)
        self.query_entry.bind("<Return>", self.load_video_thread)

        self.load_button = tk.Button(self, text="Load Video", command=self.load_video_thread)
        self.load_button.pack(pady=5)

        self.title_label = tk.Label(self, text="Video Title:")
        self.title_label.pack(pady=5)
        self.video_title = tk.StringVar()
        self.video_title.set("Please load a video.")
        self.video_title_label = tk.Label(self, textvariable=self.video_title, wraplength=500)
        self.video_title_label.pack(pady=5)

        self.format_label = tk.Label(self, text="Select Format:")
        self.format_label.pack(pady=5)
        self.format_var = tk.StringVar()
        self.format_combobox = ttk.Combobox(self, textvariable=self.format_var, state="readonly", width=50)
        self.format_combobox.pack(pady=5)

        self.download_button = tk.Button(self, text="Download", command=self.download_thread, state="disabled")
        self.download_button.pack(pady=10)

        self.log_text = tk.Text(self, height=10, width=70, state="disabled")
        self.log_text.pack(pady=5)

    def on_query_change(self, event):
        self.loaded_url = None
        self.download_button.config(state="disabled")

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def load_video_thread(self, event=None):
        threading.Thread(target=self.load_video).start()

    def load_video(self):
        self.download_button.config(state="disabled")
        query = self.query_entry.get().strip()
        if not query:
            self.log("Please enter a query.")
            return
        self.log(f"Searching/loading video for: {query}")

        url = search_youtube(query) if not is_valid_youtube_url(query) else query
        if not url:
            self.log("Failed to find a video.")
            return

        self.loaded_url = url
        self.log(f"Video URL: {url}")

        title, formats = get_available_formats(url)
        self.video_title.set(title)
        self.formats_data = formats
        self.format_combobox['values'] = [f"{i}: {fmt['resolution']} ({fmt['ext']})" for i, fmt in enumerate(formats)]
        
        if formats:
            self.format_combobox.current(0)
            self.download_button.config(state="normal")
            self.format_combobox.event_generate('<Button-1>')
        else:
            self.log("No valid formats found.")

    def download_thread(self):
        threading.Thread(target=self.download_video).start()

    def download_video(self):
        if not self.loaded_url:
            self.log("No loaded video URL available. Please load video again.")
            return

        selection = self.format_combobox.get()
        index = int(selection.split(":")[0])
        selected_format = self.formats_data[index]

        self.log("Downloading...")
        temp_file_path = download_to_temp(self.loaded_url, selected_format['id'], selected_format['resolution'] == 'Audio')
        
        save_path = save_file_dialog(f"{self.video_title.get()}.{selected_format['ext']}", selected_format['ext'])
        if save_path:
            shutil.move(temp_file_path, save_path)
            update_file_metadata(save_path)
            self.log(f"Download complete! File saved as: {save_path}")

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
