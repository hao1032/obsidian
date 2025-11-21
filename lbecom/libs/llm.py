import os
import json
import time
from pathlib import Path

import openai
import base64
import logging


PROVIDER = {
    'siliconflow': {
        'base_url': 'https://api.siliconflow.cn/v1',
        'model_image': 'Pro/Qwen/Qwen2-VL-7B-Instruct',
        'model_text': 'deepseek-ai/DeepSeek-R1-0528-Qwen3-8B',
        # 'model_text': 'deepseek-ai/DeepSeek-R1-0528-Qwen3-8B',
        # 'model_text': 'THUDM/GLM-Z1-9B-0414',
    },
    'bigmodel': {
        'base_url': 'https://open.bigmodel.cn/api/paas/v4',
        'model_image': 'glm-4v-flash',
        # 'model_text': 'glm-z1-flash',
        'model_text': 'glm-4.5-flash',
    },
    'gemini': {
        'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai/',
        'model_image': 'gemini-2.5-pro',
        'model_text': 'gemini-2.5-pro',
    }
}

class LLM(object):
    def __init__(self, provider='siliconflow'):
        self.model_image = PROVIDER[provider]['model_image']
        self.model_text = PROVIDER[provider]['model_text']
        if not os.environ.get('OPENAI_API_KEY', None):
            from dotenv import load_dotenv
            p = Path(__file__).parent.parent.parent / '.env'
            load_dotenv(dotenv_path=p)
        self.client = openai.OpenAI(base_url=PROVIDER[provider]['base_url'])

    def request(self, message, model=None):
        resp = self.client.chat.completions.create(
            model=model,
            temperature=0.1,
            messages=message,
            stream=False,
            timeout=30,
        )
        content = resp.choices[0].message.content
        return content

    def ocr(self, image):
        start_time = time.time()
        image_base64 = base64.b64encode(image).decode('utf-8')
        data_uri = f'data:image/jpeg;base64,{image_base64}'

        message = [
            {'role': "user", 'content': [
                {'type': 'image_url', 'image_url': {'url': data_uri}},
                {'type': 'text', 'text': """
                    你作为专业OCR处理引擎，请严格按以下规则处理图片：
                    1. **词级分割**：
                    - 识别所有独立单词/中文词语
                    - 按空格、标点或语义边界自动切分
                    - 保留连续数字序列（如电话号）为单一词
                    2. **位置标注**：
                    - 为每个词生成边界框(bounding box)
                    - 使用绝对坐标格式：[x_min, y_min, x_max, y_max]
                    - 坐标系：左上角为原点(0,0)，X轴向右，Y轴向下
                    3. **输出格式**：仅返回JSON对象
                    {
                    "image_size": [width, height],
                    "units": [
                        {
                        "text": "识别词",
                        "box": [x1, y1, x2, y2],
                        "confidence": 0.0-1.0
                        },
                    ]
                    }
                    4. **特殊处理**：
                    - 连接词如"&"或短横线"-"视为独立单位
                    - 模糊词降低confidence值
                    - 忽略小于5像素的噪声点
                """},
            ]},
        ]
        content = self.request(message, model=self.model_image)
        content = content.replace('\n', '').replace('```', '').replace('json{', '{')
        results = json.loads(content)
        logging.debug(f"LLM OCR 耗时: {time.time() - start_time:.2f}s")
        return results

    def content_summary(self, content):
        message = [
            {'role': "user", 'content': [
                {'type': 'text', 'text': '你觉得下面的文本内容，讲了什么？'},
                {'type': 'text', 'text': content}
            ]},
        ]
        return self.request(message, self.model_text)

    def test_time(self, test_name, data):
        message = [
            {'role': "user", 'content': [
                {'type': 'text', 'text': f'从给定的内容中提取 {test_name} 的报名截止时间和考试时间，不需要时间。'},
                {'type': 'text', 'text': f'注意考试名称，不要搞错项目，弄错时间。'},
                {'type': 'text', 'text': f'{data}'},
                {'type': 'text', 'text': '示例1：{"报名截止": "2025-01-13", "考试日期": "2025-01-23"}'},
                {'type': 'text', 'text': '示例2：{"报名截止": "不确定", "考试日期": "2025-01-23"}'},
                {'type': 'text', 'text': '示例3：{"报名截止": "2025-01-13 待定", "考试日期": "2025-01-23 待定"}'},
                {'type': 'text', 'text': '返回格式为json文本，不需要code ``` 包裹，不需要外层的```json'},
            ]},
        ]
        r = self.request(message, self.model_text)
        print( r)
        j = json.loads(r)
        return j

llm = LLM(provider='gemini')

if __name__ == '__main__':
    data =     {'code': 0, 'msg': None, 'data': {'id': 181, 'name': '美国数学测评（AMC8）', 'description': '全球权威青少年数学思维挑战活动之一', 'thumb': 'http://seed-static.seedasdan.com/wordpress/2020/10/veer-154103812.jpg', 'startDate': '2026-01-23', 'opened': True, 'hot': False, 'frequency': None, 'locationList': ['全国各合作学校校内（学校申请可提供在线测评服务）'], 'tagList': None, 'contactQrCode': None, 'signupProjectId': None, 'nameEn': 'American Mathematics Competition (AMC8)', 'descriptionEn': 'One of global authoritative youth math challenge Over 300,000 students participating annually in over 6,000 schools from 30 countries and regions', 'priority': None, 'sortSequence': 100, 'agePeriod': '8年级且14.5岁以下', 'endDate': '2026-01-13 23:59:59', 'subjectId': 6, 'qa': [{'question': '如何更改注册信息？', 'answer': '登录微信“阿思丹国际学术挑战”小程序 -“我的报名”- 点击“个人资料”可修改个人信息（如需修改手机号，点击“我的”- 账号安全处完成修改）。', 'hidden': False}, {'question': '何时收到活动细则及流程说明？', 'answer': '正式活动前3天左右（具体以实际发出时间为准）将以邮件和短信的形式发送活动说明等重要事项至报名预留的邮箱和手机号，届时请注意查收！', 'hidden': False}, {'question': '可以退费吗？', 'answer': '同学报名缴费之后，由于临时有事可以申请退出。在报名截止日之前申请，将扣除报名费的25%作为学术材料费及服务费；报名截止日之后申请，将不予退费。', 'hidden': False}, {'question': '可以使用计算器吗？', 'answer': '不允许使用任何计算器。', 'hidden': False}, {'question': '何时公布奖项？', 'answer': '具体开放时间根据国外MAA组委会公布后另行通知，所有成绩将在“阿思丹国际学术挑战”微信小程序上公布。', 'hidden': False}, {'question': '如何查询成绩和下载电子证书？', 'answer': '成绩公布后，登录微信“阿思丹国际学术挑战”小程序 -“我的报名”- 点击对应项目-“成绩查询”/“证书下载”，进行成绩查询和电子证书下载。', 'hidden': False}], 'moduleList': [{'name': '报名须知/Requirement', 'itemList': [], 'content': '<p>仅限在中国大陆地区就读的学生报名。非中国大陆地区学生如需报名请联系当地组委会。</p><p>Registration is only open to students studying in mainland China. Students outside mainland China&nbsp; &nbsp; &nbsp; &nbsp; who wish to register should contact the local organizing committee.</p>', 'hidden': False}, {'name': '项目简介', 'itemList': [{'content': 'http://seed-academy.oss-cn-beijing.aliyuncs.com/wx/65af45c7-a41d-4f1d-bbd0-ab06e0663d46.png', 'type': 2, 'toProjectId': None}], 'content': '<p><span style="font-weight: bold; color: rgb(249, 150, 59);">\n\n\n美国数学测评 (AMC) </span>由美国数学协会 (MAA) 举办，目前每年全球超过 6000 所学校的 30 万名同学参加，是全球最有影响力的青少年数学测评活动之一。美国数学测评包括了 AMC8、AMC10/12、AIME、USAMO/USAJMO，其中 AMC8 主要面向 8 年级（初二）以下的初中和小学高年级学生；AMC10/12 主要面向 10 年级（高一）和 12 年级（高三）以下的高中生；AIME 主要是面向\nAMC10/12 优秀学生，为美国数学奥林匹克 USAMO/USAJMO 和美国数学奥林匹克国家队的选拔。&nbsp;</p><p>因为设计严谨、简难兼具，AMC 不但在测试中使任何程度学生都能感受到挑战，能充分而客观的考察出学生的数学能力，还以试题的高鉴别度，从中筛选出特有天赋者进入国际数学奥林匹克活动美国国家队。\n\n\n\n</p>', 'hidden': False}, {'name': '项目规则', 'itemList': [], 'content': '<p><span style="font-weight: bold; background-color: rgb(249, 150, 59);">语言：</span>中英文双语&nbsp;</p><p><span style="font-weight: bold; background-color: rgb(249, 150, 59);">时间：</span>2026 年 1 月 23 日（周五）17:00-17:40（40 分钟）</p><p><span style="font-weight: bold; background-color: rgb(249, 150, 59);">地点：</span><span style="background-color: rgb(255, 255, 255);">全国各合作学校内（学校申请可提供在线测评服务）</span></p><p><span style="font-weight: bold; background-color: rgb(249, 150, 59);">形式：</span>个人，25 道单项选择题&nbsp;</p><p><span style="font-weight: bold; background-color: rgb(249, 150, 59);">评分标准：</span>答对一题得 1 分，答错不扣分，满分 25 分&nbsp;</p><p><span style="font-weight: bold; background-color: rgb(249, 150, 59);">资格：</span>8 年级（初二）且 14.5 岁以下年级 / 年龄学生\n <span style="color: rgb(155, 155, 155);">（年龄截止至测评活动当天）&nbsp; &nbsp;</span><br></p><p><span style="font-weight: bold; background-color: rgb(249, 150, 59);">报名截止时间：</span><span style="background-color: rgb(255, 255, 255);">2026 年 1 月 13 日</span></p><p>注：在读年级参考下图填写\n\n</p><p><img src="https://attach.seedasdan.com/STEM/GradeSystem.png" style="max-width:100%;"></p>', 'hidden': False}, {'name': '即刻加入A-PASS会员', 'itemList': [], 'content': '<p><img src="https://attach.seedasdan.com/APASS/小程序APASS介绍0327.jpg" style="max-width:100%;"><br></p>', 'hidden': False}], 'detailUrl': 'http://www.seedasdan.asia/en/amc8-en/', 'isCollect': False, 'receiveList': [], 'availableCoupons': False, 'followWechat': False, 'category': 'STEM'}, 'success': True}

    a = llm.test_time('AMC 8', data)
    print(a)