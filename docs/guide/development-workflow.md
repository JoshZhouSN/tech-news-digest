# 开发工作流

- 更新时间：2026-03-28
- 适用范围：日常开发、问题修复、小功能迭代

## 1. 开始改动前先确认什么

先判断你改的是哪一层：

- 改抓取能力：看 `fetch-*.py`
- 改配置结构：看 `config/defaults/*`、`scripts/config_loader.py`、`scripts/validate-config.py`
- 改日报排序和内容取舍：看 `scripts/merge-sources.py`
- 改输出样式：看 `references/templates/*` 或对应输出脚本

这样做的好处是可以先锁定影响范围，避免“只是改个字段”最后牵出整条链路。

## 2. 推荐的最小开发顺序

1. 先找出现象所在层
2. 先补或更新测试
3. 再改脚本
4. 先跑最小相关验证
5. 再跑全量单元测试
6. 最后同步更新文档

## 3. 常用验证命令

### 配置相关改动

```bash
python3 scripts/validate-config.py --defaults config/defaults --verbose
python3 -m unittest discover -s tests -v
```

### 合并逻辑改动

```bash
python3 -m unittest discover -s tests -v
```

如果只想快速验证某一块，也可以先跑：

```bash
python3 -m unittest tests.test_merge -v
python3 -m unittest tests.test_config -v
```

### 采集链路改动

优先从 `scripts/test-pipeline.sh` 入手做 smoke test，再决定是否跑整条管道。

```bash
bash scripts/test-pipeline.sh --only rss,github --hours 24
```

## 4. 新增一个数据源时要同步哪些地方

### 新增 RSS / Twitter / GitHub / Reddit 源

至少检查：

- `config/defaults/sources.json`
- `scripts/validate-config.py`
- `tests/test_config.py`
- 相关 README 或 `docs/memory-bank/project-facts.md`

### 新增主题

至少检查：

- `config/defaults/topics.json`
- `config/defaults/sources.json` 中的主题引用
- `scripts/config_loader.py`
- `scripts/validate-config.py`
- `tests/test_config.py`

## 5. 改评分规则时的额外要求

评分逻辑影响的是用户最终读到什么内容，所以这类改动不能只看“脚本有没有报错”。

最少要做三件事：

1. 为新规则补测试
2. 用现有夹具跑一遍，确认去重和排序没有反常
3. 更新文档，写清楚为什么改、用户会看到什么变化

## 6. 文档维护规则

- 改默认源数量、主题数量、依赖要求时，同步更新事实文档
- 改开发流程时，更新 `docs/guide/`
- 改产品定位、目标用户、交付方式时，更新 `docs/product/`
- 一次性分析和阶段结论写进 `docs/reports/`
