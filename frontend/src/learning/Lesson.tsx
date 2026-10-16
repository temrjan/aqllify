import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import WebApp from '@twa-dev/sdk';
import { errorMessage, learning, readLocal, writeLocal } from './api';
import type { Attempt, ChatMessage, Completion, Lesson } from './api';
import { Audio, BackLink, ErrorNotice } from './common';
import styles from './learning.module.css';

function Conversation({ lessonId }: { lessonId: string }) {
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [message, setMessage] = useState('');
  const [feedback, setFeedback] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const guard = useRef(false);
  async function send() {
    if (guard.current || !message.trim() || history.length >= 8) return;
    guard.current = true; setBusy(true); setError('');
    try {
      const result = await learning.chat(lessonId, message, history);
      setHistory([...history, { role: 'user', content: message }, { role: 'assistant', content: result.reply }]);
      setFeedback(result.feedback); setMessage('');
    } catch (e) { setError(errorMessage(e)); }
    finally { guard.current = false; setBusy(false); }
  }
  return <section className={styles.panel}>
    <h2>Ixtiyoriy suhbat mashqi</h2><p>Vaziyat bo‘yicha ruscha yozing. Bu mashq ball bermaydi; AI javobida xato bo‘lishi mumkin.</p>
    <div aria-live="polite">{history.map((line, i) => <p className={line.role === 'user' ? styles.userLine : styles.botLine} key={i} lang="ru"><strong>{line.role === 'user' ? 'Siz' : 'Suhbatdosh'}: </strong>{line.content}</p>)}</div>
    {feedback && <p className={styles.notice}>{feedback}</p>}
    {error && <ErrorNotice message={error} />}
    {history.length < 8 ? <form onSubmit={(event) => { event.preventDefault(); void send(); }}>
      <label className={styles.inputLabel}>Javobingiz<textarea lang="ru" value={message} maxLength={500} disabled={busy} onChange={(e) => setMessage(e.target.value)} /></label>
      <button className={styles.primary} disabled={busy || !message.trim()}>{busy ? 'Javob kutilmoqda…' : 'Yuborish'}</button>
    </form> : <><p>Qisqa suhbat tugadi. Xohlasangiz, yangi tafsilotlar bilan yana mashq qiling.</p>
      <button className={styles.secondary} onClick={() => { setHistory([]); setFeedback(''); }}>Yangi suhbat</button></>}
  </section>;
}

export function RussianLesson() {
  const { lessonId = '' } = useParams<{ lessonId: string }>();
  // A route key in App ensures lesson-specific state cannot leak across lessons.
  const owner = WebApp.initDataUnsafe.user?.id ?? 'current';
  const storageKey = `russian-attempt:${owner}:${lessonId}`;
  const requestId = useRef(readLocal(storageKey) ?? crypto.randomUUID());
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [phase, setPhase] = useState<'study' | 'practice'>('study');
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState('');
  const [completion, setCompletion] = useState<Completion | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const guard = useRef(false);

  useEffect(() => {
    const controller = new AbortController();
    setError('');
    learning.lesson(lessonId, controller.signal).then(setLesson)
      .catch((e: unknown) => { if (!controller.signal.aborted) setError(errorMessage(e)); });
    return () => controller.abort();
  }, [lessonId, reload]);

  async function start(fresh = false) {
    if (guard.current || !lesson) return;
    if (fresh) requestId.current = crypto.randomUUID();
    writeLocal(storageKey, requestId.current);
    guard.current = true; setBusy(true); setError('');
    try {
      const saved = await learning.start(requestId.current, lessonId);
      setAttempt(saved); setCompletion(null); setAnswer('');
      const next = lesson.exercises.findIndex((ex) => !saved.answers[ex.id]);
      setIndex(next === -1 ? lesson.exercises.length : next);
      setPhase('practice');
    } catch (e) { setError(errorMessage(e)); }
    finally { guard.current = false; setBusy(false); }
  }
  async function submit() {
    const exercise = lesson?.exercises[index];
    if (guard.current || !attempt || !exercise || !answer.trim() || attempt.answers[exercise.id]) return;
    guard.current = true; setBusy(true); setError('');
    try {
      const result = await learning.answer(attempt.id, exercise.id, answer);
      setAttempt({ ...attempt, answers: { ...attempt.answers, [exercise.id]: result } });
    } catch (e) { setError(errorMessage(e)); }
    finally { guard.current = false; setBusy(false); }
  }
  async function finish() {
    if (guard.current || !attempt) return;
    guard.current = true; setBusy(true); setError('');
    try { setCompletion(await learning.complete(attempt.id)); }
    catch (e) { setError(errorMessage(e)); }
    finally { guard.current = false; setBusy(false); }
  }

  if (!lesson) return <main className={styles.page}><BackLink />
    {error ? <ErrorNotice message={error} retry={() => setReload((r) => r + 1)} /> : <p role="status">Dars yuklanmoqda…</p>}
  </main>;
  const exercise = lesson.exercises[index];
  const result = exercise && attempt?.answers[exercise.id];
  return <main className={styles.page}>
    <BackLink />
    <header className={styles.lessonHeader}><span className={styles.eyebrow}>{lesson.order}-DARS · BOSHLANG‘ICH</span><h1>{lesson.title}</h1><p>{lesson.goal}</p></header>
    {error && <ErrorNotice message={error} />}
    {error && <button className={styles.textButton} disabled={busy} onClick={() => void start(true)}>Yangi urinish boshlash</button>}
    {phase === 'study' ? <>
      <section className={styles.panel}><h2>Suhbatda kerak bo‘ladi</h2>
        {lesson.phrases.map((phrase) => <article key={phrase.id} className={styles.phrase}>
          <p lang="ru" className={styles.russian}>{phrase.russian}</p><p>{phrase.uzbek}</p>
          <Audio name={phrase.audio} label={`${phrase.russian} — tinglash`} />
        </article>)}
        <p className={styles.notice}>Tinglang, keyin ovoz chiqarib takrorlang. Talaffuz bu yerda avtomatik baholanmaydi.</p>
      </section>
      <section className={styles.panel}><h2>Qisqa tushuntirish</h2><p>{lesson.explanation}</p></section>
      <section className={styles.panel}><h2>Kichik suhbat</h2>{lesson.dialogue.map((line, i) => <div className={styles.dialogue} key={i}>
        <strong>{line.speaker}</strong><p lang="ru">{line.russian}</p><small>{line.uzbek}</small>
      </div>)}</section>
      <button className={styles.primary} disabled={busy} onClick={() => void start()}>{busy ? 'Yuklanmoqda…' : 'Mashqlarni boshlash / davom ettirish'}</button>
    </> : completion ? <>
      <section className={styles.panel} role="status"><span className={styles.eyebrow}>NATIJA SAQLANDI</span>
        <h2>{completion.completed ? 'Dars bajarildi' : 'Mashq natijasi saqlandi'}</h2>
        <p>Bu urinish: {Math.round(completion.score * 100)}% · Kurs bo‘yicha jami: {completion.total_xp} XP</p>
        <p>{completion.completed ? 'Iboralar takrorlashga qo‘shildi. Bu natija til darajasi sertifikati emas.' : 'Darsni bajarish uchun kamida 80% kerak. Misollarni ko‘rib, yana urinib ko‘ring.'}</p>
        <div className={styles.actions}><button className={styles.secondary} disabled={busy} onClick={() => void start(true)}>Yana mashq qilish</button><Link to="/ru/review">Iboralarni takrorlash →</Link></div>
      </section>
      {attempt && Object.entries(attempt.answers).filter(([, item]) => !item.correct).map(([id, item]) => <section className={styles.panel} key={id}>
        <h3>{lesson.exercises.find((ex) => ex.id === id)?.prompt}</h3><p lang="ru">Sizning javobingiz: {item.answer}</p><p lang="ru">Namuna: {item.corrected}</p><p>{item.feedback}</p>
      </section>)}
      <Conversation lessonId={lessonId} />
    </> : exercise ? <section className={styles.panel}>
      <div className={styles.exerciseHeading}><span>{index + 1} / {lesson.exercises.length}</span><span>{exercise.transfer ? 'Yangi vaziyat' : 'Mashq'}</span></div>
      <progress value={index} max={lesson.exercises.length} aria-label="Mashqlar bajarilishi" />
      <h2>{exercise.prompt}</h2>
      <form onSubmit={(event) => { event.preventDefault(); void submit(); }}>
        {exercise.kind === 'choice' ? <fieldset className={styles.question}><legend className={styles.srOnly}>Javobni tanlang</legend>
          {exercise.options.map((option) => <label className={styles.option} key={option}>
            <input type="radio" name="answer" value={option} checked={(result?.answer ?? answer) === option} disabled={busy || !!result}
              onChange={() => setAnswer(option)} />{option}
          </label>)}
        </fieldset> : <label className={styles.inputLabel}>Ruscha javob<input lang="ru" autoComplete="off" maxLength={500} value={result?.answer ?? answer}
          disabled={busy || !!result} onChange={(e) => setAnswer(e.target.value)} /></label>}
        {!result && <button className={styles.primary} disabled={busy || !answer.trim()}>{busy ? 'Saqlanmoqda…' : 'Tekshirish'}</button>}
      </form>
      {result && <div className={result.correct ? styles.success : styles.notice} role="status"><p>{result.feedback}</p>
        {result.corrected && <p lang="ru">Namuna: {result.corrected}</p>}
        <button className={styles.primary} onClick={() => { setIndex(index + 1); setAnswer(''); setError(''); }}>Keyingi</button>
      </div>}
    </section> : <section className={styles.panel}><h2>Mashqlar yakunlandi</h2><p>Natijani saqlang. Qayta bosish qo‘shimcha XP bermaydi.</p>
      <button className={styles.primary} disabled={busy} onClick={() => void finish()}>{busy ? 'Saqlanmoqda…' : 'Natijani saqlash'}</button>
    </section>}
    {phase === 'practice' && <button className={styles.textButton} disabled={busy} onClick={() => setPhase('study')}>Misollarni yana ko‘rish</button>}
  </main>;
}
