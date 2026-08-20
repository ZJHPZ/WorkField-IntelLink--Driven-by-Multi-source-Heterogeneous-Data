"""
文档与思维导图生成工具模块
功能：生成知识点文档和思维导图
"""
import json
from typing import Optional
from langchain.tools import tool
from storage.database.supabase_client import get_supabase_client
from postgrest.exceptions import APIError
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def save_learning_content(subject: str, topic: str, content_type: str, content_data: str) -> str:
    """
    保存学习内容到数据库。
    
    Args:
        subject: 学习科目
        topic: 知识点主题
        content_type: 内容类型 (document/mindmap/question/multimedia)
        content_data: 内容详情 (JSON格式字符串)
    
    Returns:
        保存结果信息
    """
    ctx = request_context.get() or new_context(method="save_learning_content")
    
    try:
        client = get_supabase_client()
        
        data = {
            "subject": subject,
            "topic": topic,
            "content_type": content_type,
            "content_data": json.loads(content_data) if isinstance(content_data, str) else content_data
        }
        
        response = client.table("learning_contents").insert(data).execute()
        data_list = list(response.data) if response.data else []
        content_id = data_list[0].get("id") if data_list and isinstance(data_list[0], dict) else None
        return json.dumps({
            "success": True,
            "message": f"学习内容已保存",
            "content_id": content_id,
            "subject": subject,
            "topic": topic,
            "content_type": content_type
        }, ensure_ascii=False)
    
    except APIError as e:
        raise Exception(f"保存学习内容失败: {e.message}")


@tool
def get_learning_content(subject: str, topic: Optional[str] = None, content_type: Optional[str] = None) -> str:
    """
    获取学习内容。
    
    Args:
        subject: 学习科目
        topic: 知识点主题（可选）
        content_type: 内容类型（可选）
    
    Returns:
        学习内容列表（JSON格式）
    """
    ctx = request_context.get() or new_context(method="get_learning_content")
    
    try:
        client = get_supabase_client()
        
        query = client.table("learning_contents") \
            .select("*") \
            .eq("subject", subject)
        
        if topic:
            query = query.eq("topic", topic)
        if content_type:
            query = query.eq("content_type", content_type)
        
        response = query.execute()
        
        return json.dumps({
            "subject": subject,
            "topic": topic,
            "content_type": content_type,
            "count": len(response.data),
            "contents": response.data
        }, ensure_ascii=False, indent=2)
    
    except APIError as e:
        raise Exception(f"获取学习内容失败: {e.message}")


@tool
def generate_document_outline(subject: str, topic: str, depth: int = 3) -> str:
    """
    生成知识点的文档大纲结构。
    
    Args:
        subject: 学习科目
        topic: 知识点主题
        depth: 大纲深度（1-5）
    
    Returns:
        文档大纲（Markdown格式）
    """
    ctx = request_context.get() or new_context(method="generate_document_outline")
    
    # 生成文档大纲提示
    outline = f"""# {topic} - 知识文档大纲

## 一、基础概念
### 1.1 定义与背景
### 1.2 核心术语解释
### 1.3 基本原理

## 二、核心知识点
### 2.1 重点内容1
### 2.2 重点内容2
### 2.3 重点内容3

## 三、实践应用
### 3.1 应用场景1
### 3.2 应用场景2
### 3.3 案例分析

## 四、进阶拓展
### 4.1 相关知识点
### 4.2 延伸阅读
### 4.3 发展趋势

## 五、总结与练习
### 5.1 核心要点回顾
### 5.2 自测题
### 5.3 实践作业
"""
    
    return json.dumps({
        "subject": subject,
        "topic": topic,
        "depth": depth,
        "outline": outline,
        "message": "已生成文档大纲，请根据大纲内容填充详细内容"
    }, ensure_ascii=False, indent=2)


@tool
def generate_mindmap_structure(subject: str, topic: str, complexity: str = "medium") -> str:
    """
    生成思维导图的结构化数据（用于知识梳理，不生成图片）。
    
    ⚠️ 注意：此工具只生成思维导图的 JSON 结构，不生成真实图片！
    如果用户需要展示架构图、流程图等，请使用 generate_concept_diagram 或 generate_illustration_image 工具！
    
    Args:
        subject: 学习科目
        topic: 知识点主题
        complexity: 复杂度 (simple/medium/complex)
    
    Returns:
        思维导图结构（JSON格式，可用于前端渲染）
    """
    ctx = request_context.get() or new_context(method="generate_mindmap_structure")
    
    # 根据复杂度调整分支数量
    branch_counts = {
        "simple": 3,
        "medium": 5,
        "complex": 8
    }
    
    num_branches = branch_counts.get(complexity, 5)
    
    # 生成思维导图JSON结构
    mindmap_data = {
        "name": topic,
        "children": [
            {
                "name": f"分支{i+1}",
                "children": [
                    {"name": f"子节点{j+1}"}
                    for j in range(min(num_branches, 4))
                ]
            }
            for i in range(num_branches)
        ]
    }
    
    return json.dumps({
        "subject": subject,
        "topic": topic,
        "complexity": complexity,
        "mindmap": mindmap_data,
        "mindmap_markdown": f"# {topic}\n\n- 分支1\n  - 子节点1\n  - 分支2\n  - 分支3\n  - 分支4\n  - 分支5\n\n**提示**: 请使用可视化工具渲染上述JSON结构生成思维导图",
        "message": "已生成思维导图结构，请使用前端组件渲染"
    }, ensure_ascii=False, indent=2)


@tool
def generate_full_document(subject: str, topic: str, include_mindmap: bool = True) -> str:
    """
    生成完整的知识点文档，包含详细内容和大纲。
    
    Args:
        subject: 学习科目
        topic: 知识点主题
        include_mindmap: 是否包含思维导图
    
    Returns:
        完整文档内容（Markdown格式）
    """
    ctx = request_context.get() or new_context(method="generate_full_document")
    
    # 生成完整文档模板
    document = f"""# {topic}

> 学习科目：{subject}  
> 生成时间：自动生成

## 摘要
本文档详细介绍{topic}的核心知识点，帮助学习者系统掌握相关内容。

---

## 一、基础概念

### 1.1 定义
{topic}是指...

### 1.2 核心术语
- **术语1**: 解释
- **术语2**: 解释
- **术语3**: 解释

### 1.3 历史背景
[背景介绍]

---

## 二、核心知识点

### 2.1 重点一
[详细内容]

### 2.2 重点二
[详细内容]

### 2.3 重点三
[详细内容]

---

## 三、实践应用

### 3.1 应用场景
[场景描述]

### 3.2 案例分析
**案例**: [案例名称]
**分析**: [分析内容]

---

## 四、思维导图

"""
    
    if include_mindmap:
        mindmap_structure = """```
{template}
```
[提示]: 可使用在线思维导图工具导入上述结构
"""
        document += mindmap_structure
    
    document += """
---

## 五、练习题

### 选择题
1. [题目1]
2. [题目2]

### 简答题
1. [题目1]
2. [题目2]

---

## 六、参考资料

1. [参考资料1]
2. [参考资料2]

---

**文档生成完成！请根据实际学习内容填充详细内容。**
"""
    
    return json.dumps({
        "subject": subject,
        "topic": topic,
        "include_mindmap": include_mindmap,
        "document": document,
        "word_count_estimate": len(document),
        "message": "已生成完整文档模板，请填充详细内容"
    }, ensure_ascii=False, indent=2)
