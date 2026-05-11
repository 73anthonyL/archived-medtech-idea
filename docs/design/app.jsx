// Tweak defaults + main App shell
const { useState: useSa, useEffect: useEa, useMemo: useMa } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "nav": "sidebar",
  "accentInfo": "#a78bfa",
  "heroStyle": "command",
  "markerCardStyle": "lab",
  "chartStyle": "band",
  "density": "regular",
  "tableTier": "rail"
}/*EDITMODE-END*/;

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [tab, setTab] = useSa("overview");
  const [selectedPatient, setSelectedPatient] = useSa(null);
  const data = window.STRATA_DATA;

  // initial selected patient = top risk
  useEa(() => {
    if (!selectedPatient) {
      const top = data.ADMISSIONS.slice().sort((a, b) => b.score - a.score)[0];
      setSelectedPatient(top.admissionId);
    }
  }, []);

  // Apply 4th accent CSS variable
  useEa(() => {
    document.documentElement.style.setProperty("--accent-info", t.accentInfo);
  }, [t.accentInfo]);

  const openPatient = (id) => {
    setSelectedPatient(id);
    setTab("patient");
  };

  const navItems = [
    { id: "overview", label: "Overview", icon: NavIconGrid, count: data.totals.admissions },
    { id: "patient", label: "Patient Detail", icon: NavIconUser },
    { id: "explorer", label: "Marker Explorer", icon: NavIconChart },
    { id: "about", label: "About", icon: NavIconInfo },
  ];

  return (
    <div className={`app-shell nav-${t.nav}`}>
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo"></div>
          <div>
            <div className="sidebar-wordmark">Str<span className="accent">a</span>ta</div>
            <div className="sidebar-tagline">Clinical Signal Layer</div>
          </div>
        </div>

        <div className="sidebar-section-label">Workspace</div>
        {navItems.map((n) => {
          const Icon = n.icon;
          return (
            <div key={n.id} className={`nav-item ${tab === n.id ? "active" : ""}`} onClick={() => setTab(n.id)}>
              <span className="nav-icon"><Icon /></span>
              <span>{n.label}</span>
              {n.count !== undefined && <span className="nav-count">{n.count}</span>}
            </div>
          );
        })}

        <div className="sidebar-section-label">Cohort</div>
        <CohortLegend totals={data.totals} />

        <div className="sidebar-foot">
          <div className="sidebar-demo">
            <span className="demo-dot"></span>
            <span>DEMO MODE</span>
          </div>
          <div className="sidebar-user">
            <div className="sidebar-avatar">CL</div>
            <div className="sidebar-user-info">
              <b>Dr. Chen Liu</b><br/><span>Clinical Reviewer</span>
            </div>
          </div>
        </div>
      </aside>

      {/* TOP NAV (alternative) */}
      <header className="topnav">
        <div className="topnav-brand">
          <div className="sidebar-logo"></div>
          <div className="sidebar-wordmark">Str<span className="accent">a</span>ta</div>
        </div>
        <div className="topnav-tabs">
          {navItems.map((n) => (
            <div key={n.id} className={`topnav-tab ${tab === n.id ? "active" : ""}`} onClick={() => setTab(n.id)}>{n.label}</div>
          ))}
        </div>
        <div className="topnav-spacer"></div>
        <div className="demo-mode-pill"><span className="demo-dot"></span>DEMO MODE · NOT DIAGNOSTIC</div>
      </header>

      <main className="main">
        {tab === "overview" && <OverviewTab data={data} tweaks={t} onOpenPatient={openPatient} />}
        {tab === "patient" && <PatientDetailTab data={data} tweaks={t} selectedId={selectedPatient} onSelect={setSelectedPatient} />}
        {tab === "explorer" && <MarkerExplorerTab data={data} tweaks={t} />}
        {tab === "about" && <AboutTab data={data} tweaks={t} />}
      </main>

      <TweaksPanel title="Tweaks">
        <TweakSection label="Navigation" />
        <TweakRadio label="Pattern" value={t.nav}
          options={[{ value: "sidebar", label: "Sidebar" }, { value: "rail", label: "Rail" }, { value: "top", label: "Top" }]}
          onChange={(v) => setTweak("nav", v)} />
        <TweakSection label="Color system" />
        <TweakColor label="4th accent" value={t.accentInfo}
          options={["#a78bfa", "#2dd4bf", "#22d3ee", "#f472b6"]}
          onChange={(v) => setTweak("accentInfo", v)} />
        <TweakSection label="Marker card" />
        <TweakRadio label="Style" value={t.markerCardStyle}
          options={[{ value: "lab", label: "Lab" }, { value: "sensor", label: "Sensor" }, { value: "editorial", label: "Scale" }]}
          onChange={(v) => setTweak("markerCardStyle", v)} />
        <TweakSection label="Table density" />
        <TweakRadio label="Rows" value={t.density}
          options={[{ value: "compact", label: "Compact" }, { value: "regular", label: "Regular" }, { value: "comfy", label: "Comfy" }]}
          onChange={(v) => setTweak("density", v)} />
      </TweaksPanel>
    </div>
  );
}

function CohortLegend({ totals }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, padding: "4px 12px 8px 12px" }}>
      <CohortRow color="var(--risk-high)" label="High" count={totals.high} />
      <CohortRow color="var(--risk-mod)" label="Moderate" count={totals.moderate} />
      <CohortRow color="var(--risk-low)" label="Low" count={totals.low} />
    </div>
  );
}
function CohortRow({ color, label, count }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 12.5, color: "var(--text-3)" }}>
      <span style={{ width: 8, height: 8, borderRadius: 2, background: color }}></span>
      <span>{label}</span>
      <span style={{ marginLeft: "auto", fontFamily: "JetBrains Mono, monospace", color: "var(--text-2)", fontWeight: 600 }}>{count}</span>
    </div>
  );
}

function NavIconGrid() {
  return (<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/><rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/><rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/><rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/></svg>);
}
function NavIconUser() {
  return (<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="5.5" r="2.5" stroke="currentColor" strokeWidth="1.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>);
}
function NavIconChart() {
  return (<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 12.5 L5.5 8 L8.5 10 L13.5 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><circle cx="13.5" cy="4" r="1.3" fill="currentColor"/></svg>);
}
function NavIconInfo() {
  return (<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5"/><circle cx="8" cy="5" r="0.8" fill="currentColor"/><path d="M8 7.5 L8 11.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>);
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
