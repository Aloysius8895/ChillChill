import os, json
from flask import Flask, jsonify, request

# ---- tiny .env loader (no extra package needed) ----
if os.path.exists(".env"):
    for _line in open(".env"):
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            k, v = _line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# ---- optional Claude SDK ----
try:
    import anthropic
except ImportError:
    anthropic = None

app = Flask(__name__)

# =========================================================================
#  DIGITAL TWIN (shared data foundation) + RULE ENGINE (Features 1, 2, 3)
# =========================================================================
REGION_CI = {"us-east-1": 379, "us-west-2": 117, "eu-west-1": 291, "ap-southeast-1": 408}
DANGEROUS_PORTS = {22: "SSH", 3389: "RDP", 1883: "MQTT (plaintext)", 3306: "MySQL", 5432: "Postgres"}

RESOURCES = [
    {"id": "ec2-safety-gpu-01", "name": "Worker Safety AI - GPU Inference", "service": "Worker Safety AI", "region": "ap-southeast-1", "business_value": "high", "monthly_cost_usd": 2150, "utilization_pct": 19, "kwh_month": 1450, "security": {"public_access": False, "encryption_at_rest": True, "encryption_in_transit": True, "open_ports": [443], "iam": {"over_privileged": False, "mfa_enabled": True, "access_key_age_days": 41}}},
    {"id": "s3-safety-footage", "name": "Site Camera Footage Store", "service": "Worker Safety AI", "region": "ap-southeast-1", "business_value": "high", "monthly_cost_usd": 320, "utilization_pct": 88, "kwh_month": 90, "security": {"public_access": True, "encryption_at_rest": False, "encryption_in_transit": True, "open_ports": [], "iam": {"over_privileged": True, "mfa_enabled": False, "access_key_age_days": 410}}},
    {"id": "ec2-bim-render-01", "name": "BIM Rendering Compute", "service": "BIM Processing", "region": "eu-west-1", "business_value": "high", "monthly_cost_usd": 980, "utilization_pct": 12, "kwh_month": 720, "security": {"public_access": False, "encryption_at_rest": True, "encryption_in_transit": True, "open_ports": [443, 22], "iam": {"over_privileged": False, "mfa_enabled": True, "access_key_age_days": 60}}},
    {"id": "s3-bim-models", "name": "BIM Model Repository", "service": "BIM Processing", "region": "eu-west-1", "business_value": "high", "monthly_cost_usd": 540, "utilization_pct": 76, "kwh_month": 110, "security": {"public_access": False, "encryption_at_rest": False, "encryption_in_transit": True, "open_ports": [], "iam": {"over_privileged": False, "mfa_enabled": True, "access_key_age_days": 95}}},
    {"id": "rds-bim-meta", "name": "BIM Metadata Database", "service": "BIM Processing", "region": "eu-west-1", "business_value": "medium", "monthly_cost_usd": 410, "utilization_pct": 34, "kwh_month": 260, "security": {"public_access": False, "encryption_at_rest": True, "encryption_in_transit": True, "open_ports": [5432], "iam": {"over_privileged": False, "mfa_enabled": True, "access_key_age_days": 30}}},
    {"id": "ec2-crane-ingest-01", "name": "Crane Sensor Ingest Gateway", "service": "Crane IoT Monitoring", "region": "ap-southeast-1", "business_value": "high", "monthly_cost_usd": 290, "utilization_pct": 67, "kwh_month": 220, "security": {"public_access": True, "encryption_at_rest": True, "encryption_in_transit": False, "open_ports": [1883, 8883, 22], "iam": {"over_privileged": True, "mfa_enabled": False, "access_key_age_days": 188}}},
    {"id": "dynamodb-crane-telemetry", "name": "Crane Telemetry Store", "service": "Crane IoT Monitoring", "region": "ap-southeast-1", "business_value": "high", "monthly_cost_usd": 175, "utilization_pct": 71, "kwh_month": 80, "security": {"public_access": False, "encryption_at_rest": True, "encryption_in_transit": True, "open_ports": [], "iam": {"over_privileged": False, "mfa_enabled": True, "access_key_age_days": 22}}},
    {"id": "ec2-orphan-04", "name": "Untagged Legacy Instance", "service": "Crane IoT Monitoring", "region": "ap-southeast-1", "business_value": "low", "monthly_cost_usd": 240, "utilization_pct": 0, "kwh_month": 180, "security": {"public_access": True, "encryption_at_rest": False, "encryption_in_transit": False, "open_ports": [22, 3389], "iam": {"over_privileged": True, "mfa_enabled": False, "access_key_age_days": 540}}},
    {"id": "lambda-material-scan", "name": "Material Barcode Processor", "service": "Material Tracking", "region": "ap-southeast-1", "business_value": "medium", "monthly_cost_usd": 45, "utilization_pct": 58, "kwh_month": 15, "security": {"public_access": False, "encryption_at_rest": True, "encryption_in_transit": True, "open_ports": [], "iam": {"over_privileged": False, "mfa_enabled": True, "access_key_age_days": 18}}},
    {"id": "rds-material-inventory", "name": "Material Inventory Database", "service": "Material Tracking", "region": "ap-southeast-1", "business_value": "medium", "monthly_cost_usd": 380, "utilization_pct": 41, "kwh_month": 250, "security": {"public_access": False, "encryption_at_rest": True, "encryption_in_transit": True, "open_ports": [3306], "iam": {"over_privileged": True, "mfa_enabled": False, "access_key_age_days": 295}}},
    {"id": "s3-material-docs", "name": "Delivery Docs Archive", "service": "Material Tracking", "region": "ap-southeast-1", "business_value": "low", "monthly_cost_usd": 90, "utilization_pct": 30, "kwh_month": 40, "security": {"public_access": False, "encryption_at_rest": True, "encryption_in_transit": True, "open_ports": [], "iam": {"over_privileged": False, "mfa_enabled": True, "access_key_age_days": 70}}},
    {"id": "redshift-site-analytics", "name": "Site Analytics Warehouse", "service": "Site Analytics", "region": "us-east-1", "business_value": "medium", "monthly_cost_usd": 1890, "utilization_pct": 23, "kwh_month": 1320, "security": {"public_access": False, "encryption_at_rest": True, "encryption_in_transit": True, "open_ports": [5439], "iam": {"over_privileged": False, "mfa_enabled": True, "access_key_age_days": 88}}},
    {"id": "ec2-analytics-dash", "name": "Analytics Dashboard Server", "service": "Site Analytics", "region": "us-east-1", "business_value": "medium", "monthly_cost_usd": 160, "utilization_pct": 44, "kwh_month": 130, "security": {"public_access": True, "encryption_at_rest": True, "encryption_in_transit": True, "open_ports": [443, 22], "iam": {"over_privileged": False, "mfa_enabled": True, "access_key_age_days": 51}}},
    {"id": "ebs-unattached-vol-09", "name": "Unattached Storage Volume", "service": "Site Analytics", "region": "us-east-1", "business_value": "low", "monthly_cost_usd": 85, "utilization_pct": 0, "kwh_month": 20, "security": {"public_access": False, "encryption_at_rest": False, "encryption_in_transit": False, "open_ports": [], "iam": {"over_privileged": False, "mfa_enabled": True, "access_key_age_days": 120}}},
    {"id": "s3-analytics-backups", "name": "Analytics Backup Bucket", "service": "Site Analytics", "region": "us-east-1", "business_value": "low", "monthly_cost_usd": 210, "utilization_pct": 9, "kwh_month": 60, "security": {"public_access": True, "encryption_at_rest": True, "encryption_in_transit": True, "open_ports": [], "iam": {"over_privileged": False, "mfa_enabled": True, "access_key_age_days": 200}}},
    {"id": "ec2-safety-gpu-02", "name": "Worker Safety AI - GPU Standby", "service": "Worker Safety AI", "region": "ap-southeast-1", "business_value": "low", "monthly_cost_usd": 2150, "utilization_pct": 3, "kwh_month": 1400, "security": {"public_access": False, "encryption_at_rest": True, "encryption_in_transit": True, "open_ports": [443], "iam": {"over_privileged": False, "mfa_enabled": True, "access_key_age_days": 41}}},
]


def carbon_kg(r):
    return round(r["kwh_month"] * REGION_CI.get(r["region"], 400) / 1000, 1)


def security_issues(r):
    s, out = r["security"], []
    if s["public_access"]:
        out.append(["HIGH", "Publicly accessible"])
    if not s["encryption_at_rest"]:
        out.append(["HIGH", "No encryption at rest"])
    if not s["encryption_in_transit"]:
        out.append(["MEDIUM", "No encryption in transit"])
    for p in s["open_ports"]:
        if p in DANGEROUS_PORTS:
            out.append(["HIGH", f"Port {p} open ({DANGEROUS_PORTS[p]})"])
    if s["iam"]["over_privileged"]:
        out.append(["MEDIUM", "Over-privileged IAM role"])
    if not s["iam"]["mfa_enabled"]:
        out.append(["MEDIUM", "MFA not enabled"])
    if s["iam"]["access_key_age_days"] > 180:
        out.append(["MEDIUM", f"Key not rotated ({s['iam']['access_key_age_days']}d)"])
    return out


def waste_reasons(r):
    out = []
    if r["utilization_pct"] == 0:
        out.append("Idle / orphaned (0% use)")
    elif r["utilization_pct"] < 20 and r["monthly_cost_usd"] > 500:
        out.append("Over-provisioned (low use, high cost)")
    if r["business_value"] == "low" and r["monthly_cost_usd"] > 200:
        out.append("High cost for low value")
    return out


def analyze():
    findings = []
    total_cost = total_carbon = wasted = 0
    high = med = clean = 0
    for r in RESOURCES:
        issues, waste, c = security_issues(r), waste_reasons(r), carbon_kg(r)
        total_cost += r["monthly_cost_usd"]
        total_carbon += c
        if waste:
            wasted += r["monthly_cost_usd"]
        high += sum(1 for i in issues if i[0] == "HIGH")
        med += sum(1 for i in issues if i[0] == "MEDIUM")
        if not issues and not waste:
            clean += 1
        findings.append({**r, "issues": issues, "waste": waste, "carbon": c})
    security = max(0, 100 - (high * 8 + med * 3))
    efficiency = round(100 * (1 - wasted / total_cost))
    sustainability = round(100 * (1 - min(1, total_carbon / 4000)))
    chs = round(0.45 * security + 0.30 * efficiency + 0.25 * sustainability)
    return {
        "findings": findings, "total_cost": total_cost, "wasted": wasted,
        "total_carbon": round(total_carbon), "high": high, "med": med, "clean": clean,
        "scores": {"security": security, "efficiency": efficiency,
                   "sustainability": sustainability, "chs": chs},
    }


def findings_text(base):
    rows = []
    for f in base["findings"]:
        if f["issues"] or f["waste"]:
            sec = "; ".join(f"{i[0]}:{i[1]}" for i in f["issues"]) or "none"
            cost = "; ".join(f["waste"]) or "none"
            rows.append(f"{f['id']} ({f['service']}) | ${f['monthly_cost_usd']}/mo | "
                        f"{f['carbon']}kgCO2 | SEC[{sec}] | WASTE[{cost}]")
    return "\n".join(rows)


def project_after(base, recs):
    sec_gain = sum(r["impact"].get("security_points", 0) for r in recs)
    cost_save = sum(r["impact"].get("cost_saving_usd", 0) for r in recs)
    carbon_save = sum(r["impact"].get("carbon_saving_kg", 0) for r in recs)
    s = base["scores"]
    security = min(100, s["security"] + sec_gain)
    efficiency = min(100, round(100 * (1 - (base["wasted"] - cost_save) / base["total_cost"])))
    sustainability = min(100, round(100 * (1 - min(1, (base["total_carbon"] - carbon_save) / 4000))))
    chs = round(0.45 * security + 0.30 * efficiency + 0.25 * sustainability)
    return {"security": security, "efficiency": efficiency, "sustainability": sustainability,
            "chs": chs, "cost_saving_usd": cost_save, "carbon_saving_kg": carbon_save}


def local_fallback(base):
    ranked = []
    for f in base["findings"]:
        if not (f["issues"] or f["waste"]):
            continue
        sev_pts = sum(8 if i[0] == "HIGH" else 3 for i in f["issues"])
        cost_save = round(f["monthly_cost_usd"] * (1 if f["utilization_pct"] == 0 else 0.6)) if f["waste"] else 0
        carbon_save = round(f["carbon"] * (1 if f["utilization_pct"] == 0 else 0.5)) if f["waste"] else 0
        cat = "security" if len(f["issues"]) >= len(f["waste"]) else "cost"
        if f["utilization_pct"] == 0:
            action = f"Decommission {f['name']}"
        elif any("Public" in i[1] for i in f["issues"]):
            action = f"Block public access on {f['name']}"
        elif f["waste"]:
            action = f"Right-size {f['name']}"
        else:
            action = f"Harden {f['name']}"
        ranked.append({
            "resource_id": f["id"], "resource_name": f["name"], "action": action,
            "category": cat, "rationale": (f["issues"][0][1] if f["issues"] else f["waste"][0]),
            "impact": {"security_points": sev_pts, "cost_saving_usd": cost_save, "carbon_saving_kg": carbon_save},
        })
    ranked.sort(key=lambda r: r["impact"]["security_points"] + r["impact"]["cost_saving_usd"] / 50, reverse=True)
    ranked = ranked[:6]
    for i, r in enumerate(ranked):
        r["rank"] = i + 1
    return {"recommendations": ranked, "projected_after": project_after(base, ranked), "ai": False}


def call_claude(base):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic or not key:
        return None
    prompt = (
        "You are the AI Recommendation Engine for ConstructGuard AI, a cloud governance platform "
        "for construction tech.\n"
        f"Current Cloud Health Score: {base['scores']['chs']}/100 "
        f"(Security {base['scores']['security']}, Efficiency {base['scores']['efficiency']}, "
        f"Sustainability {base['scores']['sustainability']}).\n"
        f"Total cost ${base['total_cost']}/mo, wasted ${base['wasted']}/mo, "
        f"carbon {base['total_carbon']} kgCO2/mo.\nFindings per resource:\n"
        f"{findings_text(base)}\n\n"
        "Return ONLY valid JSON (no markdown, no prose) with this exact shape:\n"
        '{"recommendations":[{"rank":1,"resource_id":"...","resource_name":"...",'
        '"action":"short imperative action","category":"security|cost|carbon",'
        '"rationale":"one sentence, construction context",'
        '"impact":{"security_points":0,"cost_saving_usd":0,"carbon_saving_kg":0}}],'
        '"projected_after":{"security":0,"efficiency":0,"sustainability":0,"chs":0,'
        '"cost_saving_usd":0,"carbon_saving_kg":0}}\n'
        "Give the 6 highest-impact recommendations, ranked. Keep each action under 12 words."
    )
    try:
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(model="claude-sonnet-4-6", max_tokens=1000,
                                     messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in msg.content if b.type == "text")
        parsed = json.loads(text.replace("```json", "").replace("```", "").strip())
        parsed["ai"] = True
        return parsed
    except Exception as e:
        print("Claude call failed, using fallback:", e)
        return None


# =========================================================================
#  ROUTES
# =========================================================================
@app.route("/")
def index():
    return PAGE


@app.route("/api/base")
def api_base():
    b = analyze()
    return jsonify({"scores": b["scores"], "high": b["high"], "med": b["med"],
                    "wasted": b["wasted"], "total_carbon": b["total_carbon"],
                    "total_cost": b["total_cost"], "clean": b["clean"]})


@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    base = analyze()
    result = call_claude(base) or local_fallback(base)
    result["base_chs"] = base["scores"]["chs"]
    result["base_security"] = base["scores"]["security"]
    return jsonify(result)


# =========================================================================
#  FRONTEND (custom HTML/CSS/JS - your own UI/UX design)
# =========================================================================
PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>ConstructGuard AI - AI Recommendation Engine</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;500;600&display=swap');
:root{--bg:#0E141B;--surface:#18222E;--surface2:#1F2C3A;--border:#2A3A4A;--text:#EAF0F6;
--muted:#8696A7;--amber:#FFB020;--red:#FF5C5C;--teal:#2DD4BF;--green:#45D483;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif;
background-image:linear-gradient(#2A3A4A22 1px,transparent 1px),linear-gradient(90deg,#2A3A4A22 1px,transparent 1px);
background-size:34px 34px;padding:28px 22px;min-height:100vh;}
.wrap{max-width:920px;margin:0 auto}
.head{display:flex;align-items:center;justify-content:space-between;margin-bottom:22px;flex-wrap:wrap;gap:12px}
.eyebrow{font-size:11px;letter-spacing:2px;color:var(--amber);font-family:'JetBrains Mono',monospace}
.brand{font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:700;margin-top:2px}
.brand span{color:var(--amber)}
.headr{text-align:right;font-size:12px;color:var(--muted)}
.headr b{color:var(--text)}
.mono{font-family:'JetBrains Mono',monospace}
.panel{display:grid;grid-template-columns:auto 1fr;gap:24px;background:var(--surface);
border:1px solid var(--border);border-radius:16px;padding:24px;align-items:center}
.gauge-wrap{text-align:center}
.gauge{position:relative;width:170px;height:170px}
.gauge .num{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.gauge .num .v{font-family:'JetBrains Mono',monospace;font-size:44px;font-weight:700;line-height:1}
.gauge .num .l{font-size:11px;color:var(--muted);letter-spacing:1.5px;margin-top:4px}
.delta{margin-top:10px;font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--green)}
.pillar{margin-bottom:14px}
.pillar .top{display:flex;justify-content:space-between;font-size:12px;margin-bottom:6px}
.pillar .top .n{color:var(--muted);letter-spacing:.5px}
.pillar .top .v{font-family:'JetBrains Mono',monospace}
.bar{height:7px;background:var(--border);border-radius:6px;overflow:hidden}
.bar > i{display:block;height:100%;border-radius:6px;width:0;transition:width .9s cubic-bezier(.22,1,.36,1)}
.chips{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}
.chip{font-family:'JetBrains Mono',monospace;font-size:11px;padding:3px 8px;border-radius:6px;white-space:nowrap}
.center{text-align:center;margin:24px 0}
button{background:var(--amber);color:#1A1206;border:none;border-radius:10px;padding:13px 26px;
font-size:15px;font-weight:700;cursor:pointer;font-family:'Space Grotesk',sans-serif;transition:all .15s}
button:hover:not(:disabled){filter:brightness(1.08);transform:translateY(-1px)}
button:disabled{opacity:.7;cursor:default}
.note{margin-top:12px;font-size:13px;color:var(--muted);font-family:'JetBrains Mono',monospace}
.offline{margin-top:10px;font-size:12px;color:var(--amber)}
.outcomes{display:flex;gap:14px;margin-bottom:22px;flex-wrap:wrap}
.outcome{flex:1 1 160px;background:var(--surface2);border:1px solid var(--border);border-radius:12px;padding:14px 16px}
.outcome .v{font-family:'JetBrains Mono',monospace;font-size:24px;font-weight:700}
.outcome .l{font-size:12px;color:var(--muted);margin-top:3px}
.sec-title{font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:700;margin:4px 0 14px}
.rec{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px 16px;
margin-bottom:10px;display:flex;gap:14px;animation:rise .5s both}
.rec .rank{font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;color:var(--muted);min-width:26px}
.rec .body{flex:1}
.rec .r1{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
.rec .act{font-weight:600;font-size:15px}
.rec .cat{font-size:11px;text-transform:uppercase;letter-spacing:1px;font-family:'JetBrains Mono',monospace}
.rec .why{font-size:12.5px;color:var(--muted);margin:5px 0 9px}
.rec .imp{display:flex;gap:8px;flex-wrap:wrap}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:.5}50%{opacity:1}}
.pulse{animation:pulse 1.4s infinite}
@media(max-width:640px){.panel{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
  <div class="head">
    <div>
      <div class="eyebrow">FEATURE 4 - AI RECOMMENDATION ENGINE</div>
      <div class="brand">ConstructGuard <span>AI</span></div>
    </div>
    <div class="headr"><b>BuildCo Construction</b><div class="mono">digital twin &middot; 16 resources</div></div>
  </div>

  <div class="panel">
    <div class="gauge-wrap">
      <div class="gauge">
        <svg width="170" height="170" style="transform:rotate(-90deg)">
          <circle cx="85" cy="85" r="71" stroke="#2A3A4A" stroke-width="11" fill="none"/>
          <circle id="arc" cx="85" cy="85" r="71" stroke="#FF5C5C" stroke-width="11" fill="none"
            stroke-linecap="round" stroke-dasharray="446" stroke-dashoffset="446"
            style="transition:stroke-dashoffset .9s cubic-bezier(.22,1,.36,1),stroke .6s"/>
        </svg>
        <div class="num"><div class="v" id="score">0</div><div class="l" id="scoreLabel">CLOUD HEALTH</div></div>
      </div>
      <div class="delta" id="delta" style="display:none"></div>
    </div>
    <div>
      <div class="pillar"><div class="top"><span class="n">SECURITY</span><span class="v" id="pSecV">0/100</span></div><div class="bar"><i id="pSec" style="background:var(--red)"></i></div></div>
      <div class="pillar"><div class="top"><span class="n">EFFICIENCY</span><span class="v" id="pEffV">0/100</span></div><div class="bar"><i id="pEff" style="background:var(--amber)"></i></div></div>
      <div class="pillar"><div class="top"><span class="n">SUSTAINABILITY</span><span class="v" id="pSusV">0/100</span></div><div class="bar"><i id="pSus" style="background:var(--teal)"></i></div></div>
      <div class="chips" id="chips"></div>
    </div>
  </div>

  <div class="center">
    <button id="go" onclick="generate()">Generate AI Recommendations</button>
    <div class="note pulse" id="loading" style="display:none">prioritising findings &middot; estimating impact &middot; simulating outcome</div>
    <div class="offline" id="offline" style="display:none">Using built-in engine (live AI unavailable) - demo still fully functional.</div>
  </div>

  <div class="outcomes" id="outcomes" style="display:none"></div>
  <div id="recsTitle" class="sec-title" style="display:none">Prioritised actions</div>
  <div id="recs"></div>
</div>

<script>
var BASE=null;
function scoreColor(v){return v<40?'#FF5C5C':v<70?'#FFB020':'#45D483';}
function setBar(id,vid,val){document.getElementById(id).style.width=val+'%';document.getElementById(vid).textContent=val+'/100';}
function setGauge(target,label){
  var arc=document.getElementById('arc');
  arc.style.strokeDashoffset=446*(1-target/100);
  arc.setAttribute('stroke',scoreColor(target));
  document.getElementById('scoreLabel').textContent=label;
  var el=document.getElementById('score'),start=performance.now(),from=parseInt(el.textContent)||0;
  function tick(now){var p=Math.min(1,(now-start)/900),e=1-Math.pow(1-p,3);
    el.textContent=Math.round(from+(target-from)*e);if(p<1)requestAnimationFrame(tick);}
  requestAnimationFrame(tick);
}
function chip(color,text){return '<span class="chip" style="color:'+color+';background:'+color+'1A;border:1px solid '+color+'40">'+text+'</span>';}

fetch('/api/base').then(function(r){return r.json();}).then(function(b){
  BASE=b;var s=b.scores;
  setGauge(s.chs,'CLOUD HEALTH');
  setBar('pSec','pSecV',s.security);setBar('pEff','pEffV',s.efficiency);setBar('pSus','pSusV',s.sustainability);
  document.getElementById('chips').innerHTML=
    chip('#FF5C5C',b.high+' HIGH / '+b.med+' MED findings')+
    chip('#FFB020','$'+b.wasted.toLocaleString()+'/mo at risk')+
    chip('#2DD4BF',b.total_carbon.toLocaleString()+' kgCO2/mo');
});

function generate(){
  var btn=document.getElementById('go');
  btn.disabled=true;btn.textContent='Analysing cloud estate...';
  document.getElementById('loading').style.display='block';
  document.getElementById('offline').style.display='none';
  fetch('/api/recommend',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})
  .then(function(r){return r.json();}).then(function(d){
    document.getElementById('loading').style.display='none';
    btn.disabled=false;btn.textContent='Re-run AI Analysis';
    if(d.ai===false)document.getElementById('offline').style.display='block';
    var a=d.projected_after;
    setGauge(a.chs,'AFTER');
    setBar('pSec','pSecV',a.security);setBar('pEff','pEffV',a.efficiency);setBar('pSus','pSusV',a.sustainability);
    var dl=document.getElementById('delta');dl.style.display='block';
    dl.textContent='\u25B2 '+(a.chs-d.base_chs)+' from '+d.base_chs;
    document.getElementById('outcomes').style.display='flex';
    document.getElementById('outcomes').innerHTML=
      outcome('$'+(a.cost_saving_usd||0).toLocaleString(),'Monthly cost saved','#FFB020')+
      outcome((a.carbon_saving_kg||0).toLocaleString()+' kg','Carbon reduced','#2DD4BF')+
      outcome(d.base_security+' \u2192 '+a.security,'Security pillar','#45D483');
    document.getElementById('recsTitle').style.display='block';
    var cat={security:'#FF5C5C',cost:'#FFB020',carbon:'#2DD4BF'};
    var html='';
    d.recommendations.forEach(function(r,i){
      var imp='';
      if(r.impact.security_points>0)imp+=chip('#FF5C5C','+'+r.impact.security_points+' security');
      if(r.impact.cost_saving_usd>0)imp+=chip('#FFB020','-$'+r.impact.cost_saving_usd+'/mo');
      if(r.impact.carbon_saving_kg>0)imp+=chip('#2DD4BF','-'+r.impact.carbon_saving_kg+' kgCO2');
      var c=cat[r.category]||'#8696A7';
      html+='<div class="rec" style="border-left:3px solid '+c+';animation-delay:'+(i*0.06)+'s">'+
        '<div class="rank">'+r.rank+'</div><div class="body">'+
        '<div class="r1"><div class="act">'+r.action+'</div>'+
        '<span class="cat" style="color:'+c+'">'+r.category+'</span></div>'+
        '<div class="why">'+r.resource_name+' &middot; '+r.rationale+'</div>'+
        '<div class="imp">'+imp+'</div></div></div>';
    });
    document.getElementById('recs').innerHTML=html;
  });
}
function outcome(v,l,c){return '<div class="outcome"><div class="v" style="color:'+c+'">'+v+'</div><div class="l">'+l+'</div></div>';}
</script>
</body>
</html>"""

if __name__ == "__main__":
    app.run(debug=True, port=5000)