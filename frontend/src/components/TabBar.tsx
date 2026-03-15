import { useNavigate, useLocation } from 'react-router-dom';
import styles from './TabBar.module.css';

const TABS = [
  { path: '/', label: 'Уроки', icon: 'lesson' },
  { path: '/review', label: 'Повтор', icon: 'review' },
  { path: '/progress', label: 'Прогресс', icon: 'progress' },
] as const;

function TabIcon({ icon, active }: { icon: string; active: boolean }) {
  const color = active ? 'var(--accent)' : 'var(--tg-hint, #9CA3AF)';

  switch (icon) {
    case 'lesson':
      return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 19.5A2.5 2.5 0 016.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" />
          <line x1="9" y1="7" x2="16" y2="7" />
          <line x1="9" y1="11" x2="14" y2="11" />
        </svg>
      );
    case 'review':
      return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 6v6l4 2" />
        </svg>
      );
    case 'progress':
      return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="20" x2="18" y2="10" />
          <line x1="12" y1="20" x2="12" y2="4" />
          <line x1="6" y1="20" x2="6" y2="14" />
        </svg>
      );
    default:
      return null;
  }
}

export function TabBar() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <nav className={styles.tabBar}>
      {TABS.map((tab) => {
        const active = location.pathname === tab.path;
        return (
          <button
            key={tab.path}
            className={`${styles.tab} ${active ? styles.tabActive : ''}`}
            onClick={() => navigate(tab.path)}
          >
            <TabIcon icon={tab.icon} active={active} />
            <span className={styles.label}>{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
