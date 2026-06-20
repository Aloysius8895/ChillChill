import sys
import os
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
