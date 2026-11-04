import { Link } from 'react-router-dom';
import AuthedImage from '../ui/AuthedImage';
import { relativeDay } from '../../utils/relativeDay';
import './Home.css';

/** The user's latest completed enhancements; renders nothing when there are none. */
const RecentStrip = ({ items }) => {
  const recent = items.filter((job) => job.result_url);
  if (recent.length === 0) return null;

  return (
    <section className="recent" aria-label="Recent enhancements">
      <div className="recent-head">
        <h2>Recent enhancements</h2>
        <Link className="text-link" to="/history">View all →</Link>
      </div>
      <ul className="recent-grid">
        {recent.map((job) => (
          <li key={job.job_id}>
            <Link to="/history" className="recent-card">
              <div className="recent-img">
                <AuthedImage src={job.result_url} alt={`Enhanced ${job.original_filename}`} loading="lazy" />
                <span className="recent-badge">{Math.round(job.scale_factor)}×</span>
              </div>
              <div className="recent-meta">
                <span className="recent-name">{job.original_filename}</span>
                <span className="recent-date">{relativeDay(job.created_at)}</span>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
};

export default RecentStrip;
