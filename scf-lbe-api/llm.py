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
    def __init__(self, provider='siliconflow'):
        self.model_image = PROVIDER[provider]['model_image']
        self.model_text = PROVIDER[provider]['model_text']
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

    def test_time(self, purpose, data):
        message = [
            {'role': "user", 'content': [
                {'type': 'text', 'text': f'从下面的数据内容中提取 {purpose} 。'},
                {'type': 'text', 'text': f'数据内容：{data}'},
                {'type': 'text', 'text': '返回格式使用json，并根据具体情况添加置信度数据，示例如下：'},
                {'type': 'text', 'text': '示例 1：{"报名截止日期": "2025-01-13", "置信度": 0.9}'},
                {'type': 'text', 'text': '示例 2：{"考试日期": "2025-01-13", "置信度": 0.8}'},
                {'type': 'text', 'text': '示例2：{"报名截止日期": "不确定", "置信度": 0.3}'},
                {'type': 'text', 'text': '示例3：{"考试日期": "2025-01-13 暂定", "置信度": 0.85}'},
            ]},
        ]
        r = (self.request(message, self.model_text))
        print(f'ai 返回的内容: {r}')
        r = r.replace('```json', '').replace('```', '')
        j = json.loads(r)
        return j

if __name__ == '__main__':
    pass