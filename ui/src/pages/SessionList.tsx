import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { sessionApi } from '../api';
import type { SessionItem } from '../api';
import styles from './SessionList.module.css';

export default function SessionList() {
  const [list, setList] = useState<SessionItem[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const navigate = useNavigate();

  const load = () => sessionApi.list().then(setList).catch(console.error);
  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    await sessionApi.create(newName.trim());
    setNewName(''); setShowCreate(false);
    load();
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`确定删除会话「${name}」？`)) return;
    await sessionApi.delete(name);
    load();
  };

  return (
    <div>
      <div className={styles.header}>
        <h2 className={styles.title}>会话</h2>
        <button onClick={() => setShowCreate(true)} className={styles.btnPrimary}>+ 新建</button>
      </div>

      {showCreate && (
        <div className={styles.createForm}>
          <input autoFocus value={newName} onChange={e => setNewName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCreate()}
            placeholder="会话名称" className={styles.input} />
          <button onClick={handleCreate} className={styles.btnPrimary}>确认</button>
          <button onClick={() => setShowCreate(false)} className={styles.btnSec}>取消</button>
        </div>
      )}

      {list.length === 0 && <p className={styles.empty}>暂无会话</p>}

      <div className={styles.list}>
        {list.map(item => (
          <div key={item.name} className={styles.row} onClick={() => navigate(`/session/${item.name}`)}>
            <span className={styles.rowName}>💬 {item.name}</span>
            <span className={styles.rowMeta}>
              KB: {item.kb_name || '(未绑定)'} · {item.total_chats} 条聊天
            </span>
            <button onClick={e => { e.stopPropagation(); handleDelete(item.name); }} className={styles.btnDanger}>🗑️</button>
          </div>
        ))}
      </div>
    </div>
  );
}
