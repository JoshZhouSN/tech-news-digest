# Merge Readiness Review

- 审查时间：2026-03-31
- 审查范围：`main..HEAD`
- 当前分支：`feat/skill-bird-xcrawl-alignment`
- Base SHA：`581ebd69772581918cff5e97a88a8122d53980f1`
- Head SHA：`7d52555923f4f263dfe301a5ba9aa207588da534`
- 适用范围：本地待进入 `main` 的 4 个提交，包括 Bird 自动兜底、技能入口映射、流水线合并统计修正、对外文档与元数据对齐

## 1. 审查结论

- 本轮未发现未处理的 `P0` / `P1` 问题
- 当前分支相对 `main` 的新增改动，已经覆盖对应回归测试与运行验证
- 结论：在接受“外部接口稳定性仍受第三方平台与本机登录态影响”这一已知产品风险的前提下，可以进入合并步骤

## 2. 本轮重点核查了什么

### 2.1 X 层 auto 回退到 Bird

- 检查点：
  - `TWITTER_API_BACKEND=auto` 是否真实支持 `bird` 作为最后兜底
  - 当 API 凭证存在时，是否仍优先走 API，不会被 Bird 抢占
  - 文档与技能元数据是否和实际代码保持一致
- 结果：
  - `scripts/fetch-twitter.py` 已按 `getxapi -> twitterapiio -> official -> bird` 顺序选择后端
  - `tests/test_fetch_twitter.py` 已覆盖“缺 API 凭证时回退到 Bird”和“有 API 凭证时优先走 API”
  - README、`.env.example`、`SKILL.md`、`docs/` 已对齐当前行为

### 2.2 流水线合并统计口径

- 检查点：
  - `run-pipeline.py` 的控制台摘要和 `*.meta.json` 是否反映真实合并结果
  - 合并产物仅在 `output_stats.total_articles` 中给出统计时，是否仍能被正确读取
- 结果：
  - `scripts/run-pipeline.py` 已兼容读取 `output_stats.total_articles`
  - 新增回归测试 `tests/test_run_pipeline.py`
  - 本地冷启动验证中，终端摘要已从误报 `0` 修正为真实的 `Merge 47 items`

### 2.3 对外上手体验

- 检查点：
  - 首次运行没有 X / Web 凭证时，README 是否明确说明“能跑完，但覆盖率会下降”
  - 当前离线测试基线是否和仓库真实状态一致
  - agent 读取技能元数据时，是否会得到错误的安装或运行假设
- 结果：
  - README 与 README_CN 已补充无凭证首跑预期
  - 当前离线测试基线已同步为 `67` 项通过
  - `skills/tech-news-digest/*` 只是到根目录资产的符号链接，不引入额外行为分叉

## 3. 安全与稳定性复核

- secrets：
  - 未发现新增硬编码 token、cookie、私钥或 `.env` 值
  - Bird 仍通过环境变量或本机会话读凭证，没有把敏感值拼到命令参数里
- 外部输入：
  - 本轮新增改动主要是后端选择说明、统计口径修复与技能元数据同步，没有扩大外部输入处理面
- 外部依赖：
  - X 与网页搜索仍依赖第三方平台可用性和登录态/额度，不属于本轮引入的新风险

结论：

- 未发现新的高风险安全阻塞项
- 当前残余风险仍然是“第三方接口稳定性”，不是“仓库内凭证泄露或权限失控”

## 4. 残余风险

- Bird 自动兜底仍依赖本机 X 登录态或可用的 `AUTH_TOKEN` / `CT0`，不适合作为默认无人值守服务器模式
- 无 X / Web 凭证时，首轮运行虽然可以产出摘要，但覆盖率会明显下降
- GitHub Trending、RSS、Reddit 等真实抓取结果会随外部平台波动，公共 CI 仍无法完全覆盖

## 5. 验证证据

- `python3 scripts/validate-config.py --defaults config/defaults --verbose`
  - 结果：通过，`167` 个默认源与 `4` 个主题配置一致
- `python3 -m unittest discover -s tests -v`
  - 结果：`67` 项通过，退出码 `0`
- 干净环境冷启动：
  - 命令：`env -i ... /tmp/td-eval-venv/bin/python scripts/run-pipeline.py --defaults config/defaults --config workspace/config --hours 6 --freshness pd --archive-dir /tmp/td-eval-archive --output /tmp/td-eval-merged.json --verbose --force`
  - 结果：退出码 `0`，终端摘要显示 `Merge 47 items`
  - 产物：`/tmp/td-eval-merged.json` 中 `output_stats.total_articles = 47`

## 6. 合并建议

- 可以进入 `main` 合并步骤
- 如果目标是更新本地 `main`，下一步可以执行本地合并
- 如果目标是让远端协作方审阅，下一步更适合推分支并开 Pull Request
