# Ech_lecture · 管线二：课程视频 → LaTeX 讲义

> 输入 B 站课程分P，输出可查证、可打印的 LaTeX 讲义（tex + pdf + 引用截图）。

拾音笺视频观看 agent 三管线之二（姊妹仓库：[Ech_bilibili](https://github.com/WZAwza050801/Ech_bilibili) 读书笔记 · [Ech_practice](https://github.com/WZAwza050801/Ech_practice) 复刻作品集）。

![架构总览](docs/architecture.svg)

## 环境准备（3 步）

### 1. 系统要求

| 项目 | 版本要求 | 用途 | 缺失后果 |
|---|---|---|---|
| Python | >= 3.11 | 全部脚本 | 无法运行 |
| ffmpeg | 任意近期版本 | 抽音频 / 抽帧 / 转码 | ASR 与抽帧直接失败 |
| XeLaTeX | TeX Live 2023+ / MiKTeX | 把 tex 渲染成 PDF | 只有 tex，没有 pdf |
| 中文字体 | 思源/宋体等 CJK 字体 | 讲义中文正常显示 | PDF 中文变方块或回退字体 |

> macOS 注意：系统通常只有 `python3` 没有 `python` 命令。先 `python3 --version` 确认
> >= 3.11（旧系统可能是 3.9，需另装新版），再统一用 `python3` 建环境。

### 2. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows PowerShell
python --version                 # 确认激活后用的是新解释器

pip install -r requirements.txt          # 核心依赖
pip install -r requirements-asr.txt      # 可选：本地语音转写（建议独立虚拟环境）
```

懒得手动敲？一键脚本把「建环境 + 装依赖 + 自检」一次做完：

```bash
bash scripts/setup.sh          # Linux / macOS
.\scripts\setup.ps1           # Windows PowerShell
# 需要本地语音转写就加参数：--asr / -Asr
```

> 依赖刻意做薄：管线主体只用标准库 + 一两个轻量包；`faster-whisper` 会拖入
> ctranslate2 等重依赖，因此单独放 `requirements-asr.txt`，装到独立 venv 后用
> `ECHONOTES_ASR_PYTHON` 指过去，避免与主线环境互相污染。

### 3. 自检（**跑管线前先跑它**）

```bash
python scripts/check_env.py
```

逐项打印 `[ OK ] / [WARN] / [FAIL]`，缺什么、去哪装、装完怎么验证一次说清；
有必需项缺失时退出码为 1。`--ci` 只校验 Python 与 pip 依赖（给 CI 用）。

### 密钥

复制 `.env.example` 为 `.env` 后填写（启动时自动加载，`.env` 已被 `.gitignore` 拦截，永不入库）。
`run` 主流程必需 **TEXT 与 VISION 两个角色** 的 Key（`ECHONOTES_TEXT_API_KEY` /
`ECHONOTES_VISION_API_KEY`，或通过 `ECHONOTES_SECRETS_FILE` 密码书提供）；`study` 阶段
另需 `planner`/`writer`。每个 Key 用在哪、为什么选这个模型、去哪申请，见
[docs/API_SETUP.md](docs/API_SETUP.md)。

### 常见故障速查

| 症状 | 原因 | 解决 |
|---|---|---|
| PDF 中文乱码 / 字体回退 | TeX 环境缺 CJK 字体 | 装 TeX Live 完整版或指定可用中文字体 |
| 视觉阶段报超时或 401 | Key 未设置或额度用尽 | 重设对应 Key；请求默认 180s 超时 × 3 次尝试，可用 `ECHONOTES_MODEL_TIMEOUT` / `ECHONOTES_MODEL_RETRIES` / `ECHONOTES_MODEL_BACKOFF` 调整 |
| HTTP 404 / 模型不存在 | 该 Key 无此模型授权 | 先 `curl <base>/models` 看可用模型 ID，换可用模型（见 API_SETUP） |
| 退出码 1 且打印 `[error]` | 管线异常退出 | 按错误信息排查；运行目录保留可续跑 |

## 快速开始

```bash
# 在仓库根目录执行；`python pipeline2.py` 直接可用，无需安装到 PATH
python pipeline2.py run <B站视频链接或BV号> --page N
# 可选：--transcript <现成转写json> 跳过 ASR · --prepare-only 只准备不调 API · --keep-cache 保留运行缓存
```

**两阶段流程**：`run` 产出基础证据讲义（`lecture.json` + PDF）后，`study` 再把它
重写为学习讲义（出版版 + 卡片版 + 概念地图）。两阶段的模型角色不同，见
[API_SETUP](docs/API_SETUP.md) 的"角色 × 入口"矩阵。

密钥通过 `ECHONOTES_SECRETS_FILE` 指向外部密码书，或复制 `.env.example` 为 `.env` 填写
（管线启动时会自动加载 `.env`，无需手动 export）；仓库不含任何密钥。

## 生成链路

**直取 → ASR → 抽帧 → 视觉 map → 写作 → 复查 → XeLaTeX**（共享前处理只跑一次）

![管线二流程](docs/flow-pipeline2.svg)

| 阶段 | 实现 | API / 工具 |
|---|---|---|
| 音视频直取 | playurl API + 完整浏览器头 | api.bilibili.com（防 412） |
| 本地转写 | faster-whisper small/int8 | 本地模型，零成本 |
| 场景+均匀抽帧 | ffmpeg + dHash 去重 | 保留真实 PTS |
| 转写整理 polish | 只整格式不改内容 | `text` 角色（默认 DeepSeek，可配 Kimi 等） |
| 窗口 map | 每窗 ≤8 帧 + 窗内转写 | `vision` 角色（Qwen3-VL）；纯口述窗口自动切 `text` |
| reduce 目录编排 | 只编排不重写知识块 | `text` 角色 |
| 公式原帧复查 | 回原 PTS 二次问视觉 | `vision` 角色（SiliconFlow Qwen3-VL） |
| LaTeX 渲染 | 两遍 XeLaTeX（交叉引用） | TeX Live |
| study 学习讲义 | 四道工序 + 概念地图 | `planner`（百炼）+ `writer`（Kimi）角色 |

> `run` 只使用 `text` 和 `vision` 两个角色；`planner`/`writer` 仅在 `study` 阶段读取。
> 每个角色的 provider / base_url / model 都可用 `ECHONOTES_<角色>_*` 环境变量覆盖，
> 配置矩阵见 [API_SETUP.md](docs/API_SETUP.md)。

## 产物结构

```
output/课程讲义/<BV号-P页-课程名>/        # --output-root 可改输出位置
├── lecture.pdf / lecture.tex    # 成品（重编译需同目录 frames/）
├── lecture.json                 # 全证据链（transcript/blocks/quality 都在里面）
├── frames\                      # 抽帧证据（去重）
└── README.md                    # 来源、统计、模型配置
```

成功后运行缓存自动清理；`--keep-cache` 保留（调试或续跑 `study` 用）。

**退出码语义**：`exit=0` 成功收尾（质量报告中的 `needs_human_review` 是设计行为——
引用覆盖率不等于内容覆盖率，正式使用前请复核原视频）；异常退出为 `exit=1` 并打印
`[error]`。

## 已验收课程

- 李群李代数（从机器人应用的角度）P1
- 机器人学：运动学与动力学（Kevin Wood 中文配音）P2
- Godot 游戏特效｜入门至进阶实战课 8 个实操P（2026-09 批量，2 lane 并行 6 小时收官）

## 合并-分叉架构

本项目与读书笔记、复刻作品集两条管线共享同一前处理合并段（只跑一次）：

![合并段](docs/flow-merged.svg)

## API 配置

本仓库用到哪些 Key、为什么选这些模型、在哪申请、怎么自检——见 [docs/API_SETUP.md](docs/API_SETUP.md)。密钥永不入库。

## 测试

```bash
python run_tests.py          # 无需 pytest
# 或：pip install pytest && pytest tests/
```