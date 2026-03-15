import { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import { api } from '@/shared/api';
import styles from './LessonPage.module.css';

interface Phrase {
  uzbek: string;
  uzbek_cyrillic: string;
  russian: string;
}

interface Exercise {
  type: string;
  prompt: string;
  answer_context: string | null;
  answer: string | null;
  options: string[] | null;
  correct: number | null;
  context: string | null;
  bot_says: string | null;
  xp: number;
}

interface Lesson {
  meta: { title: string; block: number; lesson: number; xp_reward: number };
  phrases: Phrase[];
  grammar: { text: string }[];
  dialog: { lines: string[] } | null;
  homework: { text: string } | null;
  exercises: Exercise[];
}

export function LessonPage() {
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [step, setStep] = useState<'phrases' | 'exercises' | 'done'>('phrases');
  const [exerciseIndex, setExerciseIndex] = useState(0);
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState<string | null>(null);
  const [correct, setCorrect] = useState<boolean | null>(null);
  const [totalXp, setTotalXp] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/lessons/uzlearn/block-1/01-salomlashish')
      .then((res) => setLesson(res.data))
      .catch(() => setLesson(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className={styles.page}><div className={styles.loading}>Загрузка...</div></div>;
  }

  if (!lesson) {
    return <div className={styles.page}><div className={styles.loading}>Урок не найден</div></div>;
  }

  // Phase 1: Show phrases
  if (step === 'phrases') {
    return (
      <div className={styles.page}>
        <header className={styles.header}>
          <span className={styles.lessonNumber}>Урок {lesson.meta.lesson}</span>
          <h1 className={styles.title}>{lesson.meta.title}</h1>
        </header>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Новые фразы</h2>
          {lesson.phrases.map((phrase, i) => (
            <div key={i} className={styles.phraseCard}>
              <div className={styles.phraseUzbek}>{phrase.uzbek}</div>
              {phrase.uzbek_cyrillic && (
                <div className={styles.phraseCyrillic}>{phrase.uzbek_cyrillic}</div>
              )}
              <div className={styles.phraseRussian}>{phrase.russian}</div>
            </div>
          ))}
        </section>

        {lesson.grammar.length > 0 && (
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Грамматика</h2>
            {lesson.grammar.map((tip, i) => (
              <p key={i} className={styles.grammarText}>{tip.text}</p>
            ))}
          </section>
        )}

        {lesson.dialog && (
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Мини-диалог</h2>
            {lesson.dialog.lines.map((line, i) => (
              <p key={i} className={styles.dialogLine}>{line}</p>
            ))}
          </section>
        )}

        <div className={styles.footer}>
          <button className={styles.primaryBtn} onClick={() => setStep('exercises')}>
            Проверить знания
          </button>
        </div>
      </div>
    );
  }

  // Phase 2: Exercises
  if (step === 'exercises') {
    const ex = lesson.exercises[exerciseIndex];
    if (!ex) {
      setStep('done');
      return null;
    }

    const handleSubmit = async () => {
      if (!answer.trim()) return;

      try {
        const res = await api.post('/lessons/check-answer', {
          exercise_type: ex.type,
          prompt: ex.prompt,
          user_answer: answer,
          answer_context: ex.answer_context ?? ex.answer ?? '',
        });

        setCorrect(res.data.correct);
        setFeedback(res.data.feedback);

        if (res.data.correct) {
          setTotalXp((prev) => prev + ex.xp);
          WebApp.HapticFeedback.notificationOccurred('success');
        } else {
          WebApp.HapticFeedback.notificationOccurred('error');
        }
      } catch {
        setFeedback('Ошибка проверки. Попробуй ещё раз.');
      }
    };

    const handleNext = () => {
      setAnswer('');
      setFeedback(null);
      setCorrect(null);

      if (exerciseIndex + 1 < lesson.exercises.length) {
        setExerciseIndex((prev) => prev + 1);
      } else {
        setStep('done');
      }
    };

    const handleChoiceSelect = async (optionIndex: number) => {
      const isCorrect = optionIndex === ex.correct;
      setCorrect(isCorrect);
      setFeedback(isCorrect ? 'Правильно!' : `Правильный ответ: ${ex.options?.[ex.correct ?? 0]}`);

      if (isCorrect) {
        setTotalXp((prev) => prev + ex.xp);
        WebApp.HapticFeedback.notificationOccurred('success');
      } else {
        WebApp.HapticFeedback.notificationOccurred('error');
      }
    };

    return (
      <div className={styles.page}>
        <header className={styles.header}>
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{ width: `${((exerciseIndex + 1) / lesson.exercises.length) * 100}%` }}
            />
          </div>
          <span className={styles.xpCounter}>+{totalXp} XP</span>
        </header>

        <section className={styles.exerciseArea}>
          {ex.type === 'dialog_reply' && ex.context ? (
            <>
              <p className={styles.exerciseContext}>{ex.context}</p>
              {ex.bot_says && <p className={styles.exerciseBotSays}>— {ex.bot_says}</p>}
              <p className={styles.exercisePrompt}>Ответь:</p>
            </>
          ) : (
            <p className={styles.exercisePrompt}>{ex.prompt}</p>
          )}

          {ex.type === 'choice' && ex.options ? (
            <div className={styles.choiceGrid}>
              {ex.options.map((opt, i) => (
                <button
                  key={i}
                  className={`${styles.choiceBtn} ${
                    correct !== null && i === ex.correct ? styles.choiceCorrect : ''
                  } ${correct !== null && correct === false && i !== ex.correct ? styles.choiceWrong : ''}`}
                  onClick={() => handleChoiceSelect(i)}
                  disabled={correct !== null}
                >
                  {opt}
                </button>
              ))}
            </div>
          ) : (
            <div className={styles.inputArea}>
              <input
                className={styles.answerInput}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !feedback && handleSubmit()}
                placeholder="Напиши ответ..."
                disabled={feedback !== null}
                autoFocus
              />
              {!feedback && (
                <button
                  className={styles.submitBtn}
                  onClick={handleSubmit}
                  disabled={!answer.trim()}
                >
                  Проверить
                </button>
              )}
            </div>
          )}

          {feedback && (
            <div className={`${styles.feedback} ${correct ? styles.feedbackCorrect : styles.feedbackWrong}`}>
              {feedback}
            </div>
          )}
        </section>

        {feedback && (
          <div className={styles.footer}>
            <button className={styles.primaryBtn} onClick={handleNext}>
              {exerciseIndex + 1 < lesson.exercises.length ? 'Следующее' : 'Завершить'}
            </button>
          </div>
        )}
      </div>
    );
  }

  // Phase 3: Done
  return (
    <div className={styles.page}>
      <div className={styles.doneScreen}>
        <span className={styles.doneIcon}>&#127881;</span>
        <h2 className={styles.doneTitle}>Урок пройден!</h2>
        <p className={styles.doneXp}>+{totalXp + lesson.meta.xp_reward} XP</p>
        {lesson.homework && (
          <p className={styles.doneHomework}>{lesson.homework.text}</p>
        )}
        <button className={styles.primaryBtn} onClick={() => window.location.reload()}>
          На главную
        </button>
      </div>
    </div>
  );
}
