import os
import re
import subprocess
from collections import defaultdict

def ffmpeg_merge(video_list, output_path):
    # 创建 ffmpeg 需要的临时列表文件 (file_list.txt)
    # 格式: file 'filename.mp4'
    source_folder = os.path.dirname(video_list[0])
    list_txt_path = os.path.join(source_folder, "temp_concat_list.txt")

    with open(list_txt_path, "w", encoding="utf-8") as f:
        for abs_path in video_list:
            # 使用绝对路径防止出错，并转义单引号
            # FFmpeg 列表文件格式要求路径被单引号包裹，且反斜杠需转义
            safe_path = abs_path.replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")

    # 构建 FFmpeg 命令
    # -f concat: 使用拼接模式
    # -safe 0: 允许使用绝对路径
    # -c copy: 直接复制流，不重新编码（速度快，无损）
    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", list_txt_path,
        "-c", "copy",
        "-y",  # 覆盖已存在文件
        output_path
    ]

    try:
        # 调用系统中的 ffmpeg，屏蔽详细日志只显示错误
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print(f"✅ 成功生成: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ 生成 {output_path} 失败。FFmpeg 错误信息:")
        print(e.stderr.decode())
    finally:
        # 删除临时列表文件
        if os.path.exists(list_txt_path):
            os.remove(list_txt_path)
        print("--------------------------------------------------\n")


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
output_dir = r"/Users/tango/Desktop/Merged"  # 输出文件夹路径 (请修改这里)

def merge_videos():
    video_list = [
        '2025年AMC12A试题讲解--上.mp4',
        '2025年AMC12A试题讲解--下.mp4'
    ]
    video_list = [os.path.join(source_dir, video) for video in video_list]
    ffmpeg_merge(video_list, f'{output_dir}/2025 AMC 12A.mp4')

if __name__ == "__main__":
    # 简单的路径检查
    # merge_amc_videos(source_dir, output_dir)

    # 合并文件夹中的单个视频
    merge_videos()