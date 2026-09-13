#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按日期区间挑出墨墨学习记录里标记为「不熟 / 忘记」的单词。

用法示例：
    py -3 collect_review_words.py --days 3
    py -3 collect_review_words.py --date 2026-09-12
    py -3 collect_review_words.py --from 2026-09-01 --to 2026-09-13
    py -3 collect_review_words.py --days 3 --out work/words.json

令牌读取顺序：--token 参数 -> 环境变量 MAIMEMO_TOKEN -> ~/.codex/maimemo_token 文件。
只调用只读接口，不会修改账号里的任何数据。
"""

import argparse
import datetime as dt
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE = 'https://open.maimemo.com/open/api/v1'
RESPONSES = {'FAMILIAR': '认识', 'VAGUE': '不熟', 'FORGET': '忘记', 'WELL_FAMILIAR': '熟知'}
TOKEN_FILE = os.path.join(os.path.expanduser('~'), '.codex', 'maimemo_token')


def load_token(explicit=None):
    if explicit:
        return explicit.strip()
    env = os.environ.get('MAIMEMO_TOKEN')
    if env:
        return env.strip()
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, encoding='utf-8') as handle:
            return handle.read().strip()
    sys.exit(
        '找不到令牌。请让用户提供令牌，或用以下命令保存一次：\n'
        '  setx MAIMEMO_TOKEN "令牌"\n'
        f'  或写入文件：{TOKEN_FILE}'
    )


def api_post(path, body, token, retries=2):
    data = json.dumps(body, ensure_ascii=False).encode('utf-8')
    request = urllib.request.Request(
        BASE + path,
        data=data,
        headers={
            'Authorization': 'Bearer ' + token,
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=utf-8',
        },
        method='POST',
    )
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                payload = json.loads(response.read().decode('utf-8'))
            break
        except urllib.error.HTTPError as error:
            detail = error.read().decode('utf-8', 'replace')
            if error.code == 401:
                sys.exit('令牌无效或已过期：' + detail)
            if error.code in (429, 500, 502, 503) and attempt < retries:
                time.sleep(3 * (attempt + 1))
                continue
            sys.exit(f'请求失败（HTTP {error.code}）：{detail}')
        except urllib.error.URLError as error:
            if attempt < retries:
                time.sleep(3 * (attempt + 1))
                continue
            sys.exit(f'网络错误：{error}')
    if not payload.get('success', False):
        errors = payload.get('errors') or []
        message = '; '.join(f"{e.get('code')} {e.get('msg') or e.get('message')}" for e in errors)
        sys.exit('接口返回失败：' + (message or json.dumps(payload, ensure_ascii=False)))
    return payload.get('data') or {}


def fetch_window(token, start, end, limit=1000, depth=0):
    """按「下次复习时间」窗口拉取记录；窗口被 1000 条上限截断时自动对半拆分。"""
    body = {
        'next_study_date': {
            'start': start.strftime('%Y-%m-%dT00:00:00+08:00'),
            'end': end.strftime('%Y-%m-%dT00:00:00+08:00'),
        },
        'limit': limit,
    }
    records = api_post('/memo/study/query_study_records', body, token).get('records') or []
    if len(records) >= limit and depth < 6 and (end - start).days > 1:
        middle = start + (end - start) / 2
        print(f'  窗口 {start} ~ {end} 达到上限，自动拆分', file=sys.stderr)
        time.sleep(0.6)
        return (
            fetch_window(token, start, middle, limit, depth + 1)
            + fetch_window(token, middle, end, limit, depth + 1)
        )
    return records


def collect(token, first_day, last_day, scan_days=400):
    """从今天往前 30 天到往后 scan_days 天，按 30 天窗口把记录合并起来。"""
    today = dt.date.today()
    start = today - dt.timedelta(days=30)
    records = {}
    while start < today + dt.timedelta(days=scan_days):
        end = start + dt.timedelta(days=30)
        for record in fetch_window(token, start, end):
            records[record['voc_id']] = record
        print(f'  已扫描 {start} ~ {end}，累计 {len(records)} 条记录', file=sys.stderr)
        start = end
        time.sleep(0.6)
    return records


def main():
    parser = argparse.ArgumentParser(description='挑出某段时间里标记为不熟或忘记的单词')
    parser.add_argument('--days', type=int, help='最近多少天（含今天），例如 3')
    parser.add_argument('--date', help='只统计某一天，格式 2026-09-12')
    parser.add_argument('--from', dest='start', help='起始日期，格式 2026-09-01')
    parser.add_argument('--to', dest='end', help='结束日期，格式 2026-09-13')
    parser.add_argument('--responses', default='VAGUE,FORGET',
                        help='要统计的复习结果，默认 VAGUE,FORGET')
    parser.add_argument('--token', help='令牌，默认读环境变量或 ~/.codex/maimemo_token')
    parser.add_argument('--out', help='把结果写成 JSON 文件')
    parser.add_argument('--quiet', action='store_true', help='只输出 JSON')
    args = parser.parse_args()

    today = dt.date.today()
    if args.date:
        first_day = last_day = dt.datetime.strptime(args.date, '%Y-%m-%d').date()
    elif args.days:
        first_day = today - dt.timedelta(days=args.days - 1)
        last_day = today
    elif args.start or args.end:
        first_day = dt.datetime.strptime(args.start, '%Y-%m-%d').date() if args.start else today
        last_day = dt.datetime.strptime(args.end, '%Y-%m-%d').date() if args.end else today
    else:
        parser.error('请给出 --days、--date 或 --from/--to 之一')

    wanted = [item.strip().upper() for item in args.responses.split(',') if item.strip()]
    token = load_token(args.token)

    print(f'日期范围：{first_day} ~ {last_day}', file=sys.stderr)
    records = collect(token, first_day, last_day)

    picked = []
    for record in records.values():
        studied = (record.get('last_study_date') or '')[:10]
        if record.get('last_response') in wanted and first_day.isoformat() <= studied <= last_day.isoformat():
            picked.append({
                'spelling': record.get('voc_spelling'),
                'voc_id': record.get('voc_id'),
                'last_response': record.get('last_response'),
                'last_study_date': studied,
                'next_study_date': (record.get('next_study_date') or '')[:10],
                'study_count': record.get('study_count'),
            })
    picked.sort(key=lambda item: (item['last_study_date'], item['last_response'], item['spelling']))

    result = {
        'range': {'from': first_day.isoformat(), 'to': last_day.isoformat()},
        'responses': wanted,
        'total': len(picked),
        'by_response': {
            code: sum(1 for item in picked if item['last_response'] == code) for code in wanted
        },
        'by_date': {
            day: sum(1 for item in picked if item['last_study_date'] == day)
            for day in sorted({item['last_study_date'] for item in picked})
        },
        'words': picked,
    }

    if args.out:
        with open(args.out, 'w', encoding='utf-8') as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
        print(f'已写出 {args.out}', file=sys.stderr)

    if args.quiet:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"\n{first_day} ~ {last_day}：共 {result['total']} 个词")
    for code, count in result['by_response'].items():
        print(f"  {RESPONSES.get(code, code)}（{code}）：{count} 个")
    for day, count in result['by_date'].items():
        print(f'  {day}：{count} 个')
    print()
    for code in wanted:
        words = [item['spelling'] for item in picked if item['last_response'] == code]
        if words:
            print(f"== {RESPONSES.get(code, code)} {len(words)} 个 ==")
            print(', '.join(words))
            print()
    if not picked:
        print('这个区间里没有符合条件的词：可能当天还没同步，或这段日期没有标记不熟/忘记。')


if __name__ == '__main__':
    main()
