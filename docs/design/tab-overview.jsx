// Tabs: Overview, Patient Detail, Marker Explorer, About
const { useState: useS, useMemo: useM, useEffect: useE, useRef: useR } = React;

// ------------ OVERVIEW ------------
function OverviewTab({ data, tweaks, onOpenPatient }) {
  const { ADMISSIONS, totals } = data;
  const [tier, setTier] = useS("all");
  const [icu, setIcu] = useS("all");
  const [admType, setAdmType] = useS("all");
  const [query, setQuery] = useS("");
  const [sortKey, setSortKey] = useS("score");
  const [sortDir, setSortDir] = useS("desc");
  const [loading, setLoading] = useS(true);

  useE(() => {
    const t = setTimeout(() => setLoading(false), 650);
    return () => clearTimeout(t);
  }, []);

  const filtered = useM(() => {
    let r = ADMISSIONS.slice();
    if (tier !== "all") r = r.filter((a) => a.tier === tier);
    if (icu !== "all") r = r.filter((a) => (icu === "yes" ? a.icu : !a.icu));
    if (admType !== "all") r = r.filter((a) => a.admType === admType);
    if (query) {
      const q = query.toLowerCase();
      r = r.filter((a) => String(a.subjectId).includes(q) || String(a.admissionId).includes(q));
    }
    r.sort((a, b) => {
      const av = a[sortKey], bv = b[sortKey];
      const cmp = typeof av === "number" ? av - bv : String(av).localeCompare(String(bv));
      return sortDir === "asc" ? cmp : -cmp;
    });
    return r;
  }, [ADMISSIONS, tier, icu, admType, query, sortKey, sortDir]);

  const heroSpark = useM(() => {
    // Aggregate "high risk count" over days
    const days = 14;
    const arr = [];
    let v = totals.high - 6;
    for (let i = 0; i < days; i++) {
      v += Math.round((Math.sin(i * 0.7) + Math.random() * 0.6) * 2);
      arr.push(Math.max(2, v));
    }
    arr[arr.length - 1] = totals.high;
    return arr;
  }, [totals.high]);

  const sortBy = (k) => {
    if (sortKey === k) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(k); setSortDir("desc"); }
  };

  const topRisk = ADMISSIONS.filter((a) => a.tier === "high").slice(0, 6);

  return (
    <div className="tab-pane">
      {/* HERO */}
      <Card accent className="hero-card">
        <div className="hero-grid">
          <div className="hero-left">
            <div className="hero-eyebrow">CLINICAL MARKER INTELLIGENCE · AKI EARLY-WARNING MODULE</div>
            <h1 className="hero-wordmark">Str<span className="hero-accent">a</span>ta</h1>
            <div className="hero-tagline">
              A clinical signal intelligence layer. Surfaces meaningful patterns across labs, vitals,
              medications, and diagnosis context from structured EHR data.
            </div>
            <div className="hero-stats">
              <HeroStat label="ADMISSIONS" value={totals.admissions} accent="neutral" spark={heroSpark.map((v, i) => v + i * 0.2)} />
              <HeroStat label="HIGH RISK" value={totals.high} accent="high" spark={heroSpark} delta="+3 24h" />
              <HeroStat label="MODERATE" value={totals.moderate} accent="moderate" spark={heroSpark.map((v) => v * 1.4 + 4)} delta="+1 24h" />
              <HeroStat label="AVG MARKERS" value={totals.avgAbnormal} accent="info" spark={heroSpark.map((v) => v * 0.6 + 3)} suffix="abnormal" />
            </div>
          </div>
          <div className="hero-right">
            <div className="demo-mode-pill">
              <span className="demo-dot"></span>
              DEMO MODE · NOT DIAGNOSTIC
            </div>
            <div className="hero-watchlist">
              <div className="hero-watchlist-label">LIVE · WATCHLIST</div>
              <div className="hero-ticker">
                <div className="hero-ticker-inner">
                  {[...topRisk, ...topRisk].map((p, i) => (
                    <div key={i} className="ticker-item">
                      <span className="ticker-id">#{p.admissionId}</span>
                      <span className="ticker-score" style={{ color: "var(--risk-high)" }}>{p.score}</span>
                      <span className="ticker-concern">{p.topConcern.slice(0, 38)}…</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="hero-clock">
              <ClockBlock />
            </div>
          </div>
        </div>
      </Card>

      {/* KPI cards */}
      <SectionLabel>OVERVIEW · KEY METRICS</SectionLabel>
      <div className="kpi-grid">
        <KpiCard label="TOTAL ADMISSIONS" value={totals.admissions} accent="neutral" sub="across active dataset" iconShape="square" />
        <KpiCard label="HIGH AKI RISK" value={totals.high} accent="high" sub={`${Math.round((totals.high / totals.admissions) * 100)}% of cohort`} delta="+3 24h" iconShape="triangle" />
        <KpiCard label="MODERATE RISK" value={totals.moderate} accent="moderate" sub={`${Math.round((totals.moderate / totals.admissions) * 100)}% of cohort`} delta="+1 24h" iconShape="diamond" />
        <KpiCard label="AVG ABNORMAL MARKERS" value={totals.avgAbnormal} accent="info" sub="per admission" iconShape="dot" />
      </div>

      {/* Filters */}
      <SectionLabel>TRIAGE FILTERS</SectionLabel>
      <Card className="filter-card">
        <div className="filter-row">
          <FilterGroup label="AKI Risk Tier">
            <SegSeg value={tier} onChange={setTier} options={[
              { v: "all", label: "All" },
              { v: "high", label: "High", color: "var(--risk-high)" },
              { v: "moderate", label: "Moderate", color: "var(--risk-mod)" },
              { v: "low", label: "Low", color: "var(--risk-low)" },
            ]} />
          </FilterGroup>
          <FilterGroup label="ICU Stay">
            <SegSeg value={icu} onChange={setIcu} options={[
              { v: "all", label: "All" }, { v: "yes", label: "ICU" }, { v: "no", label: "Non-ICU" },
            ]} />
          </FilterGroup>
          <FilterGroup label="Admission Type">
            <select className="select" value={admType} onChange={(e) => setAdmType(e.target.value)}>
              <option value="all">All types</option>
              <option value="URGENT">URGENT</option>
              <option value="EMERGENCY">EMERGENCY</option>
              <option value="ELECTIVE">ELECTIVE</option>
              <option value="OBSERVATION">OBSERVATION</option>
            </select>
          </FilterGroup>
          <FilterGroup label="Search">
            <input className="input" placeholder="Subject or admission ID…" value={query} onChange={(e) => setQuery(e.target.value)} />
          </FilterGroup>
        </div>
      </Card>

      {/* Patient table */}
      <SectionLabel action={<div className="section-action-meta">Showing {filtered.length} of {ADMISSIONS.length}</div>}>
        PATIENT ADMISSIONS · ranked by AKI risk signal
      </SectionLabel>
      <Card className="table-card">
        {loading ? (
          <div className="skeleton-rows">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="sk-row">
                <Skeleton w="80px" /><Skeleton w="80px" /><Skeleton w="36px" /><Skeleton w="60px" />
                <Skeleton w="40px" /><Skeleton w="120px" /><Skeleton w="80px" />
                <Skeleton w="40px" /><Skeleton w="40%" />
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState icon="∅" title="No admissions match your filters"
            sub="Try widening the risk tier or clearing the search." />
        ) : (
          <table className="patient-table">
            <thead>
              <tr>
                <th className="th-rail"></th>
                <Th onClick={() => sortBy("subjectId")} active={sortKey === "subjectId"} dir={sortDir}>Subject</Th>
                <Th onClick={() => sortBy("admissionId")} active={sortKey === "admissionId"} dir={sortDir}>Admission</Th>
                <Th onClick={() => sortBy("age")} active={sortKey === "age"} dir={sortDir}>Age</Th>
                <Th>Sex</Th>
                <Th>ICU</Th>
                <Th onClick={() => sortBy("score")} active={sortKey === "score"} dir={sortDir}>AKI Risk Score</Th>
                <Th>Tier</Th>
                <Th onClick={() => sortBy("abnormalCount")} active={sortKey === "abnormalCount"} dir={sortDir}>Abnormal</Th>
                <Th>Top concern</Th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.admissionId} className={`row-${p.tier} ${tweaks.density === "compact" ? "row-compact" : tweaks.density === "comfy" ? "row-comfy" : ""}`}
                    onClick={() => onOpenPatient(p.admissionId)}>
                  <td className="td-rail"><span className={`row-rail rail-${p.tier}`}></span></td>
                  <td className="mono">{p.subjectId}</td>
                  <td className="mono">{p.admissionId}</td>
                  <td>{p.age}</td>
                  <td>{p.sex}</td>
                  <td>{p.icu ? <InfoTag>ICU</InfoTag> : <span className="td-muted">—</span>}</td>
                  <td>
                    <div className="score-cell">
                      <span className="score-num" style={{ color: tierColor(p.tier) }}>{p.score}</span>
                      <div className="score-bar"><div className="score-bar-fill" style={{ width: p.score + "%", background: tierColor(p.tier) }}></div></div>
                    </div>
                  </td>
                  <td><RiskBadge tier={p.tier} /></td>
                  <td className="mono">{p.abnormalCount}</td>
                  <td className="td-concern" title={p.topConcern}>{p.topConcern}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Card className="disclaimer-card">
        <div className="disclaimer-rail"></div>
        <div className="disclaimer-body">
          <div className="disclaimer-title">DEMO ENVIRONMENT · NOT FOR CLINICAL USE</div>
          <div className="disclaimer-text">
            All data shown is de-identified demo content (MIMIC-IV Clinical Demo v2.2). Strata surfaces
            statistical signals from structured EHR data — it is not a diagnostic device and does not
            recommend treatment. Always apply clinical judgment.
          </div>
        </div>
      </Card>
    </div>
  );
}

function ClockBlock() {
  const [t, setT] = useS(new Date());
  useE(() => {
    const i = setInterval(() => setT(new Date()), 1000);
    return () => clearInterval(i);
  }, []);
  const hh = String(t.getHours()).padStart(2, "0");
  const mm = String(t.getMinutes()).padStart(2, "0");
  const ss = String(t.getSeconds()).padStart(2, "0");
  return (
    <div className="clock-block">
      <div className="clock-num mono">{hh}:{mm}<span className="clock-ss">:{ss}</span></div>
      <div className="clock-meta">SESSION · LOCAL TIME</div>
    </div>
  );
}

function tierColor(t) {
  return t === "high" ? "var(--risk-high)" : t === "moderate" ? "var(--risk-mod)" : "var(--risk-low)";
}

function HeroStat({ label, value, accent, spark, delta, suffix }) {
  const colorMap = { high: "var(--risk-high)", moderate: "var(--risk-mod)", info: "var(--accent-info)", neutral: "var(--text-1)" };
  const c = colorMap[accent] || colorMap.neutral;
  return (
    <div className="hero-stat">
      <div className="hero-stat-top">
        <div className="hero-stat-value" style={{ color: c }}>{value}</div>
        <Sparkline data={spark} w={56} h={20} color={c} />
      </div>
      <div className="hero-stat-bottom">
        <div className="hero-stat-label">{label}</div>
        {delta && <div className="hero-stat-delta">{delta}</div>}
        {suffix && <div className="hero-stat-delta">{suffix}</div>}
      </div>
    </div>
  );
}

function KpiCard({ label, value, accent, sub, delta, iconShape }) {
  const colorMap = { high: "var(--risk-high)", moderate: "var(--risk-mod)", low: "var(--risk-low)", info: "var(--accent-info)", neutral: "var(--accent-blue)" };
  const c = colorMap[accent] || colorMap.neutral;
  const shape = iconShape === "triangle" ? "▲" : iconShape === "diamond" ? "◆" : iconShape === "dot" ? "●" : "■";
  return (
    <div className={`kpi-card kpi-${accent}`}>
      <div className="kpi-stripe" style={{ background: c }}></div>
      <div className="kpi-top">
        <span className="kpi-icon" style={{ color: c }}>{shape}</span>
        <span className="kpi-label">{label}</span>
      </div>
      <div className="kpi-value" style={{ color: c }}>{value}</div>
      <div className="kpi-bottom">
        <span className="kpi-sub">{sub}</span>
        {delta && <span className="kpi-delta" style={{ color: c }}>{delta}</span>}
      </div>
    </div>
  );
}

function FilterGroup({ label, children }) {
  return (
    <div className="filter-group">
      <div className="filter-label">{label}</div>
      {children}
    </div>
  );
}

function SegSeg({ value, options, onChange }) {
  return (
    <div className="segseg">
      {options.map((o) => (
        <button
          key={o.v}
          className={`segseg-btn ${value === o.v ? "active" : ""} ${value === o.v && o.color ? `active-${o.v}` : ""}`}
          onClick={() => onChange(o.v)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

function Th({ children, onClick, active, dir }) {
  return (
    <th onClick={onClick} className={`th ${onClick ? "th-sortable" : ""} ${active ? "th-active" : ""}`}>
      {children}
      {active && <span className="th-arrow">{dir === "asc" ? "↑" : "↓"}</span>}
    </th>
  );
}

Object.assign(window, { OverviewTab });
