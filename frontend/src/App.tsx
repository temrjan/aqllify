import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { LessonPage } from '@/pages/LessonPage';
import { ReviewPage } from '@/pages/ReviewPage';
import { ProgressPage } from '@/pages/ProgressPage';
import { TabBar } from '@/components/TabBar';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LessonPage />} />
        <Route path="/review" element={<ReviewPage />} />
        <Route path="/progress" element={<ProgressPage />} />
      </Routes>
      <TabBar />
    </BrowserRouter>
  );
}
