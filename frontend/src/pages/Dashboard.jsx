import { useState, useEffect } from 'react';
import api from '../api';
import DropZone from '../components/upload/DropZone';
import UploadProgress from '../components/upload/UploadProgress';
import ImageCompare from '../components/compare/ImageCompare';
import { toast } from '../components/ui/Toast';
import './Dashboard.css';

const Dashboard = () => {
  // state: 'idle' | 'uploading' | 'processing' | 'success' | 'error'
  const [appState, setAppState] = useState('idle');
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  
  const [timerStart, setTimerStart] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Timer logic for processing state
  useEffect(() => {
    let interval;
    if (appState === 'processing') {
      interval = setInterval(() => {
        setElapsedTime(Date.now() - timerStart);
      }, 100);
    }
    return () => clearInterval(interval);
  }, [appState, timerStart]);

  const handleFileSelected = async (file) => {
    setAppState('uploading');
    setErrorMsg('');
    setResult(null);

    // Create object URL for original image preview in ImageCompare
    const originalUrl = URL.createObjectURL(file);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Simulate slight delay for "uploading" animation before hitting processing
      setTimeout(() => {
        setAppState('processing');
        setTimerStart(Date.now());
      }, 800);

      const response = await api.post('/enhance', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      // Artificial minimum processing time (to show cool animation)
      const minTimeMs = 1500;
      const actualTimeMs = Date.now() - timerStart;
      if (actualTimeMs < minTimeMs) {
        await new Promise(r => setTimeout(r, minTimeMs - actualTimeMs));
      }

      setResult({
        ...response.data,
        original_url: originalUrl // injecting local preview URL
      });
      setAppState('success');
      toast.success('Image enhanced successfully!');

    } catch (err) {
      console.error("Enhancement failed:", err);
      let msg = 'An unexpected error occurred.';
      if (err.response) {
        if (err.response.status === 413) msg = 'File is too large (Max 2MB).';
        else if (err.response.status === 429) msg = 'Rate limit exceeded. Try again later.';
        else msg = err.response.data?.detail || msg;
      }
      
      setErrorMsg(msg);
      setAppState('error');
      toast.error('Failed to enhance image');
    }
  };

  const handleReset = () => {
    setAppState('idle');
    setResult(null);
    setErrorMsg('');
    setElapsedTime(0);
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header page-enter">
        <h1 className="dashboard-title">
          Enhance your images with <span className="gradient-text">Real-ESRGAN</span>
        </h1>
        <p className="dashboard-subtitle">
          Upload any low-resolution image and our AI will upscale it by 4x instantly.
        </p>
      </div>

      <div className="dashboard-content">
        {appState === 'idle' && (
          <div className="page-enter">
            <DropZone onFileSelected={handleFileSelected} />
          </div>
        )}

        {(appState === 'uploading' || appState === 'processing' || appState === 'error') && (
          <UploadProgress 
            state={appState} 
            elapsedTime={elapsedTime} 
            error={errorMsg}
            onReset={handleReset}
          />
        )}

        {appState === 'success' && result && (
          <ImageCompare result={result} onReset={handleReset} />
        )}
      </div>
    </div>
  );
};

export default Dashboard;
