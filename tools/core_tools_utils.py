


from typing import Optional, Dict, Any


def verify_task_completion(result_summary: str, meets_requirements: bool, missing_elements: list) -> Dict[str, Any]:
    """验证任务是否完成"""
    return {
        "result_summary": result_summary,
        "meets_requirements": meets_requirements,
        "missing_elements": missing_elements,
        "can_finalize": meets_requirements and len(missing_elements) == 0
    }


def finalize_session(final_result: str, completion_message: str) -> Dict[str, Any]:
    """结束会话"""
    return {
        "final_result": final_result,
        "completion_message": completion_message,
        "session_ended": True
    }