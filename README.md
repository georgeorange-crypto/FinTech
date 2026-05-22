# global-macro-morning-brief

每天早上自动生成的全球经济与跨资产市场晨报系统。项目从一个能产出报告的 MVP，升级为偏 **Research Radar** 的宏观与跨资产信息雷达：它会采集公开 RSS、主要资产行情、加密资产、A 股指数、FRED 宏观指标、SEC 披露和用户自有研报文件，并生成 Markdown、HTML、PNG 图表、结构化事件数据库和静态首页 dashboard。

> Not financial advice / 非投资建议。本项目仅供个人学习、研究与信息整理，不做自动交易，不构成投资建议。

## 截图区域

生成报告后，可打开 `public/index.html` 查看 dashboard、最近 30 天报告列表和最新晨报。截图可放在 `docs/screenshots/`，再在这里替换为真实图片。

## 功能列表

- 公开 RSS 新闻采集、去重、关键词过滤、事件分类和重要性分桶
- 美股 ETF、港股、美元、美债、VIX、商品行情采集
- CoinGecko 加密资产行情采集，支持无 API key 模式
- AKShare A 股指数采集，失败时不影响主流程
- FRED 宏观指标采集，需要 `FRED_API_KEY`
- SEC watchlist 披露追踪，需要合规 `SEC_USER_AGENT`
- 计算 1D、5D、1M、YTD、20D 波动率、MA20、MA60、RSI14 和趋势标签
- 生成跨资产市场状态：risk_on、risk_off、rates_shock、inflation_shock、dollar_liquidity_tightening、crypto_specific、mixed、unknown
- 为新闻生成自然语言“为什么重要”和逐资产影响解释
- 生成 `reports/YYYY-MM-DD.md`、`reports/YYYY-MM-DD.html`、`public/index.html`、`public/metadata.json`
- 生成结构化文件：`events.json`、`news_analysis.json`、`market_narrative.json`
- 追加历史库：`data/history/events.jsonl`、`data/history/market_snapshots.jsonl`
- GitHub Actions 每天 Asia/Taipei 06:00 自动运行，并支持手动触发

## 数据源与合规

配置位于 `config/`：

- `config/rss_feeds.yml`：公开 RSS 源
- `config/assets.yml`：资产分组
- `config/macro_series.yml`：FRED 宏观序列
- `config/watchlist_cik.yml`：SEC 公司 watchlist
- `config/importance_rules.yml`：事件分类、tier 和 routine 规则
- `config/asset_impact_rules.yml`：资产影响方向、强度和解释
- `config/report_profile.yml`：晨报偏好

项目不会绕过 WSJ、Bloomberg、FT、Reuters 等付费墙。对付费媒体或机构内容，只使用公开 RSS 中的标题、摘要、链接和发布时间。用户自有研报应放入 `inputs/reports/`，系统只读取用户已授权的本地文件。

## 新闻重要性排序逻辑

新闻先进入事件分类器，再进行分桶排序：

- Tier 1：重大宏观、央行决策、财政政策、地缘风险、金融稳定事件
- Tier 2：重要但非系统性事件，例如央行讲话、监管变化、OPEC、AI capex、加密市场结构
- Tier 3：背景材料、研究论文、统计表、普通公告

`credibility_weight` 只代表来源可靠性，不再直接等于新闻重要性。央行 RSS 中的 research paper、working paper、statistics table、accounts 默认降为 Tier 3，除非标题或摘要同时涉及重大市场主题。Top 10 会优先选择 Tier 1 和 Tier 2，Tier 3 默认最多进入 2 条。

## 市场状态 Regime

`src/analyzers/market_narrative.py` 会读取 `MarketSnapshot` 并生成：

- `risk_on`：SPY/QQQ 上涨，VIX 或美元回落，或长债走强
- `risk_off`：SPY/QQQ 下跌，VIX 上涨，长债或黄金走强
- `rates_shock`：TLT 下跌、DXY 上涨、QQQ 下跌
- `dollar_liquidity_tightening`：美元走强并压制风险资产
- `inflation_shock`：原油和黄金上涨、股指下跌
- `crypto_specific`：BTC/ETH 明显上涨但美股平淡
- `mixed`：信号冲突

报告会展示市场状态、关键异动、矛盾信号和风险观察。

## 本地运行

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.main --date today --no-llm
```

常用 CLI：

```bash
python -m src.main --date today
python -m src.main --date 2026-05-22
python -m src.main --no-llm
python -m src.main --only-market
python -m src.main --only-news
python -m src.main --build-index
```

`today` 默认使用 Asia/Taipei 日期，避免 GitHub runner 的 UTC 日期影响晨报归档。

## 自定义 report_profile.yml

编辑 `config/report_profile.yml`：

```yaml
language: zh
top_news_limit: 10
include_background_materials: true
max_tier3_in_top_news: 2
focus_regions:
  - US
  - China
focus_assets:
  - SPY
  - QQQ
  - TLT
  - BTC
```

## GitHub Actions 配置

工作流文件在 `.github/workflows/daily-brief.yml`。GitHub Actions 的 cron 使用 UTC，不支持 `timezone` 字段，所以配置为：

```yaml
cron: "0 22 * * *"
```

这等价于 Asia/Taipei 每天 06:00。也可以在 Actions 页面使用 `workflow_dispatch` 手动运行。

## GitHub Pages 发布

在仓库 `Settings -> Pages` 中选择：

- Source: Deploy from a branch
- Branch: `main`
- Folder: `/public`

启用后，`public/index.html` 会作为静态首页展示 dashboard 和最新晨报入口。

## Secrets 配置

在 GitHub 仓库 `Settings -> Secrets and variables -> Actions` 中按需添加：

- `FRED_API_KEY`
- `COINGECKO_API_KEY`
- `TUSHARE_TOKEN`
- `LLM_PROVIDER`
- `LLM_API_KEY`
- `SEC_USER_AGENT`

本地可复制 `.env.example`，但不要提交 `.env`。

## 添加新的 RSS 源

编辑 `config/rss_feeds.yml`，在对应分类下添加：

```yaml
- name: Example Source
  url: https://example.com/rss
  region: US
  category: global_macro
  language: en
  credibility_weight: 0.8
```

## 添加新的资产

编辑 `config/assets.yml`。Yahoo Finance 支持的资产可直接加入对应组；CoinGecko 使用 coin id；A 股指数需要在 `src/collectors/china_market_collector.py` 的 `INDEX_CODE_MAP` 中维护代码映射。

## 添加自己的研报 PDF/Markdown/HTML

把自有或已授权文件放入 `inputs/reports/`。系统会读取 Markdown、TXT、HTML 和 PDF 的前几页文本，并在“华尔街与机构公开观点”中做短摘录。不会抓取未授权内容。

## 开发与质量检查

```bash
pytest
ruff check .
```

所有网络请求都设置了 timeout、retry 或异常处理；数据源失败会写入 `data/processed/YYYY-MM-DD/warnings.json`，不会中断整个晨报生成。

## Roadmap

- RAG research archive
- event-to-market reaction database
- economic calendar integration
- earnings calendar
- interactive dashboard
- bilingual report
