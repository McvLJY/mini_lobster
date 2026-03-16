# tools/image_analyzer_vllm.py
import os
import base64
from openai import OpenAI

from utilities.PARAMS import *


# 工具定义
image_analysis_tool = {
    "type": "function",
    "function": {
        "name": "analyze_image",
        "description": """
分析本地图片内容。支持：
- 单张图片详细分析
- 回答关于图片的具体问题

适合任务：
- 读取图片中的文字（OCR）
- 识别图片中的物体、场景
- 分析图表、截图内容
""",
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "图片文件的完整路径"
                },
                "question": {
                    "type": "string",
                    "description": "关于图片的问题，如'这张图片里有什么？'、'请详细描述'等",
                    "default": "请详细描述这张图片"
                },
                "purpose": {
                    "type": "string",
                    "description": "分析目的说明"
                }
            },
            "required": ["image_path", "purpose"]
        }
    }
}


class ImageAnalyzerVLLM:
    """基于vLLM服务的图片分析器"""

    def __init__(self, base_url=IMAGE_AGENT_BASE_URL, model_path=IMAGE_AGENT_LOCAL_MODEL_ADDRESS):
        self.client = OpenAI(
            base_url=base_url,
            api_key="EMPTY"
        )
        self.model_path = model_path
        print(f"✅ 图片分析器初始化完成，连接 vLLM 服务: {base_url}")

    def analyze_single(self, image_path: str, question: str) -> dict:
        """
        分析单张图片

        Args:
            image_path: 图片文件路径
            question: 关于图片的问题

        Returns:
            dict: 包含分析结果的字典
        """
        result = {
            "success": False,
            "output": "",
            "error": None,
            "image_info": {}
        }

        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                result["error"] = f"文件不存在: {image_path}"
                return result

            # 获取图片基本信息
            file_size = os.path.getsize(image_path)
            result["image_info"] = {
                "filename": os.path.basename(image_path),
                "path": image_path,
                "size_bytes": file_size,
                "size_kb": round(file_size / 1024, 2)
            }

            # 读取图片并转为 base64
            with open(image_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode("utf-8")

            # 调用 vLLM 服务
            response = self.client.chat.completions.create(
                model=self.model_path,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": question
                            }
                        ]
                    }
                ],
                temperature=0.2,
                max_tokens=IMAGE_AGENT_LOCAL_MODEL_MAX_TOKENS,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}}
            )

            result["success"] = True
            result["output"] = response.choices[0].message.content

        except Exception as e:
            result["error"] = str(e)

        return result


# 全局单例
_analyzer = None


def get_analyzer(base_url=IMAGE_AGENT_BASE_URL, model_path=IMAGE_AGENT_LOCAL_MODEL_ADDRESS):
    """获取图片分析器单例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = ImageAnalyzerVLLM(base_url, model_path)
    return _analyzer


def execute_image_analysis(image_path: str, question: str = "请详细描述这张图片", purpose: str = ""):
    """
    执行图片分析的工具函数

    Args:
        image_path: 图片文件路径
        question: 问题
        purpose: 分析目的

    Returns:
        dict: 分析结果
    """
    analyzer = get_analyzer()
    result = analyzer.analyze_single(image_path, question)

    # 添加目的说明到输出
    if purpose and result["success"]:
        result["output"] = f"[分析目的: {purpose}]\n\n{result['output']}"

    return result


if __name__ == "__main__":
    # 测试代码
    import sys

    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        question = sys.argv[2] if len(sys.argv) > 2 else "这张图片里有什么？"

        print(f"正在分析图片: {image_path}")
        print(f"问题: {question}")
        print("-" * 50)

        result = execute_image_analysis(image_path, question)

        if result["success"]:
            print("✅ 分析成功!")
            print(f"图片信息: {result['image_info']}")
            print(f"\n回答:\n{result['output']}")
        else:
            print(f"❌ 分析失败: {result['error']}")
    else:
        print("请指定图片路径")