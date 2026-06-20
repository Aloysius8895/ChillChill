import json
from pathlib import Path
from typing import List, Dict, Any, Optional

class CloudResource:
    """Represents a cloud resource with its metrics for evaluation."""
    def __init__(
        self,
        resource_id: str,
        resource_type: str,
        cpu_usage_percent: float,
        memory_usage_percent: float,
        storage_usage_percent: float,
        activity_level: str
    ):
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.cpu_usage = cpu_usage_percent
        self.memory_usage = memory_usage_percent
        self.storage_usage = storage_usage_percent
        self.activity_level = activity_level.lower()


class ResourceEfficiencyEngine:
    """Analyzes cloud resource utilization and generates efficiency reports."""

    def __init__(self):
        pass

    def classify_cpu(self, cpu: float) -> str:
        if 0 <= cpu <= 10: return "Idle"
        if 10 < cpu <= 40: return "Underutilized"
        if 40 < cpu <= 75: return "Efficient"
        if 75 < cpu <= 90: return "High Usage"
        return "Overloaded"

    def classify_memory(self, memory: float) -> str:
        if 0 <= memory <= 20: return "Underused"
        if 20 < memory <= 70: return "Efficient"
        if 70 < memory <= 85: return "High Usage"
        return "Critical"

    def classify_storage(self, storage: float) -> str:
        if 0 <= storage <= 30: return "Underutilized"
        if 30 < storage <= 80: return "Normal"
        if 80 < storage <= 95: return "High"
        return "Full Risk"

    def classify_activity(self, activity: str) -> str:
        mapping = {
            "low": "Idle",
            "medium": "Normal",
            "high": "Active",
            "very_high": "Heavy Workload"
        }
        return mapping.get(activity, "Unknown")

    def detect_overall_classification(self, cpu: float, memory: float) -> str:
        """Determines overall resource efficiency flag based on priority rules."""
        if cpu < 10 and memory < 20:
            return "Idle"
        if cpu < 15 and memory > 50:
            return "Overprovisioned"
        if cpu > 90 or memory > 85:
            return "Overloaded"
        if (40 <= cpu <= 75) and (20 <= memory <= 70):
            return "Efficient"
        if cpu <= 40:
            return "Underutilized"
        return "Mixed/Unclassified"

    def calculate_efficiency_score(self, cpu: float, memory: float, storage_pct: float, activity: str) -> float:
        """Computes weighted efficiency score (0-100) including storage.

        New formula weights:
          cpu: 35%%, memory: 30%%, storage: 20%%, activity: 15%%
        """
        if 0 <= cpu <= 10: cpu_score = 10
        elif 10 < cpu <= 40: cpu_score = 40
        elif 40 < cpu <= 75: cpu_score = 80
        elif 75 < cpu <= 90: cpu_score = 60
        else: cpu_score = 20

        if 0 <= memory <= 20: mem_score = 20
        elif 20 < memory <= 70: mem_score = 80
        elif 70 < memory <= 85: mem_score = 50
        else: mem_score = 20

        # Storage mapping (derived from disk used / total percent)
        # 0-30% -> underutilized, 30-70% -> efficient, 70-90% -> high, >90% -> full risk
        if 0 <= storage_pct <= 30: storage_score = 40
        elif 30 < storage_pct <= 70: storage_score = 80
        elif 70 < storage_pct <= 90: storage_score = 50
        else: storage_score = 20

        # Activity mapping
        act_mapping = {"low": 20, "medium": 60, "high": 80, "very_high": 90}
        act_score = act_mapping.get(activity, 0)

        final_score = (
            (cpu_score * 0.35) +
            (mem_score * 0.30) +
            (storage_score * 0.20) +
            (act_score * 0.15)
        )
        return max(0.0, min(100.0, final_score))

    def analyze_resources(self, resources_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Processes raw resource datasets and builds final reporting."""
        processed_resources = []
        total_efficiency_score = 0.0
        idle_count = 0
        overprovisioned_count = 0

        for data in resources_data:
            resource = CloudResource(
                resource_id=data["resource_id"],
                resource_type=data["resource_type"],
                cpu_usage_percent=data["cpu_usage_percent"],
                memory_usage_percent=data["memory_usage_percent"],
                storage_usage_percent=data["storage_usage_percent"],
                activity_level=data["activity_level"]
            )

            classification = self.detect_overall_classification(resource.cpu_usage, resource.memory_usage)
            cpu_status = self.classify_cpu(resource.cpu_usage)
            memory_status = self.classify_memory(resource.memory_usage)
            storage_status = self.classify_storage(resource.storage_usage)
            activity_status = self.classify_activity(resource.activity_level)

            score = self.calculate_efficiency_score(resource.cpu_usage, resource.memory_usage, resource.storage_usage, resource.activity_level)
            total_efficiency_score += score
            if classification == "Idle":
                idle_count += 1
            elif classification == "Overprovisioned":
                overprovisioned_count += 1

            processed_resources.append({
                "resource_id": resource.resource_id,
                "classification": classification,
                "cpu_status": cpu_status,
                "memory_status": memory_status,
                "storage_status": storage_status,
                "activity_status": activity_status,
                "efficiency_score": round(score, 1)
            })

        total_resources = len(resources_data)
        avg_efficiency = round(total_efficiency_score / total_resources, 1) if total_resources > 0 else 0.0

        return {
            "summary": {
                "total_resources": total_resources,
                "idle_resources": idle_count,
                "overprovisioned_resources": overprovisioned_count,
                "average_efficiency_score": avg_efficiency
            },
            "resources": processed_resources
        }


def load_resources_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Load resource entries from the local JSON file and normalize fields."""
    with open(file_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    resources = payload.get("resources", [])
    normalized = []

    for resource in resources:
        cpu_pct = float(resource.get("cpuUtilizationPct", 0)) if resource.get("cpuUtilizationPct") is not None else 0.0
        mem_pct = float(resource.get("memoryUtilizationPct", 0)) if resource.get("memoryUtilizationPct") is not None else 0.0

        # Prefer disk fields if present (diskUsedGb / diskTotalGb), fallback to any storageUsagePct
        disk_used = resource.get("diskUsedGb")
        disk_total = resource.get("diskTotalGb")
        if disk_used is not None and disk_total:
            try:
                storage_pct = float(disk_used) / float(disk_total) * 100.0
            except Exception:
                storage_pct = 0.0
        else:
            storage_pct = float(resource.get("storageUsagePct", 0)) if resource.get("storageUsagePct") is not None else 0.0

        if cpu_pct >= 75 or mem_pct >= 75:
            activity_level = "very_high"
        elif cpu_pct >= 40 or mem_pct >= 40:
            activity_level = "high"
        elif cpu_pct >= 15 or mem_pct >= 20:
            activity_level = "medium"
        else:
            activity_level = "low"

        normalized.append({
            "resource_id": resource.get("id", resource.get("name", "unknown")),
            "resource_type": resource.get("type", "unknown"),
            "cpu_usage_percent": cpu_pct,
            "memory_usage_percent": mem_pct,
            "storage_usage_percent": storage_pct,
            "activity_level": activity_level
        })

    return normalized


if __name__ == "__main__":
    data_file = Path(__file__).resolve().parent / "hilti-cloud-data (3).json"
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")

    resources = load_resources_from_json(str(data_file))
    engine = ResourceEfficiencyEngine()
    output = engine.analyze_resources(resources)

    print("=" * 65)
    print("        CONSTRUCTION CLOUD: RESOURCE EFFICIENCY ENGINE REPORT     ")
    print("=" * 65)
    print(f"Total Resources Monitored : {output['summary']['total_resources']}")
    print(f"Idle Fleet Resources      : {output['summary']['idle_resources']}")
    print(f"Overprovisioned Allocations: {output['summary']['overprovisioned_resources']}")
    print(f"System Efficiency Score    : {output['summary']['average_efficiency_score']} / 100")
    print("-" * 65)
    print(f"{'Resource ID':<20} | {'Classification':<16} | {'CPU Status':<13} | {'Score':<5}")
    print("-" * 65)
    for r in output["resources"]:
        print(f"{r['resource_id']:<20} | {r['classification']:<16} | {r['cpu_status']:<13} | {r['efficiency_score']:<5}")
    print("=" * 65)
