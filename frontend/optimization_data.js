const OPTIMIZATION_DATA = {
  "score": {
    "carbon_score": 47.1,
    "rating": "Poor",
    "total_carbon_emissions": 379.36,
    "critical_hotspots": 1,
    "high_hotspots": 0
  },
  "total_monthly_energy": 984.34,
  "total_saving_kg": 86.21,
  "first_6": [
    {
      "name": "web-server-01",
      "energy_kwh_month": 31,
      "carbon_kg_month": 12.65
    },
    {
      "name": "web-server-02",
      "energy_kwh_month": 32,
      "carbon_kg_month": 9.95
    },
    {
      "name": "old-project-vm",
      "energy_kwh_month": 118,
      "carbon_kg_month": 48.14
    },
    {
      "name": "analytics-cluster",
      "energy_kwh_month": 291,
      "carbon_kg_month": 118.73
    },
    {
      "name": "staging-vm",
      "energy_kwh_month": 96,
      "carbon_kg_month": 35.23
    },
    {
      "name": "admin-portal",
      "energy_kwh_month": 34,
      "carbon_kg_month": 10.57
    }
  ],
  "top_5_hotspots": [
    {
      "name": "analytics-cluster",
      "carbon_kg_month": 118.73,
      "hotspot_level": "Critical",
      "color": "#d62728"
    },
    {
      "name": "old-project-vm",
      "carbon_kg_month": 48.14,
      "hotspot_level": "Medium",
      "color": "#bcbd22"
    },
    {
      "name": "staging-vm",
      "carbon_kg_month": 35.23,
      "hotspot_level": "Medium",
      "color": "#bcbd22"
    },
    {
      "name": "legacy-jenkins",
      "carbon_kg_month": 32.3,
      "hotspot_level": "Medium",
      "color": "#bcbd22"
    },
    {
      "name": "fleet-tracker-api",
      "carbon_kg_month": 24.65,
      "hotspot_level": "Medium",
      "color": "#bcbd22"
    }
  ],
  "action_items": [
    {
      "id": "i-04c7b1e9aa0",
      "name": "old-project-vm",
      "opportunity_type": "Idle Resource",
      "recommendation": "Terminate or shut down resource",
      "estimated_carbon_saving_kg": 48.14,
      "priority": "Critical"
    },
    {
      "id": "i-09b4a1f7d80",
      "name": "analytics-cluster",
      "opportunity_type": "Region Optimization",
      "recommendation": "Move workload to a lower-carbon region",
      "estimated_carbon_saving_kg": 17.81,
      "priority": "Medium"
    },
    {
      "id": "i-03e9c2a5f17",
      "name": "staging-vm",
      "opportunity_type": "Underutilized Resource",
      "recommendation": "Resize or downscale resource",
      "estimated_carbon_saving_kg": 10.57,
      "priority": "High"
    },
    {
      "id": "i-0d6a9b3e552",
      "name": "legacy-jenkins",
      "opportunity_type": "Underutilized Resource",
      "recommendation": "Resize or downscale resource",
      "estimated_carbon_saving_kg": 9.69,
      "priority": "High"
    }
  ],
  "top_opportunities": [
    {
      "id": "i-04c7b1e9aa0",
      "name": "old-project-vm",
      "type": "vm",
      "region": "ap-southeast-1",
      "carbon_kg_month": 48.14,
      "opportunity_type": "Idle Resource",
      "recommendation": "Terminate or shut down resource",
      "estimated_carbon_saving_kg": 48.14,
      "priority": "Critical"
    },
    {
      "id": "i-09b4a1f7d80",
      "name": "analytics-cluster",
      "type": "vm",
      "region": "ap-southeast-1",
      "carbon_kg_month": 118.73,
      "opportunity_type": "Region Optimization",
      "recommendation": "Move workload to a lower-carbon region",
      "estimated_carbon_saving_kg": 17.81,
      "priority": "Medium"
    },
    {
      "id": "i-03e9c2a5f17",
      "name": "staging-vm",
      "type": "vm",
      "region": "us-east-1",
      "carbon_kg_month": 35.23,
      "opportunity_type": "Underutilized Resource",
      "recommendation": "Resize or downscale resource",
      "estimated_carbon_saving_kg": 10.57,
      "priority": "High"
    },
    {
      "id": "i-0d6a9b3e552",
      "name": "legacy-jenkins",
      "type": "vm",
      "region": "us-east-1",
      "carbon_kg_month": 32.3,
      "opportunity_type": "Underutilized Resource",
      "recommendation": "Resize or downscale resource",
      "estimated_carbon_saving_kg": 9.69,
      "priority": "High"
    },
    {
      "id": "i-07a2f8b6c11",
      "name": "fleet-tracker-api",
      "type": "vm",
      "region": "ap-south-1",
      "carbon_kg_month": 24.65,
      "opportunity_type": "None",
      "recommendation": "No major carbon reduction action needed",
      "estimated_carbon_saving_kg": 0.0,
      "priority": "Low"
    }
  ]
};