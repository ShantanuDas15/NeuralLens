import { useEffect, useState } from 'react';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';
import './Toast.css';

// A simple local state manager to trigger toasts from anywhere
let toastCount = 0;
let addToastHandler = null;

export const toast = {
  success: (message, duration) => addToastHandler?.({ id: ++toastCount, type: 'success', message, duration }),
  error: (message, duration) => addToastHandler?.({ id: ++toastCount, type: 'error', message, duration }),
  info: (message, duration) => addToastHandler?.({ id: ++toastCount, type: 'info', message, duration })
};

const ToastContainer = () => {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    addToastHandler = (toastParams) => {
      setToasts((prev) => [...prev, toastParams]);
    };
    return () => { addToastHandler = null; };
  }, []);

  const removeToast = (id) => {
    setToasts((prev) => prev.filter(t => t.id !== id));
  };

  return (
    <div className="ui-toast-container">
      {toasts.map(t => (
        <ToastItem key={t.id} toast={t} onRemove={() => removeToast(t.id)} />
      ))}
    </div>
  );
};

const ToastItem = ({ toast, onRemove }) => {
  useEffect(() => {
    const duration = toast.duration || 4000;
    const timer = setTimeout(() => {
      onRemove();
    }, duration);
    return () => clearTimeout(timer);
  }, [toast, onRemove]);

  const Icon = toast.type === 'success' ? CheckCircle : 
               toast.type === 'error' ? AlertCircle : Info;

  return (
    <div className={`ui-toast ui-toast-${toast.type} page-enter`}>
      <Icon className="ui-toast-icon" size={20} />
      <span className="ui-toast-message">{toast.message}</span>
      <button onClick={onRemove} className="ui-toast-close" aria-label="Close toast">
        <X size={16} />
      </button>
    </div>
  );
};

export default ToastContainer;
