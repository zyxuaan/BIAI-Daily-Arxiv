"""
ArXiv API 配置文件
"""

# arXiv API 搜索配置
SEARCH_CONFIG = {
    'max_total_results': 512,         # 总共要获取的最大论文数量
    'sort_by': 'SubmittedDate',       # 排序方式: Relevance, LastUpdatedDate, SubmittedDate
    'sort_order': 'Descending',       # 排序顺序: Ascending, Descending
    'include_cross_listed': True,     # 是否包含跨类别的论文
    'abstracts': True,                # 是否包含摘要
    'id_list': None,                  # 按ID搜索特定论文
    'title_only': False,              # 是否仅在标题中搜索
    'author_only': False,             # 是否仅搜索作者
    'abstract_only': False,           # 是否仅搜索摘要
    'search_mode': 'all'             # 搜索模式：'all'(任意关键词匹配), 'any'(所有关键词都要匹配)
}

# 固定搜索查询 - 领域
# 针对脑启发AI (Brain Inspired AI) 领域优化的分类
CATEGORIES = [
    "cs.NE",
    "cs.AI",
    "cs.LG",
    "cs.CV",
    "cs.CL",
    "q-bio.NC"
]

# 搜索查询配置，用OR或用AND连接关键词，或者没有关键词也可以留空
# 最终确定的关键词组合
QUERY = "Biologically OR Spiking OR SNN OR Neuromorphic OR Event"

# 语言模型API配置
LLM_CONFIG = {
    'api_key': "YOUR_API_HERE",                                             # 在这里输入API密钥
    'model': 'gemini-2.5-flash',                                            # 模型名称
    # 'model': 'gemini-1.0-pro',
    'api_url': "https://generativelanguage.googleapis.com/v1beta/models",   # API基础URL
    'temperature': 0.5,                                                     # 温度参数
    'max_output_tokens': 8192,                                              # 最大输出长度
    'top_p': 0.8,                                                           # Top P 参数
    'top_k': 40,                                                            # Top K 参数
    'retry_count': 3,                                                       # API调用失败时的重试次数
    'retry_delay': 2,                                                       # 重试间隔（秒）
    'timeout': 300,                                                         # API请求超时时间（秒）
}

# 输出配置
OUTPUT_DIR = "data"
LAST_RUN_FILE = "last_run.json"  # 存储上次运行的信息
