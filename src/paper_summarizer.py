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
    
    def _extract_content_from_response(self, result: Dict[str, Any]) -> str:
        """从API响应中提取内容，处理不同的响应格式"""
        try:
            # 检查是否有错误
            if "error" in result:
                error_msg = result["error"].get("message", "Unknown API error")
                raise ValueError(f"API错误: {error_msg}")
            
            # 检查candidates
            if not result.get("candidates"):
                raise ValueError("API响应中没有candidates字段")
            
            candidates = result["candidates"]
            if not candidates:
                raise ValueError("API响应中candidates为空")
            
            # 获取第一个候选项
            candidate = candidates[0]
            
            # 检查是否被安全过滤器阻止
            if candidate.get("finishReason") == "SAFETY":
                raise ValueError("内容被安全过滤器阻止")
            
            # 尝试不同的内容提取方式
            content = None
            
            # 方式1: 标准格式 candidates[0].content.parts[0].text
            if "content" in candidate:
                content_obj = candidate["content"]
                if isinstance(content_obj, dict):
                    if "parts" in content_obj and content_obj["parts"]:
                        parts = content_obj["parts"]
                        if isinstance(parts, list) and len(parts) > 0:
                            first_part = parts[0]
                            if isinstance(first_part, dict) and "text" in first_part:
                                content = first_part["text"]
                    elif "text" in content_obj:
                        # 方式2: 直接在content中有text字段
                        content = content_obj["text"]
                elif isinstance(content_obj, str):
                    # 方式3: content直接是字符串
                    content = content_obj
            
            # 方式4: 直接在candidate中查找text
            if not content and "text" in candidate:
                content = candidate["text"]
            
            # 方式5: 查找message字段
            if not content and "message" in candidate:
                message = candidate["message"]
                if isinstance(message, dict) and "content" in message:
                    content = message["content"]
                elif isinstance(message, str):
                    content = message
            
            if not content:
                # 打印响应结构以便调试
                print(f"调试信息 - API响应结构: {json.dumps(result, indent=2, ensure_ascii=False)}")
                raise ValueError("无法从API响应中提取内容")
            
            if not isinstance(content, str):
                raise ValueError(f"提取的内容不是字符串类型: {type(content)}")
            
            return content.strip()
            
        except Exception as e:
            print(f"解析API响应时出错: {e}")
            print(f"响应结构: {json.dumps(result, indent=2, ensure_ascii=False)}")
            raise

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建聊天完成"""
        headers = self._create_headers()
        data = self._create_request_body(messages, temperature, max_tokens)
        
        last_exception = None
        
        for attempt in range(LLM_CONFIG['retry_count']):
            try:
                print(f"尝试API调用 (第{attempt + 1}次)...")
                response = requests.post(
                    f"{self.api_url}?key={self.api_key}",
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                # 检查HTTP状态码
                if response.status_code != 200:
                    error_msg = f"HTTP错误 {response.status_code}: {response.text}"
                    print(f"HTTP错误: {error_msg}")
                    raise requests.HTTPError(error_msg)
                
                # 解析JSON响应
                try:
                    result = response.json()
                except json.JSONDecodeError as e:
                    error_msg = f"JSON解析错误: {e}, 响应内容: {response.text[:500]}"
                    print(f"JSON解析错误: {error_msg}")
                    raise ValueError(error_msg)
                
                # 提取内容
                content = self._extract_content_from_response(result)
                
                print(f"API调用成功，内容长度: {len(content)}")
                
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": content
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": result.get("usageMetadata", {})
                }
                
            except requests.Timeout as e:
                last_exception = e
                print(f"请求超时({self.timeout}秒), 正在重试({attempt + 1}/{LLM_CONFIG['retry_count']})...")
                if attempt == LLM_CONFIG['retry_count'] - 1:
                    break
                time.sleep(LLM_CONFIG['retry_delay'] * (2 ** attempt))
                
            except requests.HTTPError as e:
                last_exception = e
                print(f"HTTP错误: {e}, 正在重试({attempt + 1}/{LLM_CONFIG['retry_count']})...")
                if attempt == LLM_CONFIG['retry_count'] - 1:
                    break
                time.sleep(LLM_CONFIG['retry_delay'] * (2 ** attempt))
                
            except Exception as e:
                last_exception = e
                print(f"API调用失败: {e}, 正在重试({attempt + 1}/{LLM_CONFIG['retry_count']})...")
                if attempt == LLM_CONFIG['retry_count'] - 1:
                    break
                time.sleep(LLM_CONFIG['retry_delay'] * (2 ** attempt))
        
        # 所有重试都失败了
        error_msg = f"API调用失败，已重试{LLM_CONFIG['retry_count']}次"
        if last_exception:
            error_msg += f"，最后一次错误: {last_exception}"
        
        print(f"最终错误: {error_msg}")
        raise Exception(error_msg)

class PaperSummarizer:
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.client = ModelClient(api_key, model)
        self.max_papers_per_batch = 20 # 适当减少批处理数量，防止Prompt过长

    def _fix_markdown_links(self, text: str) -> str:
        """使用正则表达式修复未正确格式化的Markdown链接"""
        # 正则表达式查找 '### Title (http...)' 或 '### Title(http...)' 格式
        # 它会捕获标题文本和括号内的URL
        pattern = re.compile(r'^(###\s*)(.*?)\s*\((https?://[^\s)]+)\)$', re.MULTILINE)
        
        # 替换函数，将捕获的组重新格式化为 '### [Title](URL)'
        def replacer(match):
            prefix = match.group(1)  # '### '
            title = match.group(2).strip()  # 标题
            url = match.group(3)  # URL
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
**📅 发布日期**: 论文发布日期(YYYY-MM-DD格式)

* **👥 作者**: 作者名
* **🎯 研究目的**: 详细描述研究的背景、动机和核心目标，包括解决的问题和研究意义。
* **⭐ 主要发现**: 详细阐述论文的核心贡献、创新点、实验结果和理论突破，以及对领域的潜在影响。

---

**关键指令:**
1.  **无需序号**: 论文标题前不需要添加序号，序号将由网站页面动态生成。
2.  **链接格式**: 论文标题必须作为可点击的Markdown链接，格式为 `[标题](链接)`。
3.  **日期注释**: 在标题下方，必须插入HTML注释 `<!-- YYYY-MM-DD -->` 来标记发布日期，格式严格为YYYY-MM-DD。
4.  **可见日期**: 在HTML注释后，必须添加可见的日期行：`**📅 发布日期**: YYYY-MM-DD`。
5.  **内容丰富**: "研究目的"应包含研究背景、动机和目标；"主要发现"应详细描述核心贡献、创新点和实验结果。
6.  **分隔符**: 每篇论文总结之后，必须使用 `---` 作为分隔符。
7.  **语言**: 所有输出内容必须为中文。
8.  **数学公式**: 你可以自由使用LaTeX语法（例如 `$E=mc^2$`）来表示数学公式。
9.  **完整性**: 必须为每篇论文生成完整的摘要，不得遗漏任何一篇。

**需要你处理的论文信息如下:**
{batch_prompt}
"""
        try:
            print(f"正在为{len(papers)}篇论文生成摘要...")
            response = self.client.chat_completion([{"role": "user", "content": final_prompt}])
            content = response["choices"][0]["message"]["content"].strip()
            
            # 检查生成的内容是否完整
            generated_sections = content.count('###')
            expected_sections = len(papers)
            
            if generated_sections < expected_sections:
                print(f"警告: 生成的摘要数量({generated_sections})少于预期({expected_sections})")
                print(f"可能部分论文摘要生成失败")
            
            # 在返回内容后，立即进行链接修复
            fixed_content = self._fix_markdown_links(content)
            print(f"摘要生成成功，共生成 {generated_sections} 个摘要")
            return fixed_content
            
        except Exception as e:
            print(f"批量生成摘要失败: {e}")
            print(f"将尝试为每篇论文单独生成摘要...")
            return self._generate_individual_summaries(papers)

    def _generate_individual_summaries(self, papers: List[Dict[str, Any]]) -> str:
        """逐个为论文生成摘要（作为批量失败的备选方案）"""
        individual_summaries = []
        
        for i, paper in enumerate(papers):
            try:
                print(f"正在为第{i+1}篇论文生成摘要: {paper['title'][:50]}...")
                
                # 为单篇论文生成摘要
                summary_snippet = (paper['summary'][:800] + '...') if len(paper['summary']) > 800 else paper['summary']
                
                single_prompt = f"""请为这篇来自ArXiv的论文生成中文总结。

**论文信息:**
- 标题: {paper['title']}
- 作者: {', '.join(paper['authors'])}
- 发布日期: {paper['published'][:10]}
- arXiv链接: {paper['entry_id']}
- 摘要: {summary_snippet}

**输出格式:**
### [论文标题](论文的arXiv链接)
<!-- 论文发布日期，格式：YYYY-MM-DD -->
**📅 发布日期**: 论文发布日期(YYYY-MM-DD格式)

* **👥 作者**: 作者名
* **🎯 研究目的**: 详细描述研究的背景、动机和核心目标，包括解决的问题和研究意义。
* **⭐ 主要发现**: 详细阐述论文的核心贡献、创新点、实验结果和理论突破，以及对领域的潜在影响。

---

请确保输出格式严格按照上述要求。"""

                response = self.client.chat_completion([{"role": "user", "content": single_prompt}])
                content = response["choices"][0]["message"]["content"].strip()
                fixed_content = self._fix_markdown_links(content)
                individual_summaries.append(fixed_content)
                print(f"第{i+1}篇论文摘要生成成功")
                
                # 为了避免API限制，添加小延迟
                if i < len(papers) - 1:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"第{i+1}篇论文摘要生成失败: {e}")
                # 生成错误摘要
                error_summary = f"""### [{paper['title']}]({paper['entry_id']})
<!-- {paper['published'][:10]} -->
**📅 发布日期**: {paper['published'][:10]}

* **👥 作者**: {', '.join(paper['authors'])}
* **🎯 研究目的**: 由于API调用失败，无法生成详细的研究目的摘要。请参考原始论文了解详情。
* **⭐ 主要发现**: 由于API调用失败，无法生成详细的主要发现摘要。请参考原始论文了解详情。

**错误信息**: {str(e)}

---"""
                individual_summaries.append(error_summary)
        
        return "\n".join(individual_summaries)

    def _process_batch(self, papers: List[Dict[str, Any]], start_index: int) -> str:
        """处理一批论文"""
        print(f"正在批量处理 {len(papers)} 篇论文...")
        summaries = self._generate_batch_summaries(papers, start_index)
        
        # 验证生成的摘要数量
        generated_count = summaries.count('###')
        expected_count = len(papers)
        
        if generated_count != expected_count:
            print(f"警告: 生成的摘要数量({generated_count})与预期({expected_count})不符")
        
        time.sleep(2)  # 为了避免API限制
        return summaries

    def _validate_summaries(self, summaries: str, expected_count: int) -> bool:
        """验证生成的摘要是否完整"""
        actual_count = summaries.count('###')
        is_valid = actual_count == expected_count
        
        if not is_valid:
            print(f"摘要验证失败: 期望{expected_count}篇，实际{actual_count}篇")
        
        return is_valid

    def _generate_batch_summary(self, papers: List[Dict[str, Any]]) -> str:
        """批量生成所有论文的总结"""
        all_summaries = []
        total_papers = len(papers)
        
        for i in range(0, total_papers, self.max_papers_per_batch):
            batch = papers[i:i + self.max_papers_per_batch]
            batch_size = len(batch)
            print(f"\n正在处理第 {i + 1} 到 {min(i + self.max_papers_per_batch, total_papers)} 篇论文...")
            
            try:
                batch_summary = self._process_batch(batch, i + 1)
                
                # 验证批次摘要
                if self._validate_summaries(batch_summary, batch_size):
                    all_summaries.append(batch_summary)
                    print(f"批次处理成功: {batch_size}篇论文")
                else:
                    print(f"批次验证失败，将逐个处理...")
                    individual_summary = self._generate_individual_summaries(batch)
                    all_summaries.append(individual_summary)
                    
            except Exception as e:
                print(f"批次处理失败: {e}")
                print(f"将逐个处理这{batch_size}篇论文...")
                individual_summary = self._generate_individual_summaries(batch)
                all_summaries.append(individual_summary)
            
            # 批次间等待
            if i + self.max_papers_per_batch < total_papers:
                print(f"批次处理完成，等待 {LLM_CONFIG['retry_delay']} 秒后继续...")
                time.sleep(LLM_CONFIG['retry_delay'])
        
        final_summary = "\n".join(all_summaries)
        
        # 最终验证
        if self._validate_summaries(final_summary, total_papers):
            print(f"✅ 所有{total_papers}篇论文摘要生成完成")
        else:
            print(f"⚠️ 部分论文摘要可能生成失败，请检查结果")
        
        return final_summary

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
        
        return f"""# Arxiv论文总结报告

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