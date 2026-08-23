import { useState, useRef, useMemo, useEffect } from 'react';
import { UploadCloud, Image as ImageIcon, X } from 'lucide-react';
import Button from '../ui/Button';
import './DropZone.css';

const DropZone = ({ onFileSelected }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');
  const inputRef = useRef(null);
  
  const previewUrl = useMemo(() => {
    return selectedFile ? URL.createObjectURL(selectedFile) : null;
  }, [selectedFile]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const validateFile = (file) => {
    setError('');
    
    // Check file type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setError('Please upload a valid image file (JPEG, PNG, WEBP).');
      return false;
    }

    // Check file size (2MB)
    const MAX_SIZE = 2 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      setError('Image must be less than 2MB.');
      return false;
    }

    return true;
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

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const clearFile = (e) => {
    e.stopPropagation();
    setSelectedFile(null);
    setError('');
    if (inputRef.current) inputRef.current.value = '';
  };

  const handleUpload = () => {
    if (selectedFile) {
      onFileSelected(selectedFile);
    }
  };

  return (
    <div className="dropzone-container">
      <div 
        className={`dropzone-area ${dragActive ? 'drag-active' : ''} ${selectedFile ? 'has-file' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !selectedFile && inputRef.current?.click()}
      >
        <input 
          ref={inputRef}
          type="file" 
          accept="image/jpeg, image/png, image/webp" 
          onChange={handleChange} 
          className="dropzone-input"
        />

        {selectedFile ? (
          <div className="dropzone-preview">
            <div className="preview-image-container">
              <img 
                src={previewUrl} 
                alt="Preview" 
                className="preview-image"
              />
              <button className="clear-btn" onClick={clearFile} aria-label="Remove image">
                <X size={16} />
              </button>
            </div>
            <div className="file-info">
              <ImageIcon size={18} className="file-icon" />
              <span className="file-name">{selectedFile.name}</span>
              <span className="file-size">({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)</span>
            </div>
          </div>
        ) : (
          <div className="dropzone-prompt">
            <div className="dropzone-icon-wrapper">
              <UploadCloud size={48} />
            </div>
            <h3>Drop your image here</h3>
            <p>or click to browse from your device</p>
            <div className="dropzone-limits">
              Supports JPEG, PNG, WEBP (Max 2MB)
            </div>
          </div>
        )}
      </div>

      {error && <div className="dropzone-error">{error}</div>}

      <div className="dropzone-actions">
        <Button 
          variant="primary" 
          size="lg" 
          disabled={!selectedFile}
          onClick={handleUpload}
          className="upload-submit-btn"
        >
          Enhance Image
        </Button>
      </div>
    </div>
  );
};

export default DropZone;
