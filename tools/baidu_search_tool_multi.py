
# tools/baidu_search.py
import requests
import json
from typing import List, Dict, Any, Optional, Literal
from utilities.PARAMS import BAIDU_SEARCH_API_KEY

# 定义支持的资源类型
ResourceType = Literal["web", "image", "video", "news"]
VALID_RESOURCE_TYPES = {"web", "image", "video", "news"}
DEFAULT_RESOURCE_TYPES = ["web"]


def normalize_resource_types(resource_types):
    """
    标准化 resource_types 参数
    - 处理 None -> 返回默认值
    - 处理字符串 -> 转为列表
    - 过滤非法类型
    - 处理空列表 -> 返回默认值
    """
    # 处理 None
    if resource_types is None:
        return DEFAULT_RESOURCE_TYPES.copy()

    # 处理字符串
    if isinstance(resource_types, str):
        resource_types = [resource_types]

    # 确保是列表
    if not isinstance(resource_types, list):
        print(f"警告：resource_types 应为列表或字符串，收到 {type(resource_types)}，使用默认值")
        return DEFAULT_RESOURCE_TYPES.copy()

    # 过滤非法类型
    original_count = len(resource_types)
    valid_types = [t for t in resource_types if t in VALID_RESOURCE_TYPES]

    # 如果有非法类型，记录警告
    if len(valid_types) != original_count:
        invalid = set(resource_types) - set(valid_types)
        print(f"警告：过滤了非法资源类型 {invalid}，仅支持 {VALID_RESOURCE_TYPES}")

    # 如果过滤后为空，使用默认值
    if not valid_types:
        print("警告：没有合法的资源类型，使用默认值 ['web']")
        return DEFAULT_RESOURCE_TYPES.copy()

    return valid_types


# 百度搜索工具定义
baidu_search_tool = {
    "type": "function",
    "function": {
        "name": "baidu_search",
        "description": """
使用百度搜索引擎搜索最新信息。支持网页、图片、视频等多种类型的结果。
适合查询：
- 实时新闻和事件
- 最新数据（股票、汇率、天气等）
- 需要联网验证的事实
- 当前热点话题
- 专业知识查询
- Python包或功能的用法查询
- 图片搜索（人物、地点、物品等视觉信息）

注意：返回结果包含标题和内容摘要，可以获取top_k条结果（默认5条）。
""",
        "parameters": {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "string",
                    "description": "搜索查询词，可以是一个或多个关键词，用空格分隔"
                },
                "resource_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["web", "image", "video", "news"]
                    },
                    "description": "需要返回的资源类型，默认只返回网页。如果要搜图，传入['image']",
                    "default": ["web"]
                },
                "top_k": {
                    "type": "integer",
                    "description": "每种资源类型返回的结果数量，默认5条，最多10条",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5
                },
                "search_recency": {
                    "type": "string",
                    "description": "搜索时效性，可选：'day'（一天内）、'week'（一周内）、'month'（一月内）、'year'（一年内）",
                    "enum": ["day", "week", "month", "year"],
                    "default": "year"
                },
                "purpose": {
                    "type": "string",
                    "description": "搜索目的说明，帮助理解为什么需要搜索这个信息"
                }
            },
            "required": ["queries", "purpose"]
        }
    }
}


class BaiduSearchAPI:
    """百度搜索API封装 - 支持网页和图片搜索"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        # 注意：图片搜索需要使用 chat/completions 接口
        self.web_search_url = "https://qianfan.baidubce.com/v2/ai_search/web_search"
        self.chat_completions_url = "https://qianfan.baidubce.com/v2/ai_search/chat/completions"

    def search(self,
               queries: str,
               resource_types: List[ResourceType] = ["web"],
               top_k: int = 5,
               search_recency: str = "year") -> Dict[str, Any]:
        """
        执行百度搜索（支持多类型）

        Args:
            queries: 搜索查询词
            resource_types: 资源类型列表，如 ["web"], ["image"], ["web", "image"]
            top_k: 每种类型返回的结果数量
            search_recency: 时效性过滤

        Returns:
            原始API返回结果
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构建 resource_type_filter
        resource_filter = []
        for rtype in resource_types:
            resource_filter.append({
                "type": rtype,
                "top_k": top_k
            })

        # 根据是否包含图片选择不同的接口
        if "image" in resource_types:
            # 图片搜索需要使用 chat/completions 接口
            url = self.chat_completions_url
            data = {
                "messages": [
                    {"content": queries, "role": "user"}
                ],
                "search_source": "baidu_search_v1",
                "resource_type_filter": resource_filter,
                # "search_recency_filter": search_recency,
                "model": "ernie-3.5-8k"
            }
        else:
            # 纯文本搜索用 web_search 接口
            url = self.web_search_url
            data = {
                "messages": [
                    {"content": queries, "role": "user"}
                ],
                "search_source": "baidu_search_v2",
                "resource_type_filter": resource_filter,
                "search_recency_filter": search_recency
            }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"搜索请求失败: {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"响应解析失败: {str(e)}"}

    def clean_results(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗搜索结果，提取关键信息（支持网页和图片）

        Args:
            result: 原始API返回结果

        Returns:
            清洗后的结构化结果
        """
        if "error" in result:
            return result

        cleaned = {
            "success": True,
            "total_results": 0,
            "results": [],
            "images": []
        }

        if "references" in result:
            cleaned["total_results"] = len(result["references"])

            for ref in result["references"]:
                # 通用字段
                item = {
                    "type": ref.get("type", "unknown"),
                    "title": ref.get("title", ""),
                    "url": ref.get("url", ref.get("link", "")),
                    "source": ref.get("source", ""),
                    "date": ref.get("date", "")
                }

                # 根据类型添加特定字段
                if item["type"] == "image":
                    item["image_url"] = ref.get("image_url", ref.get("img_url", ""))
                    item["width"] = ref.get("width")
                    item["height"] = ref.get("height")
                    item["content"] = ref.get("content", ref.get("description", ""))
                    cleaned["images"].append(item)
                elif item["type"] == "web":
                    item["content"] = ref.get("content", "")
                    item["snippet"] = ref.get("snippet", ref.get("content", ""))[:200]

                cleaned["results"].append(item)

        # 如果包含图片，也尝试从其他地方获取
        if "images" in result:
            for img in result["images"]:
                image_item = {
                    "type": "image",
                    "title": img.get("title", ""),
                    "url": img.get("url", ""),
                    "image_url": img.get("image_url", img.get("img_url", "")),
                    "source": img.get("source", ""),
                    "width": img.get("width"),
                    "height": img.get("height")
                }
                cleaned["images"].append(image_item)
                cleaned["results"].append(image_item)

        return cleaned

    def format_for_llm(self, cleaned_results: Dict[str, Any]) -> str:
        """
        将搜索结果格式化为适合LLM阅读的文本（支持网页和图片）

        Args:
            cleaned_results: 清洗后的结果

        Returns:
            格式化的文本
        """
        if "error" in cleaned_results:
            return f"搜索失败: {cleaned_results['error']}"

        if not cleaned_results["results"]:
            return "未找到相关搜索结果。"

        formatted = f"找到 {cleaned_results['total_results']} 条相关结果：\n\n"

        # 分别处理不同类型的资源
        web_results = [r for r in cleaned_results["results"] if r.get("type") == "web"]
        image_results = cleaned_results["images"]

        # 先显示网页结果
        if web_results:
            formatted += "📄 网页信息：\n"
            for i, res in enumerate(web_results, 1):
                formatted += f"【{i}】{res['title']}\n"
                formatted += f"   内容：{res.get('content', '')[:200]}...\n"
                if res.get('url'):
                    formatted += f"   链接：{res['url']}\n"
                if res.get('date'):
                    formatted += f"   日期：{res['date']}\n"
                formatted += "\n"

        # 再显示图片结果
        if image_results:
            formatted += "🖼️ 图片结果：\n"
            for i, img in enumerate(image_results, 1):
                formatted += f"【图{i}】{img['title']}\n"
                if img.get('content'):
                    formatted += f"   描述：{img['content'][:200]}\n"
                if img.get('image_url'):
                    formatted += f"   图片地址：{img['image_url']}\n"
                if img.get('url'):
                    formatted += f"   来源页面：{img['url']}\n"
                formatted += "\n"

        return formatted


# 工具执行函数（供智能体调用）
def execute_baidu_search(
        queries: str,
        resource_types=None,
        top_k: int = 5,
        search_recency: str = "year",
        purpose: str = ""
):
    """
    执行百度搜索的工具函数（支持网页和图片）

    参数说明：
        resource_types: 可以是列表 ["web", "image"]，也可以是字符串 "web"
                        支持的类型: web, image, video, news
    """
    # 参数验证和标准化（核心逻辑）
    resource_types = normalize_resource_types(resource_types)

    # 验证 top_k
    if not isinstance(top_k, int) or top_k < 1 or top_k > 10:
        print(f"警告：top_k {top_k} 无效，使用默认值 5")
        top_k = 5

    # 验证 search_recency
    valid_recency = {"day", "week", "month", "year"}
    if search_recency not in valid_recency:
        print(f"警告：search_recency '{search_recency}' 无效，使用默认值 'year'")
        search_recency = "year"

    # 从环境变量或配置获取API_KEY
    API_KEY = BAIDU_SEARCH_API_KEY

    if not API_KEY:
        return {
            "success": False,
            "error": "未配置百度搜索API密钥",
            "output": "搜索失败：未配置API密钥"
        }

    searcher = BaiduSearchAPI(API_KEY)
    raw_result = searcher.search(queries, resource_types, top_k, search_recency)
    cleaned = searcher.clean_results(raw_result)

    if "error" in cleaned:
        return {
            "success": False,
            "error": cleaned["error"],
            "output": f"搜索失败：{cleaned['error']}"
        }

    # 格式化输出
    formatted = searcher.format_for_llm(cleaned)

    # 返回结果
    return {
        "success": True,
        "output": formatted,
        "error": None,
        "purpose": purpose,
        "query": queries,
        "resource_types": resource_types,
        "total_results": cleaned["total_results"],
        "image_count": len(cleaned.get("images", [])),
        "raw_data": {
            "web_results": [r for r in cleaned["results"][:3] if r.get("type") == "web"],
            "images": cleaned.get("images", [])[:3]
        }
    }


def execute_image_search(queries: str, top_k: int = 5, purpose: str = ""):
    """
    专门的图片搜索函数
    """
    return execute_baidu_search(
        queries=queries,
        resource_types=["image"],
        top_k=top_k,
        purpose=purpose
    )


def execute_web_search(queries: str, top_k: int = 5, search_recency: str = "year", purpose: str = ""):
    """
    专门的网页搜索函数（保持向后兼容）
    """
    return execute_baidu_search(
        queries=queries,
        resource_types=["web"],
        top_k=top_k,
        search_recency=search_recency,
        purpose=purpose
    )