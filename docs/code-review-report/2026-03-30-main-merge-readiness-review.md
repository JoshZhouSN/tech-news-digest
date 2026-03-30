# Main Merge Readiness Review

- 审查时间：2026-03-30
- 审查范围：`origin/main..HEAD`
- 当前分支：`fix/final-report-generation`
- Base SHA：`06d1cb67c4ac1dd9de90beeaae97b9067071308d`
- Head SHA：`f6d0f7b0f0f05cf3210d1a5fb76e544b994a2690`
- 适用范围：本地待进入 `main` 的 17 个提交，包括 Bird X 后端、XCrawl Web 搜索后端、README 与 docs 对齐、相关测试补充

## 1. 审查结论

- 本地 `main` 与当前分支已经指向同一提交：`f6d0f7b0f0f05cf3210d1a5fb76e544b994a2690`
- 相对 `origin/main`，当前待落地主差异为 `17` 个提交
- 本轮未发现未处理的 `P0` / `P1` 问题
- 结论：在接受“外部接口稳定性依赖第三方平台”这一已知产品风险的前提下，可进入本地合并收尾与主分支同步步骤

## 2. 本轮重点核查了什么

### 2.1 Bird X 后端

- 检查点：
  - 凭证是否仍通过环境变量读取，而不是写死到代码或命令参数
  - `BIRD_MAX_CONSECUTIVE_429=0` 是否真的表示关闭连续 `429` 止损
  - 限流恢复策略是否有测试覆盖
- 结果：
  - Bird 仍通过 `AUTH_TOKEN` / `CT0` / 本机会话读取登录态，没有把敏感值拼进命令行
  - `scripts/fetch-twitter.py` 已允许 `BIRD_MAX_CONSECUTIVE_429` 取 `0`
  - 单元测试已覆盖顺序抓取、批次冷却、`429` 冷却、同源重试与关闭止损配置

### 2.2 Web 搜索自动回退链

- 检查点：
  - `WEB_SEARCH_BACKEND=auto` 是否真按 `tavily -> brave -> xcrawl -> interface` 走完整链路
  - 显式指定后端时，是否会因为凭证缺失偷偷切去别家
  - 输出结构是否统一，避免下游合并层读出歧义
- 结果：
  - `scripts/fetch-web.py` 在 `auto` 模式下，已按成功主题数继续尝试后续后端
  - 显式指定 `tavily` / `brave` / `xcrawl` 但凭证缺失时，会回落到 `interface`，不会静默切换真实提供方
  - `build_topic_result()` 已统一不同提供方的主题输出结构，相关单元测试覆盖 Tavily / Brave / XCrawl 三条路径

### 2.3 文档与运行方式对齐

- 检查点：
  - README、`.env.example`、`docs/` 是否和当前代码行为一致
  - 关键运行命令、默认后端规则、环境变量命名是否前后一致
- 结果：
  - README、README_CN、`.env.example`、`docs/` 已和当前默认源数量、Bird 显式启用规则、XCrawl 回退顺序对齐
  - 当前文档没有发现“文档说能这样配，代码却不是这样跑”的阻塞级偏差

## 3. 复用的既有审查结论

- [2026-03-29-web-search-xcrawl-review.md](/Users/Josh/Projects/tech-news-digest/docs/code-review-report/2026-03-29-web-search-xcrawl-review.md)
  - 已确认并修复 `auto` 模式下 Brave 不可用时不会继续尝试 XCrawl 的 `P1`
- [2026-03-30-bird-merge-review.md](/Users/Josh/Projects/tech-news-digest/docs/code-review-report/2026-03-30-bird-merge-review.md)
  - 已确认并修复 `BIRD_MAX_CONSECUTIVE_429=0` 与文档约定不一致的问题

本轮复审未发现这些已修复问题出现回归。

## 4. 安全复核

按 secrets、外部输入、第三方接口三类风险复核：

- secrets：
  - 未发现硬编码 token、cookie、私钥
  - Bird 仍通过环境变量或本机会话拿凭证，不在日志里主动打印敏感值
- 外部输入：
  - Web 搜索返回被标准化后再进入下游，显式缺凭证时退回 `interface`，避免误把“没配置好”当成“拿到了真实结果”
- 第三方接口：
  - Bird 与 XCrawl 都属于外部依赖，真正的不确定性来自平台返回和限流，不是仓库内的秘密泄露路径

结论：

- 未发现新的高风险安全阻塞项
- 当前主要是“可用性与稳定性风险”，不是“凭证外泄与权限失控风险”

## 5. 残余风险

- `origin/main` 仍落后本地 `17` 个提交；如果只做本地分支切换，不做后续推送，远端主分支不会真正更新
- Bird 依赖 X 的私有网页接口与本机会话，平台策略变化仍可能直接影响 X 层产出
- Web 搜索链虽然已有回退逻辑，但真实效果仍取决于各供应方的额度、可用性与返回结构稳定性

## 6. 验证证据

- `python3 scripts/validate-config.py --defaults config/defaults --verbose`
  - 结果：通过，`167` 个默认源与 `4` 个主题配置一致
- `python3 -m unittest discover -s tests -v`
  - 结果：`65` 项通过，退出码 `0`

## 7. 合并建议

- 可以进入 `main` 合并收尾
- 由于本地 `main` 已与当前分支同 SHA，这次“合并”本质上是确认门禁通过后切回 `main`
- 如果你的真实目标是让 GitHub 上的 `main` 也更新，还需要在本地切到 `main` 后执行推送步骤
