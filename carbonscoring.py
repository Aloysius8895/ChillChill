"""
ConstructGuard AI - Carbon Score Module
"""

def calculate_carbon_score(resources: list) -> dict:
    """
    Calculates the overall Carbon Sustainability Score (0-100) for the cloud
    environment by applying penalties for emissions, hotspots, and critical inefficiencies.
    """
    # 1. Initialize counters and totals
    total_carbon_emissions = 0.0
    critical_hotspots = 0
    high_hotspots = 0
    critical_reduction_opportunities = 0

    # 2. Loop through resources to aggregate metrics needed for score & penalties
    for res in resources:
        total_carbon_emissions += res.get("carbon_kg_month", 0.0)
        
        # Count hotspots
        hotspot = res.get("hotspot_level", "")
        if hotspot == "Critical":
            critical_hotspots += 1
        elif hotspot == "High":
            high_hotspots += 1
            
        # Count critical reduction opportunities (e.g., Idle Resources)
        priority = res.get("priority", "")
        if priority == "Critical":
            critical_reduction_opportunities += 1

    # 3. Baseline score starts at 100
    score = 100.0

    # 4. Calculate and apply deductions
    emission_penalty = total_carbon_emissions / 10.0
    critical_hotspot_penalty = critical_hotspots * 10
    high_hotspot_penalty = high_hotspots * 5
    critical_reduction_penalty = critical_reduction_opportunities * 5

    score -= (emission_penalty + critical_hotspot_penalty + high_hotspot_penalty + critical_reduction_penalty)

    # 5. Ensure the final score stays strictly bounded between 0 and 100
    if score > 100:
        score = 100
    elif score < 0:
        score = 0
    
    # Round score to 1 decimal place for a polished presentation
    score = round(score, 1)

    # 6. Determine the semantic rating scale
    if 90 <= score <= 100:
        rating = "Excellent"
    elif 75 <= score <= 89.9:
        rating = "Good"
    elif 50 <= score <= 74.9:
        rating = "Needs Improvement"
    else:
        rating = "Poor"

    # 7. Return summary dictionary matching all requirements
    return {
        "carbon_score": score,
        "rating": rating,
        "total_carbon_emissions": round(total_carbon_emissions, 2),
        "critical_hotspots": critical_hotspots,
        "high_hotspots": high_hotspots
    }


def print_carbon_score_summary(score_data: dict):
    """
    Renders a clean executive summary box showcasing the score and environmental posture.
    """
    print("\n" + "=" * 60)
    print("             CONSTRUCTGUARD AI: SUSTAINABILITY REPORT      ")
    print("=" * 60)
    
    # Choose a visual indicator badge based on the rating performance
    badge = "🟢"
    if score_data["rating"] == "Needs Improvement":
        badge = "🟡"
    elif score_data["rating"] == "Poor":
        badge = "🔴"

    print(f"  🏆 Carbon Score           : {score_data['carbon_score']} / 100")
    print(f"  {badge} Sustainability Rating  : {score_data['rating']}")
    print("-" * 60)
    print(f"  🌱 Total Carbon Footprint : {score_data['total_carbon_emissions']} kg CO₂ / mo")
    print(f"  🔥 Critical Hotspots      : {score_data['critical_hotspots']}")
    print(f"  ⚡ High Hotspots          : {score_data['high_hotspots']}")
    print("=" * 60)