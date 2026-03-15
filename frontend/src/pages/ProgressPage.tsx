import { useState, useEffect } from 'react';
import { api } from '@/shared/api';
import styles from './ProgressPage.module.css';

interface Stats {
  total_xp: number;
  current_title: string;
  next_title: string | null;
  xp_to_next: number;
  streak_days: number;
  streak_freeze_available: boolean;
  words_learned: number;
  lessons_completed: number;
}

const TITLE_LABELS: Record<string, string> = {
  spark: 'Spark',
  pulse: 'Pulse',
  wave: 'Wave',
  flash: 'Flash',
  storm: 'Storm',
  blaze: 'Blaze',
  titan: 'Titan',
  phantom: 'Phantom',
  nova: 'Nova',
  apex: 'Apex',
};

export function ProgressPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/progress/stats')
      .then((res) => setStats(res.data))
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className={styles.page}><div className={styles.center}>Загрузка...</div></div>;
  }

  if (!stats) {
    return <div className={styles.page}><div className={styles.center}>Начни первый урок!</div></div>;
  }

  const xpProgress = stats.next_title
    ? ((stats.total_xp) / (stats.total_xp + stats.xp_to_next)) * 100
    : 100;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Мой прогресс</h1>
      </header>

      {/* Title card */}
      <section className={styles.titleCard}>
        <span className={styles.titleEmoji}>
          {stats.current_title === 'apex' ? '&#11088;' : '&#9889;'}
        </span>
        <div className={styles.titleName}>
          {TITLE_LABELS[stats.current_title] ?? stats.current_title}
        </div>
        <div className={styles.xpTotal}>{stats.total_xp} XP</div>

        {stats.next_title && (
          <div className={styles.xpBarWrap}>
            <div className={styles.xpBar}>
              <div className={styles.xpFill} style={{ width: `${xpProgress}%` }} />
            </div>
            <span className={styles.xpNext}>
              {stats.xp_to_next} XP до {TITLE_LABELS[stats.next_title]}
            </span>
          </div>
        )}
      </section>

      {/* Stats grid */}
      <section className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statValue}>
            {stats.streak_days > 0 ? `${stats.streak_days}` : '0'}
          </div>
          <div className={styles.statLabel}>
            {stats.streak_days > 0 ? 'дней подряд &#128293;' : 'дней подряд'}
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statValue}>{stats.words_learned}</div>
          <div className={styles.statLabel}>слов выучено</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statValue}>{stats.lessons_completed}</div>
          <div className={styles.statLabel}>уроков пройдено</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statValue}>
            {stats.streak_freeze_available ? '&#10003;' : '&#10007;'}
          </div>
          <div className={styles.statLabel}>streak freeze</div>
        </div>
      </section>
    </div>
  );
}
