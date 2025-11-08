import ssl
import json
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PCS_URL = 'https://pcs.baidu.com/rest/2.0/pcs'
PCS_APP_ID = "778750"

class Pan(object):
    def __init__(self, cookie_string):
        self.cookie_string = cookie_string

    def __send(self, url, params):
        query_string = urlencode(params)
        url = f'{url}?{query_string}'

        req = Request(url, headers={
            "Cookie": self.cookie_string,
            "User-Agent": 'softxm;netdisk'
        })

        try:
            response = urlopen(req, context=ssl._create_unverified_context())
            response_data = response.read().decode('utf-8')
            json_data = json.loads(response_data)
            return json_data
        except Exception as e:
            print(f"请求出错: {e}")

    def format_size(self, size_bytes):
        """精简版大小格式化（到GB为止）"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0 or unit == 'GB':
                break
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} {unit}"

    def list(self, path):
        params = {'app_id': PCS_APP_ID, 'method': 'list', 'path': path, 'order': 'asc'}
        data = self.__send(f'{PCS_URL}/file', params)

        results = []
        for info in data['list']:
            results.append({
                'name': info['server_filename'],
                'path': info['path'],
                'time': time.strftime('%Y-%m-%d', time.localtime(info['mtime'])),
                'size': self.format_size(info['size']),
                'is_dir': info['isdir'],  # 是否为目录，0 文件、1 目录
                'category': info['category'],  # 文件类型，1 视频、2 音频、3 图片、4 文档、5 应用、6 其他、7 种子
                'ext': info['real_category'],
            })

        return results
