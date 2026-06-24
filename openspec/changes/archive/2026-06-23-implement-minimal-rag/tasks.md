## 1. 环境准备

- [x] 1.1 安装依赖：`pip install chromadb pypdf requests`
- [x] 1.2 确认 Ollama 可用：`curl http://127.0.0.1:11434/api/tags`
- [x] 1.3 准备测试文档：创建 `example/sample.txt`

## 2. Part 1 — 解析 + 索引 (parse_index.py)

- [x] 2.1 实现文档读取：根据文件扩展名选择 PDF(pypdf) / TXT / Markdown 解析
- [x] 2.2 实现文本分块：固定大小切分，保留词边界，可配 chunk_size 和 overlap
- [x] 2.3 实现 Embedding 调用：通过 Ollama HTTP API (`/api/embed`) 将文本块转为向量
- [x] 2.4 实现 ChromaDB 存储：初始化持久化 `rag_demo_db/` 集合，写入块文本 + 向量
- [x] 2.5 全过程打印：文件名称、总字符数、分块数、向量维度、索引完成提示

## 3. Part 2 — 检索 + 生成 (retrieve_generate.py)

- [x] 3.1 实现 Embedding 查询：将用户问题转为向量
- [x] 3.2 实现 ChromaDB 检索：semantic search，返回 top-k 结果
- [x] 3.3 构建 RAG Prompt：系统指令（基于上下文回答 + 标注来源）+ 检索片段 + 用户问题
- [x] 3.4 实现 LLM 调用：通过 Ollama Chat API (`/api/chat`) 生成回答
- [x] 3.5 输出格式：检索到的片段 → 生成回答 → 来源引用

## 4. 验证运行

- [x] 4.1 `python parse_index.py sample.txt` — 索引成功，打印分块信息
- [x] 4.2 `python retrieve_generate.py "什么是RAG？它有哪些优势？"` — 生成基于文档的回答
- [x] 4.3 验证引用来源出现在输出中
- [x] 4.4 验证空库提示：删除 rag_demo_db/ 后查询应提示先索引

## 5. 文档

- [x] 5.1 创建 `example/README.md`：说明前置条件、运行步骤、预期输出
