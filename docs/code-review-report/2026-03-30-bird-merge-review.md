# Bird Merge Review

- 审查时间：2026-03-30
- 审查范围：`main...feat/x-bird-integration`
- Base SHA：`eac2c08ef1db20368212f0eaca3e5871e45f3b7f`
- Head SHA：`177b8794bb6f729939e5babe430aed8d882cc23a`
- 适用范围：Bird 后端接入、限流节奏控制、断点续跑、相关文档与测试

## 1. 审查结论

- 初审发现 1 个会影响合并的一致性问题，已修复
- 当前未发现未处理的 `P0` / `P1` 问题
- 结论：在保留当前 Bird 产品定位的前提下，可进入合并阶段

## 2. 已修复问题

### [已修复] `BIRD_MAX_CONSECUTIVE_429=0` 与文档约定不一致

- 现象：文档说明显式配置 `BIRD_MAX_CONSECUTIVE_429=0` 可以关闭旧的连续 `429` 止损
- 原因：`scripts/fetch-twitter.py` 中 `_get_env_int()` 默认最小值是 `1`，导致显式传入 `0` 时被抬成 `1`
- 影响：默认值虽然能工作，但一旦运行环境显式设置了 `BIRD_MAX_CONSECUTIVE_429=0`，实际行为会和文档不一致，可能在第一次 `429` 后错误触发旧止损
- 处理：在 Bird 后端读取 `BIRD_MAX_CONSECUTIVE_429` 时改为 `minimum=0`，并补回归测试

## 3. 安全复核

结合本次变更范围，重点检查了以下几项：

- 凭据处理：通过环境变量读取 `AUTH_TOKEN` / `CT0`，未发现硬编码凭据
- 仓库落盘：未把敏感值写入源码、测试、示例配置或提交内容
- 外部调用：Bird CLI 调用继承进程环境，不会把凭据拼接进命令参数
- 错误输出：现有实现记录的是 Bird 返回的错误摘要，未主动打印 token 值

结论：

- 未发现新的高风险安全问题
- 当前 Bird 能力仍然属于“本机操作型后端”，不建议把带网页登录态的运行方式直接搬到默认无人值守服务器场景

## 4. 残余风险

- Bird 仍然依赖 X 的私有网页接口，平台策略变化会直接影响稳定性
- 现在的 `429` 处理是“长冷却 + 断点重试”，更接近真实行为，但仍然依赖当前会话特征，后续可能需要继续调参
- 如果某个账号长期处于持续 `429` 状态，当前策略会持续等待并重试；这是有意保留的产品选择，不是本次审查阻塞项

## 5. 验证证据

- `python3 -m unittest tests.test_fetch_twitter -v`
- `python3 -m unittest tests.test_merge tests.test_config tests.test_fetch_twitter -v`
- `python3 scripts/validate-config.py --defaults config/defaults --verbose`
- 真实 Bird 全量实验：`bash scripts/test-pipeline.sh --only twitter --twitter-backend bird --hours 24 --keep`
  - 输出目录：`/tmp/tech-digest-test-1wwhRs`
  - 结果：`48/48` Twitter 源成功，`47` 篇输入，`45` 篇合并后文章

## 6. 合并建议

- 可以合并
- 合并后建议保留当前默认值：
  - `BIRD_BATCH_SIZE=25`
  - `BIRD_BATCH_COOLDOWN_SEC=900`
  - `BIRD_429_COOLDOWN_SEC=900`
- 如果后续 Bird 覆盖率再次下降，优先重复“恢复窗口测量”实验，不要先把冷却时间往下砍
