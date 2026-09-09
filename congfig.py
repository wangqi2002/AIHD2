"""
robot agent系统配置文件
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class RAGConfig:
    """RAG系统配置类"""

    # 路径配置
    prompt_path: str = "./prompts"
    data_path: str = "./data"
    index_save_path: str = "./vector_index"

    # 模型配置
    local_model: str = "/home/win/.cache/modelscope/hub/Qwen/Qwen3-4B"
    api_model: str = "False"
    embedding_model: str = "BAAI/bge-small-zh-v1.5"

    # 音频文件



# 默认配置实例
DEFAULT_CONFIG = RAGConfig()
