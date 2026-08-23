import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';
import Button from '../components/ui/Button';

const NotFound = () => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100%',
      minHeight: '60vh',
      textAlign: 'center',
      gap: '1.5rem'
    }}>
      <h1 style={{ fontSize: '4rem', fontWeight: 800, color: 'var(--text-secondary)' }}>404</h1>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)' }}>Page Not Found</h2>
      <p style={{ color: 'var(--text-secondary)', maxWidth: '400px' }}>
        The page you are looking for doesn't exist or has been moved.
      </p>
      <div style={{ marginTop: '1rem' }}>
        <Link to="/" style={{ textDecoration: 'none' }}>
          <Button variant="primary" icon={<Home size={18} />}>
            Back to Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
