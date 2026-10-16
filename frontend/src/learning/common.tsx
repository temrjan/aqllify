import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { mediaUrl } from './api';
import styles from './learning.module.css';

export function Audio({ name, label }: { name: string; label: string }) {
  const ref = useRef<HTMLAudioElement>(null);
  const [failed, setFailed] = useState(false);
  const [slow, setSlow] = useState(false);
  return <div className={styles.audio}>
    <audio ref={ref} controls preload="none" src={mediaUrl(name)} aria-label={label}
      onError={() => setFailed(true)} onCanPlay={() => setFailed(false)} />
    <label><input type="checkbox" checked={slow} onChange={(event) => {
      setSlow(event.target.checked);
      if (ref.current) ref.current.playbackRate = event.target.checked ? 0.8 : 1;
    }} /> Sekinroq</label>
    {failed && <p role="alert">Audio yuklanmadi. <button type="button" onClick={() => {
      setFailed(false); ref.current?.load();
    }}>Qayta yuklash</button></p>}
  </div>;
}

export function BackLink() { return <Link className={styles.back} to="/ru">← Darslarga</Link>; }

export function ErrorNotice({ message, retry }: { message: string; retry?: () => void }) {
  return <div className={styles.error} role="alert"><p>{message}</p>
    {retry && <button type="button" onClick={retry}>Qayta urinish</button>}</div>;
}
