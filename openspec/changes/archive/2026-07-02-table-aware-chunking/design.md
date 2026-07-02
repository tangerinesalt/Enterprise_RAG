## Context

当前 chunker 管线：

```
Document 文本 → SentenceSplitter → nodes
```

SentenceSplitter 按句子边界切分文本，不认识 Markdown 表格结构（`| ... |` + `---|---|`）。当表格文本超过 `chunk_size`（512 token）时，表格会被从中切断。

诊断数据：权限审批矩阵页（845 chars）→ 3 nodes，其中 2 个是丢失列头的"孤儿碎片"。

## Goals / Non-Goals

**Goals:**
- 检测被切分的表格碎片 node，自动补全列头
- 不修改 SentenceSplitter 的分块逻辑
- 对所有来源的 Markdown 表格一视同仁（pdfplumber + RapidTable）

**Non-Goals:**
- 不修改索引、OCR、检索流程
- 不做跨 node 的表格行合并（碎片仍可独立检索，只是补全了上下文）

## Decisions

### Decision 1：后处理方案（post-processing），而非自定义分块器

**选择**：在 `SentenceSplitter` 执行完成后，对输出的 nodes 做遍历修复。

```
当前：Document → SentenceSplitter → nodes
改为：Document → SentenceSplitter → nodes → _fix_orphan_tables(nodes) → 干净 nodes
```

**理由**：
- SentenceSplitter 的分块行为（合并小段、处理 overlap 等）是成熟逻辑，不应绕过
- 后处理只修复"已经有管道符但没有分离线"的 node，改动最小
- 对无表格的页面零开销

### Decision 2：列头从相邻 node 继承

**算法**：

```
_fix_orphan_tables(nodes):
    current_header = None  # 当前有效的表格列头行（如 | col1 | col2 |）
    current_separator = None  # 分离线行（如 |---|---|）

    for node in nodes:
        text = node.text
        
        if text 包含 |---|:
            # 此 node 包含完整的表格头 → 更新缓存
            current_header, current_separator = extract_first_table_header(text)
        
        elif text 包含 | 但不包含 ---:
            # orphan 碎片
            if current_header and current_separator:
                # 在 node 前面补列头
                node.text = current_header + "\n" + current_separator + "\n" + node.text
```

**理由**：
- `---` 是 Markdown 表格的唯一边界标记，准确率高
- 从最近的前序 node 继承列头，保证列对应关系正确
- 如果表格跨多个 chunk，中间 node 也都能获得正确的列头上下文

### Decision 3：仅修复第一个表格头

**选择**：只提取 node 中出现的第一个 Markdown 表格的列头。

**理由**：
- 一个 node 中出现多个表格的可能性极低（chunk_size=512 的限制）
- 实现简单，正则表达式 `r'^|.*|$'` 配合 `---|---|` 即可

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 误将非表格的管道符文本判为表格 | 以 `---|---|` 为判定条件，普通文本几乎不会包含 |
| 跨 chunk 的表格有不同列数，补头后不对齐 | 通用 Markdown 渲染器会自动适应列数差异 |
| 补头后 node 文本可能超过 chunk_size | 补头仅增加一行 ~30 chars，影响可忽略 |
