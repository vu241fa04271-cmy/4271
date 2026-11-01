import { useEffect, useRef, useState } from "react";
import { Siren } from "lucide-react";

/**
 * Large SOS trigger with a press-and-hold confirmation step so it cannot be
 * fired by accident. Holding for HOLD_MS fills a progress ring; releasing
 * early cancels. On completion it calls onTrigger().
 */
const HOLD_MS = 2000;

export default function SOSButton({ onTrigger, disabled = false, sending = false }) {
  const [holding, setHolding] = useState(false);
  const [progress, setProgress] = useState(0);
  const rafRef = useRef(null);
  const startRef = useRef(0);

  const R = 56;
  const circumference = 2 * Math.PI * R;

  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  const tick = () => {
    const elapsed = performance.now() - startRef.current;
    const p = Math.min(elapsed / HOLD_MS, 1);
    setProgress(p);
    if (p >= 1) {
      setHolding(false);
      setProgress(0);
      onTrigger();
    } else {
      rafRef.current = requestAnimationFrame(tick);
    }
  };

  const startHold = (e) => {
    if (disabled || sending) return;
    e.preventDefault();
    setHolding(true);
    setProgress(0);
    startRef.current = performance.now();
    rafRef.current = requestAnimationFrame(tick);
  };

  const cancelHold = () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    setHolding(false);
    setProgress(0);
  };

  return (
    <div className="sos-wrapper">
      <div className="sos-button-wrap">
        <svg className="sos-ring" viewBox="0 0 120 120" aria-hidden="true">
          <circle
            cx="60"
            cy="60"
            r={R}
            className="sos-ring-track"
          />
          <circle
            cx="60"
            cy="60"
            r={R}
            className="sos-ring-progress"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - progress)}
            transform="rotate(-90 60 60)"
          />
        </svg>
        <button
          type="button"
          className={`sos-button ${holding ? "holding" : ""} ${sending ? "sending" : ""}`}
          onPointerDown={startHold}
          onPointerUp={cancelHold}
          onPointerLeave={cancelHold}
          onPointerCancel={cancelHold}
          disabled={disabled || sending}
          aria-label="Send emergency SOS alert"
        >
          {sending ? (
            <span className="sos-sending-label">Sending…</span>
          ) : (
            <>
              <Siren size={40} />
              <span className="sos-label">SOS</span>
            </>
          )}
        </button>
        {!holding && !sending && <span className="sos-pulse" aria-hidden="true" />}
      </div>
      <p className="sos-hint">
        {sending
          ? "Sending your emergency alert…"
          : holding
          ? "Keep holding…"
          : "Press and hold for 2 seconds to send an alert"}
      </p>
    </div>
  );
}
