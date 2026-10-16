import { Navigate, useNavigate } from 'react-router-dom';
import type { Direction } from '@/shared/direction';
import { readLocal, writeLocal } from '@/shared/storage';
import styles from './DirectionPage.module.css';

export function DirectionPage() {
  const navigate = useNavigate();
  const saved = readLocal('direction');

  if (saved === 'ru') return <Navigate to="/ru" replace />;
  if (saved === 'uz') return <Navigate to="/uz" replace />;

  function choose(direction: Direction) {
    writeLocal('direction', direction);
    navigate(`/${direction}`);
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Aqllify</h1>
        <p className={styles.subline}>Kursni tanlang · Выберите курс</p>
      </header>
      <div className={styles.cards}>
        <button type="button" className={styles.card} onClick={() => choose('ru')}>
          <span className={styles.cardBody}>
            <span className={styles.cardTitle}>Rus tili</span>
            <span className={styles.cardText}>Rus tilini o‘zbekcha tushuntirishlar bilan o‘rganish</span>
          </span>
          <span className={styles.cardArrow} aria-hidden="true">→</span>
        </button>
        <button type="button" className={styles.card} onClick={() => choose('uz')}>
          <span className={styles.cardBody}>
            <span className={styles.cardTitle}>Узбекский язык</span>
            <span className={styles.cardText}>Разговорный узбекский для русскоязычных</span>
          </span>
          <span className={styles.cardArrow} aria-hidden="true">→</span>
        </button>
      </div>
    </main>
  );
}
