import { useState, useEffect, useRef } from 'react';
import api from '../api';
import DropZone from '../components/upload/DropZone';
import ImagePreview from '../components/upload/ImagePreview';
import UploadProgress from '../components/upload/UploadProgress';
import ImageCompare from '../components/compare/ImageCompare';
import { toast } from '../components/ui/Toast';
import './Dashboard.css';

const Dashboard = () => {
  const [appState, setAppState] = useState('idle');
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const abortControllerRef = useRef(null);
  
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

  // Clean up object URL and abort pending request on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [previewUrl]);

  const handleFileSelected = async (file) => {
    setSelectedFile(file);
    setErrorMsg('');
    setResult(null);

    // Clean up previous URL if it exists
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    // Create object URL for original image preview
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    
    setAppState('preview');
  };

  const handleEnhance = async () => {
    if (!selectedFile) return;

    setAppState('uploading');
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    abortControllerRef.current = new AbortController();

    try {
      // Small artificial delay to show uploading state briefly
      await new Promise(r => setTimeout(r, 600));
      
      setAppState('processing');
      const startMs = Date.now();
      setTimerStart(startMs);

      const response = await api.post('/enhance', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        signal: abortControllerRef.current.signal
      });

      // Artificial minimum processing time (to show cool animation)
      const minTimeMs = 1500;
      const actualTimeMs = Date.now() - startMs;
      if (actualTimeMs < minTimeMs) {
        await new Promise(r => setTimeout(r, minTimeMs - actualTimeMs));
      }

      setResult({
        ...response.data,
        original_url: previewUrl // injecting local preview URL
      });
      setAppState('success');
      toast.success('Image enhanced successfully!');

    } catch (err) {
      if (err.name === 'CanceledError' || err.message === 'canceled') {
        if (import.meta.env.DEV) console.log('Upload canceled');
        return;
      }
      if (import.meta.env.DEV) console.error("Enhancement failed:", err);
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
    setSelectedFile(null);
    setElapsedTime(0);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
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

        {appState === 'preview' && (
          <ImagePreview 
            originalUrl={previewUrl}
            file={selectedFile}
            onEnhance={handleEnhance}
            onCancel={handleReset}
          />
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
