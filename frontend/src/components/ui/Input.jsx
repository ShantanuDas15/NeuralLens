import { forwardRef } from 'react';
import './Input.css';

const Input = forwardRef(({ label, error, className = '', ...props }, ref) => {
  return (
    <div className={`ui-input-wrapper ${className}`}>
      {label && <label className="ui-input-label">{label}</label>}
      <input 
        ref={ref}
        className={`ui-input ${error ? 'ui-input-error' : ''}`}
        {...props}
      />
      {error && <span className="ui-input-error-text">{error}</span>}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;
