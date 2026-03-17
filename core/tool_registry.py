# core/tool_registry.py
import inspect
from typing import Dict, Any, Callable, List, Optional
import json
from functools import wraps
import os
import importlib.util
from pathlib import Path


def auto_discover(self):
    """自动发现tools目录下所有工具模块"""
    import pkgutil
    import importlib
    import tools

    print("🔍 开始自动发现工具...")

    # 获取 tools 包的路径
    tools_path = tools.__path__

    # 遍历所有模块
    for finder, name, ispkg in pkgutil.iter_modules(tools_path):
        if name.startswith('_'):
            continue

        try:
            # 使用 importlib 导入模块
            module = importlib.import_module(f'tools.{name}')
            print(f"✅ Auto-discovered: tools.{name}")

            # 查看模块里有哪些带 @tool 的函数
            tool_funcs = [attr for attr in dir(module)
                          if hasattr(getattr(module, attr), '_is_tool')]
            if tool_funcs:
                print(f"   └─ 发现工具: {', '.join(tool_funcs)}")

        except Exception as e:
            print(f"❌ Failed to load tools.{name}: {e}")

    # 列出所有已注册工具
    print(f"\n📋 当前已注册工具: {self.list_tools()}")


class ToolRegistry:
    """工具注册器 - 单例模式"""
    _instance = None
    _tools: Dict[str, Callable] = {}  # name -> function
    _tool_schemas: Dict[str, Dict] = {}  # name -> OpenAI schema
    _tool_metadata: Dict[str, Dict] = {}  # name -> metadata

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, name: str = None, schema: Dict = None, param_descriptions: Dict = None, **metadata):
        """装饰器：注册工具

        Args:
            name: 工具名称，默认使用函数名
            schema: 手动指定的完整schema（优先级最高）
            param_descriptions: 参数描述字典，如 {"code": "要执行的代码..."}
            **metadata: 其他元数据
        """

        def decorator(func):
            tool_name = name or func.__name__

            # 如果没有提供完整schema，则生成
            if schema is None:
                # ✨ 关键修改：把param_descriptions传进去！
                generated_schema = self._generate_schema_from_func(func, param_descriptions)
            else:
                generated_schema = schema

            # 存储工具
            self._tools[tool_name] = func
            self._tool_schemas[tool_name] = generated_schema
            self._tool_metadata[tool_name] = {
                "name": tool_name,
                "description": func.__doc__ or generated_schema.get("function", {}).get("description", ""),
                "registered_at": metadata.get("registered_at", "now"),
                "version": metadata.get("version", "1.0.0"),
                "category": metadata.get("category", "general"),
                **metadata
            }

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def _generate_schema_from_func(self, func, param_descriptions: Dict = None) -> Dict:
        """从函数签名生成OpenAI工具schema

        Args:
            func: 要生成schema的函数
            param_descriptions: 参数描述的字典，如 {"code": "要执行的代码..."}
        """
        sig = inspect.signature(func)

        properties = {}
        required = []

        for name, param in sig.parameters.items():
            # 参数类型映射
            param_type = "string"  # 默认
            if param.annotation in (int, float):
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == list:
                param_type = "array"
            elif param.annotation == dict:
                param_type = "object"

            # ✨ 关键：使用传入的参数描述，如果没有就生成默认的
            if param_descriptions and name in param_descriptions:
                description = param_descriptions[name]
            else:
                # 尝试从函数文档解析（这里可以更智能）
                description = f"Parameter: {name}"

            properties[name] = {
                "type": param_type,
                "description": description
            }

            # 检查是否有默认值
            if param.default == inspect.Parameter.empty:
                required.append(name)

        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": func.__doc__ or f"Execute {func.__name__}",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def get_all_schemas(self) -> List[Dict]:
        """获取所有工具的OpenAI schema格式"""
        return list(self._tool_schemas.values())

    def execute(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        func = self._tools[tool_name]
        return func(**kwargs)

    def auto_discover(self, tools_dir: str = "tools"):
        """自动发现并加载工具模块"""
        tools_path = Path(tools_dir)
        if not tools_path.exists():
            return

        for file in tools_path.glob("*_tool.py"):
            module_name = file.stem
            try:
                # 动态导入模块
                spec = importlib.util.spec_from_file_location(module_name, file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                print(f"✅ Auto-discovered: {module_name}")
            except Exception as e:
                print(f"❌ Failed to load {module_name}: {e}")

    def list_tools(self) -> List[str]:
        """列出所有已注册工具"""
        return list(self._tools.keys())


# 创建全局单例
tool_registry = ToolRegistry()


# 便捷装饰器
def tool(name=None, schema=None, **metadata):
    return tool_registry.register(name, schema, **metadata)