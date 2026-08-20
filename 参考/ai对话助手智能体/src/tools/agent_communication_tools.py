"""
Agent 通信与状态管理工具
提供 MessageBus 和 SharedContext 的可视化接口
"""
import json
import logging
from typing import Any, Dict, List, Optional
from langchain.tools import tool

from multi_agent.agent_factory import get_agent_factory
from storage.database import get_session
from sqlalchemy import text

logger = logging.getLogger(__name__)


# ============== SharedContext 工具 ==============

@tool
def get_shared_context_status() -> str:
    """
    获取共享上下文的当前状态
    
    Returns:
        共享上下文的统计信息
    """
    try:
        factory = get_agent_factory()
        context = factory.get_shared_context()
        
        status = {
            "user_profiles_count": len(context.get_all_user_ids()),
            "user_ids": context.get_all_user_ids(),
            "features": ["user_profiles", "learning_progress", "task_states", "cache", "session_data"]
        }
        
        return json.dumps(status, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[SharedContext] Failed to get status: {e}")
        return f"获取共享上下文状态失败: {str(e)}"


@tool
def get_user_context(user_id: str) -> str:
    """
    获取指定用户的共享上下文数据（从数据库读取最新数据）
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户的学习上下文数据
    """
    try:
        # 从数据库读取最新数据
        with get_session() as db:
            result = db.execute(
                text("SELECT * FROM user_profiles WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            
            if row:
                profile_data = dict(row._mapping)
            else:
                profile_data = None
        
        # 将 datetime 对象转换为字符串
        def convert_datetime(obj):
            if isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            elif hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return obj
        
        # 如果数据库有数据，同步到 SharedContext（转换后）
        if profile_data:
            # 先转换 datetime 对象
            converted_profile = convert_datetime(profile_data)
            factory = get_agent_factory()
            context = factory.get_shared_context()
            context.set_user_profile(user_id, converted_profile)
            
            # 如果有 learning_progress，也同步
            if 'learning_progress' in profile_data and profile_data['learning_progress']:
                progress_data = profile_data.get('learning_progress')
                if isinstance(progress_data, str):
                    try:
                        progress_data = json.loads(progress_data)
                    except:
                        progress_data = None
                if progress_data:
                    context.set_learning_progress(user_id, progress_data)
        
        # 构建结果
        progress_data = None
        if profile_data and 'learning_progress' in profile_data:
            progress_data = profile_data.get('learning_progress')
            if isinstance(progress_data, str):
                try:
                    progress_data = json.loads(progress_data)
                except:
                    progress_data = None
        
        # 转换 datetime 对象
        converted_profile = convert_datetime(profile_data) if profile_data else None
        converted_progress = convert_datetime(progress_data) if progress_data else None
        
        result = {
            "user_id": user_id,
            "profile": converted_profile,
            "learning_progress": converted_progress,
            "source": "database"
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[SharedContext] Failed to get user context: {e}")
        return f"获取用户上下文失败: {str(e)}"


@tool
def update_user_context(user_id: str, feature_type: str, feature_value: str) -> str:
    """
    更新用户的共享上下文数据
    
    Args:
        user_id: 用户ID
        feature_type: 特征类型 (如 learning_goal, knowledge_level, learning_speed)
        feature_value: 特征值 (JSON格式字符串)
        
    Returns:
        更新结果
    """
    try:
        factory = get_agent_factory()
        context = factory.get_shared_context()
        
        # 解析特征值
        try:
            value = json.loads(feature_value)
        except json.JSONDecodeError:
            value = feature_value
        
        # 更新用户画像
        context.update_user_profile(user_id, {feature_type: value})
        
        return json.dumps({"success": True, "message": f"已更新 {feature_type}"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[SharedContext] Failed to update user context: {e}")
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


# ============== MessageBus 工具 ==============

@tool
def get_message_bus_status() -> str:
    """
    获取消息总线的当前状态
    
    Returns:
        消息总线的统计信息
    """
    try:
        factory = get_agent_factory()
        bus = factory.get_message_bus()
        
        # 获取统计信息
        stats = bus.get_stats()
        subscribers = bus.get_all_subscribers()
        
        result = {
            "statistics": stats,
            "subscribed_agents": subscribers,
            "features": ["点对点消息", "广播消息", "消息订阅", "回调机制"]
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[MessageBus] Failed to get status: {e}")
        return f"获取消息总线状态失败: {str(e)}"


@tool
def get_agent_collaboration_status() -> str:
    """
    获取 Agent 协作状态
    
    Returns:
        各 Agent 的协作关系和状态
    """
    try:
        factory = get_agent_factory()
        
        # 获取所有 Agent 元数据
        agents_info = factory.get_all_agents_info()
        
        # 构建协作关系图
        collaboration = {
            "federated_agents": [],  # 独立执行
            "collaborative_agents": [],  # 协作执行
            "dependencies": {}
        }
        
        for agent in agents_info:
            agent_id = agent.get("id", "")
            mode = agent.get("processing_mode", "federated")
            deps = agent.get("dependencies", [])
            
            if mode == "federated":
                collaboration["federated_agents"].append(agent_id)
            else:
                collaboration["collaborative_agents"].append(agent_id)
            
            if deps:
                collaboration["dependencies"][agent_id] = deps
        
        # 添加协作链说明
        collaboration["collaboration_chains"] = [
            {
                "name": "学习路径协作链",
                "description": "对话采集 → 学习路径规划",
                "agents": ["conversation", "learning_path"],
                "mode": "chain"
            },
            {
                "name": "评估协作链",
                "description": "对话采集 → 题库生成 → 学习评估 → 推荐",
                "agents": ["conversation", "question", "evaluation", "recommendation"],
                "mode": "chain"
            }
        ]
        
        return json.dumps(collaboration, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[AgentSystem] Failed to get collaboration status: {e}")
        return f"获取协作状态失败: {str(e)}"


@tool
def get_system_architecture() -> str:
    """
    获取多智能体系统架构信息
    
    Returns:
        系统架构说明
    """
    try:
        factory = get_agent_factory()
        context = factory.get_shared_context()
        bus = factory.get_message_bus()
        
        architecture = {
            "system_name": "层级-协作混合模式多智能体学习系统",
            "components": {
                "AgentFactory": {
                    "description": "Agent 实例化管理器",
                    "status": "运行中"
                },
                "MessageBus": {
                    "description": "Agent 间消息传递总线",
                    "status": "运行中",
                    "statistics": bus.get_stats()
                },
                "SharedContext": {
                    "description": "跨 Agent 数据共享",
                    "status": "运行中",
                    "user_count": len(context.get_all_user_ids())
                }
            },
            "agents": [
                {
                    "id": "conversation",
                    "name": "对话学习Agent",
                    "mode": "federated",
                    "description": "采集对话，抽取学习特征"
                },
                {
                    "id": "document",
                    "name": "文档生成Agent",
                    "mode": "federated",
                    "description": "生成知识文档、思维导图"
                },
                {
                    "id": "question",
                    "name": "题库练习Agent",
                    "mode": "federated",
                    "description": "生成各类练习题"
                },
                {
                    "id": "learning_path",
                    "name": "学习路径Agent",
                    "mode": "collaborative",
                    "dependencies": ["conversation"],
                    "description": "制定学习计划"
                },
                {
                    "id": "evaluation",
                    "name": "学习评估Agent",
                    "mode": "collaborative",
                    "dependencies": ["conversation", "question"],
                    "description": "评估学习成果"
                },
                {
                    "id": "qa",
                    "name": "答疑解惑Agent",
                    "mode": "federated",
                    "description": "解答学习疑问"
                },
                {
                    "id": "multimedia",
                    "name": "多媒体生成Agent",
                    "mode": "federated",
                    "description": "生成图片、视频等素材"
                },
                {
                    "id": "email",
                    "name": "邮件发送Agent",
                    "mode": "federated",
                    "description": "发送学习内容到邮箱"
                },
                {
                    "id": "wechat",
                    "name": "微信公众号Agent",
                    "mode": "federated",
                    "description": "微信公众号内容推送"
                }
            ],
            "processing_modes": {
                "federated": "联邦模式 - Agent 独立处理任务，不依赖其他 Agent 结果",
                "collaborative": "协作模式 - Agent 需要等待依赖的 Agent 完成后再执行"
            }
        }
        
        return json.dumps(architecture, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[AgentSystem] Failed to get architecture: {e}")
        return f"获取系统架构失败: {str(e)}"


# ============== 工具列表 ==============
AGENT_COMMUNICATION_TOOLS = [
    get_shared_context_status,
    get_user_context,
    update_user_context,
    get_message_bus_status,
    get_agent_collaboration_status,
    get_system_architecture
]
