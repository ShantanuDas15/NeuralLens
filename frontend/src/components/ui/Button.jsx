import './Button.css';

const Button = ({ children, variant = 'primary', size = 'md', loading = false, disabled = false, className = '', ...props }) => {
  const baseClass = 'btn';
  const variantClass = `btn-${variant}`; // primary, ghost, danger
  const sizeClass = `btn-${size}`; // sm, md, lg
  
  return (
    <button 
      className={`${baseClass} ${variantClass} ${sizeClass} ${loading ? 'btn-loading' : ''} ${className}`}
      disabled={loading || disabled}
      {...props}
    >
      {loading && <span className="btn-spinner"></span>}
      <span className="btn-text">{children}</span>
    </button>
  );
};

export default Button;
