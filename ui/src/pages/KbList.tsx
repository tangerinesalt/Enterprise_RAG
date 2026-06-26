import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { kbApi } from '../api';
import type { KbItem } from '../api';

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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>知识库</h2>
        <button onClick={() => setShowCreate(true)} style={btnPrimary}>+ 新建</button>
      </div>

      {showCreate && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          <input
            autoFocus
            value={newName}
            onChange={e => setNewName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCreate()}
            placeholder="知识库名称"
            style={inputStyle}
          />
          <button onClick={handleCreate} style={btnPrimary}>确认</button>
          <button onClick={() => setShowCreate(false)} style={btnSec}>取消</button>
        </div>
      )}

      {list.length === 0 && <p style={{ color: '#9ca3af' }}>暂无知识库</p>}

      {list.map(item => (
        <div
          key={item.name}
          style={rowStyle}
          onClick={() => navigate(`/kb/${item.name}`)}
        >
          <span style={{ fontWeight: 500 }}>📁 {item.name}</span>
          <span style={{ color: '#6b7280', fontSize: 14 }}>
            {item.files} 文件 {item.folders > 0 ? ` ${item.folders} 文件夹` : ''}
          </span>
          <button
            onClick={e => { e.stopPropagation(); handleDelete(item.name); }}
            style={btnDanger}
          >🗑️</button>
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
// NOTE: hover style removed — TypeScript 6 rejects it on CSSProperties.
// Use index.css or styled-jsx for :hover instead.

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
