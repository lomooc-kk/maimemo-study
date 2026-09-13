#Requires -Version 5.1
<#
  墨墨开放 API 命令行小工具 (PowerShell)

  准备：先拿到请求凭证（令牌）
    方式一：墨墨背单词 App -> 我的 -> 更多设置 -> 实验功能 -> 开放 API
    方式二：浏览器登录后打开 https://open.maimemo.com/open/api/v1/tokens/openapi

  设置令牌（任选其一）：
    $env:MAIMEMO_TOKEN = "你的令牌"          # 当前窗口生效
    setx MAIMEMO_TOKEN "你的令牌"            # 永久生效，重开窗口
    把令牌写进与本脚本同目录的 .maimemo_token 文件

  使用：
    powershell -ExecutionPolicy Bypass -File maimemo.ps1 help
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)][string]$Command = 'help',
    [Parameter(Position = 1)][string]$A1,
    [Parameter(Position = 2)][string]$A2,
    [Parameter(Position = 3)][string]$A3,

    [string]$Token,
    [string]$Content,
    [string]$File,
    [int]$Order = -1,
    [int]$GrammarVersion = 0,
    [int]$Limit = 0,
    [int]$Offset = 0,
    [string]$Folder,
    [string]$Ids,
    [string]$Words,
    [string]$End,
    [string]$Tags,
    [string]$Origin,
    [string]$Status,
    [string]$NoteType,
    [string]$Title,
    [string]$Brief,
    [string]$Interpretation,
    [switch]$WithCards,
    [switch]$New,
    [switch]$Finished,
    [switch]$AsCount,
    [switch]$Advance,
    [switch]$All,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }

$script:Base = 'https://open.maimemo.com/open/api/v1'
$script:Token = $Token

function Get-MmToken {
    if ($Token) { return $Token }
    if ($env:MAIMEMO_TOKEN) { return $env:MAIMEMO_TOKEN }
    $shared = Join-Path $HOME '.codex\maimemo_token'
    foreach ($p in @($shared, (Join-Path $PSScriptRoot '.maimemo_token'), (Join-Path $PWD '.maimemo_token'))) {
        if (Test-Path $p) { return (Read-TextFile $p).Trim() }
    }
    throw "没找到令牌。请设置环境变量 MAIMEMO_TOKEN，写入 $shared，或用 -Token 传入。"
}

function Get-AuthToken {
    if (-not $script:Token) { $script:Token = Get-MmToken }
    return $script:Token
}

function Read-TextFile {
    # 按 UTF-8 读取；文件若是 GBK/ANSI 编码则自动回退，避免中文变乱码
    param([Parameter(Mandatory)][string]$Path)
    $full = (Resolve-Path -LiteralPath $Path).Path
    $bytes = [System.IO.File]::ReadAllBytes($full)
    $text = $null
    try {
        $strict = New-Object System.Text.UTF8Encoding($false, $true)
        $text = $strict.GetString($bytes)
    }
    catch {
        try {
            $text = [System.Text.Encoding]::GetEncoding('GB18030').GetString($bytes)
        }
        catch {
            $text = [System.Text.Encoding]::UTF8.GetString($bytes)
        }
    }
    return [string]$text.TrimStart([char]0xFEFF)
}

function New-QueryString {
    param([hashtable]$Query)
    if (-not $Query -or $Query.Count -eq 0) { return '' }
    $parts = foreach ($k in $Query.Keys) {
        $v = $Query[$k]
        if ($null -eq $v) { continue }
        if ($v -is [bool]) { $v = if ($v) { 'true' } else { 'false' } }
        if ($v -is [array]) { $v = ($v -join ',') }
        '{0}={1}' -f $k, [uri]::EscapeDataString([string]$v)
    }
    if (-not $parts) { return '' }
    '?' + ($parts -join '&')
}

function Invoke-Mm {
    param(
        [Parameter(Mandatory)][string]$Method,
        [Parameter(Mandatory)][string]$Path,
        $Body,
        [hashtable]$Query
    )
    $uri = $script:Base + $Path + (New-QueryString $Query)
    $bearer = if ($DryRun) { 'DRYRUN' } else { Get-AuthToken }
    $headers = @{ Authorization = "Bearer $bearer"; Accept = 'application/json' }
    $params = @{ Uri = $uri; Method = $Method; Headers = $headers; TimeoutSec = 30 }
    if ($PSBoundParameters.ContainsKey('Body') -and $null -ne $Body) {
        $json = $Body | ConvertTo-Json -Depth 20 -Compress
        $params.ContentType = 'application/json; charset=utf-8'
        $params.Body = [System.Text.Encoding]::UTF8.GetBytes($json)
    }
    if ($DryRun) {
        Write-Host ("[{0}] {1}" -f $Method, $uri) -ForegroundColor Cyan
        if ($params.ContainsKey('Body')) {
            Write-Host ([System.Text.Encoding]::UTF8.GetString($params.Body))
        }
        return $null
    }
    try {
        $resp = Invoke-RestMethod @params
    }
    catch {
        $detail = $_.ErrorDetails.Message
        if (-not $detail -and $_.Exception.Response) {
            try {
                $sr = New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())
                $detail = $sr.ReadToEnd()
            } catch { }
        }
        if ($detail) {
            $hint = ''
            if ($detail -match 'unauthorized') { $hint = '（令牌无效或已过期，请重新获取令牌）' }
            elseif ($detail -match 'too_many|rate_limit|too many') { $hint = '（触发了调用频率限制，稍等几秒再试）' }
            elseif ($detail -match 'permission_denied') { $hint = '（这个令牌没有该组接口的权限：记忆卡相关接口需另行开通）' }
            elseif ($detail -match 'invalid_param') { $hint = '（参数不完整或不合法，必填项见使用说明第二节末尾）' }
            throw "请求失败$hint：$detail"
        }
        else { throw $_ }
    }
    if ($resp -is [psobject] -and $resp.PSObject.Properties.Name -contains 'success' -and -not $resp.success) {
        throw ("接口返回失败：" + (($resp.errors | ForEach-Object { "$($_.code) $($_.msg)" }) -join '; '))
    }
    if ($resp -is [psobject] -and $resp.PSObject.Properties.Name -contains 'data') { return $resp.data }
    return $resp
}

function Write-Result {
    param($Value)
    $Value | ConvertTo-Json -Depth 20
}

function Read-Content {
    # 卡片正文支持：-Content 直接给字符串，或 -File 读文件（中文按 UTF-8 读取）
    if ($Content) { return $Content }
    if ($File) {
        if (-not (Test-Path $File)) { throw "找不到文件：$File" }
        return (Read-TextFile $File)
    }
    throw "缺少内容：请用 -Content 或 -File 指定卡片正文。"
}

function Get-GrammarVersion {
    param([string]$DeckId, [string]$ChapterId, [string]$CardId)
    if ($GrammarVersion -gt 0) { return $GrammarVersion }
    # 语法版本会随墨墨更新，先读一张已有卡片沿用它的值，读不到就按 1 试
    try {
        if ($CardId) {
            $card = (Invoke-Mm -Method GET -Path "/markji/decks/$DeckId/cards/$CardId").card
        }
        else {
            $r = Invoke-Mm -Method GET -Path "/markji/decks/$DeckId/chapters/$ChapterId" -Query @{ with_cards = $true }
            $card = @($r.cards) | Select-Object -First 1
        }
        if ($card -and $card.grammar_version) { return [int]$card.grammar_version }
    } catch { }
    return 1
}

function Upload-File {
    param([string]$Path, [string]$DeckId)
    if (-not (Test-Path $Path)) { throw "找不到文件：$Path" }
    Add-Type -AssemblyName System.Net.Http -ErrorAction SilentlyContinue
    $client = New-Object System.Net.Http.HttpClient
    $client.DefaultRequestHeaders.Authorization =
        New-Object System.Net.Http.Headers.AuthenticationHeaderValue('Bearer', (Get-AuthToken))
    $form = New-Object System.Net.Http.MultipartFormDataContent
    $fs = [System.IO.File]::OpenRead((Resolve-Path $Path))
    $fileContent = New-Object System.Net.Http.StreamContent($fs)
    $form.Add($fileContent, 'file', [System.IO.Path]::GetFileName($Path))
    if ($DeckId) { $form.Add((New-Object System.Net.Http.StringContent($DeckId)), 'deck_id') }
    $resp = $client.PostAsync("$script:Base/markji/files", $form).Result
    $text = $resp.Content.ReadAsStringAsync().Result
    $client.Dispose(); $fs.Dispose()
    $obj = $text | ConvertFrom-Json
    if (-not $obj.success) { throw "上传失败：$text" }
    return $obj.data
}

function Split-List {
    # 把 "a,b,c" 或 @("a","b") 统一变成字符串数组；空值返回空数组
    param($Value)
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($item in @($Value)) {
        if ($null -eq $item) { continue }
        foreach ($piece in ([string]$item -split '[,;]')) {
            $t = $piece.Trim()
            if ($t) { $out.Add($t) }
        }
    }
    return , $out.ToArray()
}

function Show-Help {
    @'
墨墨开放 API 命令行工具

  通用
    help                              显示本帮助
    raw <GET|POST|DELETE> <路径> [json]  直接调用任意接口，例：raw GET /memo/vocabulary?spelling=hello

  墨墨记忆卡（Markji，自建牌组/卡片）
    decks [-Folder <文件夹ID>]        我的自建牌组列表
    folders                           文件夹列表
    chapters <牌组ID> [-WithCards]    牌组下的章节（-WithCards 同时列出卡片）
    card <牌组ID> <卡片ID>            单张卡片详情
    card-new <牌组ID> <章节ID> -Content "正文" [-File 正文.txt] [-Order 位置]
    card-update <牌组ID> <卡片ID> -Content "正文" [-File 正文.txt]
    upload <本地文件> [牌组ID]         上传图片/音频，返回文件 ID
    files <文件ID,文件ID>              查询文件信息

  墨墨背单词
    vocab <单词>                       查单词（拿 voc_id）
    vocab-query [-Ids id,id] [-Words a,b]  批量查询
    progress                           今日学习进度
    today [-Limit 20] [-New] [-Finished]   今日要背的单词
    records [-End 2026-04-01T00:00:00+08:00] [-Ids vocid] [-AsCount]
    add <单词...> [-Advance]           把单词加入学习计划（自动查 id）
    advance <vocId...>                 提前复习
    phrase-add <vocId> -Content "英文例句" -Interpretation "中文释义" [-Origin 出处] [-Tags a,b]
    phrase-list <vocId>                查自己创建的例句
    note-add <vocId> -Content "助记" [-NoteType 谐音]
    note-list <vocId>
    interp-add <vocId> -Content "释义" [-Tags a,b] [-Status PUBLISHED]
    interp-list <vocId>
    notepads [-Limit 10] [-Offset 0]   云词本列表
    notepad <词本ID>                   云词本详情
    notepad-new -Title "标题" -Content "内容" [-Brief 简介]
    notepad-update <词本ID> -Title "标题" -Content "内容" [-Brief 简介]
    notepad-delete <词本ID>

  首次使用先设置令牌：$env:MAIMEMO_TOKEN = "你的令牌"
'@
}

try {
switch ($Command.ToLower()) {
    'help' { Show-Help }

    'raw' {
        $method = if ($A1) { $A1.ToUpper() } else { 'GET' }
        $body = $null
        if ($A3) { $body = $A3 | ConvertFrom-Json }
        Write-Result (Invoke-Mm -Method $method -Path $A2 -Body $body)
    }

    'folders' { Write-Result (Invoke-Mm -Method GET -Path '/markji/decks/folders') }

    'decks' {
        $q = @{}
        if ($Folder) { $q.folder_id = $Folder }
        if ($Limit -gt 0) { $q.limit = $Limit }
        if ($Offset -gt 0) { $q.offset = $Offset }
        Write-Result (Invoke-Mm -Method GET -Path '/markji/decks' -Query $q)
    }

    'chapters' {
        if (-not $A1) { throw '用法：chapters <牌组ID> [-WithCards]' }
        $q = @{}
        if ($WithCards) { $q.with_cards = $true }
        Write-Result (Invoke-Mm -Method GET -Path "/markji/decks/$A1/chapters" -Query $q)
    }

    'card' {
        if (-not $A1 -or -not $A2) { throw '用法：card <牌组ID> <卡片ID>' }
        Write-Result (Invoke-Mm -Method GET -Path "/markji/decks/$A1/cards/$A2")
    }

    'card-new' {
        if (-not $A1 -or -not $A2) { throw '用法：card-new <牌组ID> <章节ID> -Content "正文"' }
        $text = Read-Content
        $gv = Get-GrammarVersion -DeckId $A1 -ChapterId $A2
        $payload = @{
            deck    = $A1
            chapter = $A2
            card    = @{ content = $text; grammar_version = $gv }
        }
        if ($Order -ge 0) { $payload.order = $Order }
        Write-Result (Invoke-Mm -Method POST -Path "/markji/decks/$A1/chapters/$A2/cards" -Body $payload)
    }

    'card-update' {
        if (-not $A1 -or -not $A2) { throw '用法：card-update <牌组ID> <卡片ID> -Content "正文"' }
        $text = Read-Content
        $gv = Get-GrammarVersion -DeckId $A1 -CardId $A2
        $payload = @{
            deck_id = $A1
            card_id = $A2
            card    = @{ content = $text; grammar_version = $gv }
        }
        Write-Result (Invoke-Mm -Method POST -Path "/markji/decks/$A1/cards/$A2" -Body $payload)
    }

    'upload' {
        if (-not $A1) { throw '用法：upload <本地文件> [牌组ID]' }
        if ($DryRun) {
            Write-Host ("[POST] {0}/markji/files  (multipart: file={1}, deck_id={2})" -f $script:Base, $A1, $A2) -ForegroundColor Cyan
            break
        }
        Write-Result (Upload-File -Path $A1 -DeckId $A2)
    }

    'files' {
        if (-not $A1) { throw '用法：files <文件ID,文件ID>' }
        Write-Result (Invoke-Mm -Method POST -Path '/markji/files/query' -Body @{ ids = (Split-List $A1) })
    }

    'vocab' {
        if (-not $A1) { throw '用法：vocab <单词>' }
        Write-Result (Invoke-Mm -Method GET -Path '/memo/vocabulary' -Query @{ spelling = $A1 })
    }

    'vocab-query' {
        $body = @{}
        $idList = Split-List $Ids
        $wordList = Split-List $Words
        if ($idList.Count) { $body.ids = $idList }
        elseif ($wordList.Count) { $body.spellings = $wordList }
        else { $body.spellings = Split-List (@($A1, $A2, $A3)) }
        Write-Result (Invoke-Mm -Method POST -Path '/memo/vocabulary/query' -Body $body)
    }

    'progress' { Write-Result (Invoke-Mm -Method POST -Path '/memo/study/get_study_progress') }

    'today' {
        $body = @{}
        if ($Limit -gt 0) { $body.limit = $Limit }
        if ($New) { $body.is_new = $true }
        if ($Finished) { $body.is_finished = $true }
        Write-Result (Invoke-Mm -Method POST -Path '/memo/study/get_today_items' -Body $body)
    }

    'records' {
        $body = @{}
        if ($End) { $body.next_study_date = @{ end = $End } }
        $idList = Split-List $Ids
        if ($idList.Count) { $body.voc_ids = $idList }
        if ($AsCount) { $body.as_count = $true }
        if ($Limit -gt 0) { $body.limit = $Limit }
        Write-Result (Invoke-Mm -Method POST -Path '/memo/study/query_study_records' -Body $body)
    }

    'add' {
        $wordList = Split-List (@($A1, $A2, $A3) + (Split-List $Words))
        if (-not $wordList.Count) { throw '用法：add <单词...> [-Advance]' }
        $found = Invoke-Mm -Method POST -Path '/memo/vocabulary/query' -Body @{ spellings = $wordList }
        $vocList = @($found.voc)
        $missing = $wordList | Where-Object { $w = $_; -not ($vocList | Where-Object { $_.spelling -eq $w }) }
        if ($missing) { Write-Warning ("词典里没找到：" + ($missing -join ', ')) }
        $payloadWords = @($vocList | ForEach-Object { @{ id = $_.id } })
        if (-not $payloadWords.Count) { throw '没有可添加的单词。' }
        Write-Result (Invoke-Mm -Method POST -Path '/memo/study/add_words' -Body @{
                words = $payloadWords; advance = [bool]$Advance
            })
    }

    'advance' {
        $vocIds = Split-List (@($A1, $A2, $A3) + (Split-List $Ids))
        if (-not $vocIds.Count) { throw '用法：advance <vocId...>' }
        Write-Result (Invoke-Mm -Method POST -Path '/memo/study/advance_study' -Body @{ voc_ids = $vocIds })
    }

    'phrase-add' {
        if (-not $A1) { throw '用法：phrase-add <vocId> -Content "英文例句" -Interpretation "中文释义" [-Origin 出处] [-Tags a,b]' }
        $interpText = if ($Interpretation) { $Interpretation } elseif ($A2) { $A2 } else { '' }
        $phrase = @{
            voc_id         = $A1
            phrase         = (Read-Content)
            interpretation = $interpText
            origin         = $(if ($Origin) { $Origin } else { '' })
            tags           = (Split-List $Tags)    # 官方要求必填，可以是空数组
        }
        Write-Result (Invoke-Mm -Method POST -Path '/memo/phrases' -Body @{ phrase = $phrase })
    }

    'phrase-list' {
        if (-not $A1) { throw '用法：phrase-list <vocId>' }
        Write-Result (Invoke-Mm -Method GET -Path '/memo/phrases' -Query @{ voc_id = $A1 })
    }

    'note-add' {
        if (-not $A1) { throw '用法：note-add <vocId> -Content "助记" [-NoteType 谐音]' }
        $note = @{ voc_id = $A1; note = (Read-Content); note_type = $(if ($NoteType) { $NoteType } else { '谐音' }) }
        Write-Result (Invoke-Mm -Method POST -Path '/memo/notes' -Body @{ note = $note })
    }

    'note-list' {
        if (-not $A1) { throw '用法：note-list <vocId>' }
        Write-Result (Invoke-Mm -Method GET -Path '/memo/notes' -Query @{ voc_id = $A1 })
    }

    'interp-add' {
        if (-not $A1) { throw '用法：interp-add <vocId> -Content "释义" [-Tags a,b] [-Status PUBLISHED]' }
        $interp = @{
            voc_id         = $A1
            interpretation = (Read-Content)
            status         = $(if ($Status) { $Status } else { 'PUBLISHED' })
            tags           = (Split-List $Tags)    # 官方要求必填，可以是空数组
        }
        Write-Result (Invoke-Mm -Method POST -Path '/memo/interpretations' -Body @{ interpretation = $interp })
    }

    'interp-list' {
        if (-not $A1) { throw '用法：interp-list <vocId>' }
        Write-Result (Invoke-Mm -Method GET -Path '/memo/interpretations' -Query @{ voc_id = $A1 })
    }

    { $_ -in 'notepads', 'notepads-list' } {
        $q = @{}
        if ($Limit -gt 0) { $q.limit = $Limit }
        if ($Offset -gt 0) { $q.offset = $Offset }
        Write-Result (Invoke-Mm -Method GET -Path '/memo/notepads' -Query $q)
    }

    'notepad' {
        if (-not $A1) { throw '用法：notepad <词本ID>' }
        Write-Result (Invoke-Mm -Method GET -Path "/memo/notepads/$A1")
    }

    { $_ -in 'notepad-new', 'notepad-update' } {
        $id = $null
        if ($Command.ToLower() -eq 'notepad-update') {
            $id = $A1; $A1 = $A2; $A2 = $A3
        }
        $body = @{
            notepad = @{
                title   = $(if ($Title) { $Title } elseif ($A1) { $A1 } else { throw '缺少标题：-Title' })
                content = (Read-Content)
                brief   = $(if ($Brief) { $Brief } else { '' })
                status  = $(if ($Status) { $Status } else { 'PUBLISHED' })
                tags    = (Split-List $Tags)    # 官方要求必填，可以是空数组
            }
        }
        if ($id) { $body.id = $id }
        $path = if ($id) { "/memo/notepads/$id" } else { '/memo/notepads' }
        Write-Result (Invoke-Mm -Method POST -Path $path -Body $body)
    }

    'notepad-delete' {
        if (-not $A1) { throw '用法：notepad-delete <词本ID>' }
        Write-Result (Invoke-Mm -Method DELETE -Path "/memo/notepads/$A1")
    }

    default {
        Write-Host "未知命令：$Command`n" -ForegroundColor Yellow
        Show-Help
        exit 1
    }
}
}
catch {
    Write-Host ("出错了：" + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
