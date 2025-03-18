from tkinter import filedialog
import tkinter as tk
import tempfile
import yt_dlp
import shutil
import time
import sys
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
        if fmt['ext'] == 'mp4' and fmt.get('height') in [2160, 1440, 1080, 720, 144]:  # Video formats
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

    ydl_opts = {'format': format_id, 'outtmpl': temp_file, 'quiet': True, 'noplaylist': True, 'postprocessors': [{ 'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192',}] if is_audio else []}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return temp_file + (".mp3" if is_audio else "")

def save_file_dialog(default_filename, file_extension):
    root = tk.Tk()
    root.withdraw()

    root.attributes("-topmost", True)
    root.update()

    file_path = filedialog.asksaveasfilename( defaultextension=f".{file_extension}", filetypes=[(f"{file_extension.upper()} files", f"*.{file_extension}"), ("All Files", "*.*")], initialfile=default_filename, title="Save Downloaded File")

    root.destroy()
    return file_path

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

def main():
    while True:
        url = input("\nEnter YouTube URL or search query (or 'q' to quit): ").strip()
        if url.lower() == 'q':
            break

        if not is_valid_youtube_url(url):
            search_result_url = search_youtube(url)
            if not search_result_url:
                print("Failed to find a video. Try again.")
                continue
            print(f"Found video: {search_result_url}")
            url = search_result_url

        print("\nFetching available formats...")
        title, formats = get_available_formats(url)

        if not formats:
            print("No valid formats found!")
            continue

        print(f"\nAvailable formats for: {title}\n")
        for i, fmt in enumerate(formats):
            print(f"{i}: {fmt['resolution']} ({fmt['ext']})")

        try:
            choice = int(input("\nEnter the number of your choice: "))
            selected_format = formats[choice]
        except (ValueError, IndexError):
            print("Invalid choice! Try again.")
            continue

        print("\nDownloading...")
        is_audio = selected_format['resolution'] == 'Audio'
        temp_file_path = download_to_temp(url, selected_format['id'], is_audio)

        default_filename = f"{title}.{selected_format['ext']}"
        save_path = save_file_dialog(default_filename, selected_format['ext'])
        if not save_path:
            print("Save canceled. Skipping this download.")
            continue

        shutil.move(temp_file_path, save_path)

        update_file_metadata(save_path)

        print(f"\nDownload complete! File saved as: {save_path}")

        shutil.rmtree(os.path.dirname(temp_file_path), ignore_errors=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
