> 本仓库（管线二）有两个入口，需要的 Key 不同：
> **`run`**（课程 → 基础证据讲义）需要 **TEXT + VISION 两个角色**；
> **`study`**（lecture.json → 学习讲义）另需 **PLANNER + WRITER 两个角色**。
> 角色用什么服务都行，只要求满足"文本/视觉"能力，下面按推荐服务展开。

# API 配置指南

> 拿到本仓库后，按本指南申请并配置 API Key，即可跑通管线。**任何密钥都不要提交进仓库**
> （.gitignore 已拦截常见密钥文件，但请自觉）。

## 一、总览：角色 × 入口矩阵（实际代码行为）

| 阶段 | 使用的角色 | 推荐服务 | 模型 | 必需性 |
|---|---|---|---|---|
| 语音转写 ASR | 无（本地） | faster-whisper small/int8 | — | 无需 API |
| 转写整理 polish（run） | `text` | Kimi 开放平台 / DeepSeek | kimi-k2.6 / deepseek-chat | **必需** |
| 窗口 map（run） | `vision`（有帧）/ `text`（纯口述） | 硅基流动 | Qwen3-VL-32B-Instruct | **必需** |
| reduce 目录编排（run） | `text` | 同上 | 同上 | **必需** |
| 公式原帧复查（run） | `vision` | 硅基流动 | Qwen3-VL-32B-Instruct | **必需** |
| 课程规划 + 四道工序（study） | `planner` + `writer` | 百炼 + Kimi | qwen3.8-max / kimi-k2.6 | 仅 study 需要 |
| 讲义渲染 | 无（本地） | XeLaTeX | — | 无需 API |

**最少配置**：只跑 `run` 需 2 个角色（TEXT + VISION，可以是同一家的两个 Key）；
要跑 `study` 再加 PLANNER + WRITER。

> 注意：`SILICONFLOW_API_KEY` 单独设置**不足以**运行——代码不会因为它的存在而把
> text/vision 角色切到硅基流动。请用 `ECHONOTES_TEXT_*` / `ECHONOTES_VISION_*`
> 显式配置（见第三节），或用密码书。

## 二、密钥放哪：三种方式任选

**方式 A · `.env` 文件**（推荐，启动时自动加载）

复制 `.env.example` 为 `.env` 填写即可，无需 export。已在 shell 里 export 的同名变量优先。

**方式 B · 终端环境变量**

```bash
# macOS / Linux (zsh/bash)
export ECHONOTES_TEXT_API_KEY="sk-xxx"
export ECHONOTES_VISION_API_KEY="sk-xxx"
```

```powershell
# Windows PowerShell
$env:ECHONOTES_TEXT_API_KEY   = "sk-xxx"
$env:ECHONOTES_VISION_API_KEY = "sk-xxx"
```

**方式 C · 密钥文件**（统一管理多个 Key）

```json
{
  "entries": [
    { "provider": "siliconflow", "apiKey": "sk-xxx",
      "baseUrl": "https://api.siliconflow.cn/v1", "models": ["Qwen/Qwen3-VL-32B-Instruct"] },
    { "provider": "moonshot", "label": "moonshot-payg", "apiKey": "sk-xxx",
      "baseUrl": "https://api.moonshot.cn/v1", "models": ["kimi-k2.6"] }
  ]
}
```

启动时传 `--secrets 路径.json`，或设 `ECHONOTES_SECRETS_FILE` 环境变量。
按 provider 匹配条目；同名 provider 有多把 Key 时用 `ECHONOTES_<角色>_KEY_LABEL`
按 label 挑选。

## 三、各服务详解（按量 / 订阅完整配置矩阵）

### 1. 硅基流动 SiliconFlow —— VISION 角色（run 必需）

- **干什么**：窗口 map（看转写+板书截图产出知识块）与公式原帧复查。
- **为什么选它**：需要**多模态视觉模型**且能**国内直连**。首选 Gemini 因中国大陆
  区域不可用（实测返回地区限制错误），**平替就是 Qwen3-VL**——开源多模态、
  视频帧理解质量接近、价格低（本管线约合每分P几毛钱）、无需科学上网。
- **在哪申请**：https://siliconflow.cn → 注册后在「API 密钥」页新建（新用户送额度）。
- **完整配置**：

```bash
export ECHONOTES_VISION_PROVIDER=siliconflow
export ECHONOTES_VISION_BASE_URL=https://api.siliconflow.cn/v1
export ECHONOTES_VISION_MODEL=Qwen/Qwen3-VL-32B-Instruct
export ECHONOTES_VISION_API_KEY=sk-xxx    # provider=siliconflow 时也可用 SILICONFLOW_API_KEY
```

> 只设 `SILICONFLOW_API_KEY` 而不设 `ECHONOTES_VISION_PROVIDER/BASE_URL` 时，
> vision 角色仍指向默认的 openrouter，主流程无法工作。

### 2. Kimi（Moonshot）—— TEXT / WRITER 角色

- **干什么**：TEXT 做转写整理 polish 与 reduce 编排；WRITER 在 study 阶段写讲义正文。
- **两种账户两种端点，别混用**：

| 账户类型 | Base URL | 可用模型（先 curl /models 确认） | 注意 |
|---|---|---|---|
| 开放平台按量 | `https://api.moonshot.cn/v1` | 以 /models 返回为准，如 `kimi-k2.6`、`kimi-k2.7-code` | **`kimi-k3` 在按量 Key 上实测 404**；temperature 可调 |
| Kimi Code Plan 订阅 | `https://api.kimi.com/coding/v1` | 订阅端点模型，如 `kimi-k3` | 强制 temperature=1（不可调低） |

- **在哪申请**：按量 https://platform.moonshot.cn ；订阅 https://www.kimi.com 。
- **完整配置（按量示例）**：

```bash
export ECHONOTES_TEXT_PROVIDER=moonshot
export ECHONOTES_TEXT_BASE_URL=https://api.moonshot.cn/v1
export ECHONOTES_TEXT_MODEL=kimi-k2.6
export ECHONOTES_TEXT_API_KEY=sk-xxx
# WRITER 同理：ECHONOTES_WRITER_{PROVIDER,BASE_URL,MODEL,API_KEY}
# Code Plan 订阅账户须加 ECHONOTES_WRITER_TEMPERATURE=1
```

> 教训：**/models 返回 200 ≠ 该模型有生成授权**。配置完先跑第四节的真实生成
> 小测试；404 时换 /models 列出的模型 ID。TEXT 与 WRITER 的变量是独立的——
> `export B="$A"` 复制的是当时的值，之后改 A 不会同步 B。

### 3. 阿里云百炼 —— PLANNER 角色（仅 study 需要）

- **干什么**：study 阶段的学习单元规划与概念地图。`run` 阶段不读取该角色。
- **两种账户两种端点**：

| 账户类型 | Base URL | 注意 |
|---|---|---|
| 按量计费 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 按量扣费，控制台确认模型已开通 |
| token plan 订阅 | `https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1` | 订阅配额内不按量扣费，注意地域 |

- **完整配置（按量示例）**：

```bash
export ECHONOTES_PLANNER_PROVIDER=bailian
export ECHONOTES_PLANNER_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export ECHONOTES_PLANNER_MODEL=qwen3.8-max
export ECHONOTES_PLANNER_API_KEY=sk-xxx
```

### 4. DeepSeek —— TEXT 角色平替（便宜稳定）

- **干什么**：TEXT 角色的默认 provider；polish 这类格式活不需要贵模型。
- **在哪申请**：https://platform.deepseek.com → 充值后建 Key（按量）。
- **配置**：只填 `ECHONOTES_TEXT_API_KEY` 即可（默认 provider/base 已指向 DeepSeek）。

### 5. 本地 ASR faster-whisper —— 全管线通用（无 API）

- **干什么**：语音转带时间戳文字稿。
- **配置**：无需 Key。模型从 HuggingFace 下载 `Systran/faster-whisper-small`
  放到本地目录，用 `ECHONOTES_ASR_MODEL` 指向；`ECHONOTES_ASR_PYTHON` 指向装了
  faster-whisper 的 Python。另需 `ffmpeg` 在 PATH。

### 6. Gemini —— 为什么默认不用

- **原因**：官方 API 对中国大陆区域不可用（实测请求返回地区限制错误），且需要代理。
- **平替**：视觉任务用硅基流动 Qwen3-VL（能力相当、国内直连）；
  `GEMINI_API_KEY` 可用时可切回。

## 四、配置完自检（先列表后生成，两步都要过）

```bash
# 第 1 步：模型列表能返回（Key 有效、网络通）
curl https://api.siliconflow.cn/v1/models -H "Authorization: Bearer $ECHONOTES_VISION_API_KEY"
curl https://api.moonshot.cn/v1/models -H "Authorization: Bearer $ECHONOTES_TEXT_API_KEY"
curl https://dashscope.aliyuncs.com/compatible-mode/v1/models -H "Authorization: Bearer $ECHONOTES_PLANNER_API_KEY"

# 第 2 步：真实生成小测试（列表通过 ≠ 生成授权通过；max_tokens=8 控制成本）
curl https://api.moonshot.cn/v1/chat/completions -H "Authorization: Bearer $ECHONOTES_TEXT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"kimi-k2.6","messages":[{"role":"user","content":"回复 OK"}],"max_tokens":8}'
```

两步都通过、且 `ffmpeg -version` / `xelatex --version` 可用，才算配置完成。
请求策略：默认单次超时 180 秒 × 3 次尝试，退避 10s 递增；可用
`ECHONOTES_MODEL_TIMEOUT` / `ECHONOTES_MODEL_RETRIES` / `ECHONOTES_MODEL_BACKOFF`
覆盖（管线启动时会打印生效值）。

## 五、安全须知

- 密钥文件放在**仓库目录之外**（本项目惯例是本地"密码书"目录）；
- `.gitignore` 已拦截常见密钥文件名（含 `.env`），但新增文件请自查 `git status`；
- 提交前可跑 `git grep -i "sk-"` 快速扫一遍暂存内容；
- Key 泄漏的第一时间去对应平台吊销重发。
