"""
多智能体系统常量定义
"""

# Agent 信息映射表
AGENT_INFO = {
    "conversation": {
        "name": "对话助手",
        "description": "处理日常对话和闲聊"
    },
    "document": {
        "name": "文档助手",
        "description": "生成和处理学习文档"
    },
    "question": {
        "name": "题库助手",
        "description": "题目检索与练习"
    },
    "multimedia": {
        "name": "多媒体助手",
        "description": "图片和视频生成"
    },
    "learning_path": {
        "name": "学习路径助手",
        "description": "制定学习计划"
    },
    "qa": {
        "name": "问答助手",
        "description": "知识问答"
    },
    "evaluation": {
        "name": "评估助手",
        "description": "学习成果评估"
    },
    "orchestrator": {
        "name": "总调度器",
        "description": "协调各子智能体工作"
    },
    "router": {
        "name": "路由助手",
        "description": "路由请求到合适的子智能体"
    },
    "default": {
        "name": "智能助手",
        "description": "处理各类请求"
    }
}


def get_agent_info(agent_id: str) -> dict:
    """
    获取 Agent 信息
    
    Args:
        agent_id: Agent ID
        
    Returns:
        Agent 信息字典，包含 name 和 description
    """
    return AGENT_INFO.get(agent_id, AGENT_INFO.get("default"))


def get_agent_name(agent_id: str) -> str:
    """获取 Agent 名称"""
    return get_agent_info(agent_id).get("name", agent_id)


def get_agent_desc(agent_id: str) -> str:
    """获取 Agent 描述"""
    return get_agent_info(agent_id).get("description", "")


# ============================================
# 错误码定义
# ============================================

class ErrorCode:
    """错误码定义"""
    SUCCESS = 0
    UNKNOWN_ERROR = 1000
    TOOL_EXECUTION_ERROR = 1001
    LLM_ERROR = 1002
    TIMEOUT_ERROR = 1003
    INVALID_INPUT = 1004
    AGENT_NOT_FOUND = 1005
    CONTEXT_OVERFLOW = 1006
    PERMISSION_DENIED = 1007
    SERVICE_UNAVAILABLE = 1008


# ============================================
# 异常类定义
# ============================================

class AgentError(Exception):
    """Agent 基类异常"""
    def __init__(self, message: str, code: int = ErrorCode.UNKNOWN_ERROR):
        self.message = message
        self.code = code
        super().__init__(self.message)


class LLMError(AgentError):
    """LLM 调用异常"""
    def __init__(self, message: str = "LLM 调用失败"):
        super().__init__(message, ErrorCode.LLM_ERROR)


class APIError(AgentError):
    """API 调用异常"""
    def __init__(self, message: str = "API 调用失败"):
        super().__init__(message, ErrorCode.LLM_ERROR)


class RateLimitError(AgentError):
    """速率限制异常"""
    def __init__(self, message: str = "请求频率超限"):
        super().__init__(message, ErrorCode.LLM_ERROR)


class ToolExecutionError(AgentError):
    """工具执行异常"""
    def __init__(self, message: str = "工具执行失败"):
        super().__init__(message, ErrorCode.TOOL_EXECUTION_ERROR)


class TimeoutError(AgentError):
    """超时异常"""
    def __init__(self, message: str = "操作超时"):
        super().__init__(message, ErrorCode.TIMEOUT_ERROR)


class InvalidInputError(AgentError):
    """输入验证异常"""
    def __init__(self, message: str = "输入无效"):
        super().__init__(message, ErrorCode.INVALID_INPUT)


# ============================================
# 统一错误响应定义
# ============================================

class ErrorResponse:
    """统一错误响应模板"""
    
    # 基础错误消息
    MESSAGES = {
        ErrorCode.UNKNOWN_ERROR: "抱歉，系统遇到了一些问题。请稍后重试，或换个方式提问。",
        ErrorCode.TOOL_EXECUTION_ERROR: "抱歉，功能执行遇到问题：{detail}。请稍后重试或换个方式提问。",
        ErrorCode.LLM_ERROR: "抱歉，AI 服务暂时不可用。请稍后重试。",
        ErrorCode.TIMEOUT_ERROR: "处理超时，请尝试简化问题或减少请求内容。",
        ErrorCode.INVALID_INPUT: "输入无效：{detail}。请检查后重新输入。",
        ErrorCode.AGENT_NOT_FOUND: "未找到对应的处理模块。请尝试换个方式描述您的问题。",
        ErrorCode.CONTEXT_OVERFLOW: "对话内容过长，请开启新话题或清理上下文。",
        ErrorCode.PERMISSION_DENIED: "权限不足，无法完成此操作。",
        ErrorCode.SERVICE_UNAVAILABLE: "服务暂时不可用，请稍后重试。",
    }
    
    # 用户友好提示（替代技术错误）
    USER_FRIENDLY = {
        ErrorCode.TOOL_EXECUTION_ERROR: "这个功能暂时有点小问题，我已经记录下来了。请换个方式提问或稍后再试。",
        ErrorCode.LLM_ERROR: "AI 助手需要休息一下，请稍后再来找它。",
        ErrorCode.TIMEOUT_ERROR: "问题有点复杂，我需要更多时间来思考。请把问题简化一些。",
        ErrorCode.CONTEXT_OVERFLOW: "我们的对话已经很长了，不如开启一个新话题？",
    }
    
    @classmethod
    def get_message(cls, error_code: int, detail: str = None, user_friendly: bool = True) -> str:
        """
        获取错误消息
        
        Args:
            error_code: 错误码
            detail: 详细错误信息（可选）
            user_friendly: 是否返回用户友好提示（默认 True）
            
        Returns:
            错误消息字符串
        """
        # 优先使用用户友好提示
        if user_friendly and error_code in cls.USER_FRIENDLY:
            message = cls.USER_FRIENDLY[error_code]
        elif error_code in cls.MESSAGES:
            message = cls.MESSAGES[error_code]
        else:
            message = cls.MESSAGES[ErrorCode.UNKNOWN_ERROR]
        
        # 填充占位符
        if detail and "{detail}" in message:
            message = message.format(detail=detail)
        
        return message
    
    @classmethod
    def format_error_response(cls, error_code: int, detail: str = None, include_detail: bool = False) -> dict:
        """
        格式化错误响应
        
        Args:
            error_code: 错误码
            detail: 详细错误信息
            include_detail: 是否在响应中包含详细信息（仅开发环境使用）
            
        Returns:
            标准错误响应字典
        """
        response = {
            "success": False,
            "error": {
                "code": error_code,
                "message": cls.get_message(error_code, detail)
            }
        }
        
        # 仅在需要时添加详细信息（生产环境应该关闭）
        if include_detail and detail:
            response["error"]["detail"] = detail
        
        return response
