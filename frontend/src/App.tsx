import { BrowserRouter, Navigate, Routes, Route, useLocation, useParams } from 'react-router-dom';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { DirectionPage } from '@/pages/DirectionPage';
import { HomePage } from '@/pages/HomePage';
import { LessonPage } from '@/pages/LessonPage';
import { CheckpointPage } from '@/pages/CheckpointPage';
import { ReviewPage } from '@/pages/ReviewPage';
import { ProgressPage } from '@/pages/ProgressPage';
import { TabBar } from '@/components/TabBar';
import { RussianHome } from '@/learning/Home';
import { RussianLesson } from '@/learning/Lesson';
import { RussianReview } from '@/learning/Review';
import { RussianProgress } from '@/learning/Progress';

function RussianLessonRoute() {
  const { lessonId } = useParams();
  return <RussianLesson key={lessonId} />;
}

function LegacyRussianLessonRedirect() {
  const { lessonId } = useParams();
  return <Navigate to={`/ru/lesson/${lessonId}`} replace />;
}

function LegacyLessonRedirect() {
  const { block, lessonSlug } = useParams();
  return <Navigate to={`/uz/lesson/${block}/${lessonSlug}`} replace />;
}

function LegacyCheckpointRedirect() {
  const { block, lessonSlug } = useParams();
  return <Navigate to={`/uz/checkpoint/${block}/${lessonSlug}`} replace />;
}

function Shell() {
  const { pathname } = useLocation();
  const hideTabBar =
    pathname === '/' || pathname.startsWith('/ru/lesson/') ||
    pathname.startsWith('/uz/lesson/') || pathname.startsWith('/uz/checkpoint/');

  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<DirectionPage />} />
        <Route path="/ru" element={<RussianHome />} />
        <Route path="/ru/lesson/:lessonId" element={<RussianLessonRoute />} />
        <Route path="/ru/review" element={<RussianReview />} />
        <Route path="/ru/progress" element={<RussianProgress />} />
        <Route path="/uz" element={<HomePage />} />
        <Route path="/uz/lesson/:block/:lessonSlug" element={<LessonPage />} />
        <Route path="/uz/checkpoint/:block/:lessonSlug" element={<CheckpointPage />} />
        <Route path="/uz/review" element={<ReviewPage />} />
        <Route path="/uz/progress" element={<ProgressPage />} />
        <Route path="/learn/lesson/:lessonId" element={<LegacyRussianLessonRedirect />} />
        <Route path="/learn/review" element={<Navigate to="/ru/review" replace />} />
        <Route path="/learn/progress" element={<Navigate to="/ru/progress" replace />} />
        <Route path="/uzbek" element={<Navigate to="/uz" replace />} />
        <Route path="/lesson/:block/:lessonSlug" element={<LegacyLessonRedirect />} />
        <Route path="/checkpoint/:block/:lessonSlug" element={<LegacyCheckpointRedirect />} />
        <Route path="/review" element={<Navigate to="/uz/review" replace />} />
        <Route path="/progress" element={<Navigate to="/uz/progress" replace />} />
      </Routes>
      {!hideTabBar && <TabBar />}
    </ErrorBoundary>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  );
}
