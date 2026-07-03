## 1. 基础设施

- [x] 1.1 创建 `ui/src/styles/tokens.css`，定义全部设计 token（颜色/间距/字号/圆角/阴影）
- [x] 1.2 添加 TypeScript CSS Modules 类型声明（`ui/src/vite-env.d.ts` 或新 `.d.ts` 文件）
- [x] 1.3 创建 `ui/src/components/ErrorBoundary.tsx` 错误边界组件
- [x] 1.4 在 `App.tsx` 中用 ErrorBoundary 包裹路由，验证白屏保护

## 2. CSS Modules 迁移 — 简单组件

- [x] 2.1 `NavBar` → 创建 `NavBar.module.css`，替换内联样式，添加 hover/focus 支持
- [x] 2.2 `KbList` → 创建 `KbList.module.css`，替换内联样式，添加行 hover 反馈
- [x] 2.3 `KbDetail` → 创建 `KbDetail.module.css`，替换内联样式
- [x] 2.4 `SessionList` → 创建 `SessionList.module.css`，替换内联样式，添加行 hover 反馈
- [x] 2.5 `MarkdownMessage` → 创建 `MarkdownMessage.module.css`，替换内联样式，代码块/表格样式 token 化

## 3. SessionChat 组件分解

- [x] 3.1 创建 `ui/src/components/SessionSidebar.tsx` + `SessionSidebar.module.css`
- [x] 3.2 创建 `ui/src/components/ChatList.tsx` + `ChatList.module.css`
- [x] 3.3 创建 `ui/src/components/ParameterPanel.tsx` + `ParameterPanel.module.css`
- [x] 3.4 创建 `ui/src/components/ChatArea.tsx` + `ChatArea.module.css`
- [x] 3.5 创建 `ui/src/components/ChatInput.tsx` + `ChatInput.module.css`
- [x] 3.6 重构 `SessionChat.tsx`：集成子组件、状态通过回调下发、移除内联样式

## 4. 数据可靠性修复

- [x] 4.1 `chatStream` 添加 `AbortController` 参数传递（`api/index.ts`）
- [x] 4.2 `SessionChat.handleSubmit` 实现前一个流中止逻辑
- [x] 4.3 聊天切换时自动中止当前流（`useEffect` cleanup）
- [x] 4.4 修复聊天删除竞态：删除后从服务器获取最新列表再计算 `activeChat`
- [x] 4.5 验证快速连续发送、中途切换聊天、删除最后一聊天的场景
