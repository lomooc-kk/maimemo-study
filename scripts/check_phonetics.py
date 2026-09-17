#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核对生词条目的词性和音标：查权威来源、挑出写错的地方。

用法：
    py -3 check_phonetics.py --md work/src.md                # 校验短文里所有词条
    py -3 check_phonetics.py --md work/src.md --offline      # 只用本地缓存，不联网
    py -3 check_phonetics.py --lookup terrain garage marshal # 写材料时查词性/音标/释义

判定规则：
    * 词条必须写成 `- 单词 词性 /音标/ 释义`；缺词性或缺音标直接报错。
    * 音标统一用美式（General American）：卷舌音写出来（car /kɑːr/），go 写 /ɡoʊ/。
    * 音标只允许 IPA 字符；多音节词必须有且只有一个重音符号 ˈ。
    * 联网时向 dictionaryapi.dev 取该词的标准音标，和我们的写法比对：
      - 辅音骨架不一致 → 报错（多半是写错了）
      - 只差元音写法（不同词典的标注差异）→ 只提示，不算错
      - 查得到的词会写进 references/phonetics_cache.tsv，之后可离线复用

退出码非 0 表示有问题，改到通过为止。
"""

import argparse
import concurrent.futures
import io
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API = 'https://api.dictionaryapi.dev/api/v2/entries/en/'
CACHE = pathlib.Path(__file__).resolve().parent.parent / 'references' / 'phonetics_cache.tsv'

ENTRY = re.compile(
    r'^[-*]\s+'
    r'(?P<word>[A-Za-z][A-Za-z\'\-\s]{0,30}?)\s+'
    r'(?:(?P<pos>(?:n|v|adj|adv|prep|conj|pron|num|int|phr|abbr)\.(?:\s*[/&,]\s*(?:n|v|adj|adv|prep|conj|pron|num|int|phr|abbr)\.)*)\s+)?'
    r'(?P<ipa>[/\[][^/\]\n]{1,40}[/\]])?\s*'
    r'(?P<senses>.*)$'
)

# IPA 里允许出现的字符（含长度、重音、音节分隔）
ALLOWED = set('abcdefghijklmnopqrstuvwxyz')
ALLOWED |= set('æɑɒɔəɚɛɜɞɐɘɵœøɤɯɨʉʊʌɪʏiyeø')
ALLOWED |= set('pbtdkgfvθðszʃʒɹɾɻɲɳŋɴʈɖɟɡqχʁʕʔɦɬɮʦʣʧʤwjçʝ')
ALLOWED |= set('ˈˌːˑ.()̃')
VOWELS = set('æɑɒɔəɚɛɜɞɐɘɵœøɤɯɨʉʊʌɪʏiy')
STRESS = set('ˈˌ')


def load_cache():
    data = {}
    if CACHE.exists():
        for line in CACHE.read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                data[parts[0].lower()] = {'pos': parts[1], 'ipa': parts[2]}
    return data


def save_cache(data):
    lines = ['# word\tpos\tipa（来自 dictionaryapi.dev，供离线核对用）']
    for word in sorted(data):
        item = data[word]
        lines.append(f"{word}\t{item['pos']}\t{item['ipa']}")
    CACHE.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def request_word(word):
    """联网取一个词的词性与音标，失败返回 None。"""
    payload = None
    for attempt in range(2):
        try:
            request = urllib.request.Request(
                API + urllib.parse.quote(word), headers={'User-Agent': 'maimemo-study-skill'}
            )
            with urllib.request.urlopen(request, timeout=25) as response:
                payload = json.loads(response.read().decode('utf-8'))
            break
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
        except Exception:
            pass
        time.sleep(1.0 + attempt)
    if payload is None:
        return None
    pos_list, ipa = [], ''
    for entry in payload if isinstance(payload, list) else []:
        for meaning in entry.get('meanings', []):
            part = meaning.get('partOfSpeech', '')
            if part and part not in pos_list:
                pos_list.append(part)
        for item in entry.get('phonetics', []):
            text = (item.get('text') or '').strip()
            if text and not ipa:
                ipa = text
        if not ipa and entry.get('phonetic'):
            ipa = entry['phonetic']
    if not ipa and not pos_list:
        return None
    return {'pos': '/'.join(pos_list), 'ipa': ipa}


def fetch(word, cache, offline=False):
    """取一个词的词性与音标，优先用缓存。"""
    key = word.lower()
    if key in cache:
        return cache[key]
    if offline:
        return None
    info = request_word(word)
    if info:
        cache[key] = info
    return info


def prefetch(words, cache, offline=False, workers=6):
    """并发把还没缓存的词一次拉全，避免一个个慢慢等。"""
    todo = [word for word in dict.fromkeys(words) if word.lower() not in cache]
    if offline or not todo:
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(request_word, todo))
    for word, info in zip(todo, results):
        if info:
            cache[word.lower()] = info


def strip_marks(ipa):
    return re.sub(r'[/\[\]\s]', '', ipa)


def normalize(ipa):
    text = strip_marks(ipa).replace('g', 'ɡ')
    return re.sub(r'[.()ˌːˑ]', '', text)


def consonants(ipa):
    text = normalize(ipa)
    return ''.join(ch for ch in text if ch not in VOWELS and ch != 'ˈ')


def check_shape(word, ipa):
    """字符集与重音的基本检查。"""
    problems = []
    body = strip_marks(ipa)
    bad = sorted({ch for ch in body if ch not in ALLOWED})
    if bad:
        problems.append('出现不该有的字符 ' + ' '.join(bad))
    primary = body.count('ˈ')
    vowels = sum(1 for ch in body if ch in VOWELS)
    if len(body) >= 6 and vowels >= 2:
        if primary == 0:
            problems.append('多音节词没有标主重音 ˈ')
        elif primary > 1:
            problems.append('标了多个主重音')
    return problems


def parse_entries(md_path):
    entries = []
    for number, raw in enumerate(pathlib.Path(md_path).read_text(encoding='utf-8').split('\n'), 1):
        if not raw.strip().startswith(('-', '*')):
            continue
        match = ENTRY.match(raw.strip())
        if match:
            entries.append({'line': number, **match.groupdict()})
    return entries


def main():
    parser = argparse.ArgumentParser(description='核对词条的词性与音标')
    parser.add_argument('--md', help='短文 Markdown（核对里面所有词条）')
    parser.add_argument('--lookup', nargs='+', help='只查这些词的词性/音标/释义')
    parser.add_argument('--offline', action='store_true', help='只用本地缓存，不联网')
    parser.add_argument('--verify', action='store_true',
                        help='联网逐词比对标准音标（慢：几十个词要好几分钟，平时不用开）')
    args = parser.parse_args()

    cache = load_cache()

    if args.lookup:
        for word in args.lookup:
            info = fetch(word, cache, offline=args.offline)
            if not info:
                print(f'{word}\t查不到')
                continue
            print(f"{word}\t{info['pos'] or '?'}\t{info['ipa'] or '（无音标）'}")
        if not args.offline:
            save_cache(cache)
        return 0

    if not args.md:
        parser.error('要么给 --md，要么给 --lookup')
    entries = parse_entries(args.md)
    if not entries:
        print('没找到词条。词条要写成 `- 单词 词性 /音标/ 释义`。')
        return 1

    problems, warnings = [], []
    do_net = args.verify and not args.offline
    prefetch([entry['word'].strip() for entry in entries], cache, offline=not do_net)
    if do_net:
        save_cache(cache)          # 先存一次，网络中途出问题也不白跑
    for entry in entries:
        word = entry['word'].strip()
        label = f"第 {entry['line']} 行 {word}"
        if not entry['pos']:
            problems.append(f'{label}：缺词性（写成 n. / v. / adj. 这样）')
        if not entry['ipa']:
            problems.append(f'{label}：缺音标')
            continue
        for issue in check_shape(word, entry['ipa']):
            problems.append(f'{label}：{issue}')
        if not do_net:
            continue
        info = fetch(word, cache, offline=False)
        if not info or not info['ipa']:
            warnings.append(f'{label}：查不到标准音标，只能人工确认')
            continue
        ours, theirs = normalize(entry['ipa']), normalize(info['ipa'])
        if ours == theirs:
            continue
        if consonants(entry['ipa']) != consonants(info['ipa']):
            problems.append(
                f"{label}：音标和标准来源不一致 —— 我们写 {strip_marks(entry['ipa'])}，"
                f"标准 {strip_marks(info['ipa'])}"
            )
        else:
            warnings.append(
                f"{label}：只有元音写法不同（不同词典的标注差异，注意我们统一写美式）—— 我们写 "
                f"{strip_marks(entry['ipa'])}，参考 {strip_marks(info['ipa'])}"
            )

    if do_net:
        save_cache(cache)

    print(f'词条 {len(entries)} 条，其中 {len(cache)} 个词已有标准音标记录')
    if not do_net:
        print('（只做了本地检查：字符集、重音位置、词性是否齐全。'
              '要联网逐词比对加 --verify；只查个别词用 --lookup，快得多。）')
    for header, items in (('需要改正', problems), ('需要人工确认', warnings)):
        print(f'\n== {header} {len(items)} 条 ==')
        for item in items:
            print('  *', item)
        if not items:
            print('  无')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
