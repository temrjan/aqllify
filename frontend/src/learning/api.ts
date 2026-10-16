import axios from 'axios';
import { api } from '@/shared/api';

export type LevelId = 'beginner' | 'intermediate' | 'advanced';
export interface Unit { title: string; task: string }
export interface Level {
  id: LevelId; title: string; description: string; available: boolean;
  entry: string[]; units: Unit[]; completion: string[];
}
export interface Phrase { id: string; russian: string; uzbek: string; audio: string }
export interface Exercise {
  id: string; kind: 'choice' | 'text'; prompt: string; options: string[]; transfer: boolean;
}
export interface PlacementQuestion extends Exercise {
  skill: string; audio: string | null; transcript: string | null;
}
export interface Lesson {
  id: string; order: number; title: string; goal: string; phrases: Phrase[];
  explanation: string; dialogue: { speaker: string; russian: string; uzbek: string }[];
  exercises: Exercise[];
}
export interface Course {
  id: string; version: string; title: string; description: string;
  alphabet: Unit[]; levels: Level[]; placement: PlacementQuestion[]; lessons: Lesson[];
}
export interface AnswerResult { answer: string; correct: boolean; feedback: string; corrected: string | null }
export interface Attempt { id: string; lesson_id: string; version: string; answers: Record<string, AnswerResult>; finalized: boolean }
export interface Completion { completed: boolean; score: number; total_xp: number }
export interface Progress {
  lessons: { lesson_id: string; completed: boolean; best_score: number }[];
  total_xp: number; due_count: number;
}
export interface ReviewCard extends Phrase { lesson_id: string; phrase_id: string; revision: number }
export interface PlacementResult { level: LevelId; score: number; skills: Record<string, number>; assisted: boolean }
export interface ChatMessage { role: 'user' | 'assistant'; content: string }

// Parse at the network boundary: malformed responses must not become saved UI state.
function object(value: unknown): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) throw new Error('Invalid response');
  return value as Record<string, unknown>;
}
function text(value: unknown): string {
  if (typeof value !== 'string') throw new Error('Invalid text');
  return value;
}
function number(value: unknown): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error('Invalid number');
  return value;
}
function bool(value: unknown): boolean {
  if (typeof value !== 'boolean') throw new Error('Invalid flag');
  return value;
}
function list<T>(value: unknown, parse: (item: unknown) => T): T[] {
  if (!Array.isArray(value)) throw new Error('Invalid list');
  return value.map(parse);
}
function optionalText(value: unknown): string | null { return value === null ? null : text(value); }
function levelId(value: unknown): LevelId {
  if (value !== 'beginner' && value !== 'intermediate' && value !== 'advanced') throw new Error('Invalid level');
  return value;
}
function unit(value: unknown): Unit { const v = object(value); return { title: text(v.title), task: text(v.task) }; }
function phrase(value: unknown): Phrase {
  const v = object(value);
  return { id: text(v.id), russian: text(v.russian), uzbek: text(v.uzbek), audio: text(v.audio) };
}
function exercise(value: unknown): Exercise {
  const v = object(value);
  if (v.kind !== 'choice' && v.kind !== 'text') throw new Error('Invalid exercise');
  return { id: text(v.id), kind: v.kind, prompt: text(v.prompt), options: list(v.options, text), transfer: bool(v.transfer) };
}
export function parseLesson(value: unknown): Lesson {
  const v = object(value);
  return { id: text(v.id), order: number(v.order), title: text(v.title), goal: text(v.goal),
    phrases: list(v.phrases, phrase), explanation: text(v.explanation), exercises: list(v.exercises, exercise),
    dialogue: list(v.dialogue, (item) => { const d = object(item); return { speaker: text(d.speaker), russian: text(d.russian), uzbek: text(d.uzbek) }; }) };
}
function parseCourse(value: unknown): Course {
  const v = object(value);
  return { id: text(v.id), version: text(v.version), title: text(v.title), description: text(v.description),
    alphabet: list(v.alphabet, unit), lessons: list(v.lessons, parseLesson),
    levels: list(v.levels, (item) => { const l = object(item); return { id: levelId(l.id), title: text(l.title),
      description: text(l.description), available: bool(l.available), entry: list(l.entry, text),
      units: list(l.units, unit), completion: list(l.completion, text) }; }),
    placement: list(v.placement, (item) => { const q = object(item); return { ...exercise(item),
      skill: text(q.skill), audio: optionalText(q.audio), transcript: optionalText(q.transcript) }; }) };
}
function parseAnswer(value: unknown): AnswerResult {
  const v = object(value);
  return { answer: text(v.answer), correct: bool(v.correct), feedback: text(v.feedback), corrected: optionalText(v.corrected) };
}
function parseAttempt(value: unknown): Attempt {
  const v = object(value); const answers: Record<string, AnswerResult> = {};
  for (const [key, item] of Object.entries(object(v.answers))) answers[key] = parseAnswer(item);
  return { id: text(v.id), lesson_id: text(v.lesson_id), version: text(v.version), answers, finalized: bool(v.finalized) };
}
function parseProgress(value: unknown): Progress {
  const v = object(value);
  return { total_xp: number(v.total_xp), due_count: number(v.due_count), lessons: list(v.lessons, (item) => {
    const l = object(item); return { lesson_id: text(l.lesson_id), completed: bool(l.completed), best_score: number(l.best_score) };
  }) };
}
async function get<T>(path: string, parse: (value: unknown) => T, signal?: AbortSignal): Promise<T> {
  const response = await api.get<unknown>(`/learning${path}`, { signal, timeout: 15000 });
  return parse(response.data);
}
async function post<T>(path: string, body: unknown, parse: (value: unknown) => T): Promise<T> {
  const response = await api.post<unknown>(`/learning${path}`, body, { timeout: 25000 });
  return parse(response.data);
}
export const learning = {
  catalog: (signal?: AbortSignal) => get('/catalog', parseCourse, signal),
  lesson: (id: string, signal?: AbortSignal) => get(`/lessons/${encodeURIComponent(id)}`, parseLesson, signal),
  start: (id: string, lesson_id: string) => post('/attempts', { id, lesson_id }, parseAttempt),
  attempt: (id: string, signal?: AbortSignal) => get(`/attempts/${encodeURIComponent(id)}`, parseAttempt, signal),
  answer: (id: string, exercise_id: string, answer: string) => post(`/attempts/${encodeURIComponent(id)}/answers`, { exercise_id, answer }, parseAnswer),
  complete: (id: string) => post(`/attempts/${encodeURIComponent(id)}/complete`, {}, (value): Completion => {
    const v = object(value); return { completed: bool(v.completed), score: number(v.score), total_xp: number(v.total_xp) };
  }),
  progress: (signal?: AbortSignal) => get('/progress', parseProgress, signal),
  reviews: (signal?: AbortSignal) => get('/review', (value) => list(value, (item): ReviewCard => {
    const v = object(item); const phrase_id = text(v.phrase_id);
    return { id: phrase_id, phrase_id, lesson_id: text(v.lesson_id), russian: text(v.russian), uzbek: text(v.uzbek), audio: text(v.audio), revision: number(v.revision) };
  }), signal),
  rate: (card: ReviewCard, rating: 'again' | 'remembered') => post('/review', {
    lesson_id: card.lesson_id, phrase_id: card.phrase_id, revision: card.revision, rating,
  }, (value) => { const v = object(value); return { revision: number(v.revision), due_at: text(v.due_at) }; }),
  placement: (answers: Record<string, string>, assisted: boolean) => post('/placement', { answers, assisted }, (value): PlacementResult => {
    const v = object(value); const skills: Record<string, number> = {};
    for (const [key, score] of Object.entries(object(v.skills))) skills[key] = number(score);
    return { level: levelId(v.level), score: number(v.score), skills, assisted: bool(v.assisted) };
  }),
  chat: (lesson_id: string, message: string, history: ChatMessage[]) => post('/dialogue', { lesson_id, message, history }, (value) => {
    const v = object(value); return { reply: text(v.reply), feedback: text(v.feedback) };
  }),
};

export function mediaUrl(name: string): string {
  return `${api.defaults.baseURL}/learning/audio/${encodeURIComponent(name)}`;
}
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    if (status === 401 || status === 422) return 'Ilovani Telegram orqali qayta oching yoki kiritilgan javobni tekshiring.';
    if (status === 409) return 'Saqlangan holat o‘zgardi. Sahifani yangilang yoki yangi urinish boshlang.';
    if (status === 429) return 'Bir oz kutib, yana urinib ko‘ring.';
    if (status === 503) return 'Suhbat hozir ishlamayapti. Oddiy mashqlarni davom ettirishingiz mumkin.';
  }
  return 'Yuklash yoki saqlash amalga oshmadi. Javobingiz yo‘qolmadi. Qayta urinib ko‘ring.';
}

export { readLocal, writeLocal } from '@/shared/storage';
