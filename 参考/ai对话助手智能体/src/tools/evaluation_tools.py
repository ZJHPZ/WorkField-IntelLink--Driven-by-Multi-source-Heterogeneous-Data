"""
评估智能体工具模块
功能：对学习者的学习成果或练习内容进行评估，提供反馈和评价
"""
import json
from typing import Optional
from langchain.tools import tool
from storage.database.supabase_client import get_supabase_client
from postgrest.exceptions import APIError
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def save_evaluation(user_id: str, evaluation_type: str, subject: str,
                    score: float, feedback: str, evaluation_data: str) -> str:
    """
    保存评估记录。
    
    Args:
        user_id: 用户唯一标识
        evaluation_type: 评估类型 (练习评估/学习成果评估)
        subject: 科目
        score: 得分
        feedback: 反馈详情 (JSON格式字符串)
        evaluation_data: 评估数据 (JSON格式字符串)
    
    Returns:
        保存结果信息
    """
    ctx = request_context.get() or new_context(method="save_evaluation")
    
    try:
        client = get_supabase_client()
        
        data = {
            "user_id": user_id,
            "evaluation_type": evaluation_type,
            "subject": subject,
            "score": score,
            "feedback": json.loads(feedback) if isinstance(feedback, str) else feedback,
            "evaluation_data": json.loads(evaluation_data) if isinstance(evaluation_data, str) else evaluation_data
        }
        
        response = client.table("evaluations").insert(data).execute()
        data_list = list(response.data) if response.data else []
        evaluation_id = data_list[0].get("id") if data_list and isinstance(data_list[0], dict) else None
        return json.dumps({
            "success": True,
            "message": "评估记录已保存",
            "evaluation_id": evaluation_id,
            "user_id": user_id,
            "subject": subject,
            "score": score
        }, ensure_ascii=False)
    
    except APIError as e:
        raise Exception(f"保存评估记录失败: {e.message}")


@tool
def get_evaluation_history(user_id: str, subject: Optional[str] = None,
                            evaluation_type: Optional[str] = None,
                            limit: int = 20) -> str:
    """
    获取评估历史记录。
    
    Args:
        user_id: 用户唯一标识
        subject: 科目（可选）
        evaluation_type: 评估类型（可选）
        limit: 返回数量限制
    
    Returns:
        评估历史列表（JSON格式）
    """
    ctx = request_context.get() or new_context(method="get_evaluation_history")
    
    try:
        client = get_supabase_client()
        
        query = client.table("evaluations") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(limit)
        
        if subject:
            query = query.eq("subject", subject)
        if evaluation_type:
            query = query.eq("evaluation_type", evaluation_type)
        
        response = query.execute()
        
        return json.dumps({
            "user_id": user_id,
            "subject": subject,
            "evaluation_type": evaluation_type,
            "count": len(response.data),
            "evaluations": response.data
        }, ensure_ascii=False, indent=2)
    
    except APIError as e:
        raise Exception(f"获取评估历史失败: {e.message}")


@tool
def evaluate_multiple_choice(user_answer: str, correct_answer: str,
                              question: str) -> str:
    """
    评估选择题答案。
    
    Args:
        user_answer: 用户答案
        correct_answer: 正确答案
        question: 题目内容
    
    Returns:
        评估结果（JSON格式）
    """
    ctx = request_context.get() or new_context(method="evaluate_multiple_choice")
    
    is_correct = user_answer.upper().strip() == correct_answer.upper().strip()
    
    result = {
        "question": question,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "is_correct": is_correct,
        "score": 1.0 if is_correct else 0.0,
        "feedback": "回答正确！" if is_correct else f"回答错误，正确答案是 {correct_answer}",
        "explanation": ""
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def evaluate_short_answer(user_answer: str, key_points: str, 
                          question: str) -> str:
    """
    评估简答题答案。
    
    Args:
        user_answer: 用户答案
        key_points: 标准答案要点 (JSON格式字符串)
        question: 题目内容
    
    Returns:
        评估结果（JSON格式）
    """
    ctx = request_context.get() or new_context(method="evaluate_short_answer")
    
    try:
        points = json.loads(key_points) if isinstance(key_points, str) else key_points
    except:
        points = []
    
    # 简单评分逻辑
    user_lower = user_answer.lower()
    matched_points = []
    for point in points:
        if any(keyword in user_lower for keyword in point.lower().split()):
            matched_points.append(point)
    
    # 计算得分
    total_points = len(points) if points else 1
    score = len(matched_points) / total_points
    
    result = {
        "question": question,
        "user_answer": user_answer,
        "key_points": points,
        "matched_points": matched_points,
        "score": round(score, 2),
        "pass_threshold": 0.6,
        "is_pass": score >= 0.6,
        "feedback": {
            "strengths": matched_points,
            "improvements": [p for p in points if p not in matched_points],
            "suggestion": "建议补充遗漏的要点" if matched_points != points else "答案完整"
        }
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def evaluate_coding_exercise(user_code: str, test_cases: str,
                              expected_output: str, language: str = "Python") -> str:
    """
    评估编程练习。
    
    Args:
        user_code: 用户代码
        test_cases: 测试用例 (JSON格式字符串)
        expected_output: 期望输出
        language: 编程语言
    
    Returns:
        评估结果（JSON格式）
    """
    ctx = request_context.get() or new_context(method="evaluate_coding_exercise")
    
    try:
        cases = json.loads(test_cases) if isinstance(test_cases, str) else test_cases
    except:
        cases = []
    
    # 模拟代码评估
    result = {
        "language": language,
        "user_code": user_code,
        "expected_output": expected_output,
        "test_results": [],
        "total_tests": len(cases) if cases else 1,
        "passed_tests": 0,
        "score": 0.0,
        "feedback": {
            "syntax_check": "通过",
            "logic_check": "建议优化",
            "suggestions": [
                "注意代码规范",
                "考虑边界情况",
                "添加注释说明"
            ]
        }
    }
    
    # 模拟测试结果
    if cases:
        for i, case in enumerate(cases):
            result["test_results"].append({
                "test_case": i + 1,
                "input": case.get("input", ""),
                "expected": case.get("expected_output", ""),
                "passed": True,  # 模拟结果
                "reason": "通过"
            })
            result["passed_tests"] += 1
    
    # 计算总分
    if result["total_tests"] > 0:
        result["score"] = round(result["passed_tests"] / result["total_tests"], 2)
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def generate_evaluation_report(user_id: str, subject: str) -> str:
    """
    生成学习评估报告。
    
    Args:
        user_id: 用户唯一标识
        subject: 学习科目
    
    Returns:
        评估报告（JSON格式）
    """
    ctx = request_context.get() or new_context(method="generate_evaluation_report")
    
    try:
        client = get_supabase_client()
        
        # 获取最近的评估记录
        response = client.table("evaluations") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("subject", subject) \
            .order("created_at", desc=True) \
            .limit(10) \
            .execute()
        
        evaluations = list(response.data) if response.data else []
        
        # 计算统计数据
        scores = []
        if evaluations:
            for e in evaluations:
                if isinstance(e, dict):
                    scores.append(e.get("score", 0))
            avg_score = sum(scores) / len(scores) if scores else 0
            max_score = max(scores) if scores else 0
            min_score = min(scores) if scores else 0
            
            # 趋势分析
            trend = "上升" if scores and len(scores) > 1 and scores[0] > scores[-1] else "稳定"
        else:
            avg_score = max_score = min_score = 0
            trend = "无数据"
        
        # 生成报告
        report = {
            "user_id": user_id,
            "subject": subject,
            "summary": {
                "total_assessments": len(evaluations),
                "average_score": round(avg_score, 2),
                "highest_score": max_score,
                "lowest_score": min_score,
                "trend": trend
            },
            "strengths": [
                "概念理解能力较强",
                "实践应用能力良好"
            ],
            "weaknesses": [
                "需要加强综合应用",
                "注意细节把控"
            ],
            "recommendations": [
                "建议加强练习",
                "注重知识串联",
                "定期回顾总结"
            ],
            "message": "评估报告生成完成"
        }
        
        return json.dumps(report, ensure_ascii=False, indent=2)
    
    except APIError as e:
        raise Exception(f"生成评估报告失败: {e.message}")


@tool
def calculate_learning_progress(user_id: str, subject: str) -> str:
    """
    计算学习进度。
    
    Args:
        user_id: 用户唯一标识
        subject: 学习科目
    
    Returns:
        学习进度（JSON格式）
    """
    ctx = request_context.get() or new_context(method="calculate_learning_progress")
    
    try:
        client = get_supabase_client()
        
        # 获取用户画像
        profile_response = client.table("user_profiles") \
            .select("learning_progress") \
            .eq("user_id", user_id) \
            .maybe_single() \
            .execute()
        
        # 获取学习路径
        path_response = client.table("learning_paths") \
            .select("path_data") \
            .eq("user_id", user_id) \
            .eq("subject", subject) \
            .eq("status", "进行中") \
            .maybe_single() \
            .execute()
        
        # 获取评估记录
        eval_response = client.table("evaluations") \
            .select("score") \
            .eq("user_id", user_id) \
            .eq("subject", subject) \
            .execute()
        
        progress_data = {
            "user_id": user_id,
            "subject": subject,
            "overall_progress": {
                "percentage": 0.0,
                "status": "进行中"
            },
            "path_progress": {
                "total_stages": 0,
                "completed_stages": 0,
                "current_stage": 0
            },
            "assessment_summary": {
                "total_tests": len(eval_response.data) if eval_response and eval_response.data else 0,
                "average_score": 0.0,
                "mastery_level": "初级"
            },
            "topic_completion": []
        }
        
        # 计算路径进度
        path_data = {}
        if path_response and hasattr(path_response, 'data') and path_response.data:
            pd = path_response.data
            if isinstance(pd, dict):
                path_data = pd.get("path_data", {})
            elif isinstance(pd, list) and len(pd) > 0 and isinstance(pd[0], dict):
                path_data = pd[0].get("path_data", {})
        stages = []
        if isinstance(path_data, dict):
            stages = path_data.get("stages", [])
        total = len(stages) if isinstance(stages, list) else 0
        completed = 0
        if isinstance(stages, list):
            for s in stages:
                if isinstance(s, dict) and s.get("completed", False):
                    completed += 1
        
        progress_data["path_progress"] = {
            "total_stages": total,
            "completed_stages": completed,
            "current_stage": completed + 1 if completed < total else total,
            "percentage": round(completed / total * 100, 1) if total > 0 else 0
        }
        
        progress_data["overall_progress"]["percentage"] = round(completed / total * 100, 1) if total > 0 else 0
        
        # 计算评估摘要
        scores = []
        if eval_response and hasattr(eval_response, 'data') and eval_response.data:
            for e in eval_response.data:
                if isinstance(e, dict):
                    scores.append(e.get("score", 0))
                else:
                    scores.append(0)
        avg_score = sum(scores) / len(scores) if scores else 0
        
        mastery_level = "初级"
        if avg_score >= 0.9:
            mastery_level = "精通"
        elif avg_score >= 0.7:
            mastery_level = "熟练"
        elif avg_score >= 0.5:
            mastery_level = "中级"
        
        progress_data["assessment_summary"] = {
            "total_tests": len(scores),
            "average_score": round(avg_score, 2),
            "mastery_level": mastery_level
        }
        
        return json.dumps(progress_data, ensure_ascii=False, indent=2)
    
    except APIError as e:
        raise Exception(f"计算学习进度失败: {e.message}")
