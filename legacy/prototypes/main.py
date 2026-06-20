import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

# Import your custom modules based on your exact file names
import carboncalculation
import energyusage
import hotspotdetection
import reductionanalysis
import carbonscoring

if __name__ == "__main__":
    FILE_NAME = "hilti-cloud-data (3).json"

    # 1. Load data using the function in main or energyusage
    cloud_data = energyusage.load_json_file(FILE_NAME)

    if cloud_data:
        # ==========================================
        # MODULE 1: Energy Usage Estimation
        # ==========================================
        # Call functions from energyusage.py
        resources_data = energyusage.extract_energy_data(cloud_data)
        total_monthly_energy = energyusage.calculate_total_energy(
            resources_data
        )

        energyusage.print_resource_table(
            resources_data, title="ConstructGuard AI: Resource Energy Summary"
        )
        print(
            f"\n⚡ Total Estimated Monthly Energy Usage: {total_monthly_energy} kWh"
        )

        # ==========================================
        # MODULE 2: Carbon Emission Calculation
        # ==========================================
        # Call functions from carboncalculation.py
        resources_data = carboncalculation.add_carbon_emissions(
            cloud_data, resources_data
        )

        carboncalculation.print_carbon_table(
            resources_data, title="ConstructGuard AI: Carbon Emission Summary"
        )

        total_monthly_carbon = carboncalculation.calculate_total_carbon(
            resources_data
        )
        top_5_emitters = carboncalculation.get_top_carbon_emitters(
            resources_data, top_n=5
        )

        print(
            f"\n🌱 Total Monthly Carbon Footprint: {total_monthly_carbon} kg CO₂"
        )

        carboncalculation.print_carbon_table(
            top_5_emitters, title="Top 5 Highest Carbon-Emitting Resources"
        )

        # ==========================================
        # MODULE 3: Carbon Hotspot Detection (NEW)
        # ==========================================

        # Step 1: Detect hotspot levels and sort the resources
        resources_data = hotspotdetection.detect_carbon_hotspots(resources_data)

        # Step 2: Isolate the top 5 worst offenders
        top_5_hotspots = hotspotdetection.get_top_carbon_hotspots(
            resources_data, top_n=5
        )

        # Step 3: Print the requested table output
        hotspotdetection.print_hotspot_table(
            top_5_hotspots, title="Top 5 Carbon Hotspots"
        )

        # =======================================================
        # MODULE 4: Reduction Opportunity Analysis (NEW)
        # =======================================================
        
        # Step 1: Run optimization rules across our dataset
        resources_data = reductionanalysis.analyze_reduction_opportunities(resources_data)

        # Step 2: Query for the highest impacting optimizations 
        top_5_savings = reductionanalysis.get_top_reduction_opportunities(resources_data, top_n=5)

        # Step 3: Print visual analytics ledger
        reductionanalysis.print_opportunity_table(
            top_5_savings, 
            title="Top 5 Carbon Reduction Opportunities"
        )

        # =======================================================
        # MODULE 5: Carbon Score (NEW)
        # =======================================================
        
        # Step 1: Run the scoring formula across the compiled asset dataset
        sustainability_summary = carbonscoring.calculate_carbon_score(resources_data)

        # Step 2: Output the executive scoreboard console card
        carbonscoring.print_carbon_score_summary(sustainability_summary)