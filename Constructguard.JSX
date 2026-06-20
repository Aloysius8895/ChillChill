import React, { useState, useEffect, useRef } from "react";

/* =========================================================================
   ConstructGuard AI — Feature 4: AI Recommendation Engine
   Reads the BuildCo digital twin, derives findings (Features 1-3 logic),
   then calls Claude to prioritise + explain + simulate the "after" state.
   No API key required — calls are handled inside the artifact runtime.
   ========================================================================= */

// ---- Theme: blueprint-ink console + hi-vis construction amber ----
const T = {
  bg: "#0E141B",
  surface: "#18222E",
  surface2: "#1F2C3A",
  border: "#2A3A4A",
  text: "#EAF0F6",
  muted: "#8696A7",
  amber: "#FFB020",   // hi-vis / cost / brand
  red: "#FF5C5C",     // security / critical
  teal: "#2DD4BF",    // carbon
  green: "#45D483",   // improved / healthy
};
const catColor = { security: T.red, cost: T.amber, carbon: T.teal };

// ---- Digital twin (shared data foundation) ----
const REGION_CI = { "us-east-1": 379, "us-west-2": 117, "eu-west-1": 291, "ap-southeast-1": 408 };
const RESOURCES = [
  { id:"ec2-safety-gpu-01", name:"Worker Safety AI - GPU Inference", type:"EC2 (GPU)", service:"Worker Safety AI", region:"ap-southeast-1", business_value:"high", monthly_cost_usd:2150, utilization_pct:19, kwh_month:1450, security:{public_access:false,encryption_at_rest:true,encryption_in_transit:true,open_ports:[443],iam:{over_privileged:false,mfa_enabled:true,access_key_age_days:41}} },
  { id:"s3-safety-footage", name:"Site Camera Footage Store", type:"S3 Bucket", service:"Worker Safety AI", region:"ap-southeast-1", business_value:"high", monthly_cost_usd:320, utilization_pct:88, kwh_month:90, security:{public_access:true,encryption_at_rest:false,encryption_in_transit:true,open_ports:[],iam:{over_privileged:true,mfa_enabled:false,access_key_age_days:410}} },
  { id:"ec2-bim-render-01", name:"BIM Rendering Compute", type:"EC2 (Compute)", service:"BIM Processing", region:"eu-west-1", business_value:"high", monthly_cost_usd:980, utilization_pct:12, kwh_month:720, security:{public_access:false,encryption_at_rest:true,encryption_in_transit:true,open_ports:[443,22],iam:{over_privileged:false,mfa_enabled:true,access_key_age_days:60}} },
  { id:"s3-bim-models", name:"BIM Model Repository", type:"S3 Bucket", service:"BIM Processing", region:"eu-west-1", business_value:"high", monthly_cost_usd:540, utilization_pct:76, kwh_month:110, security:{public_access:false,encryption_at_rest:false,encryption_in_transit:true,open_ports:[],iam:{over_privileged:false,mfa_enabled:true,access_key_age_days:95}} },
  { id:"rds-bim-meta", name:"BIM Metadata Database", type:"RDS (PostgreSQL)", service:"BIM Processing", region:"eu-west-1", business_value:"medium", monthly_cost_usd:410, utilization_pct:34, kwh_month:260, security:{public_access:false,encryption_at_rest:true,encryption_in_transit:true,open_ports:[5432],iam:{over_privileged:false,mfa_enabled:true,access_key_age_days:30}} },
  { id:"ec2-crane-ingest-01", name:"Crane Sensor Ingest Gateway", type:"EC2 (Compute)", service:"Crane IoT Monitoring", region:"ap-southeast-1", business_value:"high", monthly_cost_usd:290, utilization_pct:67, kwh_month:220, security:{public_access:true,encryption_at_rest:true,encryption_in_transit:false,open_ports:[1883,8883,22],iam:{over_privileged:true,mfa_enabled:false,access_key_age_days:188}} },
  { id:"dynamodb-crane-telemetry", name:"Crane Telemetry Store", type:"DynamoDB", service:"Crane IoT Monitoring", region:"ap-southeast-1", business_value:"high", monthly_cost_usd:175, utilization_pct:71, kwh_month:80, security:{public_access:false,encryption_at_rest:true,encryption_in_transit:true,open_ports:[],iam:{over_privileged:false,mfa_enabled:true,access_key_age_days:22}} },
  { id:"ec2-orphan-04", name:"Untagged Legacy Instance", type:"EC2 (Compute)", service:"Crane IoT Monitoring", region:"ap-southeast-1", business_value:"low", monthly_cost_usd:240, utilization_pct:0, kwh_month:180, security:{public_access:true,encryption_at_rest:false,encryption_in_transit:false,open_ports:[22,3389],iam:{over_privileged:true,mfa_enabled:false,access_key_age_days:540}} },
  { id:"lambda-material-scan", name:"Material Barcode Processor", type:"Lambda", service:"Material Tracking", region:"ap-southeast-1", business_value:"medium", monthly_cost_usd:45, utilization_pct:58, kwh_month:15, security:{public_access:false,encryption_at_rest:true,encryption_in_transit:true,open_ports:[],iam:{over_privileged:false,mfa_enabled:true,access_key_age_days:18}} },
  { id:"rds-material-inventory", name:"Material Inventory Database", type:"RDS (MySQL)", service:"Material Tracking", region:"ap-southeast-1", business_value:"medium", monthly_cost_usd:380, utilization_pct:41, kwh_month:250, security:{public_access:false,encryption_at_rest:true,encryption_in_transit:true,open_ports:[3306],iam:{over_privileged:true,mfa_enabled:false,access_key_age_days:295}} },
  { id:"s3-material-docs", name:"Delivery Docs Archive", type:"S3 Bucket", service:"Material Tracking", region:"ap-southeast-1", business_value:"low", monthly_cost_usd:90, utilization_pct:30, kwh_month:40, security:{public_access:false,encryption_at_rest:true,encryption_in_transit:true,open_ports:[],iam:{over_privileged:false,mfa_enabled:true,access_key_age_days:70}} },
  { id:"redshift-site-analytics", name:"Site Analytics Warehouse", type:"Redshift (GPU cluster)", service:"Site Analytics", region:"us-east-1", business_value:"medium", monthly_cost_usd:1890, utilization_pct:23, kwh_month:1320, security:{public_access:false,encryption_at_rest:true,encryption_in_transit:true,open_ports:[5439],iam:{over_privileged:false,mfa_enabled:true,access_key_age_days:88}} },
  { id:"ec2-analytics-dash", name:"Analytics Dashboard Server", type:"EC2 (Compute)", service:"Site Analytics", region:"us-east-1", business_value:"medium", monthly_cost_usd:160, utilization_pct:44, kwh_month:130, security:{public_access:true,encryption_at_rest:true,encryption_in_transit:true,open_ports:[443,22],iam:{over_privileged:false,mfa_enabled:true,access_key_age_days:51}} },
  { id:"ebs-unattached-vol-09", name:"Unattached Storage Volume", type:"EBS Volume", service:"Site Analytics", region:"us-east-1", business_value:"low", monthly_cost_usd:85, utilization_pct:0, kwh_month:20, security:{public_access:false,encryption_at_rest:false,encryption_in_transit:false,open_ports:[],iam:{over_privileged:false,mfa_enabled:true,access_key_age_days:120}} },
  { id:"s3-analytics-backups", name:"Analytics Backup Bucket", type:"S3 Bucket", service:"Site Analytics", region:"us-east-1", business_value:"low", monthly_cost_usd:210, utilization_pct:9, kwh_month:60, security:{public_access:true,encryption_at_rest:true,encryption_in_transit:true,open_ports:[],iam:{over_privileged:false,mfa_enabled:true,access_key_age_days:200}} },
  { id:"ec2-safety-gpu-02", name:"Worker Safety AI - GPU Standby", type:"EC2 (GPU)", service:"Worker Safety AI", region:"ap-southeast-1", business_value:"low", monthly_cost_usd:2150, utilization_pct:3, kwh_month:1400, security:{public_access:false,encryption_at_rest:true,encryption_in_transit:true,open_ports:[443],iam:{over_privileged:false,mfa_enabled:true,access_key_age_days:41}} },
];

const DANGEROUS_PORTS = { 22:"SSH", 3389:"RDP", 1883:"MQTT (plaintext)", 3306:"MySQL", 5432:"Postgres" };

// ---- Rule engine (mirrors inspect_twin.py = Features 1, 2, 3) ----
const carbonKg = (r) => Math.round((r.kwh_month * (REGION_CI[r.region] || 400)) / 1000 * 10) / 10;

function securityIssues(r) {
  const s = r.security, out = [];
  if (s.public_access) out.push(["HIGH", "Publicly accessible"]);
  if (!s.encryption_at_rest) out.push(["HIGH", "No encryption at rest"]);
  if (!s.encryption_in_transit) out.push(["MEDIUM", "No encryption in transit"]);
  s.open_ports.forEach(p => { if (DANGEROUS_PORTS[p]) out.push(["HIGH", `Port ${p} open (${DANGEROUS_PORTS[p]})`]); });
  if (s.iam.over_privileged) out.push(["MEDIUM", "Over-privileged IAM role"]);
  if (!s.iam.mfa_enabled) out.push(["MEDIUM", "MFA not enabled"]);
  if (s.iam.access_key_age_days > 180) out.push(["MEDIUM", `Key not rotated (${s.iam.access_key_age_days}d)`]);
  return out;
}
function wasteReasons(r) {
  const out = [];
  if (r.utilization_pct === 0) out.push("Idle / orphaned (0% use)");
  else if (r.utilization_pct < 20 && r.monthly_cost_usd > 500) out.push("Over-provisioned (low use, high cost)");
  if (r.business_value === "low" && r.monthly_cost_usd > 200) out.push("High cost for low value");
  return out;
}
function analyze() {
  let totalCost = 0, totalCarbon = 0, wasted = 0, high = 0, med = 0, clean = 0;
  const findings = RESOURCES.map(r => {
    const issues = securityIssues(r), waste = wasteReasons(r), c = carbonKg(r);
    totalCost += r.monthly_cost_usd; totalCarbon += c;
    if (waste.length) wasted += r.monthly_cost_usd;
    high += issues.filter(i => i[0] === "HIGH").length;
    med += issues.filter(i => i[0] === "MEDIUM").length;
    if (!issues.length && !waste.length) clean++;
    return { ...r, issues, waste, carbon: c };
  });
  const security = Math.max(0, 100 - (high * 8 + med * 3));
  const efficiency = Math.round(100 * (1 - wasted / totalCost));
  const sustainability = Math.round(100 * (1 - Math.min(1, totalCarbon / 4000)));
  const chs = Math.round(0.45 * security + 0.30 * efficiency + 0.25 * sustainability);
  return { findings, totalCost, totalCarbon: Math.round(totalCarbon), wasted, high, med, clean,
           scores: { security, efficiency, sustainability, chs } };
}

// ---- count-up hook for animated numbers ----
function useCountUp(target, run, ms = 900) {
  const [v, setV] = useState(0);
  const raf = useRef();
  useEffect(() => {
    if (!run) return;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min(1, (now - start) / ms);
      const eased = 1 - Math.pow(1 - p, 3);
      setV(target * eased);
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [target, run, ms]);
  return v;
}

// ---- circular score gauge ----
function Gauge({ value, label, color, size = 170 }) {
  const r = size / 2 - 14, c = 2 * Math.PI * r, off = c * (1 - value / 100);
  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size/2} cy={size/2} r={r} stroke={T.border} strokeWidth="11" fill="none" />
        <circle cx={size/2} cy={size/2} r={r} stroke={color} strokeWidth="11" fill="none"
          strokeLinecap="round" strokeDasharray={c} strokeDashoffset={off}
          style={{ transition: "stroke-dashoffset .9s cubic-bezier(.22,1,.36,1), stroke .6s" }} />
      </svg>
      <div style={{ position:"absolute", inset:0, display:"flex", flexDirection:"column",
        alignItems:"center", justifyContent:"center" }}>
        <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:44, fontWeight:700, color:T.text, lineHeight:1 }}>
          {Math.round(value)}
        </div>
        <div style={{ fontSize:11, color:T.muted, letterSpacing:1.5, marginTop:4 }}>{label}</div>
      </div>
    </div>
  );
}

function scoreColor(v) { return v < 40 ? T.red : v < 70 ? T.amber : T.green; }

function Pillar({ name, value, accent }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display:"flex", justifyContent:"space-between", fontSize:12, marginBottom:6 }}>
        <span style={{ color:T.muted, letterSpacing:.5 }}>{name}</span>
        <span style={{ fontFamily:"'JetBrains Mono',monospace", color:T.text }}>{value}/100</span>
      </div>
      <div style={{ height:7, background:T.border, borderRadius:6, overflow:"hidden" }}>
        <div style={{ height:"100%", width:`${value}%`, background:accent, borderRadius:6,
          transition:"width .9s cubic-bezier(.22,1,.36,1)" }} />
      </div>
    </div>
  );
}

const Chip = ({ color, children }) => (
  <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color, background:`${color}1A`,
    border:`1px solid ${color}40`, padding:"3px 8px", borderRadius:6, whiteSpace:"nowrap" }}>{children}</span>
);

export default function App() {
  const base = useRef(analyze()).current;
  const [recs, setRecs] = useState(null);
  const [after, setAfter] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const [offline, setOffline] = useState(false);

  const shown = after || base.scores;
  const chs = useCountUp(shown.chs, true);

  function buildFindingsText() {
    return base.findings
      .filter(f => f.issues.length || f.waste.length)
      .map(f => {
        const sec = f.issues.map(i => `${i[0]}:${i[1]}`).join("; ") || "none";
        const cost = f.waste.join("; ") || "none";
        return `${f.id} (${f.service}) | $${f.monthly_cost_usd}/mo | ${f.carbon}kgCO2 | SEC[${sec}] | WASTE[${cost}]`;
      }).join("\n");
  }

  // deterministic fallback so the live demo never dies on a network hiccup
  function localFallback() {
    const ranked = base.findings
      .filter(f => f.issues.length || f.waste.length)
      .map(f => {
        const sevPts = f.issues.reduce((a,i)=>a+(i[0]==="HIGH"?8:3),0);
        const costSave = f.waste.length ? Math.round(f.monthly_cost_usd * (f.utilization_pct===0?1:0.6)) : 0;
        const carbonSave = f.waste.length ? Math.round(f.carbon * (f.utilization_pct===0?1:0.5)) : 0;
        const cat = f.issues.length >= f.waste.length ? "security" : "cost";
        const action = f.utilization_pct===0 ? `Decommission ${f.name}` :
          f.issues.some(i=>i[1].includes("Public")) ? `Block public access on ${f.name}` :
          f.waste.length ? `Right-size ${f.name}` : `Harden ${f.name}`;
        return { resource_id:f.id, resource_name:f.name, action, category:cat,
          rationale: f.issues[0]?.[1] || f.waste[0] || "Optimise resource",
          impact:{ security_points:sevPts, cost_saving_usd:costSave, carbon_saving_kg:carbonSave } };
      })
      .sort((a,b)=> (b.impact.security_points+b.impact.cost_saving_usd/50) - (a.impact.security_points+a.impact.cost_saving_usd/50))
      .slice(0,6)
      .map((r,i)=>({ rank:i+1, ...r }));
    return { recommendations: ranked, projected_after: projectAfter(ranked) };
  }

  function projectAfter(list) {
    const secGain = list.reduce((a,r)=>a+(r.impact.security_points||0),0);
    const costSave = list.reduce((a,r)=>a+(r.impact.cost_saving_usd||0),0);
    const carbonSave = list.reduce((a,r)=>a+(r.impact.carbon_saving_kg||0),0);
    const security = Math.min(100, base.scores.security + secGain);
    const efficiency = Math.min(100, Math.round(100*(1-(base.wasted-costSave)/base.totalCost)));
    const sustainability = Math.min(100, Math.round(100*(1-Math.min(1,(base.totalCarbon-carbonSave)/4000))));
    const score = Math.round(0.45*security+0.30*efficiency+0.25*sustainability);
    return { security, efficiency, sustainability, chs: score,
      cost_saving_usd: costSave, carbon_saving_kg: carbonSave };
  }

  async function generate() {
    setLoading(true); setErr(null); setOffline(false); setRecs(null); setAfter(null);
    const prompt = `You are the AI Recommendation Engine for ConstructGuard AI, a cloud governance platform for construction tech.
Current Cloud Health Score: ${base.scores.chs}/100 (Security ${base.scores.security}, Efficiency ${base.scores.efficiency}, Sustainability ${base.scores.sustainability}).
Total cost $${base.totalCost}/mo, wasted $${base.wasted}/mo, carbon ${base.totalCarbon} kgCO2/mo.
Findings per resource:
${buildFindingsText()}

Return ONLY valid JSON (no markdown, no prose) with this exact shape:
{"recommendations":[{"rank":1,"resource_id":"...","resource_name":"...","action":"short imperative action","category":"security|cost|carbon","rationale":"one sentence, construction context","impact":{"security_points":0,"cost_saving_usd":0,"carbon_saving_kg":0}}],"projected_after":{"security":0,"efficiency":0,"sustainability":0,"chs":0,"cost_saving_usd":0,"carbon_saving_kg":0}}
Give the 6 highest-impact recommendations, ranked. Keep each action under 12 words.`;

    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-6",
          max_tokens: 1000,
          messages: [{ role: "user", content: prompt }],
        }),
      });
      const data = await res.json();
      const text = data.content.map(i => (i.type === "text" ? i.text : "")).join("");
      const parsed = JSON.parse(text.replace(/```json|```/g, "").trim());
      setRecs(parsed.recommendations);
      setAfter({ ...parsed.projected_after });
    } catch (e) {
      const fb = localFallback();
      setRecs(fb.recommendations);
      setAfter(fb.projected_after);
      setOffline(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ fontFamily:"Inter,system-ui,sans-serif", background:T.bg, color:T.text,
      minHeight:"100%", padding:"28px 22px",
      backgroundImage:`linear-gradient(${T.border}22 1px, transparent 1px), linear-gradient(90deg, ${T.border}22 1px, transparent 1px)`,
      backgroundSize:"34px 34px" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;500;600&display=swap');
        @keyframes rise { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:none; } }
        @keyframes pulse { 0%,100%{opacity:.5} 50%{opacity:1} }
        .cg-btn:hover:not(:disabled){ filter:brightness(1.08); transform:translateY(-1px); }
        .cg-card{ animation:rise .5s both; }
      `}</style>

      <div style={{ maxWidth: 920, margin: "0 auto" }}>
        {/* header */}
        <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:22, flexWrap:"wrap", gap:12 }}>
          <div>
            <div style={{ fontSize:11, letterSpacing:2, color:T.amber, fontFamily:"'JetBrains Mono',monospace" }}>
              FEATURE 4 — AI RECOMMENDATION ENGINE
            </div>
            <div style={{ fontFamily:"'Space Grotesk',sans-serif", fontSize:28, fontWeight:700, marginTop:2 }}>
              ConstructGuard <span style={{ color:T.amber }}>AI</span>
            </div>
          </div>
          <div style={{ textAlign:"right", fontSize:12, color:T.muted }}>
            <div style={{ color:T.text, fontWeight:600 }}>BuildCo Construction</div>
            <div style={{ fontFamily:"'JetBrains Mono',monospace" }}>digital twin · 16 resources</div>
          </div>
        </div>

        {/* score + pillars */}
        <div style={{ display:"grid", gridTemplateColumns:"auto 1fr", gap:24, background:T.surface,
          border:`1px solid ${T.border}`, borderRadius:16, padding:24, alignItems:"center" }}>
          <div style={{ textAlign:"center" }}>
            <Gauge value={chs} label={after ? "AFTER" : "CLOUD HEALTH"} color={scoreColor(shown.chs)} />
            {after && (
              <div style={{ marginTop:10, fontFamily:"'JetBrains Mono',monospace", fontSize:13, color:T.green }}>
                ▲ {after.chs - base.scores.chs} from {base.scores.chs}
              </div>
            )}
          </div>
          <div>
            <Pillar name="SECURITY" value={shown.security} accent={T.red} />
            <Pillar name="EFFICIENCY" value={shown.efficiency} accent={T.amber} />
            <Pillar name="SUSTAINABILITY" value={shown.sustainability} accent={T.teal} />
            <div style={{ display:"flex", gap:10, marginTop:16, flexWrap:"wrap" }}>
              <Chip color={T.red}>{base.high} HIGH / {base.med} MED findings</Chip>
              <Chip color={T.amber}>${base.wasted.toLocaleString()}/mo at risk</Chip>
              <Chip color={T.teal}>{base.totalCarbon.toLocaleString()} kgCO₂/mo</Chip>
            </div>
          </div>
        </div>

        {/* action */}
        <div style={{ textAlign:"center", margin:"24px 0" }}>
          <button onClick={generate} disabled={loading} className="cg-btn"
            style={{ background:T.amber, color:"#1A1206", border:"none", borderRadius:10,
              padding:"13px 26px", fontSize:15, fontWeight:700, cursor: loading?"default":"pointer",
              fontFamily:"'Space Grotesk',sans-serif", transition:"all .15s",
              opacity: loading?0.7:1 }}>
            {loading ? "Analysing cloud estate…" : recs ? "Re-run AI Analysis" : "Generate AI Recommendations"}
          </button>
          {loading && (
            <div style={{ marginTop:12, fontSize:13, color:T.muted, animation:"pulse 1.4s infinite",
              fontFamily:"'JetBrains Mono',monospace" }}>
              prioritising findings · estimating impact · simulating outcome
            </div>
          )}
          {offline && (
            <div style={{ marginTop:10, fontSize:12, color:T.amber }}>
              Using built-in engine (live AI unavailable) — demo still fully functional.
            </div>
          )}
        </div>

        {/* projected savings band */}
        {after && (
          <div className="cg-card" style={{ display:"flex", gap:14, marginBottom:22, flexWrap:"wrap" }}>
            <Outcome label="Monthly cost saved" value={`$${(after.cost_saving_usd||0).toLocaleString()}`} color={T.amber} />
            <Outcome label="Carbon reduced" value={`${(after.carbon_saving_kg||0).toLocaleString()} kg`} color={T.teal} />
            <Outcome label="Security pillar" value={`${base.scores.security} → ${after.security}`} color={T.green} />
          </div>
        )}

        {/* recommendations */}
        {recs && (
          <div>
            <div style={{ fontFamily:"'Space Grotesk',sans-serif", fontSize:16, fontWeight:700, margin:"4px 0 14px" }}>
              Prioritised actions
            </div>
            {recs.map((r, i) => (
              <div key={r.rank} className="cg-card" style={{ animationDelay:`${i*0.06}s`,
                background:T.surface, border:`1px solid ${T.border}`,
                borderLeft:`3px solid ${catColor[r.category]||T.muted}`, borderRadius:12,
                padding:"14px 16px", marginBottom:10, display:"flex", gap:14 }}>
                <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:20, fontWeight:700,
                  color:T.muted, minWidth:26 }}>{r.rank}</div>
                <div style={{ flex:1 }}>
                  <div style={{ display:"flex", justifyContent:"space-between", gap:10, flexWrap:"wrap" }}>
                    <div style={{ fontWeight:600, fontSize:15 }}>{r.action}</div>
                    <span style={{ fontSize:11, color:catColor[r.category], textTransform:"uppercase",
                      letterSpacing:1, fontFamily:"'JetBrains Mono',monospace" }}>{r.category}</span>
                  </div>
                  <div style={{ fontSize:12.5, color:T.muted, margin:"5px 0 9px" }}>
                    {r.resource_name} · {r.rationale}
                  </div>
                  <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                    {r.impact?.security_points > 0 && <Chip color={T.red}>+{r.impact.security_points} security</Chip>}
                    {r.impact?.cost_saving_usd > 0 && <Chip color={T.amber}>−${r.impact.cost_saving_usd}/mo</Chip>}
                    {r.impact?.carbon_saving_kg > 0 && <Chip color={T.teal}>−{r.impact.carbon_saving_kg} kgCO₂</Chip>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!recs && !loading && (
          <div style={{ textAlign:"center", color:T.muted, fontSize:13, padding:"10px 0 4px" }}>
            BuildCo's cloud scores {base.scores.chs}/100. Run the engine to see prioritised fixes and the projected outcome.
          </div>
        )}
      </div>
    </div>
  );
}

function Outcome({ label, value, color }) {
  return (
    <div style={{ flex:"1 1 160px", background:T.surface2, border:`1px solid ${T.border}`,
      borderRadius:12, padding:"14px 16px" }}>
      <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:24, fontWeight:700, color }}>{value}</div>
      <div style={{ fontSize:12, color:T.muted, marginTop:3 }}>{label}</div>
    </div>
  );
}