"""
ConstructGuard AI - twin inspector / mini rule engine.
Loads the digital twin JSON, derives findings, computes carbon,
and prints a Cloud Health Score. This is the same logic your
dashboard backend will run - just printed to terminal for now.
 
Run:  python inspect_twin.py buildco_cloud_twin.json
"""
import json, sys
 
DANGEROUS_PORTS = {22: "SSH", 3389: "RDP", 1883: "MQTT (plaintext)", 3306: "MySQL", 5432: "Postgres"}
 
def load(path):
    with open(path) as f:
        return json.load(f)
 
def carbon_kg(res, intensity_map):
    intensity = intensity_map.get(res["region"], 400)  # gCO2/kWh fallback
    return round(res["kwh_month"] * intensity / 1000, 1)  # -> kgCO2/month
 
def find_security_issues(res):
    """Each rule mirrors a real CSPM check. Returns (severity, message) tuples."""
    issues, s = [], res["security"]
    if s["public_access"]:
        issues.append(("HIGH", "Publicly accessible"))
    if not s["encryption_at_rest"]:
        issues.append(("HIGH", "No encryption at rest"))
    if not s["encryption_in_transit"]:
        issues.append(("MEDIUM", "No encryption in transit"))
    for p in s["open_ports"]:
        if p in DANGEROUS_PORTS:
            issues.append(("HIGH", f"Sensitive port {p} open ({DANGEROUS_PORTS[p]})"))
    if s["iam"]["over_privileged"]:
        issues.append(("MEDIUM", "Over-privileged IAM role"))
    if not s["iam"]["mfa_enabled"]:
        issues.append(("MEDIUM", "MFA not enabled"))
    if s["iam"]["access_key_age_days"] > 180:
        issues.append(("MEDIUM", f"Access key not rotated ({s['iam']['access_key_age_days']}d)"))
    return issues
 
def is_wasteful(res):
    """Cost vs value: idle, orphaned, or paying a lot for low-value/low-use."""
    reasons = []
    if res["utilization_pct"] == 0:
        reasons.append("Idle / orphaned (0% utilisation)")
    elif res["utilization_pct"] < 20 and res["monthly_cost_usd"] > 500:
        reasons.append("Over-provisioned (low use, high cost)")
    if res["business_value"] == "low" and res["monthly_cost_usd"] > 200:
        reasons.append("High cost for low business value")
    return reasons
 
def main(path):
    data = load(path)
    intensity = data["region_carbon_intensity_gco2_per_kwh"]
    resources = data["resources"]
 
    total_cost = total_carbon = wasted_cost = 0
    sec_high = sec_med = clean = 0
 
    print(f"\n=== {data['company']}  |  scan {data['scan_date']} ===\n")
    for r in resources:
        issues = find_security_issues(r)
        waste = is_wasteful(r)
        c = carbon_kg(r, intensity)
        total_cost += r["monthly_cost_usd"]
        total_carbon += c
        if waste:
            wasted_cost += r["monthly_cost_usd"]
        sec_high += sum(1 for sev, _ in issues if sev == "HIGH")
        sec_med  += sum(1 for sev, _ in issues if sev == "MEDIUM")
        if not issues and not waste:
            clean += 1
        if issues or waste:
            print(f"[{r['id']}] {r['name']}  ({r['service']})")
            for sev, msg in issues:
                print(f"   SEC  {sev:<6} {msg}")
            for w in waste:
                print(f"   COST        {w}  (${r['monthly_cost_usd']:.0f}/mo)")
            print(f"   CARBON      {c} kgCO2/mo\n")
 
    # --- Cloud Health Score: weighted blend of three pillars (0-100) ---
    n = len(resources)
    security_score = max(0, 100 - (sec_high * 8 + sec_med * 3))
    efficiency_score = round(100 * (1 - wasted_cost / total_cost))
    # sustainability: penalise carbon concentrated in low-value resources
    sustainability_score = round(100 * (1 - min(1, total_carbon / 4000)))
    chs = round(0.45 * security_score + 0.30 * efficiency_score + 0.25 * sustainability_score)
 
    print("=" * 48)
    print(f"Resources scanned        : {n}  ({clean} clean)")
    print(f"Security findings         : {sec_high} HIGH / {sec_med} MEDIUM")
    print(f"Total monthly cost        : ${total_cost:,.0f}")
    print(f"Wasted / at-risk spend    : ${wasted_cost:,.0f}/mo")
    print(f"Total carbon              : {total_carbon:,.0f} kgCO2/mo")
    print("-" * 48)
    print(f"Security pillar           : {security_score}/100")
    print(f"Efficiency pillar         : {efficiency_score}/100")
    print(f"Sustainability pillar     : {sustainability_score}/100")
    print(f"==> CLOUD HEALTH SCORE    : {chs}/100")
    print("=" * 48)
 
if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "buildco_cloud_twin.json")