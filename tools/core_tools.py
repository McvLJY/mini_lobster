import sys
from io import StringIO
from typing import Dict, Any, List
from tools import baidu_search_tool_multi
from tools import image_analyzer_vllm

# 导入注册器
from core.tool_registry import tool, tool_registry

# ==== 自动发现要在定义核心工具之前！====
print("🔄 开始自动发现其他工具...")
tool_registry.auto_discover()  # 先发现其他工具
print("✅ 自动发现完成")


# ========== 工具1: Python代码执行器 ==========
@tool(
    name="execute_python_code",
    param_descriptions={  # 👈 新增的参数！
        "code": "Python code to execute. Must include print() for output.",
        "purpose": "Brief description of what this code accomplishes"
    },
    category="system",
    version="1.0.0"
)
# 工具实现
def execute_python_code(code: str, purpose: str) -> Dict[str, Any]:
    """
    Execute Python code and return the result. Use this for calculations, data processing, or file operations, etc.
    Always include print() statements to output the results you want to see.
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


# ========== 工具2: 任务完成验证 ==========
@tool(
    name="verify_task_completion",
    param_descriptions={
        "result_summary": "Summary of what was accomplished",
        "meets_requirements": "Whether the result meets all user requirements",
        "missing_elements": "Any elements that are still missing or need improvement"
    },
    category="system",
    version="1.0.0"
)
def verify_task_completion(
        result_summary: str,
        meets_requirements: bool,
        missing_elements: List[str]  # 更明确的类型注解
) -> Dict[str, Any]:
    """
    Verify if the task has been completed satisfactorily. Call this when you believe the task is done.
    """
    return {
        "success": True,
        "result_summary": result_summary,
        "meets_requirements": meets_requirements,
        "missing_elements": missing_elements,
        "can_finalize": meets_requirements and len(missing_elements) == 0,
        "verified": meets_requirements
    }


# ========== 工具3: 结束会话 ==========
@tool(
    name="finalize_session",
    param_descriptions={
        "final_result": "The complete final result to present to the user",
        "completion_message": "A friendly message indicating task completion"
    },
    category="system",
    version="1.0.0"
)
def finalize_session(
        final_result: str,
        completion_message: str
) -> Dict[str, Any]:
    """
    Call this ONLY after verification confirms the task is complete and user requirements are met.
    This will present the final result and end the conversation.
    """
    return {
        "success": True,
        "final_result": final_result,
        "completion_message": completion_message,
        "session_ended": True
    }


# ========== 导出给主程序使用的tools列表 ==========
from core.tool_registry import tool_registry

# 然后获取 schema
tools = tool_registry.get_all_schemas()

# ========== 测试代码 ==========
if __name__ == "__main__":
    import json

    print("=" * 60)
    print("验证工具注册和schema生成")
    print("=" * 60)

    # 1. 查看所有已注册的工具
    print("\n📋 已注册的工具列表：")
    for tool_name in tool_registry.list_tools():
        print(f"  - {tool_name}")

    # 2. 查看每个工具的schema
    for tool_name in ["execute_python_code", "verify_task_completion", "finalize_session"]:
        print(f"\n🔧 {tool_name} 的 schema：")
        schema = tool_registry._tool_schemas.get(tool_name)
        if schema:
            print(json.dumps(schema, ensure_ascii=False, indent=2))
        else:
            print(f"❌ 没找到 {tool_name}")

    # 3. 测试工具执行
    print("\n🧪 测试工具执行：")

    # 测试 verify_task_completion
    result = tool_registry.execute(
        "verify_task_completion",
        result_summary="完成了任务A和B",
        meets_requirements=True,
        missing_elements=[]
    )
    print(f"\nverify_task_completion 结果: {result}")

    # 测试 finalize_session
    result = tool_registry.execute(
        "finalize_session",
        final_result="这是最终结果",
        completion_message="任务完成！"
    )
    print(f"finalize_session 结果: {result}")

# 在 tools/core_tools.py 最后加上
if __name__ == "__main__":
    print("已注册的工具:", tool_registry.list_tools())