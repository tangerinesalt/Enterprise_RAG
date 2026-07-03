import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { kbApi } from '../api';
import type { KbItem } from '../api';
import styles from './KbList.module.css';

export default function KbList() {
  const [list, setList] = useState<KbItem[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const navigate = useNavigate();

  const load = () => kbApi.list().then(setList).catch(console.error);

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    await kbApi.create(newName.trim());
    setNewName('');
    setShowCreate(false);
    load();
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`确定删除知识库「${name}」？`)) return;
    await kbApi.delete(name);
    load();
  };

  return (
    <div>
      <div className={styles.header}>
        <h2 className={styles.title}>知识库</h2>
        <button onClick={() => setShowCreate(true)} className={styles.btnPrimary}>+ 新建</button>
      </div>

      {showCreate && (
        <div className={styles.createForm}>
          <input
            autoFocus
            value={newName}
            onChange={e => setNewName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCreate()}
            placeholder="知识库名称"
            className={styles.input}
          />
          <button onClick={handleCreate} className={styles.btnPrimary}>确认</button>
          <button onClick={() => setShowCreate(false)} className={styles.btnSec}>取消</button>
        </div>
      )}

      {list.length === 0 && <p className={styles.empty}>暂无知识库</p>}

      <div className={styles.list}>
        {list.map(item => (
          <div
            key={item.name}
            className={styles.row}
            onClick={() => navigate(`/kb/${item.name}`)}
          >
            <span className={styles.rowName}>📁 {item.name}</span>
            <span className={styles.rowMeta}>
              {item.files} 文件 {item.folders > 0 ? ` ${item.folders} 文件夹` : ''}
            </span>
            <button
              onClick={e => { e.stopPropagation(); handleDelete(item.name); }}
              className={styles.btnDanger}
            >🗑️</button>
          </div>
        ))}
      </div>
    </div>
  );
}
