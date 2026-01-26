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
        '2020_l1_01-24': [
            'p01 2020年袋鼠数学L1视频讲解1-10.mp4',
            'p02 2020年袋鼠数学L1视频讲解11-12-13.mp4',
            'p03 2020年袋鼠数学L1视频讲解14-15.mp4',
            'p04 2020年袋鼠数学L1视频讲解16-17.mp4',
            'p05 2020年袋鼠数学L1视频讲解18-19-20.mp4',
            'p06 2020年袋鼠数学L1视频讲解21-22-23-24.mp4',
        ],
        '2021_l1_01-24': [
            'p07 2021年袋鼠数学L1视频讲解1-4.mp4',
            'p08 2021年袋鼠数学L1视频讲解5-6-7.mp4',
            'p09 2021年袋鼠数学L1视频讲解8-9-10.mp4',
            'p10 2021年袋鼠数学L1视频讲解11-12.mp4',
            'p11 2021年袋鼠数学L1视频讲解13-14-15.mp4',
            'p12 2021年袋鼠数学L1视频讲解16-17-18.mp4',
            'p13 2021年袋鼠数学L1视频讲解19-20.mp4',
            'p14 2021年袋鼠数学L1视频讲解21-22.mp4',
            'p15 2021年袋鼠数学L1视频讲解23-24.mp4',
        ],
        '2020_l2_01-24': [
            'p16 2020年L2 1-6.mp4',
            'p17 2020年L2  7-8-9.mp4',
            'p18 2020年L2 11-12-13-14.mp4',
            'p19 2020年L2  15-16-17-18.mp4',
            'p20 2020年L2  19-20-21-22.mp4',
            'p21 2020年L2  23-24.mp4',
        ],
        # '2021_l2_01-17': [
        #     'p22 2021年L2  1-2-3-4-5.mp4'
        #     'p23 2021年L2  6-7.mp4'
        #     'p24 2021年L2   8.mp4'
        #     'p25 2021年L2  9-10.mp4'
        #     'p26 2021年L2  11-12-13.mp4'
        #     'p27 2021年L2  14-15.mp4'
        #     'p28 2021年L2  16-17.mp4'
        # ],
        # '2021_l3_01-06': [
        #     'p29 2021年L3-1.mp4',
        #     'p30 2021年L3-2和3.mp4',
        #     'p31 2021年L3-4-5-6.mp4',
        # ],
        # '2021_l4_01-12': [
        #     'p32 2021年袋鼠数学L4 1-4.mp4',
        #     'p33 2021年袋鼠数学L4 5-8.mp4',
        #     'p34 2021年袋鼠数学L4 9-12.mp4',
        # ],
        # '2020_l5_01-19': [
        #     'p35 2020年袋鼠数学L5   1-8.mp4',
        #     'p36 2020年袋鼠数学L5   9-12.mp4',
        #     'p37 2020年袋鼠数学L5  13-19.mp4',
        # ],
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