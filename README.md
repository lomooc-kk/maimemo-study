# maimemo-study

一个给 Codex 用的技能：通过**墨墨开放 API**取自己的背单词数据，挑出某几天标记为「不熟 / 忘记」的词，写成一篇便于记忆的雅思风格短文，最后连单词表一起交给你 Word 和 PDF。

如果你是来用它的，需要准备两样东西：**你自己的墨墨令牌**，以及一台能跑 Python 的电脑。仓库里不含任何人的令牌。

## 它能做什么

1. **挑错词**：指定某天或最近几天，列出最近一次复习结果是「不熟」「忘记」的单词，附结果、日期、复习次数。
2. **写记忆材料**：把这些词写成一篇短文，文中目标词加粗，每段后面跟中文译文和该段生词（带词性、美式音标和一条记忆钩子）。风格以「读得进去」为先：句子短、有梗概、有主线；**体裁和场景每篇轮换**（见 `references/style-log.md`），优先编进你自己熟悉的场景，不重复上一篇的样子。**难度分简单 / 中等 / 困难三档**，写作前会先问你选哪一档，不问就按中等写。
3. **写回账号**：把新写的例句、助记、自定义释义、云词本写进墨墨账号（写入前会先跟你确认）。

## 安装

克隆到 Codex 的技能目录（Windows 上是 `%USERPROFILE%\.codex\skills`）：

```bash
git clone https://github.com/lomooc-kk/maimemo-study.git "$HOME/.codex/skills/maimemo-study"
```

装完在 Codex 里新开一个对话，技能列表里就会出现 `maimemo-study`（技能在对话开始时加载）。之后直接说需求就行：

> 整理我最近三天的错词，写一篇雅思风格的文章（简单一点）。
>
> 把 9 月 12 号标错的那批词做成一篇短文。
>
> 帮我看看今天的进度，再把明天要复习的词数统计一下。

也可以显式说 `$maimemo-study`。

## 准备你自己的令牌

两个入口任选一个：

- 墨墨背单词 App → 我的 → 更多设置 → 实验功能 → 开放 API
- 浏览器登录后打开 <https://open.maimemo.com/open/api/v1/tokens/openapi>

令牌按「命令行参数 → 环境变量 `MAIMEMO_TOKEN` → 文件 `~/.codex/maimemo_token`」的顺序读取。推荐存成文件，一次就好：

```powershell
# 当前窗口生效
$env:MAIMEMO_TOKEN = "你的令牌"

# 永久生效（重开终端后有效）
setx MAIMEMO_TOKEN "你的令牌"

# 或者写进文件
Set-Content -Path "$HOME\.codex\maimemo_token" -Value "你的令牌" -Encoding utf8 -NoNewline
```

令牌相当于账号钥匙，别贴到聊天里、别提交进仓库、别放进截图。

## 依赖

| 组件 | 说明 |
|---|---|
| Codex | 技能是给 Codex 用的；它读 `SKILL.md` 和 `references/` |
| Windows PowerShell | 系统自带，`scripts/maimemo.ps1` 和 `docx2pdf.ps1` 用它 |
| Python 3 | `py -3` 即可，抓取与校验脚本只用标准库 |
| python-docx | 生成 Word 需要：`py -3 -m pip install python-docx` |
| Microsoft Word | 可选。装了才能把 Word 转成 PDF，没装就只交付 Word |

## 直接用脚本

不经过对话，也可以自己跑：

```bash
# 最近三天标为不熟/忘记的词，同时存一份 JSON
py -3 scripts/collect_review_words.py --days 3 --out work/words.json

# 写完短文后核对：漏词、多余的加粗、词条顺序
py -3 scripts/check_passage.py --words work/words.json --md work/src.md

# 转成 Word，再转 PDF
py -3 scripts/md2docx.py work/src.md "outputs/错词短文.docx" "The River Town"
powershell -ExecutionPolicy Bypass -File scripts/docx2pdf.ps1 -Docx "outputs/错词短文.docx" -Pdf "outputs/错词短文.pdf"

# 看今天的进度，或把词加进学习计划
powershell -ExecutionPolicy Bypass -File scripts/maimemo.ps1 progress
powershell -ExecutionPolicy Bypass -File scripts/maimemo.ps1 today -Limit 20
```

`maimemo.ps1 help` 会列出所有命令，加 `-DryRun` 只打印请求不发送，适合先验证参数。调用接口有频率限制（10 秒 20 次、60 秒 40 次），脚本里已经加了间隔。

## 目录结构

```text
SKILL.md                        技能入口：什么时候用、三类任务怎么走
references/api.md               接口速查：端点、必填字段、报错对照
references/passage.md           记忆材料怎么写：难度、逻辑与梗概、交付格式
references/markji-card-syntax.md 记忆卡正文语法摘要
scripts/collect_review_words.py 挑出某段时间的不熟/忘记单词
scripts/check_passage.py        核对短文是否覆盖全部单词、词条是否齐全
scripts/check_difficulty.py     按简单/中等/困难三档核对句长、每句生词数与密度
scripts/maimemo.ps1             命令行工具，覆盖墨墨开放 API 的读写接口
scripts/md2docx.py              Markdown 中间稿转 Word
scripts/docx2pdf.ps1            Word 转 PDF（调用本机 Word）
```

## 隐私说明

- 脚本只把请求发往 `https://open.maimemo.com`，没有别的外部服务。
- 令牌只保存在你本机（环境变量或 `~/.codex/maimemo_token`），不写入任何生成的文件。
- 抓取脚本只调用只读接口；写入类接口（例句、助记、释义、云词本）在使用前会先跟你确认，创建的条目都有 ID，可以通过 DELETE 删除。
- 不提供改动学习计划的默认动作：把词加进计划、提前复习这两个接口需要你明确要求才会调用。

## 已知限制

- 「不熟 / 忘记」用的是**最近一次**复习结果，所以查某天得到的是「最近一次复习发生在那天且结果不熟或忘记」的词。当天在 App 里的结果要等同步后才能查到。
- 学习记录接口单次最多返回 1000 条，脚本按 30 天窗口扫描并合并，一次运行会发十几次请求。
- 记忆卡（Markji）相关接口在部分账号上返回权限不足，需要联系墨墨开发者开通。
- 例句的标签只能用墨墨已有的标签，自定义标签会被接口拒绝。

## 许可

MIT，见 [LICENSE](LICENSE)。
