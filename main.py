import json
from openai import OpenAI
import logging
from enum import Enum
from typing import Optional, Dict, Any

from tasks.tasks import *
from utilities.logger_setup import AgentLogger
from utilities.conversation_logger import ConversationLogger
from utilities.prompts import *
from utilities.misc import *
from utilities.PARAMS import base_wkd
from models.model_client import ModelClient
from models.model_config import ModelProvider

from tools.core_tools import tools
from core.tool_registry import tool_registry
# from tools.core_tools import tools, execute_python_code
# from tools.baidu_search_tool_multi import execute_baidu_search
# from tools.image_analyzer_vllm import execute_image_analysis
# from tools.core_tools_utils import *

# 测试任务
tasks = task_ds_09


# 定义任务状态枚举
class TaskStatus(Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    TOOL_CALLING = "tool_calling"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


class IntelligentAgent:
    def __init__(self, base_wkd: str, provider: ModelProvider = None):
        self.model_client = ModelClient(provider)
        self.model = self.model_client.model_name
        self.base_wkd = base_wkd
        self.messages = []
        self.task_status = TaskStatus.INITIATED
        self.max_iterations = 30
        self.tool_call_count = 0
        self.task_description = ""

        # 初始化logger
        self.log = AgentLogger(base_wkd)

        self.conv_logger = ConversationLogger(
            os.path.join(base_wkd, 'conversation_history.log')
        )

    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger('IntelligentAgent')
        self.logger.setLevel(logging.DEBUG)

        if not os.path.exists(self.base_wkd):
            os.makedirs(self.base_wkd)

        file_handler = logging.FileHandler(
            os.path.join(self.base_wkd, 'agent.log'),
            mode='w'
        )
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(status)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def log(self, message: str, status: Optional[str] = None):
        """记录日志"""
        if status is None:
            status = self.task_status.value
        extra = {'status': status}
        self.logger.info(message, extra=extra)

    def process_task(self, task: str) -> str:
        """处理用户任务的主流程"""
        self.task_description = task
        self.task_status = TaskStatus.INITIATED
        self.messages = [
            {"role": "system", "content": SystemPrompts.get_base_prompt(self.base_wkd)},
            {"role": "user", "content": task}
        ]

        self.task_status = TaskStatus.IN_PROGRESS
        self.log.task_start(task)  # 任务开始

        for iteration in range(self.max_iterations):
            self.log.iteration(iteration)  # 迭代记录
            if iteration > 0:
                self.messages.append({
                    "role": "user",
                    "content": UserPrompts.get_task_reminder(task, iteration)
                })

            # 写入详细对话日志
            self.conv_logger.write(iteration, self.messages)

            try:
                response = self.model_client.chat_completion(
                    messages=self.messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.2
                )

                assistant_message = response.choices[0].message
                self.messages.append(assistant_message)
                self.conv_logger.write(iteration, self.messages)

                # 记录AI的完整回答（包括思考内容和工具调用信息）
                self._log_assistant_message(assistant_message, iteration)

                # 检查是否调用工具
                if assistant_message.tool_calls:
                    self.task_status = TaskStatus.TOOL_CALLING
                    self.log.info(f"Tool calls detected: {len(assistant_message.tool_calls)}")

                    # 处理所有工具调用
                    all_tool_responses = []
                    for tool_call in assistant_message.tool_calls:
                        tool_response = self.handle_tool_call(tool_call)
                        all_tool_responses.append(tool_response)

                        # 如果遇到finalize_session，直接返回结果
                        if tool_call.function.name == "finalize_session":
                            self.task_status = TaskStatus.COMPLETED
                            final_result = json.loads(tool_call.function.arguments)
                            completion_msg = f"{final_result['completion_message']}\n\nFinal Result:\n{final_result['final_result']}"

                            # 尝试多种方式获取摘要
                            summary = (
                                    final_result.get('result_summary') or  # 1. 专门的summary字段
                                    final_result.get('completion_message', '')[:50] or  # 2. 从completion_message截取
                                    "Task completed successfully"  # 3. 默认
                            )

                            self.log.info(f"Task completed: {summary}")
                            return completion_msg

                    # 将工具响应添加到消息历史
                    for tool_response in all_tool_responses:
                        self.messages.append(tool_response)

                else:
                    # 没有工具调用，检查是否应该验证
                    if self.should_verify_completion():
                        self.task_status = TaskStatus.VERIFYING
                        self.log.info("No tool calls, initiating verification")

                        # 在这里添加原始任务提醒
                        self.messages.append({
                            "role": "user",
                            "content": UserPrompts.get_verification_prompt(task)
                        })
                    else:
                        # 可能是直接回答，继续对话
                        self.log.info("No tool calls, continuing conversation")

            except Exception as e:
                self.log.error(f"Error in iteration {iteration}: {str(e)}")  # 使用error方法
                self.task_status = TaskStatus.FAILED
                return f"Task failed with error: {str(e)}"

        # 达到最大迭代次数
        self.task_status = TaskStatus.FAILED
        return "Task did not complete within maximum iterations"


    def handle_tool_call(self, tool_call):
        """处理单个工具调用 - 新版，无需if-else"""
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        # 使用logger记录工具调用
        self.log.tool_call(func_name, args)

        try:
            result = tool_registry.execute(func_name, **args)

            # 统一处理响应
            response_content = json.dumps(result, ensure_ascii=False)
            self.log.tool_response(result)

        except Exception as e:
            # 统一错误处理
            error_result = {
                "success": False,
                "error": str(e),
                "output": f"Tool execution failed: {str(e)}"
            }
            response_content = json.dumps(error_result, ensure_ascii=False)
            self.log.error(f"Tool {func_name} failed: {e}")

        return {
            "role": "tool",
            "content": response_content,
            "tool_call_id": tool_call.id,
            "name": func_name
        }

    def should_verify_completion(self) -> bool:
        # 检查最近的消息是否包含结果
        recent_messages = self.messages[-3:] if len(self.messages) > 3 else self.messages

        has_tool_response = any(
            msg.get("role") == "tool"
            for msg in recent_messages
        )

        has_verification = any(
            msg.get("role") == "tool" and
            json.loads(msg.get("content", "{}")).get("name") == "verify_task_completion"
            for msg in recent_messages
        )

        # 如果有工具响应但没有验证，应该验证
        return has_tool_response and not has_verification

    def _log_assistant_message(self, message, iteration: int):
        """记录AI的完整回答"""
        try:
            log_entry = f"\n{'='*60}\n"
            log_entry += f"AI RESPONSE - Iteration {iteration + 1}\n"
            log_entry += f"{'='*60}\n"

            # 记录思考内容
            if message.content:
                log_entry += f"\n💭 THOUGHT:\n{message.content}\n"

            # 记录工具调用
            if hasattr(message, 'tool_calls') and message.tool_calls:
                log_entry += f"\n🔧 TOOL CALLS:\n"
                for i, tc in enumerate(message.tool_calls, 1):
                    log_entry += f"\n  Tool {i}: {tc.function.name}\n"
                    log_entry += f"  Arguments: {tc.function.arguments}\n"

            log_entry += f"\n{'='*60}\n"

            # 写入专门的AI回答日志文件
            ai_log_path = os.path.join(self.base_wkd, 'ai_responses.log')
            with open(ai_log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)

        except Exception as e:
            self.log.error(f"Failed to log AI response: {e}")


# 使用示例
def main(base_wkd):
    task = tasks['task_name']
    base_wkd_ = os.path.join(base_wkd, tasks['task_dir'])

    # 创建agent实例
    agent = IntelligentAgent(base_wkd_)
    ensure_folder(base_wkd_)

    print(f"\n{'=' * 60}")
    print(f"Task: {task}")
    print('=' * 60)

    result = agent.process_task(task)
    print(f"\nFinal Result:\n{result}")


if __name__ == "__main__":
    main(base_wkd)