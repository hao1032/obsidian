import io
import subprocess
import time
from pypdf import PdfWriter, PdfReader
import requests
from playwright.sync_api import sync_playwright, expect
import psutil


class AopsPdf(object):
    def __init__(self):
        self.page = None
        self.name = None

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
        self.page = context.new_page()

    def remove_href(self):
        self.page.evaluate("""() => {
                var links = document.getElementsByTagName('a');
                Array.from(links).forEach(link => {
                    const text = link.textContent;
                    const textNode = document.createTextNode(text);
                    link.parentNode.replaceChild(textNode, link);
                });
            }""")

    def remove_nodes(self, container):
        [elem.evaluate('x => x.remove()') for elem in container.query_selector_all('table.wikitable')]
        [elem.evaluate('x => x.remove()') for elem in container.query_selector_all('div.toc')]
        [elem.evaluate('x => x.remove()') for elem in container.query_selector_all('div.print')]
        [elem.evaluate('x => x.remove()') for elem in container.query_selector_all('p a')]
        [elem.evaluate('x => x.remove()') for elem in container.query_selector_all('ul')]
        [elem.evaluate('x => x.remove()') for elem in container.query_selector_all('dl')]

        # 查找所有 h2 span 元素并根据文本内容过滤
        for elem in container.query_selector_all('h2 span'):
            if 'See Also'.lower().strip() in elem.text_content().lower().strip():
                elem.evaluate('x => x.remove()')

        # 查找所有 p 元素并根据文本内容过滤
        for elem in container.query_selector_all('p'):
            if elem.text_content().strip().startswith('== This page has some problems'):
                elem.evaluate('x => x.remove()')
            if elem.text_content().startswith('~'):
                elem.evaluate('x => x.remove()')
            if elem.text_content().strip().startswith('~'):
                elem.evaluate('x => x.remove()')

        # 查找所有 pre 元素并根据文本内容过滤
        for elem in container.query_selector_all('pre'):
            if elem.text_content().strip().startswith('~'):
                elem.evaluate('x => x.remove()')
            if elem.text_content().strip().startswith('http'):
                elem.evaluate('x => x.remove()')

        # 查找所有 h2 元素并根据文本内容过滤
        for elem in container.query_selector_all('h2'):
            if ' solution' in elem.text_content().lower():
                elem.evaluate('x => x.remove()')

    def save_pdf(self, name=None):
        self.remove_href()
        pdf_bytes = self.page.pdf(
            path=f"{name}.pdf" if name else None,
            margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"},
        )
        return pdf_bytes

    def goto(self, url):
        print(f"正在处理 {url}...")
        self.page.goto(url, timeout=60000)
        self.page.wait_for_load_state()

        # 在 page 级别删除节点
        [elem.evaluate('x => x.remove()') for elem in self.page.query_selector_all('div.catlinks')]
        [elem.evaluate('x => x.remove()') for elem in self.page.query_selector_all('div.printfooter')]
        [elem.evaluate('x => x.remove()') for elem in self.page.query_selector_all('div#print-footer')]
        [elem.evaluate('x => x.remove()') for elem in self.page.query_selector_all('div#top-bar')]
        [elem.evaluate('x => x.remove()') for elem in self.page.query_selector_all('div.wikiannounce-outer')]

        # 注入自定义 CSS 规则
        self.page.add_style_tag(content="""
            #main-column .page-wrapper {
                border-top: none !important;
            }
        """)

    def page_translate(self):
        print('点击翻译')
        self.page.locator("div#immersive-translate-popup >> div.imt-fb-btn.right.btn-animate").click()
        try:
            self.page.wait_for_selector(".immersive-translate-loading-spinner", state="visible", timeout=3000)  # 等待出现
            print('翻译中')
        except Exception as e:
            print(f'翻译中出现错误：{e}')
        try:
            self.page.wait_for_selector(".immersive-translate-loading-spinner", state="hidden", timeout=60000)  # 等待完全消失
            print('翻译完成')
        except Exception as e:
            print(f'翻译完成前出现错误：{e}')

    def save_problem(self):
        name = f'{self.name}_Problems'
        url = f'https://artofproblemsolving.com/wiki/index.php?title={name}'
        self.goto(url)
        container = self.page.query_selector('div.mw-content-ltr')
        self.remove_nodes(container)
        self.save_pdf(name)

    def save_key(self):
        name = f'{self.name}_Answer_Key'
        url = f'https://artofproblemsolving.com/wiki/index.php?title={name}'
        self.goto(url)
        self.save_pdf(name)

    def remove_blank_pages_with_images(self, pdf_writer, pdf_bytes):
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))

        for page in pdf_reader.pages:
            # 检查页面是否有文本内容
            has_text = bool(page.extract_text().strip())

            # 检查页面是否有图片
            has_images = False
            if hasattr(page, 'images') and len(page.images) > 0:
                has_images = True

            # 如果有文本或图片，则不是空白页
            if has_text or has_images:
                pdf_writer.add_page(page)

    def save_solutions(self):
        # 获取所有问题的 html
        merger = PdfWriter()
        merger_cn = PdfWriter()
        for i in range(1, 26):
            name = f'{self.name}_Problems/Problem_{i}'
            url = f'https://artofproblemsolving.com/wiki/index.php?title={name}'
            self.goto(url)
            container = self.page.query_selector('div.mw-content-ltr')
            self.remove_nodes(container)
            [elem.evaluate('x => x.remove()') for elem in self.page.query_selector_all('h2 span#Problem')]
            [elem.evaluate('x => x.remove()') for elem in self.page.query_selector_all('div#contentSub')]

            self.page.query_selector('h1.firstHeading span.mw-page-title-main').evaluate('(x, text) => x.textContent = text', f'Problem {i}')
            self.remove_blank_pages_with_images(merger, self.save_pdf())
            self.page_translate()
            self.remove_blank_pages_with_images(merger_cn, self.save_pdf())

        # 保存合并后的PDF
        with open(f"{self.name}_Solutions.pdf", "wb") as output_file:
            merger.write(output_file)
        merger.close()

        # 保存合并后的PDF
        with open(f"{self.name}_Solutions_cn.pdf", "wb") as output_file:
            merger_cn.write(output_file)
        merger_cn.close()

    def save_one(self, name):
        self.name = name
        self.save_problem()
        self.save_key()
        self.save_solutions()

if __name__ == '__main__':
    ap = AopsPdf()
    ap.connect_via_cdp()
    ap.save_one('2025_AMC_10B')
    ap.save_one('2025_AMC_12A')
    ap.save_one('2025_AMC_12B')