from pathlib import Path
from feishu import calendar_update


def main_handler(event, context):
    if event['path'] == '/fs' and event['queryString']['action'] == 'calendar_update':
        calendar_update(context['environment'])

if __name__ == '__main__':
    from dotenv import dotenv_values
    kv = dotenv_values(Path(__file__).parent / '.env')
    event = {
        'path': '/fs',
        'queryString': {'action': 'calendar_update'}
    }
    context = {
        'environment': dict(kv)
    }
    main_handler(event, context)