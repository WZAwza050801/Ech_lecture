#!/usr/bin/env bash
# 一键上手：建虚拟环境 -> 装依赖 -> 自检
# 用法: bash scripts/setup.sh      （加 --asr 额外装本地语音转写）
set -euo pipefail

PY=${PYTHON:-python3}
$PY -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

if [[ "${1:-}" == "--asr" ]]; then
  pip install -r requirements-asr.txt
fi

echo
echo "依赖装好了，先做依赖自检（API Key 属于运行期配置，留到配置后再全量自检）："
# --ci 只查 Python 版本与 pip 依赖；Key 未配置时不应让一键安装报错退出。
python scripts/check_env.py --ci
echo
echo "下一步：按 docs/API_SETUP.md 配置 Key（填 .env 或导出环境变量），"
echo "然后运行完整自检：python scripts/check_env.py"
