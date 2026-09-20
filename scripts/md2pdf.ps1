# 把中间稿（Markdown）直接转成 PDF，一步到底。
# Word 只当转换引擎：中间 .docx 生成在 work/ 里，转完就删掉，不进 outputs/。
#
# 用法：
#   powershell -ExecutionPolicy Bypass -File scripts/md2pdf.ps1 -Md work/src.md `
#     -Pdf "outputs/错词短文-9月19-20日-中等.pdf" -Title "文章标题"
#
# 加 -KeepDocx 可以保留那份中间 .docx（默认删除）。
# 本机没装 Word 时会报错退出，这时跟用户说明一声，不要改成只交 Word。

param(
    [Parameter(Mandatory = $true)][string]$Md,
    [Parameter(Mandatory = $true)][string]$Pdf,
    [Parameter(Mandatory = $true)][string]$Title,
    [string]$TempDocx = '',
    [switch]$KeepDocx
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path -LiteralPath $Md)) {
    throw "找不到中间稿：$Md"
}
$mdPath = (Resolve-Path -LiteralPath $Md).Path

if (-not $TempDocx) {
    $tempName = [System.IO.Path]::GetFileNameWithoutExtension($mdPath) + '-temp.docx'
    $TempDocx = Join-Path (Split-Path -Parent $mdPath) $tempName
}
$tempPath = [System.IO.Path]::GetFullPath($TempDocx)

& py -3 (Join-Path $scriptDir 'md2docx.py') $mdPath $tempPath $Title
if ($LASTEXITCODE -ne 0) {
    throw 'md2docx.py 转换失败'
}

& (Join-Path $scriptDir 'docx2pdf.ps1') -Docx $tempPath -Pdf $Pdf

if (-not $KeepDocx -and (Test-Path -LiteralPath $tempPath)) {
    Remove-Item -LiteralPath $tempPath -Force
}

Write-Host "已生成 $([System.IO.Path]::GetFullPath($Pdf))"
