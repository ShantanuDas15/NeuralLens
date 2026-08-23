import { useEffect, useReducer, createContext, useContext } from 'react';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';
import './Toast.css';

const ToastContext = createContext(null);

export const toast = {
  dispatch: null,
  success: (message, duration = 4000) => toast.dispatch?.({ type: 'ADD', payload: { id: Date.now() + Math.random(), type: 'success', message, duration } }),
  error: (message, duration = 4000) => toast.dispatch?.({ type: 'ADD', payload: { id: Date.now() + Math.random(), type: 'error', message, duration } }),
  info: (message, duration = 4000) => toast.dispatch?.({ type: 'ADD', payload: { id: Date.now() + Math.random(), type: 'info', message, duration } })
};

export const useToast = () => useContext(ToastContext);

const toastReducer = (state, action) => {
  switch (action.type) {
    case 'ADD':
      return [...state, action.payload];
    case 'REMOVE':
      return state.filter(t => t.id !== action.payload);
    default:
      return state;
  }
};

export const ToastProvider = ({ children }) => {
  const [toasts, dispatch] = useReducer(toastReducer, []);

  useEffect(() => {
    toast.dispatch = dispatch;
    return () => { toast.dispatch = null; };
  }, []);

  return (
    <ToastContext.Provider value={dispatch}>
      {children}
      <div className="ui-toast-container">
        {toasts.map(t => (
          <ToastItem key={t.id} toast={t} onRemove={() => dispatch({ type: 'REMOVE', payload: t.id })} />
        ))}
      </div>
    </ToastContext.Provider>
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

export default ToastProvider;
