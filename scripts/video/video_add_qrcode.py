import os
import re
import subprocess

import numpy as np
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageStat
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip

# ================= 配置区域 =================
INPUT_FOLDER = "/Users/tango/Desktop/AMC 视频/合并后/AMC8/"  # 输入视频文件夹
OUTPUT_FOLDER = "/Users/tango/Desktop/AMC 视频/已添加二维码/AMC8"  # 输出视频文件夹
FONT_PATH = "/Library/Fonts/PingFang.ttc"  # Windows字体路径，Mac换成 /System/Library/Fonts/PingFang.ttc
QR_DATA = "http://weixin.qq.com/r/mp/10z54bXEIuhdrfGC9xnF"  # 二维码内容
QR_TEXT = "更多真题资料\n关注公众号"  # 二维码下方文字
QR_WIDTH = 200  # 二维码总宽度
START_TIME = 5 * 60  # 首次插入时间：5分钟
INTERVAL = 10 * 60  # 间隔时间：10分钟
DURATION = 60  # 显示持续时间：秒
CHECK_STEP = 5  # 没找到空白时，延后几秒重试
BLANK_STD_THRESHOLD = 5  # 标准差阈值：越小越“纯净”（空白）
BLANK_MEAN_THRESHOLD = 200  # 亮度阈值：大于此值认为是白色背景 (0-255)


# ===========================================

def run_ffmpeg_with_progress(cmd):
    """执行FFmpeg命令并显示进度条"""
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )

    total_duration = None

    # 实时读取stderr输出
    for line in process.stderr:
        line = line.strip()

        # 解析总时长
        if "Duration:" in line:
            duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
            if duration_match:
                h, m, s = duration_match.groups()
                total_duration = int(h) * 3600 + int(m) * 60 + float(s)

        # 解析当前处理时间
        if "time=" in line:
            time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
            if time_match:
                h, m, s = time_match.groups()
                current_time = int(h) * 3600 + int(m) * 60 + float(s)

                if total_duration:
                    progress = min(current_time / total_duration * 100, 100)
                    bar_length = 30
                    filled_length = int(bar_length * progress // 100)
                    bar = '█' * filled_length + '-' * (bar_length - filled_length)

                    print(f'\rProgress: |{bar}| {progress:.1f}% Complete', end='', flush=True)

    # 等待进程完成
    process.wait()
    return process

def create_qr_overlay(data, text, width, font_path):
    """
    生成透明背景的二维码图片素材 (PIL Image)
    """
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    qr_size = int(width * 0.9)
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

    try:
        font = ImageFont.truetype(font_path, int(width * 0.12))
    except:
        font = ImageFont.load_default()

    temp_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    text_bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    total_h = qr_size + 10 + text_h + 20

    # 创建带白色底的图片，防止视频背景干扰
    final_img = Image.new("RGBA", (width, total_h), (255, 255, 255, 255))

    qr_x = (width - qr_size) // 2
    final_img.paste(qr_img, (qr_x, 0))

    draw = ImageDraw.Draw(final_img)
    text_x = (width - text_w) // 2
    draw.text((text_x, qr_size + 5), text, font=font, fill="black")

    return final_img


def check_region_blank_pil(frame_array, x, y, w, h):
    """
    使用 PIL 判断区域是否为空白
    frame_array: moviepy 传来的 numpy 数组
    """
    # 1. 转换为 PIL 图片
    img = Image.fromarray(frame_array)

    # 2. 裁剪区域 (left, top, right, bottom)
    roi = img.crop((x, y, x + w, y + h))

    # 3. 转为灰度图以便分析
    gray_roi = roi.convert("L")

    # 4. 获取统计信息
    stat = ImageStat.Stat(gray_roi)
    mean_val = stat.mean[0]  # 平均亮度
    std_val = stat.stddev[0]  # 标准差（颜色杂乱程度）

    # 判断：亮度够高(白) 且 标准差够低(纯净)
    # 如果你的背景是黑色，改成 mean_val < 50
    return std_val < BLANK_STD_THRESHOLD and mean_val > BLANK_MEAN_THRESHOLD


def find_safe_position(clip, start_t, duration, w, h):
    """
    在 clip 中寻找 start_t 开始，持续 duration 秒都为空白的区域。
    返回 (x, y) 或 None
    """
    frame_w, frame_h = clip.size
    margin = 20

    # 定义四个角落候选区 (x, y)
    candidates = [
        (margin, margin),  # 左上
        (frame_w - w - margin, margin),  # 右上
        (margin, frame_h - h - margin),  # 左下
        (frame_w - w - margin, frame_h - h - margin)  # 右下
    ]

    # 我们需要在 duration 时间段内检查多个时间点
    # 例如显示5秒，我们在 0s, 1s, 2s, 3s, 4s, 5s 分别检查
    check_points = np.linspace(start_t, start_t + duration, num=10)

    # 优化：先一次性获取这些时间点的帧，避免重复读取 IO
    # 注意：如果内存不够，可以改回循环读取
    frames = []
    try:
        for t in check_points:
            # 防止超出视频时长
            if t >= clip.duration:
                return None
            frames.append(clip.get_frame(t))
    except Exception:
        return None

    # 遍历四个角落
    for x, y in candidates:
        is_safe = True
        # 遍历该角落在这几秒内的每一帧
        for frame in frames:
            if not check_region_blank_pil(frame, x, y, w, h):
                is_safe = False
                break

        if is_safe:
            return (x, y)  # 找到一个可用位置就直接返回

    return None


def generate_ffmpeg_cmd(video_path, overlay_image_path, output_path, insertions):
    if not insertions:
        return None
    filter_complex = ""
    current_stream = "[0:v]"
    for i, (start, dur, x, y) in enumerate(insertions):
        end = start + dur
        output_name = f"[v{i}]" if i < len(insertions) - 1 else "[outv]"
        filter_complex += (
            f"{current_stream}[1:v]overlay=x={x}:y={y}:"
            f"enable='between(t,{start},{end})'{output_name};"
        )
        current_stream = output_name
    filter_complex = filter_complex.rstrip(";")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", overlay_image_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?",

        # === 修改重点开始 ===
        "-c:v", "libx264",  # 视频编码器

        "-crf", "26",  # [关键] 质量系数：23是标准，26-28可以显著减小体积且肉眼画质损失小

        "-preset", "veryfast",  # [关键] 预设：去掉 ultrafast。
        # 可选：medium (最慢/体积最小), fast, veryfast (推荐平衡点)
        # === 修改重点结束 ===

        "-c:a", "copy",  # 音频直接复制，不占体积
        output_path
    ]
    return cmd


def process_videos():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # 1. 生成二维码图片
    overlay_pil = create_qr_overlay(QR_DATA, QR_TEXT, QR_WIDTH, FONT_PATH)
    overlay_w, overlay_h = overlay_pil.size
    overlay_path = "temp_qr_overlay.png"
    overlay_pil.save(overlay_path)

    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.avi'))]

    from moviepy import VideoFileClip  # 只需要这个来分析

    for filename in files:
        print(f"\n\n=== 正在分析: {filename} ===")
        video_path = os.path.join(INPUT_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, filename)

        insertions = []  # 记录所有插入点 (start, dur, x, y)

        try:
            # === 第一阶段：使用 MoviePy 分析空白位置 ===
            clip = VideoFileClip(video_path)
            duration = clip.duration
            current_t = START_TIME

            while current_t < duration - DURATION:
                print(f"  > 扫描时间点: {int(current_t)}s", end="\r")
                pos = find_safe_position(clip, current_t, DURATION, overlay_w, overlay_h)

                if pos:
                    print(f"  [√] 命中: {int(current_t)}s 坐标:{pos}          ")
                    insertions.append((current_t, DURATION, pos[0], pos[1]))
                    current_t += INTERVAL
                else:
                    current_t += CHECK_STEP

            clip.close()  # 分析完立刻关闭，释放资源

            # === 第二阶段：使用 FFmpeg 极速合成 ===
            if insertions:
                print(f"\n  > 开始 FFmpeg 渲染 (共 {len(insertions)} 处插入)...")
                cmd = generate_ffmpeg_cmd(video_path, overlay_path, output_path, insertions)

                # 执行命令
                result = run_ffmpeg_with_progress(cmd)

                if result.returncode == 0:
                    print(f"  [成功] 视频已保存: {output_path}")
                else:
                    print(f"  [失败] FFmpeg 报错:\n{result.stderr}")
            else:
                print("\n  [提示] 未找到合适插入点，跳过合成。")

        except Exception as e:
            print(f"\n  [异常] 处理 {filename} 时出错: {e}")
            import traceback
            traceback.print_exc()

    if os.path.exists(overlay_path):
        os.remove(overlay_path)


if __name__ == "__main__":
    process_videos()