
import logging
import os
import json
import textwrap


class PrettyLogFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        # 美化代码
        msg = msg.replace('\\n', '\n').replace('\\t', '    ')
        return msg


class AgentLogger:
    def __init__(self, base_wkd: str):
        self.logger = logging.getLogger('IntelligentAgent')
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        if not os.path.exists(base_wkd):
            os.makedirs(base_wkd)

        # 文件处理器
        file_handler = logging.FileHandler(
            os.path.join(base_wkd, 'agent.log'),
            mode='w', encoding='utf-8'
        )
        file_handler.setFormatter(PrettyLogFormatter(
            '%(asctime)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(PrettyLogFormatter(
            '%(asctime)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)

    def task_start(self, task: str):
        self.logger.info(f"\n{'★' * 60}\n📋 TASK: {task}\n{'★' * 60}\n")

    def task_complete(self):
        self.logger.info(f"\n{'✓' * 60}\n✅ TASK COMPLETE\n{'✓' * 60}\n")

    def iteration(self, i: int):
        self.logger.info(f"🔄 Iteration {i + 1}")

    def tool_call(self, func_name: str, args: dict):
        msg = f"\n{'=' * 60}\n🔧 TOOL CALL: {func_name}"
        if 'purpose' in args:
            msg += f"\n📋 PURPOSE: {args['purpose']}"
        if 'code' in args:
            msg += f"\n📝 CODE:\n{args['code']}"
        msg += f"\n{'=' * 60}\n"
        self.logger.info(msg)

    def tool_response(self, response: dict):
        status = "SUCCESS" if response.get('success') else "FAILED"
        output = response.get('output', '')
        msg = f"\n{'-' * 40}\n✅ TOOL RESPONSE:\n   Status: {status}"
        if output:
            msg += f"\n   Output:\n{textwrap.indent(output, '      ')}"
        msg += f"\n{'-' * 40}\n"
        self.logger.info(msg)

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str):
        self.logger.error(f"❌ ERROR: {msg}")