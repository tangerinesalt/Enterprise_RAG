import { useLocation, useNavigate } from 'react-router-dom';

const tabs = [
  { path: '/kb', label: '📚 知识库' },
  { path: '/session', label: '💬 会话' },
];

export default function NavBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const current = location.pathname.startsWith('/session') ? '/session' : '/kb';

  return (
    <nav style={{
      display: 'flex', gap: 0, borderBottom: '2px solid #e5e7eb',
      background: '#f9fafb', padding: '0 16px',
    }}>
      {tabs.map(tab => (
        <button
          key={tab.path}
          onClick={() => navigate(tab.path)}
          style={{
            padding: '12px 24px', border: 'none', cursor: 'pointer',
            fontSize: 15, fontWeight: current === tab.path ? 600 : 400,
            color: current === tab.path ? '#2563eb' : '#6b7280',
            borderBottom: current === tab.path ? '2px solid #2563eb' : '2px solid transparent',
            marginBottom: -2, background: 'transparent',
          }}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
