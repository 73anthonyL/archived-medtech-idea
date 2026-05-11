// Mock clinical data for Strata demo
(function () {
  const rng = mulberry32(20260511);
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const rand = (min, max) => min + rng() * (max - min);
  const ri = (min, max) => Math.floor(rand(min, max + 1));
  const pick = (arr) => arr[Math.floor(rng() * arr.length)];

  // Markers catalog
  const MARKER_DEFS = [
    { name: "Creatinine", cat: "renal", unit: "mg/dL", low: 0.5, high: 1.2, aki: true, explain: "Elevated creatinine may suggest reduced kidney filtration (GFR). A rising trend across multiple draws can be associated with AKI — requires clinical context and serial review." },
    { name: "BUN (Urea Nitrogen)", cat: "renal", unit: "mg/dL", low: 7, high: 25, aki: true, explain: "Elevated BUN may suggest impaired urea clearance, which can be associated with reduced kidney function or high protein catabolism. In combination with elevated creatinine, it may reinforce an AKI risk signal." },
    { name: "Bicarbonate", cat: "renal", unit: "mEq/L", low: 22, high: 29, aki: true, explain: "Low bicarbonate may suggest metabolic acidosis. In the context of possible kidney stress, this can be associated with a reduced ability to excrete acid — an early-warning signal worth clinical review." },
    { name: "Potassium", cat: "renal", unit: "mEq/L", low: 3.5, high: 5.0, aki: true, explain: "Abnormal potassium may reflect impaired renal excretion. Hyperkalemia in the setting of AKI warrants prompt clinical review." },
    { name: "Sodium", cat: "metabolic", unit: "mEq/L", low: 135, high: 145, aki: false, explain: "Sodium imbalance may reflect fluid status or hormonal regulation issues." },
    { name: "Chloride", cat: "metabolic", unit: "mEq/L", low: 96, high: 106, aki: false, explain: "Low chloride may accompany metabolic alkalosis or significant GI losses. Requires clinical context." },
    { name: "Glucose", cat: "metabolic", unit: "mg/dL", low: 70, high: 140, aki: false, explain: "High glucose (hyperglycemia) is common in critically ill patients and in those with diabetes. Persistent hyperglycemia warrants review." },
    { name: "Albumin", cat: "metabolic", unit: "g/dL", low: 3.5, high: 5.0, aki: false, explain: "Low albumin (hypoalbuminemia) can be associated with malnutrition, liver disease, or protein loss." },
    { name: "Bilirubin (Total)", cat: "metabolic", unit: "mg/dL", low: 0.2, high: 1.2, aki: false, explain: "Elevated bilirubin may suggest liver dysfunction or hemolysis. Hepatorenal interactions may be relevant." },
    { name: "Lactate", cat: "metabolic", unit: "mmol/L", low: 0.5, high: 2.0, aki: true, explain: "Elevated lactate may suggest tissue hypoperfusion or anaerobic metabolism. In the context of possible sepsis or circulatory compromise, it can be associated with organ — including kidney — stress." },
    { name: "WBC", cat: "hematology", unit: "K/uL", low: 4.5, high: 11.0, aki: false, explain: "Elevated WBC may reflect infection or inflammation; low values may suggest immunosuppression." },
    { name: "Hemoglobin", cat: "hematology", unit: "g/dL", low: 12, high: 17.5, aki: true, explain: "Low hemoglobin (anemia) is common in CKD and may be associated with AKI due to reduced erythropoietin production." },
    { name: "Platelets", cat: "hematology", unit: "K/uL", low: 150, high: 400, aki: false, explain: "Low platelets may reflect consumption, suppression, or sequestration." },
    { name: "Heart Rate", cat: "hemodynamic", unit: "bpm", low: 60, high: 100, aki: true, explain: "Abnormal heart rate may reflect cardiac conduction issues, volume status, or medication effect and warrants clinical context." },
    { name: "Systolic BP", cat: "hemodynamic", unit: "mmHg", low: 90, high: 140, aki: true, explain: "Low systolic BP can reduce renal perfusion; sustained hypotension is an AKI risk factor." },
    { name: "Diastolic BP", cat: "hemodynamic", unit: "mmHg", low: 60, high: 90, aki: false, explain: "Low diastolic BP can accompany distributive states, possibly reducing renal perfusion." },
    { name: "MAP", cat: "hemodynamic", unit: "mmHg", low: 65, high: 100, aki: true, explain: "Mean arterial pressure below 65 mmHg is associated with reduced organ perfusion and AKI risk." },
    { name: "Respiratory Rate", cat: "hemodynamic", unit: "/min", low: 12, high: 20, aki: false, explain: "Abnormal respiratory rate may reflect acid-base disturbance or respiratory compromise." },
    { name: "SpO2", cat: "hemodynamic", unit: "%", low: 92, high: 100, aki: false, explain: "Low SpO2 may reflect hypoxemia and respiratory compromise." },
    { name: "Temperature", cat: "hemodynamic", unit: "°C", low: 36.0, high: 37.8, aki: false, explain: "Fever may reflect infection; hypothermia may accompany sepsis." },
    { name: "INR", cat: "hematology", unit: "", low: 0.8, high: 1.2, aki: false, explain: "Elevated INR may reflect anticoagulation or coagulopathy." },
    { name: "Urine Output", cat: "renal", unit: "mL/hr", low: 30, high: 100, aki: true, explain: "Low urine output (oliguria) is a direct AKI criterion — sustained values below 0.5 mL/kg/hr warrant urgent review." },
    { name: "AST", cat: "metabolic", unit: "U/L", low: 10, high: 40, aki: false, explain: "Elevated AST may reflect hepatocellular injury." },
    { name: "ALT", cat: "metabolic", unit: "U/L", low: 7, high: 56, aki: false, explain: "Elevated ALT may reflect hepatocellular injury." },
  ];

  // Generate trend series for a marker
  function genTrend(def, abnormalDirection) {
    const n = 14;
    const mid = (def.low + def.high) / 2;
    const span = def.high - def.low;
    const out = [];
    let val;
    if (abnormalDirection === "high") val = mid + span * 0.2;
    else if (abnormalDirection === "low") val = mid - span * 0.2;
    else val = mid;
    for (let i = 0; i < n; i++) {
      const drift = abnormalDirection === "high" ? span * 0.12 : abnormalDirection === "low" ? -span * 0.12 : 0;
      const noise = (rng() - 0.5) * span * 0.18;
      val = val + drift * 0.5 + noise;
      // clamp negative
      if (def.unit !== "°C" && val < 0) val = Math.abs(val);
      out.push(+val.toFixed(def.unit === "" || def.high < 5 ? 2 : 1));
    }
    return out;
  }

  function statusOf(def, value) {
    if (value > def.high) return "high";
    if (value < def.low) return "low";
    return "normal";
  }

  const ADMISSION_TYPES = ["URGENT", "EMERGENCY", "ELECTIVE", "OBSERVATION"];
  const SEX = ["Male", "Female"];

  // Generate 32 patient admissions
  const ADMISSIONS = [];
  for (let i = 0; i < 32; i++) {
    const subjectId = 10000000 + ri(1000, 999999);
    const admissionId = 20000000 + ri(100000, 999999);
    const age = ri(34, 92);
    const sex = pick(SEX);
    const icu = rng() > 0.45;
    const admType = pick(ADMISSION_TYPES);
    const los = +rand(1, 22).toFixed(1);

    // Assign risk
    const r = rng();
    let tier, score;
    if (r < 0.28) { tier = "high"; score = ri(60, 100); }
    else if (r < 0.62) { tier = "moderate"; score = ri(30, 59); }
    else { tier = "low"; score = ri(2, 29); }

    // Build markers
    const markers = MARKER_DEFS.map((def) => {
      // Probability of abnormality scales with tier
      const pAbn = tier === "high" ? 0.55 : tier === "moderate" ? 0.32 : 0.12;
      const isAbn = rng() < pAbn;
      let dir = "normal";
      if (isAbn) dir = def.aki ? (rng() < 0.7 ? "high" : "low") : (rng() < 0.5 ? "high" : "low");
      // Some markers always trend high in high-risk
      if (tier === "high" && (def.name === "Creatinine" || def.name === "BUN (Urea Nitrogen)")) dir = "high";
      if (tier === "high" && (def.name === "Bicarbonate" || def.name === "Urine Output")) dir = "low";
      const series = genTrend(def, dir);
      const latest = series[series.length - 1];
      const min = +Math.min(...series).toFixed(2);
      const max = +Math.max(...series).toFixed(2);
      const mean = +(series.reduce((a, b) => a + b, 0) / series.length).toFixed(2);
      const status = statusOf(def, latest);
      return { ...def, latest, min, max, mean, status, series };
    });

    const abnormal = markers.filter((m) => m.status !== "normal");
    const highCount = markers.filter((m) => m.status === "high").length;
    const lowCount = markers.filter((m) => m.status === "low").length;

    // Top concern
    const creat = markers.find((m) => m.name === "Creatinine");
    const topConcern =
      tier === "high"
        ? `Creatinine ${creat.latest} ${creat.unit} (+${(creat.latest - creat.series[0]).toFixed(1)} rise): strong kidney function risk signal`
        : tier === "moderate"
        ? `${abnormal[0]?.name || "Marker"} ${abnormal[0]?.latest ?? ""} ${abnormal[0]?.unit ?? ""}: possible concern`
        : "Within expected range — routine review";

    // Contributing signals
    const signals = [];
    if (tier !== "low") {
      const c = markers.find((m) => m.name === "Creatinine");
      if (c.status === "high") signals.push(`Creatinine ${c.latest} mg/dL (+${(c.latest - c.series[0]).toFixed(1)} rise): strong kidney function risk signal`);
      const b = markers.find((m) => m.name === "BUN (Urea Nitrogen)");
      if (b.status === "high") signals.push(`BUN ${b.latest} mg/dL: significantly elevated nitrogen waste — strong renal clearance risk signal`);
      const u = markers.find((m) => m.name === "Urine Output");
      if (u.status === "low") signals.push(`Low urine output (~${u.latest} mL/hr): oliguria risk signal`);
      const m = markers.find((m) => m.name === "MAP");
      if (m.status === "low") signals.push(`Low MAP (min ${m.min} mmHg): renal perfusion risk signal`);
      const bc = markers.find((m) => m.name === "Bicarbonate");
      if (bc.status === "low") signals.push(`Bicarbonate ${bc.latest} mEq/L: metabolic acidosis risk signal`);
    }
    if (tier === "high") signals.push("Diagnosis context: CKD history, diabetes, hypertension — relevant risk signal");
    if (signals.length === 0) signals.push("No strong signals — markers within or near expected ranges");

    ADMISSIONS.push({
      subjectId, admissionId, age, sex, icu, admType, los,
      tier, score, markers, abnormal,
      abnormalCount: abnormal.length, highCount, lowCount,
      topConcern, signals,
    });
  }

  ADMISSIONS.sort((a, b) => b.score - a.score);

  const totals = {
    admissions: ADMISSIONS.length,
    high: ADMISSIONS.filter((a) => a.tier === "high").length,
    moderate: ADMISSIONS.filter((a) => a.tier === "moderate").length,
    low: ADMISSIONS.filter((a) => a.tier === "low").length,
    avgAbnormal: +(ADMISSIONS.reduce((s, a) => s + a.abnormalCount, 0) / ADMISSIONS.length).toFixed(1),
  };

  window.STRATA_DATA = { ADMISSIONS, MARKER_DEFS, totals };
})();
