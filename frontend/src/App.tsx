import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { HomePage } from '@/pages/HomePage';
import { LessonPage } from '@/pages/LessonPage';
import { CheckpointPage } from '@/pages/CheckpointPage';
import { ReviewPage } from '@/pages/ReviewPage';
import { ProgressPage } from '@/pages/ProgressPage';
import { TabBar } from '@/components/TabBar';

export function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/lesson/:block/:lessonSlug" element={<LessonPage />} />
        <Route path="/checkpoint/:block/:lessonSlug" element={<CheckpointPage />} />
        <Route path="/review" element={<ReviewPage />} />
        <Route path="/progress" element={<ProgressPage />} />
      </Routes>
      <TabBar />
      </ErrorBoundary>
    </BrowserRouter>
  );
}
