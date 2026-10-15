import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { errorMessage, learning, readLocal, writeLocal } from './api';
import type { Course, LevelId, PlacementResult, Progress } from './api';
import { Audio, ErrorNotice, LearningNav } from './common';
import styles from './learning.module.css';

export function RussianHome() {
  const [course, setCourse] = useState<Course | null>(null);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const [level, setLevel] = useState<LevelId>(() => {
    const value = readLocal('russian-level');
    return value === 'intermediate' || value === 'advanced' ? value : 'beginner';
  });
  const [checking, setChecking] = useState(false);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [assisted, setAssisted] = useState(false);
  const [revealed, setRevealed] = useState<Record<string, boolean>>({});
  const [result, setResult] = useState<PlacementResult | null>(null);
  const [busy, setBusy] = useState(false);
  const guard = useRef(false);

  useEffect(() => {
    const controller = new AbortController();
    setError('');
    Promise.all([learning.catalog(controller.signal), learning.progress(controller.signal)])
      .then(([nextCourse, nextProgress]) => { setCourse(nextCourse); setProgress(nextProgress); })
      .catch((e: unknown) => { if (!controller.signal.aborted) setError(errorMessage(e)); });
    return () => controller.abort();
  }, [revision]);

  function choose(next: LevelId) { setLevel(next); writeLocal('russian-level', next); }
  async function submitPlacement() {
    if (guard.current) return;
    guard.current = true; setBusy(true); setError('');
    try { setResult(await learning.placement(answers, assisted)); }
    catch (e) { setError(errorMessage(e)); }
    finally { guard.current = false; setBusy(false); }
  }

  if (!course || !progress) return <main className={styles.page}>
    {error ? <ErrorNotice message={error} retry={() => setRevision((r) => r + 1)} /> : <p role="status">Yuklanmoqda…</p>}
    <Link to="/uzbek">Узбекский для русскоговорящих</Link>
  </main>;
  const selected = course.levels.find((item) => item.id === level);
  return <main className={styles.page}>
    <header className={styles.hero}><span className={styles.eyebrow}>AQLLIFY · O‘Z SUR’ATINGIZDA</span>
      <h1>{course.title}</h1><p>{course.description}</p>
      <button className={styles.secondary} onClick={() => { setChecking(!checking); setResult(null); }}>Darajamni tekshirish</button>
    </header>
    {error && <ErrorNotice message={error} retry={() => setRevision((r) => r + 1)} />}
    {checking && <section className={styles.panel} aria-label="Darajani tekshirish">
      <h2>Qayerdan boshlash qulay?</h2><p>6 ta qisqa savol. Natija taxminiy: erkin gapirishni baholamaydi. Darajani o‘zingiz ham tanlashingiz mumkin.</p>
      {!result ? <>
        {course.placement.map((q, index) => <fieldset key={q.id} className={styles.question}>
          <legend>{index + 1}. {q.prompt}</legend>
          {q.audio && <Audio name={q.audio} label={`${index + 1}-savol audiosi`} />}
          {q.transcript && <><button type="button" className={styles.textButton} onClick={() => { setAssisted(true); setRevealed((old) => ({ ...old, [q.id]: true })); }}>Matnni yordam sifatida ko‘rish</button>
            {revealed[q.id] && <p lang="ru">{q.transcript}</p>}</>}
          {q.options.map((option) => <label className={styles.option} key={option}>
            <input type="radio" name={q.id} checked={answers[q.id] === option} onChange={() => setAnswers((old) => ({ ...old, [q.id]: option }))} />{option}
          </label>)}
        </fieldset>)}
        <button className={styles.primary} disabled={busy || Object.keys(answers).length !== course.placement.length} onClick={() => void submitPlacement()}>{busy ? 'Tekshirilmoqda…' : 'Tavsiyani ko‘rish'}</button>
      </> : <div role="status"><h3>Tavsiya: {course.levels.find((l) => l.id === result.level)?.title}</h3>
        <p>{result.score}/6 · {result.assisted ? 'Matn yordami bilan' : 'Matn yordamisiz'}</p>
        <p>O‘qish: {result.skills.reading}/2 · Tinglash: {result.skills.listening}/2 · Mos javobni tanlash: {result.skills.response}/2</p>
        <button className={styles.primary} onClick={() => { choose(result.level); setChecking(false); }}>Shu darajani ko‘rish</button>
      </div>}
      <button className={styles.textButton} onClick={() => setChecking(false)}>Hozircha o‘zim tanlayman</button>
    </section>}
    <div className={styles.levels} aria-label="Darajani tanlang">
      {course.levels.map((item) => <button key={item.id} className={level === item.id ? styles.selectedLevel : styles.level}
        aria-pressed={level === item.id} onClick={() => choose(item.id)}>{item.title}<small>{item.available ? '12 ta vaziyat' : 'Dastur bilan tanishing'}</small></button>)}
    </div>
    {selected && <section className={styles.panel}><h2>{selected.title}</h2><p>{selected.description}</p>
      {!selected.available && <p className={styles.notice}>To‘liq darslar tayyorlanmoqda. Quyida bosqich dasturi va maqsadlari berilgan.</p>}
      <details open={!selected.available}><summary>Kim uchun va nimalarni o‘rganamiz?</summary>
        <ul>{selected.entry.map((line) => <li key={line}>{line}</li>)}</ul>
        {selected.units.map((unit) => <div className={styles.unit} key={unit.title}><h3>{unit.title}</h3><p>{unit.task}</p></div>)}
      </details>
      <details><summary>Keyingi bosqichga qachon o‘taman?</summary><ul>{selected.completion.map((line) => <li key={line}>{line}</li>)}</ul></details>
      {!selected.available && <button className={styles.secondary} onClick={() => choose('beginner')}>Boshlang‘ich mashqlarga qaytish</button>}
    </section>}
    {level === 'beginner' && <>
      <details className={styles.panel}><summary>Kirill yozuvi bo‘yicha yordam</summary>
        {course.alphabet.map((unit) => <div className={styles.unit} key={unit.title}><h3>{unit.title}</h3><p>{unit.task}</p></div>)}
      </details>
      <div className={styles.lessonList}>{course.lessons.map((lesson) => {
        const saved = progress.lessons.find((item) => item.lesson_id === lesson.id);
        return <Link to={`/learn/lesson/${lesson.id}`} className={styles.lesson} key={lesson.id}>
          <span className={styles.order}>{String(lesson.order).padStart(2, '0')}</span><span><h3>{lesson.title}</h3><p>{lesson.goal}</p>
            {saved && <small>{saved.completed ? 'Bajarilgan' : 'Mashq qilingan'} · eng yaxshi natija {Math.round(saved.best_score * 100)}%</small>}</span><span aria-hidden="true">→</span>
        </Link>;
      })}</div>
    </>}
    <p className={styles.legacy}><Link to="/uzbek">Узбекский для русскоговорящих →</Link></p>
    <LearningNav />
  </main>;
}
