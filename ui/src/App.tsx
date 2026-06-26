import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import NavBar from './components/NavBar';
import KbList from './pages/KbList';
import KbDetail from './pages/KbDetail';
import SessionList from './pages/SessionList';
import SessionChat from './pages/SessionChat';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <main style={{ padding: '16px', maxWidth: 1200, margin: '0 auto' }}>
        <Routes>
          <Route path="/" element={<Navigate to="/kb" replace />} />
          <Route path="/kb" element={<KbList />} />
          <Route path="/kb/:name" element={<KbDetail />} />
          <Route path="/session" element={<SessionList />} />
          <Route path="/session/:name" element={<SessionChat />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;
