"""知识库 REST API。"""

import json
import os

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.schemas import KbCreateRequest, KbIndexRequest, KbReindexRequest
from app.modules.kb_manager import KnowledgeBase, KnowledgeBaseError, KnowledgeBasePathError
from app.modules.kb_manager.indexer import Indexer

router = APIRouter()

_kb = KnowledgeBase()
_indexer = Indexer()


def _ok(data=None):
    return {"ok": True, "data": data}


def _err(msg: str, status: int = 400):
    return JSONResponse(status_code=status, content={"ok": False, "error": msg})


def _kb_error_status(exc: Exception, missing_status: int = 404) -> int:
    if isinstance(exc, KnowledgeBasePathError):
        return 400
    if isinstance(exc, FileNotFoundError):
        return missing_status
    return 400


@router.get("")
def list_kb():
    items = _kb.list_all()
    result = []
    for name in items:
        files = _kb.list_files(name)
        file_count = sum(1 for item in files if item["type"] == "file")
        folder_count = sum(1 for item in files if item["type"] == "folder")
        result.append({"name": name, "files": file_count, "folders": folder_count})
    return _ok(result)


@router.post("")
def create_kb(body: KbCreateRequest):
    try:
        path = _kb.create(body.name)
        return _ok({"name": body.name, "path": path})
    except KnowledgeBaseError as exc:
        return _err(str(exc), _kb_error_status(exc, 400))


@router.get("/{name}")
def get_kb(name: str):
    try:
        items = _kb.list_files(name)
        for item in items:
            status = _kb.get_file_status(name, item["name"])
            item["indexed"] = status["status"]
            item["chunks"] = status["chunks"]
            item["indexed_at"] = status["indexed_at"]
        return _ok({"name": name, "files": items})
    except KnowledgeBaseError as exc:
        return _err(str(exc), _kb_error_status(exc))


@router.post("/upload")
async def upload_kb(name: str = Form(...), files: list[UploadFile] = File(...)):
    try:
        _kb.ensure_exists(name)
        saved = []
        for upload in files:
            flat_name = _kb.validate_upload_name(upload.filename or "unknown")
            dest_name = _kb._unique_filename(name, flat_name)
            dest_path = _kb.file_path(name, dest_name)
            with open(dest_path, "wb") as handle:
                handle.write(await upload.read())
            _kb.set_file_status(name, dest_name, "pending")
            saved.append(dest_name)
        return _ok({"name": name, "saved": saved})
    except (KnowledgeBaseError, OSError) as exc:
        return _err(str(exc), _kb_error_status(exc, 400))


@router.post("/index")
def index_kb(body: KbIndexRequest):
    try:
        _kb.ensure_exists(body.name)
        if body.all:
            results = _indexer.index_all(body.name)
        elif body.target and _kb.folder_exists(body.name, body.target):
            results = _indexer.index_folder(body.name, body.target)
        elif body.target and _kb.file_exists(body.name, body.target):
            chunk_count = _indexer.index_file(body.name, body.target)
            results = {body.target: chunk_count}
        else:
            return _err(f"目标 '{body.target}' 不存在", 404)

        ok_count = sum(1 for value in results.values() if isinstance(value, int))
        total_chunks = sum(value for value in results.values() if isinstance(value, int))
        return _ok({"indexed": ok_count, "total_chunks": total_chunks, "details": results})
    except (KnowledgeBaseError, FileNotFoundError) as exc:
        return _err(str(exc), _kb_error_status(exc))


def _index_stream_events(events):
    for event in events:
        event_type = event["type"]
        if event_type == "index_start":
            payload = {"file": event["file"], "total_chunks": event["total_chunks"]}
            yield f"event: index_start\ndata: {json.dumps(payload)}\n\n"
        elif event_type == "index_progress":
            payload = {
                "file": event["file"],
                "current": event["current"],
                "total": event["total"],
                "pct": event["pct"],
            }
            yield f"event: index_progress\ndata: {json.dumps(payload)}\n\n"
        elif event_type == "index_done":
            if "chunks" in event:
                payload = {"file": event["file"], "chunks": event["chunks"]}
            else:
                payload = {"status": event["status"], "files": event["files"]}
            yield f"event: index_done\ndata: {json.dumps(payload)}\n\n"
        elif event_type == "index_error":
            payload = {"file": event["file"], "message": event["message"]}
            yield f"event: index_error\ndata: {json.dumps(payload)}\n\n"


@router.post("/index/stream")
def index_kb_stream(body: KbIndexRequest):
    try:
        _kb.ensure_exists(body.name)
        if body.all:
            events = _indexer.index_all_stream(body.name)
        elif body.target and _kb.folder_exists(body.name, body.target):
            events = _indexer.index_folder_stream(body.name, body.target)
        elif body.target and _kb.file_exists(body.name, body.target):
            events = _indexer.index_file_stream(body.name, body.target)
        else:
            return _err(f"目标 '{body.target}' 不存在", 404)
        return StreamingResponse(_index_stream_events(events), media_type="text/event-stream")
    except (KnowledgeBaseError, FileNotFoundError) as exc:
        return _err(str(exc), _kb_error_status(exc))


@router.post("/reindex")
def reindex_kb(body: KbReindexRequest):
    try:
        chunk_count = _indexer.reindex_file(body.name, body.filename)
        return _ok({"filename": body.filename, "chunks": chunk_count})
    except (KnowledgeBaseError, FileNotFoundError) as exc:
        return _err(str(exc), _kb_error_status(exc))
    except Exception as exc:  # pragma: no cover
        return _err(f"重新索引失败: {exc}", 500)


@router.post("/upload-and-index")
async def upload_and_index(name: str = Form(...), files: list[UploadFile] = File(...)):
    try:
        _kb.ensure_exists(name)
        saved = []
        for upload in files:
            flat_name = _kb.validate_upload_name(upload.filename or "unknown")
            dest_name = _kb._unique_filename(name, flat_name)
            dest_path = _kb.file_path(name, dest_name)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "wb") as handle:
                handle.write(await upload.read())
            _kb.set_file_status(name, dest_name, "pending")
            saved.append(dest_name)

        results = {}
        for filename in saved:
            results[filename] = _indexer.index_file(name, filename)
        return _ok({"name": name, "saved": saved, "index_results": results})
    except (KnowledgeBaseError, FileNotFoundError, OSError) as exc:
        return _err(str(exc), _kb_error_status(exc))


@router.delete("/{name}")
def delete_kb(name: str):
    try:
        _kb.destroy(name)
        return _ok({"name": name})
    except KnowledgeBaseError as exc:
        return _err(str(exc), _kb_error_status(exc))


@router.delete("/{name}/files")
def delete_kb_file(name: str, filename: str):
    try:
        _kb.delete_file(name, filename)
        return _ok({"name": name, "filename": filename})
    except KnowledgeBaseError as exc:
        return _err(str(exc), _kb_error_status(exc))
