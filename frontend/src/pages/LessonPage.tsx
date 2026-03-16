import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  words: string[] | null;
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

interface Mistake {
  prompt: string;
  corrected: string;
}

export function LessonPage() {
  const { block, lessonSlug } = useParams<{ block: string; lessonSlug: string }>();
  const navigate = useNavigate();

  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [step, setStep] = useState<'phrases' | 'exercises' | 'done'>('phrases');
  const [exerciseIndex, setExerciseIndex] = useState(0);
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState<string | null>(null);
  const [correct, setCorrect] = useState<boolean | null>(null);
  const [totalXp, setTotalXp] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedWords, setSelectedWords] = useState<string[]>([]);
  const [availableWords, setAvailableWords] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [mistakes, setMistakes] = useState<Mistake[]>([]);

  // ═══ ALL useEffects at the top, before any returns ═══

  // Load lesson
  useEffect(() => {
    if (!block || !lessonSlug) {
      setLoading(false);
      return;
    }
    api.get(`/lessons/uzlearn/${block}/${lessonSlug}`)
      .then((res) => setLesson(res.data))
      .catch(() => setLesson(null))
      .finally(() => setLoading(false));
  }, [block, lessonSlug]);

  // Transition to done when exercises are exhausted
  useEffect(() => {
    if (step === 'exercises' && lesson && exerciseIndex >= lesson.exercises.length) {
      setStep('done');
    }
  }, [step, exerciseIndex, lesson]);

  // Init build_sentence words when exercise changes
  useEffect(() => {
    if (step !== 'exercises' || !lesson) return;
    const ex = lesson.exercises[exerciseIndex];
    if (ex?.type === 'build_sentence' && ex.words) {
      setAvailableWords([...ex.words].sort(() => Math.random() - 0.5));
      setSelectedWords([]);
    }
  }, [step, exerciseIndex, lesson]);

  // Save progress when done
  useEffect(() => {
    if (step !== 'done' || saved || saving || !block || !lessonSlug || !lesson) return;
    setSaving(true);
    const xpTotal = totalXp + (lesson.meta?.xp_reward ?? 50);
    const exerciseCount = lesson.exercises?.length ?? 1;
    api.post('/progress/complete-lesson', {
      lesson_slug: `${block}/${lessonSlug}`,
      xp: xpTotal,
      score: exerciseCount > 0 ? totalXp / (exerciseCount * 10) : 1,
    })
      .then(() => {
        try { WebApp.HapticFeedback.notificationOccurred('success'); } catch {}
      })
      .catch(() => {})
      .finally(() => {
        setSaving(false);
        setSaved(true);
      });
  }, [step, saved, saving, block, lessonSlug, totalXp, lesson]);

  // ═══ Handlers (stable references) ═══

  const handleRetry = useCallback(() => {
    setStep('exercises');
    setExerciseIndex(0);
    setAnswer('');
    setFeedback(null);
    setCorrect(null);
    setTotalXp(0);
    setSelectedWords([]);
    setAvailableWords([]);
    setMistakes([]);
    setSaved(false);
    setSaving(false);
  }, []);

  // ═══ Render ═══

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
      return <div className={styles.page}><div className={styles.loading}>Загрузка...</div></div>;
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
          const promptText = ex.type === 'dialog_reply' ? (ex.bot_says ?? ex.prompt) : ex.prompt;
          setMistakes((prev) => [...prev, {
            prompt: promptText,
            corrected: res.data.corrected ?? res.data.feedback ?? '',
          }]);
        }
      } catch {
        setFeedback('Ошибка проверки. Попробуй ещё раз.');
      }

      // Close keyboard and scroll to see button
      if (document.activeElement instanceof HTMLElement) {
        document.activeElement.blur();
      }
      setTimeout(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }), 100);
    };

    const handleNext = () => {
      setAnswer('');
      setFeedback(null);
      setCorrect(null);
      setSelectedWords([]);
      setAvailableWords([]);

      if (exerciseIndex + 1 < lesson.exercises.length) {
        setExerciseIndex((prev) => prev + 1);
      } else {
        setStep('done');
      }
    };

    const handleWordSelect = (word: string, idx: number) => {
      setSelectedWords((prev) => [...prev, word]);
      setAvailableWords((prev) => prev.filter((_, i) => i !== idx));
    };

    const handleWordRemove = (word: string, idx: number) => {
      setAvailableWords((prev) => [...prev, word]);
      setSelectedWords((prev) => prev.filter((_, i) => i !== idx));
    };

    const handleBuildCheck = () => {
      const built = selectedWords.join(' ');
      const isCorrect = built.toLowerCase() === (ex.answer ?? '').toLowerCase();
      setCorrect(isCorrect);
      setFeedback(isCorrect ? 'Правильно!' : `Правильный ответ: ${ex.answer}`);

      if (isCorrect) {
        setTotalXp((prev) => prev + ex.xp);
        WebApp.HapticFeedback.notificationOccurred('success');
      } else {
        WebApp.HapticFeedback.notificationOccurred('error');
        setMistakes((prev) => [...prev, { prompt: ex.prompt, corrected: ex.answer ?? '' }]);
      }
    };

    const handleChoiceSelect = (optionIndex: number) => {
      const isCorrect = optionIndex === ex.correct;
      setCorrect(isCorrect);
      setFeedback(isCorrect ? 'Правильно!' : `Правильный ответ: ${ex.options?.[ex.correct ?? 0]}`);

      if (isCorrect) {
        setTotalXp((prev) => prev + ex.xp);
        WebApp.HapticFeedback.notificationOccurred('success');
      } else {
        WebApp.HapticFeedback.notificationOccurred('error');
        setMistakes((prev) => [...prev, {
          prompt: ex.prompt,
          corrected: ex.options?.[ex.correct ?? 0] ?? '',
        }]);
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
              {ex.bot_says && <p className={styles.exerciseBotSays}>{'\u2014'} {ex.bot_says}</p>}
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
          ) : ex.type === 'build_sentence' && ex.words ? (
            <div className={styles.buildArea}>
              <div className={styles.buildResult}>
                {selectedWords.length > 0 ? selectedWords.map((w, i) => (
                  <button
                    key={i}
                    className={styles.buildWordSelected}
                    onClick={() => !feedback && handleWordRemove(w, i)}
                    disabled={feedback !== null}
                  >
                    {w}
                  </button>
                )) : (
                  <span className={styles.buildPlaceholder}>Нажми на слова ниже</span>
                )}
              </div>
              <div className={styles.buildWords}>
                {availableWords.map((w, i) => (
                  <button
                    key={i}
                    className={styles.buildWord}
                    onClick={() => handleWordSelect(w, i)}
                    disabled={feedback !== null}
                  >
                    {w}
                  </button>
                ))}
              </div>
              {!feedback && selectedWords.length > 0 && (
                <button className={styles.submitBtn} onClick={handleBuildCheck}>
                  Проверить
                </button>
              )}
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
  const correctCount = lesson.exercises.length - mistakes.length;
  const scorePercent = Math.round((correctCount / lesson.exercises.length) * 100);

  return (
    <div className={styles.page}>
      <div className={styles.doneScreen}>
        <span className={styles.doneIcon}>{mistakes.length === 0 ? '\uD83C\uDF89' : '\uD83D\uDCAA'}</span>
        <h2 className={styles.doneTitle}>
          {mistakes.length === 0 ? 'Отлично! Без ошибок!' : 'Урок пройден!'}
        </h2>
        <p className={styles.doneXp}>+{totalXp + lesson.meta.xp_reward} XP</p>
        <p className={styles.doneScore}>{correctCount}/{lesson.exercises.length} правильно ({scorePercent}%)</p>

        {mistakes.length > 0 && (
          <div className={styles.mistakesSection}>
            <h3 className={styles.mistakesTitle}>Работа над ошибками:</h3>
            {mistakes.map((m, i) => (
              <div key={i} className={styles.mistakeCard}>
                <div className={styles.mistakePrompt}>{m.prompt}</div>
                <div className={styles.mistakeCorrected}>{m.corrected}</div>
              </div>
            ))}
          </div>
        )}

        {lesson.homework && (
          <p className={styles.doneHomework}>{lesson.homework.text}</p>
        )}

        <div className={styles.doneButtons}>
          {mistakes.length > 0 && (
            <button className={styles.retryBtn} onClick={handleRetry}>
              Попробовать ещё раз
            </button>
          )}
          <button className={styles.primaryBtn} onClick={() => navigate('/')} disabled={saving}>
            {saving ? 'Сохранение...' : 'На главную'}
          </button>
        </div>
      </div>
    </div>
  );
}
