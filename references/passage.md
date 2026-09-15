# 用错词写记忆材料

## 目标

把这批标错的词放进能想起的语境里，读一遍就记住"这个词长什么样、用在什么地方"。默认写成**雅思阅读**那种学术说明文，因为雅思阅读本身就是考"在不熟悉的文章里认出词"，风格对上了，记忆和实战是一件事。

但风格是外壳，第一目标是**读得进去**。文章要让人一口气读完不卡壳，读完能说出"这篇讲了什么、分几块讲"。难词已经够多了，句子结构必须简单。

## 难度：让人一遍读懂

上一版失败的地方就是句子太绕。照下面这几条写，写完逐条检查：

- **句子短。**平均 12–18 个词，单句不超过 30 个词。
- **一句最多一个从句。**不要写"which 里面套 that"这种两层结构；想加信息就另起一句。
- **一句里的目标词不超过两个。**一条句子里塞三四个生词，读者会直接放弃。一段 4–6 个目标词比较合适。
- **除目标词外全用常见词。**不要用另一个生僻词去解释一个生僻词。
- **专业概念当场解释。**第一次出现时用同位语带一下，例如 `a **propeller**, a device that pushes a ship forward`。
- **句式别雷同。**不要连续三段都用 `By the 1830s, ...` 开头。
- **写不通就拆句。**宁可句子碎一点，也不要一句话读两遍才懂。

自检：通读时只要有一句需要回头重看，就把那句改短或拆开。

## 逻辑与梗概

上一版另一个问题是东一段西一段，没有主线。按下面的骨架写：

**开头段 2–3 句，给出梗概。**第一句交代背景，第二句是导航句，明确告诉读者这篇讲什么、按什么顺序讲，例如：

> This passage describes how steam power changed coastal shipping. It first explains why sails were slow, then describes the engines that replaced them, and finally shows what happened to cost and speed.

**每一节的第一句是主题句。**只看小标题和每段第一句，应该能串出一条完整的线。**梗概测试**：把所有小标题和每段第一句摘出来连起来读，如果读得通，文章的逻辑就成立了。

**小节的顺序要能说出是什么关系**，而且要让人看出来：

- 时间先后：背景 → 早期尝试 → 转折 → 后来 → 现在
- 因果链：问题 → 原因 → 解决办法 → 结果
- 由浅入深：是什么 → 怎么运作 → 有什么影响
- 对比：一种做法 → 另一种做法 → 两者差别

小标题里体现顺序，例如 "1 Background"、"2 The first attempt"、"3 What went wrong"、"4 A better method"、"5 Results"。

**每两段之间至少有一处显式衔接**，用时间词、因果词或指代前文的名词短语（After this, As a result, These changes, By contrast）。不要指望读者自己脑补转折。

**结尾段 2–3 句收回主线。**可以说清最终结果或长期影响，不复述细节、不做价值判断、不喊口号。可以用 `Taken together, ...`、`In the long run, ...` 这类开头。

## 雅思阅读风格怎么写

体裁上是一篇学术说明文，不是散文、不是故事、不是词表造句。照下面的特征写：

**标题与篇幅**

- 标题用中性名词短语，例如 "The Decline of Coastal Shipping"、"How Birds Adapt to Cities"；不要问句，不要口号。
- 篇幅按词数定：二十来个词写 400–600 词，五十个左右写 700–1000 词，一百个上下写 1200–1800 词。小节数跟着增加，一百个词配五到七节，每节 200–300 词。词数超过 120 个时，先问用户要一篇长的还是拆成两三篇短的。
- 开头段给背景并交代全文范围；中间小节按上面那几种顺序展开，至少有一个具体的例子、地点或研究数据；结尾段收回整体。

**语言特征**（这是"雅思味"的核心）

- 被动语态与无人称主语：It is estimated that…, The samples were collected from…
- 名词化：the introduction of, the decline in, an increase in
- 让步与对比：although, whereas, while, despite, nevertheless
- 因果与推断：as a result, thereby, which in turn
- 有保留的表达：appears to, is thought to, may well, suggests
- 用数据和举例代替空泛评价：a survey of 300 farmers, for instance
- 不用第一人称，不用口语缩写，不用情绪化的形容词
- 复杂名词短语、分词结构和定语从句是"雅思味"的来源，但**一句最多用一个**，不要叠着用

样例段落，用来校准难度和语气：

> Steam power reached coastal shipping slowly. In the 1820s most goods still travelled by sail, because early engines were heavy and burned too much coal. Engineers then built a smaller **apparatus** that could be fitted into an old wooden hull. As a result, a ship could leave the **dock** within hours instead of waiting for a favourable wind. The change was gradual, but it never reversed.

这段五句话，最长 20 个词，两个目标词，一句一个从句。写每一段都按这个尺度来。

**目标词怎么放**

- 平均每 12–18 个词出现一个目标词，读起来像生词本来就在文章里，而不是硬塞进去。写完用 `check_passage.py` 看实际密度，超过 18 就删掉些铺垫句。
- 优先放进解释性从句、并列名词短语、数据句和对比句里；词性不合就换一句重写，不要写出语法错误或怪句子。
- 目标词加粗，标题和小标题不加粗。
- 词多的时候，先把词按主题粗分到各节（每节 15–25 个），再逐节写；比边写边想下一句更难漏词，也更容易让每个词落到合适的语境里。

## 必须做到的两件事

1. **每个词都要出现在文章里**，允许时态和单复数变化（`weep→wept`、`swell→swelled`、`withhold→withheld`、`levy→levied` 等）。写完用脚本核对，不要凭印象说"都写进去了"。
2. **每段后面紧跟该段的中文译文和该段用到的生词**，顺序是：英文段落 → 中文译文 → 生词清单。生词按在段内出现的先后排，条目写成 `单词 /英式音标/ 释义`，例如 `cottage /ˈkɒtɪdʒ/ 小屋；村舍`、`plumb /plʌm/ 垂直的；探测深度`。这样读一段就能立刻对照译文、顺手过一遍词，比把词表堆在文末好用。

   条目写原形；正文里用了变形时不必逐条加括号（两列排不下），在全文末尾补一行说明即可，例如「文中用了这些变形：wept、swelled、hybridising」。每个词一到两个常用义项，一般 20 字以内；放不下会自动换行，不用为了凑一行把常用义项砍掉。中文释义和音标接口都拿不到，要自己写；不要搬词典的长解释，也不要用只在本文成立的临时义。

核对脚本有两个用法：

```bash
# 先出骨架：按正文出现顺序列出原形，把释义补在问号处
py -3 scripts/check_passage.py --words work/words.json --md work/src.md --skeleton

# 写完核对：漏词、多余的加粗、重复加粗、词条收全与顺序
py -3 scripts/check_passage.py --words work/words.json --md work/src.md
```

它会把变形还原成原形再比对，所以 `wept`、`lorries`、`hybridising` 这类写法不会误报；退出码非 0 说明还有问题，改到通过为止。

## 什么时候可以换风格

雅思风格是默认，不是铁律。如果这批词里全是口语、动作或情绪类的词，硬写成学术说明文会又别扭又难记，那就换成更顺手的写法（连成故事、对话、同语义场分组短句），并在交付时说一句为什么换。判断标准只有一个：哪种写法更容易记住这批词。

如果用户明确要别的风格（故事、口语、商务、小说片段等），以用户要求为准。换风格时，"句子短、有主线、有梗概"这三条仍然适用。

## 交付

- 成品给 Word 和 PDF 两份，内容都是「每段英文 + 该段中文译文 + 该段生词」交替往下排。不要加导语、使用说明、数据来源说明、落款；用户明确说不要翻译时才省掉译文。
- 做法：先写一份 Markdown 中间稿放在本次对话目录的 `work/`，再转换：

  ```bash
  py -3 scripts/md2docx.py work/src.md "outputs/错词短文.docx" "标题"
  powershell -ExecutionPolicy Bypass -File scripts/docx2pdf.ps1 `
    -Docx "outputs/错词短文.docx" -Pdf "outputs/错词短文.pdf"
  ```

  `docx2pdf.ps1` 调用本机 Microsoft Word 导出，排版和 Word 里完全一致；没装 Word 就直接报错，这时交付 Word 并说明一下。转换完可以抽查一下 PDF 能打开、页数正常。
- 中间稿的写法：文章标题写在命令行参数里，正文用 `##` 做小节标题；英文段落直接写，中文译文单独一段（脚本按"含汉字、几乎不含英文"自动认出来，排成 9 磅小字），该段的生词用 `- 单词 /音标/ 释义` 一串列表写在译文后面（脚本自动排成两列小字）。`md2docx.py` 还支持 `**加粗**`、表格、引用和代码块。
- 需要 python-docx。`py -3 -m pip install python-docx` 装上即可；已经装好 python-docx 的解释器直接用。
- 用户自用材料，不需要渲染和逐页排版检查；生成后确认文件能打开、内容齐全即可。
- 中间稿和临时文件放 `work/`，最终 Word 放到该对话目录的 `outputs/`。用户指定了别的路径就以用户说的为准。
- 文件名带上日期区间，如 `错词短文-9月11-12日.docx` / `.pdf`；文章标题用英文，中文只出现在译文和生词释义里。
- 生词块会自动排成两列：单词 9.5 磅加粗、音标 8.5 磅灰字、中文释义与单词同字号；释义放不下会自动换行并悬挂缩进，每条不跨页。块的前后会自动留出间距（前 10 磅、后 12 磅），不会和上下段落贴在一起。

## 文风

客观、克制、具体。像给一个已经知道大概背景的同学讲这件事：说人话，不用炫技的句式，不堆抽象名词，也不对读者说话。不要"赋能、打造、助力、见证"这类词。中文小标题和单词释义用日常说法。
