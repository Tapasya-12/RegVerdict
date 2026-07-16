import { useRef, useState } from "react";

// Shared ripple-press interaction — IntakeForm's submit button and
// PolicyDiffView's Compare button both use this so the effect (and its
// timing) stays identical everywhere a primary action button appears.
export default function RippleButton({ className, onClick, disabled, children }) {
  const [ripples, setRipples] = useState([]);
  const btnRef = useRef(null);

  function handleClick(e) {
    const btn = btnRef.current;
    if (btn) {
      const rect = btn.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height) * 2;
      const id = Date.now() + Math.random();
      const ripple = {
        id,
        size,
        left: e.clientX - rect.left - size / 2,
        top: e.clientY - rect.top - size / 2,
      };
      setRipples((prev) => [...prev, ripple]);
      setTimeout(() => {
        setRipples((prev) => prev.filter((r) => r.id !== id));
      }, 650);
    }
    onClick?.(e);
  }

  return (
    <button ref={btnRef} className={className} onClick={handleClick} disabled={disabled}>
      {children}
      {ripples.map((r) => (
        <span
          key={r.id}
          className="ripple"
          style={{ width: r.size, height: r.size, left: r.left, top: r.top }}
        />
      ))}
    </button>
  );
}
