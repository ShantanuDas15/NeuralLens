import { useState, useEffect, useRef } from 'react';
import api from '../api';
import DropZone from '../components/upload/DropZone';
import ImagePreview from '../components/upload/ImagePreview';
import UploadProgress from '../components/upload/UploadProgress';
import ImageCompare from '../components/compare/ImageCompare';
import BatchQueue from '../components/upload/BatchQueue';
import { toast } from '../components/ui/Toast';
import './Dashboard.css';

const Dashboard = () => {
  const [appState, setAppState] = useState('idle');
  
  // Single file state
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [timerStart, setTimerStart] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Batch files state
  const [batchFiles, setBatchFiles] = useState([]);
  const [batchPreviewUrls, setBatchPreviewUrls] = useState([]);
  const [batchStatuses, setBatchStatuses] = useState([]);
  const [batchResults, setBatchResults] = useState([]);
  const [batchErrors, setBatchErrors] = useState([]);

  const abortControllerRef = useRef(null);

  // Timer logic for single processing state
  useEffect(() => {
    let interval;
    if (appState === 'processing') {
      interval = setInterval(() => {
        setElapsedTime(Date.now() - timerStart);
      }, 100);
    }
    return () => clearInterval(interval);
  }, [appState, timerStart]);

  // Clean up object URLs and abort pending request on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      batchPreviewUrls.forEach(url => URL.revokeObjectURL(url));
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [previewUrl, batchPreviewUrls]);

  const handleFilesSelected = (files, batchScale) => {
    setErrorMsg('');
    setResult(null);

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    batchPreviewUrls.forEach(url => URL.revokeObjectURL(url));

    if (files.length === 1) {
      const file = files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setAppState('preview');
    } else {
      setBatchFiles(files);
      setBatchPreviewUrls(files.map(f => URL.createObjectURL(f)));
      setBatchStatuses(new Array(files.length).fill('queued'));
      setBatchResults(new Array(files.length).fill(null));
      setBatchErrors(new Array(files.length).fill(''));
      setAppState('batch');
      startBatchProcessing(files, batchScale);
    }
  };

  const startBatchProcessing = async (files, scale) => {
    const statuses = new Array(files.length).fill('queued');
    const results = new Array(files.length).fill(null);
    const errors = new Array(files.length).fill('');
    
    abortControllerRef.current = new AbortController();
    
    const toastId = toast.loading(`Batch processing ${files.length} images...`);

    for (let i = 0; i < files.length; i++) {
      // Check if aborted
      if (abortControllerRef.current.signal.aborted) {
        toast.dismiss(toastId);
        break;
      }

      statuses[i] = 'processing';
      setBatchStatuses([...statuses]);

      const formData = new FormData();
      formData.append('file', files[i]);
      formData.append('scale', scale);

      try {
        const response = await api.post('/enhance', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          signal: abortControllerRef.current.signal
        });

        results[i] = {
          ...response.data,
          original_url: URL.createObjectURL(files[i])
        };
        statuses[i] = 'success';
        
      } catch (err) {
        if (err.name === 'CanceledError' || err.message === 'canceled') {
          statuses[i] = 'queued';
          break;
        }
        
        statuses[i] = 'error';
        let msg = 'Error';
        if (err.response) {
          if (err.response.status === 413) msg = 'Too large';
          else if (err.response.status === 429) msg = 'Rate limit';
          else msg = err.response.data?.detail || 'Failed';
        }
        errors[i] = msg;
      }
      
      setBatchResults([...results]);
      setBatchStatuses([...statuses]);
      setBatchErrors([...errors]);
    }
    
    if (!abortControllerRef.current.signal.aborted) {
      toast.dismiss(toastId);
      const successCount = statuses.filter(s => s === 'success').length;
      if (successCount > 0) {
        toast.success(`Completed! ${successCount}/${files.length} images enhanced.`);
      } else {
        toast.error('Batch processing failed.');
      }
    }
  };

  const handleEnhanceSingle = async (scale) => {
    if (!selectedFile) return;

    setAppState('uploading');
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('scale', scale);
    
    abortControllerRef.current = new AbortController();
    const toastId = toast.loading(`Processing image at ${scale}x scale...`);

    try {
      await new Promise(r => setTimeout(r, 600));
      setAppState('processing');
      const startMs = Date.now();
      setTimerStart(startMs);

      const response = await api.post('/enhance', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        signal: abortControllerRef.current.signal
      });

      const minTimeMs = 1500;
      const actualTimeMs = Date.now() - startMs;
      if (actualTimeMs < minTimeMs) {
        await new Promise(r => setTimeout(r, minTimeMs - actualTimeMs));
      }

      setResult({
        ...response.data,
        original_url: previewUrl
      });
      setAppState('success');
      toast.dismiss(toastId);
      toast.success('Image enhanced successfully!');

    } catch (err) {
      toast.dismiss(toastId);
      if (err.name === 'CanceledError' || err.message === 'canceled') {
        toast.info('Enhancement cancelled');
        return;
      }
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
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setAppState('idle');
    setResult(null);
    setErrorMsg('');
    setSelectedFile(null);
    setElapsedTime(0);
    setBatchFiles([]);
    setBatchStatuses([]);
    setBatchResults([]);
    setBatchErrors([]);
    
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    
    batchPreviewUrls.forEach(url => URL.revokeObjectURL(url));
    setBatchPreviewUrls([]);
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
            <DropZone onFilesSelected={handleFilesSelected} />
          </div>
        )}

        {appState === 'preview' && (
          <ImagePreview 
            originalUrl={previewUrl}
            file={selectedFile}
            onEnhance={handleEnhanceSingle}
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

        {appState === 'batch' && (
          <BatchQueue 
            files={batchFiles}
            previewUrls={batchPreviewUrls}
            results={batchResults}
            statuses={batchStatuses}
            errors={batchErrors}
            onReset={handleReset}
          />
        )}
      </div>
    </div>
  );
};

export default Dashboard;
