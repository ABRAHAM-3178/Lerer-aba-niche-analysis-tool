"""
AI客户端 - 默认使用DeepSeek，预留其他接口扩展
"""

import os
import json
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


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
    """
    AI客户端 - 统一接口
    
    默认使用 DeepSeek API（兼容OpenAI格式）
    预留接口，便于后续切换其他提供商
    """
    
    # 各提供商的默认配置
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
        "azure": {
            "base_url": None,  # 需要用户提供 endpoint
            "model": "gpt-4",
            "env_key": "AZURE_OPENAI_API_KEY",
        },
        "local": {
            "base_url": "http://localhost:11434/api/generate",  # Ollama 示例
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
        """
        初始化AI客户端
        
        Args:
            provider: deepseek | openai | azure | local
            api_key: API密钥，不传则从环境变量读取
            base_url: 自定义API端点
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大输出token数
        """
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 获取提供商配置
        config = self.PROVIDER_CONFIGS.get(provider, {})
        
        # 设置API Key
        if api_key:
            self.api_key = api_key
        elif config.get("env_key"):
            self.api_key = os.getenv(config["env_key"])
        else:
            self.api_key = None
        
        # 设置Base URL
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = config.get("base_url")
        
        # 设置模型
        if model:
            self.model = model
        else:
            self.model = config.get("model", "deepseek-chat")
        
        # 初始化客户端
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """初始化底层客户端"""
        if self.provider in ["deepseek", "openai", "azure"]:
            try:
                from openai import OpenAI
                
                # 构建客户端参数
                client_kwargs = {
                    "api_key": self.api_key,
                }
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                
                self._client = OpenAI(**client_kwargs)
                self._client_type = "openai"
                
            except ImportError:
                raise ImportError("请安装 openai: pip install openai")
        
        elif self.provider == "local":
            # 本地模型（如 Ollama），使用 requests
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
        response_format: Optional[str] = None,
    ) -> str:
        """
        发送聊天请求
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度（覆盖默认值）
            max_tokens: 最大输出token（覆盖默认值）
            response_format: 响应格式（json | text）
        
        Returns:
            AI响应文本
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            if self._client_type == "openai":
                return self._chat_openai(prompt, system_prompt, temp, tokens, response_format)
            elif self._client_type == "requests":
                return self._chat_local(prompt, system_prompt, temp, tokens)
            else:
                return "[错误] 客户端未初始化"
                
        except Exception as e:
            return f"[AI调用失败] {str(e)}"
    
    def _chat_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        response_format: Optional[str] = None,
    ) -> str:
        """OpenAI兼容接口（DeepSeek、Azure均使用此格式）"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # 构建请求参数
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # JSON模式支持（部分模型支持）
        if response_format == "json" and self.provider in ["deepseek", "openai"]:
            params["response_format"] = {"type": "json_object"}
        
        response = self._client.chat.completions.create(**params)
        return response.choices[0].message.content.strip()
    
    def _chat_local(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """本地模型（如Ollama）"""
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
        else:
            return f"[本地模型错误] HTTP {response.status_code}: {response.text}"
    
    def chat_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        请求JSON格式响应
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度（JSON建议用较低温度）
        
        Returns:
            解析后的JSON字典
        """
        # 添加JSON格式指示
        if not system_prompt:
            system_prompt = "你是一位数据分析专家。请始终以JSON格式返回结果，不要包含任何其他文字。"
        else:
            system_prompt += "\n\n请始终以JSON格式返回结果，不要包含任何其他文字。"
        
        response = self.chat(prompt, system_prompt, temperature, response_format="json")
        
        # 尝试解析JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON代码块
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except:
                    pass
            
            # 尝试提取纯JSON对象
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            return {"error": "无法解析JSON", "raw_response": response[:500]}
    
    def summarize(self, text: str, max_length: int = 100) -> str:
        """文本摘要快捷方法"""
        prompt = f"请将以下内容用{max_length}字以内简洁概括：\n\n{text}"
        return self.chat(prompt, temperature=0.5, max_tokens=max_length * 2)
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """提取关键词快捷方法"""
        prompt = f"从以下文本中提取{top_n}个最重要的关键词或短语，用逗号分隔：\n\n{text}"
        response = self.chat(prompt, temperature=0.3, max_tokens=200)
        keywords = [k.strip() for k in response.split(",")]
        return keywords[:top_n]
    
    def classify_sentiment(self, text: str) -> Dict[str, Any]:
        """情感分析快捷方法"""
        prompt = f"分析以下文本的情感，返回JSON格式：{{'sentiment': 'positive|negative|neutral', 'confidence': 0.0-1.0, 'keywords': []}}\n\n{text}"
        return self.chat_json(prompt, temperature=0.1)
    
    def generate_solutions(self, pain_point: str, product_name: str = "该产品") -> List[str]:
        """生成产品改良建议"""
        prompt = f"""
        消费者对【{product_name}】的差评中反馈以下痛点：
        
        【{pain_point}】
        
        请给出2-3条具体的、可落地的产品改良建议。
        每条建议控制在30字以内，用序号列出。
        """
        response = self.chat(prompt, temperature=0.7, max_tokens=300)
        
        # 解析建议列表
        suggestions = []
        for line in response.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                # 移除序号符号
                clean = re.sub(r'^[\d\-•]+\.?\s*', '', line)
                if clean:
                    suggestions.append(clean)
        
        return suggestions if suggestions else [response[:100]]


# 便捷函数：创建默认客户端
def create_deepseek_client(api_key: Optional[str] = None) -> AIClient:
    """创建DeepSeek客户端（默认）"""
    return AIClient(
        provider="deepseek",
        api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
    )


def create_openai_client(api_key: Optional[str] = None) -> AIClient:
    """创建OpenAI客户端（备用）"""
    return AIClient(
        provider="openai",
        api_key=api_key or os.getenv("OPENAI_API_KEY"),
    )


def create_local_client(base_url: str = "http://localhost:11434/api/generate", model: str = "llama3") -> AIClient:
    """创建本地客户端（备用）"""
    return AIClient(
        provider="local",
        base_url=base_url,
        model=model,
        api_key="",  # 本地不需要key
    )
