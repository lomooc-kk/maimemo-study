# -*- coding: utf-8 -*-
"""把结构简单的 Markdown 转成排版规范的 Word 文档。

支持：#/##/### 标题、**加粗**、`行内代码`、[文字](链接)、
代码块、- / 1. 列表、> 引用、| 表格 |、--- 分隔线、<!-- 注释 -->。

「单词表」小节里的 `- 单词 /音标/ 释义` 会排成两列小字，省纸、方便打印；
音标可省略，省略时该条只显示单词和释义。
"""

import io
import re
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BODY_LATIN = 'Cambria'
BODY_EA = 'Microsoft YaHei'
CODE_FONT = 'Consolas'
HEADER_FILL = '1F3864'
ALT_FILL = 'F2F5FA'
BORDER = 'D9D9D9'


def set_run_font(run, latin=BODY_LATIN, ea=BODY_EA):
    run.font.name = latin
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts')
        rpr.append(rfonts)
    rfonts.set(qn('w:ascii'), latin)
    rfonts.set(qn('w:hAnsi'), latin)
    rfonts.set(qn('w:eastAsia'), ea)


def style_font(style, latin, ea, size):
    style.font.name = latin
    style.font.size = Pt(size)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts')
        rpr.append(rfonts)
    rfonts.set(qn('w:ascii'), latin)
    rfonts.set(qn('w:hAnsi'), latin)
    rfonts.set(qn('w:eastAsia'), ea)


def add_hyperlink(paragraph, url, text):
    part = paragraph.part
    r_id = part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)
    new_run = OxmlElement('w:r')
    rpr = OxmlElement('w:rPr')
    color = OxmlElement('w:color')
    color.set(qn('w:val'), '1F3864')
    rpr.append(color)
    underline = OxmlElement('w:u')
    underline.set(qn('w:val'), 'single')
    rpr.append(underline)
    rfonts = OxmlElement('w:rFonts')
    rfonts.set(qn('w:ascii'), BODY_LATIN)
    rfonts.set(qn('w:hAnsi'), BODY_LATIN)
    rfonts.set(qn('w:eastAsia'), BODY_EA)
    rpr.append(rfonts)
    new_run.append(rpr)
    t = OxmlElement('w:t')
    t.text = text
    t.set(qn('xml:space'), 'preserve')
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


INLINE_RE = re.compile(r'(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))')


def add_inline(paragraph, text, size=None, bold=False):
    for piece in INLINE_RE.split(text):
        if not piece:
            continue
        if piece.startswith('**') and piece.endswith('**'):
            run = paragraph.add_run(piece[2:-2])
            run.bold = True
        elif piece.startswith('`') and piece.endswith('`'):
            run = paragraph.add_run(piece[1:-1])
            set_run_font(run, CODE_FONT, CODE_FONT)
            run.font.size = Pt((size or 11) - 1.5)
        elif piece.startswith('[') and '](' in piece and piece.endswith(')'):
            label, url = piece[1:-1].split('](', 1)
            add_hyperlink(paragraph, url, label)
            continue
        else:
            run = paragraph.add_run(piece)
        set_run_font(run)
        if size:
            run.font.size = Pt(size)
        if bold:
            run.bold = True


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    tc_pr.append(shd)


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement('w:' + edge)
        el.set(qn('w:val'), 'single')
        el.set(qn('w:sz'), '6')
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), BORDER)
        borders.append(el)
    tbl_pr.append(borders)


def set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement('w:tblHeader'))


def set_fixed_layout(table):
    tbl_pr = table._tbl.tblPr
    layout = OxmlElement('w:tblLayout')
    layout.set(qn('w:type'), 'fixed')
    tbl_pr.append(layout)


def apply_column_widths(table, rows, total_inches=6.5):
    """按各列内容的相对长度分配列宽，避免 Word 把列挤成一样宽或过窄。"""
    cols = max(len(r) for r in rows)
    lengths = []
    for c in range(cols):
        longest = max((len(r[c]) for r in rows if c < len(r)), default=1)
        lengths.append(max(longest, 4))
    total = float(sum(lengths))
    widths = []
    for value in lengths:
        width = total_inches * value / total
        widths.append(min(max(width, 0.7), total_inches - 0.7 * (cols - 1)))
    scale = total_inches / sum(widths)
    widths = [w * scale for w in widths]
    for c, width in enumerate(widths):
        for row in table.rows:
            row.cells[c].width = Inches(round(width, 3))


def cell_text(cell, text, size=10, bold=False, color=None, align=None):
    cell.text = ''
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_before = Pt(1.5)
    paragraph.paragraph_format.space_after = Pt(1.5)
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    if align is not None:
        paragraph.alignment = align
    add_inline(paragraph, text, size=size, bold=bold)
    for run in paragraph.runs:
        if bold:
            run.bold = True
        if color:
            run.font.color.rgb = RGBColor.from_string(color)


def add_code_block(doc, lines):
    paragraph = doc.add_paragraph()
    pf = paragraph.paragraph_format
    pf.space_before = Pt(4)
    pf.space_after = Pt(10)
    pf.left_indent = Inches(0.18)
    pf.line_spacing = 1.05
    for index, line in enumerate(lines):
        run = paragraph.add_run(line)
        set_run_font(run, CODE_FONT, CODE_FONT)
        run.font.size = Pt(9.5)
        if index != len(lines) - 1:
            run.add_break()


def is_table_divider(line):
    return bool(re.fullmatch(r'\|[\s:\-|]+\|', line.strip())) and '-' in line


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


ENTRY_RE = re.compile(
    r'^(?P<word>[^\s/\[（(]+)\s*(?P<phon>[/\[][^/\]\n]{1,40}[/\]])?\s*(?P<mean>.*)$'
)


def parse_entry(text):
    """把 `- terrain /təˈreɪn/ 地形；地势` 拆成单词、音标、释义。"""
    text = text.strip().lstrip('-*').strip()
    match = ENTRY_RE.match(text)
    if not match:
        return text, '', ''
    word = match.group('word').strip('*`')
    return word, (match.group('phon') or '').strip(), match.group('mean').strip()


def set_cant_split(row):
    """让一条词表内容不要被分页截断。"""
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement('w:cantSplit'))


def set_row_min_height(row, points):
    """行高下限，允许被内容撑高（释义换行时才不会被裁掉）。"""
    tr_pr = row._tr.get_or_add_trPr()
    height = tr_pr.find(qn('w:trHeight'))
    if height is None:
        height = OxmlElement('w:trHeight')
        tr_pr.append(height)
    height.set(qn('w:val'), str(int(points * 20)))
    height.set(qn('w:hRule'), 'atLeast')


def add_word_list(doc, entries, size=9.5, columns=2):
    """把单词表排成多列小字：单词（大一点）+ 音标（灰）+ 释义（更小）。

    释义可以写到 20 字上下，放不下会自动换行，换行处留出悬挂缩进对齐。
    """
    if not entries:
        return
    rows = -(-len(entries) // columns)
    table = doc.add_table(rows=rows, cols=columns)
    table.autofit = False
    set_fixed_layout(table)
    per_column = rows
    width = 6.5 / columns
    for index, entry in enumerate(entries):
        column = index // per_column
        row_index = index % per_column
        if column >= columns:
            break
        cell = table.cell(row_index, column)
        cell.width = Inches(round(width, 3))
        word, phon, mean = parse_entry(entry)
        paragraph = cell.paragraphs[0]
        for run in list(paragraph.runs):
            run._element.getparent().remove(run._element)
        pf = paragraph.paragraph_format
        pf.space_before = Pt(0.5)
        pf.space_after = Pt(0.5)
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
        pf.left_indent = Inches(0.15)
        pf.first_line_indent = Inches(-0.15)
        run = paragraph.add_run(word)
        set_run_font(run)
        run.bold = True
        run.font.size = Pt(size)
        if phon:
            run = paragraph.add_run(' ' + phon)
            set_run_font(run)
            run.font.size = Pt(size - 1)
            run.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
        if mean:
            add_inline(paragraph, ' ' + mean, size=size)
    for row in table.rows:
        set_cant_split(row)
        set_row_min_height(row, size + 3)


def render(md_path, out_path, doc_title, subtitle=None):
    lines = open(md_path, encoding='utf-8-sig').read().split('\n')
    doc = Document()

    style_font(doc.styles['Normal'], BODY_LATIN, BODY_EA, 11)
    doc.styles['Normal'].paragraph_format.space_after = Pt(8)
    doc.styles['Normal'].paragraph_format.line_spacing = 1.2
    style_font(doc.styles['Title'], BODY_LATIN, BODY_EA, 24)
    doc.styles['Title'].font.color.rgb = RGBColor(0, 0, 0)
    for name, size in (('Heading 1', 15), ('Heading 2', 12.5), ('Heading 3', 11.5)):
        style_font(doc.styles[name], BODY_LATIN, BODY_EA, size)
        doc.styles[name].font.color.rgb = RGBColor(0, 0, 0)
        doc.styles[name].font.bold = True
        doc.styles[name].paragraph_format.space_before = Pt(16)
        doc.styles[name].paragraph_format.space_after = Pt(6)

    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    for attr in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'):
        setattr(section, attr, Inches(1))

    title_paragraph = doc.add_paragraph(style='Title')
    title_run = title_paragraph.add_run(doc_title)
    set_run_font(title_run)
    title_run.font.size = Pt(24)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(0, 0, 0)
    if subtitle:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(14)
        run = paragraph.add_run(subtitle)
        set_run_font(run)
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor(0x40, 0x40, 0x40)

    index = 0
    skipped_first_h1 = False
    in_word_list = False
    small_body = False
    pending_entries = []

    def flush_word_list():
        if pending_entries:
            add_word_list(doc, list(pending_entries))
            pending_entries.clear()

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()

        if stripped.startswith('<!--'):
            index += 1
            continue
        if not stripped:
            index += 1
            continue

        if stripped.startswith('```'):
            flush_word_list()
            block = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith('```'):
                block.append(lines[index].rstrip())
                index += 1
            index += 1
            add_code_block(doc, block)
            continue

        if stripped.startswith('|') and index + 1 < len(lines) and is_table_divider(lines[index + 1]):
            flush_word_list()
            rows = [split_row(stripped)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith('|'):
                rows.append(split_row(lines[index]))
                index += 1
            cols = max(len(r) for r in rows)
            table = doc.add_table(rows=0, cols=cols)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False
            set_table_borders(table)
            set_fixed_layout(table)
            for r_i, row in enumerate(rows):
                cells = table.add_row().cells
                if r_i == 0:
                    set_repeat_header(table.rows[0])
                for c_i in range(cols):
                    value = row[c_i] if c_i < len(row) else ''
                    if r_i == 0:
                        shade(cells[c_i], HEADER_FILL)
                        cell_text(cells[c_i], value, size=10, bold=True, color='FFFFFF',
                                  align=WD_ALIGN_PARAGRAPH.CENTER)
                    else:
                        if r_i % 2 == 0:
                            shade(cells[c_i], ALT_FILL)
                        cell_text(cells[c_i], value, size=9.5, align=WD_ALIGN_PARAGRAPH.LEFT)
            apply_column_widths(table, rows)
            spacer = doc.add_paragraph()
            spacer.paragraph_format.space_after = Pt(4)
            continue

        if stripped.startswith('#'):
            level = len(stripped) - len(stripped.lstrip('#'))
            text = stripped[level:].strip()
            if level == 1 and not skipped_first_h1:
                skipped_first_h1 = True
                index += 1
                continue
            flush_word_list()
            if level <= 2:
                in_word_list = '单词表' in text
                small_body = '翻译' in text
            if small_body and level >= 3:
                paragraph = doc.add_paragraph()
                paragraph.paragraph_format.space_before = Pt(7)
                paragraph.paragraph_format.space_after = Pt(3)
                add_inline(paragraph, text, size=10, bold=True)
                index += 1
                continue
            style = {1: 'Heading 1', 2: 'Heading 2'}.get(level, 'Heading 3')
            paragraph = doc.add_paragraph(style=style)
            add_inline(paragraph, text)
            index += 1
            continue

        if stripped.startswith('---'):
            index += 1
            continue

        if stripped.startswith('> '):
            flush_word_list()
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.left_indent = Inches(0.2)
            paragraph.paragraph_format.space_before = Pt(6)
            paragraph.paragraph_format.space_after = Pt(10)
            add_inline(paragraph, stripped[2:], size=10)
            for run in paragraph.runs:
                run.italic = True
                run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
            index += 1
            continue

        bullet = re.match(r'^[-*]\s+(.*)$', stripped)
        numbered = re.match(r'^(\d+)[.)]\s+(.*)$', stripped)
        if bullet or numbered:
            text = bullet.group(1) if bullet else numbered.group(2)
            if in_word_list and bullet:
                pending_entries.append(text)
                index += 1
                continue
            style = 'List Bullet' if bullet else 'List Number'
            paragraph = doc.add_paragraph(style=style)
            paragraph.paragraph_format.space_after = Pt(4)
            add_inline(paragraph, text, size=9 if small_body else None)
            index += 1
            continue

        flush_word_list()
        paragraph = doc.add_paragraph()
        if small_body:
            paragraph.paragraph_format.space_after = Pt(5)
            paragraph.paragraph_format.line_spacing = 1.15
            add_inline(paragraph, stripped, size=9)
            index += 1
            continue
        add_inline(paragraph, stripped)
        index += 1

    flush_word_list()
    doc.save(out_path)
    print('saved', out_path)


if __name__ == '__main__':
    render(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
