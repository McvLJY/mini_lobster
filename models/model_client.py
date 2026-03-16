# models/model_client.py
from openai import OpenAI
from .model_config import MODEL_CONFIGS, CURRENT_MODEL, ModelProvider


class ModelClient:
    """统一的模型客户端接口"""
    def __init__(self, provider=None):
        self.provider = provider or CURRENT_MODEL
        self.config = MODEL_CONFIGS[self.provider]
        self.client = OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["base_url"]
        )
        self.model_name = self.config["default_model"]
        print(f"✅ 使用模型: {self.provider.value} - {self.model_name}")

    def chat_completion(self, messages, tools=None, tool_choice="auto", temperature=0.2):
        # 基础参数
        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
        }

        # 根据不同的模型提供商做适配
        if self.provider == ModelProvider.DEEPSEEK:
            # DeepSeek 原生支持工具调用
            if tools:
                params["tools"] = tools
                params["tool_choice"] = tool_choice

        elif self.provider == ModelProvider.VLLM:
            # vLLM 需要特殊参数启用工具调用
            if tools:
                params["tools"] = tools
                params["tool_choice"] = tool_choice
                params["extra_body"] = {
                    "chat_template_kwargs": {"enable_thinking": False},
                    "enable_auto_tool_choice": True,
                    "tool_choice": tool_choice
                }
            else:
                # 纯文本对话时不需要工具参数
                params["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}

        # elif self.provider == ModelProvider.OPENAI:
        #     # OpenAI 原生支持工具调用
        #     if tools:
        #         params["tools"] = tools
        #         params["tool_choice"] = tool_choice
        #
        # elif self.provider == ModelProvider.OLLAMA:
        #     # Ollama 可能不支持工具调用，或者方式不同
        #     if tools:
        #         print("Ollama 可能不支持工具调用，将忽略工具参数")

        # 添加配置中的额外参数
        params.update(self.config.get("extra_params", {}))

        try:
            return self.client.chat.completions.create(**params)
        except Exception as e:
            print(f"❌ 模型调用失败: {e}")
            print(f"参数: {params}")
            raise