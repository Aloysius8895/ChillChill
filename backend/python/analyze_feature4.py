import json
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "hilti-cloud-data.json"
OVERPROVISIONED_UTILIZATION_MAX = 25
OVERPROVISIONED_MIN_COST_USD = 50
DANGEROUS_PUBLIC_PORTS = {
    22: "SSH",
    3306: "MYSQL",
    5432: "POSTGRES",
    27017: "MONGO",
}


def number(value, default=0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def count_values(values):
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def get_region_intensity(resource, cloud_data):
    if resource.get("carbonIntensity_gPerKWh") is not None:
        return number(resource.get("carbonIntensity_gPerKWh"), 400)

    region_map = cloud_data.get("regionCarbonIntensity_gPerKWh", {})
    return number(region_map.get(resource.get("region")), 400)


def is_orphaned_or_idle(resource, utilization_pct, idle_days):
    status = str(resource.get("status", "")).lower()
    return (
        utilization_pct <= 0 or
        idle_days > 14 or
        resource.get("attached") is False or
        status in {"available", "orphaned", "unused"}
    )


def is_overprovisioned(utilization_pct, monthly_cost_usd):
    return (
        0 < utilization_pct <= OVERPROVISIONED_UTILIZATION_MAX and
        monthly_cost_usd >= OVERPROVISIONED_MIN_COST_USD
    )


def calculate_savings(resource, monthly_cost_usd, carbon_kg, utilization_pct, idle_days):
    if is_orphaned_or_idle(resource, utilization_pct, idle_days):
        return {
            "type": "delete",
            "cost_saved_usd": round(monthly_cost_usd),
            "reduced_carbon_kg": round(carbon_kg, 1),
        }

    if is_overprovisioned(utilization_pct, monthly_cost_usd):
        return {
            "type": "right-size",
            "cost_saved_usd": round(monthly_cost_usd * 0.6),
            "reduced_carbon_kg": round(carbon_kg * 0.6, 1),
        }

    return {
        "type": "none",
        "cost_saved_usd": 0,
        "reduced_carbon_kg": 0,
    }


def build_feature1_security_output(resource):
    findings = []

    for port_info in resource.get("openPorts", []):
        port = port_info.get("port")
        source = port_info.get("source", "")
        if source == "0.0.0.0/0" and port in DANGEROUS_PUBLIC_PORTS:
            findings.append({
                "severity": "HIGH",
                "message": f"PORT {port} OPEN ({DANGEROUS_PUBLIC_PORTS[port]})",
            })

    if not resource.get("encryptionAtRest", True):
        findings.append({
            "severity": "MED",
            "message": "NO ENCRYPTION AT REST",
        })

    if resource.get("publicAccess") and resource.get("environment") == "prod":
        findings.append({
            "severity": "MED",
            "message": "PUBLIC ACCESS ENABLED",
        })

    high_count = sum(1 for finding in findings if finding["severity"] == "HIGH")
    med_count = sum(1 for finding in findings if finding["severity"] == "MED")

    return {
        "score": max(0, 100 - high_count * 35 - med_count * 20),
        "findings": findings,
    }


def build_feature2_efficiency_output(resource):
    cpu = number(resource.get("cpuUtilizationPct"), 0)
    memory = number(resource.get("memoryUtilizationPct"), 0)
    cost = number(resource.get("monthlyCostUsd"), 0)
    idle_days = number(resource.get("idleDays"), 0)

    storage = 0
    disk_total = number(resource.get("diskTotalGb"), 0)
    if disk_total:
        storage = round(number(resource.get("diskUsedGb"), 0) / disk_total * 100, 1)
    elif resource.get("sizeGb"):
        storage = round(number(resource.get("diskUsedGb"), 0) / max(number(resource.get("sizeGb"), 1), 1) * 100, 1)

    if is_orphaned_or_idle(resource, cpu, idle_days):
        classification = "Idle / Orphaned"
        score = 20
        waste_reasons = ["IDLE / ORPHANED"]
    elif is_overprovisioned(cpu, cost):
        classification = "Over-provisioned"
        score = 45
        waste_reasons = ["OVER-PROVISIONED"]
    elif cpu < 15 and memory < 20:
        classification = "Underutilized"
        score = 55
        waste_reasons = ["UNDERUTILIZED"]
    else:
        classification = "Efficient"
        score = 100
        waste_reasons = []

    if idle_days > 14:
        waste_reasons = [f"IDLE {int(idle_days)}D"]

    if resource.get("runsOutsideWorkHours"):
        waste_reasons.append("RUNS OUTSIDE WORK HOURS")

    return {
        "score": score,
        "classification": classification,
        "cpu_pct": round(cpu),
        "memory_pct": round(memory),
        "storage_pct": storage,
        "monthly_cost_usd": round(cost),
        "idle_days": round(idle_days),
        "waste_reasons": waste_reasons,
    }


def build_feature3_carbon_output(resource, cloud_data):
    kwh_month = number(resource.get("estimatedKwhMonth"), 0)
    region_ci = get_region_intensity(resource, cloud_data)
    carbon_kg = round(kwh_month * region_ci / 1000, 1)

    if carbon_kg >= 100:
        hotspot_level = "Critical"
    elif carbon_kg >= 25:
        hotspot_level = "Medium"
    elif carbon_kg > 0:
        hotspot_level = "Low"
    else:
        hotspot_level = "None"

    return {
        "score": max(0, min(100, round(100 - carbon_kg / 2))),
        "energy_kwh_month": round(kwh_month, 2),
        "region_carbon_intensity": round(region_ci),
        "carbon_kg_month": carbon_kg,
        "hotspot_level": hotspot_level,
    }


def calculate_resource_scores(issues, waste, carbon_kg, savings_type):
    high_count = sum(1 for issue in issues if issue[0] == "HIGH")
    med_count = sum(1 for issue in issues if issue[0] == "MED")
    security_score = max(0, 100 - high_count * 35 - med_count * 20)

    if savings_type == "delete":
        efficiency_score = 0
    elif savings_type == "right-size":
        efficiency_score = 45
    elif waste:
        efficiency_score = 70
    else:
        efficiency_score = 100

    carbon_score = max(0, min(100, round(100 - carbon_kg / 2)))
    return security_score, efficiency_score, carbon_score


def build_resource_recommendation(resource, issues, savings_type):
    name = resource.get("name") or resource.get("id") or "resource"

    if savings_type == "delete":
        return f"Decommission {name}"

    if savings_type == "right-size":
        return f"Right-size {name}"

    issue_messages = [issue[1] for issue in issues]
    if any("PORT 22 OPEN" in message for message in issue_messages):
        return f"Restrict SSH access on {name}"
    if any("PORT" in message and "OPEN" in message for message in issue_messages):
        return f"Restrict public port access on {name}"
    if any("NO ENCRYPTION" in message for message in issue_messages):
        return f"Enable encryption on {name}"
    if any("PUBLIC ACCESS" in message for message in issue_messages):
        return f"Block public access on {name}"

    return "No immediate action"


def build_recommendation_rationale(resource, savings_type, issues, cost_saved, reduced_carbon):
    name = resource.get("name") or resource.get("id") or "resource"

    if savings_type == "delete":
        return f"{name} is idle or orphaned, so deleting it saves 100% of monthly cost and carbon."
    if savings_type == "right-size":
        return f"{name} is low-utilisation and high-cost, so right-sizing saves 60% of monthly cost and carbon."
    if issues:
        return f"{name} has security findings, but fixing them does not reduce cost or carbon."

    return f"{name} is healthy under the current rules."


def build_local_recommendations(analyzed):
    candidates = [
        resource for resource in analyzed
        if resource["issues"] or resource["waste"] or resource["cost_saved_usd"] or resource["reduced_carbon_kg"]
    ]

    def priority(resource):
        security_points = sum(15 if issue[0] == "HIGH" else 8 for issue in resource["issues"])
        return (
            security_points +
            resource["cost_saved_usd"] / 50 +
            resource["reduced_carbon_kg"] / 25
        )

    recommendations = []
    for resource in sorted(candidates, key=priority, reverse=True)[:6]:
        security_points = sum(15 if issue[0] == "HIGH" else 8 for issue in resource["issues"])
        category = "cost"
        if security_points and security_points >= resource["cost_saved_usd"] / 50:
            category = "security"
        elif resource["reduced_carbon_kg"] > resource["cost_saved_usd"] / 2:
            category = "carbon"

        recommendations.append({
            "rank": len(recommendations) + 1,
            "resource_id": resource["id"],
            "resource_name": resource["name"],
            "category": category,
            "action": resource["ai_recommendation"],
            "rationale": resource["recommendation_rationale"],
            "impact": {
                "cost_saving_usd": resource["cost_saved_usd"],
                "carbon_saving_kg": resource["reduced_carbon_kg"],
                "security_points": security_points,
            },
        })

    return recommendations


def analyze_cloud_ops(cloud_data):
    resources_raw = cloud_data.get("resources", [])

    analyzed = []
    total_cost = 0.0
    wasted_cost = 0.0
    total_carbon = 0.0
    high_count = 0
    med_count = 0
    clean_count = 0

    for resource in resources_raw:
        security_output = build_feature1_security_output(resource)
        efficiency_output = build_feature2_efficiency_output(resource)
        carbon_output = build_feature3_carbon_output(resource, cloud_data)

        issues = [
            [finding["severity"], finding["message"]]
            for finding in security_output["findings"]
        ]
        waste = efficiency_output["waste_reasons"]
        cpu = efficiency_output["cpu_pct"]
        cost = efficiency_output["monthly_cost_usd"]
        idle_days = efficiency_output["idle_days"]
        carbon_kg = carbon_output["carbon_kg_month"]
        savings = calculate_savings(resource, cost, carbon_kg, cpu, idle_days)

        total_cost += cost
        total_carbon += carbon_kg
        wasted_cost += savings["cost_saved_usd"]
        high_count += sum(1 for issue in issues if issue[0] == "HIGH")
        med_count += sum(1 for issue in issues if issue[0] == "MED")

        if not issues and not waste:
            clean_count += 1

        ai_recommendation = build_resource_recommendation(resource, issues, savings["type"])

        analyzed.append({
            "name": resource.get("name"),
            "service": resource.get("service") or resource.get("type"),
            "id": resource.get("id"),
            "monthly_cost_usd": round(cost),
            "carbon": carbon_kg,
            "utilization_pct": round(cpu),
            "security_score": security_output["score"],
            "efficiency_score": efficiency_output["score"],
            "carbon_score": carbon_output["score"],
            "issues": issues,
            "waste": waste,
            "feature_outputs": {
                "feature1_security": security_output,
                "feature2_efficiency": efficiency_output,
                "feature3_carbon": carbon_output,
            },
            "savings_type": savings["type"],
            "cost_saved_usd": savings["cost_saved_usd"],
            "reduced_carbon_kg": savings["reduced_carbon_kg"],
            "ai_recommendation": ai_recommendation,
            "recommendation_rationale": build_recommendation_rationale(
                resource,
                savings["type"],
                issues,
                savings["cost_saved_usd"],
                savings["reduced_carbon_kg"],
            ),
        })

    security_score = max(0, 100 - high_count * 15 - med_count * 8)
    efficiency_score = round(
        sum(resource["feature_outputs"]["feature2_efficiency"]["score"] for resource in analyzed) /
        max(len(analyzed), 1)
    )
    sustainability_score = round(
        sum(resource["feature_outputs"]["feature3_carbon"]["score"] for resource in analyzed) /
        max(len(analyzed), 1)
    )
    cloud_health_score = round(
        security_score * 0.4 +
        efficiency_score * 0.3 +
        sustainability_score * 0.3
    )

    recommendations = build_local_recommendations(analyzed)

    total_cost_saving = sum(resource["cost_saved_usd"] for resource in analyzed)
    total_carbon_saving = sum(resource["reduced_carbon_kg"] for resource in analyzed)
    total_security_points = sum(item["impact"]["security_points"] for item in recommendations)

    projected = {
        "chs": min(100, cloud_health_score + round(
            total_security_points * 0.3 +
            (total_cost_saving / total_cost * 30 if total_cost else 0)
        )),
        "security": min(100, security_score + total_security_points),
        "efficiency": min(100, efficiency_score + round(total_cost_saving / max(total_cost, 1) * 50)),
        "sustainability": min(100, sustainability_score + round(total_carbon_saving / max(total_carbon, 1) * 40)),
        "cost_saving_usd": round(total_cost_saving),
        "carbon_saving_kg": round(total_carbon_saving),
    }

    return {
        "ai": False,
        "dataset": "backend/data/hilti-cloud-data.json",
        "feature_outputs": {
            "feature1_security": {
                "high": high_count,
                "medium": med_count,
                "score": security_score,
            },
            "feature2_efficiency": {
                "score": efficiency_score,
                "classification_counts": count_values(
                    resource["feature_outputs"]["feature2_efficiency"]["classification"]
                    for resource in analyzed
                ),
            },
            "feature3_carbon": {
                "score": sustainability_score,
                "total_carbon_kg_month": round(total_carbon),
                "total_reduced_carbon_kg_month": round(total_carbon_saving),
            },
        },
        "current": {
            "scores": {
                "chs": cloud_health_score,
                "security": security_score,
                "efficiency": efficiency_score,
                "sustainability": sustainability_score,
            },
            "total_cost": round(total_cost),
            "wasted": round(wasted_cost),
            "total_carbon": round(total_carbon),
            "high": high_count,
            "med": med_count,
            "clean": clean_count,
            "resources": analyzed,
        },
        "recommendations": recommendations,
        "projected_after": projected,
    }


def main():
    with DATA_FILE.open(encoding="utf-8") as file:
        cloud_data = json.load(file)

    result = analyze_cloud_ops(cloud_data)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
