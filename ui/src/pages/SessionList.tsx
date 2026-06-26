import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { sessionApi } from '../api';
import type { SessionItem } from '../api';

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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>会话</h2>
        <button onClick={() => setShowCreate(true)} style={btnPrimary}>+ 新建</button>
      </div>

      {showCreate && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          <input autoFocus value={newName} onChange={e => setNewName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCreate()}
            placeholder="会话名称" style={inputStyle} />
          <button onClick={handleCreate} style={btnPrimary}>确认</button>
          <button onClick={() => setShowCreate(false)} style={btnSec}>取消</button>
        </div>
      )}

      {list.length === 0 && <p style={{ color: '#9ca3af' }}>暂无会话</p>}

      {list.map(item => (
        <div key={item.name} style={rowStyle} onClick={() => navigate(`/session/${item.name}`)}>
          <span style={{ fontWeight: 500 }}>💬 {item.name}</span>
          <span style={{ color: '#6b7280', fontSize: 14 }}>
            KB: {item.kb_name || '(未绑定)'} · {item.total_chats} 条聊天
          </span>
          <button onClick={e => { e.stopPropagation(); handleDelete(item.name); }} style={btnDanger}>🗑️</button>
        </div>
      ))}
    </div>
  );
}

const rowStyle: React.CSSProperties = {
  display: 'flex', alignItems: 'center', gap: 12,
  padding: '10px 12px', cursor: 'pointer', borderRadius: 6,
  borderBottom: '1px solid #f3f4f6',
};
const btnPrimary: React.CSSProperties = {
  padding: '6px 14px', background: '#2563eb', color: '#fff',
  border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 14,
};
const btnSec: React.CSSProperties = {
  padding: '6px 14px', background: '#e5e7eb', color: '#374151',
  border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 14,
};
const btnDanger: React.CSSProperties = {
  marginLeft: 'auto', background: 'none', border: 'none',
  cursor: 'pointer', fontSize: 16, padding: '4px 8px',
};
const inputStyle: React.CSSProperties = {
  padding: '6px 12px', border: '1px solid #d1d5db',
  borderRadius: 4, fontSize: 14, flex: 1,
};
