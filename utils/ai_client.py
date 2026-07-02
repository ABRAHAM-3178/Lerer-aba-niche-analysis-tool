"""
大模型统一客户端
支持 OpenAI、DeepSeek、通义千问等兼容接口
"""

import openai
import json
from typing import Optional, Dict, Any, List


class AIClient:
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def chat_json(self, messages: List[Dict[str, str]], temperature: float = 0.3) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content
            return json.loads(result)
        except Exception as e:
            raise RuntimeError(f"AI API 调用失败: {e}")
    
    def chat_text(self, messages: List[Dict[str, str]], temperature: float = 0.5) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"AI API 调用失败: {e}")
