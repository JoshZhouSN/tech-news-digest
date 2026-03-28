# Web Search XCrawl Review Report

- 日期：2026-03-29
- 分支：`feat/more-web-search-method`
- 审查范围：`main..HEAD`
- 审查方式：本地差异审查 + 单元测试 + 真实 smoke test

## 初审结论

### P1

1. `auto` 模式下 Brave 不可用时不会继续尝试 XCrawl

现象：
- 当前 `WEB_SEARCH_BACKEND=auto` 会先选 Tavily，再选 Brave，再选 XCrawl。
- 但实现里只要检测到存在 Brave key，就先进入 Brave 路径。
- 如果 `select_brave_key_and_limits()` 返回 `None`，代码会直接退回 `interface`，跳过已经配置好的 `XCRAWL_API_KEY`。

原因：
- 优先级判断和“Brave 实际可用性”判断分成了两步。
- 第二步失败后，没有继续沿着优先级链往下走。

影响：
- 用户明明已经配置 XCrawl，仍会在 Brave 配额耗尽或探测失败时丢失真实搜索结果。
- 这会让 `tavily -> brave -> xcrawl` 变成“有 Brave key 就先赌 Brave，失败后直接放弃”，和本次功能目标不一致。

建议修复：
- 仅在 `auto` 模式下，如果 Brave key 存在但最终拿不到可用 `api_key`，继续尝试 XCrawl。
- 显式 `WEB_SEARCH_BACKEND=brave` 时保持当前行为，仍然退回 `interface`，不要偷偷换后端。

## 修复状态

- 状态：已修复

### 修复内容

1. 在 `auto` 模式下，把后端选择补成真正的链式尝试：
   - `tavily` 没有成功主题结果时，继续尝试 `brave`
   - `brave` 没有可用 key，或有 key 但所有查询都失败时，继续尝试 `xcrawl`
2. 新增回归测试，覆盖三类情况：
   - Brave key 存在但探测不可用时，自动回退到 XCrawl
   - Tavily 实际查询全失败时，自动回退到 Brave
   - Brave 实际查询全失败时，自动回退到 XCrawl

### 复审结果

- P0：0
- P1：0
- 结论：可以进入后续合并准备步骤

### 复审证据

- `python3 -m unittest discover -s tests -v`：49 项通过
- 强制真实 smoke test：
  - 条件：`WEB_SEARCH_BACKEND=auto`，移除 `TAVILY_API_KEY`，注入一个不可用的 `BRAVE_API_KEY`，保留真实 `XCRAWL_API_KEY`
  - 结果：Brave 先被选中并全部返回错误，随后自动回退到 XCrawl
  - 输出：`api_used=xcrawl`、`topics_ok=4`、`total_articles=53`
