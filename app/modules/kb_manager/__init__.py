"""知识库管理模块。

- KnowledgeBase: 知识库创建、文件/文件夹管理
- KnowledgeBaseError: 操作异常
"""

from app.modules.kb_manager.knowledge_base import KnowledgeBase, KnowledgeBaseError, KnowledgeBasePathError

__all__ = ["KnowledgeBase", "KnowledgeBaseError", "KnowledgeBasePathError"]
