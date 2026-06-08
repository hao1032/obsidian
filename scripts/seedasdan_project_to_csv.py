#!/usr/bin/env python3
"""
Fetch Seedasdan project detail pages by id, ask the configured LLM to normalize
the competition information, and save the result as CSV.

Example:
    ./.venv/bin/python scripts/seedasdan_project_to_csv.py
"""

import csv
import html
import json
import random
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCF_API_DIR = ROOT / "scf-lbe-api"
if str(SCF_API_DIR) not in sys.path:
    sys.path.insert(0, str(SCF_API_DIR))


DETAIL_URL_TEMPLATE = "https://secure.seedasdan.com/hk/project/wx/detail/{id}"
DEFAULT_OUTPUT = ROOT / "scripts" / "seedasdan_projects.csv"

# 运行配置：直接修改这里，然后运行脚本即可。
PROJECT_IDS = "181"  # 支持 "181"、"181,185-190"，也支持 [181, 182, 183]
START_ID = 0
END_ID = 10
OUTPUT = DEFAULT_OUTPUT
USE_LLM = True
LLM_PROVIDER = "codex"
REQUEST_DELAY_SECONDS = 2.0
REQUEST_JITTER_SECONDS = 0.8
REQUEST_TIMEOUT_SECONDS = 20.0
REQUEST_RETRIES = 2
INSECURE = True
WRITE_EMPTY_OUTPUT = False
SAVE_AFTER_EACH = True
APPEND_OUTPUT = True

CSV_COLUMNS = [
    "id",
    "name",
    "name_en",
    "description",
    "category",
    "age_period",
    "start_date",
    "end_date",
    "open_date",
    "location",
    "language",
    "competition_time",
    "duration",
    "format",
    "scoring",
    "eligibility",
    "registration_requirement",
    "refund_policy",
    "calculator_policy",
    "result_release",
    "result_query",
    "detail_url",
    "thumb",
    "opened",
    "hot",
    "confidence",
    "date_conflict_note",
    "summary",
    "qa",
    "raw_response",
]
LLM_COLUMNS = [column for column in CSV_COLUMNS if column not in ("qa", "raw_response")]


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        data = data.strip()
        if data:
            self.parts.append(data)

    def get_text(self):
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def html_to_text(value):
    if not value:
        return ""
    parser = TextExtractor()
    parser.feed(html.unescape(str(value)))
    return parser.get_text()


def expand_project_ids(ids=None, start_id=None, end_id=None):
    if isinstance(ids, int):
        ids = [ids]
    elif ids is None:
        ids = []
    elif isinstance(ids, str):
        raw_ids = []
        for part in ids.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                start, end = part.split("-", 1)
                raw_ids.extend(range(int(start), int(end) + 1))
            else:
                raw_ids.append(int(part))
        ids = raw_ids
    else:
        ids = list(ids)

    if start_id is not None or end_id is not None:
        if start_id is None or end_id is None:
            raise ValueError("START_ID 和 END_ID 需要同时指定")
        ids.extend(range(start_id, end_id + 1))

    if not ids:
        raise ValueError("请在脚本配置里设置 PROJECT_IDS，或同时设置 START_ID/END_ID")

    return list(dict.fromkeys(ids))


def fetch_project(project_id, timeout, retries, insecure=False):
    url = DETAIL_URL_TEMPLATE.format(id=project_id)
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Referer": "https://secure.seedasdan.com/",
    }

    last_error = None
    context = ssl._create_unverified_context() if insecure else None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                body = resp.read().decode(charset)
            return json.loads(body)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"请求失败: {last_error}")


def compact_project(payload):
    data = payload.get("data") or {}
    modules = []
    for module in data.get("moduleList") or []:
        if module.get("hidden"):
            continue
        item_texts = []
        for item in module.get("itemList") or []:
            content = item.get("content")
            if content:
                item_texts.append(str(content))
        modules.append(
            {
                "name": module.get("name"),
                "content": html_to_text(module.get("content")),
                "items": item_texts,
            }
        )

    qa = []
    for item in data.get("qa") or []:
        if not item.get("hidden"):
            qa.append({"question": item.get("question"), "answer": item.get("answer")})

    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "nameEn": data.get("nameEn"),
        "description": data.get("description"),
        "descriptionEn": data.get("descriptionEn"),
        "category": data.get("category"),
        "agePeriod": data.get("agePeriod"),
        "startDate": data.get("startDate"),
        "endDate": data.get("endDate"),
        "openDate": data.get("openDate"),
        "locationList": data.get("locationList"),
        "detailUrl": data.get("detailUrl"),
        "thumb": data.get("thumb"),
        "opened": data.get("opened"),
        "hot": data.get("hot"),
        "qa": qa,
        "moduleList": modules,
    }


def extract_json(text):
    text = text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def normalize_with_llm(llm, project):
    system_prompt = (
        "你是竞赛信息整理助手。请从接口 JSON 和富文本内容中提取竞赛信息，"
        "按指定字段输出一个 JSON 对象。没有明确依据的字段填空字符串。"
    )
    user_prompt = f"""
请把下面竞赛资料整理成类似表格的一行数据，字段必须完整，且只返回 JSON。

字段：
{json.dumps(LLM_COLUMNS, ensure_ascii=False)}

要求：
1. 日期优先使用接口结构化字段；如果正文日期与结构化字段冲突，请在 date_conflict_note 说明。
2. location 可以合并 locationList 和正文地点。
3. language、competition_time、duration、format、scoring、eligibility 等字段通常在 moduleList 富文本中。
4. refund_policy、calculator_policy、result_release、result_query 可从 qa 中提取。
5. confidence 是 0 到 1 的数字，表示整理结果整体置信度。
6. summary 用一句中文概括竞赛。

竞赛资料：
{json.dumps(project, ensure_ascii=False)}
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    result = llm.request(messages, llm.model_text)
    return extract_json(result)


def fallback_row(project, error):
    return {
        "id": project.get("id"),
        "name": project.get("name"),
        "name_en": project.get("nameEn"),
        "description": project.get("description"),
        "category": project.get("category"),
        "age_period": project.get("agePeriod"),
        "start_date": project.get("startDate"),
        "end_date": project.get("endDate"),
        "open_date": project.get("openDate"),
        "location": " / ".join(project.get("locationList") or []),
        "detail_url": project.get("detailUrl"),
        "thumb": project.get("thumb"),
        "opened": project.get("opened"),
        "hot": project.get("hot"),
        "confidence": 0,
        "date_conflict_note": f"LLM 整理失败: {error}",
        "summary": project.get("description") or "",
        "qa": project.get("qa"),
    }


def error_row(project_id, message, payload=None):
    raw_response = payload if payload is not None else {"id": project_id, "error": message}
    return {
        "id": project_id,
        "confidence": 0,
        "date_conflict_note": message,
        "raw_response": raw_response,
    }


def normalize_row(row, project, payload=None):
    aliases = {
        "nameEn": "name_en",
        "agePeriod": "age_period",
        "startDate": "start_date",
        "endDate": "end_date",
        "openDate": "open_date",
        "detailUrl": "detail_url",
    }

    normalized = {column: "" for column in CSV_COLUMNS}
    for key, value in row.items():
        column = aliases.get(key, key)
        if column in normalized:
            normalized[column] = value

    defaults = {
        "id": project.get("id"),
        "name": project.get("name"),
        "name_en": project.get("nameEn"),
        "description": project.get("description"),
        "category": project.get("category"),
        "age_period": project.get("agePeriod"),
        "start_date": project.get("startDate"),
        "end_date": project.get("endDate"),
        "open_date": project.get("openDate"),
        "location": " / ".join(project.get("locationList") or []),
        "detail_url": project.get("detailUrl"),
        "thumb": project.get("thumb"),
        "opened": project.get("opened"),
        "hot": project.get("hot"),
        "qa": project.get("qa"),
    }
    for key, value in defaults.items():
        if normalized.get(key) in ("", None):
            normalized[key] = value
    if payload is not None:
        normalized["raw_response"] = payload

    for key, value in list(normalized.items()):
        if isinstance(value, (list, dict)):
            normalized[key] = json.dumps(value, ensure_ascii=False)
        elif value is None:
            normalized[key] = ""
    return normalized


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def append_rows(path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not path.exists() or path.stat().st_size == 0
    encoding = "utf-8-sig" if needs_header else "utf-8"
    with path.open("a", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if needs_header:
            writer.writeheader()
        writer.writerows(rows)


def run_export(
    ids=None,
    start_id=None,
    end_id=None,
    output=DEFAULT_OUTPUT,
    use_llm=True,
    provider="bigmodel",
    delay=2.0,
    jitter=0.8,
    timeout=20.0,
    retries=2,
    insecure=False,
    write_empty_output=False,
    save_after_each=True,
    append_output=True,
):
    project_ids = expand_project_ids(ids, start_id, end_id)
    output = Path(output)

    if not use_llm:
        llm = None
    else:
        from llm import LLM

        llm = LLM(provider=provider)
    rows = []
    saved_count = 0

    for index, project_id in enumerate(project_ids, start=1):
        print(f"[{index}/{len(project_ids)}] fetching project id={project_id}", flush=True)
        current_row = None
        try:
            payload = fetch_project(project_id, timeout, retries, insecure)
            project = compact_project(payload)
            if not payload.get("success") or not project.get("id"):
                print(f"  skip: empty or unsuccessful response", flush=True)
                current_row = normalize_row(
                    error_row(project_id, "接口返回为空或失败", payload),
                    {"id": project_id},
                    payload,
                )
            else:
                if llm is None:
                    row = fallback_row(project, "未启用 LLM")
                else:
                    try:
                        row = normalize_with_llm(llm, project)
                    except Exception as exc:
                        print(f"  LLM failed, writing fallback row: {exc}", flush=True)
                        row = fallback_row(project, exc)
                current_row = normalize_row(row, project, payload)
        except Exception as exc:
            print(f"  failed: {exc}", flush=True)
            current_row = normalize_row(
                error_row(project_id, str(exc)),
                {"id": project_id},
            )

        if current_row is not None:
            rows.append(current_row)
            if save_after_each:
                if append_output:
                    append_rows(output, [current_row])
                else:
                    write_rows(output, rows)
                saved_count += 1
                print(f"  saved progress: {saved_count} rows to {output}", flush=True)

        if index < len(project_ids):
            sleep_seconds = delay + random.uniform(0, max(jitter, 0))
            print(f"  sleeping {sleep_seconds:.1f}s", flush=True)
            time.sleep(sleep_seconds)

    if (rows or write_empty_output) and not save_after_each:
        if append_output:
            append_rows(output, rows)
        else:
            write_rows(output, rows)
        print(f"saved {len(rows)} rows to {output}", flush=True)
    elif rows:
        print(f"saved {saved_count} rows to {output}", flush=True)
    else:
        print(f"no rows saved; skip writing empty output to {output}", flush=True)
    return rows


def main():
    run_export(
        ids=PROJECT_IDS,
        start_id=START_ID,
        end_id=END_ID,
        output=OUTPUT,
        use_llm=USE_LLM,
        provider=LLM_PROVIDER,
        delay=REQUEST_DELAY_SECONDS,
        jitter=REQUEST_JITTER_SECONDS,
        timeout=REQUEST_TIMEOUT_SECONDS,
        retries=REQUEST_RETRIES,
        insecure=INSECURE,
        write_empty_output=WRITE_EMPTY_OUTPUT,
        save_after_each=SAVE_AFTER_EACH,
        append_output=APPEND_OUTPUT,
    )


if __name__ == "__main__":
    main()
