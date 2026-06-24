# Project — RAG V

> **企业级 RAG 应用** | 当前阶段：最小可用产品 (MVP)

## 项目定位

构建一套面向企业场景的 **RAG（检索增强生成）** 应用，让用户能够通过自然语言与私有文档进行对话，实现高效的知识检索与内容生成。

## 当前目标 — MVP

MVP 阶段聚焦于 **最小可用**，先跑通核心链路，再做扩展。

### 第一阶段：简单文档检索

1. **文档接入**
   - 支持上传常见文档格式（PDF、TXT、Markdown、Word 等）
   - 文档解析与文本提取

2. **向量化与索引**
   - 文档分块 (Chunking)
   - 使用 Embedding 模型将文本转为向量
   - 存入向量数据库，构建索引

3. **检索**
   - 基于用户 Query 进行语义检索
   - 返回最相关的文档片段
   - 支持简单的相关性排序

4. **生成**
   - 将检索结果注入 LLM 上下文
   - 生成基于文档的准确回答
   - 标注引用来源

## 技术方向（待确定）

| 模块 | 候选技术 |
|------|---------|
| 向量数据库 | Chroma / Milvus / Qdrant / pgvector |
| Embedding | text-embedding-3-small / bge / m3e |
| LLM | 通义千问 / DeepSeek / Claude API |
| 文档解析 | Unstructured / LangChain Document Loaders |
| 后端框架 | FastAPI / Python |
| 前端 | Streamlit / Gradio / Vue |

## 非目标（当前阶段不考虑）

- 多模态检索（图片、音视频）
- 复杂的权限管理与多租户
- 大规模文档集的分布式部署
- 实时数据同步与增量更新
- 工作流编排与 Agent 功能

## 里程碑

- [x] **M1** — 搭建项目骨架、确定技术栈（GitHub 仓库已同步）
- [x] **M2** — 实现文档上传与解析（LlamaIndex + RobustPDFReader + OCR 兜底）
- [x] **M3** — 实现向量化与检索（Ollama Embedding + ChromaDB）
- [x] **M4** — 实现生成回答（检索+LLM）
- [ ] **M5** — 提供简易 UI 交互界面
- [ ] **M6** — MVP 验收与反馈收集

## 已完成功能

- 知识库管理（创建、上传、删除、重新索引、列出）
- 文档解析（TXT/MD/PDF，含 OCR 兜底）
- 向量化索引（基于 llama_index + Ollama Embedding）
- 检索增强生成（基于 llama_index QueryEngine）
- CLI 管理入口
- 测试检索接口

---

*项目动态更新于此文件。*
