import requests

url = 'http://lbepan.luoboedu.com?path=/US-美国/AMC 美国数学竞赛/AMC8/中英版'

resp = requests.get(url)
print(resp.json())