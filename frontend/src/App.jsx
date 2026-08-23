import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<div className="page-enter" style={{ padding: '2rem' }}><h1>Dashboard Stub</h1></div>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
