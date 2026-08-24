import Button from '../ui/Button';
import { Sparkles, X } from 'lucide-react';
import './ImagePreview.css';

const ImagePreview = ({ originalUrl, file, onEnhance, onCancel }) => {
  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="image-preview-container page-enter">
      <div className="preview-image-wrapper">
        <img src={originalUrl} alt="Preview" className="preview-image" />
      </div>
      <div className="preview-details">
        <div className="preview-filename">{file.name}</div>
        <div className="preview-filesize">{formatBytes(file.size)}</div>
      </div>
      <div className="preview-actions">
        <Button variant="secondary" onClick={onCancel} icon={<X size={18} />}>
          Choose Different
        </Button>
        <Button variant="primary" onClick={onEnhance} icon={<Sparkles size={18} />}>
          Enhance This Image
        </Button>
      </div>
    </div>
  );
};

export default ImagePreview;
