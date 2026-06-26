## Why

FastAPI 后端已完整（知识库 + 会话 + 聊天），但只有 CLI 和 curl 可用。需要提供 React Web 界面，让用户通过浏览器管理知识库、进行对话。界面参考 RAGFlow 的设计风格。

## What Changes

- 新增 `ui/` 目录 — React + TypeScript + Vite 前端项目
- 顶部导航栏（知识库 / 会话），高亮当前模块并可点击切换
- **知识库模块**：
  - 列表页：显示所有知识库，支持创建和删除
  - 详情页：显示库内文件/文件夹，支持上传、删除、索引操作
- **会话模块**：
  - 列表页：显示所有会话，支持创建和删除
  - 详情页：左右双栏布局
    - 左栏：会话名 → 绑定 KB → 新聊天按钮 → 聊天列表
    - 右栏：消息展示（最新优先，滚动加载历史）+ 输入框
    - 输入：Enter 提交，Shift+Enter 换行
- 通过 Vite proxy 对接后端 FastAPI（`/api/*` → `localhost:8000`）

## Capabilities

### New Capabilities
- `ui-kb-page`: 知识库列表与详情页面（文件/文件夹管理）
- `ui-session-page`: 会话列表与聊天双栏页面
- `ui-layout`: 顶部导航 + 路由布局

### Modified Capabilities

- 无（UI 层不修改后端代码）

## Impact

- 新增 `ui/` 目录（React + Vite + TypeScript）
- 新增 `ui/src/` 组件、页面、路由
- 后端无修改，API 已就位
- 新增 `requirements-web.txt` 中 `node` 和 `npm` 为运行依赖
