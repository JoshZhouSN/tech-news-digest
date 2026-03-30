# 项目事实总览

- 更新时间：2026-03-28
- 适用范围：项目认知建立、任务拆分、技术交接

## 1. 项目是什么

`tech-news-digest` 是一个自动化科技资讯汇总项目。它从多个来源抓取近时段内容，做去重、评分和主题归类，再为 Discord、邮件、PDF 等输出形态提供统一输入。

对产品来说，它解决的是“原始信息太分散、人工筛选成本高”的问题；对开发来说，它本质上是一条可扩展的数据采集与整理管道。

## 2. 当前代码里确认过的事实

- 默认数据源总数：`167`
- 当前启用数据源：`165`
- 主题数：`4`
- 主题 ID：`llm`、`ai-agent`、`crypto`、`frontier-tech`
- 优先级源数量：`64`
- 主语言：Python
- Python 版本要求：`3.8+`
- 测试方式：`unittest`
- CI 方式：GitHub Actions

## 3. 仓库结构

- `scripts/`：核心业务脚本，包含抓取、合并、富化、校验、输出
- `config/defaults/`：默认源配置与主题配置
- `tests/`：单元测试和真实抓取结果夹具
- `references/`：摘要提示词和输出模板
- `.github/workflows/`：自动化测试流程

## 4. 关键入口

### 运行整条管道

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

### 跑单元测试

```bash
python3 -m unittest discover -s tests -v
```

### 跑配置校验

```bash
python3 scripts/validate-config.py --defaults config/defaults --verbose
```

## 5. 已知外部依赖

- Twitter/X：默认依赖 `GETX_API_KEY`、`TWITTERAPI_IO_KEY` 或 `X_BEARER_TOKEN`；也可显式走 Bird，本机使用 `BIRD_CLI` + 浏览器登录态或 `AUTH_TOKEN` / `CT0`
- Web Search：依赖 `TAVILY_API_KEY`、`BRAVE_API_KEY` / `BRAVE_API_KEYS` 或 `XCRAWL_API_KEY`
- GitHub：`GITHUB_TOKEN` 可提升限流表现
- PDF：`weasyprint`

这些依赖不是“项目能不能启动”的门槛，但会直接影响可抓取的数据覆盖率。换句话说，缺少密钥时项目不会完全失效，但日报质量会下降。

当前网页搜索后端真实优先级：

- `auto` 模式：`tavily -> brave -> xcrawl -> interface`
- 显式指定某个后端但缺少对应凭证时：不会偷偷切到别家，而是直接退回 interface 输出

## 6. 现阶段最重要的开发约束

- 项目定位是“标准库优先”，不要轻易引入重量级依赖
- 很多脚本通过子进程拼接成总流程，改接口时要注意前后脚本的输入输出兼容
- 配置支持默认值加用户覆盖，新增字段时要同时考虑默认配置、覆盖逻辑和校验逻辑
- `tests/fixtures/` 是当前稳定回归的基础，改合并逻辑时优先补夹具和测试
