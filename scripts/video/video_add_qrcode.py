import os
import numpy as np
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageStat
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip

# ================= 配置区域 =================
INPUT_FOLDER = "/Users/tango/Desktop/video/"  # 输入视频文件夹
OUTPUT_FOLDER = "/Users/tango/Desktop/Merged/"  # 输出视频文件夹
FONT_PATH = "/Library/Fonts/PingFang.ttc"  # Windows字体路径，Mac换成 /System/Library/Fonts/PingFang.ttc
QR_DATA = "https://www.example.com"  # 二维码内容
QR_TEXT = "更多真题、关注公众号"  # 二维码下方文字
QR_WIDTH = 200  # 二维码总宽度
START_TIME = 5 * 60  # 首次插入时间：5分钟
INTERVAL = 10 * 60  # 间隔时间：10分钟
DURATION = 5  # 显示持续时间：5秒
CHECK_STEP = 5  # 没找到空白时，延后几秒重试
BLANK_STD_THRESHOLD = 15  # 标准差阈值：越小越“纯净”（空白）
BLANK_MEAN_THRESHOLD = 200  # 亮度阈值：大于此值认为是白色背景 (0-255)


# ===========================================

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
    check_points = np.linspace(start_t, start_t + duration, num=6)

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


def process_videos():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # 生成二维码素材
    overlay_pil = create_qr_overlay(QR_DATA, QR_TEXT, QR_WIDTH, FONT_PATH)
    overlay_w, overlay_h = overlay_pil.size
    overlay_path = "temp_qr_pil.png"
    overlay_pil.save(overlay_path)

    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.avi'))]

    for filename in files:
        print(f"处理中: {filename}")
        video_path = os.path.join(INPUT_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, filename)

        try:
            clip = VideoFileClip(video_path)

            # 收集所有的贴图层
            overlays = []

            current_t = START_TIME

            # 循环直到视频结束
            while current_t < clip.duration - DURATION:
                print(f"  > 正在检查时间点 {int(current_t)}s ...", end="\r")

                pos = find_safe_position(clip, current_t, DURATION, overlay_w, overlay_h)

                if pos:
                    print(f"\n    [√] 在 {int(current_t)}s 发现空白区域 {pos}，插入二维码")
                    # 创建贴图 Clip
                    qr_clip = (ImageClip(overlay_path)
                               .with_start(current_t)
                               .with_duration(DURATION)
                               .with_position(pos))
                    overlays.append(qr_clip)

                    # 成功插入后，跳过 10 分钟
                    current_t += INTERVAL
                else:
                    # 失败，延后 5 秒重试
                    current_t += CHECK_STEP

            print(f"\n  > 开始合成视频，共有 {len(overlays)} 个插入点...")

            # 合成视频
            if overlays:
                final = CompositeVideoClip([clip] + overlays)
            else:
                final = clip

            final.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="ultrafast", fps=clip.fps)

            final.close()
            clip.close()
            print(f"完成: {filename}\n" + "-" * 30)

        except Exception as e:
            print(f"错误: {e}")

    if os.path.exists(overlay_path):
        os.remove(overlay_path)


if __name__ == "__main__":
    process_videos()