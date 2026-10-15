import { BrowserRouter, Routes, Route, useLocation, useParams } from 'react-router-dom';
import { ErrorBoundary } from '@/components/ErrorBoundary';
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

function Shell() {
  const { pathname } = useLocation();
  const hideTabBar =
    pathname === '/' || pathname.startsWith('/learn/') ||
    pathname.startsWith('/lesson/') || pathname.startsWith('/checkpoint/');

  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<RussianHome />} />
        <Route path="/learn/lesson/:lessonId" element={<RussianLessonRoute />} />
        <Route path="/learn/review" element={<RussianReview />} />
        <Route path="/learn/progress" element={<RussianProgress />} />
        <Route path="/uzbek" element={<HomePage />} />
        <Route path="/lesson/:block/:lessonSlug" element={<LessonPage />} />
        <Route path="/checkpoint/:block/:lessonSlug" element={<CheckpointPage />} />
        <Route path="/review" element={<ReviewPage />} />
        <Route path="/progress" element={<ProgressPage />} />
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
