#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核对错词短文：目标词是否都写进正文、单词表是否收全且顺序正确。

用法示例：
    py -3 check_passage.py --words work/words.json --md work/src.md
    py -3 check_passage.py --words work/words.json --md work/src.md --skeleton

--skeleton 会按词在正文中出现的顺序打印单词表骨架，把释义补在问号处即可。
词表条目写 "- word 释义"，也接受 "- word（说明） 释义"。

判定时把时态和单复数变化视为同一个词（weep→wept、swell→swelled、
lorry→lorries、hybridise→hybridising 等），所以正文用变形不算漏词；
单词表条目仍应写原形，另用括号注出正文里的变形。

有漏词或词表问题时退出码为 1，可用于反复修改直到通过。
"""

import argparse
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

LIST_HEADING = re.compile(r'^#{1,6}\s*单词表|\*\*单词表\*\*|^单词表', re.M)
BOLD = re.compile(r'\*\*(.+?)\*\*')
ENTRY = re.compile(r'^[-*]\s+([A-Za-z][A-Za-z\-]*)', re.M)
ENTRY_RAW = re.compile(r'^[-*]\s+(.+)$', re.M)
PHONETIC = re.compile(r'[/\[][^/\]\n]{1,40}[/\]]')

# 不规则变化：正文里出现的形式 -> 单词表里的原形
IRREGULAR = {
    'wept': 'weep',
    'withheld': 'withhold',
    'upheld': 'uphold',
    'held': 'hold',
    'wound': 'wind',
    'wore': 'wear',
    'borne': 'bear',
    'arose': 'arise',
    'sought': 'seek',
    'wrought': 'work',
    'drew': 'draw',
    'fled': 'flee',
    'flung': 'fling',
    'struck': 'strike',
    'shrank': 'shrink',
    'sprang': 'spring',
    'sang': 'sing',
    'swam': 'swim',
    'rose': 'rise',
    'drove': 'drive',
    'rode': 'ride',
    'fed': 'feed',
    'led': 'lead',
    'met': 'meet',
    'built': 'build',
    'bent': 'bend',
    'lent': 'lend',
    'sent': 'send',
    'spent': 'spend',
    'kept': 'keep',
    'swept': 'sweep',
    'crept': 'creep',
    'dealt': 'deal',
    'meant': 'mean',
    'set': 'set',
    'shed': 'shed',
    'spread': 'spread',
    'split': 'split',
    'cut': 'cut',
    'put': 'put',
    'read': 'read',
    'ground': 'grind',
    'bound': 'bind',
    'fought': 'fight',
    'bought': 'buy',
    'brought': 'bring',
    'caught': 'catch',
    'taught': 'teach',
    'thought': 'think',
    'tore': 'tear',
    'woke': 'wake',
    'chose': 'choose',
    'froze': 'freeze',
    'spoke': 'speak',
    'stole': 'steal',
    'broke': 'break',
    'wrote': 'write',
    'flew': 'fly',
    'grew': 'grow',
    'knew': 'know',
    'threw': 'throw',
    'blew': 'blow',
}


def key(text):
    """只保留字母，便于忽略大小写和标点。"""
    return re.sub(r'[^a-z]', '', text.lower())


def bases(word):
    """一个词的常见原形集合，用来把变形还原成原形。"""
    form = key(word)
    if not form:
        return set()
    found = {form}
    if form in IRREGULAR:
        found.add(IRREGULAR[form])
    changed = True
    while changed:
        changed = False
        for item in list(found):
            candidates = set()
            if item.endswith('ies') and len(item) > 3:
                candidates.add(item[:-3] + 'y')
            if item.endswith('ied') and len(item) > 3:
                candidates.add(item[:-3] + 'y')
            if item.endswith('es') and len(item) > 3:
                candidates.add(item[:-2])
            if item.endswith('s') and not item.endswith('ss') and len(item) > 2:
                candidates.add(item[:-1])
            if item.endswith('ing') and len(item) > 4:
                candidates.add(item[:-3])
                candidates.add(item[:-3] + 'e')
            if item.endswith('ed') and len(item) > 3:
                candidates.add(item[:-2])
                candidates.add(item[:-1])
            # 重叠辅音两个方向都生成：omitted → omitt → omit，swell → swel
            if len(item) > 3 and item[-1] == item[-2]:
                candidates.add(item[:-1])
            elif len(item) > 3:
                candidates.add(item + item[-1])
            for candidate in candidates:
                if len(candidate) > 2 and candidate not in found:
                    found.add(candidate)
                    changed = True
    return {item for item in found if len(item) > 2}


def same(one, other):
    if key(one) == key(other):
        return True
    return bool(bases(one) & bases(other))


def show(items, limit=30):
    """列表太长时截断，避免刷屏。"""
    items = list(items)
    if len(items) <= limit:
        return '、'.join(items) if items else '无'
    return '、'.join(items[:limit]) + f'……等 {len(items)} 个'


def load_targets(path):
    with open(path, encoding='utf-8') as handle:
        raw = handle.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return [line.strip() for line in raw.splitlines() if line.strip() and not line.startswith('#')]
    if isinstance(payload, list):
        items = payload
    else:
        items = payload.get('words') or payload.get('data', {}).get('words') or []
    out = []
    for item in items:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            spelling = item.get('spelling') or item.get('word')
            if spelling:
                out.append(spelling)
    return out


def split_body_and_list(md):
    match = LIST_HEADING.search(md)
    if not match:
        return md, ''
    return md[:match.start()], md[match.end():]


def main():
    parser = argparse.ArgumentParser(description='核对错词短文的用词与词表')
    parser.add_argument('--words', required=True, help='collect_review_words.py 的 JSON，或一行一个词的文本')
    parser.add_argument('--md', required=True, help='短文中间稿 Markdown')
    parser.add_argument('--skeleton', action='store_true', help='打印单词表骨架')
    parser.add_argument('--max-gap', type=float, default=18.0,
                        help='平均多少词才出现一个目标词，超过就提醒（默认 18）')
    parser.add_argument('--min-gap', type=float, default=6.0,
                        help='目标词过密的下限（默认 6）')
    args = parser.parse_args()

    for path in (args.words, args.md):
        if not os.path.exists(path):
            sys.exit('找不到文件：' + path)

    targets = load_targets(args.words)
    md = open(args.md, encoding='utf-8').read()
    body, listing = split_body_and_list(md)
    bold = [m.group(1) for m in BOLD.finditer(body)]
    entries = ENTRY.findall(listing)
    plain = re.sub(r'\*\*', '', body)
    word_count = len(re.findall(r"[A-Za-z][A-Za-z'\-]*", plain))

    problems = []
    missing = [t for t in targets if not any(same(t, b) for b in bold)]
    extra = [b for b in dict.fromkeys(bold) if not any(same(b, t) for t in targets)]
    repeated = sorted({b for b in bold if sum(1 for x in bold if key(x) == key(b)) > 1})

    print(f'目标词 {len(targets)} 个，正文加粗 {len(bold)} 处（去重 {len(set(map(key, bold)))} 个）')
    print(f'正文 {word_count} 词，平均每 {word_count / max(len(targets), 1):.1f} 词出现一个目标词')
    print(f'漏词（{len(missing)}）：' + show(missing))
    print(f'正文里多出来的加粗（{len(extra)}）：' + show(extra))
    print(f'重复加粗（{len(repeated)}）：' + show(repeated))

    if missing:
        problems.append('漏词')
    if extra:
        problems.append('多出的加粗')

    if not listing:
        print('没找到「单词表」小节')
        problems.append('缺单词表')
    else:
        list_missing = [t for t in targets if not any(same(t, e) for e in entries)]
        list_extra = [e for e in entries if not any(same(e, t) for t in targets)]
        duplicated = [e for e in dict.fromkeys(entries) if sum(1 for x in entries if key(x) == key(e)) > 1]
        first_seen = [b for b in dict.fromkeys(bold)]
        order_bad = []
        for index, entry in enumerate(entries):
            if index >= len(first_seen) or not same(entry, first_seen[index]):
                order_bad.append((entry, first_seen[index] if index < len(first_seen) else '（正文词数不足）'))
        print(f'单词表 {len(entries)} 条；缺词（{len(list_missing)}）：' + show(list_missing))
        print(f'单词表多余（{len(list_extra)}）：' + show(list_extra))
        print(f'单词表重复（{len(duplicated)}）：' + show(duplicated))
        if order_bad:
            print('单词表与正文出现顺序不一致，最早一处：' + f'{order_bad[0][0]} 对 {order_bad[0][1]}')
        else:
            print('单词表顺序与正文出现顺序一致')
        raw_entries = ENTRY_RAW.findall(listing)
        no_phonetic = [text.split()[0] for text in raw_entries if not PHONETIC.search(text)]
        print(f'带音标（{len(raw_entries) - len(no_phonetic)}/{len(raw_entries)}）：'
              + (show(no_phonetic) + ' 缺音标' if no_phonetic else '都有'))
        if list_missing or list_extra or duplicated or order_bad:
            problems.append('单词表')

    gap = word_count / max(len(targets), 1)
    if gap > args.max_gap:
        print(f'提醒：目标词偏稀（平均每 {gap:.1f} 词一个，建议不超过 {args.max_gap:g}），'
              '可以删些铺垫句或补几个结构句。')
    elif gap < args.min_gap:
        print(f'提醒：目标词偏密（平均每 {gap:.1f} 词一个），读起来容易生硬。')

    if args.skeleton:
        print('\n单词表骨架（按正文出现顺序）：')
        for word in dict.fromkeys(bold):
            match = next((t for t in targets if same(t, word)), word)
            print(f'- {match} ')

    if problems:
        print('\n需要修改：' + '、'.join(problems))
        return 1
    print('\n全部通过：目标词都在正文里，单词表收全且顺序一致。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
