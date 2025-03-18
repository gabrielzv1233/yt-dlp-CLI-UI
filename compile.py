import subprocess
commands = [
    'pyinstaller --onefile --noconsole --name="yt-dlp UI" UI.py',
    'pyinstaller --onefile --name="yt-dlp CLI" CLI.py'
]
processes = [subprocess.Popen(cmd, shell=True) for cmd in commands]
for process in processes:
    process.wait()
