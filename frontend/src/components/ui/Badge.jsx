import './Badge.css';

const Badge = ({ status = 'pending', children, className = '' }) => {
  // status: completed (green) / processing (amber) / failed (red) / pending (default)
  return (
    <span className={`ui-badge ui-badge-${status} ${className}`}>
      <span className="ui-badge-dot"></span>
      {children || status}
    </span>
  );
};

export default Badge;
