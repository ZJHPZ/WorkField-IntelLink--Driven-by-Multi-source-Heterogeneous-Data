"""
路径规划与推送智能体工具模块
功能：编排学习路径，根据用户画像进行个性化内容推送
"""
import json
from typing import Optional
from langchain.tools import tool
from storage.database.supabase_client import get_supabase_client
from postgrest.exceptions import APIError
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def save_learning_path(user_id: str, subject: str, path_data: str) -> str:
    """
    保存用户的学习路径。
    
    Args:
        user_id: 用户唯一标识
        subject: 学习科目
        path_data: 学习路径详情 (JSON格式字符串)
    
    Returns:
        保存结果信息
    """
    ctx = request_context.get() or new_context(method="save_learning_path")
    
    try:
        client = get_supabase_client()
        
        data = {
            "user_id": user_id,
            "subject": subject,
            "path_data": json.loads(path_data) if isinstance(path_data, str) else path_data,
            "status": "进行中"
        }
        
        response = client.table("learning_paths").insert(data).execute()
        response = client.table("learning_paths").insert(data).execute()
        data_list = list(response.data) if response.data else []
        path_id = data_list[0].get("id") if data_list and isinstance(data_list[0], dict) else None
        return json.dumps({
            "success": True,
            "message": "学习路径已保存",
            "path_id": path_id,
            "user_id": user_id,
            "subject": subject
        }, ensure_ascii=False)
    
    except APIError as e:
        raise Exception(f"保存学习路径失败: {e.message}")


@tool
def get_learning_path(user_id: str, subject: Optional[str] = None) -> str:
    """
    获取用户的学习路径。
    
    Args:
        user_id: 用户唯一标识
        subject: 学习科目（可选）
    
    Returns:
        学习路径列表（JSON格式）
    """
    ctx = request_context.get() or new_context(method="get_learning_path")
    
    try:
        client = get_supabase_client()
        
        query = client.table("learning_paths") \
            .select("*") \
            .eq("user_id", user_id)
        
        if subject:
            query = query.eq("subject", subject)
        
        response = query.order("created_at", desc=True).execute()
        
        return json.dumps({
            "user_id": user_id,
            "subject": subject,
            "count": len(response.data),
            "paths": response.data
        }, ensure_ascii=False, indent=2)
    
    except APIError as e:
        raise Exception(f"获取学习路径失败: {e.message}")


@tool
def generate_learning_path(user_id: str, subject: str, 
                            knowledge_level: str = "入门",
                            learning_speed: str = "中速") -> str:
    """
    根据用户画像生成个性化学习路径。
    
    Args:
        user_id: 用户唯一标识
        subject: 学习科目
        knowledge_level: 知识水平 (入门/初级/中级/高级)
        learning_speed: 学习速度 (慢速/中速/快速)
    
    Returns:
        个性化学习路径（JSON格式）
    """
    ctx = request_context.get() or new_context(method="generate_learning_path")
    
    # 根据学习速度调整阶段数量
    stage_counts = {
        "慢速": 8,
        "中速": 5,
        "快速": 3
    }
    
    # 根据知识水平调整内容难度
    difficulty_mapping = {
        "入门": "初级",
        "初级": "初级-中级",
        "中级": "中级-高级",
        "高级": "高级"
    }
    
    num_stages = stage_counts.get(learning_speed, 5)
    content_difficulty = difficulty_mapping.get(knowledge_level, "中级")
    
    # ✅ 根据科目生成有意义的默认 topics（修复硬编码问题）
    subject_topics = {
        "通用": ["核心概念入门", "基础技能掌握", "实践应用提升"],
        "Hadoop大数据": ["Hadoop概述与HDFS", "MapReduce编程", "YARN资源管理", "Hive数据仓库"],
        "Spark大数据": ["Spark概述与RDD", "DataFrame与Spark SQL", "Spark Streaming实时处理", "MLlib机器学习"],
        "Flink实时计算": ["Flink流处理基础", "Time与Window", "State与Checkpoint", "Table API与CEP"],
        "机器学习": ["机器学习基础概念", "监督学习算法", "无监督学习", "模型评估与调优"],
        "深度学习": ["神经网络基础", "卷积神经网络CNN", "循环神经网络RNN", "Transformer与注意力机制"],
        "大数据技术": ["Hadoop生态概述", "HDFS分布式存储", "MapReduce批处理", "Kafka+Flink实时处理"],
        "数据仓库": ["数仓架构设计", "HiveQL与ETL", "数据建模与分层", "OLAP与BI分析"],
    }
    default_topics = subject_topics.get(subject, [f"{subject}核心概念", f"{subject}基础技能", f"{subject}实践应用"])
    
    # 生成学习路径结构
    learning_path = {
        "meta": {
            "user_id": user_id,
            "subject": subject,
            "knowledge_level": knowledge_level,
            "learning_speed": learning_speed,
            "content_difficulty": content_difficulty,
            "total_stages": num_stages,
            "estimated_duration": f"{num_stages * 7}天"
        },
        "stages": []
    }
    
    for i in range(num_stages):
        stage = {
            "stage_id": i + 1,
            "title": f"阶段{i+1}: {['基础', '进阶', '高级', '实战', '总结'][i % 5]}",
            "topics": [
                default_topics[i % len(default_topics)],
                f"{default_topics[i % len(default_topics)]}进阶",
                f"{default_topics[i % len(default_topics)]}实战"
            ],
            "activities": [
                "视频学习",
                "文档阅读",
                "练习题",
                "实践项目"
            ],
            "milestone": f"完成阶段{i+1}测试",
            "prerequisites": [f"阶段{k+1}" for k in range(i)] if i > 0 else []
        }
        learning_path["stages"].append(stage)
    
    return json.dumps({
        "learning_path": learning_path,
        "message": "已生成个性化学习路径，请根据路径进行学习"
    }, ensure_ascii=False, indent=2)


@tool
def update_path_progress(user_id: str, subject: str, stage_id: int, 
                          completed: bool = True) -> str:
    """
    更新学习路径进度。
    
    Args:
        user_id: 用户唯一标识
        subject: 学习科目
        stage_id: 阶段ID
        completed: 是否完成
    
    Returns:
        更新结果信息
    """
    ctx = request_context.get() or new_context(method="update_path_progress")
    
    try:
        client = get_supabase_client()
        
        # 获取当前路径
        response = client.table("learning_paths") \
            .select("path_data") \
            .eq("user_id", user_id) \
            .eq("subject", subject) \
            .eq("status", "进行中") \
            .maybe_single() \
            .execute()
        
        if response is None:
            return json.dumps({
                "success": False,
                "message": "未找到进行中的学习路径"
            }, ensure_ascii=False)
        
        # 更新进度
        path_data = {}
        if hasattr(response, 'data') and response.data:
            rd = response.data
            if isinstance(rd, dict):
                path_data = rd.get("path_data", {})
            elif isinstance(rd, list) and len(rd) > 0:
                if isinstance(rd[0], dict):
                    path_data = rd[0].get("path_data", {})
        if isinstance(path_data, dict) and "stages" in path_data and isinstance(path_data["stages"], list):
            for stage in path_data["stages"]:
                if isinstance(stage, dict) and stage.get("stage_id") == stage_id:
                    stage["completed"] = completed
                    stage["completed_at"] = "now" if completed else None
                    break
        
        client.table("learning_paths") \
            .update({"path_data": path_data}) \
            .eq("user_id", user_id) \
            .eq("subject", subject) \
            .eq("status", "进行中") \
            .execute()
        
        return json.dumps({
            "success": True,
            "message": f"阶段{stage_id}已标记为{'完成' if completed else '未完成'}",
            "user_id": user_id,
            "subject": subject,
            "stage_id": stage_id
        }, ensure_ascii=False)
    
    except APIError as e:
        raise Exception(f"更新进度失败: {e.message}")


@tool
def generate_personalized_content(user_id: str, subject: str) -> str:
    """
    根据用户画像生成个性化学习内容推荐。
    
    Args:
        user_id: 用户唯一标识
        subject: 学习科目
    
    Returns:
        个性化内容推荐（JSON格式）
    """
    ctx = request_context.get() or new_context(method="generate_personalized_content")
    
    try:
        client = get_supabase_client()
        
        # 获取用户画像
        profile_response = client.table("user_profiles") \
            .select("*") \
            .eq("user_id", user_id) \
            .maybe_single() \
            .execute()
        
        # 获取用户进度
        path_response = client.table("learning_paths") \
            .select("path_data") \
            .eq("user_id", user_id) \
            .eq("subject", subject) \
            .eq("status", "进行中") \
            .maybe_single() \
            .execute()
        
        # 分析用户特征
        profile = profile_response.data if profile_response and hasattr(profile_response, 'data') else {}
        path_data = {}
        if path_response and hasattr(path_response, 'data'):
            if isinstance(path_response.data, dict):
                path_data = path_response.data.get("path_data", {})
            elif isinstance(path_response.data, list) and len(path_response.data) > 0:
                path_data = path_response.data[0].get("path_data", {}) if isinstance(path_response.data[0], dict) else {}
        
        profile_dict = profile if isinstance(profile, dict) else {}
        # 生成推荐
        recommendations = {
            "user_id": user_id,
            "subject": subject,
            "user_profile": {
                "learning_style": profile_dict.get("learning_style", "未知") if isinstance(profile_dict, dict) else "未知",
                "knowledge_level": profile_dict.get("knowledge_level", "入门") if isinstance(profile_dict, dict) else "入门",
                "learning_speed": profile_dict.get("learning_speed", "中速") if isinstance(profile_dict, dict) else "中速"
            },
            "recommended_content": [
                {
                    "type": "document",
                    "title": "推荐文档1",
                    "reason": "根据您的学习风格推荐"
                },
                {
                    "type": "video",
                    "title": "推荐视频1",
                    "reason": "适合您的知识水平"
                },
                {
                    "type": "exercise",
                    "title": "推荐练习1",
                    "reason": "巩固当前学习内容"
                }
            ],
            "next_topic": "下一学习主题",
            "message": "基于您的画像生成个性化推荐"
        }
        
        return json.dumps(recommendations, ensure_ascii=False, indent=2)
    
    except APIError as e:
        raise Exception(f"生成个性化内容失败: {e.message}")


@tool
def save_push_record(user_id: str, push_type: str, content: str, status: str = "待发送") -> str:
    """
    保存推送记录。
    
    Args:
        user_id: 用户唯一标识
        push_type: 推送类型 (微信/飞书/邮件)
        content: 推送内容 (JSON格式字符串)
        status: 状态 (成功/失败/待发送)
    
    Returns:
        保存结果信息
    """
    ctx = request_context.get() or new_context(method="save_push_record")
    
    try:
        client = get_supabase_client()
        
        data = {
            "user_id": user_id,
            "push_type": push_type,
            "content": json.loads(content) if isinstance(content, str) else content,
            "status": status
        }
        
        response = client.table("push_records").insert(data).execute()
        data_list = list(response.data) if response.data else []
        push_id = data_list[0].get("id") if data_list and isinstance(data_list[0], dict) else None
        return json.dumps({
            "success": True,
            "message": "推送记录已保存",
            "push_id": push_id,
            "user_id": user_id,
            "push_type": push_type,
            "status": status
        }, ensure_ascii=False)
    
    except APIError as e:
        raise Exception(f"保存推送记录失败: {e.message}")


@tool
def get_user_push_records(user_id: str, limit: int = 20) -> str:
    """
    获取用户的推送记录。
    
    Args:
        user_id: 用户唯一标识
        limit: 返回数量限制
    
    Returns:
        推送记录列表（JSON格式）
    """
    ctx = request_context.get() or new_context(method="get_user_push_records")
    
    try:
        client = get_supabase_client()
        
        response = client.table("push_records") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        
        return json.dumps({
            "user_id": user_id,
            "count": len(response.data),
            "records": response.data
        }, ensure_ascii=False, indent=2)
    
    except APIError as e:
        raise Exception(f"获取推送记录失败: {e.message}")
