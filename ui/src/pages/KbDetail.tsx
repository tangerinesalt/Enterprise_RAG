import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { kbApi } from '../api';
import type { FileItem } from '../api';
import styles from './KbDetail.module.css';

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
      <button onClick={() => navigate('/kb')} className={styles.backLink}>← 返回</button>
      <h2 className={styles.title}>📁 {name}</h2>

      <div className={styles.actions}>
        <button onClick={() => fileRef.current?.click()} className={styles.btnPrimary}>📄 上传文件</button>
        <button onClick={() => folderRef.current?.click()} className={styles.btnPrimary}>📁 上传文件夹</button>
        <button onClick={handleIndexAll} className={styles.btnSec}>⚡ 索引全部</button>
      </div>

      <input ref={fileRef} type="file" multiple style={{ display: 'none' }} onChange={() => handleUpload(false)} />
      <input ref={folderRef} type="file" style={{ display: 'none' }} onChange={() => handleUpload(true)} {...{ 'webkitdirectory': '' } as any} />

      {files.length === 0 && <p className={styles.empty}>暂无文件</p>}

      <div className={styles.fileList}>
        {files.map(f => (
          <div key={f.name} className={styles.row}>
            <span className={styles.rowName}>{f.type === 'folder' ? '📁' : '📄'} {f.name}</span>
            <span className={styles.rowSize}>{f.size_str}</span>
            <div className={styles.rowActions}>
              <button onClick={() => handleIndex(f.name)} className={styles.btnSmall}>索引</button>
              <button onClick={() => handleDelete(f.name)} className={styles.btnSmallDanger}>🗑️</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
