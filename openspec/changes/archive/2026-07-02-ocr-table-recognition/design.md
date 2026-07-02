## Context

当前扫描件 OCR 路径：

```
pypdfium2 渲染每页 → RapidOCR 纯文本识别 → 每页一个 Document（纯文本）
```

RapidTable（RapidAI 组织）提供基于 ONNX Runtime 的表格结构识别能力：

- 模型：SLANet Plus（7.4MB ONNX）
- 推理：ONNX Runtime（已有）
- 内置 RapidOCR 引擎做单元格文本识别
- 输出：HTML 表格 + 单元格坐标 + 行列逻辑位置

实测结果：印章管理制度权限矩阵页（1191×1684），2.9s 完成表格结构识别 + 全部单元格文本识别，输出含 colspan 合并单元格的正确 HTML 表格。

## Goals / Non-Goals

**Goals:**
- 用 RapidTable 检测扫描件中的表格区域并还原行列结构
- 表格区域输出为 HTML/Markdown，嵌入对应页的 Document 文本
- 非表格区域仍用 RapidOCR 纯文本识别（零开销）
- RapidTable 作为可选增强，由配置控制

**Non-Goals:**
- 不替代 RapidOCR——两者共存，按需选择
- 不修改分块、检索、生成等下游环节
- 不引入额外运行时依赖（ONNX Runtime 已在用）
- 不做跨页表格合并（与 pdf-table-extraction 设计一致）

## Decisions

### Decision 1：RapidTable 作为可选增强层，不替代 RapidOCR

**选择**：在 `_ocr_pdf()` 中新增一条走 RapidTable 的分支，由配置或 import 可用性决定。RapidOCR 保持不变。

```
_ocr_pdf(file_path)
  │
  ├─ RapidTable 可用 + 启用表格识别
  │   └─ pypdfium2 渲染 → RapidTable
  │       ├─ 检测到表格 → HTML → 转为 Markdown 合并
  │       └─ 无表格（或异常）→ RapidOCR 文本识别
  │
  └─ RapidTable 不可用 → RapidOCR 文本识别（现有流程）
```

**理由**：
- RapidTable 与 RapidOCR 同属 RapidAI 组织，共用 ONNX Runtime 底座
- 实测工作，模型自动下载（7.4MB），推理稳定
- 共存策略零风险——RapidTable 不可用时静默降级

### Decision 2：RapidTable 输出 HTML 后转 Markdown

**选择**：RapidTable 原生输出 HTML 表格（含 colspan/rowspan），转为 Markdown 格式嵌入 Document。

**理由**：
- HTML 保留了合并单元格信息，Markdown 转换时尽量保留
- 输出格式与现有 `_table_to_markdown()` 一致，下游无感知
- HTML 格式本身也可保留在节点 metadata 中供后续使用

### Decision 3：模型由首次使用自动下载

**选择**：RapidTable 首次 import 时自动下载 slanet-plus.onnx（7.4MB）到 `~/.rapid_table/models/`。

**理由**：
- RapidTable 官方已有此机制
- 7.4MB 下载一次，后续使用无网络开销

### Decision 4：不做独立的版面分析步骤

**选择**：不先用独立的版面分析检测"是否含表格"，直接调用 RapidTable。

**理由**：
- RapidTable 本身会做表格检测 + 结构识别一体化
- 对纯文本页面，RapidTable 返回空结果，开销很小（<0.5s 判定无表）
- 省去了维护两个模型（版面分析 + 表格识别）的复杂度

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| RapidTable 对纯文本页面额外开销 | 实测 <0.5s，通过配置可完全禁用 |
| SLANet 模型版本更新后行为变化 | 锁定 `rapid-table` 版本号 |
| 合并单元格还原不完美 | 即使部分正确也优于当前无结构状态 |
| 与已有 RapidOCR 版本冲突 | 两者通过不同 import 路径隔离，互不依赖 |
