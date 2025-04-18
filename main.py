"""
ArXiv 文献元数据获取工具
"""
import os
import argparse
from pathlib import Path
from src.arxiv_client import ArxivClient
from src.paper_summarizer import create_summarizer
from datetime import datetime
from config.settings import (
    OUTPUT_DIR, METADATA_FILE, 
    LAST_RUN_FILE, LLM_API_KEY, LLM_CONFIG,
    CATEGORIES, QUERY
)

def parse_args():
    parser = argparse.ArgumentParser(description='ArXiv论文搜索和总结工具')
    parser.add_argument(
        '--model',
        default=LLM_CONFIG['model'],
        help='使用的LLM模型名称'
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 初始化目录
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"正在查询以下领域的论文:")
    for category in CATEGORIES:
        print(f"- {category}")
    
    client = ArxivClient()
    
    # 搜索论文（增量更新）
    last_run_path = output_dir / LAST_RUN_FILE
    results = client.search_papers(
        categories=CATEGORIES,
        query=QUERY,
        last_run_file=str(last_run_path)
    )
    
    if not results:
        print("没有发现新论文。")
        return
        
    print(f"找到 {len(results)} 篇新论文（已去除重复）")
    
    # 保存元数据
    metadata_path = output_dir / METADATA_FILE
    client.save_results(results, str(output_dir), METADATA_FILE)
    print(f"元数据已保存到: {metadata_path}")
    
    # 生成论文总结
    print(f"正在使用模型 {args.model} 生成论文总结...")
    summarizer = create_summarizer(LLM_API_KEY, args.model)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"summary_{timestamp}.md"
    summarizer.summarize_papers(results, str(output_path))
    print(f"论文总结已保存到: {output_path}")

if __name__ == '__main__':
    main()