# Tech News Digest

> 一个可自动化运行的科技资讯汇总项目，内置 167 个数据源，其中 165 个默认启用，支持 6 个抓取步骤，以及可配置的 X 与网页搜索后端。

[English](README.md) | **中文**

[![Tests](https://github.com/draco-agent/tech-news-digest/actions/workflows/test.yml/badge.svg)](https://github.com/draco-agent/tech-news-digest/actions/workflows/test.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![ClawHub](https://img.shields.io/badge/ClawHub-tech--news--digest-blueviolet)](https://clawhub.com/draco-agent/tech-news-digest)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 安装方式

### 方式一：一句话安装

直接对你的 [OpenClaw](https://openclaw.ai) 助手说：

> **"安装 tech-news-digest，每天早上 9 点发科技日报到 #tech-news 频道"**

更多示例：

> "配置一个每周 AI 周报，只保留 LLM 和 AI Agent 主题，每周一发到 Discord #ai-weekly"

> "安装 tech-news-digest，加上我的 RSS 源，把加密货币新闻发到 Telegram"

> "现在就生成一份科技日报，跳过 Twitter 数据源"

或者走 CLI：

```bash
clawhub install tech-news-digest
```

### 方式二：本地快速启动

```bash
git clone https://github.com/draco-agent/tech-news-digest.git
cd tech-news-digest

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

cp .env.example .env
# 先编辑 .env，再把它导入当前 shell
set -a
source .env
set +a

mkdir -p workspace/config workspace/archive/tech-news-digest
python3 scripts/validate-config.py --defaults config/defaults --verbose

python3 scripts/run-pipeline.py \
  --defaults config/defaults \
  --config workspace/config \
  --hours 48 \
  --freshness pd \
  --archive-dir workspace/archive/tech-news-digest \
  --output /tmp/td-merged.json \
  --verbose

python3 scripts/run-daily-digest.py \
  --defaults config/defaults \
  --config workspace/config \
  --archive-dir workspace/archive/tech-news-digest \
  --timezone Asia/Shanghai
```

跑完后你会看到：

- 汇总结果：`/tmp/td-merged.json`
- 本次流水线元数据：`/tmp/td-merged.meta.json`
- Markdown 日报：`workspace/archive/tech-news-digest/daily-YYYY-MM-DD.md`
- 你的自定义覆盖配置：`workspace/config/`
- 如果没有 X 或网页搜索相关凭证，流水线仍可跑完，但首轮运行里 X 和网页搜索可能都是 `0` 条

## 这个项目会产出什么

它会把 167 个内置来源里的内容抓下来，做打分、去重、归类，再形成一份可继续分发的科技日报输入。

| 层级 | 数量 | 说明 |
|------|-----:|------|
| RSS | 78 个订阅源 | OpenAI、Anthropic、Ben's Bites、HN、36Kr、CoinDesk，以及部分 YouTube RSS |
| X 账号 | 48 个 | 可走 API；在 auto 模式下也可回退到 Bird 读取本机 X 登录态 |
| 网页搜索 | 4 个主题 | Tavily、Brave、XCrawl，带时效控制 |
| GitHub | 28 个仓库 | Release 加 Trending 一起进入总流水线 |
| Reddit | 13 个子版块 | r/MachineLearning、r/LocalLLaMA、r/CryptoCurrency 等 |

### 数据流水线

```text
run-pipeline.py
  -> fetch-rss.py
  -> fetch-twitter.py
  -> fetch-github.py
  -> fetch-github.py --trending
  -> fetch-reddit.py
  -> fetch-web.py
  -> merge-sources.py
  -> generate-markdown.py
  -> enrich-articles.py (可选)
  -> 下游模板或投递脚本
```

这条流水线的核心价值，不只是“抓到了什么”，更是“怎么把噪音压下去，把值得看的内容排到前面”。评分会综合优先级来源、多源交叉出现、时效性、互动度和主题匹配度，再对历史已出现内容做降权。

## X 搜索与 Web 搜索怎么用

这是这次文档更新的重点。你现在新增的两个能力，实际运行方式如下。

### X 层：通过 Bird 读取 X

- `TWITTER_API_BACKEND=auto` 会按 `getxapi -> twitterapiio -> official -> bird` 依次尝试
- Bird 仍然支持显式启用：传 `--backend bird`，或者设置 `TWITTER_API_BACKEND=bird`
- Bird 依赖本机 X 登录态、浏览器 cookie，或者 `AUTH_TOKEN` 和 `CT0`
- 在 `auto` 模式下，只有当前面 API 凭证都不可用、且 Bird CLI 登录态可用时，才会回退到 Bird

如果你要走 Bird：

```bash
npm install -g @steipete/bird
# 或者不全局安装，按需临时运行
export BIRD_CLI="bunx @steipete/bird"
bird whoami --plain
```

只跑 X 层：

```bash
python3 scripts/fetch-twitter.py \
  --defaults config/defaults \
  --config workspace/config \
  --hours 24 \
  --backend bird \
  --output /tmp/td-twitter.json \
  --verbose
```

Bird 常用节奏参数：

- `BIRD_MAX_WORKERS=1`
- `BIRD_REQUEST_INTERVAL_SEC=2.0`
- `BIRD_BATCH_SIZE=25`
- `BIRD_BATCH_COOLDOWN_SEC=900`
- `BIRD_429_COOLDOWN_SEC=900`
- `BIRD_MAX_CONSECUTIVE_429=0`

### Web 层：通过 XCrawl 做网页搜索

- `WEB_SEARCH_BACKEND=auto` 会按 `tavily -> brave -> xcrawl -> interface` 依次尝试
- 如果你显式指定了 `tavily`、`brave` 或 `xcrawl`，但对应凭证缺失，脚本不会偷偷切到别家，而是直接回落成 `interface` JSON
- `XCRAWL_API_KEY` 既可以让你显式走 XCrawl，也可以作为 `auto` 模式下的第三顺位兜底

只跑网页搜索层：

```bash
python3 scripts/fetch-web.py \
  --defaults config/defaults \
  --config workspace/config \
  --freshness pd \
  --output /tmp/td-web.json \
  --verbose
```

你最需要看这 3 个字段：

- `api_used`
- `topics_ok`
- `topics[].articles[]`

## 配置方式

- 默认配置在 `config/defaults/sources.json` 和 `config/defaults/topics.json`
- 用户覆盖配置在 `workspace/config/tech-news-digest-sources.json` 和 `workspace/config/tech-news-digest-topics.json`
- 覆盖规则：
  - `id` 相同：用你的配置覆盖默认项
  - 新 `id`：追加为新来源
  - `"enabled": false`：关闭内置来源

示例：

```json
{
  "sources": [
    {
      "id": "my-blog",
      "type": "rss",
      "enabled": true,
      "url": "https://myblog.com/feed",
      "topics": ["llm"]
    },
    {
      "id": "openai-blog",
      "enabled": false
    }
  ]
}
```

## 环境变量

`.env.example` 现在就是标准参考清单。你可以复制成 `.env`，再通过 `source .env` 导入当前 shell。

```bash
# X API 后端
export GETX_API_KEY=""
export TWITTERAPI_IO_KEY=""
export X_BEARER_TOKEN=""
export TWITTER_API_BACKEND="auto"

# Bird 本机登录态后端
export BIRD_CLI="bird"
export AUTH_TOKEN=""
export CT0=""
export BIRD_MAX_WORKERS="1"
export BIRD_REQUEST_INTERVAL_SEC="2.0"
export BIRD_BATCH_SIZE="25"
export BIRD_BATCH_COOLDOWN_SEC="900"
export BIRD_429_COOLDOWN_SEC="900"
export BIRD_MAX_CONSECUTIVE_429="0"

# 网页搜索后端
export TAVILY_API_KEY=""
export BRAVE_API_KEYS=""
export BRAVE_API_KEY=""
export XCRAWL_API_KEY=""
export WEB_SEARCH_BACKEND="auto"
export BRAVE_PLAN="free"

# GitHub
export GITHUB_TOKEN=""
```

## 常用命令

校验配置：

```bash
python3 scripts/validate-config.py --defaults config/defaults --verbose
```

跑完整流水线：

```bash
python3 scripts/run-pipeline.py \
  --defaults config/defaults \
  --config workspace/config \
  --hours 48 \
  --freshness pd \
  --archive-dir workspace/archive/tech-news-digest \
  --output /tmp/td-merged.json \
  --verbose
```

跑“抓取 + Markdown 日报”一体化命令：

```bash
python3 scripts/run-daily-digest.py \
  --defaults config/defaults \
  --config workspace/config \
  --archive-dir workspace/archive/tech-news-digest \
  --timezone Asia/Shanghai
```

跑轻量烟雾测试：

```bash
bash scripts/test-pipeline.sh --only rss,github,web --hours 24
```

跑单元测试：

```bash
python3 -m unittest discover -s tests -v
```

当前离线测试基线：70 项通过。

## 依赖

核心依赖：

```bash
python3 -m pip install -r requirements.txt
```

- `feedparser`：让 RSS 解析更稳
- `jsonschema`：让配置校验更稳

可选依赖：

```bash
python3 -m pip install weasyprint
```

- `weasyprint`：启用 PDF 生成

## 仓库地址

**GitHub**: [github.com/draco-agent/tech-news-digest](https://github.com/draco-agent/tech-news-digest)

## 相关引用

- [Awesome OpenClaw Use Cases](https://github.com/hesamsheikh/awesome-openclaw-usecases)

## 开源协议

MIT License，详见 [LICENSE](LICENSE)。
