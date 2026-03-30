# 架构与数据流

- 更新时间：2026-03-28
- 适用范围：理解系统结构、评估改动影响、定位问题

## 1. 总体结构

这个项目不是一个长驻服务，而是一组按步骤串起来的脚本。

核心思路：

1. 并行抓取不同来源的数据
2. 把各来源结果收敛成统一文章模型
3. 按质量分、时间、重复度做筛选
4. 产出供下游消息模板或报告模板消费的中间结果

## 2. 核心数据流

```text
run-pipeline.py
  -> fetch-rss.py
  -> fetch-twitter.py
  -> fetch-github.py
  -> fetch-github.py --trending
  -> fetch-reddit.py
  -> fetch-web.py
  -> merge-sources.py
  -> enrich-articles.py (可选)
  -> references/templates/* 或下游分发脚本
```

## 3. 脚本职责拆分

### 调度层

- `scripts/run-pipeline.py`
  负责并发启动抓取脚本、收集阶段结果、执行合并、按需触发富化

### 配置层

- `scripts/config_loader.py`
  负责把默认配置和 `workspace/config` 中的覆盖配置合并
- `scripts/validate-config.py`
  负责检查结构是否合法、主题引用是否一致、ID 是否冲突

### 采集层

- `scripts/fetch-rss.py`
- `scripts/fetch-twitter.py`
- `scripts/fetch-github.py`
- `scripts/fetch-reddit.py`
- `scripts/fetch-web.py`

这些脚本的共同目标，是把来源各异的数据转成后续可统一处理的结构。

其中 `fetch-twitter.py` 目前支持官方 API、GetXAPI、twitterapi.io，以及显式可选的 Bird CLI。前 3 种更偏“密钥驱动”，Bird 更偏“本机网页登录态驱动”。

### 处理层

- `scripts/merge-sources.py`
  负责打分、去重、域名限额、主题归组，是“日报质量”最关键的一层
- `scripts/enrich-articles.py`
  为高分文章补全文内容，提升最终摘要质量

### 输出层

- `scripts/generate-pdf.py`
- `scripts/sanitize-html.py`
- `scripts/send-email.py`
- `references/templates/discord.md`
- `references/templates/email.md`
- `references/templates/pdf.md`

这层决定“怎么展示”，不决定“抓什么”。

## 4. 合并层的业务意义

`merge-sources.py` 是项目最像“产品核心”的地方，因为它定义了哪些内容更值得进日报。

从代码可确认的关键规则：

- 多源交叉出现会加分
- 优先级源会加分
- 新近内容会加分
- Twitter/X 内容会按互动数据加分
- 标题或 URL 很像的内容会被视为重复
- 历史已出现内容会降权
- 主题归组时，一篇内容只会归到一个主主题

这意味着如果你改了评分或分组逻辑，影响的不只是技术细节，而是“用户看到的日报结构和重点”。

## 5. 配置覆盖模型

配置设计采用“默认配置 + 用户覆盖”的方式：

- 默认源：`config/defaults/sources.json`
- 默认主题：`config/defaults/topics.json`
- 用户覆盖：`workspace/config/tech-news-digest-sources.json`
- 用户覆盖：`workspace/config/tech-news-digest-topics.json`

覆盖规则：

- 同一 `id`：用户版本覆盖默认版本
- 新 `id`：追加
- 源配置里若设置 `enabled: false`：可关闭内置源

这套设计的好处是升级默认配置时不必整份复制；代价是字段变更后更容易出现“默认配置、覆盖配置、校验规则”不同步。

## 6. 当前质量门槛

- 单元测试：42 项通过
- CI：仅验证单元测试
- 夹具来源：`tests/fixtures/*.json`

这说明目前项目已经有稳定的纯离线回归能力，但还没有把真实外部接口联调放进 CI，所以和外部平台有关的问题仍需要人工或脚本级 smoke test 补位。
