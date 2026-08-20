"""
学习辅助智能体工具集
"""
from tools.email_tools import (
    send_text_email,
    send_html_email,
    send_email_with_image,
    send_learning_plan_email,
    test_email_connection,
)
__all__ = [
    "send_text_email",
    "send_html_email", 
    "send_email_with_image",
    "send_learning_plan_email",
    "test_email_connection",
]
