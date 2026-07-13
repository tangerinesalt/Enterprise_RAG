import { useLocation, useNavigate } from 'react-router-dom';
import styles from './NavBar.module.css';

const tabs = [
  { path: '/kb', icon: '📁', label: '知识库' },
  { path: '/session', icon: '💬', label: '会话' },
];

export default function NavBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const current = location.pathname.startsWith('/session') ? '/session' : '/kb';

  return (
    <nav className={styles.nav}>
      <div className={styles.navCenter}>
        {tabs.map(tab => (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            className={current === tab.path ? styles.tabActive : styles.tab}
          >
            <span className={styles.navIcon}>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
}
