# global-macro-morning-brief

每天早上自动生成的全球经济与跨资产市场晨报系统。项目会采集公开 RSS、主要资产行情、加密资产、A 股指数、FRED 宏观指标、SEC 披露和用户自有研报文件，生成 Markdown、HTML、图表和静态首页。

> Not financial advice / 非投资建议。本项目仅供个人学习、研究与信息整理，不做自动交易，不构成投资建议。

## 功能列表

- 公开 RSS 新闻采集、去重、关键词过滤和相关性排序
- 美股 ETF、港股、美元、美债、VIX、商品行情采集
- CoinGecko 加密资产行情采集，支持无 API key 模式
- AKShare A 股指数采集，失败时不影响主流程
- FRED 宏观指标采集，需要 `FRED_API_KEY`
- SEC watchlist 披露追踪，需要合规 `SEC_USER_AGENT`
- 计算 1D、5D、1M、YTD、20D 波动率、MA20、MA60、RSI14 和趋势标签
- 生成 PNG 价格图和资产组收益概览图
- 生成 `reports/YYYY-MM-DD.md`、`reports/YYYY-MM-DD.html`、`public/index.html`
- GitHub Actions 每天 Asia/Taipei 06:00 自动运行，并支持手动触发

## 数据源说明

配置位于 `config/`：

- `config/rss_feeds.yml`：公开 RSS 源
- `config/assets.yml`：资产分组
- `config/macro_series.yml`：FRED 宏观序列
- `config/watchlist_cik.yml`：SEC 公司 watchlist

项目不会绕过 WSJ、Bloomberg、FT、Reuters 等付费墙。对付费媒体或机构内容，只使用公开 RSS 中的标题、摘要、链接和发布时间。

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

## GitHub Actions 配置

工作流文件在 `.github/workflows/daily-brief.yml`。GitHub Actions 的 cron 使用 UTC，不支持 `timezone` 字段，所以配置为：

```yaml
cron: "0 22 * * *"
```

这等价于 Asia/Taipei 每天 06:00。也可以在 Actions 页面使用 `workflow_dispatch` 手动运行。

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

## 示例报告截图

生成报告后，可打开 `public/index.html` 查看最近 30 天晨报入口。截图可放在 `docs/screenshots/`，并在 README 中替换为真实图片。

## 开发与质量检查

```bash
pytest
ruff check .
```

所有网络请求都设置了 timeout、retry 或异常处理；数据源失败会写入 `data/processed/YYYY-MM-DD/warnings.json`，不会中断整个晨报生成。

## Roadmap

- 增加经济日历数据源
- 增加更多央行讲话与政策日历解析
- 增加图表主题和交互式 HTML 图表
- 增加本地向量检索，用于用户自有研报归档
- 增加多语言报告输出
- 增加 GitHub Pages 发布示例
