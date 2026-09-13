# 用错词写记忆材料

## 目标

把这批标错的词放进能想起的语境里，让人读一遍就记住"这个词长什么样、用在什么地方"。默认写成**雅思阅读**那种学术说明文，因为雅思阅读本来就是考"在不熟悉的文章里认出词"，风格对上了，记忆和实战是一件事。

## 雅思阅读风格怎么写

体裁上是一篇学术说明文，不是散文、不是故事、不是词表造句。照下面的特征写：

**标题与结构**

- 标题用中性名词短语，例如 "The Decline of Coastal Shipping"、"How Birds Adapt to Cities"；不要问句，不要口号。
- 篇幅按词数定：二十来个词写 400–600 词，五十个左右写 800–1100 词，一百个上下写 1500–2000 词。小节数跟着增加，一百个词配五到七节很正常，每节 200–350 词，配简短小标题。词数超过 120 个时，先问用户要一篇长的还是拆成两三篇短的。
- 开头段给背景并交代全文范围；中间小节按时间顺序、因果、分类或对比展开，中间至少有一个具体的例子、地点或研究数据；结尾段收回整体，不做价值判断、不喊口号。

**语言特征**（这是"雅思味"的核心）

- 被动语态与无人称主语：It is estimated that…, The samples were collected from…
- 名词化：the introduction of, the decline in, an increase in
- 复杂名词短语带后置定语：a species that nests in…, the technique used by…
- 让步与对比：although, whereas, while, despite, nevertheless
- 因果与推断：as a result, thereby, which in turn
- 有保留的表达：appears to, is thought to, may well, suggests
- 分词与定语从句：originally built to…, having been introduced…
- 用数据和举例代替空泛评价：a survey of 300 farmers, for instance
- 不用第一人称，不用口语缩写，不用情绪化的形容词

样例段落，用来校准语气：

> The introduction of steam power to coastal shipping is often described as a single moment of change, yet the transition took decades. Whereas early engines were too heavy for small vessels, later designs allowed a **compatible** **apparatus** to be fitted to existing hulls, and freight costs fell accordingly. It appears that shipowners adopted the new technology not because they welcomed risk, but because insurance rates left them little choice.

**目标词怎么放**

- 平均每 10 个词上下出现一个目标词，读起来像生词本来就在文章里，而不是硬塞进去。写完用 `check_passage.py` 看实际密度，超过 18 就删掉些铺垫句。
- 优先放进解释性从句、并列名词短语、数据句和对比句里；词性不合就换一句重写，不要写出语法错误或怪句子。
- 目标词加粗，标题和小标题不加粗。
- 词多的时候，先把词按主题粗分到各节（每节 15–25 个），再逐节写；比边写边想下一句更难漏词，也更容易让每个词落到合适的语境里。

## 必须做到的两件事

1. **每个词都要出现在文章里**，允许时态和单复数变化（`weep→wept`、`swell→swelled`、`withhold→withheld`、`levy→levied` 等）。写完用脚本核对，不要凭印象说"都写进去了"。
2. **单词表跟在文章最后**，按词在文中出现的顺序排列，条目写成 `单词 /英式音标/ 释义`，例如 `cottage /ˈkɒtɪdʒ/ 小屋；村舍`、`plumb /plʌm/ 垂直的；探测深度`。条目写原形；正文里用了变形时，不必逐条加括号（两列排不下），在词表末尾补一行说明即可，例如「文中用了这些变形：wept、swelled、hybridising」。每个词一到两个常用义项，一般 20 字以内；放不下会自动换行，不用为了凑一行把常用义项砍掉。中文释义和音标接口都拿不到，要自己写；不要搬词典的长解释，也不要用只在本文成立的临时义。

核对脚本有两个用法：

```bash
# 先出骨架：按正文出现顺序列出原形，把释义补在问号处
py -3 scripts/check_passage.py --words work/words.json --md work/src.md --skeleton

# 写完核对：漏词、多余的加粗、重复加粗、词表收词与顺序
py -3 scripts/check_passage.py --words work/words.json --md work/src.md
```

它会把变形还原成原形再比对，所以 `wept`、`lorries`、`hybridising` 这类写法不会误报；退出码非 0 说明还有问题，改到通过为止。

## 什么时候可以换风格

雅思风格是默认，不是铁律。如果这批词里全是口语、动作或情绪类的词，硬写成学术说明文会又别扭又难记，那就换成更顺手的写法（连成故事、对话、同语义场分组短句），并在交付时说一句为什么换。判断标准只有一个：哪种写法更容易记住这批词。

如果用户明确要别的风格（故事、口语、商务、小说片段等），以用户要求为准。

## 交付

- 成品是 Word（`.docx`），默认三部分，按这个顺序：**文章正文**、**单词表**、**全文中文翻译**。中文翻译用 `## 中文翻译` 起，内部按 `### 小标题` 分段，与英文正文的段落一一对应；脚本会把它排成 9 磅小字（小标题 10 磅加粗），跟在词表后面方便对照自查。不要加导语、使用说明、数据来源说明、落款；用户明确说不要翻译时才省掉。
- 做法：先写一份 Markdown 中间稿放在本次对话目录的 `work/`，再转换：

  ```bash
  py -3 scripts/md2docx.py work/src.md "outputs/错词短文.docx" "标题"
  ```

  `md2docx.py` 支持 `#/##/###` 标题、`**加粗**`、表格、列表和代码块。文章标题写在文件名参数里，正文用 `##` 做小节标题。
- 需要 python-docx。这台机器上装好的解释器是
  `C:\Users\江润\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`，
  用其它解释器时先 `py -3 -m pip install python-docx`。
- 用户自用材料，不需要渲染和逐页排版检查；生成后确认文件能打开、内容齐全即可。
- 中间稿和临时文件放 `work/`，最终 Word 放到该对话目录的 `outputs/`。用户指定了别的路径就以用户说的为准。
- 文件名带上日期区间，如 `错词短文-9月11-12日.docx`；文章标题用英文，单词表那一节的小标题用中文「单词表」。
- 「单词表」小节会自动排成两列：单词 9.5 磅加粗、音标 8.5 磅灰字、中文释义与单词同字号；释义放不下会自动换行并悬挂缩进，每条不跨页。

## 文风

客观、克制、具体。不要"赋能、打造、助力、见证"这类词，不要为了显得高级堆抽象名词，也不要在正文里对读者说话。中文小标题和单词表释义用日常说法。
