## 1. 回归测试基线

- [x] 1.1 补充同步聊天失败回归测试，锁定“保留首问 + 保留助手错误消息”行为
- [x] 1.2 补充流式聊天失败与 SSE 结构化错误负载测试，锁定 `code/category/message` 契约
- [x] 1.3 补充同会话并发写入测试，锁定配置文件与聊天文件保持有效 JSON 的基线

## 2. 聊天语义收敛

- [x] 2.1 提取同步与流式聊天共享的执行步骤，统一创建/选择 chat、首问持久化、错误消息持久化语义
- [x] 2.2 调整 `SessionManager.chat()`，使其在失败场景下与 `chat_stream()` 对齐，不再留下空聊天或丢失首问
- [x] 2.3 保持 `/api/session/chat` 现有错误包装不变，同时验证其失败持久化语义已与流式路径对齐

## 3. 会话存储安全

- [x] 3.1 为会修改会话文件系统状态的路径引入每会话进程内锁，覆盖 `new_chat`、`select_chat`、`delete(chat_file)`、`update_config`、`chat()`、`chat_stream()`
- [x] 3.2 将 `config.json` 写入改为临时文件加原子替换，并确保 `chat_previews`、`active_chat` 等字段通过同一持久化路径提交
- [x] 3.3 验证并修正锁引入后的关键写路径，避免死锁和明显的锁范围遗漏

## 4. 结构化错误协议与前端适配

- [x] 4.1 在后端定义并映射最小错误码集合：`KB_NOT_BOUND`、`KB_NOT_FOUND`、`KB_INDEX_MISSING`、`KB_VECTOR_EMPTY`、`MODEL_UNAVAILABLE`、`RUNTIME_ERROR`
- [x] 4.2 扩展 `/api/session/chat/stream` 的 SSE `error` 负载，加入稳定的 `code`、`category` 和保留 `message`
- [x] 4.3 更新 `ui/src/api/index.ts` 与 `SessionChat`，改为基于 `code/category` 分支显示 KB、模型和通用错误，并保留 `message` 作为展示文案

## 5. 验证与收口

- [x] 5.1 运行后端单元/集成测试，确认聊天失败语义、结构化错误事件和并发写入回归全部通过
- [x] 5.2 运行前端构建与类型检查，确认结构化错误适配未破坏会话页
- [x] 5.3 复核 proposal、design、specs 与实现结果一致，确保无遗留开放问题再进入 apply/implementation
