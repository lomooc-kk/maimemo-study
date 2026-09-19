#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按难度档检查错词短文的句子长度、每句生词数和从句数量。

用法示例：
    py -3 check_difficulty.py --md work/src.md --level 中等
    py -3 check_difficulty.py --md work/src.md --level 简单 --words work/words.json

检查项：
    平均句长 / 最长句长 / 每句目标词数 / 每句从句标记数 / 每段目标词数 / 全局密度

判定为目标词的方式：文中加粗的词，加上 --words 里给出的单词（在正文中出现就算）。
有超出该档上限的句子时退出码为 1，方便改到通过。
"""

import argparse
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 每档：平均句长区间、单句上限、单句目标词上限、单句从句标记上限、密度区间（多少词一个目标词）
LEVELS = {
    '简单': {'avg': (8, 14), 'max_len': 20, 'max_targets': 1, 'max_clauses': 1, 'density': (8, 16),
             'per_para': (3, 5)},
    '中等': {'avg': (12, 18), 'max_len': 30, 'max_targets': 2, 'max_clauses': 1, 'density': (10, 20),
             'per_para': (4, 7)},
    '困难': {'avg': (16, 26), 'max_len': 38, 'max_targets': 3, 'max_clauses': 2, 'density': (7, 14),
             'per_para': (6, 10)},
}

# 只统计指向从句的明确标记；that / as / if / after / before 太容易误判，不计入
CLAUSE_MARKERS = (
    'which', 'who', 'whom', 'whose', 'where', 'when', 'while', 'whereas',
    'although', 'though', 'because', 'since', 'unless', 'despite', 'until', 'whether',
)
# 这些是介词短语或固定搭配，不引导从句，算进去会误判
PHRASES_TO_IGNORE = ('as a result', 'such as', 'as well as', 'so that', 'rather than', 'instead of',
                     'because of', 'in spite of', 'apart from', 'regardless of')
ABBREVIATIONS = ('Mr.', 'Mrs.', 'Dr.', 'St.', 'etc.', 'e.g.', 'i.e.', 'vs.', 'No.')
BOLD = re.compile(r'\*\*(.+?)\*\*')
SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')


def english_paragraphs(md_text):
    """挑出正文里的英文段落：排除标题、列表、引用和以中文为主的段落。"""
    paragraphs = []
    for raw in md_text.split('\n'):
        line = raw.strip()
        # 只跳过真正的标题/列表/引用/表格/代码行。以 **单词** 开头的句子是正文，
        # 不能因为首字符是 * 就被当成列表丢掉。
        if not line or re.match(r'^(#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||```)', line):
            continue
        letters = sum(1 for ch in line if ch.isascii() and ch.isalpha())
        chinese = sum(1 for ch in line if '\u4e00' <= ch <= '\u9fff')
        if letters >= 12 and chinese <= 2:
            paragraphs.append(line)
    return paragraphs


def sentences(paragraph):
    protected = paragraph
    for i, abbr in enumerate(ABBREVIATIONS):
        protected = protected.replace(abbr, f'@@{i}@@')
    parts = [p.strip() for p in SENTENCE_SPLIT.split(protected) if p.strip()]
    out = []
    for part in parts:
        for i, abbr in enumerate(ABBREVIATIONS):
            part = part.replace(f'@@{i}@@', abbr)
        out.append(part)
    return out


def count_words(text):
    return len(re.findall(r"[A-Za-z][A-Za-z'\-]*", text))


def load_words(path):
    if not path:
        return []
    raw = open(path, encoding='utf-8-sig').read()
    try:
        data = json.loads(raw)
        return [item['spelling'].lower() for item in data.get('words', [])]
    except json.JSONDecodeError:
        return [w.strip().lower() for w in raw.split() if w.strip()]


def count_targets(sentence, word_list=None):
    """句子里加粗的目标词数（首现）。

    刻意安排的复现（同一个词后文不再加粗地再出现）不算进"一句最多几个目标词"，
    不然"复现两三次"这条新规则会被误判。可以用 count_repeats 单独看复现量。
    """
    return len(BOLD.findall(sentence))


def count_repeats(sentence, word_list):
    """句子里没加粗、但属于目标词的复现次数。"""
    lowered = BOLD.sub(' ', sentence).lower()
    hits = []
    for word in word_list:
        if word and re.search(rf'\b{re.escape(word)}\w*', lowered):
            hits.append(word)
    return hits


def count_clauses(sentence):
    lowered = sentence.lower()
    for phrase in PHRASES_TO_IGNORE:
        lowered = lowered.replace(phrase, ' ')
    return sum(1 for marker in CLAUSE_MARKERS if re.search(rf'\b{marker}\b', lowered))


def main():
    parser = argparse.ArgumentParser(description='按难度档检查短文句子长度与生词密度')
    parser.add_argument('--md', required=True, help='短文中间稿 Markdown')
    parser.add_argument('--level', default='中等', choices=list(LEVELS), help='难度档，默认中等')
    parser.add_argument('--words', help='collect_review_words.py 的 JSON，用于统计未加粗的目标词')
    args = parser.parse_args()

    limits = LEVELS[args.level]
    md_text = open(args.md, encoding='utf-8-sig').read()
    paragraphs = english_paragraphs(md_text)
    word_list = load_words(args.words)

    if not paragraphs:
        print('没有找到英文段落，检查一下文件内容。')
        return 1

    all_sentences, per_paragraph = [], []
    repeat_words = {}
    for index, paragraph in enumerate(paragraphs, 1):
        items = sentences(paragraph)
        per_paragraph.append(sum(count_targets(s, word_list) for s in items))
        for sentence in items:
            for word in count_repeats(sentence, word_list):
                repeat_words[word] = repeat_words.get(word, 0) + 1
            all_sentences.append({
                'paragraph': index,
                'text': sentence,
                'length': count_words(sentence),
                'targets': count_targets(sentence, word_list),
                'clauses': count_clauses(sentence),
            })

    total_words = sum(count_words(p) for p in paragraphs)
    total_targets = sum(sum(1 for _ in BOLD.findall(p)) for p in paragraphs)
    average = total_words / max(len(all_sentences), 1)
    density = total_words / max(total_targets, 1)
    longest = max(all_sentences, key=lambda s: s['length'])

    print(f'难度档：{args.level}')
    print(f'段落 {len(paragraphs)} 段，句子 {len(all_sentences)} 句，正文 {total_words} 词，加粗目标词 {total_targets} 个')
    print(f'平均句长 {average:.1f} 词（该档建议 {limits["avg"][0]}–{limits["avg"][1]}）')
    print(f'最长句 {longest["length"]} 词（该档上限 {limits["max_len"]}）')
    print(f'密度：每 {density:.1f} 个词一个目标词（该档建议 {limits["density"][0]}–{limits["density"][1]}）')
    print(f'每段加粗词数：{per_paragraph}（该档建议 {limits["per_para"][0]}–{limits["per_para"][1]}）')
    if word_list:
        repeated = sum(repeat_words.values())
        print(f'复现：另有 {repeated} 处未加粗复现，涉及 {len(repeat_words)} 个词'
              + (f'（{", ".join(sorted(repeat_words)[:8])}…）' if repeated else '（还没有刻意复现）'))

    problems = []
    if not limits['avg'][0] <= average <= limits['avg'][1]:
        problems.append(f'平均句长 {average:.1f} 词，超出该档建议范围')
    if not limits['density'][0] <= density <= limits['density'][1]:
        problems.append(f'密度每 {density:.1f} 词一个目标词，超出该档建议范围')
    for sentence in all_sentences:
        if sentence['length'] > limits['max_len']:
            problems.append(f'第 {sentence["paragraph"]} 段有 {sentence["length"]} 词的长句：{sentence["text"][:60]}...')
        if sentence['targets'] > limits['max_targets']:
            problems.append(f'第 {sentence["paragraph"]} 段一句里有 {sentence["targets"]} 个目标词：{sentence["text"][:60]}...')
        if sentence['clauses'] > limits['max_clauses']:
            problems.append(f'第 {sentence["paragraph"]} 段有 {sentence["clauses"]} 处从句标记：{sentence["text"][:60]}...')
    for index, count in enumerate(per_paragraph, 1):
        if count and not limits['per_para'][0] <= count <= limits['per_para'][1]:
            problems.append(f'第 {index} 段有 {count} 个加粗词，超出该档建议范围')

    print('\n超出该档的项目：')
    if problems:
        for item in problems[:20]:
            print(' *', item)
        if len(problems) > 20:
            print(f' …… 还有 {len(problems) - 20} 条')
        return 1
    print(' 无')
    return 0


if __name__ == '__main__':
    sys.exit(main())
