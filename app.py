"""
ConstructGuard AI — Single-File Frontend Web Dashboard
"""
import streamlit as st
import plotly.express as px

# 1. Import your 5 functional backend modules
import energyusage
import carboncalculation
import hotspotdetection
import reductionanalysis
import carbonscoring

# Page setup for a wide enterprise dashboard look
st.set_page_config(page_title="ConstructGuard AI", page_icon="🛡️", layout="wide")

st.title("🛡️ ConstructGuard AI — Carbon Governance Platform")
st.markdown("### Welcome back, *Carbon Intelligence Lead*")

# 2. Run the processing pipeline to fetch data
FILE_NAME = "hilti-cloud-data (3).json"
cloud_data = energyusage.load_json_file(FILE_NAME)

if cloud_data:
    # Pass data sequentially through your modules exactly like your terminal version
    resources_data = energyusage.extract_energy_data(cloud_data)
    resources_data = carboncalculation.add_carbon_emissions(cloud_data, resources_data)
    resources_data = hotspotdetection.detect_carbon_hotspots(resources_data)
    resources_data = reductionanalysis.analyze_reduction_opportunities(resources_data)
    
    # Grab aggregated summaries for score cards
    total_monthly_energy = energyusage.calculate_total_energy(resources_data)
    sustainability_summary = carbonscoring.calculate_carbon_score(resources_data)

    # =========================================================================
    # SECTION 1: HERO SCORECARDS (Carbon Score Module Summary)
    # =========================================================================
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="🏆 Sustainability Score", value=f"{sustainability_summary['carbon_score']} / 100")
    with col2:
        st.metric(label="📊 Account Rating", value=sustainability_summary['rating'])
    with col3:
        st.metric(label="⚡ Total Account Energy", value=f"{total_monthly_energy} kWh")
    with col4:
        st.metric(label="🌱 Total Carbon Footprint", value=f"{sustainability_summary['total_carbon_emissions']} kg CO₂")

    # =========================================================================
    # SECTION 2: SEPARATE BASELINE INVENTORY CHARTS (Tables 1 & 2)
    # =========================================================================
    st.markdown("## 📊 Infrastructure Baseline Profiles")
    st.caption("Visualizing the baseline properties of the first 6 active resources.")
    
    # Isolate the first 6 resources for the top charts
    first_6 = resources_data[:6]
    resource_names = [res.get('name', 'Unknown') for res in first_6]
    energy_values = [res.get('energy_kwh_month', 0) for res in first_6]
    carbon_values = [res.get('carbon_kg_month', 0) for res in first_6]

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("🟦 Table 1: Energy Usage (kWh)")
        st.bar_chart(data=dict(zip(resource_names, energy_values)), color="#1f77b4")

    with chart_col2:
        st.subheader("🟩 Table 2: Carbon Emissions (kg CO₂)")
        st.bar_chart(data=dict(zip(resource_names, carbon_values)), color="#2ca02c")

    # =========================================================================
    # SECTION 3: COMBINED TOP OFFENDERS & HOTSPOTS (Tables 3 & 4)
    # =========================================================================
    st.markdown("---")
    st.markdown("## 🔥 Threat Vector: Top 5 Carbon Hotspots")
    st.caption("Resources sorted by highest carbon footprints, dynamically color-coded by severity state.")

    # Get your top 5 highest emitting hotspots using your backend sort order
    top_5_hotspots = hotspotdetection.get_top_carbon_hotspots(resources_data, top_n=5)

    # State severity hex code dictionary mapping 
    severity_colors = {
        "Critical": "#d62728",  # Crimson Red
        "High": "#ff7f0e",      # Dark Orange
        "Medium": "#bcbd22",    # Amber Yellow
        "Low": "#2ca02c"        # Muted Green
    }

    hotspot_names = [res.get('name') for res in top_5_hotspots]
    hotspot_carbon = [res.get('carbon_kg_month') for res in top_5_hotspots]
    hotspot_levels = [res.get('hotspot_level') for res in top_5_hotspots]

    # Build the specialized Plotly chart to allow state colors
    fig = px.bar(
        x=hotspot_names,
        y=hotspot_carbon,
        color=hotspot_levels,
        color_discrete_map=severity_colors,
        labels={"x": "Resource Name", "y": "Carbon Output (kg)", "color": "Hotspot Severity"},
        title="Top 5 Emissions Offenders Cross-Referenced by Alert Severity State"
    )
    st.plotly_chart(fig, width="stretch")

    # =========================================================================
    # SECTION 4: REDUCTION OPPORTUNITIES (Table 5)
    # =========================================================================
    st.markdown("---")
    st.markdown("## 💡 Carbon Reduction Action Items")
    st.caption("Prescriptive mitigation task logs compiled by your optimization engine.")

    top_5_opportunities = reductionanalysis.get_top_reduction_opportunities(resources_data, top_n=5)

    # Format the table entries into clean UI expandable card widgets
    for opp in top_5_opportunities:
        if opp.get('opportunity_type') != "None":
            priority = opp.get('priority', 'Low')
            badge = "🚨 CRITICAL PRIORITY" if priority == "Critical" else "⚠️ HIGH PRIORITY" if priority == "High" else "⚡ MEDIUM PRIORITY"
                
            with st.expander(f"{badge} | {opp.get('name')} — Potential Savings: {opp.get('estimated_carbon_saving_kg')} kg CO₂"):
                st.write(f"**Asset ID:** {opp.get('id')}")
                st.write(f"**Issue Category:** {opp.get('opportunity_type')}")
                st.info(f"**Recommended Action Plan:** {opp.get('recommendation')}")