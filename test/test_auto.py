"""
test_auto.py — 全自动端到端测试。

在桌面创建 rag-test/ 嵌套目录，上传到知识库，索引后查询 A1~A4，
验证回答包含预期关键词，最后清理全部测试数据。

用法：
    python test/test_auto.py

注意：此脚本为测试用途，归档 change 时删除。
"""

import os
import sys
import shutil
import subprocess
import tempfile

# 确保项目根目录在 Python 路径中
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


# ── 测试数据 ─────────────────────────────────

TEST_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "rag-test")
KB_NAME = "auto-test"

TEST_FILES = {
    "A1-概述.txt": "A1 是系统核心模块，负责数据采集与预处理，为后续分析提供基础数据支持。",
    "A2-原理.txt": "A2 基于双重校验算法，通过数据交叉验证确保系统一致性和准确性。",
}

TEST_SUBDIR = "sub"
TEST_SUBFILES = {
    "A3-应用.txt": "A3 广泛应用于金融风控、医疗诊断和智能制造领域，显著提升效率。",
    "A4-实践.txt": "A4 的最佳实践包括日志监控、灰度发布和自动化回滚机制。",
}

# 每个问题期望回答中必须包含的关键词
EXPECTED_KEYWORDS = {
    "什么是A1？": ["A1", "数据采集", "预处理"],
    "什么是A2？": ["A2", "双重校验", "一致性"],
    "什么是A3？": ["A3", "金融", "医疗", "制造"],
    "什么是A4？": ["A4", "日志监控", "灰度发布", "自动化"],
}


# ── 工具函数 ─────────────────────────────────

def run(cmd: list[str], cwd: str = _project_root) -> tuple[int, str]:
    """运行命令并返回 (exit_code, stdout)"""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


def cli(*args: str) -> tuple[int, str]:
    """运行 CLI 命令"""
    return run([sys.executable, "-m", "app.modules.kb_manager.cli"] + list(args))


def test_query(kb_name: str, question: str) -> tuple[int, str]:
    """运行检索测试"""
    return run([sys.executable, "test/test_retrieve.py", kb_name, question])


# ── 测试流程 ─────────────────────────────────

def setup_test_data():
    """创建测试目录结构"""
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

    os.makedirs(TEST_DIR, exist_ok=True)
    for name, content in TEST_FILES.items():
        with open(os.path.join(TEST_DIR, name), "w", encoding="utf-8") as f:
            f.write(content)

    subdir = os.path.join(TEST_DIR, TEST_SUBDIR)
    os.makedirs(subdir, exist_ok=True)
    for name, content in TEST_SUBFILES.items():
        with open(os.path.join(subdir, name), "w", encoding="utf-8") as f:
            f.write(content)

    print(f"[setup] 测试目录已创建: {TEST_DIR}")


def run_test() -> bool:
    """执行全链路测试。返回 True 表示全部通过。"""
    results = []

    # 1. 创建知识库
    print(f"\n{'='*50}")
    print(f"[1/6] 创建知识库 '{KB_NAME}'")
    print(f"{'='*50}")
    code, out = cli("kb", "create", KB_NAME)
    if code != 0:
        print(f"[FAIL] 创建知识库失败: {out}")
        return False
    print(f"  [OK] {out}")

    # 2. 上传文件夹
    print(f"\n{'='*50}")
    print(f"[2/6] 上传文件夹到知识库")
    print(f"{'='*50}")
    code, out = cli("kb", "upload", KB_NAME, TEST_DIR)
    if code != 0:
        print(f"[FAIL] 上传文件夹失败: {out}")
        return False
    print(f"  [OK] {out}")

    # 3. 索引文件夹
    folder_name = os.path.basename(TEST_DIR)
    print(f"\n{'='*50}")
    print(f"[3/6] 索引文件夹 '{folder_name}'")
    print(f"{'='*50}")
    code, out = cli("kb", "index", KB_NAME, folder_name)
    if code != 0:
        print(f"[FAIL] 索引文件夹失败: {out}")
        return False
    for line in out.split("\n"):
        print(f"  {line}")

    # 4. 查询并验证
    print(f"\n{'='*50}")
    print(f"[4/6] 查询验证")
    print(f"{'='*50}")
    all_pass = True
    for question, keywords in EXPECTED_KEYWORDS.items():
        code, answer = test_query(KB_NAME, question)
        if code != 0:
            print(f"  [FAIL] 查询失败 ({question}): {answer[:100]}")
            all_pass = False
            continue

        # 检查关键词
        missing = [kw for kw in keywords if kw not in answer]
        if missing:
            print(f"  [FAIL] '{question}'")
            print(f"         缺失关键词: {missing}")
            print(f"         回答片段: {answer[:200]}")
            all_pass = False
            results.append((question, False, missing))
        else:
            print(f"  [PASS] '{question}'")
            results.append((question, True, []))

    if not all_pass:
        print(f"\n  [WARN] 部分查询未通过验证（可能是 LLM 表达差异，建议人工确认）")

    # 5. 清理知识库（删除文件夹）
    print(f"\n{'='*50}")
    print(f"[5/6] 清理知识库")
    print(f"{'='*50}")
    code, out = cli("kb", "delete", KB_NAME, folder_name)
    print(f"  {'[OK]' if code == 0 else '[FAIL]'} {out}")

    return all_pass


def cleanup():
    """清理测试残留"""
    # 删除知识库
    cli("kb", "delete", KB_NAME)
    # 删除桌面测试目录
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
        print(f"[cleanup] 已删除测试目录: {TEST_DIR}")


# ── 主函数 ───────────────────────────────────

def main():
    print(f"{'='*50}")
    print(f"RAG V — 自动测试脚本")
    print(f"{'='*50}")
    print(f"测试知识库: {KB_NAME}")
    print(f"测试目录:   {TEST_DIR}")

    success = False
    try:
        setup_test_data()
        success = run_test()
    finally:
        cleanup()

    print(f"\n{'='*50}")
    print(f"测试{'通过' if success else '失败'}")
    print(f"{'='*50}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
