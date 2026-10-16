import { useNavigate, useLocation } from 'react-router-dom';
import { directionFromPath } from '@/shared/direction';
import type { Direction } from '@/shared/direction';
import styles from './TabBar.module.css';

type IconName = 'lesson' | 'review' | 'progress' | 'courses';

const TABS: Record<Direction, readonly { path: string; label: string; icon: IconName }[]> = {
  ru: [
    { path: '/ru', label: 'Darslar', icon: 'lesson' },
    { path: '/ru/review', label: 'Takrorlash', icon: 'review' },
    { path: '/ru/progress', label: 'Natijalar', icon: 'progress' },
    { path: '/?reset=1', label: 'Kurslar', icon: 'courses' },
  ],
  uz: [
    { path: '/uz', label: 'Уроки', icon: 'lesson' },
    { path: '/uz/review', label: 'Повтор', icon: 'review' },
    { path: '/uz/progress', label: 'Прогресс', icon: 'progress' },
    { path: '/?reset=1', label: 'Курсы', icon: 'courses' },
  ],
};

function TabIcon({ icon, active }: { icon: IconName; active: boolean }) {
  const color = active ? 'var(--accent)' : 'var(--tg-hint)';

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
    case 'courses':
      return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
        </svg>
      );
    default:
      return null;
  }
}

export function TabBar() {
  const navigate = useNavigate();
  const location = useLocation();
  const direction = directionFromPath(location.pathname);

  if (!direction) return null;

  return (
    <nav className={styles.tabBar}>
      {TABS[direction].map((tab) => {
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
