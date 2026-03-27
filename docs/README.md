# 项目文档索引

- 更新时间：2026-03-28
- 适用范围：`tech-news-digest` 仓库开发、维护、交接
- 事实来源：以当前代码、测试、配置文件为准；若与外部说明冲突，优先相信代码

## 1. 这套文档解决什么问题

这个项目已经能跑，但仓库里的公开说明和代码现状已经出现偏差。最明显的例子是：

- README 仍写 `151` 个数据源
- 实际 `config/defaults/sources.json` 中共有 `167` 个源
- 其中当前启用 `165` 个
- 类型分布为 `rss: 78`、`twitter: 48`、`github: 28`、`reddit: 13`

这意味着后续开发如果只看 README，容易在产品判断、测试预期和改动评估上产生误差。当前 `docs/` 的目标，就是把“代码里真实存在的东西”整理成一套可直接参考的开发文档。

## 2. 文档地图

- [memory-bank/project-facts.md](/Users/Josh/Projects/tech-news-digest/docs/memory-bank/project-facts.md)：项目事实总览，适合第一次接手时快速建立全局认知
- [memory-bank/architecture.md](/Users/Josh/Projects/tech-news-digest/docs/memory-bank/architecture.md)：数据流、脚本职责、输入输出边界
- [memory-bank/current-status.md](/Users/Josh/Projects/tech-news-digest/docs/memory-bank/current-status.md)：当前质量状态、风险、文档漂移点
- [guide/development-workflow.md](/Users/Josh/Projects/tech-news-digest/docs/guide/development-workflow.md)：日常开发建议、改动路径、最小验证顺序
- [guide/configuration-and-operations.md](/Users/Josh/Projects/tech-news-digest/docs/guide/configuration-and-operations.md)：配置覆盖、环境变量、运行与排障入口
- [product/product-context.md](/Users/Josh/Projects/tech-news-digest/docs/product/product-context.md)：产品定位、目标用户、非目标范围
- [reports/2026-03-28-project-analysis-initialization.md](/Users/Josh/Projects/tech-news-digest/docs/reports/2026-03-28-project-analysis-initialization.md)：本次初始化分析和结论

## 3. 当前项目快照

- 语言与运行时：Python 3.8+
- 依赖策略：标准库优先，`feedparser` 与 `jsonschema` 为增强依赖，`weasyprint` 为 PDF 可选依赖
- 主入口：`scripts/run-pipeline.py`
- 测试命令：`python3 -m unittest discover -s tests -v`
- 当前测试结果：42 项通过
- CI：`.github/workflows/test.yml` 在 Python `3.9` 和 `3.12` 上运行单元测试

## 4. 建议阅读顺序

1. 先读 [memory-bank/project-facts.md](/Users/Josh/Projects/tech-news-digest/docs/memory-bank/project-facts.md)
2. 再读 [memory-bank/architecture.md](/Users/Josh/Projects/tech-news-digest/docs/memory-bank/architecture.md)
3. 准备改代码前读 [guide/development-workflow.md](/Users/Josh/Projects/tech-news-digest/docs/guide/development-workflow.md)
4. 涉及配置或联调时读 [guide/configuration-and-operations.md](/Users/Josh/Projects/tech-news-digest/docs/guide/configuration-and-operations.md)
5. 做产品取舍或改定位时读 [product/product-context.md](/Users/Josh/Projects/tech-news-digest/docs/product/product-context.md)
