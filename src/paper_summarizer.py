"""
论文总结模块 - 使用大语言模型API生成论文摘要
"""
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests
import time
from datetime import datetime
from config.settings import LLM_CONFIG

class ModelClient:
    """语言模型API客户端"""
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or LLM_CONFIG['model']
        self.api_url = f"{LLM_CONFIG['api_url']}/{self.model}:generateContent"
        self.timeout = LLM_CONFIG.get('timeout', 30)
        
    def _create_headers(self) -> Dict[str, str]:
        """创建请求头"""
        return {
            "Content-Type": "application/json"
        }
    
    def _create_request_body(
        self, 
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建请求体"""
        # 将最后一条消息作为提示词
        prompt = messages[-1]["content"]
        
        return {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": temperature or LLM_CONFIG['temperature'],
                "maxOutputTokens": max_tokens or LLM_CONFIG['max_output_tokens'],
                "topP": LLM_CONFIG['top_p'],
                "topK": LLM_CONFIG['top_k']
            }
        }
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建聊天完成"""
        headers = self._create_headers()
        data = self._create_request_body(messages, temperature, max_tokens)
        
        for attempt in range(LLM_CONFIG['retry_count']):
            try:
                response = requests.post(
                    f"{self.api_url}?key={self.api_key}",
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    raise Exception(f"API 调用失败: {response.text}")
                    
                result = response.json()
                
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": result["candidates"][0]["content"]["parts"][0]["text"]
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                }
            except requests.Timeout:
                print(f"请求超时（{self.timeout}秒），正在重试...")
                if attempt == LLM_CONFIG['retry_count'] - 1:
                    raise TimeoutError(f"API调用在{self.timeout}秒内未响应，已重试{LLM_CONFIG['retry_count']}次")
                time.sleep(LLM_CONFIG['retry_delay'] * (2 ** attempt))
            except Exception as e:
                if attempt == LLM_CONFIG['retry_count'] - 1:
                    raise
                time.sleep(LLM_CONFIG['retry_delay'] * (2 ** attempt))

class PaperSummarizer:
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.client = ModelClient(api_key, model)
        self.max_papers_per_batch = 25

    def _generate_batch_summaries(self, papers: List[Dict[str, Any]], start_index: int) -> str:
        """为一批论文生成总结"""
        batch_prompt = ""
        for i, paper in enumerate(papers, start=start_index):
            batch_prompt += f"""
论文 {i}：
标题：{paper['title']}
作者：{', '.join(paper['authors'])}
发布日期：{paper['published'][:10]}
arXiv链接：{paper['pdf_url']}
论文摘要：{paper['summary']}

"""
        
        final_prompt = f"""请为以下{len(papers)}篇论文分别生成markdown语言格式的总结。对每篇论文：
1. 用一句话说明研究目的
2. 用一句话说明主要发现
请用中文回答，保持原有格式，对每篇论文的回答后加入markdown格式的"---"分隔符。
确保对每篇论文的编号、标题等信息保持不变。
输出格式为：

#### [标题](文章链接)
- 作者: (作者)
- 研究目的: (研究目的)
- 主要发现: (主要发现)

---

[标题](文章链接)
- 作者: (作者)
- 研究目的: (研究目的)
- 主要发现: (主要发现)

---

......

---

[标题](文章链接)
- 作者: (作者)
- 研究目的: (研究目的)
- 主要发现: (主要发现)

---


请注意，以上是对每篇论文的总结格式示例。请确保输出格式与示例一致。
请根据以下论文信息生成总结：
{batch_prompt}"""

        try:
            response = self.client.chat_completion([{
                "role": "user",
                "content": final_prompt
            }])
            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            # 如果批处理失败，生成错误信息
            error_summaries = []
            for i, paper in enumerate(papers, start=start_index):
                error_summaries.append(f"""
论文 {i}：
标题：{paper['title']}
作者：{', '.join(paper['authors'])}
发布日期：{paper['published'][:10]}
arXiv链接：{paper['pdf_url']}
研究目的：[生成失败: {str(e)}]
主要发现：[生成失败: {str(e)}]
---""")
            return "\n".join(error_summaries)

    def _process_batch(self, papers: List[Dict[str, Any]], start_index: int) -> str:
        """处理一批论文"""
        print(f"正在批量处理 {len(papers)} 篇论文...")
        summaries = self._generate_batch_summaries(papers, start_index)
        time.sleep(2)  # 在批次之间添加短暂延迟
        return summaries

    def _generate_batch_summary(self, papers: List[Dict[str, Any]]) -> str:
        """批量生成所有论文的总结"""
        all_summaries = []
        total_papers = len(papers)
        
        for i in range(0, total_papers, self.max_papers_per_batch):
            batch = papers[i:i + self.max_papers_per_batch]
            print(f"\n正在处理第 {i + 1} 到 {min(i + self.max_papers_per_batch, total_papers)} 篇论文...")
            batch_summary = self._process_batch(batch, i + 1)
            all_summaries.append(batch_summary)
            
            if i + self.max_papers_per_batch < total_papers:
                print("批次处理完成，等待3秒后继续...")
                time.sleep(3)  # 批次之间的冷却时间
        
        return "\n".join(all_summaries)

    def summarize_papers(self, papers: List[Dict[str, Any]], output_file: str):
        """批量处理所有论文并创建Markdown报告"""
        try:
            # 生成总结内容
            print(f"开始生成论文总结，共 {len(papers)} 篇...")
            summaries = self._generate_batch_summary(papers)
            
            # 转换为markdown格式
            markdown_content = self._generate_markdown(papers, summaries)
            
            # 保存为markdown文件
            output_md = output_file.replace('.pdf', '.md')
            with open(output_md, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"Markdown文件已保存：{output_md}")
            
        except Exception as e:
            # 如果生成总结失败，保存基本信息为markdown格式
            error_content = f"""# Arxiv论文总结报告

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**生成总结时发生错误，以下是论文基本信息：**

"""
            for i, paper in enumerate(papers, 1):
                error_content += f"""
## 论文 {i}：
- 标题：{paper['title']}
- 作者：{', '.join(paper['authors'])}
- 发布日期：{paper['published'][:10]}
- arXiv链接：{paper['pdf_url']}

"""
            
            # 保存错误信息为markdown文件
            error_md = output_file.replace('.pdf', '_error.md')
            with open(error_md, 'w', encoding='utf-8') as f:
                f.write(error_content)
            print(f"发生错误，已保存基本信息到：{error_md}")

    def _generate_markdown(self, papers: List[Dict[str, Any]], summaries: str) -> str:
        """生成markdown格式的报告"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        markdown_content = f"""# Arxiv论文总结报告

## 基本信息
- 生成时间：{current_time}
- 使用模型：{self.client.model}
- 论文数量：{len(papers)} 篇

---

## 论文总结

{summaries}

---

## 生成说明
- 本报告由AI模型自动生成
- 每篇论文的总结包含研究目的和主要发现
- 如有错误或遗漏请以原文为准
"""
        return markdown_content

def create_summarizer(api_key: str, model: Optional[str] = None) -> PaperSummarizer:
    """
    创建论文总结器实例
    
    Args:
        api_key: API密钥
        model: 可选的模型名称，默认使用配置中的模型
    """
    return PaperSummarizer(api_key, model)