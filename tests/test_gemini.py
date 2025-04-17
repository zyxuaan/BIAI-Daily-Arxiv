"""
测试 Gemini API 连接
"""
import sys
import os
import json
import requests
from typing import Dict, Any, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import GEMINI_API_KEY

class GeminiClient:
    """使用 OpenAI 风格的 API 格式调用 Gemini"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
    def _create_headers(self) -> Dict[str, str]:
        """创建请求头"""
        return {
            "Content-Type": "application/json"
        }
    
    def _create_request_body(
        self, 
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
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
                "temperature": temperature,
                "maxOutputTokens": max_tokens if max_tokens else 2048,
                "topP": 0.8,
                "topK": 40
            }
        }
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建聊天完成（模拟 OpenAI 的 chat.completions.create）"""
        headers = self._create_headers()
        data = self._create_request_body(messages, temperature, max_tokens)
        
        try:
            print("调试 - 发送请求到:", f"{self.api_url}?key={self.api_key[:10]}...")
            print("调试 - 请求体:", json.dumps(data, ensure_ascii=False, indent=2))
            
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=data
            )
            
            print("调试 - 响应状态码:", response.status_code)
            print("调试 - 响应内容:", response.text[:200])
            
            if response.status_code != 200:
                raise Exception(f"API 调用失败: {response.text}")
                
            result = response.json()
            
            # 将 Gemini 响应转换为 OpenAI 格式
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": result["candidates"][0]["content"]["parts"][0]["text"]
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 0,  # Gemini 不提供这些信息
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        except Exception as e:
            print("调试 - 发生错误:", str(e))
            raise

def test_gemini_connection():
    """测试 Gemini API 的连接性"""
    print("开始测试 Gemini API 连接...")
    
    try:
        # 创建客户端
        client = GeminiClient(GEMINI_API_KEY)
        
        # 准备测试消息
        messages = [{
            "role": "user",
            "content": "请用中文回复：你好，这是一条测试消息。"
        }]
        
        # 发送请求
        response = client.chat_completion(
            messages=messages,
            temperature=0.7
        )
        
        print("\n模型响应:")
        print("-" * 50)
        print(response["choices"][0]["message"]["content"])
        print("-" * 50)
        print("\nGemini API 连接测试成功！")
        return True
        
    except Exception as e:
        print("\n错误：Gemini API 连接失败")
        print(f"错误信息: {str(e)}")
        return False

if __name__ == "__main__":
    test_gemini_connection()