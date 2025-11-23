import jmespath
import requests
from llm import LLM
import lark_oapi as lark
from datetime import datetime, date
from lark_oapi.api.bitable.v1 import *

cache = {}

def _get_asd_data(id_):
    print(f'请求 阿思丹数据，id: {id_}')
    if not id_:
        return {}
    url = f'https://secure.seedasdan.com/hk/project/wx/detail/{id_}'
    if id_ not in cache:
        cache[id_] = requests.get(url).json()
        # print(json.dumps(cache[id_], indent=4, ensure_ascii=False))
    return cache[id_]

def _get_client(environment):
    client = lark.Client.builder() \
        .app_id(environment['FS_APP_ID']) \
        .app_secret(environment['FS_APP_SECRET']) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()
    return client

def _get_json_path_value(json_obj, expression):
    if not json_obj or not expression:
        return ''
    matches = jmespath.search(expression, json_obj)
    return matches[0] if matches else ''

def days_from_today(date_str):
    try:
        date_only = date_str.split()[0]  # 取空格前的部分
        target_date = datetime.strptime(date_only, '%Y-%m-%d').date()
        today = date.today()

        delta = target_date - today
        return delta.days
    except Exception as e:
        return None

def calendar_update(environment):
    app_token = 'KU8HbpYCuac5jIshdTXccJZ5n6f'
    table_id = 'tblhABdrZqDRxOLR'
    client = _get_client(environment)

    list_request = ListAppTableRecordRequest.builder() \
        .app_token(app_token) \
        .table_id(table_id) \
        .build()

    list_response = client.bitable.v1.app_table_record.list(list_request)
    if not list_response.success():
        print(f'获取列表，失败: {list_response.code}')
        return

    for record in list_response.data.items:
        name = record.fields.get('名称', None)
        print(f'当前处理: {name}')

        # 检查下次报名截止时间是否过期
        next_reg_days = days_from_today(record.fields.get('下次报名截止日期', ''))
        if next_reg_days is not None and next_reg_days < 0:
            record.fields['上次报名截止日期'] = record.fields['下次报名截止日期']
            record.fields['下次报名截止日期'] = ''
            print(f'{name} 报名截止 已过期 {record.fields["下次报名截止日期"]}')

        # 检查下次考试时间是否过期
        next_test_days = days_from_today(record.fields.get('下次考试日期', ''))
        if next_test_days is not None and next_test_days < 0:
            record.fields['上次考试日期'] = record.fields['下次考试日期']
            record.fields['下次考试日期'] = ''
            print(f'{name} 考试 已过期 {record.fields["下次考试日期"]}')

        # 检查下次报名截止时间和下次考试时间是否依然有效
        if next_reg_days is not None and next_reg_days > 0 and next_test_days is not None and next_test_days > 0:
            print(f'{name} 考试、报名时间依然有效')
            continue

        # 检查是否需要更新，一周内不再更新
        update_days = days_from_today(record.fields.get('阿思丹查询日期', ''))
        if update_days is not None and update_days > -7:
            print(f'{name} 一周内有更新，跳过本次更新')
            continue

        # 获取日期位置的 json path
        reg_path = record.fields.get('下次报名截止日期 json path', '')
        test_path = record.fields.get('下次考试日期 json path', '')
        if not reg_path and not test_path:
            print(f'{name} 缺少 json path，跳过更新')
            continue

        # 获取阿思丹竞赛数据
        data = _get_asd_data(record.fields.get('阿思丹id', ''))
        next_reg_date = _get_json_path_value(data, reg_path)
        next_test_date = _get_json_path_value(data, test_path)
        print(f'{name} 获取到新的 下次报名截止时间\n {next_reg_date}\n\n下次考试时间\n {next_test_date}')

        # 使用相同的 path，说明需要使用 ai 分析
        if reg_path == test_path:
            print(f'{name} 使用 ai 分析获取时间')
            try:
                llm = LLM(key=environment['OPENAI_API_KEY'])
                result = llm.test_time(record.fields.get('名称'), _get_json_path_value(data, reg_path))
                print(f'{name}, ai 分析结果: {result}')
                next_reg_date = result.get('报名截止日期', '')
                next_test_date = result.get('考试日期', '')
            except Exception as e:
                print(e)

        # 更新 下次报名截止时间
        next_reg_days  = days_from_today(next_reg_date)
        if next_reg_days is not None and next_reg_days >= 0:
            record.fields['下次报名截止日期'] = next_reg_date
            record.fields['更新时间'] = datetime.now().strftime('%Y-%m-%d')
            print(f'{name} 获取到新的 下次报名截止时间 {next_reg_date}')
        if next_reg_days is not None and next_reg_days < 0 and not record.fields.get('上次报名截止日期', ''):
            record.fields['上次报名截止日期'] = next_reg_date
            print(f'{name} 上次报名截止为空，更新为 {next_reg_date}')

        # 更新 下次考试时间
        next_test_days  = days_from_today(next_test_date)
        if next_test_days is not None and next_test_days >= 0:
            record.fields['下次考试日期'] = next_test_date
            record.fields['更新时间'] = datetime.now().strftime('%Y-%m-%d')
            print(f'{name} 获取到新的 下次考试时间 {next_test_date}')
        if next_test_days is not None and next_test_days < 0 and not record.fields.get('上次考试日期', ''):
            record.fields['上次考试日期'] = next_test_date
            print(f'{name} 上次考试日期为空，更新为 {next_test_date}')

        # 记录 更新日期
        record.fields['阿思丹查询日期'] = datetime.now().strftime('%Y-%m-%d')

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
            return

        print(record.fields)

        # break