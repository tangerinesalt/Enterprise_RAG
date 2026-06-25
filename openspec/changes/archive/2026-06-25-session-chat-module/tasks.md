## 1. 模块结构准备

- [x] 1.1 创建 `app/modules/session/` 模块（`__init__.py` + `session_manager.py`）
- [x] 1.2 更新 `.gitignore`：添加 `sessions/`（运行时数据）

## 2. SessionManager 实现

- [x] 2.1 实现 `create(name)`：创建会话目录结构
- [x] 2.2 实现 `bind(name, kb_name)`：写入 config.json，验证 KB 存在
- [x] 2.3 实现 `list_all()`：列出所有会话
- [x] 2.4 实现 `list_chats(name)`：列出会话的聊天文件
- [x] 2.5 实现 `_ensure_exists(name)` / `_load_config(name)` / `_save_config(name, data)`
- [x] 2.6 实现 `_gen_chat_filename()`：按时间生成文件名，处理冲突

## 3. 聊天功能

- [x] 3.1 实现 `chat(name, query)`：加载 SimpleChatStore → 追加用户消息
- [x] 3.2 加载绑定 KB 的 ChromaDB → 检索 top-5
- [x] 3.3 调用 LLM 生成回答 → 追加助手消息（含来源）
- [x] 3.4 persist 到 chat JSON 文件
- [x] 3.5 print 回答 + 来源到控制台

## 4. CLI 集成

- [x] 4.1 在 `cli.py` 中添加 `session` 子命令组（create / bind / delete / info / list / new / select / chat）
- [x] 4.2 更新帮助文本和示例

## 5. 验证

- [x] 5.1 创建会话：`session create test-session`
- [x] 5.2 绑定知识库：`session bind test-session test-kb`
- [x] 5.3 聊天测试：`session chat test-session "内容？"`
- [x] 5.4 验证聊天文件已生成且可读
- [x] 5.5 验证多轮对话上下文保持
