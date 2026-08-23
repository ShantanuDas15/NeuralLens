import './Spinner.css';

const Spinner = ({ size = 'md', className = '' }) => {
  return (
    <div className={`ui-spinner ui-spinner-${size} ${className}`}></div>
  );
};

export default Spinner;
