import os
import sys
import subprocess
import shutil


VIDEO_EXTS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".ts",
    ".flv",
    ".webm",
    ".m4v",
}


def collect_video_files(base_dir):
    files = []
    for name in os.listdir(base_dir):
        path = os.path.join(base_dir, name)
        if os.path.isfile(path):
            ext = os.path.splitext(name)[1].lower()
            if ext in VIDEO_EXTS:
                files.append(name)
    return sorted(files)


def safe_name(stem):
    # RTSP path should avoid spaces and special characters
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in stem)


def start_rtsp_for_file(base_dir, filename):
    stem = os.path.splitext(filename)[0]
    name = safe_name(stem)
    rtsp_url = f"rtsp://10.1.10.206:8554/{name}"

    cmd = (
        f"nohup ffmpeg -re -stream_loop -1 -i '{filename}' "
        f"-rtsp_transport tcp -vcodec copy -an -f rtsp {rtsp_url} "
        f"> /dev/null 2>&1 &"
    )

    subprocess.Popen(cmd, cwd=base_dir, shell=True)
    return rtsp_url


def main():
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found in PATH.")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    videos = collect_video_files(base_dir)
    if not videos:
        print("No video files found.")
        sys.exit(0)

    print("Starting RTSP streams in background...")
    for v in videos:
        url = start_rtsp_for_file(base_dir, v)
        print(f"RTSP: {url}")


if __name__ == "__main__":
    main()

