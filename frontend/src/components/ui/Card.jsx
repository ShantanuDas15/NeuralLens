import './Card.css';

const Card = ({ children, className = '', ...props }) => {
  return (
    <div className={`ui-card ${className}`} {...props}>
      {children}
    </div>
  );
};

export default Card;
