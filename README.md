# RAG V

企业级 RAG 应用 MVP。项目提供知识库管理、文档上传与索引、会话管理、基于知识库的问答，以及一个 React + FastAPI 的 Web 界面。

## 功能介绍

- 知识库管理：创建、删除、查看知识库。
- 文档管理：上传文件或文件夹到知识库，支持通过 CLI 或 Web 操作。
- 向量索引：基于 LlamaIndex + ChromaDB 建立知识库索引。
- RAG 问答：会话绑定知识库后，按用户问题检索相关片段并调用 LLM 生成回答。
- 会话与聊天记录：支持创建会话、新建聊天、切换历史聊天、查看聊天记录。
- 延迟创建聊天：进入会话后显示空白状态，输入问题时自动创建聊天文件；侧边栏显示首条 query 预览。
- Web 服务：FastAPI 后端提供 REST API，Vite + React 前端提供知识库和会话页面。

## 运行依赖

### 基础环境

- **Python** 3.13 或兼容版本
- **Node.js** / npm（用于前端）
- **Ollama**（本地 LLM/Embedding 模式时必需；DeepSeek/OpenAI 远端模式不需要）

### 模型清单

| 层级 | 模型 | 大小 | 说明 |
|------|------|------|------|
| **LLM** | `deepseek-v4-flash`（远端）或 `qwen3.5:9b`（本地 Ollama） | ~5GB | 问答生成 |
| **Embedding** | `bge-m3` | ~1.2GB | 文档向量化 |
| **Reranker** | `BAAI/bge-reranker-v2-m3` | ~2.2GB | 检索结果重排序 |
| **OCR 兜底**（可选） | rapidocr-onnxruntime + pypdfium2 | ~100MB | PDF 文字提取失败时自动启用 |
| **表格识别**（可选） | rapid-table（SLANet Plus ONNX） | 7.4MB | 扫描件表格结构化识别，需 `ENABLE_TABLE_RECOGNITION=true` |

安装命令见下方「安装」节。

### 配置项

所有模型和密钥配置通过 `settings.json`（**已加入 `.gitignore`，不会被提交**）：

| 键 | 说明 | 默认值 |
|----|------|--------|
| `LLM_PROVIDER` | LLM 提供商：`ollama` / `deepseek` / `openai` | `ollama` |
| `LLM_MODEL` | LLM 模型名 | `qwen3.5:9b` |
| `LLM_URL` | LLM 服务地址 | `http://127.0.0.1:11434` |
| `LLM_TOKEN` | DeepSeek / OpenAI API 密钥 | `""` |
| `EMBED_MODEL` | Embedding 模型名 | `qwen3-embedding:4b` |
| `EMBED_URL` | Embedding 服务地址（可独立于 LLM） | `http://127.0.0.1:11434` |
| `RAGV_LOG_LEVEL` | 日志级别：`DEBUG` / `INFO` / `WARNING` | （不设置 = INFO） |

> `RAGV_LOG_LEVEL=DEBUG` 时输出 RAG 查询全链路日志（query→检索→LLM）。

表格识别为自动检测——`pip install rapid-table` 后首次索引自动启用，无需额外配置。

## 安装

### 后端

```powershell
cd C:\Users\tangerine\.rag_v

# 1. 基础 Web 框架
pip install fastapi uvicorn python-multipart

# 2. RAG 核心：LlamaIndex + ChromaDB + 中文分词
pip install llama-index chromadb jieba pypdf

# 3. LLM 驱动（按需选装）
pip install llama-index-llms-ollama   # Ollama 本地模式
pip install llama-index-llms-openai   # DeepSeek / OpenAI 远端模式

# 4. Embedding 驱动（按需选装）
pip install llama-index-embeddings-ollama   # Ollama 本地模式

# 5. 重排序模型（必需）
pip install sentence-transformers torch
python scripts/download_reranker.py

# 6. OCR 兜底（可选，PDF 文字提取失败时自动启用）
pip install rapidocr-onnxruntime pypdfium2 rapidocr

# 7. 表格识别（可选，扫描件表格结构化提取，ENABLE_TABLE_RECOGNITION=true）
pip install rapid-table

# 8. pypdf 表格提取（可选，已安装 pdfplumber 时自动启用）
pip install pdfplumber
```

**Ollama 模型**（本地模式时需要）：

```powershell
ollama pull qwen3.5:9b      # LLM
ollama pull bge-m3           # Embedding
```

各组之间独立——你可以只装需要的。例如仅用 DeepSeek API + Ollama Embedding：
```powershell
pip install fastapi uvicorn python-multipart
pip install llama-index chromadb jieba pypdf
pip install llama-index-llms-openai
pip install llama-index-embeddings-ollama
pip install sentence-transformers torch
python scripts/download_reranker.py
```

有表格类文档（扫描件或 PDF）时，建议额外安装：
```powershell
pip install pdfplumber rapid-table rapidocr
```

### 前端

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

# 需要 DEBUG 日志时将下面这行取消注释：
# $env:RAGV_LOG_LEVEL = "DEBUG"

Start-Process -FilePath python `
  -ArgumentList @('-m','uvicorn','app.api.server:app','--host','0.0.0.0','--port','8000','--log-level','warning') `
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
- `sessions/`：会话配置（含 query 预览预览）和聊天记录（SimpleChatStore JSON）。
- `logs/`：后台运行日志。
- `settings.json`：LLM/Embedding 模型配置（已加入 `.gitignore`，本地专属）。
- `openspec/`：OpenSpec 规范驱动开发工件（specs、变更记录、归档）。

## 日志与调试路线

默认运行模式保持安静，第三方库噪音（httpx、chromadb INFO、tqdm 进度条）已屏蔽。以下是不同调试场景的入口速查：

| 你想看什么 | 怎么做 |
|-----------|--------|
| 后端应用日志（INFO） | 默认就有，查看终端或 `logs/dev-backend.err.log` |
| RAG 查询全链路（query→检索→LLM） | 开启 `RAGV_LOG_LEVEL=DEBUG` |
| 前端 API 请求耗时 | 开启 `VITE_API_DEBUG=true` |
| 检索召回质量分析（分阶段诊断） | 运行 `test/test_retrieval_diagnostic.py` |
| uvicorn HTTP 访问日志 | 启动时加 `--log-level warning` 关闭 |

---

### 后端日志

**在哪里看**

| 运行方式 | 日志位置 |
|---------|---------|
| 前台（直接启动） | PowerShell 窗口 |
| 后台（Start-Process） | `logs/dev-backend.err.log`（应用日志）/ `logs/dev-backend.out.log`（stdout） |

**日志级别控制**

```powershell
# 方式 1：环境变量（临时）
$env:RAGV_LOG_LEVEL = "DEBUG"
python -m uvicorn app.api.server:app --host 127.0.0.1 --port 8000

# 方式 2：settings.json（持久）
# {"env": {"RAGV_LOG_LEVEL": "DEBUG"}}
```

#### RAG 查询 DEBUG 日志

`RAGV_LOG_LEVEL=DEBUG` 后，每次问答输出结构化日志，格式 `key=value` 方便 `grep`：

```
query | sync start session=光伏对话 kb=光伏信息 top_k=8 top_n=5 mode=hybrid query=数字化转型
query | sync done  session=光伏对话 sources=6 elapsed=8.42s ans_len=892 score_min=0.32 score_max=0.97
                     ans_pfx=数字化转型的具体要求包括以下方面：1...
query | sync error session=光伏对话 elapsed=0.53s err=知识库不存在
```

包含字段：

| 阶段 | 字段 | 说明 |
|------|------|------|
| **start** | `session` / `kb` / `top_k` / `top_n` / `mode` / `query` | 查询上下文 |
| **done** | `sources` / `elapsed` / `ans_len` / `score_min~max` / `ans_pfx` | 来源数、耗时、答案长度、分数范围、答案预览 |

#### 噪音已被消除

| 来源 | 改前 | 改后 |
|------|------|------|
| uvicorn HTTP 访问日志 | 每个请求一行 `200 OK` | 后端加 `--log-level warning` 关闭 |
| httpx HTTP 请求日志 | 每次 embed/LLM 调用一行 | 降至 WARNING，DEBUG 级才可见 |
| tqdm 进度条 | embedding 时刷屏 | 全局关闭 |
| 重排序模型 | 每次查询重新加载（~1s） | 进程级单例缓存 |

---

### 前端日志

| 运行方式 | 日志位置 |
|---------|---------|
| 前台（`npm run dev`） | 浏览器 Console + Network 面板 |
| 后台（Start-Process） | `logs/dev-frontend.out.log` / `logs/dev-frontend.err.log` |

**前端 API 请求日志** — 默认只输出失败请求；需要查看成功请求和耗时：

```powershell
cd C:\Users\tangerine\.rag_v\ui
$env:VITE_API_DEBUG = "true"
npm run dev -- --host 127.0.0.1
```

---

### 检索诊断

普通聊天不会输出检索各阶段的明细（ChromaDB、BM25、RRF、Reranker）。需要排查召回质量时：

```powershell
python test/test_retrieval_diagnostic.py <kb_name> "<query>"
```

诊断 JSON 报告写入 `test/diagnostic_output/`。

---

> 根目录下的 `backend.log`、`backend_err.log`、`frontend.log`、`frontend_err.log` 为历史文件；日常调试以 `logs/`、浏览器 Console/Network 和显式诊断报告为准。
