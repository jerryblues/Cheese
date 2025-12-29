import os
import sys
import subprocess


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


def write_video_list(base_dir, filenames):
    list_path = os.path.join(base_dir, "video_list.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for name in filenames:
            f.write(f"file '{name}'\n")
    return list_path


def start_rtsp_stream(base_dir, list_path):
    folder_name = os.path.basename(base_dir.rstrip(os.sep))
    rtsp_url = f"rtsp://10.1.10.206:8554/{folder_name}"

    cmd_str = (
        f"nohup ffmpeg -re -stream_loop -1 -f concat -safe 0 "
        f"-i {os.path.basename(list_path)} -c:v copy -c:a copy "
        f"-bufsize 500k -maxrate 1500k -rtsp_transport tcp -f rtsp {rtsp_url} "
        "> /dev/null 2>&1 &"
    )

    try:
        subprocess.Popen(cmd_str, cwd=base_dir, shell=True)
    except FileNotFoundError:
        print("ffmpeg not found. Install and add to PATH.")
        sys.exit(1)

    return rtsp_url


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    videos = collect_video_files(base_dir)
    if not videos:
        print("No video files found in current directory.")
        sys.exit(1)

    list_path = write_video_list(base_dir, videos)
    print(f"Video list written: {list_path}")

    rtsp_url = start_rtsp_stream(base_dir, list_path)
    print(f"RTSP started in background: {rtsp_url}")


if __name__ == "__main__":
    main()
