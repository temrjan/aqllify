import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { errorMessage, learning } from './api';
import type { ReviewCard } from './api';
import { Audio, ErrorNotice } from './common';
import styles from './learning.module.css';

export function RussianReview() {
  const [cards, setCards] = useState<ReviewCard[] | null>(null);
  const [show, setShow] = useState(false);
  const [error, setError] = useState('');
  const [reload, setReload] = useState(0);
  const [busy, setBusy] = useState(false);
  const guard = useRef(false);
  useEffect(() => {
    const controller = new AbortController(); setError(''); setCards(null);
    learning.reviews(controller.signal).then((result) => { setCards(result); setShow(false); })
      .catch((e: unknown) => { if (!controller.signal.aborted) setError(errorMessage(e)); });
    return () => controller.abort();
  }, [reload]);
  const card = cards?.[0];
  async function rate(rating: 'again' | 'remembered') {
    if (guard.current || !card) return;
    guard.current = true; setBusy(true); setError('');
    try { await learning.rate(card, rating); setCards((current) => current?.slice(1) ?? []); setShow(false); }
    catch (e) { setError(errorMessage(e)); }
    finally { guard.current = false; setBusy(false); }
  }
  return <main className={styles.page}><header className={styles.lessonHeader}><h1>Iboralarni eslaymiz</h1><p>Avval ruschasini o‘zingiz ayting, keyin namunani oching. Bu o‘zingiz baholaydigan mashq, bilim darajasi testi emas.</p></header>
    {error && <ErrorNotice message={error} retry={() => setReload((r) => r + 1)} />}
    {!cards && !error && <p role="status">Yuklanmoqda…</p>}
    {card ? <section className={styles.panel}>
      <span className={styles.eyebrow}>{cards?.length} TA IBORA</span><h2>{card.uzbek}</h2>
      {!show ? <button className={styles.primary} onClick={() => setShow(true)}>Ruschasini ko‘rish</button> : <>
        <p lang="ru" className={styles.russian}>{card.russian}</p><Audio name={card.audio} label={card.russian} />
        <div className={styles.actions}><button className={styles.secondary} disabled={busy} onClick={() => void rate('again')}>Yana mashq qilaman</button>
          <button className={styles.primary} disabled={busy} onClick={() => void rate('remembered')}>Esladim</button></div>
      </>}
    </section> : cards && !error && <section className={styles.panel}><h2>Hozircha navbat bo‘sh</h2><p>Keyingi takrorlash vaqti kelganda iboralar yana chiqadi. Yangi darsni tugatsangiz, uning iboralari ham qo‘shiladi.</p><Link to="/ru">Darslarni ko‘rish →</Link></section>}
  </main>;
}
