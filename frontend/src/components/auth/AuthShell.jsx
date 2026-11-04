import { Lock, Maximize2, Sparkles } from 'lucide-react';
import BeforeAfterSlider from './BeforeAfterSlider';
import beforeImg from '../../assets/auth/before.webp';
import afterImg from '../../assets/auth/after.webp';
import './AuthShell.css';

/**
 * Split-screen layout shared by the Login and Signup pages.
 *
 * Left: an always-dark "showcase" with a live before/after comparison (a real
 * Real-ESRGAN 4x result). Right: the form, themed with the app's tokens.
 * On narrow screens the two stack, showcase first.
 */
const AuthShell = ({ children }) => (
  <div className="auth-shell page-enter">
    <section className="auth-showcase" aria-label="NeuralLens preview">
      <div className="aurora aurora-1" aria-hidden="true" />
      <div className="aurora aurora-2" aria-hidden="true" />
      <div className="aurora aurora-3" aria-hidden="true" />
      <div className="auth-showcase-fade" aria-hidden="true" />

      <div className="auth-showcase-inner">
        <div className="auth-brand">
          <svg width="30" height="30" viewBox="0 0 30 30" fill="none" aria-hidden="true">
            <defs>
              <linearGradient id="auth-lens" x1="4" y1="4" x2="26" y2="26" gradientUnits="userSpaceOnUse">
                <stop stopColor="#A78BFA" />
                <stop offset="1" stopColor="#22D3EE" />
              </linearGradient>
            </defs>
            <circle cx="15" cy="15" r="11" stroke="url(#auth-lens)" strokeWidth="2.4" />
            <circle cx="15" cy="15" r="4.2" fill="url(#auth-lens)" />
          </svg>
          <span>NeuralLens</span>
        </div>

        <div className="auth-showcase-body">
          <div className="auth-pitch">
            <h1>See every pixel you didn&rsquo;t know you had.</h1>
            <p>
              Upscale low-resolution photos 2&times;, 4&times; or 8&times; with
              Real-ESRGAN. Drag the handle to compare.
            </p>
          </div>

          <BeforeAfterSlider
            beforeSrc={beforeImg}
            afterSrc={afterImg}
            beforeAlt="Low-resolution photo of an espresso cup, enlarged with a plain resize: soft and blurry"
            afterAlt="The same photo enhanced 4 times by NeuralLens: crisp wood grain and spoon highlights"
            beforeLabel="Original"
            beforeMeta="300×200"
            afterLabel="NeuralLens 4×"
            afterMeta="1200×800"
            width={1200}
            height={800}
          />

          <ul className="auth-chips">
            <li>
              <Maximize2 size={16} aria-hidden="true" className="chip-violet" />
              2&times; &middot; 4&times; &middot; 8&times; upscaling
            </li>
            <li>
              <Sparkles size={16} aria-hidden="true" className="chip-cyan" />
              Real-ESRGAN model
            </li>
            <li>
              <Lock size={16} aria-hidden="true" className="chip-green" />
              Your images stay private
            </li>
          </ul>
        </div>
      </div>
    </section>

    <main className="auth-panel">
      <div className="auth-panel-glow" aria-hidden="true" />
      <div className="auth-panel-inner">{children}</div>
    </main>
  </div>
);

export default AuthShell;
