## Why

React 19 + Vite 8 + TypeScript 6 toolchain 已就位，但前端样式方案停留在 `React.CSSProperties` 内联对象模式。TypeScript 6 类型系统拒绝伪选择器（`:hover`、`:focus` 等），导致所有交互反馈缺失，且样式常量在 4 个页面文件中重复定义。同时 SessionChat 单组件膨胀至 350 行/13 个状态变量，存在 2 处数据竞态。当前阶段修复这些问题，为后续功能增长建立可靠基础。

## What Changes

- **样式方案迁移**：内联 `React.CSSProperties` → CSS Modules，所有交互组件获得 `:hover`/`:focus`/`:active` 支持
- **共享设计常量**：提取颜色/间距/按钮/输入框等设计 token 到单一源，消除 4 个文件中的重复定义
- **SessionChat 组件分解**：350 行单组件 → Sidebar（左栏）+ ChatPanel（聊天区）+ ParameterPanel（检索参数面板），每个子组件自带 `.module.css`
- **SSE 流中止控制**：`AbortController` 管理流式请求，防止快速操作和聊天切换时的数据竞态
- **修复聊天删除竞态**：`load()` 异步未 await 导致的过期状态计算
- **添加 ErrorBoundary**：全局渲染异常捕获，防止白屏

### 不做的事

- 不改动路由结构（4 条平铺路由保持）
- 不改动 API 通信层（`api/index.ts` 保持不变）
- 不引入全局状态管理（仍用本地 `useState`）
- 不替换 UI 框架（无 shadcn/ui、Ant Design 等）

## Capabilities

### New Capabilities

- `ui-style-system`: CSS Modules 迁移方案、设计 token 定义、组件样式编写规范
- `ui-chat-reliability`: SSE 流中止、竞态修复、前端错误边界

### Modified Capabilities

*无 — 本次变更不改变功能需求，只改变实现方式。*

## Impact

| 模块 | 影响 |
|---|---|
| `ui/src/pages/KbList.tsx` | 样式抽取到 `.module.css`，移除 `btnPrimary`/`btnSec`/`rowStyle` 等内联常量 |
| `ui/src/pages/KbDetail.tsx` | 同上 |
| `ui/src/pages/SessionList.tsx` | 同上 |
| `ui/src/pages/SessionChat.tsx` | 样式抽取 + 组件分解 + 竞态修复 |
| `ui/src/components/NavBar.tsx` | 样式抽取 |
| `ui/src/components/MarkdownMessage.tsx` | 样式抽取 |
| `ui/src/api/index.ts` | 无变更 |
| `ui/src/index.css` | 保留，补充少量全局工具类 |
| 新增 `ui/src/styles/tokens.css` | 设计 token 定义 |
| 新增 `ui/src/components/` 文件 | Sidebar、ChatPanel、ParameterPanel、ErrorBoundary |
| 新增 `ui/src/types/` | 类型定义从 `api/index.ts` 分离（可选） |
