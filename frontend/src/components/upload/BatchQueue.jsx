import { useState } from 'react';
import { CheckCircle2, Loader2, AlertCircle, Download } from 'lucide-react';
import JSZip from 'jszip';
import Button from '../ui/Button';
import './BatchQueue.css';

const BatchQueue = ({ files, previewUrls, results, statuses, errors, onReset }) => {
  const [isZipping, setIsZipping] = useState(false);
  
  const allDone = statuses.every(s => s === 'success' || s === 'error');
  const anySuccess = statuses.some(s => s === 'success');
  
  const downloadZip = async () => {
    setIsZipping(true);
    try {
      const zip = new JSZip();
      
      const promises = results.map(async (result, idx) => {
        if (!result) return;
        const response = await fetch(result.result_url);
        const blob = await response.blob();
        
        // Generate a filename based on original file
        const originalName = files[idx].name;
        const nameParts = originalName.split('.');
        const ext = nameParts.pop();
        const baseName = nameParts.join('.');
        
        zip.file(`${baseName}_enhanced.${ext}`, blob);
      });
      
      await Promise.all(promises);
      
      const zipBlob = await zip.generateAsync({ type: 'blob' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(zipBlob);
      link.download = 'neural_lens_batch.zip';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    } catch (err) {
      console.error('Error creating zip:', err);
      alert('Failed to create ZIP file.');
    } finally {
      setIsZipping(false);
    }
  };

  return (
    <div className="batch-queue-container page-enter">
      <div className="batch-header">
        <h2>Batch Processing</h2>
        <p>{files.length} images</p>
      </div>
      
      <div className="batch-list">
        {files.map((file, idx) => (
          <div key={idx} className={`batch-item status-${statuses[idx]}`}>
            <div className="batch-item-preview">
              <img src={previewUrls[idx]} alt="Preview" />
            </div>
            
            <div className="batch-item-info">
              <span className="batch-item-name">{file.name}</span>
              {statuses[idx] === 'error' && (
                <span className="batch-item-error">{errors[idx] || 'Failed'}</span>
              )}
            </div>
            
            <div className="batch-item-status">
              {statuses[idx] === 'queued' && <span className="status-badge queued">Queued</span>}
              {statuses[idx] === 'processing' && (
                <span className="status-badge processing">
                  <Loader2 size={14} className="spin" /> Processing
                </span>
              )}
              {statuses[idx] === 'success' && (
                <span className="status-badge success">
                  <CheckCircle2 size={14} /> Done
                </span>
              )}
              {statuses[idx] === 'error' && (
                <span className="status-badge error">
                  <AlertCircle size={14} /> Error
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="batch-actions">
        {allDone && anySuccess && (
          <Button 
            variant="primary" 
            size="lg" 
            onClick={downloadZip} 
            disabled={isZipping}
            className="batch-btn"
          >
            {isZipping ? (
              <><Loader2 size={18} className="spin" /> Creating ZIP...</>
            ) : (
              <><Download size={18} /> Download All as ZIP</>
            )}
          </Button>
        )}
        
        {(allDone || statuses.every(s => s === 'queued')) && (
          <Button 
            variant="outline" 
            size="lg" 
            onClick={onReset}
            className="batch-btn"
          >
            {allDone ? 'Process More Images' : 'Cancel'}
          </Button>
        )}
      </div>
    </div>
  );
};

export default BatchQueue;
