## Context

前端基于 React 19 + TypeScript 6 + Vite 8。当前所有样式通过 `React.CSSProperties` 内联对象实现，TS6 移除了对伪选择器的类型支持，导致 `:hover` 等交互反馈完全缺失。样式常量（`btnPrimary`、`rowStyle` 等）在 4 个页面文件中重复定义，无共享源。SessionChat 单组件 350 行承载全部聊天功能，存在 2 处数据竞态。

构建工具链已包含 PostCSS（Vite 内置），无需新增依赖即可支持 CSS Modules。

## Goals / Non-Goals

**Goals:**
- 替换所有 `React.CSSProperties` 内联样式为 CSS Modules，恢复 `:hover`/`:focus`/`:active` 支持
- 提取设计 token（颜色、间距、字号、圆角）到单一 CSS 自定义属性文件
- 将 SessionChat 按功能域分解为 3 个子组件
- 通过 AbortController 消除 SSE 流竞态
- 添加全局 ErrorBoundary 防止白屏

**Non-Goals:**
- 不引入 Tailwind / styled-components / UI 组件库
- 不改动路由结构、API 层、后端
- 不改动功能行为（只是实现方式的替换和修复）
- 不添加全局状态管理
- 不做响应式布局适配（非目标，但 CSS 自定义属性为后续留了空间）

## Decisions

### D1: CSS Modules over Tailwind / styled-components

| 方案 | 评价 |
|---|---|
| CSS Modules | ✅ Vite 原生支持，零配置。` composes:` 支持 token 复用。与 JS 并行的独立样式文件，TS6 无冲突。增量为每个组件一个 `.module.css` |
| Tailwind | ❌ 增加配置复杂度（tailwind.config.js + PostCSS 插件）。utility class 记忆成本与现有内联样式等价但语法不同。对 6 个文件的迁移量来说工具太重 |
| styled-components | ❌ 运行时注入开销。TS6 下 `attrs` 泛型可能收紧需要 workaround |
| CSS 文件 + BEM | 可行但无模块作用域隔离，大型项目易冲突 |

**结论**: CSS Modules。No new dependencies. 逐文件迁移，每个文件 <200 行 CSS。

### D2: 设计 token 用 CSS 自定义属性 (custom properties)

```css
/* tokens.css — 设计系统的基础原料 */
:root {
  /* 主色调 */
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-danger: #dc2626;
  --color-text: #1f2937;
  --color-text-secondary: #6b7280;
  --color-text-muted: #9ca3af;
  --color-border: #d1d5db;
  --color-border-light: #e5e7eb;
  --color-bg: #fff;
  --color-bg-hover: #f3f4f6;
  --color-bg-active: #eff6ff;

  /* 字号 */
  --font-size-sm: 12px;
  --font-size-base: 14px;
  --font-size-lg: 16px;

  /* 间距 */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 12px;
  --space-lg: 16px;

  /* 圆角 */
  --radius-sm: 3px;
  --radius-md: 4px;
  --radius-lg: 6px;

  /* 阴影（预留） */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
}
```

理由: 零运行时、浏览器原生、可在 DevTools 中实时调试。与 CSS Modules 的 `composes:` 配合天然。

### D3: SessionChat 分解边界

```
SessionChat (容器)
├── SessionSidebar
│   ├── 会话信息 + 绑定KB
│   └── ParameterPanel (topK/topN/systemPrompt + 保存)
│       └── ChatList (可切换/可删除)
├── ChatArea
│   ├── MessageList (MarkdownMessage × N)
│   └── ChatInput (textarea + 发送按钮)
└── 职责
    ├── SessionChat: 顶层状态协调 + 路由参数 + API 编排
    ├── SessionSidebar: 显示/交互，状态通过父级回调上报
    ├── ParameterPanel: 自包含参数表单 + 保存状态机
    ├── ChatList: 列表渲染 + 选中/删除
    ├── ChatArea: 消息渲染 + 自动滚动
    └── ChatInput: 输入框 + Enter/Shift+Enter + 发送按钮
```

**为什么用回调而非 Context/Store**: 目前只有两层传递，状态总量可控（~13 个），引入 Context 会增加不必要的间接层。等 SessionChat 再增长一倍时再考虑。

### D4: AbortController 模式

当前 SSE 流 (`chatStream`) 无中止机制。模式设计：

```
SessionChat 层:
  const abortRef = useRef<AbortController | null>(null)

  handleSubmit():
    abortRef.current?.abort()          // 中止上一个
    abortRef.current = new AbortController()
    sessionApi.chatStream(..., {       // signal 传入 fetch
      signal: abortRef.current.signal
    })

  // 切换聊天时自动中止
  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [activeChat])

api/index.ts 层:
  chatStream(..., signal):
    fetch(url, { signal, ... })        // 浏览器原生中止 SSE
```

不修改 `api/index.ts` 的其他函数。`signal` 作为可选参数追加到 `chatStream`。

### D5: 聊天删除竞态修复

```diff
  const handleDeleteChat = async (chatFile: string) => {
    await sessionApi.deleteChat(name, chatFile);
-   load();
-   setActiveChat(chats.filter(...));
+   const updated = await sessionApi.listChats(name);  // 重新获取最新列表
+   setChats(updated.chats);
+   const remaining = updated.chats.filter(x => x.file !== chatFile);
+   setActiveChat(remaining.length > 0 ? remaining[0].file : null);
+   if (remaining.length === 0) setMessages([]);
  };
```

核心思路：删除后不依赖本地 `chats` 状态计算下一个，而是直接从服务器取最新数据。

### D6: ErrorBoundary 布局

```
<BrowserRouter>
  <ErrorBoundary>       ← 包裹所有路由，捕获渲染异常
    <NavBar />
    <main>
      <Routes>...</Routes>
    </main>
  </ErrorBoundary>
</BrowserRouter>
```

`ErrorBoundary` 渲染一个简化的错误页面 + "重新加载"按钮。不放回 Fallback UI，因为单页面应用适合整页回退。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|---|---|
| CSS Modules 和现有内联样式混用导致优先级冲突 | 策略：一次性迁移一个文件，迁移完成后移除对应的内联对象。不存在长期混用 |
| 组件分解后状态提升导致 SessionChat 仍臃肿 | 设计已刻意保持回调扁平，父级只做转发不处理业务逻辑。如仍臃肿，下一步考虑 Context |
| AbortController 接入后 `chatStream` 的 `catch` 路径需处理 `AbortError` | `chatStream` 内对 `AbortError` 静默忽略，不触发 `onError` |
| `*.module.css` 需要 TypeScript 类型声明 | 一条全局声明 `declare module '*.module.css' { const x: Record<string, string>; export default x }` 即可 |

## Open Questions

1. `types/` 目录从 `api/index.ts` 分离类型定义属于"可以顺手做"但不是必须。是否纳入本次变更？
