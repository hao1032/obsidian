import subprocess
import time

import requests
from playwright.sync_api import sync_playwright
import psutil


class AospPdf(object):
    def __init__(self):
        pass

    def kill_existing_chromium(self):
        """只检查并关闭Chromium进程"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                # 只检查名称包含chromium的进程
                if proc.info['name'] and 'chromium' in proc.info['name'].lower():
                    print(f"发现Chromium进程: PID {proc.info['pid']}")
                    proc.terminate()
                    print(f"已终止Chromium进程: {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 等待进程退出
        time.sleep(2)

    def launch_debug_chromium(self):
        if self.is_debug_browser_running():
            print("已存在Chromium调试模式进程")
            return
        self.kill_existing_chromium()
        # 启动Chromium调试模式
        cmd = [
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
            f"--remote-debugging-port=9222",
            "--no-first-run",
            "about:blank"
        ]

        self.browser_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 等待启动
        time.sleep(3)

    def is_debug_browser_running(self):
        """检测debug浏览器是否已经在运行"""
        try:
            # 尝试连接调试端口
            response = requests.get(f"http://localhost:9222/json/version", timeout=2)
            return response.status_code == 200
        except ConnectionError:
            return False
        except:
            return False

    def connect_via_cdp(self):
        self.launch_debug_chromium()
        p = sync_playwright().start()

        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        return  page

if __name__ == '__main__':
    aosp_pdf = AospPdf()
    page = aosp_pdf.connect_via_cdp()
    page.pdf(path="baidu.pdf")