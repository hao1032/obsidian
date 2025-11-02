import os
import json
from baidupan import Pan

def main_handler(event, context):
    prefix = '/重新整理的竞赛真题'

    data = {'list': []}
    try:
        environment = json.loads(context.get("environment", "{}"))
        pan = Pan(environment['cookie'])
        items = pan.list(f"{prefix}{event['queryString']['path']}")
        for item in items:
            item['path'] = item['path'].replace(prefix, '')
        data['list'] = items
    except Exception as e:
        print(e)

    return json.dumps(data, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    if os.path.exists('test_data.py'):
        from test_data import get_data
        e, c = get_data()
        main_handler(e, c)
    else:
        raise Exception("test_data.py not found")
