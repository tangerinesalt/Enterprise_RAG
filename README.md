# RAG V

> 企业级 RAG 应用 — 最小可用产品 (MVP)

## 快速开始

```bash
# 1. 克隆后进入项目
cd rag_v

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Linux / macOS

# 3. 安装依赖
pip install -r requirements.txt

# 4. 环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 5. 启动
uvicorn app.main:app --reload
```

## 项目结构

```
rag_v/
├── app/                    # 主应用代码
│   ├── api/               # API 路由层
│   │   └── v1/            # API v1
│   ├── core/              # 核心业务逻辑
│   │   ├── ingestion/     # 文档接入与解析
│   │   ├── chunking/      # 文本分块策略
│   │   ├── embedding/     # 向量化
│   │   ├── retrieval/     # 检索逻辑
│   │   └── generation/    # 生成回答
│   ├── models/            # 数据模型 (Pydantic/SQLAlchemy)
│   ├── schemas/           # 请求/响应 Schema
│   └── utils/             # 通用工具
├── config/                # 配置管理
├── storage/               # 数据存储
│   ├── vector_db/         # 向量数据库
│   ├── documents/         # 原始文档
│   └── indices/           # 索引
├── tests/                 # 测试
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── fixtures/          # 测试数据
├── scripts/               # 工具脚本
├── docs/                  # 项目文档
├── docker/                # Docker 部署配置
├── uploads/               # 上传文件缓存
├── logs/                  # 运行时日志
├── project.md             # 项目规划文档
└── requirements.txt       # Python 依赖
```

## 文档

- [项目规划](project.md) — 目标、里程碑、技术选型
- [docs/](docs/) — 详细设计文档
