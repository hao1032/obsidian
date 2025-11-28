import os
from datetime import datetime
from lbecom.libs.llm import llm
from pathlib import Path
import requests
from lbecom.libs import md_table

cache = {}

def get_test_time(id_, name):
    url = f'https://secure.seedasdan.com/hk/project/wx/detail/{id_}'
    if id_ not in cache:
        cache[id_] = requests.get(url).json()
    return llm.test_time(name, cache[id_])


def calculate_days_until(target_date_str):
    """
    计算目标日期距离今天的天数
    Args: target_date_str (str): 目标日期字符串，格式为 'YYYY-MM-DD'
    Returns: int: 距离今天的天数，正数表示未来，负数表示过去
    """
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        days_difference = (target_date - today).days
        return days_difference
    except Exception as e:
        return None


if __name__ == '__main__':
    p = Path(__file__).parent.parent / 'docs' / 'calendar.md'
    with p.open() as f:
        md_str = f.read()

    editor = md_table.Editor(md_str)
    table = editor.find_table_by_keyword('下次考试')
    headers = editor.get_row_headers(table)

    for row_header in headers:
        # 过滤空行
        if not row_header:
            continue
        print(f'{row_header} 检测中...')

        # 检查下次报名截止时间是否过期
        next_reg_date = editor.get_cell_value(table, row_header, '下次报名截止')
        next_reg_days = calculate_days_until(next_reg_date)
        if next_reg_days is not None and next_reg_days < 0:
            editor.set_cell_value(table, row_header, '上次报名截止', next_reg_date)
            editor.set_cell_value(table, row_header, '下次报名截止', '')
            next_reg_date = ''
            print(f'{row_header} 报名截止 已过期 {next_reg_date}')

        # 检查下次考试时间是否过期
        next_test_date = editor.get_cell_value(table, row_header, '下次考试')
        next_test_days = calculate_days_until(next_test_date)
        if next_test_days is not None and next_test_days < 0:
            editor.set_cell_value(table, row_header, '上次考试', next_test_date)
            editor.set_cell_value(table, row_header, '下次考试', '')
            next_test_date = ''
            print(f'{row_header} 考试 已过期 {next_test_date}')

        # 检查下次报名截止时间和下次考试时间是否依然有效
        if next_reg_days is not None and next_reg_days > 0 and next_test_days is not None and next_test_days > 0:
            continue

        # 检查是否需要更新，一周内不再更新
        update_date = editor.get_cell_value(table, row_header, 'update')
        update_days = calculate_days_until(update_date)
        if update_days is not None and update_days > -7:
            continue

        id_ = editor.get_cell_value(table, row_header, 'id')
        if not id_:
            continue

        # 更新
        result = get_test_time(id_, row_header)
        next_reg_date = result.get('报名截止', '')
        next_reg_days = calculate_days_until(next_reg_date)
        if next_reg_days is not None and next_reg_days >= 0:
            editor.set_cell_value(table, row_header, '下次报名截止', next_reg_date)
            print(f'{row_header} 更新 报名截止 {next_reg_date}')

        next_test_date = result.get('考试日期', '')
        next_test_days = calculate_days_until(next_test_date)
        if next_test_days is not None and next_test_days >= 0:
            editor.set_cell_value(table, row_header, '下次考试', next_test_date)
            print(f'{row_header} 更新 考试 {next_test_date}')

        editor.set_cell_value(table, row_header, 'update', datetime.now().strftime('%Y-%m-%d'))

    md_str = editor.rebuild_markdown()
    with p.open('w', encoding='utf-8') as f:
        f.write(md_str)