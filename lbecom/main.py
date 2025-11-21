import requests
import json

# 设置请求的URL和API密钥
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
api_key = "AIzaSyBAFYpIq4NMwBbLlq_az1IPrqtaQ6wloUA"  # 替换为你的API密钥

headers = {
    "Content-Type": "application/json"
}

data = {"contents": [{"parts": [{"text": "Explain how AI works"}]}]}

response = requests.post(f"{url}?key={api_key}", headers=headers, data=json.dumps(data))
print(response.json())