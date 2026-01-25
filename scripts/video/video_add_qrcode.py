import os
import re
import time
import shutil
import subprocess
import numpy as np
import qrcode

from dataclasses import dataclass
from multiprocessing import Manager
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw, ImageFont, ImageStat
from moviepy import VideoFileClip

from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    SpinnerColumn,
)
from rich.console import Console


INPUT_FOLDER = "/Users/tango/Desktop/AMC 视频/合并后"
OUTPUT_FOLDER = "/Users/tango/Desktop/AMC 视频/已添加二维码"

FONT_PATH = "/System/Library/Fonts/PingFang.ttc"
QR_DATA = "http://weixin.qq.com/r/mp/10z54bXEIuhdrfGC9xnF"
QR_TEXT = "更多真题资料\n关注公众号"

QR_WIDTH = 200
START_TIME = 5 * 60
INTERVAL = 10 * 60
DURATION = 60
CHECK_STEP = 5

BLANK_STD_THRESHOLD = 5
BLANK_MEAN_THRESHOLD = 200

MAX_WORKERS = 3
PER_VIDEO_TIMEOUT = 1800

@dataclass
class TaskProgress:
    video: str
    stage: str      # analyzing / rendering / done / error
    percent: float
    message: str
    elapsed: float

def create_progress():
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.fields[video]}"),
        BarColumn(bar_width=None),
        TextColumn("{task.percentage:>5.1f}%"),
        TextColumn("[yellow]{task.fields[stage]}"),
        TextColumn("[white]{task.fields[msg]}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=Console(force_terminal=True),
        transient=False,   # 不清屏
        refresh_per_second=5
    )


def create_qr_overlay(data, text, width, font_path):
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    qr_size = int(width * 0.9)
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

    font = ImageFont.truetype(font_path, int(width * 0.12))
    temp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bbox = temp.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    total_h = qr_size + 10 + text_h + 20
    img = Image.new("RGBA", (width, total_h), (255, 255, 255, 255))

    img.paste(qr_img, ((width - qr_size) // 2, 0))
    draw = ImageDraw.Draw(img)
    draw.text(((width - text_w) // 2, qr_size + 5), text, font=font, fill="black")
    return img

def check_region_blank_pil(frame_array, x, y, w, h):
    img = Image.fromarray(frame_array)
    roi = img.crop((x, y, x + w, y + h)).convert("L")
    stat = ImageStat.Stat(roi)
    return stat.stddev[0] < BLANK_STD_THRESHOLD and stat.mean[0] > BLANK_MEAN_THRESHOLD

def find_safe_position(clip, start_t, duration, w, h):
    frame_w, frame_h = clip.size
    margin = 20
    candidates = [
        (margin, margin),
        (frame_w - w - margin, margin),
        (margin, frame_h - h - margin),
        (frame_w - w - margin, frame_h - h - margin),
    ]

    times = np.linspace(start_t, start_t + duration, num=10)
    frames = []
    for t in times:
        if t >= clip.duration:
            return None
        frames.append(clip.get_frame(t))

    for x, y in candidates:
        if all(check_region_blank_pil(f, x, y, w, h) for f in frames):
            return (x, y)
    return None

def generate_ffmpeg_cmd(video, overlay, output, insertions):
    cur = "[0:v]"
    fc = ""
    for i, (s, d, x, y) in enumerate(insertions):
        out = f"[v{i}]" if i < len(insertions) - 1 else "[outv]"
        fc += f"{cur}[1:v]overlay=x={x}:y={y}:enable='between(t,{s},{s+d})'{out};"
        cur = out
    fc = fc.rstrip(";")

    return [
        "ffmpeg", "-y",
        "-i", video,
        "-i", overlay,
        "-filter_complex", fc,
        "-map", "[outv]",
        "-map", "0:a?",
        "-c:v", "libx264", "-crf", "26", "-preset", "veryfast",
        "-c:a", "copy",
        output
    ]

def run_ffmpeg(cmd, video, queue, start_ts):
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
    total = None

    for line in p.stderr:
        if "Duration:" in line:
            m = re.search(r'(\d+):(\d+):(\d+\.\d+)', line)
            if m:
                h, m_, s = m.groups()
                total = int(h)*3600 + int(m_)*60 + float(s)

        if "time=" in line and total:
            m = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
            if m:
                h, m_, s = m.groups()
                cur = int(h)*3600 + int(m_)*60 + float(s)
                queue.put(TaskProgress(
                    video, "rendering",
                    min(cur/total*100, 100),
                    "FFmpeg 编码",
                    time.time() - start_ts
                ))
    return p.wait()

def process_single_video(video_path, output_path, overlay_path, queue):
    name = os.path.basename(video_path)
    start = time.time()

    try:
        clip = VideoFileClip(video_path)
        ow, oh = Image.open(overlay_path).size
        t = START_TIME
        ins = []

        while t < clip.duration - DURATION:
            queue.put(TaskProgress(
                name, "analyzing",
                t / clip.duration * 100,
                f"扫描 {int(t)}s",
                time.time() - start
            ))
            pos = find_safe_position(clip, t, DURATION, ow, oh)
            t += INTERVAL if pos else CHECK_STEP
            if pos:
                ins.append((t, DURATION, pos[0], pos[1]))
                t += INTERVAL
            else:
                t += CHECK_STEP

        clip.close()

        if ins:
            cmd = generate_ffmpeg_cmd(video_path, overlay_path, output_path, ins)
            if run_ffmpeg(cmd, name, queue, start) != 0:
                raise RuntimeError("FFmpeg 失败")
        else:
            shutil.copy2(video_path, output_path)

        queue.put(TaskProgress(name, "done", 100, "完成", time.time() - start))

    except Exception as e:
        queue.put(TaskProgress(name, "error", 0, str(e), time.time() - start))

def process_folder(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    overlay = create_qr_overlay(QR_DATA, QR_TEXT, QR_WIDTH, FONT_PATH)
    overlay_path = "temp_overlay.png"
    overlay.save(overlay_path)

    files = [
        f for f in os.listdir(input_dir)
        if f.lower().endswith((".mp4", ".mov")) and not os.path.exists(os.path.join(output_dir, f))
    ]

    manager = Manager()
    queue = manager.Queue()

    with create_progress() as progress:
        total_task = progress.add_task(
            "[bold green]总进度",
            total=len(files),
            video="ALL",
            stage="",
            msg=""
        )

        task_map = {}
        for f in files:
            task_id = progress.add_task(
                f,
                total=100,
                video=f[:30],
                stage="等待",
                msg=""
            )
            task_map[f] = task_id

        with ProcessPoolExecutor(MAX_WORKERS) as pool:
            futures = [
                pool.submit(
                    process_single_video,
                    os.path.join(input_dir, f),
                    os.path.join(output_dir, f),
                    overlay_path,
                    queue
                )
                for f in files
            ]

            finished = 0
            while finished < len(files):
                msg = queue.get()

                task_id = task_map.get(msg.video)
                if task_id is None:
                    continue

                progress.update(
                    task_id,
                    completed=msg.percent,
                    stage=msg.stage,
                    msg=msg.message
                )

                if msg.stage in ("done", "error"):
                    finished += 1
                    progress.update(
                        total_task,
                        advance=1,
                        msg=f"{msg.video} 完成"
                    )

    os.remove(overlay_path)


if __name__ == "__main__":
    for name in ["AMC8专题", "AMC10", "AMC10专题", "AMC12"]:
        process_folder(
            f"{INPUT_FOLDER}/{name}",
            f"{OUTPUT_FOLDER}/{name}"
        )
