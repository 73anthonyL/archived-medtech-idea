// Patient Detail tab
const { useState: useSp, useMemo: useMp } = React;

function PatientDetailTab({ data, tweaks, selectedId, onSelect }) {
  const { ADMISSIONS } = data;
  const sorted = useMp(() => ADMISSIONS.slice().sort((a, b) => b.score - a.score), [ADMISSIONS]);
  const current = useMp(() => sorted.find((p) => p.admissionId === selectedId) || sorted[0], [sorted, selectedId]);
  const [chartMarker, setChartMarker] = useSp(null);

  const abnormalMarkers = current.markers.filter((m) => m.status !== "normal");
  const priorityMarkers = ["Creatinine", "BUN (Urea Nitrogen)", "Potassium", "Bicarbonate", "WBC", "Hemoglobin", "Heart Rate", "MAP"];
  const trendCharts = priorityMarkers.map((n) => current.markers.find((m) => m.name === n)).filter(Boolean);

  return (
    <div className="tab-pane">
      <SectionLabel>SELECT ADMISSION</SectionLabel>
      <Card className="admission-select-card">
        <div className="adm-select-row">
          <div className="adm-select-pre">
            <div className="adm-select-label">PATIENT ADMISSION</div>
            <div className="adm-select-meta">Sorted by AKI risk · {sorted.length} admissions</div>
          </div>
          <select className="select select-lg" value={current.admissionId} onChange={(e) => onSelect(+e.target.value)}>
            {sorted.map((p) => (
              <option key={p.admissionId} value={p.admissionId}>
                Admission {p.admissionId} · Subject {p.subjectId} · {p.tier.toUpperCase()} ({p.score}/100)
              </option>
            ))}
          </select>
          <button className="btn-prev-next" onClick={() => {
            const idx = sorted.findIndex((p) => p.admissionId === current.admissionId);
            if (idx > 0) onSelect(sorted[idx - 1].admissionId);
          }}>↑ Higher risk</button>
          <button className="btn-prev-next" onClick={() => {
            const idx = sorted.findIndex((p) => p.admissionId === current.admissionId);
            if (idx < sorted.length - 1) onSelect(sorted[idx + 1].admissionId);
          }}>↓ Lower risk</button>
        </div>
      </Card>

      {/* Header row: patient + AKI risk */}
      <div className="patient-header-grid">
        <Card accent className="patient-summary-card">
          <div className="patient-eyebrow">ADMISSION {current.admissionId}</div>
          <h2 className="patient-name">Subject {current.subjectId}</h2>
          <div className="patient-pills">
            <InfoTag>Age {current.age}</InfoTag>
            <InfoTag>{current.sex}</InfoTag>
            {current.icu && <InfoTag>ICU Admission</InfoTag>}
            <InfoTag>{current.admType}</InfoTag>
            <InfoTag>LOS {current.los} days</InfoTag>
          </div>
          <div className="mini-stat-grid">
            <MiniStat label="ABNORMAL MARKERS" value={current.abnormalCount} color="var(--accent-info)" />
            <MiniStat label="HIGH" value={current.highCount} color="var(--risk-high)" />
            <MiniStat label="LOW" value={current.lowCount} color="var(--accent-blue-2)" />
          </div>
        </Card>

        <Card className={`aki-risk-card aki-${current.tier}`}>
          <div className="aki-risk-top">
            <div>
              <div className="section-label">AKI RISK SIGNAL</div>
              <div className="aki-score-row">
                <div className="aki-score" style={{ color: tierColor(current.tier) }}>{current.score}</div>
                <div className="aki-score-frac">/ 100</div>
              </div>
              <RiskBadge tier={current.tier} size="md" />
            </div>
            <RiskDial score={current.score} tier={current.tier} />
          </div>
          <div className="aki-score-bar">
            <div className="aki-score-bar-fill" style={{ width: current.score + "%", background: tierColor(current.tier) }}></div>
            <div className="aki-score-bar-tick" style={{ left: "30%" }}></div>
            <div className="aki-score-bar-tick" style={{ left: "60%" }}></div>
          </div>
          <div className="aki-score-bar-labels">
            <span>0</span><span>Low</span><span>Moderate</span><span>High</span><span>100</span>
          </div>
          <div className="contributing-signals">
            <div className="section-label">CONTRIBUTING SIGNALS</div>
            <ul className="signals-list">
              {current.signals.map((s, i) => (
                <li key={i}>
                  <span className="signal-dot" style={{ background: tierColor(current.tier) }}></span>
                  {s}
                </li>
              ))}
            </ul>
          </div>
        </Card>
      </div>

      {/* Abnormal markers grid */}
      <SectionLabel action={<div className="section-action-meta">{abnormalMarkers.length} flagged · {current.markers.length - abnormalMarkers.length} within range</div>}>
        ABNORMAL MARKERS
      </SectionLabel>
      {abnormalMarkers.length === 0 ? (
        <Card>
          <EmptyState icon="✓" title="All markers within reference range"
            sub="No abnormal labs or vitals identified for this admission." />
        </Card>
      ) : (
        <div className="marker-grid">
          {abnormalMarkers.map((m) => <MarkerCard key={m.name} marker={m} style={tweaks.markerCardStyle} />)}
        </div>
      )}

      {/* Trend charts */}
      <SectionLabel>TREND VIEW · PRIORITY MARKERS</SectionLabel>
      <div className="trend-grid">
        {trendCharts.map((m) => (
          <Card key={m.name} className="trend-card">
            <div className="trend-card-header">
              <div className="trend-card-title">
                <span>{m.name}</span>
                {m.aki && <AkiTag />}
              </div>
              <div className="trend-card-meta">
                <span className="mono trend-value" style={{ color: m.status === "high" ? "var(--risk-high)" : m.status === "low" ? "var(--accent-blue-2)" : "var(--risk-low)" }}>
                  {m.latest}
                </span>
                <span className="trend-unit">{m.unit}</span>
                <StatusPill status={m.status} />
              </div>
            </div>
            <TrendChart marker={m} height={160} showAxis={true} />
          </Card>
        ))}
      </div>
    </div>
  );
}

function RiskDial({ score, tier }) {
  const c = tierColor(tier);
  const r = 36, cx = 44, cy = 44;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - score / 100);
  return (
    <svg width="88" height="88" className="risk-dial">
      <circle cx={cx} cy={cy} r={r} stroke="rgba(148,163,184,0.12)" strokeWidth="6" fill="none" />
      <circle cx={cx} cy={cy} r={r} stroke={c} strokeWidth="6" fill="none"
        strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`} />
      <text x={cx} y={cy + 4} textAnchor="middle" fontSize="20" fontWeight="700" fill={c} fontFamily="ui-monospace,SF Mono,Menlo,monospace">{score}</text>
    </svg>
  );
}

function MiniStat({ label, value, color }) {
  return (
    <div className="mini-stat">
      <div className="mini-stat-label">{label}</div>
      <div className="mini-stat-value" style={{ color }}>{value}</div>
    </div>
  );
}

function MarkerCard({ marker, style }) {
  const tone = marker.status === "high" ? "high" : marker.status === "low" ? "low" : "normal";
  const c = marker.status === "high" ? "var(--risk-high)" : marker.status === "low" ? "var(--accent-blue-2)" : "var(--risk-low)";
  const delta = marker.latest - marker.series[0];
  const deltaSign = delta >= 0 ? "+" : "";

  // Position on reference scale
  const span = (marker.high - marker.low) * 2.5;
  const start = marker.low - (marker.high - marker.low) * 0.75;
  const pos = Math.max(0, Math.min(100, ((marker.latest - start) / span) * 100));
  const lowPos = ((marker.low - start) / span) * 100;
  const highPos = ((marker.high - start) / span) * 100;

  if (style === "sensor") {
    return (
      <Card className={`marker-card marker-${tone} marker-style-sensor`}>
        <div className={`marker-rail rail-${tone}`}></div>
        <div className="marker-card-head">
          <div className="marker-name">{marker.name}</div>
          <StatusPill status={marker.status} />
        </div>
        <div className="marker-value-row">
          <div className="marker-value mono" style={{ color: c }}>{marker.latest}<span className="marker-unit">{marker.unit}</span></div>
          <Sparkline data={marker.series} w={100} h={32} color={c} />
        </div>
        <div className="marker-delta-row">
          <span className="marker-ref mono">REF {marker.low}–{marker.high}</span>
          <span className="marker-delta mono" style={{ color: c }}>{deltaSign}{delta.toFixed(2)} Δ</span>
        </div>
        {marker.aki && <AkiTag />}
        <div className="marker-explain">{marker.explain}</div>
      </Card>
    );
  }

  if (style === "editorial") {
    return (
      <Card className={`marker-card marker-${tone} marker-style-editorial`}>
        <div className={`marker-rail rail-${tone}`}></div>
        <div className="marker-card-head">
          <div className="marker-name">{marker.name}</div>
          <StatusPill status={marker.status} />
        </div>
        <div className="marker-value-xl mono" style={{ color: c }}>
          {marker.latest}<span className="marker-unit-sm">{marker.unit}</span>
        </div>
        <div className="ref-scale">
          <div className="ref-scale-track">
            <div className="ref-scale-band" style={{ left: lowPos + "%", width: (highPos - lowPos) + "%" }}></div>
            <div className="ref-scale-marker" style={{ left: pos + "%", background: c, boxShadow: `0 0 0 3px ${tone === "high" ? "rgba(248,113,113,0.22)" : tone === "low" ? "rgba(56,189,248,0.22)" : "rgba(74,222,128,0.22)"}` }}></div>
          </div>
          <div className="ref-scale-labels mono">
            <span>{marker.low}</span><span>REF</span><span>{marker.high}</span>
          </div>
        </div>
        {marker.aki && <AkiTag />}
        <div className="marker-explain">{marker.explain}</div>
      </Card>
    );
  }

  // default: lab-result inspired
  return (
    <Card className={`marker-card marker-${tone}`}>
      <div className={`marker-rail rail-${tone}`}></div>
      <div className="marker-card-head">
        <div className="marker-name">{marker.name}</div>
        <StatusPill status={marker.status} />
      </div>
      <div className="marker-value mono" style={{ color: c }}>
        {marker.latest}<span className="marker-unit">{marker.unit}</span>
      </div>
      <div className="marker-ref mono">Ref {marker.low}–{marker.high} {marker.unit}</div>
      {marker.aki && <AkiTag />}
      <div className="marker-explain">{marker.explain}</div>
    </Card>
  );
}

Object.assign(window, { PatientDetailTab, MarkerCard });
