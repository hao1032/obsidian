from yt_dlp import YoutubeDL

folder_url = {
    "amc8": "https://www.youtube.com/playlist?list=PLXrtlcyIn87rq6xH-4xGiXWM1XMovHlwn",
    'amc10': 'https://www.youtube.com/playlist?list=PLXrtlcyIn87qhdRi9DDQbLBt07-Q3yGya',
    'amc12': 'https://www.youtube.com/playlist?list=PLXrtlcyIn87oR07HIUchgOEY76hgv3CTA',
    'amc10topic': 'https://www.youtube.com/playlist?list=PLXrtlcyIn87qjTESOsKst8brB-c0BTh_4',
}

video_urls = [
    'https://www.bilibili.com/video/BV1GHCMBpEdZ/?spm_id_from=333.337.search-card.all.click&vd_source=c0537c5a5377f2ba272405e35c1565c5',
    'https://www.bilibili.com/video/BV16B2FBJEWn/?spm_id_from=333.337.search-card.all.click',
    'https://www.bilibili.com/video/BV1nB2FBnEv8/?spm_id_from=333.337.search-card.all.click'
]

ydl_opts = {
    "download_archive": "downloaded.txt",
    "format": "bestvideo+bestaudio/best",
    "merge_output_format": "mp4",
    "cookiesfrombrowser": ("chromium",),

    "windowsfilenames": True,
    "sleep_interval": 1,
    "max_sleep_interval": 5,
    "retries": 10,
    "fragment_retries": 10,
    "concurrent_fragment_downloads": 1,
    "ignoreerrors": True,
}

# 下载 folder_url 中的视频
for folder, playlist_url in folder_url.items():
    continue
    ydl_opts["outtmpl"] = f'/Users/tango/Desktop/{folder}/%(title)s.%(ext)s'
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([playlist_url])

# 下载 video_urls 中的视频
for video_url in video_urls:
    ydl_opts["outtmpl"] = f'/Users/tango/Desktop/video/%(title)s.%(ext)s'
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])