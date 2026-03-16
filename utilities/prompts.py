# prompts/system_prompts.py
class SystemPrompts:
    """系统提示词管理"""

    @staticmethod
    def get_base_prompt(working_dir: str) -> str:
        """基础系统提示"""
        return f"""You are an intelligent assistant that helps users complete tasks.
Important guidelines:
1. You have access to tools for executing Python code and verifying results.
2. Always check if a tool is needed before assuming the task is complete.
3. After getting results, VERIFY if they meet the user's requirements.
4. Only finalize when verification confirms completion.
5. Working directory: {working_dir}

Task completion process:
- Use execute_python_code for any computation or file operations
- After getting results, call verify_task_completion to check if done
- If verification shows incomplete, continue working
- Only call finalize_session when verification confirms task is complete"""


class UserPrompts:
    """用户提示词管理"""

    @staticmethod
    def get_task_reminder(task: str, iteration: int) -> str:
        """任务提醒提示词"""
        return f"""【任务提醒】这里是用户需求的复述。请确保在执行任务过程中，以及验证任务结果的时候，始终与用户需求进行比对：
{task}"""

    @staticmethod
    def get_verification_prompt(task: str) -> str:
        """验证提示词"""
        return f"""请验证任务是否完成。

【原始任务】
{task}

请仔细对照原始任务，确认是否满足所有要求。如果已完成，请调用 verify_task_completion 工具并设置 meets_requirements=True；如果还有遗漏，请继续处理。"""

    @staticmethod
    def get_verification_reminder(task: str, missing_elements: list) -> str:
        """验证不通过时的提醒"""
        missing = "\n".join([f"- {item}" for item in missing_elements])
        return f"""验证结果显示任务尚未完成。

【原始任务】
{task}

【缺失要素】
{missing}

请继续处理缺失的部分。"""


class ToolPrompts:
    """工具相关提示词"""

    @staticmethod
    def get_search_purpose(query: str) -> str:
        """搜索目的说明"""
        return f"搜索相关信息: {query}"

    @staticmethod
    def get_code_purpose(description: str) -> str:
        """代码执行目的说明"""
        return f"执行代码: {description}"