"""
ConstructGuard AI - Reduction Opportunity Analysis Module
"""

def analyze_reduction_opportunities(resources: list) -> list:
    """
    Analyzes cloud resources against predefined sustainability rules to detect
    inefficiencies and inject optimization recommendations.
    """
    for resource in resources:
        # 1. Gather all dependencies for our rule engine
        # Use .get() with defaults to safely handle missing data points
        carbon = resource.get("carbon_kg_month", 0.0)
        cpu = resource.get("cpuUtilizationPct")
        idle_days = resource.get("idleDays")
        region_flexible = resource.get("regionFlexible", False)
        cost = resource.get("monthlyCostUsd", 0.0)

        # 2. Evaluate rules sequentially (ordered by severity and impact)
        
        # RULE 1: Idle Assets (Highest Priority)
        if idle_days is not None and idle_days > 30:
            opp_type = "Idle Resource"
            rec = "Terminate or shut down resource"
            saving = carbon * 1.00
            priority = "Critical"

        # RULE 2: Underutilized Assets 
        elif cpu is not None and cpu < 20 and carbon >= 20:
            opp_type = "Underutilized Resource"
            rec = "Resize or downscale resource"
            saving = carbon * 0.30
            priority = "High"

        # RULE 3: Location Arbitrage / Carbon Intense Zones
        elif region_flexible is True and carbon >= 20:
            opp_type = "Region Optimization"
            rec = "Move workload to a lower-carbon region"
            saving = carbon * 0.15
            priority = "Medium"

        # RULE 4: Double Offenders (Expensive & Polluting)
        elif carbon >= 50 and cost >= 100:
            opp_type = "High Carbon and High Cost"
            rec = "Review resource for optimization"
            saving = carbon * 0.20
            priority = "Medium"

        # Default Catch-all if everything operates optimally
        else:
            opp_type = "None"
            rec = "No major carbon reduction action needed"
            saving = 0.0
            priority = "Low"

        # 3. Inject findings back into the resource dictionary
        resource["opportunity_type"] = opp_type
        resource["recommendation"] = rec
        resource["estimated_carbon_saving_kg"] = round(saving, 2)
        resource["priority"] = priority

    return resources


def get_top_reduction_opportunities(resources: list, top_n: int = 5) -> list:
    """
    Sorts your entire cloud inventory by highest projected carbon savings
    and returns the top N recommendations.
    """
    sorted_opportunities = sorted(
        resources,
        key=lambda x: x.get("estimated_carbon_saving_kg", 0.0),
        reverse=True
    )
    return sorted_opportunities[:top_n]


def print_opportunity_table(resources: list, title: str):
    """
    Renders an enterprise-grade terminal summary ledger highlighting 
    the financial and environmental sustainability opportunities.
    """
    print("\n" + "=" * 140)
    print(f" {title.upper()} ".center(140, "="))
    print("=" * 140)

    # Clean character alignment block definitions
    header_format = "{:<15} | {:<20} | {:>12} | {:<25} | {:<40} | {:>12} | {:^10}"
    row_format    = "{:<15} | {:<20} | {:>12} | {:<25} | {:<40} | {:>12} | {:^10}"

    # Print Table Headers
    print(
        header_format.format(
            "ID", "Name", "Carbon (kg)", "Opportunity Type", "Actionable Recommendation", "Savings (kg)", "Priority"
        )
    )
    print("-" * 140)

    # Print Individual Data Items
    for res in resources:
        print(
            row_format.format(
                str(res.get("id")),
                str(res.get("name")),
                res.get("carbon_kg_month", 0.0),
                str(res.get("opportunity_type")),
                str(res.get("recommendation")),
                res.get("estimated_carbon_saving_kg", 0.0),
                str(res.get("priority"))
            )
        )
    print("=" * 140)