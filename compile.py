import subprocess
commands = [
    'pyinstaller --onefile --noconsole --name="yt-dlp UI" UI.py && echo UI done compiling.',
    'pyinstaller --onefile --name="yt-dlp CLI" CLI.py && echo CLI done compiling.'
]
processes = [subprocess.Popen(cmd, shell=True) for cmd in commands]
for process in processes:
    process.wait()
