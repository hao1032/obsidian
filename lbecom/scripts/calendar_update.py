import os
from lbecom.libs.llm import llm
from pathlib import Path
import requests
from lbecom.libs import md_table

cache = {}

def get_test_time(id_, name):
    url = f'https://secure.seedasdan.com/hk/project/wx/detail/{id_}'
    if id_ not in cache:
        cache[id_] = requests.get(url).json()
        print( url, cache[id_])
    if 'Round 1' in name:
        return llm.test_time(name, cache[id_]['data']['moduleList'])
    return llm.test_time(name, cache[id_])


if __name__ == '__main__':
    p = Path(__file__).parent.parent / 'internal' / '竞赛时间.md'
    with p.open() as f:
        md_str = f.read()

    editor = md_table.Editor(md_str)
    table = editor.find_table_by_keyword('下次考试')
    headers = editor.get_row_headers(table)

    for row_header in headers:
        id_ = editor.get_cell_value(table, row_header, 'id')
        update = editor.get_cell_value(table, row_header, 'update')

        if not row_header or not id_:
            continue

        if row_header != 'BPhO Round 1':
            continue

        next_registration_deadline = editor.get_cell_value(table, row_header, '下次报名截止')
        next_test_date = editor.get_cell_value(table, row_header, '下次考试')




        print(row_header, id_, update)
        r = get_test_time(id_, row_header)
        print(r)
        break