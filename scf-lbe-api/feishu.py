import os
import jmespath
import requests
from llm import LLM
import lark_oapi as lark
from datetime import datetime, date
from lark_oapi.api.bitable.v1 import *

cache = {}

def _get_asd_data(id_):
    if not id_:
        return {}
    url = f'https://secure.seedasdan.com/hk/project/wx/detail/{id_}'
    print(f'请求阿思丹数据: {url}')
    if id_ not in cache:
        cache[id_] = requests.get(url).json()
        # print(json.dumps(cache[id_], indent=4, ensure_ascii=False))
    return cache[id_]

def _get_client():
    client = lark.Client.builder() \
        .app_id(os.environ['FS_APP_ID']) \
        .app_secret(os.environ['FS_APP_SECRET']) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()
    return client

def _get_json_path_value(json_obj, expression):
    if not json_obj or not expression:
        return ''
    matches = jmespath.search(expression, json_obj)
    return matches if matches else ''

def days_from_today(date_str):
    try:
        date_only = date_str.split()[0]  # 取空格前的部分
        target_date = datetime.strptime(date_only, '%Y-%m-%d').date()
        today = date.today()

        delta = target_date - today
        return delta.days
    except Exception as e:
        return None

def _get_new_date_from_asd(record, key):
    # 检查 阿思丹id 和 json path 配置
    asd_id = record.fields.get('阿思丹id', '')
    json_path_name = f'下次{key}日期 json path'
    expression = record.fields.get(json_path_name, '')  # json path 表达式
    if not asd_id or not expression:
        print('没有配置阿思丹id 或者 json path')
        return None, None

    # 获取阿思丹数据
    data = _get_asd_data(asd_id)
    date_str = _get_json_path_value(data, expression)
    print(f'通过 json path 获取到的内容为: {date_str}')
    record.fields['阿思丹查询日期'] = datetime.now().strftime('%Y-%m-%d')  # 记录阿思丹查询时间

    date_delta = days_from_today(date_str)
    if date_delta is None:
        purpose = f"{record.fields.get('名称')} 的 {key} 日期"
        print(f'获取到的数据不是具体日期，需要使用 ai 分析获取：{purpose}')
        llm = LLM()
        result = llm.test_time(purpose, date_str)
        print(f'ai 获取到的内容: {result}')
        date_str = result.get(f'{key}日期', '')
        date_delta = days_from_today(date_str)
    return date_str, date_delta

def update_time(record, key):
    print(f'处理 {key} 日期 的更新')
    prev_date_name = f'上次{key}日期'
    next_date_name = f'下次{key}日期'
    modified = False

    # 下次日期，有3种情况：1. 空，2. 有效日期【2025-03-18】，3. 无效日期【2025-03-18 暂定】
    next_date = record.fields.get(next_date_name, '')
    next_date_delta = days_from_today(next_date) # 下次日期距离今天的天数

    # 下次日期，有效，并且没有过期
    if next_date_delta is not None and next_date_delta >= 0:
        print(f'{key} 日期有效，距离今天还有 {next_date_delta} 天')
        return modified

    # 下次日期，有效，但是已经过期，复制给上次日期
    if next_date_delta is not None and next_date_delta < 0:
        record.fields[prev_date_name] = next_date
        record.fields[next_date_name] = ''
        modified = True

    # 如果最近更新过，就不在更新
    update_date = record.fields.get('更新日期', '')
    update_delta = days_from_today(update_date)
    if update_delta is not None and update_delta != 0 and update_delta > -7:
        print('一周内已经更新过')
        return modified

    next_date, next_date_delta = _get_new_date_from_asd(record, key)
    modified = True

    prev_date = record.fields.get(prev_date_name, '')
    if next_date_delta is not None and next_date_delta < 0 and next_date != prev_date:
        print(f'获取的 {key} 日期已过期，写入 上次日期')
        record.fields[prev_date_name] = next_date
        return modified

    if next_date:
        print(f'将获取的 {key} 日期写入 {next_date_name}：{next_date}')
        record.fields[next_date_name] = next_date
        record.fields['更新日期'] = datetime.now().strftime('%Y-%m-%d')

    return modified


def calendar_update():
    app_token = 'KU8HbpYCuac5jIshdTXccJZ5n6f'
    table_id = 'tblhABdrZqDRxOLR'
    client = _get_client()

    list_request = ListAppTableRecordRequest.builder() \
        .app_token(app_token) \
        .table_id(table_id) \
        .build()

    list_response = client.bitable.v1.app_table_record.list(list_request)
    if not list_response.success():
        print(f'获取列表，失败: {list_response.code}')
        return

    for record in list_response.data.items:
        name = record.fields.get('名称', '')
        if not name:
            continue
        print(f'\n\n当前处理: {name}')

        f1 = update_time(record, '报名截止')
        f2 = update_time(record, '考试')
        if not f1 and not f2:
            continue

        update_request = UpdateAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .record_id(record.record_id) \
            .request_body(AppTableRecord.builder()
                      .fields(record.fields)
                      .build()) \
            .build()
        response = client.bitable.v1.app_table_record.update(update_request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.bitable.v1.app_table_record.update failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
            continue

        return name
    return '完成'

