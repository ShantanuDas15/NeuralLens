import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import api from '../api';
import { useAuth } from '../hooks/useAuth';
import useHomeData from '../hooks/useHomeData';
import DropZone from '../components/upload/DropZone';
import ImagePreview from '../components/upload/ImagePreview';
import UploadProgress from '../components/upload/UploadProgress';
import ImageCompare from '../components/compare/ImageCompare';
import BatchQueue from '../components/upload/BatchQueue';
import SamplePanel from '../components/home/SamplePanel';
import RecentStrip from '../components/home/RecentStrip';
import {
  ActivityTile,
  AboutProject,
  HowItWorks,
  ScaleTile,
  TipTile,
  UnderTheHood,
} from '../components/home/HomeTiles';
import { toast } from '../components/ui/Toast';
import './Dashboard.css';

// Batches run one image at a time on a CPU-only server, so cap them at 4x.
const MAX_BATCH_SCALE = 4;

const Dashboard = () => {
  const { user } = useAuth();
  const home = useHomeData();
  const { refresh: refreshHome } = home;

  const [appState, setAppState] = useState('idle');
  const [scale, setScale] = useState(4);
  const [samplePending, setSamplePending] = useState(false);

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

  const handleFilesSelected = (files, requestedScale) => {
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
      const batchScale = Math.min(requestedScale, MAX_BATCH_SCALE);
      if (batchScale < requestedScale) {
        toast.info(`Batches run at up to ${MAX_BATCH_SCALE}× to keep things quick.`);
      }
      setBatchFiles(files);
      setBatchPreviewUrls(files.map(f => URL.createObjectURL(f)));
      setBatchStatuses(new Array(files.length).fill('queued'));
      setBatchResults(new Array(files.length).fill(null));
      setBatchErrors(new Array(files.length).fill(''));
      setAppState('batch');
      startBatchProcessing(files, batchScale);
    }
  };

  const startBatchProcessing = async (files, batchScale) => {
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
      formData.append('scale', batchScale);

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
        refreshHome();
      } else {
        toast.error('Batch processing failed.');
      }
    }
  };

  // Shared by the preview step (user picks a scale) and the one-click samples.
  const runEnhance = async (file, enhanceScale, originalUrl) => {
    setAppState('uploading');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('scale', enhanceScale);

    abortControllerRef.current = new AbortController();
    const toastId = toast.loading(`Processing image at ${enhanceScale}x scale...`);

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
        original_url: originalUrl
      });
      setAppState('success');
      toast.dismiss(toastId);
      toast.success('Image enhanced successfully!');
      refreshHome();

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
        else if (err.response.status === 503) msg = 'The server is busy right now. Please try again in a moment.';
        else msg = err.response.data?.detail || msg;
      }

      setErrorMsg(msg);
      setAppState('error');
      toast.error('Failed to enhance image');
    }
  };

  const handleEnhanceSingle = (chosenScale) => {
    if (!selectedFile) return;
    runEnhance(selectedFile, chosenScale, previewUrl);
  };

  // One click: load the bundled low-res photo and send it through the real pipeline.
  const handleSample = async (sample) => {
    if (samplePending || appState !== 'idle') return;
    setSamplePending(true);
    try {
      const blob = await (await fetch(sample.src)).blob();
      const file = new File([blob], sample.filename, { type: 'image/jpeg' });
      const url = URL.createObjectURL(file);

      setErrorMsg('');
      setResult(null);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setSelectedFile(file);
      setPreviewUrl(url);

      runEnhance(file, scale, url);
    } catch (err) {
      if (import.meta.env.DEV) console.error('Sample load failed:', err);
      toast.error('Could not load the sample image.');
    } finally {
      setSamplePending(false);
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

  // The home screen adapts to the user's history: samples first for someone with
  // no enhancements yet, the drop zone and recent work for everyone else.
  const idle = appState === 'idle';
  const layout =
    home.status === 'loading' ? 'loading'
      : home.status === 'ready' && home.total === 0 ? 'new'
        : 'returning';
  const firstName = user?.displayName?.trim().split(' ')[0];

  return (
    <div className="dashboard-container">
      {idle && layout !== 'loading' ? (
        <header className="home-head page-enter">
          <div>
            {layout === 'new' ? (
              <>
                <span className="home-eyebrow"><Sparkles size={14} aria-hidden="true" />First time here?</span>
                <h1>Welcome to NeuralLens</h1>
                <p>Turn a blurry photo into a sharp one in seconds. Pick a sample to watch the real model work.</p>
              </>
            ) : (
              <>
                <h1>{firstName ? `Welcome back, ${firstName}` : 'Welcome back'}</h1>
                <p>Drop an image and watch it come into focus.</p>
              </>
            )}
          </div>
          {layout === 'returning' && <Link className="text-link" to="/history">View history →</Link>}
        </header>
      ) : (
        !idle && (
          <header className="dashboard-header page-enter">
            <h1 className="dashboard-title">
              Enhance your images with <span className="gradient-text">Real-ESRGAN</span>
            </h1>
          </header>
        )
      )}

      <div className="dashboard-content">
        {idle && layout === 'loading' && (
          <div className="home-skeleton" aria-busy="true" aria-label="Loading">
            <div /><div />
          </div>
        )}

        {idle && layout === 'new' && (
          <div className="home-stack page-enter">
            <div className="home-bento">
              <SamplePanel scale={scale} onPick={handleSample} busy={samplePending}>
                <DropZone variant="compact" scale={scale} onFilesSelected={handleFilesSelected} />
              </SamplePanel>
              <div className="home-side">
                <ScaleTile scale={scale} onChange={setScale} />
                <HowItWorks />
                <AboutProject />
              </div>
            </div>
            <UnderTheHood />
          </div>
        )}

        {idle && layout === 'returning' && (
          <div className="home-stack page-enter">
            <div className="home-bento">
              <DropZone variant="hero" scale={scale} onFilesSelected={handleFilesSelected} />
              <div className="home-side">
                <ScaleTile scale={scale} onChange={setScale} />
                <ActivityTile stats={home.stats} />
                <TipTile />
              </div>
            </div>
            <RecentStrip items={home.items} />
          </div>
        )}

        {appState === 'preview' && (
          <ImagePreview
            originalUrl={previewUrl}
            file={selectedFile}
            initialScale={scale}
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
