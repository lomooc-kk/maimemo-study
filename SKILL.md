---
name: maimemo-study
description: 通过墨墨开放 API 取用背单词数据并产出复习材料：挑出某段时间标记为不熟或忘记的单词、据此创作背诵短文、把例句助记释义云词本写回账号。用户提到墨墨、背单词、错词整理、单词小短文或学习记录时使用；与墨墨账号无关的一般英语写作不要用。
---

# 墨墨背单词数据整理

用户用墨墨背单词，日常需要复盘的场景就三个：看某几天哪些词没记住、把这些词串成能背的短文、把新写的例句助记存回账号。这个技能负责调用墨墨开放 API 完成它们。

## 开工前

令牌按这个顺序取：命令行 `--token` → 环境变量 `MAIMEMO_TOKEN` → 文件 `~/.codex/maimemo_token`。三个地方都没有就问用户要一个，别自己编。令牌等于账号钥匙，不要写进交付物或日志。

脚本用 `py -3` 运行，只依赖 Python 标准库，不用装包。

接口根地址是 `https://open.maimemo.com/open/api/v1`，每次请求带 `Authorization: Bearer 令牌`。返回统一是 `{"success": true, "data": {...}}` 或 `{"success": false, "errors": [...]}`。

## 一、挑出某几天的错词

```bash
py -3 scripts/collect_review_words.py --days 3
py -3 scripts/collect_review_words.py --date 2026-09-12
py -3 scripts/collect_review_words.py --from 2026-09-01 --to 2026-09-13 --out work/words.json
```

脚本会输出中文汇总（区间、每天多少词、不熟与忘记各多少、按结果分组的词表），`--out` 可以同时落一份 JSON 给后面核对用。它只调只读接口，不会改账号里的数据。

几个必须知道的前提：

- `last_response` 是这个词**最近一次**复习的结果，`last_study_date` 是最近一次复习的日期。所以"某天标了不熟"实际含义是"最近一次复习发生在那天且结果是 不熟/忘记"。同一个词后来答对了就不会再出现，这正是想要的效果。
- 当天在 App 里的结果要等同步之后才查得到。整个区间都为空时，先请用户打开 App 同步一次，再重跑；如果只是区间里"今天"那一段是 0、前一天有记录，那多半是当天还没背或还没同步，交付时说一句就行，不用反复重跑。
- 单次请求最多返回 1000 条，脚本按 30 天窗口扫描"下次复习时间"并自动合并、必要时对半拆分，所以一次运行会发十几次请求。这是接口本身的限制，不要改成单次大请求。
- 如果只想看今天要背的、而不是复盘错词，用 `maimemo.ps1 today`。

## 二、把错词写成记忆材料

动手前读 [references/passage.md](references/passage.md)。默认写成雅思阅读那种学术说明文：中性标题、若干个小节、被动语态与名词化、有保留的表述，目标词像生词本来就在文章里一样自然嵌入并加粗。这批词明显不适合学术文体时（比如全是口语动作词）可以换写法，交付时说明一句。

篇幅跟着词数走，不是固定值：二三十个词写 400–600 词，五十来个写 800–1100 词，一百个上下写 1500–2000 词、六节左右。平均每 10 个词出现一个目标词最舒服，超过 18 就说明铺垫太多。一次超过 120 个词时先问用户要一篇长的还是拆成两三篇短的。

中间稿按「英文段落 → 该段中文译文 → 该段生词」交替写，用脚本核对，不要凭印象：

```bash
# 先拿词条骨架（按正文出现顺序排好原形），照着填释义
py -3 scripts/check_passage.py --words work/words.json --md work/src.md --skeleton

# 写完核对：漏词、多余的加粗、重复加粗、词条收全与顺序
py -3 scripts/check_passage.py --words work/words.json --md work/src.md
```

退出码非 0 就改到通过为止；它还会报有几条生词缺音标。中文释义和音标接口都不提供，都得自己写，条目写成 `单词 /英式音标/ 释义`（释义放不下会自动换行，不用为凑一行砍义项）。成品给 Word 和 PDF 两份，文件名带日期区间：

```bash
py -3 scripts/md2docx.py work/src.md "outputs/错词短文-9月11-12日.docx" "标题"
powershell -ExecutionPolicy Bypass -File scripts/docx2pdf.ps1 -Docx "outputs/错词短文-9月11-12日.docx" -Pdf "outputs/错词短文-9月11-12日.pdf"
```

`md2docx.py` 会把中文段落排成 9 磅小字、把生词块排成两列小字（单词 9.5 磅加粗、音标 8.5 磅灰字、释义同字号，每条不跨页）；`docx2pdf.ps1` 用本机装的 Word 导出 PDF，没装就只交 Word 并说明一句。

## 三、把内容写回账号

用 `scripts/maimemo.ps1`，它对每个接口都有一层封装：

```bash
powershell -ExecutionPolicy Bypass -File scripts/maimemo.ps1 vocab <单词>
powershell -ExecutionPolicy Bypass -File scripts/maimemo.ps1 today -Limit 20
powershell -ExecutionPolicy Bypass -File scripts/maimemo.ps1 progress
powershell -ExecutionPolicy Bypass -File scripts/maimemo.ps1 phrase-add <vocId> -Content "英文例句" -Interpretation "中文释义"
powershell -ExecutionPolicy Bypass -File scripts/maimemo.ps1 note-add <vocId> -Content "谐音：哈喽"
powershell -ExecutionPolicy Bypass -File scripts/maimemo.ps1 interp-add <vocId> -Content "你好；喂"
powershell -ExecutionPolicy Bypass -File scripts/maimemo.ps1 notepad-new -Title "标题" -Content "内容"
powershell -ExecutionPolicy Bypass -File scripts/maimemo.ps1 raw GET "/memo/vocabulary?spelling=hello"
```

加 `-DryRun` 只打印将要发出的请求，不发出去。拿不准参数时先跑一遍。

写入前先跟用户确认，因为这些都是往真实账号里加内容（每天上限 600 条）。写完要能说清创建了什么、ID 是什么，方便删除；接口提供 DELETE，删除是可逆的。

**不要碰改动学习计划的接口**（`add_words`、`advance_study`），除非用户明确说要把词加进计划或提前复习——它们会改变用户接下来的复习安排。

## 四、查接口细节

端点清单、必填字段、常见报错、记忆卡正文语法，都在 [references/api.md](references/api.md)。遇到没见过的报错先去那里对一遍再动手。

记忆卡（Markji）那组接口目前对这个账号返回权限不足，需要用户在 App 里联系开发者开通；背单词那组完全可用。

## 维护这个技能

这个目录同时是 GitHub 私有仓库 `lomooc-kk/maimemo-study` 的工作副本，`origin` 已经配好，改完直接提交推送：

```bash
cd "$HOME/.codex/skills/maimemo-study"
git add -A
git commit -m "更新说明"
git push
```

改脚本后要真跑一次确认能用（`collect_review_words.py` 需要令牌；`maimemo.ps1` 可以用 `-DryRun` 空跑；`check_passage.py` 不用令牌，拿任意一份 words.json 加短文跑一次，漏词和顺序两种情况都验一下；`docx2pdf.ps1` 要本机有 Word，转一份出来看页数对不对）。PowerShell 脚本必须存成带 BOM 的 UTF-8——用编辑器或脚本改过之后检查一下开头是不是还有 BOM，否则 Windows PowerShell 会把中文注释读成乱码并直接语法报错。令牌只放在 `~/.codex/maimemo_token`，永远不要提交进仓库。
