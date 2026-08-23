import { useEffect, useState } from 'react';
import { User as UserIcon, Image as ImageIcon, CheckCircle, XCircle, RefreshCw, Edit2, Save } from 'lucide-react';
import { updateProfile } from 'firebase/auth';
import { auth } from '../firebase';
import { useAuth } from '../hooks/useAuth';
import api from '../api';
import useApi from '../hooks/useApi';
import Spinner from '../components/ui/Spinner';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { toast } from '../components/ui/Toast';
import './Profile.css';

const Profile = () => {
  const { user } = useAuth();
  const { data: profile, loading, error, execute } = useApi();
  const [isEditing, setIsEditing] = useState(false);
  const [newName, setNewName] = useState('');
  const [updateLoading, setUpdateLoading] = useState(false);

  const handleEditClick = () => {
    setNewName(user?.displayName || '');
    setIsEditing(true);
  };

  const handleSaveProfile = async () => {
    try {
      setUpdateLoading(true);
      if (auth.currentUser) {
        await updateProfile(auth.currentUser, { displayName: newName });
        // Force token refresh to immediately sync to backend next request
        await auth.currentUser.getIdToken(true);
        // Sync with backend
        await execute(() => api.get('/profile'));
        toast.success("Profile updated successfully");
      }
      setIsEditing(false);
    } catch (err) {
      if (import.meta.env.DEV) console.error("Update profile error:", err);
      toast.error("Failed to update profile");
    } finally {
      setUpdateLoading(false);
    }
  };

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
          {isEditing ? (
            <div className="profile-edit-form">
              <div className="form-group">
                <label className="form-label">Username</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={newName} 
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Enter username"
                  disabled={updateLoading}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Email <span className="text-muted" style={{ fontSize: '0.8rem', marginLeft: '8px' }}>(Cannot be changed)</span></label>
                <input 
                  type="email" 
                  className="form-input" 
                  value={user?.email || ''} 
                  disabled
                />
              </div>
              <div className="profile-edit-actions" style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                <Button 
                  size="sm" 
                  variant="primary" 
                  onClick={handleSaveProfile}
                  disabled={updateLoading || !newName.trim() || newName.trim() === user?.displayName}
                  icon={<Save size={16} />}
                >
                  {updateLoading ? 'Saving...' : 'Save'}
                </Button>
                <Button 
                  size="sm" 
                  variant="secondary" 
                  onClick={() => setIsEditing(false)}
                  disabled={updateLoading}
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <>
              <div className="profile-name-row" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h1 className="profile-name">{user?.displayName || 'NeuralLens User'}</h1>
                <button className="btn btn-sm btn-ghost" style={{ padding: '4px' }} onClick={handleEditClick} aria-label="Edit Username">
                  <Edit2 size={16} />
                </button>
              </div>
              <p className="profile-email">{user?.email}</p>
            </>
          )}
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
