import os
from pathlib import Path
from feishu import calendar_update


def main_handler(event, context):
    if event['path'] == '/fs' and event['queryString']['action'] == 'calendar_update':
        calendar_update()

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / '.env')
    event = {
        'path': '/fs',
        'queryString': {'action': 'calendar_update'}
    }
    context = {}
    main_handler(event, context)