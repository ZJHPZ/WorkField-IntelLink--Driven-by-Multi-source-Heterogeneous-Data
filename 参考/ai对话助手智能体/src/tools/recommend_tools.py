"""
推荐智能体工具模块
提供联网搜索学习资源的能力
"""
import json
from typing import List, Dict, Any, Optional
from langchain.tools import tool
from coze_coding_dev_sdk import SearchClient
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def search_learning_resources(
    topic: str,
    resource_type: str = "all",
    count: int = 10,
    difficulty: str = "all"
) -> str:
    """
    联网搜索学习资源。
    
    根据用户指定的主题和偏好，搜索互联网上的优质学习资源，
    包括教程、文档、视频课程、实战项目等。
    
    Args:
        topic: 学习主题，如 "Python", "Machine Learning", "Hadoop"
        resource_type: 资源类型，可选: "all", "tutorial", "video", "document", "practice"
        count: 返回结果数量，默认10条
        difficulty: 难度级别，可选: "all", "beginner", "intermediate", "advanced"
    
    Returns:
        JSON格式的搜索结果，包含标题、URL、摘要、来源等信息
    """
    ctx = new_context(method="recommendation.search")
    client = SearchClient(ctx=ctx)
    
    # 构建搜索查询
    query_parts = [topic]
    
    if difficulty != "all":
        query_parts.append(difficulty)
    
    if resource_type == "tutorial":
        query_parts.extend(["教程", "教程", "guide"])
    elif resource_type == "video":
        query_parts.extend(["视频课程", "video", "教程"])
    elif resource_type == "document":
        query_parts.extend(["文档", "documentation", "教程"])
    elif resource_type == "practice":
        query_parts.extend(["实战项目", "练习", "project"])
    
    query = " ".join(query_parts)
    
    try:
        # 执行搜索
        response = client.web_search_with_summary(
            query=query,
            count=count
        )
        
        if not response.web_items:
            return json.dumps({
                "success": False,
                "message": f"未找到 {topic} 相关的学习资源",
                "resources": []
            }, ensure_ascii=False)
        
        # 整理结果
        resources = []
        for i, item in enumerate(response.web_items, 1):
            resources.append({
                "index": i,
                "title": item.title,
                "url": item.url,
                "site_name": item.site_name,
                "snippet": item.snippet,
                "summary": item.summary,
                "authority": item.auth_info_des if hasattr(item, 'auth_info_des') else None
            })
        
        result = {
            "success": True,
            "topic": topic,
            "resource_type": resource_type,
            "count": len(resources),
            "resources": resources,
            "ai_summary": response.summary
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"搜索失败: {str(e)}",
            "resources": []
        }, ensure_ascii=False)


@tool
def search_official_docs(topic: str, count: int = 5) -> str:
    """
    搜索官方文档和权威资料。
    
    专门搜索官方文档、权威教程等高质量学习资源。
    
    Args:
        topic: 学习主题
        count: 返回结果数量，默认5条
    
    Returns:
        JSON格式的官方文档搜索结果
    """
    ctx = new_context(method="recommendation.docs")
    client = SearchClient(ctx=ctx)
    
    # 搜索官方文档和权威资料
    query = f"{topic} 官方文档 教程 site:github.com OR site:readthedocs.io OR site:official"
    
    try:
        response = client.web_search(
            query=query,
            count=count
        )
        
        if not response.web_items:
            return json.dumps({
                "success": False,
                "message": f"未找到 {topic} 的官方文档",
                "docs": []
            }, ensure_ascii=False)
        
        docs = []
        for i, item in enumerate(response.web_items, 1):
            docs.append({
                "index": i,
                "title": item.title,
                "url": item.url,
                "site_name": item.site_name,
                "snippet": item.snippet
            })
        
        return json.dumps({
            "success": True,
            "topic": topic,
            "docs": docs
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"搜索失败: {str(e)}"
        }, ensure_ascii=False)


@tool
def search_practice_projects(topic: str, count: int = 8) -> str:
    """
    搜索实战项目和练习资源。
    
    搜索适合练习和实战的学习项目，帮助用户巩固知识。
    
    Args:
        topic: 学习主题
        count: 返回结果数量，默认8条
    
    Returns:
        JSON格式的实战项目搜索结果
    """
    ctx = new_context(method="recommendation.projects")
    client = SearchClient(ctx=ctx)
    
    # 搜索实战项目
    query = f"{topic} 实战项目 练习 github 完整项目"
    
    try:
        response = client.web_search_with_summary(
            query=query,
            count=count
        )
        
        if not response.web_items:
            return json.dumps({
                "success": False,
                "message": f"未找到 {topic} 相关的实战项目",
                "projects": []
            }, ensure_ascii=False)
        
        projects = []
        for i, item in enumerate(response.web_items, 1):
            projects.append({
                "index": i,
                "title": item.title,
                "url": item.url,
                "site_name": item.site_name,
                "description": item.snippet,
                "summary": item.summary
            })
        
        return json.dumps({
            "success": True,
            "topic": topic,
            "projects": projects
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"搜索失败: {str(e)}"
        }, ensure_ascii=False)


@tool
def recommend_learning_path(topic: str, current_level: str = "beginner") -> str:
    """
    推荐学习路径和资源。
    
    根据用户的学习主题和当前水平，推荐完整的学习路径。
    
    Args:
        topic: 学习主题
        current_level: 当前水平，可选: "beginner", "intermediate", "advanced"
    
    Returns:
        JSON格式的学习路径推荐
    """
    ctx = new_context(method="recommendation.path")
    client = SearchClient(ctx=ctx)
    
    # 搜索学习路径
    query = f"{topic} 学习路线 教程 从入门到精通"
    
    try:
        response = client.web_search_with_summary(
            query=query,
            count=5
        )
        
        if not response.web_items:
            return json.dumps({
                "success": False,
                "message": f"未找到 {topic} 的学习路径",
                "path": []
            }, ensure_ascii=False)
        
        path = []
        for i, item in enumerate(response.web_items, 1):
            path.append({
                "step": i,
                "title": item.title,
                "url": item.url,
                "description": item.summary or item.snippet
            })
        
        return json.dumps({
            "success": True,
            "topic": topic,
            "current_level": current_level,
            "recommended_path": path
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": f"搜索失败: {str(e)}"
        }, ensure_ascii=False)
