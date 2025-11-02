import requests

url = 'http://lbepan.luoboedu.com?path=/US-美国'

resp = requests.get(url)
print(resp.json())