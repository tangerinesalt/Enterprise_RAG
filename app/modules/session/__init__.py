"""会话管理模块。

- SessionManager: 会话创建、绑定、聊天、持久化
- SessionError: 操作异常
"""

from app.modules.session.session_manager import SessionManager, SessionError, SessionPathError

__all__ = ["SessionManager", "SessionError", "SessionPathError"]
