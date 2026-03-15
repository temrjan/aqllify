import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/shared/api';
import styles from './HomePage.module.css';

interface LessonListItem {
  slug: string;
  title: string;
  block: number;
  lesson: number;
  completed: boolean;
  score: number;
}

export function HomePage() {
  const [lessons, setLessons] = useState<LessonListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/lessons/uzlearn')
      .then((res) => setLessons(res.data))
      .catch(() => setLessons([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className={styles.page}><div className={styles.loading}>Загрузка...</div></div>;
  }

  if (lessons.length === 0) {
    return (
      <div className={styles.page}>
        <div className={styles.loading}>Уроки не найдены</div>
      </div>
    );
  }

  // Group lessons by block
  const blocks = new Map<number, LessonListItem[]>();
  for (const lesson of lessons) {
    const blockLessons = blocks.get(lesson.block) ?? [];
    blockLessons.push(lesson);
    blocks.set(lesson.block, blockLessons);
  }

  const isCheckpoint = (lesson: LessonListItem): boolean => {
    return lesson.title.toLowerCase().includes('checkpoint');
  };

  const isLessonUnlocked = (index: number): boolean => {
    if (index === 0) return true;
    return lessons[index - 1]?.completed === true;
  };

  const handleLessonClick = (lesson: LessonListItem, globalIndex: number) => {
    if (!isLessonUnlocked(globalIndex)) return;
    // slug format: "block-1/01-salomlashish" → split into block and lessonSlug
    const parts = lesson.slug.split('/');
    if (parts.length === 2) {
      const prefix = isCheckpoint(lesson) ? '/checkpoint' : '/lesson';
      navigate(`${prefix}/${parts[0]}/${parts[1]}`);
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Уроки</h1>
      </header>

      {Array.from(blocks.entries()).map(([blockNum, blockLessons]) => (
        <section key={blockNum} className={styles.block}>
          <h2 className={styles.blockTitle}>Блок {blockNum}</h2>

          <div className={styles.lessonList}>
            {blockLessons.map((lesson) => {
              const globalIndex = lessons.indexOf(lesson);
              const unlocked = isLessonUnlocked(globalIndex);

              return (
                <button
                  key={lesson.slug}
                  className={[
                    styles.lessonCard,
                    isCheckpoint(lesson) ? styles.checkpointCard : '',
                    !unlocked ? styles.lockedCard : '',
                  ].join(' ')}
                  onClick={unlocked ? () => handleLessonClick(lesson, globalIndex) : undefined}
                >
                  <div className={
                    !unlocked
                      ? styles.lockedNumber
                      : isCheckpoint(lesson)
                        ? styles.checkpointNumber
                        : styles.lessonNumber
                  }>
                    {!unlocked
                      ? '\uD83D\uDD12'
                      : isCheckpoint(lesson)
                        ? '\u2605'
                        : lesson.lesson}
                  </div>
                  <div className={styles.lessonInfo}>
                    <span className={styles.lessonTitle}>{lesson.title}</span>
                    {lesson.completed && (
                      <span className={styles.lessonScore}>{lesson.score} XP</span>
                    )}
                  </div>
                  {lesson.completed && (
                    <span className={styles.completedBadge}>{'\u2713'}</span>
                  )}
                </button>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
