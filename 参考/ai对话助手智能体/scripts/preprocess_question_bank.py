"""
题库 RAG 预处理脚本
将 Excel 题库转换为知识库可导入的文档格式
"""

import pandas as pd
import json
import os
from typing import List, Dict, Any


class QuestionBankPreprocessor:
    """题库预处理工具"""
    
    def __init__(self, file_path: str):
        """初始化预处理器
        
        Args:
            file_path: Excel 文件路径
        """
        self.file_path = file_path
        self.df = None
        self.documents = []
        
    def load_data(self) -> pd.DataFrame:
        """加载题库数据"""
        self.df = pd.read_excel(self.file_path, sheet_name='统一题库')
        print(f"✅ 加载题库成功，共 {len(self.df)} 道题目")
        return self.df
    
    def _format_single_choice(self, row: pd.Series) -> str:
        """格式化单选题"""
        options = []
        for opt in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            val = row.get(f'选项{opt}')
            if pd.notna(val):
                options.append(f"{opt}. {val}")
        
        return f"""【单选题】
知识点：{row['一级知识点']} > {row['二级知识点']} > {row['三级知识点']}
难度：{row['难度']}
题目：{row['题干']}
选项：
{chr(10).join(options)}
答案：{row['答案']}"""
    
    def _format_multiple_choice(self, row: pd.Series) -> str:
        """格式化多选题"""
        options = []
        for opt in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            val = row.get(f'选项{opt}')
            if pd.notna(val):
                options.append(f"{opt}. {val}")
        
        return f"""【多选题】
知识点：{row['一级知识点']} > {row['二级知识点']} > {row['三级知识点']}
难度：{row['难度']}
题目：{row['题干']}
选项：
{chr(10).join(options)}
答案：{row['答案']}"""
    
    def _format_essay(self, row: pd.Series) -> str:
        """格式化简答题"""
        return f"""【简答题】
知识点：{row['一级知识点']} > {row['二级知识点']} > {row['三级知识点']}
难度：{row['难度']}
题目：{row['题干']}

答案解析：
{row['答案']}"""
    
    def process(self) -> List[Dict[str, Any]]:
        """处理所有题目，生成知识库文档
        
        Returns:
            文档列表，每个文档包含 id 和 content
        """
        if self.df is None:
            self.load_data()
        
        self.documents = []
        
        for idx, row in self.df.iterrows():
            qid = int(row['ID'])
            qtype = row['题型']
            
            # 根据题型格式化
            if qtype == '单选题':
                content = self._format_single_choice(row)
            elif qtype == '多选题':
                content = self._format_multiple_choice(row)
            elif qtype == '简答题':
                content = self._format_essay(row)
            else:
                content = f"【{qtype}】\n{row['题干']}\n答案：{row['答案']}"
            
            # 添加标签
            if pd.notna(row.get('标签')):
                content += f"\n标签：{row['标签']}"
            
            # 添加题目功能
            if pd.notna(row.get('题目功能')):
                content += f"\n用途：{row['题目功能']}"
            
            self.documents.append({
                'id': qid,
                'type': qtype,
                'knowledge_level1': row['一级知识点'],
                'knowledge_level2': row['二级知识点'],
                'knowledge_level3': row['三级知识点'],
                'difficulty': row['难度'],
                'content': content
            })
        
        print(f"✅ 处理完成，共生成 {len(self.documents)} 个文档")
        return self.documents
    
    def export_to_json(self, output_path: str = 'assets/question_bank_rag.json'):
        """导出为 JSON 文件
        
        Args:
            output_path: 输出文件路径
        """
        if not self.documents:
            self.process()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 导出成功：{output_path}")
        return output_path
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取题库统计信息"""
        if self.df is None:
            self.load_data()
        
        return {
            'total': len(self.df),
            'by_type': self.df['题型'].value_counts().to_dict(),
            'by_difficulty': self.df['难度'].value_counts().to_dict(),
            'by_knowledge': self.df['一级知识点'].value_counts().to_dict(),
        }


def main():
    """主函数"""
    # 文件路径
    file_path = 'assets/统一题库.xlsx'
    output_path = 'assets/question_bank_rag.json'
    
    # 创建预处理器
    preprocessor = QuestionBankPreprocessor(file_path)
    
    # 加载数据
    preprocessor.load_data()
    
    # 打印统计信息
    stats = preprocessor.get_statistics()
    print("\n📊 题库统计：")
    print(f"   总题数：{stats['total']}")
    print(f"   按题型：{stats['by_type']}")
    print(f"   按难度：{stats['by_difficulty']}")
    
    # 处理并导出
    preprocessor.process()
    preprocessor.export_to_json(output_path)
    
    print("\n✅ 预处理完成！")
    return preprocessor.documents


if __name__ == '__main__':
    main()
