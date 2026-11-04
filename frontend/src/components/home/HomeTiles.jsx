import { ArrowRight, ExternalLink, Sparkles } from 'lucide-react';
import { relativeDay } from '../../utils/relativeDay';
import './Home.css';

const REPO_URL = 'https://github.com/ShantanuDas15/NeuralLens';
const SCALES = [2, 4, 8];

/** 2x / 4x / 8x segmented control shared by the samples and the drop zone. */
export const ScaleTile = ({ scale, onChange }) => (
  <section className="tile scale-tile" aria-label="Upscale factor">
    <div className="tile-label">Upscale factor</div>
    <div className="seg-group" role="group" aria-label="Upscale factor">
      {SCALES.map((s) => (
        <button
          key={s}
          type="button"
          className={`seg ${scale === s ? 'on' : ''}`}
          aria-pressed={scale === s}
          onClick={() => onChange(s)}
        >
          {s}×
        </button>
      ))}
    </div>
    <p className="tile-note">
      A 600×400 photo becomes <strong>{600 * scale}×{400 * scale}</strong>
    </p>
  </section>
);

export const HowItWorks = () => (
  <section className="tile" aria-label="How it works">
    <div className="tile-label">How it works</div>
    <ol className="steps">
      <li><span>1</span>Pick a sample, or drop a photo of your own.</li>
      <li><span>2</span>Choose 2×, 4× or 8×. The model rebuilds the missing detail.</li>
      <li><span>3</span>Drag to compare against a plain resize, then download the PNG.</li>
    </ol>
  </section>
);

export const AboutProject = () => (
  <section className="tile about-tile" aria-label="About this project">
    <div className="tile-label">About this project</div>
    <p className="tile-note">A full-stack project by Shantanu Das, built and deployed end to end.</p>
    <a className="text-link" href={REPO_URL} target="_blank" rel="noopener noreferrer">
      View the source on GitHub <ExternalLink size={14} aria-hidden="true" />
    </a>
  </section>
);

export const ActivityTile = ({ stats }) => {
  if (!stats) return null;
  const total = stats.total_jobs ?? 0;
  const rate = total > 0 ? `${Math.round(((stats.successful_jobs ?? 0) / total) * 100)}%` : '–';
  return (
    <section className="tile" aria-label="Your activity">
      <div className="tile-label">Your activity</div>
      <dl className="stats">
        <div><dd>{stats.successful_jobs ?? 0}</dd><dt>Images enhanced</dt></div>
        <div><dd>{rate}</dd><dt>Success rate</dt></div>
        <div><dd>{relativeDay(stats.last_job_at) || '–'}</dd><dt>Last job</dt></div>
      </dl>
    </section>
  );
};

export const TipTile = () => (
  <section className="tile tip-tile" aria-label="Tip">
    <Sparkles size={20} aria-hidden="true" />
    <p>Photos up to about 2000 px on the long side give the best results.</p>
  </section>
);

const PIPELINE = [
  { title: 'React app', note: 'Firebase sign-in' },
  { title: 'FastAPI', note: 'auth, limits, validation' },
  { title: 'Real-ESRGAN', note: 'PyTorch inference' },
  { title: 'PostgreSQL + volume', note: 'history and images' },
];

export const UnderTheHood = () => (
  <section className="tile hood" aria-label="Under the hood">
    <div className="hood-head">
      <div className="tile-label">Under the hood</div>
      <span>Hosted on Railway · every push tested by GitHub Actions</span>
    </div>
    <ol className="pipeline">
      {PIPELINE.map((node, i) => (
        <li key={node.title}>
          <div className="node"><b>{node.title}</b><span>{node.note}</span></div>
          {i < PIPELINE.length - 1 && <ArrowRight className="arrow" size={20} aria-hidden="true" />}
        </li>
      ))}
    </ol>
  </section>
);
