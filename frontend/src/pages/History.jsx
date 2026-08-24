import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Download, ExternalLink, RefreshCw, AlertCircle, Trash2, RotateCcw, Columns } from 'lucide-react';
import api from '../api';
import useApi from '../hooks/useApi';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import { toast } from '../components/ui/Toast';
import HistoryCardSkeleton from '../components/history/HistoryCardSkeleton';
import ImageCompare from '../components/compare/ImageCompare';
import './History.css';

const History = () => {
  const [page, setPage] = useState(1);
  const pageSize = 9;
  const navigate = useNavigate();
  const [deleteLoading, setDeleteLoading] = useState(null);
  const [compareJob, setCompareJob] = useState(null);
  
  const { data, loading, error, execute } = useApi();

  useEffect(() => {
    execute(() => api.get(`/history?page=${page}&page_size=${pageSize}`)).catch(() => {});
  }, [page, execute]);

  const handleDownload = async (url, id) => {
    if (!url) return;
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const objUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objUrl;
      a.download = `neurallens-${id}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(objUrl);
      toast.success('Download started');
    } catch (err) {
      toast.error('Failed to download image');
    }
  };

  const handleProcessAgain = (job) => {
    toast.info(`Ready to re-enhance! Please select "${job.original_filename}"`);
    navigate('/');
  };

  const handleDelete = async (job) => {
    if (!window.confirm(`Are you sure you want to remove "${job.original_filename}" from your history?`)) return;
    
    try {
      setDeleteLoading(job.job_id);
      await api.delete(`/history/${job.job_id}`);
      toast.success('Job removed from history');
      execute(() => api.get(`/history?page=${page}&page_size=${pageSize}`));
    } catch (err) {
      toast.error('Failed to delete job');
    } finally {
      setDeleteLoading(null);
    }
  };

  if (loading && !data) {
    return (
      <div className="history-container page-enter">
        <div className="history-header">
          <div>
            <h1 className="history-title">Enhancement History</h1>
            <p className="history-subtitle">View and download your previously processed images.</p>
          </div>
        </div>
        <div className="history-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <HistoryCardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="history-error page-enter">
        <AlertCircle size={48} className="error-icon" />
        <h2>Failed to load history</h2>
        <p>{error}</p>
        <Button onClick={() => execute(page)}>Try Again</Button>
      </div>
    );
  }

  const items = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="history-container page-enter">
      <div className="history-header">
        <div>
          <h1 className="history-title">Enhancement History</h1>
          <p className="history-subtitle">View and download your previously processed images.</p>
        </div>
        <div className="history-stats" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <Button 
            variant="secondary" 
            size="sm"
            onClick={() => execute(() => api.get(`/history?page=${page}&page_size=${pageSize}`))}
            disabled={loading}
            icon={<RefreshCw size={16} className={loading ? "spin" : ""} />}
          >
            Refresh
          </Button>
          <Badge status="completed">{total} Total Images</Badge>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="history-empty">
          <div className="empty-icon-wrapper">
            <RefreshCw size={40} />
          </div>
          <h3>No history yet</h3>
          <p>You haven't enhanced any images yet. Head over to the dashboard to get started!</p>
        </div>
      ) : (
        <>
          <div className="history-grid">
            {items.map((job) => (
              <div key={job.job_id} className="history-card">
                <div className="history-card-image-wrapper">
                  {job.status === 'completed' && job.result_url ? (
                    <img 
                      src={job.result_url} 
                      alt={job.original_filename} 
                      className="history-card-image" 
                      loading="lazy" 
                    />
                  ) : (
                    <div className="history-card-placeholder">
                      <AlertCircle size={32} />
                      <span>{job.status === 'failed' ? 'Processing Failed' : 'Processing...'}</span>
                    </div>
                  )}
                  <div className="history-card-overlay">
                    <Button 
                      size="sm" 
                      variant="primary" 
                      disabled={job.status !== 'completed'}
                      onClick={() => handleDownload(job.result_url, job.job_id)}
                      aria-label="Download Image"
                      title="Download"
                    >
                      <Download size={16} />
                    </Button>
                    <a 
                      href={job.result_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className={`btn btn-sm btn-ghost ${job.status !== 'completed' ? 'disabled' : ''}`}
                      onClick={(e) => job.status !== 'completed' && e.preventDefault()}
                      aria-label="View Original"
                      title="View Full Size"
                    >
                      <ExternalLink size={16} />
                    </a>
                    <Button 
                      size="sm" 
                      variant="secondary" 
                      onClick={() => handleProcessAgain(job)}
                      aria-label="Process Again"
                      title="Process Again"
                    >
                      <RotateCcw size={16} />
                    </Button>
                    <Button 
                      size="sm" 
                      variant="primary" 
                      onClick={() => setCompareJob(job)}
                      disabled={job.status !== 'completed'}
                      aria-label="Compare"
                      title="Compare Original & Enhanced"
                    >
                      <Columns size={16} />
                    </Button>
                    <Button 
                      size="sm" 
                      variant="danger" 
                      onClick={() => handleDelete(job)}
                      disabled={deleteLoading === job.job_id}
                      aria-label="Delete"
                      title="Remove from history"
                    >
                      {deleteLoading === job.job_id ? <Spinner size="sm" /> : <Trash2 size={16} />}
                    </Button>
                  </div>
                </div>
                
                <div className="history-card-details">
                  <div className="detail-row">
                    <span className="file-name" title={job.original_filename}>
                      {job.original_filename}
                    </span>
                    <Badge status={job.status} />
                  </div>
                  
                  <div className="detail-meta">
                    <span className="meta-item">
                      {job.input_w}x{job.input_h} → {job.output_w}x{job.output_h}
                    </span>
                    <span className="meta-dot">•</span>
                    <span className="meta-item">
                      {new Date(job.created_at).toLocaleDateString(undefined, { 
                        month: 'short', 
                        day: 'numeric',
                        year: 'numeric'
                      })}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="history-pagination">
              <Button 
                variant="ghost" 
                disabled={page === 1 || loading} 
                onClick={() => setPage(p => p - 1)}
              >
                Previous
              </Button>
              <span className="pagination-text">
                Page {page} of {totalPages}
              </span>
              <Button 
                variant="ghost" 
                disabled={page === totalPages || loading} 
                onClick={() => setPage(p => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}

      {compareJob && (
        <div className="history-modal-overlay" onClick={() => setCompareJob(null)}>
          <div className="history-modal-content" onClick={e => e.stopPropagation()}>
            <div className="history-modal-header">
              <h3>Compare: {compareJob.original_filename}</h3>
              <button className="history-modal-close" onClick={() => setCompareJob(null)}>×</button>
            </div>
            <div className="history-modal-body">
              <ImageCompare result={compareJob} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default History;
