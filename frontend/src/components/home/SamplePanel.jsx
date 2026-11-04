import { SAMPLES } from './samples';
import './Home.css';

/** One-click samples (the first-visit hero), with the drop zone passed in as children. */
const SamplePanel = ({ scale, onPick, busy, children }) => (
  <section className="tile sample-panel" aria-label="Try a sample">
    <div className="sample-head">
      <h2>Try a sample</h2>
      <span className="chip">Runs on the real Real-ESRGAN model</span>
    </div>

    <div className="sample-grid">
      {SAMPLES.map((sample) => (
        <article key={sample.id} className="sample-card">
          <div className="sample-img">
            <img src={sample.src} alt={sample.alt} width={sample.width} height={sample.height} />
            <span className="sample-tag">Low-res · {sample.width}×{sample.height}</span>
          </div>
          <div className="sample-body">
            <h3>{sample.name}</h3>
            <p>{sample.width}×{sample.height} → {sample.width * scale}×{sample.height * scale}</p>
            <button
              type="button"
              className="sample-btn"
              disabled={busy}
              onClick={() => onPick(sample)}
            >
              Enhance {scale}×
            </button>
          </div>
        </article>
      ))}
    </div>

    {children}
  </section>
);

export default SamplePanel;
