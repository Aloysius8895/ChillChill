"""Runs the pipeline and writes frontend/optimization_data.js for the HTML page."""
import sys, json, os
sys.stdout.reconfigure(encoding="utf-8")

import energyusage
import carboncalculation
import hotspotdetection
import reductionanalysis
import carbonscoring

FILE_NAME = "hilti-cloud-data (3).json"

cloud_data     = energyusage.load_json_file(FILE_NAME)
resources      = energyusage.extract_energy_data(cloud_data)
resources      = carboncalculation.add_carbon_emissions(cloud_data, resources)
resources      = hotspotdetection.detect_carbon_hotspots(resources)
resources      = reductionanalysis.analyze_reduction_opportunities(resources)
score          = carbonscoring.calculate_carbon_score(resources)
top5_opps      = reductionanalysis.get_top_reduction_opportunities(resources, top_n=5)
top5_hotspots  = hotspotdetection.get_top_carbon_hotspots(resources, top_n=5)
total_energy   = energyusage.calculate_total_energy(resources)

# First 6 resources for baseline charts (original order before hotspot sort)
raw_resources  = energyusage.extract_energy_data(cloud_data)
raw_resources  = carboncalculation.add_carbon_emissions(cloud_data, raw_resources)
first_6        = raw_resources[:6]

SEVERITY_COLORS = {
    "Critical": "#d62728",
    "High":     "#ff7f0e",
    "Medium":   "#bcbd22",
    "Low":      "#2ca02c",
}

payload = {
    # Section 1 — score cards
    "score": score,
    "total_monthly_energy": round(total_energy, 2),
    "total_saving_kg": round(sum(r.get("estimated_carbon_saving_kg", 0) for r in top5_opps), 2),

    # Section 2 — baseline charts (first 6 resources)
    "first_6": [
        {
            "name":             r.get("name"),
            "energy_kwh_month": r.get("energy_kwh_month", 0),
            "carbon_kg_month":  r.get("carbon_kg_month", 0),
        }
        for r in first_6
    ],

    # Section 3 — hotspot chart
    "top_5_hotspots": [
        {
            "name":            r.get("name"),
            "carbon_kg_month": r.get("carbon_kg_month", 0),
            "hotspot_level":   r.get("hotspot_level"),
            "color":           SEVERITY_COLORS.get(r.get("hotspot_level"), "#535352"),
        }
        for r in top5_hotspots
    ],

    # Section 4 — action items
    "action_items": [
        {
            "id":                         r.get("id"),
            "name":                       r.get("name"),
            "opportunity_type":           r.get("opportunity_type"),
            "recommendation":             r.get("recommendation"),
            "estimated_carbon_saving_kg": r.get("estimated_carbon_saving_kg", 0),
            "priority":                   r.get("priority"),
        }
        for r in top5_opps
        if r.get("opportunity_type") != "None"
    ],

    # Section 5 — opportunities table
    "top_opportunities": [
        {
            "id":                         r.get("id"),
            "name":                       r.get("name"),
            "type":                       r.get("type"),
            "region":                     r.get("region"),
            "carbon_kg_month":            r.get("carbon_kg_month", 0),
            "opportunity_type":           r.get("opportunity_type"),
            "recommendation":             r.get("recommendation"),
            "estimated_carbon_saving_kg": r.get("estimated_carbon_saving_kg", 0),
            "priority":                   r.get("priority"),
        }
        for r in top5_opps
    ],
}

out_path = os.path.join("frontend", "optimization_data.js")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(f"const OPTIMIZATION_DATA = {json.dumps(payload, indent=2)};")

print(f"Written to {out_path}")
