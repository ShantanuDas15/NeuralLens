import { RefreshCcw } from 'lucide-react';
import Spinner from '../ui/Spinner';
import Button from '../ui/Button';
import './UploadProgress.css';

const UploadProgress = ({ state, elapsedTime, error, onReset }) => {
  // state can be: 'uploading', 'processing', 'error'
  
  return (
    <div className="upload-progress-container page-enter">
      <div className="progress-card">
        
        {state === 'uploading' && (
          <div className="progress-state">
            <div className="progress-icon-wrapper">
              <Spinner size="lg" className="progress-spinner" />
            </div>
            <h3>Uploading Image</h3>
            <p>Transferring file to secure servers...</p>
            <div className="progress-bar-container">
              <div className="progress-bar-fill uploading-animation"></div>
            </div>
          </div>
        )}

        {state === 'processing' && (
          <div className="progress-state">
            <div className="progress-icon-wrapper pulse-animation">
              <div className="ai-icon">AI</div>
            </div>
            <h3 className="gradient-text">Enhancing Image</h3>
            <p>Real-ESRGAN model is processing your image.</p>
            <div className="elapsed-time">
              Elapsed time: {(elapsedTime / 1000).toFixed(1)}s
            </div>
            <div className="progress-bar-container">
              <div className="progress-bar-fill processing-animation"></div>
            </div>
          </div>
        )}

        {state === 'error' && (
          <div className="progress-state error-state">
            <div className="progress-icon-wrapper error-icon">
              <RefreshCcw size={32} />
            </div>
            <h3 className="error-text">Enhancement Failed</h3>
            <p className="error-message">{error || 'An unexpected error occurred during processing.'}</p>
            <Button variant="ghost" onClick={onReset} className="reset-btn">
              Try Again
            </Button>
          </div>
        )}

      </div>
    </div>
  );
};

export default UploadProgress;
