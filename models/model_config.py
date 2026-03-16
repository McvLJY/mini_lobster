# models/model_config.py
from enum import Enum
from utilities.PARAMS import *

class ModelProvider(Enum):
    DEEPSEEK = "deepseek"
    VLLM = "vllm"

# 模型配置
MODEL_CONFIGS = {
    ModelProvider.DEEPSEEK: {
        "api_key": DEEPSEEK_API_KEY,
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "extra_params": {}
    },
    ModelProvider.VLLM: {
        "api_key": "EMPTY",
        "base_url": MAIN_AGENT_BASE_URL,
        "default_model": MAIN_AGENT_LOCAL_MODEL_ADDRESS,
        "extra_params": {
            "max_tokens": MAIN_AGENT_LOCAL_MODEL_MAX_TOKENS,
            # 其他 vLLM 特定参数
        }
    }
}

# 当前使用的模型 - 在这里切换
CURRENT_MODEL = ModelProvider.VLLM
