# 把 .docx 转成 .pdf，用本机安装的 Microsoft Word（排版和 Word 里看到的一致）。
#
# 用法：
#   powershell -ExecutionPolicy Bypass -File scripts/docx2pdf.ps1 -Docx "outputs/短文.docx" -Pdf "outputs/短文.pdf"
#
# 没有装 Word 时会报错退出；这种情况下改成用 WPS 手动导出，或在交付时说明只给 Word。

param(
    [Parameter(Mandatory = $true)][string]$Docx,
    [Parameter(Mandatory = $true)][string]$Pdf
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Docx)) {
    throw "找不到 Word 文件：$Docx"
}
$docxPath = (Resolve-Path -LiteralPath $Docx).Path
$pdfPath = [System.IO.Path]::GetFullPath($Pdf)
$pdfDir = Split-Path -Parent $pdfPath
if ($pdfDir -and -not (Test-Path -LiteralPath $pdfDir)) {
    New-Item -ItemType Directory -Path $pdfDir -Force | Out-Null
}

$word = $null
$doc = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    # 第三个参数 true = 只读打开，避免改动原文件
    $doc = $word.Documents.Open($docxPath, [ref]$false, [ref]$true)
    $doc.SaveAs([ref]$pdfPath, [ref]17)   # 17 = wdFormatPDF
}
finally {
    if ($doc) { $doc.Close([ref]0) }      # 0 = 不保存改动
    if ($word) {
        $word.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    }
}

if (-not (Test-Path -LiteralPath $pdfPath)) {
    throw "转换似乎没有成功，找不到输出文件：$pdfPath"
}
Write-Host "已生成 $pdfPath"
