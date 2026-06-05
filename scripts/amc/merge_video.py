import os
import re
import subprocess
from collections import defaultdict


def ffmpeg_merge(video_list, output_path):
    temp_dir = "temp_standardized"
    os.makedirs(temp_dir, exist_ok=True)

    standardized_files = []
    list_txt_path = "inputs.txt"

    print("--- 第一步：标准化转码 ---")
    for i, video in enumerate(video_list):
        temp_output = os.path.join(temp_dir, f"std_{i}.mp4")

        # 统一参数：1080p, 30fps, H.264, AAC, YUV420P
        # 这些参数如果不统一，concat 极易失败
        cmd_std = [
            "ffmpeg", "-i", video,
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            # 统一分辨率且填充黑边
            "-r", "30",  # 统一帧率
            "-c:v", "libx264",  # 统一编码器
            "-pix_fmt", "yuv420p",  # 统一像素格式
            "-c:a", "aac",  # 统一音频编码
            "-ar", "44100",  # 统一音频采样率
            "-y", temp_output
        ]
        print(f"正在处理: {video}...")
        subprocess.run(cmd_std, check=True)
        standardized_files.append(temp_output)

    print("--- 第二步：生成合并列表 ---")
    with open(list_txt_path, "w", encoding="utf-8") as f:
        for file in standardized_files:
            # 获取绝对路径，避免路径报错
            abs_path = os.path.abspath(file).replace("\\", "/")
            f.write(f"file '{abs_path}'\n")

    print("--- 第三步：执行无损合并 ---")
    cmd_merge = [
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", list_txt_path,
        "-c", "copy",  # 因为已经标准化了，这里可以直接 copy，速度极快
        "-y", output_path
    ]
    subprocess.run(cmd_merge, check=True)

    print(f"合并完成！输出文件：{output_path}")


def merge_amc_videos(source_folder, output_folder):
    # 如果输出目录不存在，则创建
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 正则表达式解释：
    # Group 1: 提取年份和考试ID (例如: "2021 AMC 10B FALL" 或 "2023 AMC 10A")
    # 匹配逻辑：4位数字 + 空格 + AMC + 空格 + 10[AB] + 可选的(空格+FALL)
    # Group 2: 提取题目开始序号 (用于排序)
    # Group 3: 提取题目结束序号
    pattern = re.compile(r"^(\d{4}\s+AMC\s+12[AB](?:\s+FALL)?).*?(\d+)\s*-\s*(\d+)", re.IGNORECASE)

    # 用于分组存储文件信息的字典
    # key: 考试名称 (如 "2021 AMC 10B FALL")
    # value: list of tuples (开始序号, 完整文件名)
    grouped_files = defaultdict(list)

    print(f"正在扫描文件夹: {source_folder} ...")

    files = [f for f in os.listdir(source_folder) if f.endswith('.mp4')]

    for filename in files:
        match = pattern.search(filename)
        if match:
            exam_name = match.group(1).strip()
            start_num = int(match.group(2))
            end_num = int(match.group(3))
            # 将文件归类
            grouped_files[exam_name].append({
                "start": start_num,
                "end": end_num,
                "filename": filename
            })
        else:
            print(f"跳过不符合命名规则的文件: {filename}")

    print(f"\n找到 {len(grouped_files)} 组需要合并的考试视频。\n")

    # 开始处理每一组
    for exam_name, video_list in grouped_files.items():
        # 按照题目开始序号排序 (1-15, 16-20, 21-25)
        video_list.sort(key=lambda x: x["start"])
        if video_list[-1]["end"] != 25:
            print(f"{exam_name} 的题目数量不足 25，请检查文件命名是否正确。")
            continue

        output_filename = f"{exam_name}.mp4"
        output_path = os.path.join(output_folder, output_filename)

        print(f"正在处理: {exam_name} ->包含 {len(video_list)} 个片段")
        print(f'{exam_name}: {video_list}')

        video_list = [os.path.join(source_folder, video["filename"]) for video in video_list]
        ffmpeg_merge(video_list, output_path)

    print("\n所有任务完成！")


# ================= 配置区域 =================
# 请在这里修改你的文件夹路径
# "." 表示当前脚本所在的目录
# 如果你的视频在 "videos" 文件夹，请改为 source_dir = "videos"

source_dir = r"/Users/tango/Desktop/video/"  # 输入文件夹路径 (请修改这里)
output_dir = r"/Users/tango/Desktop/Merged/"  # 输出文件夹路径 (请修改这里)

def merge_videos():
    video_list = [
        '2025年AMC12A试题讲解--上.mp4',
        '2025年AMC12A试题讲解--下.mp4'
    ]
    video_list = [os.path.join(source_dir, video) for video in video_list]
    ffmpeg_merge(video_list, f'{output_dir}/2025 AMC 12A.mp4')

def merge_multi_videos():
    video_list = {
        '2019_F_01-30': [
            '袋鼠数学2019F(1-10).mp4',
            '袋鼠数学2019F(11-20).mp4',
            '袋鼠数学2019F(21-30).mp4'
        ],
    }

    for name, videos in video_list.items():
        video_list = [os.path.join(source_dir, video) for video in videos]
        ffmpeg_merge(video_list, f'{output_dir}/{name}.mp4')

if __name__ == "__main__":
    # 简单的路径检查
    # merge_amc_videos(source_dir, output_dir)

    # 合并文件夹中的单个视频
    # merge_videos()

    # 合并文件夹中的多个视频
    merge_multi_videos()