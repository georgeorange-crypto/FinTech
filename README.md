# Global Macro Morning Brief

一个每天早上自动更新的全球宏观与跨资产市场晨报系统。

项目会采集公开 RSS、主要市场行情、加密资产、港股、A 股指数、FRED、SEC 披露和用户自有研报文件，生成结构化数据、Markdown/HTML 报告、图表，并自动导出 GitHub Pages 可直接打开的 `public/index.html`。

> Not financial advice / 非投资建议。  
> 本项目仅用于个人学习、研究和信息整理，不提供投资建议，不做自动交易，不绕过任何付费墙。

## 最新报告首页

GitHub Pages:

```text
https://georgeorange-crypto.github.io/FinTech/
```

如果 Pages 尚未启用，请按下方“GitHub Pages 设置”开启。启用后，这个链接会打开每日最新晨报首页。

每天运行后，系统会自动生成：

- `index.html`
- `reports/YYYY-MM-DD.md`
- `reports/YYYY-MM-DD.html`
- `charts/YYYY-MM-DD/*.png`
- `data/processed/YYYY-MM-DD/*.json`
- `public/index.html`
- `public/reports/YYYY-MM-DD.html`
- `public/charts/YYYY-MM-DD/*.png`
- `public/metadata.json`

其中 `public/index.html` 会直接内嵌最新一天晨报正文，并展示 dashboard cards、市场状态和今日三大主线。  
根目录 `index.html` 也会同步生成一份，方便仓库首页或其他静态托管方式直接使用。
只要 GitHub Pages 指向 `/public`，打开 Pages 网址看到的就是每日最新晨报。

## GitHub Pages 设置

在 GitHub 仓库中进入：

`Settings -> Pages`

选择：

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/public`

保存后，GitHub Pages 会把 `public/index.html` 作为站点首页。项目每日自动运行后，`public/index.html` 会被更新并提交，Pages 首页也会跟着更新。

Pages 链接：

```text
https://georgeorange-crypto.github.io/FinTech/
```

## 自动运行

工作流文件：

```text
.github/workflows/daily-brief.yml
```

触发方式：

- 每天 Asia/Taipei 06:00 自动运行
- 支持 `workflow_dispatch` 手动运行
- 推送核心代码或配置时自动运行

GitHub Actions 的 cron 使用 UTC，因此配置为：

```yaml
cron: "0 22 * * *"
```

这等价于 Asia/Taipei 每天 06:00。

## 功能概览

- 公开 RSS 新闻采集、去重、关键词过滤
- 新闻事件分类：宏观数据、央行决策、央行讲话、财政政策、监管、地缘风险、财报、商品供给、加密市场结构、金融稳定、研究论文、普通公告等
- 新闻重要性分桶：Tier 1 / Tier 2 / Tier 3
- Top 10 新闻限制低价值背景材料数量，避免普通研究论文挤占头条
- 为每条重要新闻生成自然语言“为什么重要”
- 为新闻生成逐资产影响解释：资产、资产类别、方向、强度、原因
- 采集 Yahoo Finance、CoinGecko、AKShare、FRED、SEC 数据
- 计算 1D、5D、1M、YTD、20D 波动率、MA20、MA60、RSI14 和趋势标签
- 识别跨资产市场状态：`risk_on`、`risk_off`、`rates_shock`、`inflation_shock`、`dollar_liquidity_tightening`、`crypto_specific`、`mixed`、`unknown`
- 生成 PNG 图表和资产组 summary chart
- 生成结构化事件数据库和历史 JSONL
- 导出 GitHub Pages 可用静态站点

## 目录结构

```text
config/                  配置文件
src/                     核心代码
  collectors/            数据采集
  analyzers/             新闻、资产影响、市场状态分析
  charts/                图表生成
  reports/               Markdown/HTML/Public 首页生成
  models/                Pydantic 数据结构
  utils/                 工具函数
reports/                 每日 Markdown 和 HTML 报告
charts/                  每日图表
data/processed/          每日结构化数据
data/history/            事件和行情历史 JSONL
public/                  GitHub Pages 静态站点输出
tests/                   pytest 测试
```

## 配置文件

核心配置都在 `config/`：

- `assets.yml`：资产分组
- `rss_feeds.yml`：公开 RSS 源
- `macro_series.yml`：FRED 宏观序列
- `watchlist_cik.yml`：SEC watchlist
- `importance_rules.yml`：事件分类、tier、routine 规则
- `asset_impact_rules.yml`：资产影响方向、强度和原因
- `report_profile.yml`：晨报偏好

示例 `report_profile.yml`：

```yaml
language: zh
top_news_limit: 10
include_background_materials: true
max_tier3_in_top_news: 2
focus_regions:
  - US
  - China
  - Hong Kong
  - EU
  - Japan
focus_assets:
  - SPY
  - QQQ
  - TLT
  - DXY
  - GC=F
  - CL=F
  - BTC
  - ETH
  - ^HSI
  - 沪深300
```

## 本地运行

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.main --date today --no-llm
```

常用命令：

```bash
python -m src.main --date today
python -m src.main --date 2026-05-22
python -m src.main --no-llm
python -m src.main --only-market
python -m src.main --only-news
python -m src.main --build-index
```

`today` 默认使用 Asia/Taipei 日期，避免 GitHub runner 的 UTC 日期导致晨报日期偏差。

## Secrets

在 `Settings -> Secrets and variables -> Actions` 中按需配置：

- `FRED_API_KEY`
- `COINGECKO_API_KEY`
- `TUSHARE_TOKEN`
- `LLM_PROVIDER`
- `LLM_API_KEY`
- `SEC_USER_AGENT`

没有这些 key 时，相关模块会跳过或降级，不会中断主流程。

## 数据合规

- 不绕过 WSJ、Bloomberg、FT、Reuters 等付费墙
- 对付费媒体只使用公开 RSS 标题、摘要、链接和发布时间
- 不复制长篇原文
- 用户自有研报可放入 `inputs/reports/`
- 所有输出必须标注 `Not financial advice / 非投资建议`
- 本项目不做自动交易

## 开发检查

```bash
pytest
ruff check .
python -m src.main --date today --no-llm
python -m src.main --build-index
```

外部数据源失败会写入：

```text
data/processed/YYYY-MM-DD/warnings.json
```

不会导致整个晨报失败。

## Roadmap

- RAG research archive
- event-to-market reaction database
- economic calendar integration
- earnings calendar
- interactive dashboard
- bilingual report
