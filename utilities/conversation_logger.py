# utils/conversation_logger.py
import json
from datetime import datetime


class ConversationLogger:
    """对话历史日志记录器"""

    def __init__(self, log_path: str):
        self.log_path = log_path

    def write(self, iteration: int, messages: list):
        """写入对话历史"""
        try:
            with open(self.log_path, 'w', encoding='utf-8') as f:
                self._write_header(f, iteration)
                self._write_messages(f, messages)
                self._write_footer(f)
        except Exception as e:
            print(f"Failed to write conversation log: {e}")

    def _write_header(self, f, iteration: int):
        """写入头部"""
        f.write(f"=== Conversation Updated at {datetime.now()} ===\n")
        f.write(f"=== Current Iteration: {iteration + 1} ===\n\n")

    def _write_footer(self, f):
        """写入尾部"""
        f.write(f"\n{'=' * 80}\n")

    def _write_messages(self, f, messages: list):
        """写入所有消息"""
        for i, msg in enumerate(messages):
            self._write_message(f, i, msg)

    def _write_message(self, f, index: int, msg):
        """写入单条消息"""
        f.write(f"[{index}] ")

        if hasattr(msg, 'role'):  # ChatCompletionMessage对象
            self._write_chat_message(f, msg)
        else:  # 字典
            self._write_dict_message(f, msg)

        f.write("-" * 40 + "\n")

    def _write_chat_message(self, f, msg):
        """写入ChatCompletionMessage对象"""
        f.write(f"role: {msg.role}\n")
        if msg.content:
            f.write(f"content: {msg.content}\n")
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            tool_calls_data = self._format_tool_calls(msg.tool_calls)
            f.write(f"tool_calls: {json.dumps(tool_calls_data, indent=2, ensure_ascii=False)}\n")

    def _write_dict_message(self, f, msg):
        """写入字典消息"""
        f.write(f"role: {msg.get('role', 'unknown')}\n")
        if msg.get('content'):
            f.write(f"content: {msg['content']}\n")
        if msg.get('tool_calls'):
            f.write(f"tool_calls: {json.dumps(msg['tool_calls'], indent=2, ensure_ascii=False)}\n")
        if msg.get('tool_call_id'):
            f.write(f"tool_call_id: {msg['tool_call_id']}\n")

    def _format_tool_calls(self, tool_calls):
        """格式化工具调用"""
        formatted = []
        for tc in tool_calls:
            formatted.append({
                'id': tc.id,
                'type': tc.type,
                'function': {
                    'name': tc.function.name,
                    'arguments': tc.function.arguments
                }
            })
        return formatted