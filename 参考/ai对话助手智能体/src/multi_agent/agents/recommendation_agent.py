"""
推荐智能体
联网搜索并推荐精准的学习资源
"""
import json
import re
from typing import Dict, Any, Optional
from multi_agent.base.base_agent import BaseAgent
from multi_agent.base.agent_state import MultiAgentState
from multi_agent.system_prompts import RECOMMENDATION_AGENT_PROMPT
from tools.recommend_tools import (
    search_learning_resources,
    search_official_docs,
    search_practice_projects,
    recommend_learning_path
)


class RecommendationAgent(BaseAgent):
    """推荐智能体 - 联网搜索精准学习资源"""
    
    def __init__(self):
        super().__init__(
            agent_id="recommendation",
            name="推荐智能体",
            description="联网搜索并推荐精准的学习资源",
            processing_mode="FEDERATED"
        )
        # 注册工具
        self.tools = [
            search_learning_resources,
            search_official_docs,
            search_practice_projects,
            recommend_learning_path
        ]
    
    @property
    def intent_type(self) -> str:
        return "recommendation"
    
    async def process(self, state: MultiAgentState) -> Dict[str, Any]:
        """处理推荐请求"""
        self.state = state
        user_id = self._get_user_id()
        user_input = self._get_user_input()
        
        # 解析用户需求
        parsed = self._parse_request(user_input)
        
        # 执行搜索
        search_results = await self._execute_search(parsed)
        
        # 格式化响应
        response = self._format_response(parsed, search_results)
        
        return {
            "success": True,
            "agent": self.agent_id,
            "response": response,
            "recommendations": search_results,
            "user_id": user_id
        }
    
    def _parse_request(self, user_input: str) -> Dict[str, Any]:
        """解析用户的推荐请求"""
        parsed = {
            "original": user_input,
            "topic": "",
            "resource_type": "all",
            "difficulty": "all",
            "search_type": "general"
        }
        
        topic = ""
        
        # 模式6: 学习xxx (支持英文关键词，如: 学习Python) - 优先匹配英文
        match = re.search(r"学习([a-zA-Z]{3,20})", user_input)
        if match:
            topic = match.group(1)
        
        # 模式1: 学习xxx (如: 学习大数据, 学习Python)
        if not topic:
            match = re.search(r"学习([\u4e00-\u9fa5a-zA-Z0-9]+)", user_input)
            if match:
                topic = match.group(1)
        
        # 模式2: 推荐xxx资源/教程
        if not topic:
            match = re.search(r"推荐([\u4e00-\u9fa5a-zA-Z0-9]+)(?:教程|课程|网站|资源|书籍)", user_input)
            if match:
                topic = match.group(1)
        
        # 模式3: xxx有什么好
        if not topic:
            match = re.search(r"([\u4e00-\u9fa5a-zA-Z0-9]+)有什么好", user_input)
            if match:
                topic = match.group(1)
        
        # 模式4: 帮我推荐xxx
        if not topic:
            match = re.search(r"(?:帮我推荐|推荐)\s*(?:一些)?\s*([\u4e00-\u9fa5a-zA-Z0-9]+)", user_input)
            if match:
                topic = match.group(1)
        
        # 模式5: xxx教程/课程
        if not topic:
            match = re.search(r"([\u4e00-\u9fa5a-zA-Z0-9]+)(?:教程|课程|网站)", user_input)
            if match:
                topic = match.group(1)
        
        # 模式7: 提取连续的关键词 (如: Python编程, Hadoop大数据等)
        if not topic:
            match = re.search(r"([\u4e00-\u9fa5a-zA-Z]{2,8})", user_input)
            if match:
                topic = match.group(1)
        
        parsed["topic"] = topic
        
        # 判断资源类型
        if any(keyword in user_input for keyword in ["官方文档", "文档"]):
            parsed["resource_type"] = "document"
            parsed["search_type"] = "docs"
        elif any(keyword in user_input for keyword in ["视频", "课程"]):
            parsed["resource_type"] = "video"
        elif any(keyword in user_input for keyword in ["项目", "实战", "练习"]):
            parsed["resource_type"] = "practice"
            parsed["search_type"] = "projects"
        elif any(keyword in user_input for keyword in ["学习路径", "路线", "怎么学"]):
            parsed["search_type"] = "path"
        
        # 判断难度级别
        if "入门" in user_input or "初学" in user_input:
            parsed["difficulty"] = "beginner"
        elif "进阶" in user_input or "深入" in user_input:
            parsed["difficulty"] = "intermediate"
        elif "高级" in user_input or "精通" in user_input:
            parsed["difficulty"] = "advanced"
        
        return parsed
    
    async def _execute_search(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """执行联网搜索"""
        topic = parsed["topic"]
        results = {
            "general": None,
            "docs": None,
            "projects": None,
            "path": None
        }
        
        try:
            # 根据搜索类型选择搜索策略
            if parsed["search_type"] == "docs":
                # 搜索官方文档
                docs_result = search_official_docs.invoke({
                    "topic": topic,
                    "count": 5
                })
                results["docs"] = json.loads(docs_result)
                
            elif parsed["search_type"] == "projects":
                # 搜索实战项目
                projects_result = search_practice_projects.invoke({
                    "topic": topic,
                    "count": 8
                })
                results["projects"] = json.loads(projects_result)
                
            elif parsed["search_type"] == "path":
                # 搜索学习路径
                path_result = recommend_learning_path.invoke({
                    "topic": topic,
                    "current_level": parsed["difficulty"]
                })
                results["path"] = json.loads(path_result)
                
            else:
                # 综合搜索
                general_result = search_learning_resources.invoke({
                    "topic": topic,
                    "resource_type": parsed["resource_type"],
                    "count": 10,
                    "difficulty": parsed["difficulty"]
                })
                results["general"] = json.loads(general_result)
                
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def _format_response(self, parsed: Dict[str, Any], results: Dict[str, Any]) -> str:
        """格式化推荐响应"""
        topic = parsed["topic"]
        parts = []
        
        # 开场白
        parts.append(f"为你搜索了「{topic}」相关的学习资源 🔍\n")
        
        # 处理不同类型的搜索结果
        if parsed["search_type"] == "docs" and results.get("docs"):
            parts.append(self._format_docs(results["docs"]))
            
        elif parsed["search_type"] == "projects" and results.get("projects"):
            parts.append(self._format_projects(results["projects"]))
            
        elif parsed["search_type"] == "path" and results.get("path"):
            parts.append(self._format_path(results["path"]))
            
        elif results.get("general"):
            parts.append(self._format_general(results["general"]))
            
        elif results.get("error"):
            parts.append(f"搜索过程中出现了一些问题：{results['error']}")
            
        else:
            parts.append(f"抱歉，暂时没有找到「{topic}」相关的学习资源")
        
        return "\n".join(parts)
    
    def _format_general(self, result: Dict) -> str:
        """格式化综合搜索结果"""
        if not result.get("success"):
            return f"搜索失败：{result.get('message', '未知错误')}"
        
        resources = result.get("resources", [])
        if not resources:
            return "未找到相关资源"
        
        parts = [f"找到 {len(resources)} 个优质资源：\n"]
        
        for i, res in enumerate(resources[:5], 1):
            parts.append(f"{i}. **{res.get('title', '未命名')}**")
            if res.get('site_name'):
                parts.append(f"   📍 来源：{res['site_name']}")
            if res.get('snippet'):
                # 截取摘要
                snippet = res['snippet'][:100]
                parts.append(f"   📝 {snippet}...")
            if res.get('url'):
                parts.append(f"   🔗 {res['url']}")
            parts.append("")
        
        # 添加 AI 总结
        if result.get("ai_summary"):
            parts.append("---")
            parts.append(f"💡 AI 总结：{result['ai_summary']}")
        
        return "\n".join(parts)
    
    def _format_docs(self, result: Dict) -> str:
        """格式化官方文档结果"""
        if not result.get("success"):
            return f"搜索失败：{result.get('message', '未知错误')}"
        
        docs = result.get("docs", [])
        if not docs:
            return "未找到官方文档"
        
        parts = [f"📚 找到 {len(docs)} 个官方文档/权威资料：\n"]
        
        for doc in docs:
            parts.append(f"- **{doc.get('title', '未命名')}**")
            if doc.get('site_name'):
                parts.append(f"  来源：{doc['site_name']}")
            if doc.get('url'):
                parts.append(f"  🔗 {doc['url']}")
            parts.append("")
        
        return "\n".join(parts)
    
    def _format_projects(self, result: Dict) -> str:
        """格式化实战项目结果"""
        if not result.get("success"):
            return f"搜索失败：{result.get('message', '未知错误')}"
        
        projects = result.get("projects", [])
        if not projects:
            return "未找到实战项目"
        
        parts = [f"💻 找到 {len(projects)} 个实战项目/练习资源：\n"]
        
        for proj in projects[:5]:
            parts.append(f"- **{proj.get('title', '未命名')}**")
            if proj.get('description'):
                desc = proj['description'][:80]
                parts.append(f"  📝 {desc}...")
            if proj.get('url'):
                parts.append(f"  🔗 {proj['url']}")
            parts.append("")
        
        return "\n".join(parts)
    
    def _format_path(self, result: Dict) -> str:
        """格式化学习路径结果"""
        if not result.get("success"):
            return f"搜索失败：{result.get('message', '未知错误')}"
        
        path = result.get("recommended_path", [])
        if not path:
            return "未找到学习路径"
        
        parts = [f"🗺️ 推荐学习路径：\n"]
        
        for step in path:
            parts.append(f"{step.get('step', '?')}. **{step.get('title', '未命名')}**")
            if step.get('description'):
                parts.append(f"   {step['description'][:80]}...")
            if step.get('url'):
                parts.append(f"   🔗 {step['url']}")
            parts.append("")
        
        return "\n".join(parts)
    
    def _get_user_id(self) -> str:
        """获取用户 ID"""
        return getattr(self.state, 'user_id', 'unknown')
    
    def _get_user_input(self) -> str:
        """获取用户输入"""
        messages = self.state.get('messages', [])
        if messages:
            last_msg = messages[-1]
            if isinstance(last_msg, dict):
                return last_msg.get('content', '')
            elif hasattr(last_msg, 'content'):
                return last_msg.content
        return ''


# 单例模式
_instance: Optional[RecommendationAgent] = None

def get_recommendation_agent() -> RecommendationAgent:
    """获取推荐智能体单例"""
    global _instance
    if _instance is None:
        _instance = RecommendationAgent()
    return _instance
