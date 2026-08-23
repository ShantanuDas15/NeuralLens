import './HistoryCardSkeleton.css';

const HistoryCardSkeleton = () => {
  return (
    <div className="history-card skeleton-card fade-in-up">
      <div className="history-image skeleton-pulse"></div>
      <div className="history-content">
        <div className="history-meta">
          <div className="skeleton-text skeleton-pulse" style={{ width: '40%' }}></div>
          <div className="skeleton-text skeleton-pulse" style={{ width: '30%' }}></div>
        </div>
        <div className="history-actions">
          <div className="skeleton-button skeleton-pulse"></div>
          <div className="skeleton-button skeleton-pulse"></div>
        </div>
      </div>
    </div>
  );
};

export default HistoryCardSkeleton;
