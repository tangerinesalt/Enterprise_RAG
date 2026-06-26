import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { kbApi } from '../api';
import type { FileItem } from '../api';

export default function KbDetail() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [files, setFiles] = useState<FileItem[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);
  const folderRef = useRef<HTMLInputElement>(null);

  const load = () => {
    if (!name) return;
    kbApi.get(name).then(d => setFiles(d.files)).catch(console.error);
  };

  useEffect(() => { load(); }, [name]);

  const handleUpload = async (isFolder: boolean) => {
    if (!name) return;
    const input = isFolder ? folderRef.current : fileRef.current;
    if (!input?.files?.length) return;
    await kbApi.upload(name, Array.from(input.files));
    input.value = '';
    load();
  };

  const handleDelete = async (target: string) => {
    if (!name || !confirm(`确定删除「${target}」？`)) return;
    await kbApi.deleteFile(name, target);
    load();
  };

  const handleIndexAll = async () => {
    if (!name) return;
    await kbApi.indexAll(name);
    load();
  };

  const handleIndex = async (target: string) => {
    if (!name) return;
    await kbApi.index(name, target);
    load();
  };

  return (
    <div>
      <button onClick={() => navigate('/kb')} style={linkStyle}>← 返回</button>
      <h2 style={{ margin: '8px 0 16px' }}>📁 {name}</h2>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <button onClick={() => fileRef.current?.click()} style={btnPrimary}>📄 上传文件</button>
        <button onClick={() => folderRef.current?.click()} style={btnPrimary}>📁 上传文件夹</button>
        <button onClick={handleIndexAll} style={btnSec}>⚡ 索引全部</button>
      </div>

      <input ref={fileRef} type="file" multiple style={{ display: 'none' }} onChange={() => handleUpload(false)} />
      <input ref={folderRef} type="file" style={{ display: 'none' }} onChange={() => handleUpload(true)} {...{ 'webkitdirectory': '' } as any} />

      {files.length === 0 && <p style={{ color: '#9ca3af' }}>暂无文件</p>}

      {files.map(f => (
        <div key={f.name} style={rowStyle}>
          <span>{f.type === 'folder' ? '📁' : '📄'} {f.name}</span>
          <span style={{ color: '#6b7280', fontSize: 13 }}>{f.size_str}</span>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
            <button onClick={() => handleIndex(f.name)} style={btnSmall}>索引</button>
            <button onClick={() => handleDelete(f.name)} style={btnSmallDanger}>🗑️</button>
          </div>
        </div>
      ))}
    </div>
  );
}

const linkStyle: React.CSSProperties = {
  background: 'none', border: 'none', color: '#2563eb',
  cursor: 'pointer', padding: 0, fontSize: 14,
};
const rowStyle: React.CSSProperties = {
  display: 'flex', alignItems: 'center', gap: 12,
  padding: '8px 12px', borderRadius: 4,
  borderBottom: '1px solid #f3f4f6',
};
const btnPrimary: React.CSSProperties = {
  padding: '6px 14px', background: '#2563eb', color: '#fff',
  border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 13,
};
const btnSec: React.CSSProperties = {
  padding: '6px 14px', background: '#e5e7eb', color: '#374151',
  border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 13,
};
const btnSmall: React.CSSProperties = {
  padding: '2px 10px', background: '#e5e7eb', color: '#374151',
  border: 'none', borderRadius: 3, cursor: 'pointer', fontSize: 12,
};
const btnSmallDanger: React.CSSProperties = {
  background: 'none', border: 'none', cursor: 'pointer', padding: '2px 6px', fontSize: 14,
};
