# 项目事实总览

- 更新时间：2026-03-30
- 适用范围：项目认知建立、任务拆分、技术交接

## 1. 项目是什么

`tech-news-digest` 是一条自动化科技资讯汇总流水线。它把 RSS、X、网页搜索、GitHub、Reddit 等来源抓到的内容，整理成统一结构，再做去重、评分、主题归类，最后交给下游模板或投递脚本继续消费。

对产品来说，它解决的是“信息太分散、人工筛选太慢”的问题；对开发来说，它本质上是一条可扩展的数据采集和排序管道。

## 2. 当前代码里确认过的事实

- 默认数据源总数：`167`
- 默认启用数据源：`165`
- 主题数：`4`
- 主题 ID：`llm`、`ai-agent`、`crypto`、`frontier-tech`
- 优先级源数量：`64`
- 主语言：Python
- Python 版本要求：`3.8+`
- 测试方式：`unittest`
- 当前离线测试结果：`65` 项通过
- CI 方式：GitHub Actions

## 3. 仓库结构

- `scripts/`：核心业务脚本，包含抓取、合并、富化、校验、输出
- `config/defaults/`：默认源配置与主题配置
- `tests/`：单元测试和真实抓取结果夹具
- `references/`：摘要提示词和输出模板
- `docs/`：项目事实、运行指南、阶段报告
- `.env.example`：本地环境变量参考模板

## 4. 关键入口

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

### 跑配置校验

```bash
python3 scripts/validate-config.py --defaults config/defaults --verbose
```

### 跑单元测试

```bash
python3 -m unittest discover -s tests -v
```

### 单独验证 Bird

```bash
python3 scripts/fetch-twitter.py \
  --defaults config/defaults \
  --config workspace/config \
  --hours 24 \
  --backend bird \
  --output /tmp/td-twitter.json \
  --verbose
```

### 单独验证 XCrawl

```bash
python3 scripts/fetch-web.py \
  --defaults config/defaults \
  --config workspace/config \
  --freshness pd \
  --output /tmp/td-web.json \
  --verbose
```

## 5. 已知外部依赖

- X API：`GETX_API_KEY`、`TWITTERAPI_IO_KEY` 或 `X_BEARER_TOKEN`
- Bird：`BIRD_CLI` + 本机浏览器登录态，或 `AUTH_TOKEN` / `CT0`
- Web Search：`TAVILY_API_KEY`、`BRAVE_API_KEY` / `BRAVE_API_KEYS`、`XCRAWL_API_KEY`
- GitHub：`GITHUB_TOKEN` 可提升限流表现
- PDF：`weasyprint`

这些依赖不是“项目能不能启动”的硬门槛，但会直接决定抓取覆盖率。换句话说，缺少密钥时项目可能还能跑完，但日报质量会下降。

当前搜索相关后端真实规则：

- X 层：`TWITTER_API_BACKEND=auto` 会按 `getxapi -> twitterapiio -> official -> bird` 依次尝试；当前面 API 不可用且 Bird CLI 可用时，会自动回退到 Bird
- Web 层：`WEB_SEARCH_BACKEND=auto` 会按 `tavily -> brave -> xcrawl -> interface` 依次尝试
- 显式指定 `tavily`、`brave` 或 `xcrawl` 但缺少凭证时：不会偷偷切到别家，而是直接退回 interface 输出

## 6. 现阶段最重要的开发约束

- 项目定位是“标准库优先”，不要轻易引入重量级依赖
- 多个脚本通过子进程拼接成总流程，改接口时要同时看前后脚本的输入输出
- 配置支持“默认值 + 用户覆盖”，新增字段时要同步考虑默认配置、覆盖逻辑和校验逻辑
- `tests/fixtures/` 是当前稳定回归的基础，改合并逻辑时优先补夹具和测试
- 每次调整默认源数量、后端优先级或环境变量，都要同步更新 README、`.env.example` 和 `docs/`
