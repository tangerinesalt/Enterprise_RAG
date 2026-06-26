## 1. 项目脚手架

- [x] 1.1 `npm create vite@latest ui -- --template react-ts`
- [x] 1.2 配置 `vite.config.ts`：proxy `/api` → `localhost:8000`
- [x] 1.3 安装依赖：react-router-dom
- [x] 1.4 创建目录结构：`src/api/` `src/pages/` `src/components/`

## 2. API 封装层

- [x] 2.1 实现 `src/api/index.ts`：封装所有 kb 端点（list/create/delete）
- [x] 2.2 实现 session 端点（list/create/delete/bind）
- [x] 2.3 实现 chat 端点（new/select/chat/list chats/get messages）

## 3. 导航与布局

- [x] 3.1 实现 `App.tsx`：React Router 路由配置
- [x] 3.2 实现 `NavBar.tsx`：顶部导航（知识库/会话），高亮当前模块
- [x] 3.3 整体布局样式

## 4. 知识库列表页

- [x] 4.1 实现 `KbList.tsx`：显示所有知识库，创建/删除操作
- [x] 4.2 删除确认弹窗

## 5. 知识库详情页

- [x] 5.1 实现 `KbDetail.tsx`：文件/文件夹列表
- [x] 5.2 文件上传功能（多文件选择）
- [x] 5.3 文件夹上传功能（webkitdirectory）
- [x] 5.4 文件/文件夹索引按钮
- [x] 5.5 文件/文件夹删除按钮
- [x] 5.6 索引全部按钮

## 6. 会话列表页

- [x] 6.1 实现 `SessionList.tsx`：显示所有会话，创建/删除

## 7. 会话聊天页

- [x] 7.1 实现 `SessionChat.tsx`：双栏布局
- [x] 7.2 左栏：会话名 + KB 绑定 + 新聊天按钮 + 聊天列表
- [x] 7.3 绑定知识库弹窗
- [x] 7.4 右栏：消息展示（滚动加载）
- [x] 7.5 聊天文件切换：左栏点击聊天 → 右栏加载消息
- [x] 7.6 输入框：Enter 提交，Shift+Enter 换行，提交按钮
- [x] 7.7 新聊天：左侧新建 → 右侧空白

## 8. 验证

- [x] 8.1 `npm run dev` 启动正常（build 通过 ✅）
- [ ] 8.2 知识库列表 → 详情 → 上传 → 索引 全流程（需启动后端）
- [ ] 8.3 会话列表 → 进入 → 聊天 → 切换聊天 全流程（需启动后端）
