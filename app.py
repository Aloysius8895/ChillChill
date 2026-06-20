"""
ConstructGuard AI - Feature 4 BACKEND
=====================================
Pure backend. No UI of its own. It:
  1. Serves your team's frontend at /frontend/...
  2. Answers GET /api/analyze with the exact JSON your
     construction-ready-ops.html expects (scores, metrics,
     recommendations, projected_after, resource table).

Folder layout (important):
    Hackathon/
        app.py                                <- this file
        .env                                  <- optional, for real Claude AI
        frontend/
            construction-ready-ops.html       <- your existing frontend

Run it:
    pip install flask
    python app.py
Then open:  http://localhost:8000
(redirects to http://localhost:8000/frontend/construction-ready-ops.html)

Works with NO API key (built-in rule engine -> badge shows "Rule Engine").
For real Claude AI (badge shows "Claude AI"):
    pip install anthropic
    create a .env file containing:  ANTHROPIC_API_KEY=sk-ant-...
"""

import os
import json
from flask import Flask, jsonify, request, send_from_directory, abort

# ---- tiny .env loader (no extra package needed) ----
if os.path.exists(".env"):
    for _line in open(".env"):
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# ---- optional Claude SDK ----
try:
    import anthropic
except ImportError:
    anthropic = None

# static_url_path/static_folder makes /frontend/<file> serve from ./frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__)


@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


# =========================================================================
#  DIGITAL TWIN (shared data) + RULE ENGINE (Features 1, 2, 3)
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


# =========================================================================
#  RECOMMENDATIONS (Feature 4) - Claude with deterministic fallback
# =========================================================================
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
    return {"recommendations": ranked, "ai": False}


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
        '"impact":{"security_points":0,"cost_saving_usd":0,"carbon_saving_kg":0}}]}\n'
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


_CACHE = {}


def build_payload(force=False):
    if "result" in _CACHE and not force:
        return _CACHE["result"]
    base = analyze()
    rec = call_claude(base) or local_fallback(base)
    projected = project_after(base, rec["recommendations"])
    resources = [{
        "id": f["id"], "name": f["name"], "service": f["service"], "region": f["region"],
        "monthly_cost_usd": f["monthly_cost_usd"], "utilization_pct": f["utilization_pct"],
        "carbon": f["carbon"], "issues": f["issues"], "waste": f["waste"],
    } for f in base["findings"]]
    result = {
        "ai": rec.get("ai", False),
        "current": {
            "scores": base["scores"],
            "total_cost": base["total_cost"],
            "wasted": base["wasted"],
            "total_carbon": base["total_carbon"],
            "high": base["high"],
            "med": base["med"],
            "clean": base["clean"],
            "resources": resources,
        },
        "recommendations": rec["recommendations"],
        "projected_after": projected,
    }
    _CACHE["result"] = result
    return result


# =========================================================================
#  ROUTES
# =========================================================================
def serve_file(filename):
    """Serve a file from frontend/ (preferred) or next to app.py."""
    for d in (FRONTEND_DIR, BASE_DIR):
        if os.path.isfile(os.path.join(d, filename)):
            return send_from_directory(d, filename)
    # helpful 404 so you can see what went wrong
    available = []
    for d in (FRONTEND_DIR, BASE_DIR):
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(".html"):
                    available.append(os.path.basename(d) + "/" + f)
    msg = ("<h2>404 - '" + filename + "' not found</h2>"
           "<p>Looked in:<br><code>" + FRONTEND_DIR + "</code><br><code>" + BASE_DIR + "</code></p>"
           "<p>HTML files I can actually see:</p><ul>"
           + "".join("<li>" + a + "</li>" for a in available)
           + "</ul><p>Check the file name matches exactly and sits in the <b>frontend</b> folder.</p>")
    return msg, 404


@app.route("/")
def home():
    return serve_file("index.html")


@app.route("/api/analyze")
def api_analyze():
    return jsonify(build_payload(force=request.args.get("refresh") == "1"))


@app.route("/<path:filename>")
def any_file(filename):
    return serve_file(filename)


if __name__ == "__main__":
    app.run(debug=True, port=8000)
