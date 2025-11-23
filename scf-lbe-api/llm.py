import os
import json
import openai


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
        'model_text': 'gemini-2.5-flash',
    }
}

class LLM(object):
    def __init__(self, provider='siliconflow', key=None):
        self.model_image = PROVIDER[provider]['model_image']
        self.model_text = PROVIDER[provider]['model_text']
        os.environ['OPENAI_API_KEY'] = key
        self.client = openai.OpenAI(base_url=PROVIDER[provider]['base_url'], timeout=50)

    def request(self, message, model=None):
        resp = self.client.chat.completions.create(
            model=model,
            temperature=0.1,
            messages=message,
            stream=False,
            timeout=50
        )
        content = resp.choices[0].message.content
        return content

    def test_time(self, test_name, data):
        message = [
            {'role': "user", 'content': [
                {'type': 'text', 'text': f'从下面的数据源中提取 {test_name} 的“报名截止日期”和“考试日期”，不需要时间。'},
                {'type': 'text', 'text': f'注意考试名称，不要搞错项目，弄错日期。'},
                {'type': 'text', 'text': f'数据源：{data}'},
                {'type': 'text', 'text': '示例1：{"报名截止日期": "2025-01-13", "考试日期": "2025-01-23"}'},
                {'type': 'text', 'text': '示例2：{"报名截止日期": "不确定", "考试日期": "2025-01-23"}'},
                {'type': 'text', 'text': '示例3：{"报名截止日期": "2025-01-13 暂定", "考试日期": "2025-01-23 暂定"}'},
            ]},
        ]
        r = self.request(message, self.model_text).replace('```json', '').replace('```', '')
        j = json.loads(r)
        return j

if __name__ == '__main__':
    pass