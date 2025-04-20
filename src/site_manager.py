#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import time
import shutil
import argparse
from datetime import datetime
import re
from pathlib import Path

def clean_old_files(data_dir, days=30):
    """清理超过指定天数的markdown文件"""
    print(f"清理超过{days}天的旧markdown文件...")
    
    current_time = time.time()
    seconds_in_day = 86400  # 24 * 60 * 60
    max_age = days * seconds_in_day
    
    # 查找所有摘要文件
    summary_pattern = os.path.join(data_dir, "summary_*.md")
    files = glob.glob(summary_pattern)
    
    removed_count = 0
    for file_path in files:
        # 获取文件的修改时间
        file_time = os.path.getmtime(file_path)
        age = current_time - file_time
        
        # 如果文件超过指定天数，删除它
        if age > max_age:
            file_date = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S')
            print(f"删除旧文件: {file_path} ({file_date})")
            os.remove(file_path)
            removed_count += 1
    
    print(f"清理完成，共删除{removed_count}个文件")
    return removed_count

def get_sorted_summary_files(data_dir):
    """获取按时间排序的摘要文件列表（最新在前）"""
    summary_pattern = os.path.join(data_dir, "summary_*.md")
    files = glob.glob(summary_pattern)
    
    # 按照修改时间排序文件（最新的在前）
    if files:
        files.sort(key=os.path.getmtime, reverse=True)
    
    return files

def copy_latest_to_index(data_dir, sorted_files=None):
    """复制最新的md文件到index.md"""
    if sorted_files is None:
        sorted_files = get_sorted_summary_files(data_dir)
    
    if sorted_files:
        latest_file = sorted_files[0]
        
        index_path = os.path.join(data_dir, "index.md")
        print(f"找到最新文件: {latest_file}")
        print(f"更新index.md...")
        
        # 复制最新文件到index.md
        shutil.copy2(latest_file, index_path)
        print("index.md更新成功")
    else:
        # 如果没有找到文件，创建一个简单的index.md
        index_path = os.path.join(data_dir, "index.md")
        print("未找到摘要文件，创建空的index.md")
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# ArXiv Summary Daily\n\n")
            f.write("No summaries available yet.\n")
    
    return True

def create_archive_page(data_dir, sorted_files=None):
    """创建归档页面，允许访问所有摘要"""
    if sorted_files is None:
        sorted_files = get_sorted_summary_files(data_dir)
    
    archive_path = os.path.join(data_dir, "archive.md")
    print(f"创建归档页面: {archive_path}")
    
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write("---\n")
        f.write("layout: default\n")
        f.write("title: ArXiv Summary 归档\n")
        f.write("---\n\n")
        f.write("# ArXiv 摘要归档\n\n")
        f.write("以下是所有可用的ArXiv摘要文件，按日期排序（最新在前）：\n\n")
        
        # 使用纯Markdown列表格式，去除HTML标记
        for file_path in sorted_files:
            filename = os.path.basename(file_path)
            # 从文件名中提取日期部分 (格式: summary_YYYYMMDD_HHMMSS.md)
            match = re.search(r'summary_(\d{4})(\d{2})(\d{2})_', filename)
            if match:
                year, month, day = match.groups()
                formatted_date = f"{year}-{month}-{day}"
                f.write(f'- [{formatted_date} 摘要]({filename})\n')
    
    print("归档页面创建成功")
    return True

def setup_site_structure(data_dir, github_dir):
    """设置Jekyll部署环境，直接部署index.md，不使用导航栏"""
    # 1. 复制配置文件
    config_src = os.path.join(github_dir, "_config.yml")
    config_dest = os.path.join(data_dir, "_config.yml")
    shutil.copy2(config_src, config_dest)
    
    # 2. 创建简单的Gemfile以支持GitHub Pages
    gemfile_path = os.path.join(data_dir, "Gemfile")
    with open(gemfile_path, 'w', encoding='utf-8') as f:
        f.write('source "https://rubygems.org"\n')
        f.write('gem "github-pages", group: :jekyll_plugins\n')
        f.write('gem "jekyll-theme-cayman"\n')
    
    # 3. 确保index.md有正确的前置元数据
    index_path = os.path.join(data_dir, "index.md")
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 如果没有front matter，添加一个
        if not content.startswith('---'):
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write('---\n')
                f.write('layout: default\n')
                f.write('title: ArXiv Summary Daily\n')
                f.write('---\n\n')
                f.write(content)
    
    # 4. 清理不再需要的文件和目录
    includes_dir = os.path.join(data_dir, "_includes")
    layouts_dir = os.path.join(data_dir, "_layouts")
    
    # 删除导航文件和自定义布局
    nav_html = os.path.join(includes_dir, "navigation.html")
    nav_md = os.path.join(includes_dir, "navigation.md")
    default_html = os.path.join(layouts_dir, "default.html")
    default_md = os.path.join(layouts_dir, "default.md")
    
    for file_path in [nav_html, nav_md, default_html, default_md]:
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # 保留mathjax.html（如果需要）
    mathjax_src = os.path.join(github_dir, "_includes", "mathjax.html")
    if os.path.exists(mathjax_src):
        os.makedirs(includes_dir, exist_ok=True)
        mathjax_dest = os.path.join(includes_dir, "mathjax.html")
        shutil.copy2(mathjax_src, mathjax_dest)
    
    # 删除可能存在的.nojekyll文件，因为我们希望使用Jekyll
    nojekyll_path = os.path.join(data_dir, ".nojekyll")
    if os.path.exists(nojekyll_path):
        os.remove(nojekyll_path)
    
    print("Jekyll部署配置完成 - 直接部署index.md文件")
    return True

def main():
    parser = argparse.ArgumentParser(description="ArXiv Summary网站管理工具")
    parser.add_argument('--data-dir', default='./data', help='数据目录路径 (默认: ./data)')
    parser.add_argument('--github-dir', default='./.github', help='GitHub配置目录路径 (默认: ./.github)')
    parser.add_argument('--days', type=int, default=30, help='保留摘要文件的天数 (默认: 30)')
    parser.add_argument('--skip-clean', action='store_true', help='跳过清理旧文件')
    args = parser.parse_args()
    
    # 确保数据目录存在
    os.makedirs(args.data_dir, exist_ok=True)
    
    # 清理旧文件
    if not args.skip_clean:
        clean_old_files(args.data_dir, args.days)
    
    # 获取排序后的文件列表（只需获取一次）
    sorted_files = get_sorted_summary_files(args.data_dir)
    
    # 执行各项任务
    copy_latest_to_index(args.data_dir, sorted_files)
    create_archive_page(args.data_dir, sorted_files)
    setup_site_structure(args.data_dir, args.github_dir)
    
    print("所有任务完成！")

if __name__ == "__main__":
    main()