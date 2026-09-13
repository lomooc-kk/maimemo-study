# 墨墨开放 API 速查

官方文档：<https://open.maimemo.com/api_bundle.yaml>（Redoc 页面 <https://open.maimemo.com/>）。

## 基础

- 根地址 `https://open.maimemo.com/open/api/v1`。文档里写的 `/api/v1/...` 前面要补一个 `/open`。
- 请求头 `Authorization: Bearer 令牌`，`Accept: application/json`。
- 成功 `{"success": true, "data": {...}}`，失败 `{"success": false, "errors": [{"code", "msg"}]}`。
- 令牌获取：墨墨背单词 App → 我的 → 更多设置 → 实验功能 → 开放 API；或登录后打开 <https://open.maimemo.com/open/api/v1/tokens/openapi>。

## 频控

10 秒 20 次、60 秒 40 次、5 小时 2000 次（背单词）/ 8000 次（记忆卡）。创建内容（例句、助记、释义合计）每天上限 600 条。批量操作要留间隔，脚本里默认每次请求间停 0.6 秒。

## 背单词（`/memo/...`）

| 接口 | 说明 |
|---|---|
| `GET /memo/vocabulary?spelling=hello` | 查单词，返回 `voc_id` |
| `POST /memo/vocabulary/query` | `{spellings:[...]}` 或 `{ids:[...]}`，两者互斥 |
| `POST /memo/study/get_study_progress` | 今日进度 `{finished,total,study_time}` |
| `POST /memo/study/get_today_items` | 今日单词，可传 `{is_new,is_finished,limit}` |
| `POST /memo/study/query_study_records` | 学习记录，见下文 |
| `POST /memo/study/add_words` | `{words:[{id}],advance}`，**会改学习计划** |
| `POST /memo/study/advance_study` | `{voc_ids:[...]}`，提前复习，**会改计划** |
| `GET /memo/phrases?voc_id=` / `POST /memo/phrases` | 查 / 建例句 |
| `GET /memo/notes?voc_id=` / `POST /memo/notes` | 查 / 建助记 |
| `GET /memo/interpretations?voc_id=` / `POST /memo/interpretations` | 查 / 建自定义释义 |
| `GET /memo/notepads` / `POST /memo/notepads` / `POST /memo/notepads/{id}` | 云词本 |

DELETE 端点：`/memo/phrases/{id}`、`/memo/notes/{id}`、`/memo/interpretations/{id}`、`/memo/notepads/{id}`，都能删掉自己刚建的内容。

## 学习记录怎么查

请求体字段：`next_study_date:{start,end}`、`voc_ids`、`spellings`、`tags`、`as_count`、`limit`。

两个容易踩的点：

1. `limit` 最大 1000，没有 offset，所以不能靠翻页拿全量。`collect_review_words.py` 的做法是按 `next_study_date` 分 30 天窗口扫描再合并。
2. `next_study_date` 是**下次复习时间**，不是历史复习时间。想筛"某天真背过的词"，得先把记录拉下来，再用返回里的 `last_study_date` 和 `last_response` 在本地过滤。

返回值里每个词带 `last_study_date`、`next_study_date`、`last_response`（`FAMILIAR` 认识 / `VAGUE` 不熟 / `FORGET` 忘记 / `WELL_FAMILIAR` 熟知）、`study_count`、`tags`。

`as_count: true` 时只回数量，用来估算规划总量。

## 写入时的必填字段

文档里没强调、但接口强制的字段，漏了会报 `common_invalid_param ... must have required property`：

- 例句：`voc_id`、`phrase`、`interpretation`、`origin`、`tags` 全部必填，没有出处传空字符串、没有标签传 `[]`。
- 释义：`voc_id`、`interpretation`、`tags`、`status`（`PUBLISHED` / `UNPUBLISHED`）。
- 助记：`voc_id`、`note_type`（例如 `谐音`）、`note`。
- 云词本：`status`、`content`、`title`、`brief`、`tags`。
- 卡片：`card.content` 和 `card.grammar_version` 必填。

`tags` 只能是墨墨已有的标签，填自定义标签会报 `phrase_forbid_tags`。不确定就传空数组。

## 报错对照

| 报错 | 原因 |
|---|---|
| `common_unauthorized` | 令牌没填、填错或失效 |
| `common_permission_denied` | 令牌没开这组接口的权限；记忆卡接口目前属于这一类 |
| `common_invalid_param` + `must have required property` | 漏必填项，对照上一节 |
| `phrase_forbid_tags` | 例句标签不是墨墨已有的标签 |
| `property 'limit' must be <= 1000` | `limit` 超上限 |
| 提示调用过于频繁 | 触发频控，等 10 秒以上并拆批 |
| `add_words` 返回 `added_count: 0` | 词已不在计划里或已在计划中 |

## 记忆卡（`/markji/...`）

端点：`GET /markji/decks/folders`、`GET /markji/decks`、`GET /markji/decks/{deck}/chapters`、`GET /markji/decks/{deck}/cards/{card}`、`POST /markji/decks/{deck}/chapters/{chapter}/cards`（新建卡片）、`POST /markji/decks/{deck_id}/cards/{card_id}`（改正文）、`POST /markji/files`（multipart 上传图片音频）、`POST /markji/files/query`。

卡片正文是一套方括号语法（挖空、选择题、公式、图片等），写之前读 [markji-card-syntax.md](markji-card-syntax.md)。

当前账号在这组接口上返回 `common_permission_denied`，需要用户在 App 的【我的 - 帮助与反馈】里联系开发者开通，或换记忆卡那边的入口拿令牌。`maimemo.ps1` 里的 `card-new` / `upload` 等命令可以直接用，权限开了就能跑。

## 命令行工具

`scripts/maimemo.ps1` 覆盖了上面所有端点，`help` 会打印全部命令。`-DryRun` 只打印请求不发送，适合先验证参数。脚本需要 Windows PowerShell（系统自带），不用装东西。
