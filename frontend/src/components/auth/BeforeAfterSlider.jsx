import { useState } from 'react';
import './BeforeAfterSlider.css';

/**
 * Static before/after comparison for the auth screens.
 *
 * A transparent native range input sits over the images, so mouse, touch and
 * keyboard (arrow keys) all work and screen readers get a real slider.
 */
const BeforeAfterSlider = ({
  beforeSrc,
  afterSrc,
  beforeAlt,
  afterAlt,
  beforeLabel,
  beforeMeta,
  afterLabel,
  afterMeta,
  width,
  height,
  initial = 52,
}) => {
  const [pos, setPos] = useState(initial);

  return (
    <div
      className="ba"
      style={{ '--pos': `${pos}%`, aspectRatio: `${width} / ${height}` }}
    >
      <img
        className="ba-img"
        src={beforeSrc}
        alt={beforeAlt}
        width={width}
        height={height}
        decoding="async"
        fetchPriority="high"
      />
      <img
        className="ba-img ba-img-after"
        src={afterSrc}
        alt={afterAlt}
        width={width}
        height={height}
        decoding="async"
      />

      <span className="ba-tag ba-tag-before">
        {beforeLabel}
        <span className="ba-meta"> · {beforeMeta}</span>
      </span>
      <span className="ba-tag ba-tag-after">
        {afterLabel}
        <span className="ba-meta"> · {afterMeta}</span>
      </span>

      <input
        className="ba-range"
        type="range"
        min="0"
        max="100"
        step="1"
        value={pos}
        onChange={(e) => setPos(Number(e.target.value))}
        aria-label="Comparison slider: original on the left, enhanced on the right"
        aria-valuetext={`${pos}% original, ${100 - pos}% enhanced`}
      />
      <div className="ba-line" aria-hidden="true" />
      <div className="ba-knob" aria-hidden="true">
        <svg
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M9 7l-5 5 5 5" />
          <path d="M15 7l5 5-5 5" />
        </svg>
      </div>
    </div>
  );
};

export default BeforeAfterSlider;
