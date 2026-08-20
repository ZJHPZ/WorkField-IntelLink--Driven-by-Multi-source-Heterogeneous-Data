"""
RAG 题库检索工具
基于知识库的题目检索和智能出题
"""

import json
import re
from typing import List, Dict, Any, Optional
from langchain.tools import tool
from coze_coding_dev_sdk import KnowledgeClient, Config
from coze_coding_utils.runtime_ctx.context import new_context


# 知识库配置
DATASET_NAME = "bigdata_question_bank"

# 初始化知识库客户端
_config = Config()
_knowledge_client = None


def _get_knowledge_client():
    """获取知识库客户端（延迟初始化）"""
    global _knowledge_client
    if _knowledge_client is None:
        ctx = new_context(method="rag_search")
        _knowledge_client = KnowledgeClient(config=_config, ctx=ctx)
    return _knowledge_client


@tool
def search_questions(
    query: str,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    knowledge_point: Optional[str] = None,
    top_k: int = 5
) -> str:
    """搜索相关题目
    
    当用户需要查找相关题目、搜索练习题、或询问特定知识点时使用此工具。
    
    Args:
        query: 搜索查询，可以是知识点、关键词或问题描述
        question_type: 题目类型筛选，可选值：单选题、多选题、简答题
        difficulty: 难度筛选，可选值：易、中、难
        knowledge_point: 精确知识点筛选，如 "MapReduce"、"Spark Streaming" 等
        top_k: 返回结果数量，默认5条
    
    Returns:
        JSON 格式的搜索结果，包含相关题目列表
    """
    ctx = new_context(method="search_questions")
    client = _get_knowledge_client()
    
    # 构建增强查询
    enhanced_query = query
    if knowledge_point:
        enhanced_query = f"{knowledge_point} {query}"
    
    try:
        # 调用知识库搜索
        response = client.search(
            query=enhanced_query,
            table_names=[DATASET_NAME],
            top_k=top_k,
            min_score=0.3
        )
        
        if response.code != 0:
            return json.dumps({
                'success': False,
                'error': f"搜索失败: {response.msg}",
                'results': []
            }, ensure_ascii=False)
        
        # 处理搜索结果
        results = []
        for chunk in response.chunks:
            # 解析题目内容
            question_data = _parse_question_content(chunk.content)
            if question_data:
                # 应用筛选条件
                if question_type and question_data.get('题型') != question_type:
                    continue
                if difficulty and question_data.get('难度') != difficulty:
                    continue
                
                results.append(question_data)
                
                if len(results) >= top_k:
                    break
        
        return json.dumps({
            'success': True,
            'query': query,
            'count': len(results),
            'results': results
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            'success': False,
            'error': f"搜索异常: {str(e)}",
            'results': []
        }, ensure_ascii=False)


@tool
def get_similar_questions(
    knowledge_point: str,
    count: int = 5,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None
) -> str:
    """获取指定知识点的相似题目
    
    当用户需要针对特定知识点获取练习题时使用。
    
    Args:
        knowledge_point: 知识点名称，如 "Kafka架构"、"Hadoop" 等
        count: 返回题目数量，默认5道
        question_type: 题目类型，可选值：单选题、多选题、简答题
        difficulty: 难度级别，可选值：易、中、难
    
    Returns:
        JSON 格式的题目列表
    """
    ctx = new_context(method="get_similar_questions")
    client = _get_knowledge_client()
    
    try:
        # 搜索该知识点的题目
        response = client.search(
            query=knowledge_point,
            table_names=[DATASET_NAME],
            top_k=count * 2,  # 多取一些用于筛选
            min_score=0.3
        )
        
        if response.code != 0:
            return json.dumps({
                'success': False,
                'error': f"搜索失败: {response.msg}",
                'questions': []
            }, ensure_ascii=False)
        
        # 处理结果
        questions = []
        for chunk in response.chunks:
            question_data = _parse_question_content(chunk.content)
            if question_data:
                # 检查知识点匹配
                if knowledge_point in question_data.get('知识点路径', ''):
                    # 应用筛选
                    if question_type and question_data.get('题型') != question_type:
                        continue
                    if difficulty and question_data.get('难度') != difficulty:
                        continue
                    
                    questions.append(question_data)
                    
                    if len(questions) >= count:
                        break
        
        return json.dumps({
            'success': True,
            'knowledge_point': knowledge_point,
            'count': len(questions),
            'questions': questions
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            'success': False,
            'error': f"搜索异常: {str(e)}",
            'questions': []
        }, ensure_ascii=False)


@tool
def generate_practice_set(
    topic: str,
    count: int = 10,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None
) -> str:
    """生成练习题组
    
    当用户需要生成一组练习题时使用。
    
    Args:
        topic: 主题/领域，如 "Spark"、"Hive"、"Kafka" 等
        count: 题目数量，默认10道
        question_type: 题目类型分布，默认自动混合
        difficulty: 难度级别，默认中等难度为主
    
    Returns:
        JSON 格式的练习题组
    """
    ctx = new_context(method="generate_practice_set")
    client = _get_knowledge_client()
    
    try:
        # 搜索相关题目
        response = client.search(
            query=topic,
            table_names=[DATASET_NAME],
            top_k=count * 3,  # 多取一些用于组合
            min_score=0.3
        )
        
        if response.code != 0:
            return json.dumps({
                'success': False,
                'error': f"搜索失败: {response.msg}",
                'practice_set': []
            }, ensure_ascii=False)
        
        # 处理结果
        practice_set = []
        seen_ids = set()
        
        for chunk in response.chunks:
            question_data = _parse_question_content(chunk.content)
            if question_data:
                qid = question_data.get('题目ID')
                
                # 去重
                if qid and qid in seen_ids:
                    continue
                
                # 应用筛选
                if question_type and question_data.get('题型') != question_type:
                    continue
                if difficulty and question_data.get('难度') != difficulty:
                    continue
                
                practice_set.append(question_data)
                if qid:
                    seen_ids.add(qid)
                
                if len(practice_set) >= count:
                    break
        
        return json.dumps({
            'success': True,
            'topic': topic,
            'count': len(practice_set),
            'practice_set': practice_set
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            'success': False,
            'error': f"生成失败: {str(e)}",
            'practice_set': []
        }, ensure_ascii=False)


@tool
def get_answer_explanation(
    question_content: str
) -> str:
    """获取题目答案和解析
    
    当用户提交答案或询问某道题的解析时使用。
    
    Args:
        question_content: 题目内容（题干）用于匹配题库中的原题
    
    Returns:
        JSON 格式的答案和解析
    """
    ctx = new_context(method="get_answer_explanation")
    client = _get_knowledge_client()
    
    try:
        # 搜索该题目
        response = client.search(
            query=question_content,
            table_names=[DATASET_NAME],
            top_k=1,
            min_score=0.8  # 高相似度匹配
        )
        
        if response.code != 0:
            return json.dumps({
                'success': False,
                'error': f"搜索失败: {response.msg}"
            }, ensure_ascii=False)
        
        if not response.chunks:
            return json.dumps({
                'success': False,
                'error': "未找到该题目"
            }, ensure_ascii=False)
        
        # 解析题目内容
        question_data = _parse_question_content(response.chunks[0].content)
        
        return json.dumps({
            'success': True,
            'answer': question_data.get('答案', ''),
            'explanation': question_data.get('解析', ''),
            'question': question_data
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            'success': False,
            'error': f"查询异常: {str(e)}"
        }, ensure_ascii=False)


def _parse_question_content(content: str) -> Optional[Dict[str, Any]]:
    """解析题目内容
    
    Args:
        content: 题目原始内容
        
    Returns:
        解析后的题目数据字典
    """
    try:
        # 提取各部分
        result = {
            '原始内容': content[:200],
            '题目ID': '',
            '题型': '',
            '难度': '',
            '知识点路径': '',
            '一级知识点': '',
            '二级知识点': '',
            '三级知识点': '',
            '题干': '',
            '选项A': '',
            '选项B': '',
            '选项C': '',
            '选项D': '',
            '选项E': '',
            '答案': '',
            '解析': ''
        }
        
        # 提取题目ID
        id_match = re.search(r'【ID】(\d+)', content)
        if id_match:
            result['题目ID'] = id_match.group(1)
        
        # 提取题型
        type_match = re.search(r'【单选题】|【多选题】|【简答题】', content)
        if type_match:
            result['题型'] = type_match.group(0)[1:-1]
        
        # 提取难度
        diff_match = re.search(r'【(易|中|难)】', content)
        if diff_match:
            result['难度'] = diff_match.group(1)
        
        # 提取知识点路径
        knowledge_match = re.search(r'【知识点】([^【]+)', content)
        if knowledge_match:
            result['知识点路径'] = knowledge_match.group(1).strip()
            # 分解知识点
            parts = result['知识点路径'].split(' > ')
            if len(parts) >= 1:
                result['一级知识点'] = parts[0].strip()
            if len(parts) >= 2:
                result['二级知识点'] = parts[1].strip()
            if len(parts) >= 3:
                result['三级知识点'] = parts[2].strip()
        
        # 提取题干
        question_match = re.search(r'【题干】(.*?)(?=\n【|\Z)', content, re.DOTALL)
        if question_match:
            result['题干'] = question_match.group(1).strip()
        
        # 提取选项
        for option in ['A', 'B', 'C', 'D', 'E']:
            option_match = re.search(rf'【选项{option}】(.*?)(?=\n【|\Z)', content, re.DOTALL)
            if option_match:
                result[f'选项{option}'] = option_match.group(1).strip()
        
        # 提取答案
        answer_match = re.search(r'【答案】(.*?)(?=\n【|\Z)', content, re.DOTALL)
        if answer_match:
            result['答案'] = answer_match.group(1).strip()
        
        # 提取解析
        explanation_match = re.search(r'【解析】(.*?)(?=\n【|\Z)', content, re.DOTALL)
        if explanation_match:
            result['解析'] = explanation_match.group(1).strip()
        
        return result
        
    except Exception:
        return None


# 工具列表
RAG_TOOLS = [
    search_questions,
    get_similar_questions,
    generate_practice_set,
    get_answer_explanation
]
