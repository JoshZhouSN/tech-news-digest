# 项目文档索引

- 更新时间：2026-03-31
- 适用范围：`tech-news-digest` 仓库开发、维护、交接
- 事实来源：以当前代码、测试、配置文件为准；若与外部说明冲突，优先相信代码

## 1. 这套文档现在负责什么

这套文档的目标，已经从“修复 README 漂移”变成“保证新接手的人照文档就能安装、运行、排查”。

当前文档已经与仓库现状对齐的关键事实：

- 默认数据源总数：`167`
- 默认启用数据源：`165`
- 抓取步骤：`6`
- X 层支持 Bird 显式启用，并可在 auto 模式下作为最后兜底
- Web 搜索支持 `tavily -> brave -> xcrawl -> interface` 自动兜底
- 离线单元测试：`67` 项通过

## 2. 文档地图

- [memory-bank/project-facts.md](/Users/Josh/Projects/tech-news-digest/docs/memory-bank/project-facts.md)：项目事实总览，适合第一次接手时快速建立全局认知
- [memory-bank/architecture.md](/Users/Josh/Projects/tech-news-digest/docs/memory-bank/architecture.md)：数据流、脚本职责、输入输出边界
- [memory-bank/current-status.md](/Users/Josh/Projects/tech-news-digest/docs/memory-bank/current-status.md)：当前质量状态、剩余风险、维护建议
- [guide/development-workflow.md](/Users/Josh/Projects/tech-news-digest/docs/guide/development-workflow.md)：日常开发建议、改动路径、最小验证顺序
- [guide/configuration-and-operations.md](/Users/Josh/Projects/tech-news-digest/docs/guide/configuration-and-operations.md)：本地安装、环境变量、运行与排障入口
- [product/product-context.md](/Users/Josh/Projects/tech-news-digest/docs/product/product-context.md)：产品定位、目标用户、非目标范围
- [reports/2026-03-28-project-analysis-initialization.md](/Users/Josh/Projects/tech-news-digest/docs/reports/2026-03-28-project-analysis-initialization.md)：初始化分析与原始判断
- [reports/2026-03-29-bird-coverage-optimization.md](/Users/Josh/Projects/tech-news-digest/docs/reports/2026-03-29-bird-coverage-optimization.md)：Bird 覆盖率调优实验记录

## 3. 当前项目快照

- 语言与运行时：Python `3.8+`
- 依赖策略：标准库优先，`feedparser` 与 `jsonschema` 为增强依赖，`weasyprint` 为 PDF 可选依赖
- 主入口：`scripts/run-pipeline.py`
- 本地环境模板：`.env.example`
- 配置入口：`config/defaults/` + `workspace/config/`
- 当前测试结果：`67` 项单元测试通过
- CI：`.github/workflows/test.yml` 在 Python `3.9` 和 `3.12` 上运行

## 4. 建议阅读顺序

1. 先读 [memory-bank/project-facts.md](/Users/Josh/Projects/tech-news-digest/docs/memory-bank/project-facts.md)
2. 再读 [memory-bank/architecture.md](/Users/Josh/Projects/tech-news-digest/docs/memory-bank/architecture.md)
3. 准备跑本地环境或联调时读 [guide/configuration-and-operations.md](/Users/Josh/Projects/tech-news-digest/docs/guide/configuration-and-operations.md)
4. 准备改代码前读 [guide/development-workflow.md](/Users/Josh/Projects/tech-news-digest/docs/guide/development-workflow.md)
5. 做产品取舍或改定位时读 [product/product-context.md](/Users/Josh/Projects/tech-news-digest/docs/product/product-context.md)
