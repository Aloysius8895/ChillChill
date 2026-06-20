import sys
import os
import json
sys.stdout.reconfigure(encoding="utf-8")

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

import energyusage
import carboncalculation
import hotspotdetection
import reductionanalysis
import carbonscoring

app = Flask(__name__, static_folder="frontend")
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = os.path.join(BASE_DIR, "hilti-cloud-data (3).json")


def run_pipeline():
    cloud_data = energyusage.load_json_file(FILE_NAME)
    if not cloud_data:
        return None, None

    resources = energyusage.extract_energy_data(cloud_data)
    resources = carboncalculation.add_carbon_emissions(cloud_data, resources)
    resources = hotspotdetection.detect_carbon_hotspots(resources)
    resources = reductionanalysis.analyze_reduction_opportunities(resources)
    score = carbonscoring.calculate_carbon_score(resources)
    return resources, score


@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("frontend", filename)


@app.route("/api/optimization")
def api_optimization():
    resources, score = run_pipeline()
    if resources is None:
        return jsonify({"error": "Failed to load data"}), 500

    top5 = reductionanalysis.get_top_reduction_opportunities(resources, top_n=5)
    total_saving = sum(r.get("estimated_carbon_saving_kg", 0) for r in top5)

    return jsonify({
        "score": score,
        "top_opportunities": [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "type": r.get("type"),
                "region": r.get("region"),
                "carbon_kg_month": r.get("carbon_kg_month", 0),
                "opportunity_type": r.get("opportunity_type"),
                "recommendation": r.get("recommendation"),
                "estimated_carbon_saving_kg": r.get("estimated_carbon_saving_kg", 0),
                "priority": r.get("priority"),
            }
            for r in top5
        ],
        "total_saving_kg": round(total_saving, 2),
    })


@app.route("/api/analyze")
def api_analyze():
    with open(FILE_NAME, encoding="utf-8") as f:
        raw = json.load(f)

    resources_raw = raw.get("resources", [])

    analyzed = []
    total_cost = 0.0
    wasted_cost = 0.0
    total_carbon = 0.0
    high_count = 0
    med_count = 0
    clean_count = 0

    for r in resources_raw:
        issues = []
        waste = []

        for port_info in r.get("openPorts", []):
            port = port_info.get("port")
            src = port_info.get("source", "")
            if port == 22 and src == "0.0.0.0/0":
                issues.append(["HIGH", "PORT 22 OPEN (SSH)"])
            elif port == 3306 and src == "0.0.0.0/0":
                issues.append(["HIGH", "PORT 3306 OPEN (MYSQL)"])
            elif port == 5432 and src == "0.0.0.0/0":
                issues.append(["HIGH", "PORT 5432 OPEN (POSTGRES)"])
            elif port == 27017 and src == "0.0.0.0/0":
                issues.append(["HIGH", "PORT 27017 OPEN (MONGO)"])

        if not r.get("encryptionAtRest", True):
            issues.append(["MED", "NO ENCRYPTION AT REST"])

        if r.get("publicAccess") and r.get("environment") == "prod":
            issues.append(["MED", "PUBLIC ACCESS ENABLED"])

        idle_days = r.get("idleDays", 0)
        cpu = r.get("cpuUtilizationPct", 0)
        mem = r.get("memoryUtilizationPct", 0)
        cost = r.get("monthlyCostUsd", 0)

        if idle_days > 14:
            waste.append(f"IDLE {idle_days}D")
            wasted_cost += cost
        elif cpu < 15 and mem < 20:
            waste.append("UNDERUTILIZED")
            wasted_cost += cost * 0.4

        if r.get("runsOutsideWorkHours"):
            waste.append("RUNS OUTSIDE WORK HOURS")

        kwh = r.get("estimatedKwhMonth", 0)
        intensity = r.get("carbonIntensity_gPerKWh", 400)
        carbon_kg = round(kwh * intensity / 1000, 1)

        total_cost += cost
        total_carbon += carbon_kg
        high_count += sum(1 for i in issues if i[0] == "HIGH")
        med_count += sum(1 for i in issues if i[0] == "MED")
        if not issues and not waste:
            clean_count += 1

        analyzed.append({
            "name": r.get("name"),
            "service": r.get("service"),
            "id": r.get("id"),
            "monthly_cost_usd": cost,
            "carbon": carbon_kg,
            "utilization_pct": cpu,
            "issues": issues,
            "waste": waste,
        })

    sec_score = max(0, 100 - high_count * 15 - med_count * 8)
    eff_penalties = sum(
        20 if any("IDLE" in w for w in r["waste"]) else
        10 if "UNDERUTILIZED" in r["waste"] else 0
        for r in analyzed
    )
    eff_score = max(0, 100 - eff_penalties)
    sus_score = max(0, min(100, int(100 - (total_carbon / 50))))
    chs = round(sec_score * 0.4 + eff_score * 0.3 + sus_score * 0.3)

    recs = []
    rank = 1

    idle_resources = [r for r in analyzed if any("IDLE" in w for w in r["waste"])]
    if idle_resources:
        recs.append({
            "rank": rank,
            "category": "Cost & Efficiency",
            "action": "Decommission Idle Resources",
            "rationale": f"{len(idle_resources)} resource(s) idle 14+ days ({', '.join(r['name'] for r in idle_resources[:3])}). Shutting them down eliminates unnecessary spend immediately.",
            "impact": {
                "cost_saving_usd": round(sum(r["monthly_cost_usd"] for r in idle_resources)),
                "carbon_saving_kg": round(sum(r["carbon"] for r in idle_resources)),
                "security_points": 0,
            },
        })
        rank += 1

    ssh_resources = [r for r in analyzed if any("PORT 22 OPEN" in i[1] for i in r["issues"])]
    if ssh_resources:
        recs.append({
            "rank": rank,
            "category": "Security",
            "action": "Restrict SSH Access",
            "rationale": f"Port 22 open to 0.0.0.0/0 on {', '.join(r['name'] for r in ssh_resources[:3])}. Restrict to known IP ranges to reduce attack surface.",
            "impact": {
                "cost_saving_usd": 0,
                "carbon_saving_kg": 0,
                "security_points": len(ssh_resources) * 15,
            },
        })
        rank += 1

    under_resources = [r for r in analyzed if "UNDERUTILIZED" in r["waste"]]
    if under_resources:
        recs.append({
            "rank": rank,
            "category": "Cost & Efficiency",
            "action": "Right-size Underutilised VMs",
            "rationale": f"{len(under_resources)} resource(s) running at <15% CPU and <20% memory. Downsizing saves cost with no performance impact.",
            "impact": {
                "cost_saving_usd": round(sum(r["monthly_cost_usd"] * 0.4 for r in under_resources)),
                "carbon_saving_kg": round(sum(r["carbon"] * 0.4 for r in under_resources)),
                "security_points": 0,
            },
        })
        rank += 1

    afterhours = [r for r in analyzed if "RUNS OUTSIDE WORK HOURS" in r["waste"]]
    if afterhours:
        recs.append({
            "rank": rank,
            "category": "Sustainability",
            "action": "Schedule Workloads During Green Hours",
            "rationale": f"{len(afterhours)} staging/dev resource(s) run 24/7 but only need business hours. Auto-stop schedules cut carbon and cost by ~55%.",
            "impact": {
                "cost_saving_usd": round(sum(r["monthly_cost_usd"] * 0.55 for r in afterhours)),
                "carbon_saving_kg": round(sum(r["carbon"] * 0.55 for r in afterhours)),
                "security_points": 0,
            },
        })
        rank += 1

    no_enc = [r for r in analyzed if any("NO ENCRYPTION" in i[1] for i in r["issues"])]
    if no_enc:
        recs.append({
            "rank": rank,
            "category": "Security",
            "action": "Enable Encryption at Rest",
            "rationale": f"{len(no_enc)} resource(s) lack encryption at rest, creating compliance risk. Enable server-side encryption with no performance penalty.",
            "impact": {
                "cost_saving_usd": 0,
                "carbon_saving_kg": 0,
                "security_points": len(no_enc) * 10,
            },
        })
        rank += 1

    flexible_high_carbon = [r for r in resources_raw if r.get("regionFlexible") and r.get("carbonIntensity_gPerKWh", 0) > 400]
    if flexible_high_carbon:
        kwh_total = sum(r.get("estimatedKwhMonth", 0) for r in flexible_high_carbon)
        carbon_save = round(kwh_total * (632 - 311) / 1000)
        recs.append({
            "rank": rank,
            "category": "Sustainability",
            "action": "Migrate Flexible Workloads to Lower-Carbon Regions",
            "rationale": f"{len(flexible_high_carbon)} region-flexible resource(s) in ap-south-1 (632 gCO₂/kWh). Moving to eu-central-1 (311 gCO₂/kWh) cuts emissions by ~51%.",
            "impact": {
                "cost_saving_usd": 0,
                "carbon_saving_kg": carbon_save,
                "security_points": 0,
            },
        })

    total_cost_save = sum(r["impact"]["cost_saving_usd"] for r in recs)
    total_carbon_save = sum(r["impact"]["carbon_saving_kg"] for r in recs)
    total_sec_pts = sum(r["impact"]["security_points"] for r in recs)

    projected = {
        "chs": min(100, chs + round(total_sec_pts * 0.3 + (total_cost_save / total_cost * 30 if total_cost else 0))),
        "security": min(100, sec_score + total_sec_pts),
        "efficiency": min(100, eff_score + round(total_cost_save / max(total_cost, 1) * 50)),
        "sustainability": min(100, sus_score + round(total_carbon_save / max(total_carbon, 1) * 40)),
        "cost_saving_usd": round(total_cost_save),
        "carbon_saving_kg": round(total_carbon_save),
    }

    return jsonify({
        "ai": False,
        "current": {
            "scores": {"chs": chs, "security": sec_score, "efficiency": eff_score, "sustainability": sus_score},
            "total_cost": round(total_cost),
            "wasted": round(wasted_cost),
            "total_carbon": round(total_carbon),
            "high": high_count,
            "med": med_count,
            "clean": clean_count,
            "resources": analyzed,
        },
        "recommendations": recs,
        "projected_after": projected,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
