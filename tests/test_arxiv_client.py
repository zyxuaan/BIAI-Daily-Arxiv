"""
ArxivClient 测试模块
"""
import unittest
from pathlib import Path
import json
from src.arxiv_client import ArxivClient
from config.settings import CATEGORIES, QUERY, SEARCH_CONFIG

class TestArxivClient(unittest.TestCase):
    def setUp(self):
        self.client = ArxivClient()
        self.test_output_dir = "test_output"
        self.test_filename = "test_metadata.json"

    def test_search_papers_with_settings(self):
        # 使用settings.py中的配置进行搜索
        results = self.client.search_papers(
            categories=CATEGORIES,
            query=QUERY
        )
        
        # 基本验证
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), SEARCH_CONFIG['max_total_results'])
        
        print("\n检索到的论文标题:")
        for i, paper in enumerate(results, 1):
            print(f"{i}. {paper['title']}")
        
        # 验证返回的数据结构
        if results:
            paper = results[0]
            required_fields = ['title', 'authors', 'published', 'summary', 'categories']
            for field in required_fields:
                self.assertIn(field, paper)
            
            # 验证论文分类是否符合配置要求
            self.assertTrue(
                any(cat in paper['categories'] for cat in CATEGORIES),
                f"论文 {paper['title']} 的分类 {paper['categories']} 不在指定分类 {CATEGORIES} 中"
            )
            
    def test_save_results(self):
        results = [{"title": "Test Paper", "authors": ["Test Author"]}]
        
        # 保存测试数据
        self.client.save_results(results, self.test_output_dir, self.test_filename)
        
        # 验证文件是否创建并包含正确的数据
        output_path = Path(self.test_output_dir) / self.test_filename
        self.assertTrue(output_path.exists())
        
        with open(output_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, results)
        
        # 清理测试文件
        output_path.unlink()
        Path(self.test_output_dir).rmdir()

if __name__ == '__main__':
    unittest.main()