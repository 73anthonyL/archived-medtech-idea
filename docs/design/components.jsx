// Shared UI components
const { useState, useEffect, useMemo, useRef } = React;

// Risk badge
function RiskBadge({ tier, size = "sm" }) {
  const map = {
    high: { label: "HIGH", color: "var(--risk-high)", bg: "rgba(248,113,113,0.12)", border: "rgba(248,113,113,0.35)" },
    moderate: { label: "MODERATE", color: "var(--risk-mod)", bg: "rgba(251,191,36,0.10)", border: "rgba(251,191,36,0.35)" },
    low: { label: "LOW", color: "var(--risk-low)", bg: "rgba(74,222,128,0.10)", border: "rgba(74,222,128,0.30)" },
  };
  const s = map[tier] || map.low;
  return (
    <span className={`risk-badge size-${size}`} style={{ color: s.color, background: s.bg, borderColor: s.border }}>
      <span className="risk-dot" style={{ background: s.color }}></span>
      {s.label}
    </span>
  );
}

function StatusPill({ status }) {
  if (status === "normal") {
    return <span className="status-pill normal">NORMAL</span>;
  }
  return <span className={`status-pill ${status}`}>{status.toUpperCase()}</span>;
}

function AkiTag() {
  return <span className="aki-tag">AKI-RELEVANT</span>;
}

function InfoTag({ children }) {
  return <span className="info-tag">{children}</span>;
}

// Mini sparkline (SVG)
function Sparkline({ data, w = 80, h = 24, color = "var(--accent-blue)", showFill = true }) {
  if (!data || data.length === 0) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pad = 2;
  const points = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (w - pad * 2);
    const y = pad + (1 - (v - min) / range) * (h - pad * 2);
    return [x, y];
  });
  const path = points.map((p, i) => (i === 0 ? `M${p[0]},${p[1]}` : `L${p[0]},${p[1]}`)).join(" ");
  const fillPath = `${path} L${points[points.length - 1][0]},${h - pad} L${points[0][0]},${h - pad} Z`;
  return (
    <svg width={w} height={h} className="sparkline">
      {showFill && <path d={fillPath} fill={color} opacity="0.15" />}
      <path d={path} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

// Full trend chart with shaded normal band
function TrendChart({ marker, height = 220, showAxis = true }) {
  const wrapRef = useRef(null);
  const [w, setW] = useState(600);
  useEffect(() => {
    if (!wrapRef.current) return;
    const ro = new ResizeObserver((entries) => {
      for (const e of entries) setW(e.contentRect.width);
    });
    ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  const [hover, setHover] = useState(null);

  if (!marker) return <div ref={wrapRef} className="trend-chart-empty">No marker selected</div>;
  const data = marker.series;
  const padL = 44, padR = 16, padT = 16, padB = 30;
  const innerW = Math.max(100, w - padL - padR);
  const innerH = height - padT - padB;
  const lo = marker.low, hi = marker.high;
  const dataMin = Math.min(...data, lo);
  const dataMax = Math.max(...data, hi);
  const span = dataMax - dataMin || 1;
  const yMin = dataMin - span * 0.15;
  const yMax = dataMax + span * 0.15;
  const yRange = yMax - yMin;

  const x = (i) => padL + (i / (data.length - 1)) * innerW;
  const y = (v) => padT + (1 - (v - yMin) / yRange) * innerH;

  const pts = data.map((v, i) => [x(i), y(v)]);
  const path = pts.map((p, i) => (i === 0 ? `M${p[0]},${p[1]}` : `L${p[0]},${p[1]}`)).join(" ");
  const fillPath = `${path} L${pts[pts.length - 1][0]},${padT + innerH} L${pts[0][0]},${padT + innerH} Z`;

  const bandTop = y(hi);
  const bandBot = y(lo);

  // Y ticks
  const yTicks = 4;
  const ticks = [];
  for (let i = 0; i <= yTicks; i++) {
    const v = yMin + (i / yTicks) * yRange;
    ticks.push({ v: +v.toFixed(marker.high < 5 ? 2 : 1), y: y(v) });
  }

  const handleMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const idx = Math.round(((mx - padL) / innerW) * (data.length - 1));
    if (idx >= 0 && idx < data.length) setHover(idx);
    else setHover(null);
  };

  return (
    <div ref={wrapRef} className="trend-chart-wrap">
      <svg width={w} height={height} onMouseMove={handleMove} onMouseLeave={() => setHover(null)}>
        <defs>
          <linearGradient id={`g-${marker.name.replace(/\W/g, "")}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent-blue)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--accent-blue)" stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* Normal range band */}
        <rect x={padL} y={Math.min(bandTop, bandBot)} width={innerW} height={Math.abs(bandBot - bandTop)}
              fill="rgba(74,222,128,0.07)" stroke="rgba(74,222,128,0.20)" strokeDasharray="3 3" strokeWidth="1" />
        {/* Grid */}
        {ticks.map((t, i) => (
          <line key={i} x1={padL} x2={padL + innerW} y1={t.y} y2={t.y} stroke="rgba(148,163,184,0.08)" />
        ))}
        {/* Y axis labels */}
        {showAxis && ticks.map((t, i) => (
          <text key={i} x={padL - 8} y={t.y + 4} textAnchor="end" fill="rgba(148,163,184,0.6)" fontSize="10" fontFamily="ui-monospace, SF Mono, Menlo, monospace">{t.v}</text>
        ))}
        {/* Normal range labels */}
        <text x={padL + innerW - 4} y={bandTop - 4} textAnchor="end" fill="rgba(74,222,128,0.55)" fontSize="9.5" fontFamily="ui-monospace, SF Mono, Menlo, monospace">REF {lo}–{hi}</text>
        {/* Area */}
        <path d={fillPath} fill={`url(#g-${marker.name.replace(/\W/g, "")})`} />
        {/* Line */}
        <path d={path} fill="none" stroke="var(--accent-blue)" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
        {/* Points */}
        {pts.map((p, i) => {
          const s = data[i] > hi ? "var(--risk-high)" : data[i] < lo ? "var(--accent-blue-2)" : "var(--accent-blue)";
          const oor = data[i] > hi || data[i] < lo;
          return <circle key={i} cx={p[0]} cy={p[1]} r={oor ? 3.2 : 2.4} fill={s} stroke="var(--bg)" strokeWidth="1" />;
        })}
        {/* X axis labels */}
        {showAxis && data.map((_, i) => (
          i % 3 === 0 && <text key={i} x={x(i)} y={padT + innerH + 16} textAnchor="middle" fill="rgba(148,163,184,0.5)" fontSize="10" fontFamily="ui-monospace, SF Mono, Menlo, monospace">D{i + 1}</text>
        ))}
        {/* Hover */}
        {hover !== null && (
          <g>
            <line x1={x(hover)} x2={x(hover)} y1={padT} y2={padT + innerH} stroke="rgba(56,189,248,0.4)" strokeDasharray="2 2" />
            <circle cx={x(hover)} cy={y(data[hover])} r="5" fill="var(--accent-blue)" stroke="var(--bg)" strokeWidth="2" />
          </g>
        )}
        {/* Unit label */}
        {showAxis && <text x={12} y={padT + 4} fill="rgba(148,163,184,0.55)" fontSize="10" fontFamily="ui-monospace, SF Mono, Menlo, monospace">{marker.unit}</text>}
      </svg>
      {hover !== null && (() => {
        const v = data[hover];
        const out = v > hi ? "high" : v < lo ? "low" : "in range";
        const color = out === "high" ? "var(--risk-high)" : out === "low" ? "var(--accent-blue-2)" : "var(--risk-low)";
        const px = x(hover);
        const left = Math.min(Math.max(px - 80, 8), w - 168);
        return (
          <div className="chart-tooltip" style={{ left, top: 8 }}>
            <div className="tt-row"><span className="tt-label">Day {hover + 1}</span></div>
            <div className="tt-row"><span className="tt-value">{v}</span><span className="tt-unit">{marker.unit}</span></div>
            <div className="tt-row tt-meta" style={{ color }}>● {out} (ref {lo}–{hi})</div>
          </div>
        );
      })()}
    </div>
  );
}

// Card chrome
function Card({ children, accent, className = "", style = {} }) {
  return (
    <div className={`card ${accent ? "card-accent" : ""} ${className}`} style={style}>
      {accent && <div className="card-stripe"></div>}
      {children}
    </div>
  );
}

// Section header (small caps)
function SectionLabel({ children, action }) {
  return (
    <div className="section-label-row">
      <div className="section-label">{children}</div>
      {action}
    </div>
  );
}

// Empty state
function EmptyState({ icon = "◇", title, sub }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon}</div>
      <div className="empty-title">{title}</div>
      {sub && <div className="empty-sub">{sub}</div>}
    </div>
  );
}

// Skeleton row
function Skeleton({ w = "100%", h = 14, r = 4, style = {} }) {
  return <div className="skeleton" style={{ width: w, height: h, borderRadius: r, ...style }}></div>;
}

Object.assign(window, { RiskBadge, StatusPill, AkiTag, InfoTag, Sparkline, TrendChart, Card, SectionLabel, EmptyState, Skeleton });
