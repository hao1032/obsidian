import os
from pathlib import Path
import requests
from lbecom.libs import md_table

def get_asdan_time(id_):
    url = f'https://secure.seedasdan.com/hk/project/wx/detail/{id_}'
    data = requests.get(url).json()
    print(data)


if __name__ == '__main__':
    p = Path(__file__).parent.parent / 'internal' / '竞赛时间.md'
    with p.open() as f:
        md_str = f.read()

    editor = md_table.Editor(md_str)
    table = editor.find_table_by_keyword('下次考试')
    headers = editor.get_row_headers(table)

    for row_header in headers:
        id_ = editor.get_cell_value(table, row_header, 'id')
        time = editor.get_cell_value(table, row_header, 'time')
        if not (row_header and id_):
            continue
        print(row_header, id_, time)
        get_asdan_time(id_)
        break