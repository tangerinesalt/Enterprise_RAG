"""知识库 REST API。"""

import os
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from app.api.schemas import KbCreateRequest, KbIndexRequest, KbReindexRequest
from app.modules.kb_manager import KnowledgeBase, KnowledgeBaseError
from app.modules.kb_manager.indexer import Indexer

router = APIRouter()

_kb = KnowledgeBase()
_indexer = Indexer()


def _ok(data=None):
    return {"ok": True, "data": data}

def _err(msg: str, status: int = 400):
    return JSONResponse(status_code=status, content={"ok": False, "error": msg})


@router.get("")
def list_kb():
    """列出所有知识库"""
    items = _kb.list_all()
    result = []
    for name in items:
        files = _kb.list_files(name)
        fcount = sum(1 for f in files if f["type"] == "file")
        dircount = sum(1 for f in files if f["type"] == "folder")
        result.append({"name": name, "files": fcount, "folders": dircount})
    return _ok(result)


@router.post("")
def create_kb(body: KbCreateRequest):
    """创建知识库"""
    try:
        path = _kb.create(body.name)
        return _ok({"name": body.name, "path": path})
    except KnowledgeBaseError as e:
        return _err(str(e))


@router.get("/{name}")
def get_kb(name: str):
    """知识库详情（文件列表）"""
    try:
        items = _kb.list_files(name)
        return _ok({"name": name, "files": items})
    except KnowledgeBaseError as e:
        return _err(str(e), 404)


@router.post("/upload")
async def upload_kb(name: str = Form(...), files: list[UploadFile] = File(...)):
    """上传文件或文件夹到知识库"""
    try:
        _kb.ensure_exists(name)
        saved = []
        for f in files:
            dest = _kb.file_path(name, f.filename or "unknown")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            content = await f.read()
            with open(dest, "wb") as wf:
                wf.write(content)
            saved.append(f.filename)
        return _ok({"name": name, "saved": saved})
    except KnowledgeBaseError as e:
        return _err(str(e))


@router.post("/index")
def index_kb(body: KbIndexRequest):
    """索引文件/文件夹/全部"""
    try:
        _kb.ensure_exists(body.name)
        if body.all:
            results = _indexer.index_all(body.name)
        elif body.target and _kb.folder_exists(body.name, body.target):
            results = _indexer.index_folder(body.name, body.target)
        elif body.target and _kb.file_exists(body.name, body.target):
            c = _indexer.index_file(body.name, body.target)
            results = {body.target: c}
        else:
            return _err(f"目标 '{body.target}' 不存在")
        ok_count = sum(1 for v in results.values() if isinstance(v, int))
        total_chunks = sum(v for v in results.values() if isinstance(v, int))
        return _ok({"indexed": ok_count, "total_chunks": total_chunks, "details": results})
    except (KnowledgeBaseError, FileNotFoundError) as e:
        return _err(str(e))


@router.post("/reindex")
def reindex_kb(body: KbReindexRequest):
    """重新索引文件"""
    try:
        c = _indexer.reindex_file(body.name, body.filename)
        return _ok({"filename": body.filename, "chunks": c})
    except (KnowledgeBaseError, FileNotFoundError) as e:
        return _err(str(e))


@router.post("/upload-and-index")
async def upload_and_index(name: str = Form(...), files: list[UploadFile] = File(...)):
    """上传并索引（一步完成）"""
    try:
        _kb.ensure_exists(name)
        saved = []
        for f in files:
            dest = _kb.file_path(name, f.filename or "unknown")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            content = await f.read()
            with open(dest, "wb") as wf:
                wf.write(content)
            saved.append(f.filename)

        results = {}
        for filename in saved:
            c = _indexer.index_file(name, filename)
            results[filename] = c
        return _ok({"name": name, "saved": saved, "index_results": results})
    except (KnowledgeBaseError, FileNotFoundError) as e:
        return _err(str(e))


@router.delete("/{name}")
def delete_kb(name: str):
    """删除知识库"""
    try:
        _kb.destroy(name)
        return _ok({"name": name})
    except KnowledgeBaseError as e:
        return _err(str(e), 404)


@router.delete("/{name}/files")
def delete_kb_file(name: str, filename: str):
    """删除知识库中的单个文件（含向量）"""
    try:
        _kb.delete_file(name, filename)
        return _ok({"name": name, "filename": filename})
    except KnowledgeBaseError as e:
        return _err(str(e), 404)
