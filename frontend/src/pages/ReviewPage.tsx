import { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import { api } from '@/shared/api';
import styles from './ReviewPage.module.css';

interface Card {
  id: number;
  word: string;
  translation: string;
}

export function ReviewPage() {
  const [cards, setCards] = useState<Card[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [completed, setCompleted] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/progress/review')
      .then((res) => setCards(res.data))
      .catch(() => setCards([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className={styles.page}><div className={styles.center}>Загрузка...</div></div>;
  }

  if (cards.length === 0) {
    return (
      <div className={styles.page}>
        <div className={styles.empty}>
          <span className={styles.emptyIcon}>&#9989;</span>
          <h2 className={styles.emptyTitle}>Всё повторено!</h2>
          <p className={styles.emptyText}>Новые карточки появятся после следующего урока</p>
        </div>
      </div>
    );
  }

  const card = cards[currentIndex];

  if (!card) {
    return (
      <div className={styles.page}>
        <div className={styles.empty}>
          <span className={styles.emptyIcon}>&#127881;</span>
          <h2 className={styles.emptyTitle}>Повторение завершено!</h2>
          <p className={styles.emptyText}>Повторено: {completed} слов</p>
        </div>
      </div>
    );
  }

  const handleRate = async (quality: number) => {
    try {
      await api.post('/progress/review', {
        card_id: card.id,
        quality,
      });

      if (quality >= 3) {
        WebApp.HapticFeedback.notificationOccurred('success');
      } else {
        WebApp.HapticFeedback.impactOccurred('light');
      }
    } catch {
      // continue regardless
    }

    setCompleted((prev) => prev + 1);
    setShowAnswer(false);
    setCurrentIndex((prev) => prev + 1);
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <span className={styles.counter}>{currentIndex + 1} / {cards.length}</span>
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{ width: `${((currentIndex + 1) / cards.length) * 100}%` }}
          />
        </div>
      </header>

      <div className={styles.cardArea}>
        <div
          className={`${styles.card} ${showAnswer ? styles.cardFlipped : ''}`}
          onClick={() => setShowAnswer(true)}
        >
          <div className={styles.cardFront}>
            <p className={styles.cardWord}>{card.word}</p>
            <p className={styles.cardHint}>Нажми, чтобы увидеть перевод</p>
          </div>
          {showAnswer && (
            <div className={styles.cardBack}>
              <p className={styles.cardTranslation}>{card.translation}</p>
            </div>
          )}
        </div>
      </div>

      {showAnswer && (
        <div className={styles.rateButtons}>
          <button className={styles.rateBtnHard} onClick={() => handleRate(1)}>
            Не помню
          </button>
          <button className={styles.rateBtnOk} onClick={() => handleRate(3)}>
            Вспомнил
          </button>
          <button className={styles.rateBtnEasy} onClick={() => handleRate(5)}>
            Легко
          </button>
        </div>
      )}
    </div>
  );
}
