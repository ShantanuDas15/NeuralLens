import { useState, useRef, useMemo, useEffect } from 'react';
import { UploadCloud, Image as ImageIcon, X } from 'lucide-react';
import Button from '../ui/Button';
import './DropZone.css';

const MAX_FILES = 5;
const MAX_SIZE = 2 * 1024 * 1024;

const DropZone = ({ onFilesSelected, multiple = true }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [error, setError] = useState('');
  const [scale, setScale] = useState(4);
  const inputRef = useRef(null);

  const previewUrls = useMemo(() => {
    return selectedFiles.map(file => URL.createObjectURL(file));
  }, [selectedFiles]);

  useEffect(() => {
    return () => {
      previewUrls.forEach(url => URL.revokeObjectURL(url));
    };
  }, [previewUrls]);

  const validateFiles = (files) => {
    setError('');
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    const validFiles = [];

    if (files.length > MAX_FILES) {
      setError(`You can only upload a maximum of ${MAX_FILES} images at once.`);
      return [];
    }

    for (const file of files) {
      if (!validTypes.includes(file.type)) {
        setError('Please upload only valid image files (JPEG, PNG, WEBP).');
        return [];
      }
      if (file.size > MAX_SIZE) {
        setError('Each image must be less than 2MB.');
        return [];
      }
      validFiles.push(file);
    }

    return validFiles;
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const filesArray = Array.from(e.dataTransfer.files);
      const validFiles = validateFiles(filesArray);
      if (validFiles.length > 0) {
        setSelectedFiles(validFiles);
      }
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      const filesArray = Array.from(e.target.files);
      const validFiles = validateFiles(filesArray);
      if (validFiles.length > 0) {
        setSelectedFiles(validFiles);
      }
    }
  };

  const removeFile = (e, indexToRemove) => {
    e.stopPropagation();
    setSelectedFiles(prev => prev.filter((_, idx) => idx !== indexToRemove));
    setError('');
    if (inputRef.current) inputRef.current.value = '';
  };

  const clearAllFiles = (e) => {
    e.stopPropagation();
    setSelectedFiles([]);
    setError('');
    if (inputRef.current) inputRef.current.value = '';
  };

  const handleUpload = () => {
    if (selectedFiles.length > 0) {
      onFilesSelected(selectedFiles, scale);
    }
  };

  return (
    <div className="dropzone-container">
      <div 
        className={`dropzone-area ${dragActive ? 'drag-active' : ''} ${selectedFiles.length > 0 ? 'has-file' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => selectedFiles.length === 0 && inputRef.current?.click()}
      >
        <input 
          ref={inputRef}
          type="file" 
          accept="image/jpeg, image/png, image/webp" 
          onChange={handleChange} 
          className="dropzone-input"
          multiple={multiple}
        />

        {selectedFiles.length > 0 ? (
          <div className="dropzone-previews">
            <div className="preview-grid">
              {selectedFiles.map((file, idx) => (
                <div key={idx} className="preview-image-container">
                  <img 
                    src={previewUrls[idx]} 
                    alt={`Preview ${idx + 1}`} 
                    className="preview-image"
                  />
                  <button className="clear-btn" onClick={(e) => removeFile(e, idx)} aria-label="Remove image">
                    <X size={14} />
                  </button>
                  <div className="file-info-mini">
                    <span className="file-name">{file.name}</span>
                  </div>
                </div>
              ))}
            </div>
            {selectedFiles.length > 1 && (
               <button className="clear-all-btn" onClick={clearAllFiles}>
                 Clear All
               </button>
            )}
          </div>
        ) : (
          <div className="dropzone-prompt">
            <div className="dropzone-icon-wrapper">
              <UploadCloud size={48} />
            </div>
            <h3>Drop your image{multiple ? 's' : ''} here</h3>
            <p>or click to browse from your device</p>
            <div className="dropzone-limits">
              Supports JPEG, PNG, WEBP (Max 2MB per file, up to {MAX_FILES} files)
            </div>
          </div>
        )}
      </div>

      {error && <div className="dropzone-error">{error}</div>}

      <div className="dropzone-actions">
        {selectedFiles.length > 1 && (
          <div className="batch-scale-picker">
            <span className="scale-label">Scale:</span>
            <div className="scale-toggle-group">
              {[2, 4].map((s) => (
                <button
                  key={s}
                  className={`scale-btn ${scale === s ? 'active' : ''}`}
                  onClick={() => setScale(s)}
                >
                  {s}×
                </button>
              ))}
            </div>
          </div>
        )}
        <Button 
          variant="primary" 
          size="lg" 
          disabled={selectedFiles.length === 0}
          onClick={handleUpload}
          className="upload-submit-btn"
        >
          {selectedFiles.length > 1 ? `Enhance ${selectedFiles.length} Images` : 'Enhance Image'}
        </Button>
      </div>
    </div>
  );
};

export default DropZone;
