import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { errorMessage, learning } from './api';
import type { Course, Progress } from './api';
import { BackLink, ErrorNotice, LearningNav } from './common';
import styles from './learning.module.css';

export function RussianProgress() {
  const [data, setData] = useState<{ course: Course; progress: Progress } | null>(null);
  const [error, setError] = useState('');
  const [reload, setReload] = useState(0);
  useEffect(() => {
    const controller = new AbortController(); setError('');
    Promise.all([learning.catalog(controller.signal), learning.progress(controller.signal)])
      .then(([course, progress]) => setData({ course, progress }))
      .catch((e: unknown) => { if (!controller.signal.aborted) setError(errorMessage(e)); });
    return () => controller.abort();
  }, [reload]);
  return <main className={styles.page}><BackLink /><header className={styles.lessonHeader}><h1>Rus tili bo‘yicha natijalar</h1><p>Bajarilgan mashqlarni kuzating. Bu raqamlar erkin gapirish darajasi yoki sertifikat emas.</p></header>
    {error && <ErrorNotice message={error} retry={() => setReload((r) => r + 1)} />}
    {!data && !error && <p role="status">Yuklanmoqda…</p>}
    {data && <><div className={styles.stats}>
      <div><strong>{data.progress.lessons.filter((l) => l.completed).length}/{data.course.lessons.length}</strong><span>Bajarilgan dars</span></div>
      <div><strong>{data.progress.total_xp}</strong><span>Kurs XP</span></div>
      <div><strong>{data.progress.due_count}</strong><span>Takrorlash navbatida</span></div>
    </div><section className={styles.panel}><h2>Amaliy ko‘nikmalar</h2>
      {data.course.lessons.map((lesson) => {
        const saved = data.progress.lessons.find((item) => item.lesson_id === lesson.id);
        return <div className={styles.unit} key={lesson.id}><Link to={`/learn/lesson/${lesson.id}`}>{lesson.title}</Link><p>{lesson.goal}</p>
          <small>{saved ? `Eng yaxshi natija: ${Math.round(saved.best_score * 100)}% · ${saved.completed ? 'bajarilgan' : 'mashq qilingan'}` : 'Hali mashq qilinmagan'}</small></div>;
      })}
    </section></>}
    <LearningNav />
  </main>;
}
