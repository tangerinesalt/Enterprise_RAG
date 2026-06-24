## Context

项目目前使用 Ollama 本地部署，通过 llama_index 的 `OllamaEmbedding` 和 `Ollama` 类对接模型。当前的问题是：

1. 模型配置分散：`indexer.py` 创建 Embedding，`test_retrieve.py` 创建 Embedding + LLM，各自从 `config.settings` 导入参数
2. 更换模型成本高：如果从 Ollama 切换到 OpenAI/HuggingFace，需要修改 N 个文件
3. 没有统一的初始化入口：调用方要自行负责实例化

参考方案：利用 llama_index 的全局 `Settings` 对象，在 `config/` 下按关注点分离，集中配置并注入。

## Goals / Non-Goals

**Goals:**
- 新增 `config/embedding.py` + `config/llm.py` + `config/init.py`
- 所有消费模块通过 `Settings` 获取已配置的模型实例
- 更换模型只需修改 `config/` 下的对应文件
- `config/settings.py` 保持不变（仍负责原始配置项读取）

**Non-Goals:**
- 不改变 example/ 目录的代码
- 不做模型的热切换/运行时切换
- 不做多 provider 支持（一次只用一个 provider）

## Decisions

### 1. 三文件结构替代单文件

```
config/
├── __init__.py       # 保持不变
├── settings.py       # 保持不变：读取 settings.json 的原始配置项
├── embedding.py      # 新增：创建并设置 Settings.embed_model
├── llm.py            # 新增：创建并设置 Settings.llm
└── init.py           # 新增：按序调用 embedding.init() + llm.init()
```

参考文章按 `configs/embedding.py` + `configs/llm.py` 拆分，但项目已有 `config/` 目录，将新文件放在同一目录下更紧凑。

### 2. 使用 LlamaIndex Settings 而非自定义全局变量

llama_index 的 `Settings` 已经是全局单例，所有组件（索引、查询引擎等）都会自动读取。不再需要各模块自行导入模型类。

使用方式：
```python
from config.init import init_models
init_models()

# 之后所有组件自动使用全局配置
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
```

### 3. 每个模型文件只暴露一个 init 函数

```python
# config/embedding.py
from config.settings import EMBED_URL, EMBED_MODEL

def init_embedding():
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=EMBED_URL,
    )
```

```python
# config/llm.py
from config.settings import OLLAMA_URL, LLM_MODEL

def init_llm():
    Settings.llm = Ollama(
        model=LLM_MODEL,
        base_url=OLLAMA_URL,
        temperature=0.3,
        request_timeout=60,
    )
```

```python
# config/init.py
def init_models():
    init_embedding()
    init_llm()
```

## 调用方式变化

```python
# 之前（修改前）
from config.settings import EMBED_URL, EMBED_MODEL
Settings.embed_model = OllamaEmbedding(model_name=EMBED_MODEL, base_url=EMBED_URL)

# 之后（修改后）
from config.init import init_models
init_models()  # 一次调用，LLM 和 Embedding 全局就绪
```

## Risks / Trade-offs

- **[风险] 初始化顺序依赖** → `init_models()` 中按 embedding → llm 顺序，各自独立无交叉依赖
- **[风险] 全局可变状态** → Settings 是进程级全局对象，当前为单用户 CLI 场景无问题
- **[权衡] 增加抽象层** → 多了一层间接调用，但换来"更换模型改一处"的便利
