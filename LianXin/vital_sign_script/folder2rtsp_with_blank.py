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

INSERT_VIDEO = "0_person.mp4"
OUTPUT_VIDEO = "output.mp4"


def collect_video_files(base_dir):
    files = []
    for name in os.listdir(base_dir):
        path = os.path.join(base_dir, name)
        if not os.path.isfile(path):
            continue

        if name in (OUTPUT_VIDEO, INSERT_VIDEO):
            continue

        ext = os.path.splitext(name)[1].lower()
        if ext in VIDEO_EXTS:
            files.append(name)

    return sorted(files)


def write_concat_list(base_dir, video_files):
    list_path = os.path.join(base_dir, "video_list.txt")

    insert_path = os.path.join(base_dir, INSERT_VIDEO)
    if not os.path.exists(insert_path):
        print(f"❌ 插播视频不存在: {INSERT_VIDEO}")
        sys.exit(1)

    with open(list_path, "w", encoding="utf-8") as f:
        for v in video_files:
            f.write(f"file '{v}'\n")
            f.write(f"file '{INSERT_VIDEO}'\n")

    return list_path


def concat_to_output(base_dir, list_path):
    print("▶ 正在拼接视频生成 output.mp4（一次性转码）")

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-fflags", "+genpts",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-r", "25",
        "-g", "50",
        "-keyint_min", "50",
        "-sc_threshold", "0",
        "-c:a", "aac",
        "-b:a", "128k",
        OUTPUT_VIDEO,
    ]

    subprocess.check_call(cmd, cwd=base_dir)
    print("✅ output.mp4 生成完成")


def start_rtsp_stream(base_dir):
    folder_name = os.path.basename(base_dir.rstrip(os.sep))
    rtsp_url = f"rtsp://10.1.10.206:8554/{folder_name}"

    cmd = (
        f"nohup ffmpeg -re -stream_loop -1 "
        f"-i {OUTPUT_VIDEO} "
        f"-c copy "
        f"-rtsp_transport tcp "
        f"-f rtsp {rtsp_url} "
        f"> /dev/null 2>&1 &"
    )

    subprocess.Popen(cmd, cwd=base_dir, shell=True)
    return rtsp_url


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, OUTPUT_VIDEO)

    if not os.path.exists(output_path):
        print("ℹ 未发现 output.mp4，开始拼接")

        videos = collect_video_files(base_dir)
        if not videos:
            print("❌ 当前目录没有可用视频文件")
            sys.exit(1)

        list_path = write_concat_list(base_dir, videos)
        concat_to_output(base_dir, list_path)
    else:
        print("✅ 已存在 output.mp4，直接推流")

    rtsp_url = start_rtsp_stream(base_dir)
    print(f"🚀 RTSP 推流已启动：{rtsp_url}")


if __name__ == "__main__":
    main()

