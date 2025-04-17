"""
ArXiv API 客户端模块
"""
import arxiv
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from config.settings import SEARCH_CONFIG, QUERY

class ArxivClient:
    def __init__(self):
        self.client = arxiv.Client()

    def _remove_duplicates(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除重复的论文（基于论文ID）"""
        seen_ids = set()
        unique_papers = []
        
        for paper in papers:
            if paper['entry_id'] not in seen_ids:
                seen_ids.add(paper['entry_id'])
                unique_papers.append(paper)
                
        return unique_papers

    def _safe_get_categories(self, paper: arxiv.Result) -> List[str]:
        """安全地获取论文分类"""
        try:
            # print(f"调试 - 分类信息: {paper.categories}, 类型: {type(paper.categories)}")
            if isinstance(paper.categories, (list, tuple, set)):
                return list(paper.categories)
            elif isinstance(paper.categories, str):
                return [paper.categories]
            else:
                return [str(paper.categories)]
        except Exception as e:
            print(f"调试 - 获取分类出错: {e}")
            return [paper.primary_category] if paper.primary_category else []

    def _load_last_run_info(self, last_run_file: str) -> Optional[str]:
        """加载上次运行的最新文章ID"""
        try:
            with open(last_run_file, 'r') as f:
                data = json.load(f)
                return data.get('latest_entry_id')
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _save_last_run_info(self, latest_entry_id: str, last_run_file: str):
        """保存本次运行的最新文章ID"""
        with open(last_run_file, 'w') as f:
            json.dump({'latest_entry_id': latest_entry_id, 'timestamp': datetime.now().isoformat()}, f)

    def _create_search_query(self, query: str = "", 
                           categories: Optional[List[str]] = None,
                           keywords: Optional[Dict[str, List[str]]] = None) -> str:
        """构建高级搜索查询"""
        search_parts = []
        
        # 添加基本查询
        if query:
            if SEARCH_CONFIG['title_only']:
                search_parts.append(f"ti:{query}")
            elif SEARCH_CONFIG['abstract_only']:
                search_parts.append(f"abs:{query}")
            elif SEARCH_CONFIG['author_only']:
                search_parts.append(f"au:{query}")
            else:
                search_parts.append(query)

        # 添加分类（使用 OR 连接所有分类）
        if categories:
            try:
                cat_parts = []
                for cat in categories:
                    if not cat:
                        continue
                    if SEARCH_CONFIG['include_cross_listed']:
                        cat_parts.append(f"cat:{cat}")
                    else:
                        cat_parts.append(f"primary_cat:{cat}")
                
                if cat_parts:
                    cat_query = " OR ".join(cat_parts)
                    search_parts.append(f"({cat_query})")
            except Exception as e:
                print(f"调试 - 构建分类查询出错: {e}")

        final_query = " AND ".join(search_parts) if search_parts else "*:*"
        # print(f"调试 - 最终查询: {final_query}")
        return final_query

    def search_papers(self, 
                     categories: Optional[List[str]] = None,
                     query: str = QUERY,
                     last_run_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索论文并返回元数据，支持多个分类的查询和去重
        
        Args:
            categories: arXiv分类列表
            query: 搜索关键词
            last_run_file: 存储上次运行信息的文件路径（可选）
        """
        # 加载上次运行的最新文章ID
        last_entry_id = None
        if last_run_file and os.path.exists(last_run_file):
            try:
                with open(last_run_file, 'r') as f:
                    data = json.load(f)
                    last_entry_id = data.get('latest_entry_id')
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        all_results = []
        
        # 构建查询
        search_query = self._create_search_query(query, categories)
        print(f"使用查询: {search_query}")
        
        # 设置排序标准
        sort_criterion = getattr(arxiv.SortCriterion, SEARCH_CONFIG['sort_by'])
        sort_order = getattr(arxiv.SortOrder, SEARCH_CONFIG['sort_order'])
        
        try:
            # 创建搜索参数字典
            search_kwargs = {
                'query': search_query,
                'max_results': SEARCH_CONFIG['max_total_results'],
                'sort_by': sort_criterion,
                'sort_order': sort_order
            }
            
            # 只在 id_list 不为 None 时添加到参数中
            if SEARCH_CONFIG['id_list'] is not None:
                search_kwargs['id_list'] = SEARCH_CONFIG['id_list']
            
            search = arxiv.Search(**search_kwargs)

            # print("调试 - 开始获取结果")
            for paper in self.client.results(search):
                try:
                    # 如果遇到上次处理过的文章，就停止查询
                    if last_entry_id and paper.entry_id == last_entry_id:
                        break

                    metadata = {
                        'title': paper.title,
                        'authors': [author.name for author in paper.authors],
                        'published': paper.published.isoformat(),
                        'updated': paper.updated.isoformat(),
                        'summary': paper.summary,
                        'doi': paper.doi,
                        'primary_category': paper.primary_category,
                        'categories': self._safe_get_categories(paper),
                        'links': [link.href for link in paper.links],
                        'pdf_url': paper.pdf_url,
                        'entry_id': paper.entry_id,
                        'comment': getattr(paper, 'comment', '')
                    }
                    all_results.append(metadata)
                    # print(f"调试 - 成功处理文章: {metadata['title'][:30]}...")
                    
                except Exception as e:
                    print(f"调试 - 处理单篇文章时出错: {e}")
                    continue
                
        except Exception as e:
            print(f"调试 - 搜索过程出错: {e}")
            print(f"错误类型: {type(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")

        # 去除重复的论文并排序
        unique_results = self._remove_duplicates(all_results)
        unique_results.sort(key=lambda x: x['published'], reverse=True)
        
        # 保存本次运行的最新文章ID
        if unique_results and last_run_file:
            self._save_last_run_info(unique_results[0]['entry_id'], last_run_file)

        return unique_results

    def search_recent(self, query: str, days: int = 7, **kwargs) -> List[Dict[str, Any]]:
        """
        搜索最近几天发布的论文
        
        Args:
            query: 搜索关键词
            days: 最近的天数（默认7天）
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return self.search_papers(query, start_date=start_date, end_date=end_date, **kwargs)

    def save_results(self, results: List[Dict[str, Any]], output_dir: str, filename: str):
        """
        保存搜索结果到JSON文件
        """
        os.makedirs(output_dir, exist_ok=True)
        output_path = Path(output_dir) / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    def load_results(self, output_dir: str, filename: str) -> List[Dict[str, Any]]:
        """
        从JSON文件加载之前保存的结果
        """
        output_path = Path(output_dir) / filename
        if not output_path.exists():
            return []
            
        with open(output_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def filter_results(self, results: List[Dict[str, Any]], 
                      categories: Optional[List[str]] = None,
                      keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        过滤搜索结果
        
        Args:
            results: 搜索结果列表
            categories: 要过滤的分类列表
            keywords: 标题或摘要中必须包含的关键词列表
        """
        filtered = results
        
        if categories:
            filtered = [
                paper for paper in filtered
                if any(cat in paper['categories'] for cat in categories)
            ]
            
        if keywords:
            filtered = [
                paper for paper in filtered
                if any(
                    keyword.lower() in paper['title'].lower() 
                    or keyword.lower() in paper['summary'].lower()
                    for keyword in keywords
                )
            ]
            
        return filtered