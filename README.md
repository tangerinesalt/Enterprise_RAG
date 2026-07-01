# RAG V

企业级 RAG 应用 MVP。项目提供知识库管理、文档上传与索引、会话管理、基于知识库的问答，以及一个 React + FastAPI 的 Web 界面。

## 功能介绍

- 知识库管理：创建、删除、查看知识库。
- 文档管理：上传文件或文件夹到知识库，支持通过 CLI 或 Web 操作。
- 向量索引：基于 LlamaIndex + ChromaDB 建立知识库索引。
- RAG 问答：会话绑定知识库后，按用户问题检索相关片段并调用 LLM 生成回答。
- 会话与聊天记录：支持创建会话、新建聊天、切换历史聊天、查看聊天记录。
- Web 服务：FastAPI 后端提供 REST API，Vite + React 前端提供知识库和会话页面。

## 运行依赖

- Python 3.13 或兼容版本。
- Node.js / npm。
- 默认使用本地 Ollama 服务（`http://127.0.0.1:11434/`）。也支持 DeepSeek 和 OpenAI。
- 默认模型配置在 `settings.json`：
  - LLM Provider：`ollama`（可选 `deepseek`、`openai`）
  - LLM 模型：`qwen3.5:9b`
  - Embedding：`qwen3-embedding:4b`

使用 DeepSeek 或 OpenAI：
```json
{"env": {"LLM_PROVIDER": "deepseek", "LLM_MODEL": "deepseek-chat", "LLM_TOKEN": "sk-..."}}
{"env": {"LLM_PROVIDER": "openai",   "LLM_MODEL": "gpt-4o",       "LLM_TOKEN": "sk-..."}}
```

如果本机 Ollama 没有这些模型，页面可以打开，但索引或对话会失败。先用下面命令检查：

```powershell
ollama list
```

## 安装

后端依赖：

```powershell
cd C:\Users\tangerine\.rag_v
pip install -r requirements-web.txt
```

前端依赖：

```powershell
cd C:\Users\tangerine\.rag_v\ui
npm install
```

## 启动服务

### 本机访问

后端：

```powershell
cd C:\Users\tangerine\.rag_v
python -m uvicorn app.api.server:app --host 127.0.0.1 --port 8000
```

前端另开一个 PowerShell：

```powershell
cd C:\Users\tangerine\.rag_v\ui
npm run dev -- --host 127.0.0.1
```

访问地址：

```text
http://127.0.0.1:5173/
```

### 局域网访问

后端：

```powershell
cd C:\Users\tangerine\.rag_v
python -m uvicorn app.api.server:app --host 0.0.0.0 --port 8000
```

前端另开一个 PowerShell：

```powershell
cd C:\Users\tangerine\.rag_v\ui
npm run dev -- --host 0.0.0.0
```

查看本机局域网 IP：

```powershell
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown' } |
  Select-Object InterfaceAlias,IPAddress
```

其他机器访问：

```text
http://<本机局域网IP>:5173/
```

例如：

```text
http://192.168.1.68:5173/
```

如果其他机器无法访问，检查 Windows 防火墙是否允许 `5173` 和 `8000` 入站。

## 后台启动

如果希望服务在后台运行，并把日志写入 `logs/`：

```powershell
cd C:\Users\tangerine\.rag_v

Start-Process -FilePath python `
  -ArgumentList @('-m','uvicorn','app.api.server:app','--host','0.0.0.0','--port','8000') `
  -WorkingDirectory (Get-Location) `
  -RedirectStandardOutput logs\dev-backend.out.log `
  -RedirectStandardError logs\dev-backend.err.log `
  -WindowStyle Hidden

Start-Process -FilePath npm.cmd `
  -ArgumentList @('run','dev','--','--host','0.0.0.0') `
  -WorkingDirectory (Join-Path (Get-Location) 'ui') `
  -RedirectStandardOutput logs\dev-frontend.out.log `
  -RedirectStandardError logs\dev-frontend.err.log `
  -WindowStyle Hidden
```

## 验证服务

检查端口监听：

```powershell
Get-NetTCPConnection -LocalPort 8000,5173 -State Listen -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,State,OwningProcess
```

验证后端健康状态：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

期望返回：

```json
{
  "ok": true,
  "status": "running"
}
```

验证前端首页：

```powershell
$r = Invoke-WebRequest http://127.0.0.1:5173/ -UseBasicParsing
"$($r.StatusCode) $($r.StatusDescription)"
```

局域网模式下，也可以用本机 IP 自测：

```powershell
Invoke-RestMethod http://192.168.1.68:8000/api/health
Invoke-WebRequest http://192.168.1.68:5173/ -UseBasicParsing
```

## 关闭服务

按端口关闭当前前后端服务：

```powershell
foreach ($port in @(8000, 5173)) {
  $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($conn in $conns) {
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
  }
}
```

验证是否关闭：

```powershell
Get-NetTCPConnection -LocalPort 8000,5173 -State Listen -ErrorAction SilentlyContinue
```

没有输出表示服务已关闭。

也可以用请求验证：

```powershell
Invoke-WebRequest http://127.0.0.1:5173/ -UseBasicParsing
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

关闭成功时，这两个命令会报无法连接。

## CLI 快速验证命令

CLI 入口：

```powershell
cd C:\Users\tangerine\.rag_v
python -m app.cli --help
```

轻量验证，不依赖模型：

```powershell
python -m app.cli kb list
python -m app.cli session list
python -m app.cli session info 062503
```

创建知识库和会话：

```powershell
python -m app.cli kb create demo_kb
python -m app.cli session create demo_session
python -m app.cli session bind demo_session demo_kb
python -m app.cli session info demo_session
```

上传并索引文档，需要 Ollama Embedding 模型可用：

```powershell
python -m app.cli kb upload demo_kb .\test_file
python -m app.cli kb index demo_kb --all
python -m app.cli kb list demo_kb
```

完整问答验证，需要 LLM 和 Embedding 模型都可用：

```powershell
python -m app.cli session chat demo_session "这个知识库主要讲什么？"
```

清理验证数据：

```powershell
python -m app.cli session delete demo_session
python -m app.cli kb delete demo_kb
```

## 常用目录

- `app/api/`：FastAPI 路由和服务入口。
- `app/modules/kb_manager/`：知识库、上传、索引逻辑。
- `app/modules/session/`：会话、聊天、RAG 问答逻辑。
- `ui/`：React 前端。
- `kb/`：知识库文件与向量数据。
- `sessions/`：会话配置和聊天记录。
- `logs/`：后台运行日志。
- `settings.json`：Ollama 地址和模型配置。

## 日志与调试路线

默认运行模式保持安静：成功的后端 API 请求和成功的前端 API 请求不会输出应用层耗时日志，也不会再要求 `[TIMING]` 或 `/api/performance`。

后端日志：

- 前台运行时，查看启动后端的 PowerShell 窗口。
- 后台运行时，查看 `logs/dev-backend.out.log` 和 `logs/dev-backend.err.log`。
- 应用日志级别可用环境变量控制：

```powershell
$env:RAGV_LOG_LEVEL = "DEBUG"
python -m uvicorn app.api.server:app --host 127.0.0.1 --port 8000
```

也可以在 `settings.json` 的 `env` 中设置：

```json
{
  "env": {
    "RAGV_LOG_LEVEL": "DEBUG"
  }
}
```

前端日志：

- 普通页面问题先看浏览器 DevTools 的 Console 和 Network。
- 前端请求失败始终会通过 `console.error` 输出。
- 成功请求和慢请求日志默认关闭；需要调试 API 代理或请求链路时启用：

```powershell
cd C:\Users\tangerine\.rag_v\ui
$env:VITE_API_DEBUG = "true"
npm run dev -- --host 127.0.0.1
```

后台前端进程日志仍写入：

```text
logs/dev-frontend.out.log
logs/dev-frontend.err.log
```

检索诊断：

- 普通聊天请求不会默认输出 ChromaDB、BM25、RRF、Reranker 的分阶段诊断。
- 需要排查召回质量时，显式运行：

```powershell
python test/test_retrieval_diagnostic.py <kb_name> "<query>"
```

- 诊断 JSON 报告写入 `test/diagnostic_output/`。

根目录下的 `backend.log`、`backend_err.log`、`frontend.log`、`frontend_err.log` 只视为历史或临时文件；日常调试以 `logs/`、浏览器 Console/Network 和显式诊断报告为准。
