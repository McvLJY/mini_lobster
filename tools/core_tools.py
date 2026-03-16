import sys
from io import StringIO
from typing import Dict, Any
from tools.baidu_search_tool_multi import baidu_search_tool
from tools.image_analyzer_vllm import image_analysis_tool

# # 导入注册器
# from core.tool_registry import tool


# 改进后的工具定义
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_python_code",
            "description": """
Execute Python code and return the result. Use this for calculations, data processing, or file operations.
Always include print() statements to output the results you want to see.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute. Must include print() for output."
                    },
                    "purpose": {
                        "type": "string",
                        "description": "Brief description of what this code accomplishes"
                    }
                },
                "required": ["code", "purpose"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "verify_task_completion",
            "description": """
Verify if the task has been completed satisfactorily. Call this when you believe the task is done.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "result_summary": {
                        "type": "string",
                        "description": "Summary of what was accomplished"
                    },
                    "meets_requirements": {
                        "type": "boolean",
                        "description": "Whether the result meets all user requirements"
                    },
                    "missing_elements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Any elements that are still missing or need improvement"
                    }
                },
                "required": ["result_summary", "meets_requirements", "missing_elements"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finalize_session",
            "description": """
Call this ONLY after verification confirms the task is complete and user requirements are met.
This will present the final result and end the conversation.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "final_result": {
                        "type": "string",
                        "description": "The complete final result to present to the user"
                    },
                    "completion_message": {
                        "type": "string",
                        "description": "A friendly message indicating task completion"
                    }
                },
                "required": ["final_result", "completion_message"]
            }
        }
    }
]

tools.append(baidu_search_tool)
tools.append(image_analysis_tool)

# ========== 工具1: Python代码执行器 ==========
# @tool(
#     name="execute_python_code",
#     category="system",
#     version="1.0.0"
# )
# 工具实现
def execute_python_code(code: str, purpose: str) -> Dict[str, Any]:
    """
    安全执行Python代码并返回结果

    参数:
        code: 要执行的Python代码，必须包含print()语句输出结果
        purpose: 代码目的的简要说明

    返回:
        包含执行结果的字典
    """
    result = {
        "success": False,
        "output": "",
        "error": None,
        "purpose": purpose
    }

    try:
        # 捕获输出
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        # 执行代码
        exec_globals = {}
        exec(code, exec_globals)

        # 获取输出
        output = sys.stdout.getvalue()
        result["output"] = output if output else "Code executed successfully (no output)"
        result["success"] = True

    except Exception as e:
        result["error"] = str(e)
        result["output"] = f"Error executing code: {str(e)}"

    finally:
        # 恢复标准输出
        sys.stdout = old_stdout

    return result






