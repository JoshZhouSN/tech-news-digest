# 配置与运行指南

- 更新时间：2026-03-28
- 适用范围：本地运行、环境准备、联调排障

## 1. 本地准备

### 安装依赖

```bash
python3 -m pip install -r requirements.txt
```

如果你只需要最基础能力，这个项目本身也尽量依赖标准库；但为了 RSS 解析和配置校验更稳定，还是建议装上 `requirements.txt`。

### 环境变量

项目根目录新增了 [.env.example](/Users/Josh/Projects/tech-news-digest/.env.example)，可以直接作为本地环境变量清单参考。

关键原则：

- 没有密钥时，项目不一定完全失败
- 但对应来源会被跳过，最终日报覆盖率会下降

## 2. 用户覆盖配置

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

## 3. 常见运行方式

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

### 只做配置验证

```bash
python3 scripts/validate-config.py --defaults config/defaults --verbose
```

### 只做轻量烟雾测试

```bash
bash scripts/test-pipeline.sh --only rss,github --hours 24
```

## 4. 排障入口

### 问题：某类内容突然明显变少

优先检查：

- 相关环境变量是否失效
- 外部平台是否限流
- `scripts/test-pipeline.sh` 单独跑该来源是否失败
- 是否是 `config/defaults/sources.json` 中被误关掉

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

## 5. 输出物位置

按当前代码与技能说明，可预期的输出位置包括：

- `/tmp/td-*.json`
- `/tmp/td-email.html`
- `/tmp/td-digest.pdf`
- `workspace/archive/tech-news-digest/`

如果后续改输出目录，记得同步更新技能说明和这里的运维文档，否则最容易出现“生成成功但找不到文件”的假故障。
