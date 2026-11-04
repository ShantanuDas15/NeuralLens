import { useState, useRef, useMemo, useEffect } from 'react';
import { UploadCloud, X } from 'lucide-react';
import Button from '../ui/Button';
import './DropZone.css';

const MAX_FILES = 5;
const MAX_SIZE = 2 * 1024 * 1024;
// The backend only decodes JPEG and PNG (services/image_utils.py), so accepting
// anything else here would just fail after the upload.
const VALID_TYPES = ['image/jpeg', 'image/png'];

/**
 * variant "hero": the large centrepiece (returning users).
 * variant "compact": a one-row strip under the samples (first visit).
 * The upscale factor is owned by the dashboard so samples and uploads share it.
 */
const DropZone = ({ onFilesSelected, scale, variant = 'hero', multiple = true }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [error, setError] = useState('');
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
    const validFiles = [];

    if (files.length > MAX_FILES) {
      setError(`You can only upload a maximum of ${MAX_FILES} images at once.`);
      return [];
    }

    for (const file of files) {
      if (!VALID_TYPES.includes(file.type)) {
        setError('Please upload only JPEG or PNG images.');
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

  const browse = (e) => {
    e.stopPropagation(); // the area also opens the picker on click
    inputRef.current?.click();
  };

  const handleUpload = () => {
    if (selectedFiles.length > 0) {
      onFilesSelected(selectedFiles, scale);
    }
  };

  const limits = `JPEG or PNG · up to 2 MB each · up to ${MAX_FILES} at once`;

  return (
    <div className={`dropzone-container dz-${variant}`}>
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
          accept="image/jpeg, image/png"
          onChange={handleChange}
          className="dropzone-input"
          multiple={multiple}
          tabIndex={-1}
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
        ) : variant === 'compact' ? (
          <div className="dz-row">
            <UploadCloud size={26} aria-hidden="true" className="dz-row-icon" />
            <div className="dz-row-text">
              <strong>Or drop your own photo here</strong>
              <span>{limits}</span>
            </div>
            <Button variant="secondary" type="button" onClick={browse}>Browse files</Button>
          </div>
        ) : (
          <div className="dropzone-prompt">
            <div className="dz-ring"><UploadCloud size={34} aria-hidden="true" /></div>
            <h3>Drop image{multiple ? 's' : ''} here</h3>
            <p>or choose {multiple ? 'them' : 'it'} from your device</p>
            <Button variant="primary" type="button" onClick={browse}>Browse files</Button>
            <ul className="dz-chips">
              <li>JPEG or PNG</li>
              <li>Up to 2 MB each</li>
              <li>Up to {MAX_FILES} at once</li>
            </ul>
          </div>
        )}
      </div>

      {error && <div className="dropzone-error" role="alert">{error}</div>}

      {selectedFiles.length > 0 && (
        <div className="dropzone-actions">
          <Button
            variant="primary"
            size="lg"
            onClick={handleUpload}
            className="upload-submit-btn"
          >
            {selectedFiles.length > 1
              ? `Enhance ${selectedFiles.length} Images`
              : `Enhance Image ${scale}×`}
          </Button>
        </div>
      )}
    </div>
  );
};

export default DropZone;
