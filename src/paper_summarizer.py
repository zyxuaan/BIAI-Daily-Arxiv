"""
论文总结模块 - 使用大语言模型API生成论文摘要
"""
import os
import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests
import time
from datetime import datetime
import pytz
from config.settings import LLM_CONFIG

class ModelClient:
    """语言模型API客户端"""
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or LLM_CONFIG['model']
        self.api_url = f"{LLM_CONFIG['api_url']}/{self.model}:generateContent"
        self.timeout = LLM_CONFIG.get('timeout', 60) # 增加超时时间
        
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
        prompt = messages[-1]["content"]
        
        return {
            "contents": [{"parts": [{"text": prompt}]}],
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
                
                response.raise_for_status() # 如果状态码不是2xx，则抛出异常
                    
                result = response.json()
                
                # 检查返回内容是否有效
                if not result.get("candidates") or not result["candidates"][0].get("content"):
                    raise ValueError("API返回了无效的响应内容")

                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": result["candidates"][0]["content"]["parts"][0]["text"]
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": result.get("usageMetadata", {})
                }
            except requests.Timeout:
                print(f"请求超时({self.timeout}秒), 正在重试({attempt + 1}/{LLM_CONFIG['retry_count']})...")
                if attempt == LLM_CONFIG['retry_count'] - 1:
                    raise
                time.sleep(LLM_CONFIG['retry_delay'] * (2 ** attempt))
            except Exception as e:
                print(f"API调用失败: {e}, 正在重试({attempt + 1}/{LLM_CONFIG['retry_count']})...")
                if attempt == LLM_CONFIG['retry_count'] - 1:
                    raise
                time.sleep(LLM_CONFIG['retry_delay'] * (2 ** attempt))

class PaperSummarizer:
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.client = ModelClient(api_key, model)
        self.max_papers_per_batch = 20 # 适当减少批处理数量，防止Prompt过长

    def _fix_markdown_links(self, text: str) -> str:
        """使用正则表达式修复未正确格式化的Markdown链接"""
        # 正则表达式查找 '### Title (http...)' 或 '### Title(http...)' 格式
        # 它会捕获标题文本和括号内的URL
        pattern = re.compile(r'^(###\s*)(.*?)\s*\((https?://[^\s)]+)\)$', re.MULTILINE)
        
        # 替换函数，将捕获的组重新格式化为 '[Title](URL)'
        def replacer(match):
            prefix = match.group(1)
            title = match.group(2).strip()
            url = match.group(3)
            return f'{prefix}[{title}]({url})'
            
        return pattern.sub(replacer, text)

    def _generate_batch_summaries(self, papers: List[Dict[str, Any]], start_index: int) -> str:
        """为一批论文生成总结"""
        batch_prompt = ""
        for i, paper in enumerate(papers, start=start_index):
            # 确保摘要只取一部分，避免prompt过长
            summary_snippet = (paper['summary'][:800] + '...') if len(paper['summary']) > 800 else paper['summary']
            batch_prompt += f"""
---
论文 {i}:
- 标题: {paper['title']}
- 作者: {', '.join(paper['authors'])}
- 发布日期: {paper['published'][:10]}
- arXiv链接: {paper['entry_id']}
- 摘要: {summary_snippet}
"""
        
        final_prompt = f"""请为以下{len(papers)}篇来自ArXiv的论文生成中文总结。每篇论文的总结都需要遵循严格的Markdown格式。

**必须遵循的输出格式:**
对于每一篇论文，你的输出必须是以下格式，不得有任何变动：

### [论文标题](论文的arXiv链接)
<!-- 论文发布日期，格式：YYYY-MM-DD -->
* **作者**: 作者名
* **研究目的**: 一句话总结研究的核心目标。
* **主要发现**: 一句话总结最重要的发现或贡献。

---

**关键指令:**
1.  **链接格式**: 论文标题必须作为可点击的Markdown链接，格式为 `[标题](链接)`。
2.  **日期注释**: 在标题下方，必须插入HTML注释 `<!-- YYYY-MM-DD -->` 来标记发布日期，格式严格为YYYY-MM-DD。
3.  **内容**: "研究目的"和"主要发现"必须是简洁的一句话总结。
4.  **分隔符**: 每篇论文总结之后，必须使用 `---` 作为分隔符。
5.  **语言**: 所有输出内容必须为中文。
6.  **数学公式**: 你可以自由使用LaTeX语法（例如 `$E=mc^2$`）来表示数学公式。

**需要你处理的论文信息如下:**
{batch_prompt}
"""
        try:
            response = self.client.chat_completion([{"role": "user", "content": final_prompt}])
            content = response["choices"][0]["message"]["content"].strip()
            # 在返回内容后，立即进行链接修复
            return self._fix_markdown_links(content)
        except Exception as e:
            error_msg = f"[摘要生成失败: {str(e)}]"
            return "\n".join([f"### {p['title']}\n<!-- {p['published'][:10]} -->\n- **研究目的**: {error_msg}\n- **主要发现**: {error_msg}\n---" for p in papers])

    def _process_batch(self, papers: List[Dict[str, Any]], start_index: int) -> str:
        """处理一批论文"""
        print(f"正在批量处理 {len(papers)} 篇论文...")
        summaries = self._generate_batch_summaries(papers, start_index)
        time.sleep(2)
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
                print(f"批次处理完成，等待 {LLM_CONFIG['retry_delay']} 秒后继续...")
                time.sleep(LLM_CONFIG['retry_delay'])
        
        return "\n".join(all_summaries)

    def summarize_papers(self, papers: List[Dict[str, Any]], output_file: str) -> bool:
        """批量处理所有论文并创建Markdown报告"""
        print(f"开始生成论文总结，共 {len(papers)} 篇...")
        summaries = self._generate_batch_summary(papers)
        
        api_success = "[生成失败:" not in summaries
        if not api_success:
            print("警告: 摘要生成过程中出现错误，结果可能不完整")

        markdown_content = self._generate_markdown(papers, summaries)
        
        output_md = Path(output_file).with_suffix('.md')
        output_md.write_text(markdown_content, encoding='utf-8')
        print(f"Markdown文件已保存：{output_md}")
        
        return api_success

    def _generate_markdown(self, papers: List[Dict[str, Any]], summaries: str) -> str:
        """生成markdown格式的报告"""
        beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""# Arxiv论文总结报告(Brain-inspired AI)

## 基本信息
- 生成时间: {beijing_time}
- 使用模型: {self.client.model}
- 论文数量: {len(papers)} 篇

---

## 论文总结

{summaries}

---

## 生成说明
- 本报告由AI模型自动生成，摘要内容仅供参考。
- 如有错误或遗漏，请以原始论文为准。
"""