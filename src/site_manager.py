#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import shutil
import argparse
from datetime import datetime
import re
from pathlib import Path

class SiteManager:
    """ArXiv摘要网站管理器，处理文件清理、索引和归档页面生成"""
    
    DEFAULT_FRONT_MATTER = """---
layout: default
title: {title}
---

"""
    
    def __init__(self, data_dir, github_dir=None):
        self.data_dir = Path(data_dir)
        self.github_dir = Path(github_dir) if github_dir else None
        self.data_dir.mkdir(exist_ok=True)
    
    def clean_old_files(self, days=30):
        """清理超过指定天数的markdown文件"""
        print(f"开始清理超过 {days} 天的旧摘要文件...")
        current_time = time.time()
        cutoff_time = current_time - (days * 86400)
        
        removed_count = 0
        for file_path in self.data_dir.glob("summary_*.md"):
            if file_path.stat().st_mtime < cutoff_time:
                print(f"删除旧文件: {file_path.name}")
                file_path.unlink()
                removed_count += 1
        
        print(f"清理完成，共删除 {removed_count} 个文件。")
        return removed_count
    
    def get_sorted_summary_files(self):
        """获取按时间排序的摘要文件列表（最新在前）"""
        return sorted(self.data_dir.glob("summary_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    def extract_content_and_title(self, file_path):
        """从文件中提取内容，移除Jekyll前置元数据"""
        content = file_path.read_text(encoding='utf-8')
        
        # 移除前置元数据
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].strip()
        
        # 从第一个H1标题提取标题
        title_match = re.search(r'^#\s*(.*?)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Arxiv论文总结报告(Brain-inspired AI)"
        
        return title, content
    
    def copy_latest_to_index(self, sorted_files):
        """将最新的摘要文件内容复制到index.md"""
        index_path = self.data_dir / "index.md"
        today = datetime.now().strftime('%Y-%m-%d')
        
        if not sorted_files:
            print("未找到任何摘要文件，创建空的index.md。")
            title = "Arxiv论文总结报告(Brain-inspired AI)"
            content = "[查看所有摘要归档](archive.md)\n\n# Arxiv论文总结报告(Brain-inspired AI)\n\n暂无可用摘要。"
        else:
            latest_file = sorted_files[0]
            print(f"找到最新文件: {latest_file.name}，正在更新index.md...")
            title, content = self.extract_content_and_title(latest_file)
            content = f"[查看所有摘要归档](archive.md) | 更新日期: {today}\n\n{content}"

        full_content = self.DEFAULT_FRONT_MATTER.format(title=title) + content
        index_path.write_text(full_content, encoding='utf-8')
        print("index.md 更新成功。")

    def create_archive_page(self, sorted_files):
        """创建归档页面，链接到所有历史摘要"""
        archive_path = self.data_dir / "archive.md"
        print(f"正在创建或更新归档页面: {archive_path.name}...")
        
        archive_title = "Arxiv论文摘要归档(Brain-inspired AI)"
        header = f"[返回首页](index.md)\n\n# {archive_title}\n\n以下是所有可用的历史摘要，按日期排序（最新在前）：\n\n"
        
        links = []
        for file_path in sorted_files:
            filename = file_path.name
            match = re.search(r'summary_(\d{4})(\d{2})(\d{2})_', filename)
            if match:
                date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                # 确保每个历史文件都有Jekyll前置元数据
                self.ensure_file_has_front_matter(file_path, f"{date_str} Arxiv论文摘要")
                links.append(f'- [{date_str} 摘要]({filename})')
        
        content = self.DEFAULT_FRONT_MATTER.format(title=archive_title) + header + "\n".join(links)
        archive_path.write_text(content, encoding='utf-8')
        print("归档页面创建成功。")

    def ensure_file_has_front_matter(self, file_path, title):
        """确保文件有Jekyll前置元数据，如果缺少则添加"""
        content = file_path.read_text(encoding='utf-8')
        if not content.startswith('---'):
            new_content = self.DEFAULT_FRONT_MATTER.format(title=title) + content
            file_path.write_text(new_content, encoding='utf-8')

    def setup_site_structure(self):
        """设置Jekyll部署所需的基本文件结构"""
        if not self.github_dir:
            print("未提供GitHub配置目录，跳过网站结构设置。")
            return
        
        print("正在同步网站配置文件...")
        files_to_copy = ["_config.yml", "_layouts/default.html", "_includes/mathjax.html", "img/paper.png"]
        for file_rel_path in files_to_copy:
            src = self.github_dir / file_rel_path
            dest = self.data_dir / file_rel_path
            if src.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            else:
                print(f"警告: 未找到源文件 {src}")

        # 创建Gemfile
        gemfile_path = self.data_dir / "Gemfile"
        gemfile_content = 'source "https://rubygems.org"\ngem "github-pages", group: :jekyll_plugins\n'
        gemfile_path.write_text(gemfile_content, encoding='utf-8')
        
        print("Jekyll部署配置完成。")

def main():
    parser = argparse.ArgumentParser(description="ArXiv Summary网站管理工具")
    parser.add_argument('--data-dir', default='./data', help='数据目录路径')
    parser.add_argument('--github-dir', default='./.github', help='GitHub配置目录路径')
    parser.add_argument('--days', type=int, default=30, help='摘要文件保留天数')
    parser.add_argument('--skip-clean', action='store_true', help='跳过清理旧文件')
    args = parser.parse_args()
    
    site = SiteManager(args.data_dir, args.github_dir)
    
    if not args.skip_clean:
        site.clean_old_files(args.days)
    
    sorted_files = site.get_sorted_summary_files()
    
    site.copy_latest_to_index(sorted_files)
    site.create_archive_page(sorted_files)
    site.setup_site_structure()
    
    print("\n所有任务完成！")

if __name__ == "__main__":
    main()