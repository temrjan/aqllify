import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import WebApp from '@twa-dev/sdk';
import { api } from '@/shared/api';
import styles from './CheckpointPage.module.css';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

const SCENARIO_PROMPT =
  'You are a friendly Uzbek person named Laziz at a social event in Tashkent. ' +
  'You approach the student and start a conversation. Speak simple Uzbek (A1 level). ' +
  'Use only words from lessons 1-4: greetings, introductions, yes/no, politeness. ' +
  'After each Uzbek phrase, add Russian translation in parentheses. ' +
  'Lead the conversation through: greeting → asking name → asking where from → saying nice to meet you → goodbye. ' +
  'Keep it 5-7 exchanges total.';

const FIRST_AI_MESSAGE =
  "Assalomu alaykum! Mening ismim Laziz. Siz kimsiz?\n(Здравствуйте! Меня зовут Лазиз. А вы кто?)";

const MAX_EXCHANGES = 7;
const XP_REWARD = 30;

export function CheckpointPage() {
  const { block, lessonSlug } = useParams<{ block: string; lessonSlug: string }>();
  const navigate = useNavigate();

  const [phase, setPhase] = useState<'intro' | 'chat' | 'done'>('intro');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const userMessageCount = messages.filter((m) => m.role === 'user').length;
  const canFinish = userMessageCount >= 5;

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  // Start the dialog
  const handleStart = () => {
    WebApp.HapticFeedback.impactOccurred('medium');
    setPhase('chat');
    setMessages([{ role: 'assistant', content: FIRST_AI_MESSAGE }]);
  };

  // Send a user message
  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;

    WebApp.HapticFeedback.impactOccurred('light');

    const userMsg: ChatMessage = { role: 'user', content: text };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput('');
    setSending(true);

    try {
      const res = await api.post('/lessons/checkpoint-dialog', {
        scenario: SCENARIO_PROMPT,
        message: text,
        history: updatedMessages.map((m) => ({ role: m.role, content: m.content })),
      });

      const aiReply: string = res.data.reply ?? res.data.content ?? '';
      if (aiReply) {
        setMessages((prev) => [...prev, { role: 'assistant', content: aiReply }]);
        WebApp.HapticFeedback.impactOccurred('light');
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '(Ошибка соединения. Попробуйте ещё раз.)' },
      ]);
    } finally {
      setSending(false);
    }
  };

  // Finish and save progress
  const handleFinish = () => {
    WebApp.HapticFeedback.notificationOccurred('success');
    setPhase('done');
  };

  // Save progress on done
  useEffect(() => {
    if (phase !== 'done' || saved || saving || !block || !lessonSlug) return;
    setSaving(true);

    api.post('/progress/complete-lesson', {
      lesson_slug: `${block}/${lessonSlug}`,
      xp: XP_REWARD,
      score: 1,
    })
      .then(() => {
        WebApp.HapticFeedback.notificationOccurred('success');
      })
      .catch(() => {})
      .finally(() => {
        setSaving(false);
        setSaved(true);
      });
  }, [phase, saved, saving, block, lessonSlug]);

  // Parse AI message into text + translation
  const parseMessage = (content: string): { text: string; translation: string | null } => {
    // Match content in parentheses at the end of a line as translation
    const lines = content.split('\n');
    const textLines: string[] = [];
    const translationLines: string[] = [];

    for (const line of lines) {
      const match = line.match(/^(.*?)\s*\(([^)]+)\)\s*$/);
      if (match && match[1] !== undefined && match[2] !== undefined) {
        textLines.push(match[1].trim());
        translationLines.push(match[2].trim());
      } else {
        textLines.push(line);
      }
    }

    const translation = translationLines.length > 0 ? translationLines.join('\n') : null;
    return { text: textLines.join('\n'), translation };
  };

  // --- INTRO PHASE ---
  if (phase === 'intro') {
    return (
      <div className={styles.page}>
        <div className={styles.intro}>
          <span className={styles.introIcon}>&#128172;</span>
          <h1 className={styles.introTitle}>Checkpoint: Диалог</h1>
          <p className={styles.introSubtitle}>
            Поговорите с Лазизом на узбекском языке. Используйте фразы из уроков 1-4.
          </p>

          <div className={styles.introScenario}>
            <div className={styles.scenarioLabel}>Сценарий</div>
            <p className={styles.scenarioText}>
              Вы на мероприятии в Ташкенте. К вам подходит Лазиз и начинает разговор.
              Поздоровайтесь, представьтесь, расскажите откуда вы, и попрощайтесь.
            </p>
          </div>

          <button className={styles.primaryBtn} onClick={handleStart}>
            Начать диалог
          </button>
        </div>
      </div>
    );
  }

  // --- DONE PHASE ---
  if (phase === 'done') {
    return (
      <div className={styles.page}>
        <div className={styles.doneScreen}>
          <span className={styles.doneIcon}>&#127881;</span>
          <h2 className={styles.doneTitle}>Диалог завершён!</h2>
          <p className={styles.doneSubtitle}>
            Вы провели {userMessageCount} обменов реплик с Лазизом.
          </p>
          <p className={styles.doneXp}>+{XP_REWARD} XP</p>
          <button
            className={styles.primaryBtn}
            onClick={() => navigate('/')}
            disabled={saving}
          >
            {saving ? 'Сохранение...' : 'На главную'}
          </button>
        </div>
      </div>
    );
  }

  // --- CHAT PHASE ---
  return (
    <div className={styles.page}>
      <div className={styles.chatHeader}>
        <div className={styles.chatAvatar}>L</div>
        <div>
          <div className={styles.chatName}>Laziz</div>
          <div className={styles.chatHint}>Checkpoint Dialog</div>
        </div>
        <span className={styles.exchangeCounter}>
          {userMessageCount}/{MAX_EXCHANGES}
        </span>
      </div>

      <div className={styles.messagesArea}>
        {messages.map((msg, i) => {
          const { text, translation } = parseMessage(msg.content);
          return (
            <div
              key={i}
              className={`${styles.messageBubble} ${
                msg.role === 'assistant' ? styles.messageAi : styles.messageUser
              }`}
            >
              <div>{text}</div>
              {translation && (
                <div className={styles.messageTranslation}>{translation}</div>
              )}
            </div>
          );
        })}

        {sending && (
          <div className={styles.typingIndicator}>
            <span className={styles.typingDots}>
              <span className={styles.typingDot} />
              <span className={styles.typingDot} />
              <span className={styles.typingDot} />
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {canFinish ? (
        <div className={styles.finishBar}>
          <input
            className={styles.chatInput}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Напишите на узбекском..."
            disabled={sending}
          />
          {input.trim() ? (
            <button
              className={styles.sendBtn}
              onClick={handleSend}
              disabled={sending}
              aria-label="Отправить"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          ) : (
            <button className={styles.finishBtn} onClick={handleFinish}>
              Завершить
            </button>
          )}
        </div>
      ) : (
        <div className={styles.inputBar}>
          <input
            className={styles.chatInput}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Напишите на узбекском..."
            disabled={sending}
            autoFocus
          />
          <button
            className={styles.sendBtn}
            onClick={handleSend}
            disabled={sending || !input.trim()}
            aria-label="Отправить"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
