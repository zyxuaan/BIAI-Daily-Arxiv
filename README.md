# ArXiv Summary Daily

一个自动获取和总结 arXiv 论文的工具。每天自动检索最新的论文，并使用 Gemini 生成摘要。

## 功能特点

- 支持多个 arXiv 分类的论文检索
- 自动过滤重复论文
- 使用 Gemini AI 生成论文摘要
- 支持增量更新，避免重复处理
- 可配置的搜索参数和关键词
- 输出示例

<img src="img/overview.png" alt="overview" style="zoom: 33%;" />

## 安装

```bash
git clone https://github.com/dong-zehao/ArxivSummaryDaily.git
cd ArxivSummaryDaily
pip install -r requirements.txt
```

## 配置

在 `config/settings.py` 中配置：

- 搜索分类 (CATEGORIES)
- 搜索关键词 (QUERY)
- Gemini API 密钥 (GEMINI_API_KEY)
- 其他搜索参数 (SEARCH_CONFIG)

## 使用方法

运行主程序：
```bash
python main.py
```

可选参数：
- `--model`: 指定使用的 Gemini 模型

## 输出

- 论文元数据保存在 `data/metadata.json`
- 论文总结保存在 `data/summary.md`





