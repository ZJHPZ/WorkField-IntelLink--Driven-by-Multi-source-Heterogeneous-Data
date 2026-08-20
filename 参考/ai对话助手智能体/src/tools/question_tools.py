"""
题库与实操智能体工具模块
功能：生成练习题和代码实操案例
"""
import json
from typing import Optional
from langchain.tools import tool
from storage.database.supabase_client import get_supabase_client
from postgrest.exceptions import APIError
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def save_question(subject: str, topic: str, difficulty: str, question_type: str,
                  question_data: str, answer_data: str) -> str:
    """
    保存练习题到题库。
    
    Args:
        subject: 科目
        topic: 知识点
        difficulty: 难度 (简单/中等/困难)
        question_type: 题型 (选择题/简答题/编程题)
        question_data: 题目详情 (JSON格式字符串)
        answer_data: 答案详情 (JSON格式字符串)
    
    Returns:
        保存结果信息
    """
    ctx = request_context.get() or new_context(method="save_question")
    
    try:
        client = get_supabase_client()
        
        data = {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "question_type": question_type,
            "question_data": json.loads(question_data) if isinstance(question_data, str) else question_data,
            "answer_data": json.loads(answer_data) if isinstance(answer_data, str) else answer_data
        }
        
        response = client.table("questions").insert(data).execute()
        data_list = list(response.data) if response.data else []
        question_id = data_list[0].get("id") if data_list and isinstance(data_list[0], dict) else None
        return json.dumps({
            "success": True,
            "message": "题目已保存",
            "question_id": question_id,
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "question_type": question_type
        }, ensure_ascii=False)
    
    except APIError as e:
        raise Exception(f"保存题目失败: {e.message}")


@tool
def get_questions(subject: str, topic: Optional[str] = None,
                   difficulty: Optional[str] = None,
                   question_type: Optional[str] = None,
                   limit: int = 10) -> str:
    """
    从题库获取练习题。
    
    Args:
        subject: 科目
        topic: 知识点（可选）
        difficulty: 难度（可选）
        question_type: 题型（可选）
        limit: 返回数量限制
    
    Returns:
        题目列表（JSON格式）
    """
    ctx = request_context.get() or new_context(method="get_questions")
    
    try:
        client = get_supabase_client()
        
        query = client.table("questions") \
            .select("*") \
            .eq("subject", subject) \
            .limit(limit)
        
        if topic:
            query = query.eq("topic", topic)
        if difficulty:
            query = query.eq("difficulty", difficulty)
        if question_type:
            query = query.eq("question_type", question_type)
        
        response = query.execute()
        
        return json.dumps({
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "question_type": question_type,
            "count": len(response.data),
            "questions": response.data
        }, ensure_ascii=False, indent=2)
    
    except APIError as e:
        raise Exception(f"获取题目失败: {e.message}")


@tool
def generate_multiple_choice(subject: str, topic: str, difficulty: str, count: int = 5) -> str:
    """
    生成选择题练习题（使用 LLM 生成真实内容）。
    
    Args:
        subject: 科目
        topic: 知识点
        difficulty: 难度 (简单/中等/困难)
        count: 生成数量
    
    Returns:
        选择题列表（JSON格式）
    """
    ctx = request_context.get() or new_context(method="generate_multiple_choice")
    
    # 尝试使用 LLM 生成真实题目
    try:
        import logging
        from integrations.llm_factory import create_llm_from_config
        
        logger = logging.getLogger(__name__)
        llm = create_llm_from_config()
        
        # 构建 prompt
        prompt = f"""你是一位大数据教育专家。请为以下主题生成练习题。

主题：{subject} - {topic}
难度：{difficulty}
题目类型：选择题
数量：{count}道

要求：
1. 题目要有专业性，体现{subject}的核心知识点
2. 答案要准确，不能有歧义
3. 返回JSON格式，包含questions数组，每个题目包含question、options（A-D，格式为["A. 选项1", "B. 选项2", ...]）和answer字段
4. 只返回JSON，不要有其他解释说明

JSON格式示例：
{{
    "questions": [
        {{
            "question": "题目内容",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "answer": "A"
        }}
    ]
}}"""
        
        messages = [{"role": "user", "content": prompt}]
        result = llm.chat(messages)
        
        if result:
            import re
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                import json as json_module
                json_str = json_match.group()
                data = json_module.loads(json_str)
                raw_questions = data.get("questions", [])
                
                # 转换格式
                questions = []
                for q in raw_questions:
                    formatted_q = {
                        "id": len(questions) + 1,
                        "type": "multiple_choice",
                        "question": q.get("question", ""),
                        "answer": q.get("answer", ""),
                        "explanation": q.get("explanation", "")
                    }
                    
                    # 处理 options 格式
                    options = q.get("options", [])
                    if options:
                        if isinstance(options[0], str):
                            formatted_q["options"] = []
                            for opt in options:
                                if ". " in opt:
                                    key, text = opt.split(". ", 1)
                                    formatted_q["options"].append({"key": key.strip(), "text": text.strip()})
                                elif opt and len(opt) > 0:
                                    formatted_q["options"].append({"key": opt[0], "text": opt[1:].strip() if len(opt) > 1 else opt})
                        else:
                            formatted_q["options"] = options
                    
                    questions.append(formatted_q)
                
                return json.dumps({
                    "subject": subject,
                    "topic": topic,
                    "difficulty": difficulty,
                    "question_type": "选择题",
                    "count": len(questions),
                    "questions": questions,
                    "generated_by": "llm"
                }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        import logging
        import json as json_module
        logger = logging.getLogger(__name__)
        logger.warning(f"[generate_multiple_choice] LLM调用失败，使用模板: {e}")
    
    # 如果 LLM 调用失败，生成占位符模板
    questions = []
    for i in range(count):
        question = {
            "id": i + 1,
            "type": "multiple_choice",
            "question": f"[{topic}] 第{i+1}题：",
            "options": [
                {"key": "A", "text": "选项A内容"},
                {"key": "B", "text": "选项B内容"},
                {"key": "C", "text": "选项C内容"},
                {"key": "D", "text": "选项D内容"}
            ],
            "answer": "A",
            "explanation": "答案解析"
        }
        questions.append(question)
    
    return json.dumps({
        "subject": subject,
        "topic": topic,
        "difficulty": difficulty,
        "question_type": "选择题",
        "count": count,
        "questions": questions,
        "message": f"已生成{count}道选择题"
    }, ensure_ascii=False, indent=2)


@tool
def generate_short_answer(subject: str, topic: str, difficulty: str, count: int = 3) -> str:
    """
    生成简答题练习题。
    
    Args:
        subject: 科目
        topic: 知识点
        difficulty: 难度 (简单/中等/困难)
        count: 生成数量
    
    Returns:
        简答题列表（JSON格式）
    """
    ctx = request_context.get() or new_context(method="generate_short_answer")
    
    # 生成简答题模板
    questions = []
    for i in range(count):
        question = {
            "id": i + 1,
            "type": "short_answer",
            "question": f"[{topic}] 第{i+1}题：",
            "answer_template": "参考答案：\n1. 要点1\n2. 要点2\n3. 要点3",
            "grading_criteria": {
                "key_points": ["要点1", "要点2", "要点3"],
                "weight": [0.3, 0.4, 0.3]
            }
        }
        questions.append(question)
    
    return json.dumps({
        "subject": subject,
        "topic": topic,
        "difficulty": difficulty,
        "question_type": "简答题",
        "count": count,
        "questions": questions,
        "message": f"已生成{count}道简答题，请填充具体内容"
    }, ensure_ascii=False, indent=2)


@tool
def generate_coding_exercise(subject: str, topic: str, difficulty: str, 
                              programming_language: str = "Python", count: int = 3) -> str:
    """
    生成编程练习题。
    
    Args:
        subject: 科目
        topic: 知识点
        difficulty: 难度 (简单/中等/困难)
        programming_language: 编程语言
        count: 生成数量
    
    Returns:
        编程题列表（JSON格式）
    """
    ctx = request_context.get() or new_context(method="generate_coding_exercise")
    
    # 根据编程语言生成代码模板
    code_templates = {
        "Python": {
            "template": "def solution():\n    # 在此编写代码\n    pass",
            "test_case": "assert solution() == expected_output"
        },
        "JavaScript": {
            "template": "function solution() {\n    // 在此编写代码\n    return null;\n}",
            "test_case": "console.log(solution());"
        },
        "Java": {
            "template": "public class Solution {\n    public static void main(String[] args) {\n        // 在此编写代码\n    }\n}",
            "test_case": "// 测试用例"
        }
    }
    
    template = code_templates.get(programming_language, code_templates["Python"])
    
    exercises = []
    for i in range(count):
        exercise = {
            "id": i + 1,
            "type": "coding",
            "programming_language": programming_language,
            "title": f"[{topic}] 编程练习{i+1}",
            "description": "题目描述",
            "requirements": [
                "要求1",
                "要求2"
            ],
            "code_template": template["template"],
            "test_cases": [
                {
                    "input": "示例输入",
                    "expected_output": "预期输出",
                    "explanation": "用例说明"
                }
            ],
            "hints": [
                "提示1",
                "提示2"
            ],
            "answer_template": template["template"]
        }
        exercises.append(exercise)
    
    return json.dumps({
        "subject": subject,
        "topic": topic,
        "difficulty": difficulty,
        "programming_language": programming_language,
        "question_type": "编程题",
        "count": count,
        "exercises": exercises,
        "message": f"已生成{count}道{programming_language}编程题，请填充具体内容"
    }, ensure_ascii=False, indent=2)


@tool
def generate_practice_set(subject: str, topic: str, difficulty: str,
                          mc_count: int = 3, sa_count: int = 2, 
                          code_count: int = 1,
                          programming_language: str = "Python") -> str:
    """
    生成完整的练习题集，包含多种题型。
    
    Args:
        subject: 科目
        topic: 知识点
        difficulty: 难度
        mc_count: 选择题数量
        sa_count: 简答题数量
        code_count: 编程题数量
        programming_language: 编程语言
    
    Returns:
        完整练习题集（JSON格式）
    """
    ctx = request_context.get() or new_context(method="generate_practice_set")
    
    practice_set = {
        "meta": {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "total_questions": mc_count + sa_count + code_count,
            "estimated_time": f"{(mc_count * 2 + sa_count * 5 + code_count * 15)}分钟"
        },
        "sections": {
            "multiple_choice": {
                "type": "选择题",
                "count": mc_count,
                "questions": []
            },
            "short_answer": {
                "type": "简答题",
                "count": sa_count,
                "questions": []
            },
            "coding": {
                "type": "编程题",
                "count": code_count,
                "language": programming_language,
                "exercises": []
            }
        }
    }
    
    # 生成选择题
    for i in range(mc_count):
        practice_set["sections"]["multiple_choice"]["questions"].append({
            "id": i + 1,
            "question": f"[{topic}] 第{i+1}题：",
            "options": [
                {"key": "A", "text": "选项A"},
                {"key": "B", "text": "选项B"},
                {"key": "C", "text": "选项C"},
                {"key": "D", "text": "选项D"}
            ],
            "answer": "A",
            "explanation": ""
        })
    
    # 生成简答题
    for i in range(sa_count):
        practice_set["sections"]["short_answer"]["questions"].append({
            "id": i + 1,
            "question": f"[{topic}] 第{i+1}题：",
            "answer_template": "",
            "key_points": []
        })
    
    # 生成编程题
    template = {
        "Python": "def solution():\n    pass",
        "JavaScript": "function solution() {\n    return null;\n}",
        "Java": "public class Solution {}"
    }
    
    for i in range(code_count):
        practice_set["sections"]["coding"]["exercises"].append({
            "id": i + 1,
            "title": f"编程练习{i+1}",
            "description": "",
            "code_template": template.get(programming_language, template["Python"]),
            "test_cases": []
        })
    
    return json.dumps({
        "practice_set": practice_set,
        "message": "已生成完整练习题集，请填充具体内容"
    }, ensure_ascii=False, indent=2)
