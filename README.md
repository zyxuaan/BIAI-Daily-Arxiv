# ArXiv Summary Daily

一个自动获取和总结 arXiv 论文的工具。每天自动检索最新的论文，并使用 AI 生成摘要。

## 功能特点

- 支持多个 arXiv 分类的论文检索
- 自动过滤重复论文
- 使用 AI 生成论文摘要
- 支持增量更新，避免重复处理
- 可配置的搜索参数和关键词
- 输出示例

<img src="img/overview.png" alt="overview" style="zoom: 33%;" />

## 安装

1. 克隆仓库并进入项目目录：
```bash
git clone https://github.com/dong-zehao/ArxivSummaryDaily.git
cd ArxivSummaryDaily
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 安装命令行工具：
```bash
pip install -e .
```

安装完成后，`arxivsummary` 命令将被添加到系统路径中，可以在任何目录下直接使用。

## 配置

首先将 `config/settings.example.py` 改名为 `config/settings.py`

在 `config/settings.py` 中配置：

- 搜索分类 (CATEGORIES)
- 搜索关键词 (QUERY)
- AI 模型的 API 密钥 (LLM_CONFIG中的api_key参数)
- 其他搜索参数 (SEARCH_CONFIG)
- 输出配置 (OUTPUT_DIR): 设置存放AI summary的文件路径

## 使用方法

运行主程序：
```bash
arxivsummary
```

可选参数：
- `--query`: 设置搜索关键词，默认使用配置文件中的 QUERY
- `--categories`: 设置要搜索的 arXiv 分类，可指定多个，默认使用配置文件中的 CATEGORIES
- `--max-results`: 设置要获取的最大论文数量，默认使用配置文件中的设置
- `--output-dir`: 设置输出目录，默认使用配置文件中的 OUTPUT_DIR

使用示例：
- 搜索关键词`nickelate`，只搜索最新的10篇文献
    ```bash
    arxivsummary --query "nickelate" --max-results 10
    ```
- 搜索关键词`cuprate`，在凝聚态-超导或者凝聚态-强关联领域搜索，输出在指定的文件夹中
    ```bash
    arxivsummary --query "cuprate" --categories cond-mat.supr-con cond-mat.str-el --output-dir "G:\ArxivSummary\cuprate"
    ```

## 输出

- 论文总结保存在 `OUTPUT_DIR/summary_yyyyMMdd_hhmmss.md`





