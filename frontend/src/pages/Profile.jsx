import { useEffect } from 'react';
import { User as UserIcon, Calendar, Image as ImageIcon, CheckCircle, XCircle, Clock, RefreshCw } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import api from '../api';
import useApi from '../hooks/useApi';
import Spinner from '../components/ui/Spinner';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import './Profile.css';

const Profile = () => {
  const { user } = useAuth();
  
  const { data: profile, loading, error, execute } = useApi();

  useEffect(() => {
    execute(() => api.get('/profile')).catch(() => {});
  }, [execute]);

  if (loading && !profile) {
    return (
      <div className="profile-loading page-enter">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error && !profile) {
    return (
      <div className="profile-error page-enter">
        <p>Failed to load profile stats: {error}</p>
      </div>
    );
  }

  const stats = profile?.stats || { total_jobs: 0, successful_jobs: 0, failed_jobs: 0, last_job_at: null };

  return (
    <div className="profile-container page-enter">
      <div className="profile-header">
        <div className="profile-avatar-large">
          {user?.photoURL ? (
            <img 
              src={user.photoURL} 
              alt="Profile" 
              referrerPolicy="no-referrer"
            />
          ) : (
            <UserIcon size={48} />
          )}
        </div>
        <div className="profile-info-header">
          <h1 className="profile-name">{user?.displayName || 'NeuralLens User'}</h1>
          <p className="profile-email">{user?.email}</p>
        </div>
        <div style={{ marginLeft: 'auto' }}>
          <Button 
            variant="secondary" 
            size="sm"
            onClick={() => execute(() => api.get('/profile'))}
            disabled={loading}
            icon={<RefreshCw size={16} className={loading ? "spin" : ""} />}
          >
            Refresh
          </Button>
        </div>
      </div>

      <div className="profile-content">
        <Card className="profile-card">
          <h2 className="card-title">Account Details</h2>
          <div className="details-list">
            <div className="detail-item">
              <UserIcon size={18} className="detail-icon" />
              <div className="detail-text">
                <span className="detail-label">Account ID</span>
                <span className="detail-value">{user?.uid}</span>
              </div>
            </div>
            <div className="detail-item">
              <Calendar size={18} className="detail-icon" />
              <div className="detail-text">
                <span className="detail-label">Member Since</span>
                <span className="detail-value">
                  {profile?.member_since ? new Date(profile.member_since).toLocaleDateString() : 'Unknown'}
                </span>
              </div>
            </div>
            <div className="detail-item">
              <Clock size={18} className="detail-icon" />
              <div className="detail-text">
                <span className="detail-label">Last Enhanced Activity</span>
                <span className="detail-value">
                  {stats.last_job_at ? new Date(stats.last_job_at).toLocaleString() : 'Never'}
                </span>
              </div>
            </div>
          </div>
        </Card>

        <Card className="profile-card">
          <h2 className="card-title">Usage Statistics</h2>
          <div className="stats-grid">
            <div className="stat-box">
              <div className="stat-icon-wrapper total">
                <ImageIcon size={24} />
              </div>
              <span className="stat-value">{stats.total_jobs}</span>
              <span className="stat-label">Total Processed</span>
            </div>
            <div className="stat-box">
              <div className="stat-icon-wrapper success">
                <CheckCircle size={24} />
              </div>
              <span className="stat-value">{stats.successful_jobs}</span>
              <span className="stat-label">Successful</span>
            </div>
            <div className="stat-box">
              <div className="stat-icon-wrapper failed">
                <XCircle size={24} />
              </div>
              <span className="stat-value">{stats.failed_jobs}</span>
              <span className="stat-label">Failed</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Profile;
