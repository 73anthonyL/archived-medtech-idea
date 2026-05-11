// Marker Explorer + About tabs

function MarkerExplorerTab({ data, tweaks }) {
  const { ADMISSIONS } = data;
  const sorted = React.useMemo(() => ADMISSIONS.slice().sort((a, b) => b.score - a.score), [ADMISSIONS]);
  const [selId, setSelId] = React.useState(sorted[0].admissionId);
  const current = sorted.find((p) => p.admissionId === selId) || sorted[0];
  const [query, setQuery] = React.useState("");
  const [abnOnly, setAbnOnly] = React.useState(false);
  const [cat, setCat] = React.useState("all");
  const [selectedMarker, setSelectedMarker] = React.useState(current.markers[0].name);

  const cats = ["all", "renal", "hemodynamic", "metabolic", "hematology"];
  const rows = current.markers.filter((m) => {
    if (abnOnly && m.status === "normal") return false;
    if (cat !== "all" && m.cat !== cat) return false;
    if (query && !m.name.toLowerCase().includes(query.toLowerCase())) return false;
    return true;
  });

  const focus = current.markers.find((m) => m.name === selectedMarker) || rows[0] || current.markers[0];

  return (
    <div className="tab-pane">
      <SectionLabel>EXPLORE CLINICAL MARKERS</SectionLabel>
      <Card className="filter-card">
        <div className="filter-row">
          <FilterGroup label="Search marker name">
            <input className="input" placeholder="e.g. Creatinine, WBC, Potassium…" value={query} onChange={(e) => setQuery(e.target.value)} />
          </FilterGroup>
          <FilterGroup label="Category">
            <select className="select" value={cat} onChange={(e) => setCat(e.target.value)}>
              {cats.map((c) => <option key={c} value={c}>{c[0].toUpperCase() + c.slice(1)}</option>)}
            </select>
          </FilterGroup>
          <FilterGroup label="Patient admission">
            <select className="select" value={selId} onChange={(e) => setSelId(+e.target.value)}>
              {sorted.map((p) => (
                <option key={p.admissionId} value={p.admissionId}>
                  Adm {p.admissionId} · {p.tier.toUpperCase()} ({p.score})
                </option>
              ))}
            </select>
          </FilterGroup>
          <FilterGroup label="View">
            <label className="checkbox-row">
              <input type="checkbox" checked={abnOnly} onChange={(e) => setAbnOnly(e.target.checked)} />
              <span>Abnormal only</span>
            </label>
          </FilterGroup>
        </div>
      </Card>

      <SectionLabel action={<div className="section-action-meta">{rows.length} markers · click a row to view trend</div>}>
        MARKERS · ADMISSION {current.admissionId}
      </SectionLabel>
      <Card className="table-card">
        {rows.length === 0 ? (
          <EmptyState icon="∅" title="No markers match your filters" sub="Try clearing search or category." />
        ) : (
          <table className="explorer-table">
            <thead>
              <tr>
                <th className="th-rail"></th>
                <th>Marker</th><th>Category</th><th>Latest</th><th>Min</th><th>Max</th><th>Mean</th><th>Unit</th><th>Status</th><th>AKI</th><th>Trend</th><th>Explanation</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((m) => (
                <tr key={m.name} className={`row-${m.status === "high" ? "high" : m.status === "low" ? "info" : "normal"} ${selectedMarker === m.name ? "row-selected" : ""}`}
                    onClick={() => setSelectedMarker(m.name)}>
                  <td className="td-rail"><span className={`row-rail rail-${m.status === "high" ? "high" : m.status === "low" ? "info" : "normal"}`}></span></td>
                  <td className="cell-strong">{m.name}</td>
                  <td><InfoTag>{m.cat}</InfoTag></td>
                  <td className="mono cell-latest" style={{ color: m.status === "high" ? "var(--risk-high)" : m.status === "low" ? "var(--accent-blue-2)" : "var(--text-1)" }}>{m.latest}</td>
                  <td className="mono">{m.min}</td>
                  <td className="mono">{m.max}</td>
                  <td className="mono">{m.mean}</td>
                  <td className="mono td-muted">{m.unit}</td>
                  <td><StatusPill status={m.status} /></td>
                  <td>{m.aki ? <AkiTag /> : <span className="td-muted">—</span>}</td>
                  <td><Sparkline data={m.series} w={70} h={20} color={m.status === "high" ? "var(--risk-high)" : m.status === "low" ? "var(--accent-blue-2)" : "var(--accent-blue)"} /></td>
                  <td className="cell-explain">{m.explain}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <SectionLabel>TREND DETAIL · {focus.name}</SectionLabel>
      <Card className="trend-card-lg">
        <div className="trend-card-header">
          <div className="trend-card-title">
            <span>{focus.name}</span>
            {focus.aki && <AkiTag />}
            <InfoTag>{focus.cat}</InfoTag>
          </div>
          <div className="trend-card-meta">
            <span className="mono trend-value" style={{ color: focus.status === "high" ? "var(--risk-high)" : focus.status === "low" ? "var(--accent-blue-2)" : "var(--risk-low)" }}>
              {focus.latest}
            </span>
            <span className="trend-unit">{focus.unit}</span>
            <StatusPill status={focus.status} />
          </div>
        </div>
        <TrendChart marker={focus} height={280} showAxis={true} />
        <div className="trend-explain">
          <div className="trend-explain-label">CLINICAL CONTEXT</div>
          <div className="trend-explain-text">{focus.explain}</div>
        </div>
      </Card>
    </div>
  );
}

function AboutTab({ data, tweaks }) {
  const signalsArch = [
    { name: "Creatinine elevation", pts: 25, why: "Direct marker of reduced GFR" },
    { name: "BUN elevation", pts: 15, why: "Renal clearance dysfunction" },
    { name: "Urine output (oliguria)", pts: 15, why: "Direct AKI KDIGO criterion" },
    { name: "MAP / BP signal", pts: 10, why: "Renal perfusion adequacy" },
    { name: "Bicarbonate / acidosis", pts: 10, why: "Acid-base homeostasis loss" },
    { name: "Potassium derangement", pts: 8, why: "Renal excretion impairment" },
    { name: "Lactate", pts: 7, why: "Tissue hypoperfusion signal" },
    { name: "Hemoglobin / anemia", pts: 5, why: "CKD comorbidity context" },
    { name: "Diagnosis history (CKD/DM/HTN)", pts: 5, why: "Baseline risk context" },
  ];
  return (
    <div className="tab-pane about-tab">
      <Card accent className="about-hero">
        <div className="about-eyebrow">ABOUT</div>
        <h1 className="hero-wordmark">Str<span className="hero-accent">a</span>ta</h1>
        <div className="about-lede">
          A clinical signal intelligence layer built to surface AKI early-warning patterns from
          structured EHR data. Strata weighs labs, vitals, diagnosis history, and trend dynamics
          into a single triage signal — designed for clinical review, not autonomous decisions.
        </div>
      </Card>

      <SectionLabel>RISK SCORE ARCHITECTURE</SectionLabel>
      <Card>
        <table className="arch-table">
          <thead>
            <tr><th>Signal</th><th>Max points</th><th>Why it matters</th></tr>
          </thead>
          <tbody>
            {signalsArch.map((s) => (
              <tr key={s.name}>
                <td className="cell-strong">{s.name}</td>
                <td className="mono">{s.pts}</td>
                <td>{s.why}</td>
              </tr>
            ))}
            <tr className="row-total">
              <td className="cell-strong">Maximum risk score</td>
              <td className="mono"><b>100</b></td>
              <td>Composite — capped, not summed beyond ceiling</td>
            </tr>
          </tbody>
        </table>
      </Card>

      <SectionLabel>RISK TIERS</SectionLabel>
      <div className="tier-grid">
        <TierCard tier="low" range="0–29" title="Low signal">
          Markers largely within reference range. Routine clinical review at standard cadence.
        </TierCard>
        <TierCard tier="moderate" range="30–59" title="Moderate signal">
          Multiple abnormal markers or single high-weight signal. Consider closer monitoring.
        </TierCard>
        <TierCard tier="high" range="60–100" title="High signal">
          Strong AKI-relevant pattern across labs and perfusion. Warrants prompt clinical review.
        </TierCard>
      </div>

      <SectionLabel>DATA SOURCE</SectionLabel>
      <Card>
        <div className="data-source">
          <div className="data-source-line"><span className="data-source-key">SOURCE</span><span>MIMIC-IV Clinical Demo v2.2</span></div>
          <div className="data-source-line"><span className="data-source-key">VERSION</span><span className="mono">v2.2 · {data.totals.admissions} de-identified admissions</span></div>
          <div className="data-source-line"><span className="data-source-key">UPDATED</span><span className="mono">2026-05-11 · 14:02 UTC</span></div>
          <div className="data-source-line"><span className="data-source-key">CITATION</span><span>Johnson, A., et al. MIMIC-IV (PhysioNet)</span></div>
        </div>
      </Card>

      <Card className="disclaimer-card">
        <div className="disclaimer-rail"></div>
        <div className="disclaimer-body">
          <div className="disclaimer-title">FULL DISCLAIMER</div>
          <div className="disclaimer-text">
            Strata is a demonstration of statistical signal surfacing on structured EHR data. It is
            not a medical device, is not FDA-cleared, and does not provide diagnosis, treatment
            recommendations, or clinical decision support. All patient identifiers shown are
            de-identified demo data. The intelligence layer is intended to support, never replace,
            clinical judgment.
          </div>
        </div>
      </Card>
    </div>
  );
}

function TierCard({ tier, range, title, children }) {
  const c = tier === "high" ? "var(--risk-high)" : tier === "moderate" ? "var(--risk-mod)" : "var(--risk-low)";
  return (
    <div className={`tier-card tier-${tier}`}>
      <div className="tier-card-stripe" style={{ background: c }}></div>
      <div className="tier-card-head">
        <RiskBadge tier={tier} size="md" />
        <span className="tier-range mono">{range}</span>
      </div>
      <div className="tier-card-title" style={{ color: c }}>{title}</div>
      <div className="tier-card-body">{children}</div>
    </div>
  );
}

Object.assign(window, { MarkerExplorerTab, AboutTab });
