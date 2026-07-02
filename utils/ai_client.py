"""
AI客户端 - 默认使用DeepSeek，预留其他接口扩展
"""

import os
import json
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class AIConfig:
    """AI配置"""
    provider: str = "deepseek"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.7


class AIClient:
    """AI客户端 - 统一接口，默认DeepSeek"""
    
    PROVIDER_CONFIGS = {
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "env_key": "DEEPSEEK_API_KEY",
        },
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "env_key": "OPENAI_API_KEY",
        },
        "local": {
            "base_url": "http://localhost:11434/api/generate",
            "model": "llama3",
            "env_key": None,
        }
    }
    
    def __init__(
        self,
        provider: str = "deepseek",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        config = self.PROVIDER_CONFIGS.get(provider, {})
        
        if api_key:
            self.api_key = api_key
        elif config.get("env_key"):
            self.api_key = os.getenv(config["env_key"])
        else:
            self.api_key = None
        
        self.base_url = base_url or config.get("base_url")
        self.model = model or config.get("model", "deepseek-chat")
        
        self._client = None
        self._client_type = None
        self._init_client()
    
    def _init_client(self):
        if self.provider in ["deepseek", "openai"]:
            try:
                from openai import OpenAI
                client_kwargs = {"api_key": self.api_key}
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                self._client = OpenAI(**client_kwargs)
                self._client_type = "openai"
            except ImportError:
                raise ImportError("请安装 openai: pip install openai")
        elif self.provider == "local":
            try:
                import requests
                self._client = requests.Session()
                self._client_type = "requests"
            except ImportError:
                raise ImportError("请安装 requests: pip install requests")
        else:
            raise ValueError(f"不支持的AI提供商: {self.provider}")
    
    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """发送聊天请求"""
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            if self._client_type == "openai":
                return self._chat_openai(prompt, system_prompt, temp, tokens)
            elif self._client_type == "requests":
                return self._chat_local(prompt, system_prompt, temp, tokens)
            return "[错误] 客户端未初始化"
        except Exception as e:
            return f"[AI调用失败] {str(e)}"
    
    def _chat_openai(self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    
    def _chat_local(self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        response = self._client.post(self.base_url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()
        return f"[本地模型错误] HTTP {response.status_code}"
    
    def chat_json(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.3) -> Dict[str, Any]:
        """请求JSON格式响应"""
        sys_prompt = system_prompt or "你是一位数据分析专家。请始终以JSON格式返回结果，不要包含其他文字。"
        if "JSON" not in sys_prompt:
            sys_prompt += "\n\n请始终以JSON格式返回结果，不要包含其他文字。"
        
        response = self.chat(prompt, sys_prompt, temperature)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except:
                    pass
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            return {"error": "无法解析JSON", "raw_response": response[:500]}
    
    def generate_solutions(self, pain_point: str, product_name: str = "该产品") -> List[str]:
        """生成产品改良建议"""
        prompt = f"""
        消费者对【{product_name}】的差评中反馈以下痛点：
        
        【{pain_point}】
        
        请给出2-3条具体的、可落地的产品改良建议。
        每条建议控制在30字以内，用序号列出。
        """
        response = self.chat(prompt, temperature=0.7, max_tokens=300)
        
        suggestions = []
        for line in response.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                clean = re.sub(r'^[\d\-•]+\.?\s*', '', line)
                if clean:
                    suggestions.append(clean)
        
        return suggestions if suggestions else [response[:100]]


def create_deepseek_client(api_key: Optional[str] = None) -> AIClient:
    """创建DeepSeek客户端"""
    return AIClient(provider="deepseek", api_key=api_key)


def create_openai_client(api_key: Optional[str] = None) -> AIClient:
    """创建OpenAI客户端"""
    return AIClient(provider="openai", api_key=api_key)
