"""
题库知识库导入脚本
将预处理后的题库导入到知识库
"""

import json
import time
from typing import List, Dict, Any
from coze_coding_dev_sdk import KnowledgeClient, Config, KnowledgeDocument, DataSourceType, ChunkConfig
from coze_coding_utils.runtime_ctx.context import new_context


class QuestionBankImporter:
    """题库知识库导入工具"""
    
    # 数据集名称
    DATASET_NAME = "bigdata_question_bank"
    
    def __init__(self):
        """初始化导入工具"""
        self.ctx = new_context(method="question_bank_import")
        self.config = Config()
        self.client = KnowledgeClient(config=self.config, ctx=self.ctx, verbose=True)
        self.documents = []
        
    def load_documents(self, file_path: str = 'assets/question_bank_rag.json') -> List[Dict]:
        """加载预处理后的文档
        
        Args:
            file_path: JSON 文件路径
            
        Returns:
            文档列表
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            self.documents = json.load(f)
        
        print(f"✅ 加载文档成功，共 {len(self.documents)} 个文档")
        return self.documents
    
    def _create_knowledge_document(self, doc: Dict) -> KnowledgeDocument:
        """创建知识库文档对象
        
        Args:
            doc: 文档数据
            
        Returns:
            KnowledgeDocument 对象
        """
        return KnowledgeDocument(
            source=DataSourceType.TEXT,
            raw_data=doc['content'],
        )
    
    def import_to_knowledge_base(self, batch_size: int = 50) -> Dict[str, Any]:
        """批量导入文档到知识库
        
        Args:
            batch_size: 每批导入数量
            
        Returns:
            导入结果统计
        """
        if not self.documents:
            print("❌ 没有文档，请先调用 load_documents()")
            return {'success': False, 'error': 'No documents loaded'}
        
        total = len(self.documents)
        imported = 0
        failed = 0
        all_doc_ids = []
        
        print(f"\n🚀 开始导入 {total} 个文档到知识库...")
        print(f"   数据集名称: {self.DATASET_NAME}")
        print(f"   批次大小: {batch_size}")
        print("-" * 50)
        
        # 分批导入
        for i in range(0, total, batch_size):
            batch = self.documents[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            print(f"\n📦 正在导入第 {batch_num}/{total_batches} 批 ({len(batch)} 个文档)...")
            
            # 转换为 KnowledgeDocument
            knowledge_docs = [self._create_knowledge_document(doc) for doc in batch]
            
            try:
                # 调用导入 API
                response = self.client.add_documents(
                    documents=knowledge_docs,
                    table_name=self.DATASET_NAME,
                    chunk_config=ChunkConfig(
                        separator="\n\n",
                        max_tokens=2000,
                        remove_extra_spaces=True
                    )
                )
                
                if response.code == 0:
                    imported += len(batch)
                    if response.doc_ids:
                        all_doc_ids.extend(response.doc_ids)
                    print(f"   ✅ 第 {batch_num} 批导入成功")
                else:
                    failed += len(batch)
                    print(f"   ❌ 第 {batch_num} 批导入失败: {response.msg}")
                
                # 避免请求过快
                if i + batch_size < total:
                    time.sleep(0.5)
                    
            except Exception as e:
                failed += len(batch)
                print(f"   ❌ 第 {batch_num} 批导入异常: {str(e)}")
        
        result = {
            'success': failed == 0,
            'total': total,
            'imported': imported,
            'failed': failed,
            'doc_ids': all_doc_ids,
            'dataset_name': self.DATASET_NAME
        }
        
        print("\n" + "=" * 50)
        print("📊 导入结果统计：")
        print(f"   总计: {result['total']}")
        print(f"   成功: {result['imported']}")
        print(f"   失败: {result['failed']}")
        print("=" * 50)
        
        return result
    
    def search_sample(self, query: str = "Spark架构", top_k: int = 3):
        """搜索示例
        
        Args:
            query: 搜索查询
            top_k: 返回数量
        """
        print(f"\n🔍 搜索示例: '{query}'")
        print("-" * 50)
        
        try:
            response = self.client.search(
                query=query,
                table_names=[self.DATASET_NAME],
                top_k=top_k,
                min_score=0.5
            )
            
            if response.code == 0:
                print(f"✅ 找到 {len(response.chunks)} 条结果：\n")
                for i, chunk in enumerate(response.chunks):
                    print(f"【结果 {i+1}】(相似度: {chunk.score:.4f})")
                    print(chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content)
                    print()
            else:
                print(f"❌ 搜索失败: {response.msg}")
                
        except Exception as e:
            print(f"❌ 搜索异常: {str(e)}")


def main():
    """主函数"""
    # 创建导入工具
    importer = QuestionBankImporter()
    
    # 加载文档
    importer.load_documents()
    
    # 导入到知识库
    result = importer.import_to_knowledge_base(batch_size=50)
    
    if result['success']:
        # 搜索示例
        importer.search_sample("MapReduce")
        print("\n✅ 题库导入完成！")
    else:
        print(f"\n❌ 导入失败，请检查错误信息")


if __name__ == '__main__':
    main()
