$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Builder = Join-Path $ProjectRoot 'scripts\build.py'

if (-not (Test-Path -LiteralPath $Builder -PathType Leaf)) {
    throw "找不到打包脚本：$Builder"
}

# 优先使用 Python Launcher（py -3），找不到时再尝试 python。
$PythonCommand = Get-Command py -ErrorAction SilentlyContinue
if ($PythonCommand) {
    & py -3 $Builder
    if ($LASTEXITCODE -ne 0) { throw "打包失败，Python 退出代码：$LASTEXITCODE" }
    exit 0
}

$PythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($PythonCommand) {
    & python $Builder
    if ($LASTEXITCODE -ne 0) { throw "打包失败，Python 退出代码：$LASTEXITCODE" }
    exit 0
}

throw '没有找到 Python。请安装 Python 3，并勾选 Add Python to PATH。'
