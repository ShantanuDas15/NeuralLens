import { useEffect, useReducer, createContext, useContext } from 'react';
import { X, CheckCircle, AlertCircle, Info, Loader2 } from 'lucide-react';
import './Toast.css';

const ToastContext = createContext(null);

export const toast = {
  dispatch: null,
  success: (message, duration = 4000) => {
    const id = Date.now() + Math.random();
    toast.dispatch?.({ type: 'ADD', payload: { id, type: 'success', message, duration } });
    return id;
  },
  error: (message, duration = 4000) => {
    const id = Date.now() + Math.random();
    toast.dispatch?.({ type: 'ADD', payload: { id, type: 'error', message, duration } });
    return id;
  },
  info: (message, duration = 4000) => {
    const id = Date.now() + Math.random();
    toast.dispatch?.({ type: 'ADD', payload: { id, type: 'info', message, duration } });
    return id;
  },
  loading: (message) => {
    const id = Date.now() + Math.random();
    toast.dispatch?.({ type: 'ADD', payload: { id, type: 'loading', message, duration: 0 } });
    return id;
  },
  dismiss: (id) => {
    toast.dispatch?.({ type: 'REMOVE', payload: id });
  }
};

export const useToast = () => useContext(ToastContext);

const toastReducer = (state, action) => {
  switch (action.type) {
    case 'ADD':
      return [...state.slice(-2), action.payload];
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
    if (toast.duration === 0) return;
    const duration = toast.duration || 4000;
    const timer = setTimeout(() => {
      onRemove();
    }, duration);
    return () => clearTimeout(timer);
  }, [toast, onRemove]);

  const Icon = toast.type === 'success' ? CheckCircle : 
               toast.type === 'error' ? AlertCircle : 
               toast.type === 'loading' ? Loader2 : Info;

  return (
    <div className={`ui-toast ui-toast-${toast.type} page-enter`}>
      <Icon className={`ui-toast-icon ${toast.type === 'loading' ? 'spin' : ''}`} size={20} />
      <span className="ui-toast-message">{toast.message}</span>
      <button onClick={onRemove} className="ui-toast-close" aria-label="Close toast">
        <X size={16} />
      </button>
    </div>
  );
};

export default ToastProvider;
