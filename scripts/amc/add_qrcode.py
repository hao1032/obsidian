import os
import qrcode
import random
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from io import BytesIO

# 配置
INPUT_DIR = r'/Volumes/share/share/paper/00-original/US-美国/AMC/'
OUTPUT_DIR = r'/Users/tango/Downloads/AMC/'
# QR_IMAGE_URL = r'https://mp.weixin.qq.com/mp/homepage?__biz=MzA3NzUxNDQ5Nw==&hid=5'  # BPhO 地址
QR_IMAGE_URL = r'https://mp.weixin.qq.com/mp/homepage?__biz=MzA3NzUxNDQ5Nw==&hid=3'  # AMC 地址
PAGE_INTERVAL = 3
QR_INSERT_SIZE = 60  # 插入到PDF页面时的宽高，pt单位，1pt=1/72英寸
MARGIN = 20
DPI = 300  # 二维码图像DPI，决定PDF插入尺寸

def get_qrcode_image(text):
    # 创建QRCode对象
    qr = qrcode.QRCode(
        version=1,  # 控制二维码大小的参数，范围1-40。值越小，二维码尺寸越小。
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # 容错级别
        box_size=1,  # 每个“盒子”的像素数
        border=1,  # 边框的盒子数（默认为4，是标准最小值）
    )

    # 向QRCode对象添加数据
    qr.add_data(text)

    # 生成二维码图像（默认为前/背景色）
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def load_qr_with_text(url, insert_size_pt, text="真题视频详解", max_font_size=40, dpi=300):
    qr_img = get_qrcode_image(url).convert("RGBA")
    target_px = int(insert_size_pt * dpi / 72)
    qr_img = qr_img.resize((target_px, target_px), resample=Image.NEAREST)

    font_path = "msyh.ttc"  # 你的字体路径
    font_path = os.path.join(os.path.dirname(__file__), "fonts", "Arial.ttf")
    font_path = "/Library/Fonts/PingFang.ttc"  # Linux/macOS
    font_size = max_font_size
    font = ImageFont.truetype(font_path, font_size)

    # 调整字体大小，确保文字宽度不超二维码宽度，留出5像素左右间距
    while True:
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        if text_width <= target_px - 10 or font_size <= 5:
            break
        font_size -= 1
        font = ImageFont.truetype(font_path, font_size)

    # 给文字预留足够空间，增加底部间距（例如5px）
    bottom_padding = 5
    canvas_height = target_px + text_height + bottom_padding

    canvas = Image.new("RGBA", (target_px, canvas_height), (255, 255, 255, 0))
    canvas.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(canvas)
    # 文字水平居中
    text_x = (target_px - text_width) // 2
    # 文字纵向位置，文字基线对齐，y坐标减去bbox[1]是关键（让文字底部对齐）
    text_y = target_px - bbox[1]

    draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0, 255))

    buf = BytesIO()
    canvas.save(buf, format="PNG")
    buf.seek(0)
    qr_doc = fitz.open("png", buf.read())
    pix = qr_doc[0].get_pixmap()
    return pix

def pixmap_to_rect(page, insert_size_pt, margin):
    rect = page.rect
    x1 = rect.x1 - margin
    y1 = rect.y1 - margin
    x0 = x1 - insert_size_pt
    y0 = y1 - insert_size_pt
    return fitz.Rect(x0, y0, x1, y1)

def find_best_blank_area_random_direction(page, qr_size, margin, threshold=245, white_ratio=1, step=10):
    zoom = 2
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    gray = img.convert("L")
    gray_np = np.array(gray)

    page_width, page_height = gray_np.shape[1], gray_np.shape[0]
    qr_w = int(qr_size * zoom)
    qr_h = int(qr_size * zoom)

    x = page_width - qr_w - margin

    # 随机决定方向
    search_from_bottom = random.choice([True, False])
    if search_from_bottom:
        y_range = range(page_height - qr_h - margin, margin - 1, -step)
    else:
        y_range = range(margin, page_height - qr_h - margin + 1, step)

    for y in y_range:
        area = gray_np[y:y+qr_h, x:x+qr_w]
        if area.shape != (qr_h, qr_w):
            continue
        white_pixels = np.sum(area >= threshold)
        ratio = white_pixels / (qr_w * qr_h)
        if ratio >= white_ratio:
            # 返回页面坐标
            scale = 1 / zoom
            x0 = x * scale
            y0 = y * scale
            x1 = x0 + qr_size
            y1 = y0 + qr_size
            return fitz.Rect(x0, y0, x1, y1)

    return None

def insert_qr_to_pdf(pdf_path, output_path, qr_pix, interval, margin):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    if total_pages <= interval:
        # 小文档：从最后一页往前插入
        print(f"[小文档模式] 页数 {total_pages}，从后向前每隔 {interval} 页尝试插入")
        page_indices = list(range(total_pages - 1, -1, -interval))
        for page_index in page_indices:
            page = doc[page_index]
            qr_rect = find_best_blank_area_random_direction(page, QR_INSERT_SIZE, MARGIN)
            if qr_rect:
                page.insert_image(qr_rect, pixmap=qr_pix)
                print(f"[插入] 第 {page_index+1} 页插入二维码")
            else:
                print(f"[跳过] 第 {page_index+1} 页未找到空白区域")
    else:
        # 大文档：从 interval 页开始每隔 interval 插入
        print(f"[大文档模式] 页数 {total_pages}，从第 {interval} 页开始，每隔 {interval} 页尝试插入")
        page_index = interval
        while page_index < total_pages:
            page = doc[page_index]
            qr_rect = find_best_blank_area_random_direction(page, QR_INSERT_SIZE, MARGIN)
            if qr_rect:
                page.insert_image(qr_rect, pixmap=qr_pix)
                print(f"[插入] 第 {page_index+1} 页插入二维码")
            else:
                print(f"[跳过] 第 {page_index+1} 页未找到空白区域")
            # strict_interval = True：不管是否插入成功都跳过 interval 页
            page_index += interval

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    doc.close()


def process_pdfs_recursively(input_dir, output_dir, qr_pix, interval, margin):
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".pdf"):
                input_path = os.path.join(root, file)
                rel_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, rel_path)
                print(f"处理: {input_path} → {output_path}")
                insert_qr_to_pdf(input_path, output_path, qr_pix, interval, margin)
                # if "solution" in file.lower():
                #     break
        # break

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    qr_pix = load_qr_with_text(QR_IMAGE_URL, QR_INSERT_SIZE)
    process_pdfs_recursively(INPUT_DIR, OUTPUT_DIR, qr_pix, PAGE_INTERVAL, MARGIN)
