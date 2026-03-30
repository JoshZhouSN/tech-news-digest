# 配置与运行指南

- 更新时间：2026-03-30
- 适用范围：本地运行、环境准备、联调排障

## 1. 本地准备

### 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

如果你只需要最基础能力，这个项目本身尽量依赖标准库；但为了 RSS 解析和配置校验更稳定，仍然建议装上 `requirements.txt`。

### 准备环境变量

项目根目录提供了 [.env.example](/Users/Josh/Projects/tech-news-digest/.env.example)，可以直接作为本地环境变量清单参考。

推荐方式：

```bash
cp .env.example .env
# 编辑 .env
set -a
source .env
set +a
```

关键原则：

- 没有密钥时，项目不一定完全失败
- 但对应来源会被跳过，最终日报覆盖率会下降
- Bird 不是 API key 模式，它依赖本机 X 网页登录态或 `AUTH_TOKEN` / `CT0`

### 准备用户覆盖目录

```bash
mkdir -p workspace/config workspace/archive/tech-news-digest
```

## 2. X / Bird 运行说明

- `TWITTER_API_BACKEND=auto` 会按 `getxapi -> twitterapiio -> official -> bird` 依次尝试
- 当前面 API 凭证都不可用、且 Bird CLI 登录态可用时，`auto` 会自动回退到 Bird
- 你仍然可以显式传 `--backend bird` 或设置 `TWITTER_API_BACKEND=bird`，强制走 Bird
- Bird 适合“有人在本机登录过 X、希望直接读取动态”的场景，不适合作为默认服务器后端
- Bird CLI 默认命令是 `bird`，也可以通过 `BIRD_CLI="bunx @steipete/bird"` 覆盖

建议先验证 Bird 本身能否拿到当前登录态：

```bash
bird whoami --plain
```

Bird 节奏控制参数：

- `BIRD_MAX_WORKERS`：Bird 抓取并发数，默认 `1`
- `BIRD_REQUEST_INTERVAL_SEC`：账号之间的等待秒数，默认 `2`
- `BIRD_BATCH_SIZE`：每批账号数，默认 `25`
- `BIRD_BATCH_COOLDOWN_SEC`：每批结束后的额外冷却秒数，默认 `900`
- `BIRD_429_COOLDOWN_SEC`：每次遇到 `429` 后的冷却秒数，默认 `900`
- `BIRD_MAX_CONSECUTIVE_429`：连续 `429` 达到多少次后触发旧止损逻辑，默认 `0`，表示关闭

默认恢复策略：

- 每成功完成 `25` 个账号后，Bird 自动休眠 `15` 分钟，再从下一个账号继续
- 每次遇到 `429` 时，Bird 自动休眠 `15` 分钟，然后重试当前账号，不会直接跳过断点

## 3. Web 搜索运行说明

网页搜索当前真实优先级：

- `WEB_SEARCH_BACKEND=auto` 时：`tavily -> brave -> xcrawl -> interface`
- 如果显式指定 `tavily`、`brave` 或 `xcrawl`，但缺少对应密钥，脚本不会自动改用别家，而是直接输出 interface JSON 兜底

这意味着：

- 想让系统自动找可用供应商，用 `auto`
- 想固定某一家，就显式指定它，但要自己保证凭证可用

## 4. 用户覆盖配置

建议目录：

```bash
mkdir -p workspace/config
cp config/defaults/sources.json workspace/config/tech-news-digest-sources.json
cp config/defaults/topics.json workspace/config/tech-news-digest-topics.json
```

当前代码里的真实文件名约定是：

- `workspace/config/tech-news-digest-sources.json`
- `workspace/config/tech-news-digest-topics.json`

不要只创建 `sources.json` 或 `topics.json`，否则覆盖逻辑不会生效。

## 5. 常见运行方式

### 先做配置校验

```bash
python3 scripts/validate-config.py --defaults config/defaults --verbose
```

### 跑整条管道

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

### 单独验证网页搜索层

```bash
python3 scripts/fetch-web.py \
  --defaults config/defaults \
  --config workspace/config \
  --freshness pd \
  --output /tmp/td-web.json \
  --verbose
```

重点看三件事：

- `api_used` 是否符合预期
- `topics_ok` 是否大于 `0`
- `topics[].articles[]` 是否已经有统一字段结构

### 单独验证 Bird 的 X 层

```bash
python3 scripts/fetch-twitter.py \
  --defaults config/defaults \
  --config workspace/config \
  --hours 24 \
  --backend bird \
  --output /tmp/td-twitter.json \
  --verbose
```

### 跑轻量烟雾测试

```bash
bash scripts/test-pipeline.sh --only rss,github,web --hours 24
```

### 跑单元测试

```bash
python3 -m unittest discover -s tests -v
```

当前离线基线：`65` 项通过。

## 6. 排障入口

### 问题：某类内容突然明显变少

优先检查：

- 相关环境变量是否失效
- 外部平台是否限流
- `scripts/test-pipeline.sh` 单独跑该来源是否失败
- 是否是 `config/defaults/sources.json` 中被误关掉
- 如果使用 Bird，再检查本机 X 登录态是否还有效，或 `AUTH_TOKEN` / `CT0` 是否过期

如果是网页搜索层，还要额外检查：

- `WEB_SEARCH_BACKEND` 是否被显式固定到了一个当前没有密钥的后端
- 是否误以为系统会从显式 `xcrawl` 回退到 `tavily` 或 `brave`
- `/tmp/td-web.json` 里的 `api_used` 到底是什么

### 问题：脚本成功但日报质量变差

优先检查：

- `scripts/merge-sources.py` 的评分规则是否改过
- 去重阈值是否改过
- 主题优先级是否变化
- 历史归档是否错误影响去重惩罚

### 问题：用户覆盖配置不生效

优先检查：

- 文件名是否是 `tech-news-digest-sources.json` / `tech-news-digest-topics.json`
- `id` 是否与默认配置匹配
- JSON 是否合法

## 7. 输出物位置

按当前代码，可预期的输出位置包括：

- `/tmp/td-merged.json`
- `/tmp/td-merged.meta.json`
- `/tmp/td-twitter.json`
- `/tmp/td-web.json`
- `/tmp/td-email.html`
- `/tmp/td-digest.pdf`
- `workspace/archive/tech-news-digest/`

如果后续改输出目录，记得同步更新 README、`.env.example` 和这里的运维文档，否则最容易出现“生成成功但找不到文件”的假故障。
