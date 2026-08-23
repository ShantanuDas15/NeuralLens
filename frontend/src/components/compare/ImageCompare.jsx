import { useState, useRef, useEffect, useCallback } from 'react';
import { Download, RefreshCw } from 'lucide-react';
import Button from '../ui/Button';
import './ImageCompare.css';

const ImageCompare = ({ result, onReset }) => {
  const [sliderPos, setSliderPos] = useState(50);
  const containerRef = useRef(null);
  
  // Keep stable reference to latest handleDrag logic without changing function identity
  const handleDragRef = useRef(null);

  handleDragRef.current = (e) => {
    if (!containerRef.current) return;
    
    // Get mouse or touch position
    const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
    const rect = containerRef.current.getBoundingClientRect();
    
    // Calculate percentage
    let pos = ((clientX - rect.left) / rect.width) * 100;
    
    // Clamp between 0 and 100
    pos = Math.max(0, Math.min(pos, 100));
    setSliderPos(pos);
  };

  const handleDragStable = useCallback((e) => {
    handleDragRef.current?.(e);
  }, []);

  const handleKeyDown = (e) => {
    let newPos = sliderPos;
    if (e.key === 'ArrowLeft') {
      newPos -= 5;
    } else if (e.key === 'ArrowRight') {
      newPos += 5;
    }
    
    if (newPos !== sliderPos) {
      e.preventDefault();
      setSliderPos(Math.max(0, Math.min(newPos, 100)));
    }
  };

  const stopDragRef = useRef(null);
  stopDragRef.current = () => {
    window.removeEventListener('mousemove', handleDragStable);
    window.removeEventListener('touchmove', handleDragStable);
    window.removeEventListener('mouseup', stopDragRef.current);
    window.removeEventListener('touchend', stopDragRef.current);
  };

  const startDrag = (e) => {
    handleDragStable(e);
    window.addEventListener('mousemove', handleDragStable);
    window.addEventListener('touchmove', handleDragStable, { passive: false });
    window.addEventListener('mouseup', stopDragRef.current);
    window.addEventListener('touchend', stopDragRef.current);
  };

  useEffect(() => {
    // Cleanup listeners on unmount
    return () => {
      stopDragRef.current?.();
    };
  }, []);

  const handleDownload = async () => {
    try {
      const response = await fetch(result.result_url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `neurallens-enhanced-${result.job_id}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      if (import.meta.env.DEV) console.error("Download failed:", err);
    }
  };

  return (
    <div className="image-compare-wrapper page-enter">
      <div 
        className="image-compare-container" 
        ref={containerRef}
        onMouseDown={startDrag}
        onTouchStart={startDrag}
      >
        {/* Right Image (Enhanced) - Base layer */}
        <img 
          src={result.result_url} 
          alt="Enhanced" 
          className="compare-img compare-enhanced" 
          draggable="false"
        />
        
        {/* Left Image (Original) - Clipped top layer */}
        <div 
          className="compare-clip-container"
          style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
        >
          <img 
            src={result.original_url} 
            alt="Original" 
            className="compare-img compare-original" 
            draggable="false"
          />
        </div>

        {/* Slider Handle */}
        <div 
          className="compare-slider" 
          style={{ left: `${sliderPos}%` }}
          role="slider"
          aria-valuenow={Math.round(sliderPos)}
          aria-valuemin="0"
          aria-valuemax="100"
          aria-label="Image comparison slider"
          tabIndex={0}
          onKeyDown={handleKeyDown}
        >
          <div className="compare-slider-handle">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 18l-4-4 4-4M13 6l4 4-4 4" />
            </svg>
          </div>
        </div>

        {/* Labels */}
        <div className="compare-label label-left">Original</div>
        <div className="compare-label label-right">Enhanced 4x</div>
      </div>

      <div className="compare-metadata">
        <span>{result.input_w}x{result.input_h} → {result.output_w}x{result.output_h}</span>
        <span className="metadata-dot">•</span>
        <span>{result.processing_time_ms}ms</span>
      </div>

      <div className="compare-actions">
        <Button variant="ghost" onClick={onReset} className="action-btn">
          <RefreshCw size={18} className="mr-2" />
          Enhance Another
        </Button>
        <Button variant="primary" onClick={handleDownload} className="action-btn">
          <Download size={18} className="mr-2" />
          Download Enhanced
        </Button>
      </div>
    </div>
  );
};

export default ImageCompare;
