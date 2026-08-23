import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ProtectedRoute from './components/layout/ProtectedRoute';
import Navbar from './components/layout/Navbar';
import PageShell from './components/layout/PageShell';
import ToastContainer from './components/ui/Toast';

function App() {
  return (
    <BrowserRouter>
      <ToastContainer />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/*" element={
          <ProtectedRoute>
            <Navbar />
            <PageShell>
              <Routes>
                <Route path="/" element={
                  <div>
                    <h1>Dashboard Stub</h1>
                  </div>
                } />
                {/* Future routes like /history and /profile will go here */}
              </Routes>
            </PageShell>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
