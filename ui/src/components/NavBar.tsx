import { useLocation, useNavigate } from 'react-router-dom';
import styles from './NavBar.module.css';

const tabs = [
  { path: '/kb', label: '📁 知识库' },
  { path: '/session', label: '💬 会话' },
];

export default function NavBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const current = location.pathname.startsWith('/session') ? '/session' : '/kb';

  return (
    <nav className={styles.nav}>
      <span className={styles.logo}>rag_v</span>
      {tabs.map(tab => (
        <button
          key={tab.path}
          onClick={() => navigate(tab.path)}
          className={current === tab.path ? styles.tabActive : styles.tab}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
