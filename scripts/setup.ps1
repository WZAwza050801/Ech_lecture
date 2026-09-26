# 一键上手：建虚拟环境 -> 装依赖 -> 自检
# 用法: .\scripts\setup.ps1        （加 -Asr 额外装本地语音转写）
param([switch]$Asr)

$ErrorActionPreference = "Stop"

python -m venv .venv
. .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
if ($Asr) { pip install -r requirements-asr.txt }

Write-Host ""
Write-Host "依赖装好了，先做依赖自检（API Key 属于运行期配置，留到配置后再全量自检）："
python scripts/check_env.py --ci
Write-Host ""
Write-Host "下一步：按 docs/API_SETUP.md 配置 Key（填 .env 或导出环境变量），"
Write-Host "然后运行完整自检：python scripts/check_env.py"
