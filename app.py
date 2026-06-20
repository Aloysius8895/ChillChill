import importlib.util
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Resource Efficiency Engine",
    page_icon="cloud",
    layout="wide",
    initial_sidebar_state="expanded",
)


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent if (APP_DIR.parent / "Resource Efficiency Engine.py").exists() else APP_DIR
ENGINE_FILE = PROJECT_ROOT / "Resource Efficiency Engine.py"
DATA_FILE = PROJECT_ROOT / "hilti-cloud-data (3).json"

CLASSIFICATION_COLORS = {
    "Efficient": "#22c55e",
    "Idle": "#ef4444",
    "Underutilized": "#f59e0b",
    "Overloaded": "#dc2626",
    "Overprovisioned": "#8b5cf6",
    "Mixed/Unclassified": "#64748b",
}


def load_backend():
    spec = importlib.util.spec_from_file_location("resource_efficiency_engine", ENGINE_FILE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to import backend from {ENGINE_FILE}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ResourceEfficiencyEngine, module.load_resources_from_json


@st.cache_data(show_spinner=False)
def load_dashboard_data():
    ResourceEfficiencyEngine, load_resources_from_json = load_backend()
    normalized_resources = load_resources_from_json(str(DATA_FILE))

    engine = ResourceEfficiencyEngine()
    analysis = engine.analyze_resources(normalized_resources)

    analyzed_by_id = {
        resource["resource_id"]: resource
        for resource in analysis["resources"]
    }

    rows = []
    for resource in normalized_resources:
        analyzed = analyzed_by_id[resource["resource_id"]]
        rows.append(
            {
                "Resource ID": resource["resource_id"],
                "Resource Type": resource["resource_type"],
                "CPU Usage %": round(resource["cpu_usage_percent"], 1),
                "Memory Usage %": round(resource["memory_usage_percent"], 1),
                "Storage Usage %": round(resource["storage_usage_percent"], 1),
                "Activity Level": resource["activity_level"].replace("_", " ").title(),
                "Classification": analyzed["classification"],
                "Efficiency Score": analyzed["efficiency_score"],
                "CPU Status": analyzed["cpu_status"],
                "Memory Status": analyzed["memory_status"],
                "Storage Status": analyzed["storage_status"],
                "Activity Status": analyzed["activity_status"],
            }
        )

    return pd.DataFrame(rows), analysis["summary"]


def efficiency_zone(score):
    if score < 40:
        return "Poor", "#ef4444"
    if score < 70:
        return "Moderate", "#f59e0b"
    return "Efficient", "#22c55e"


def make_efficiency_gauge(score):
    zone, color = efficiency_zone(score)
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "System Efficiency Score", "font": {"size": 24, "color": "#e5e7eb"}},
            number={"suffix": " / 100", "font": {"size": 48, "color": "#f8fafc"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#94a3b8"},
                "bar": {"color": color, "thickness": 0.22},
                "bgcolor": "#111827",
                "borderwidth": 1,
                "bordercolor": "#334155",
                "steps": [
                    {"range": [0, 40], "color": "rgba(239, 68, 68, 0.35)"},
                    {"range": [40, 70], "color": "rgba(245, 158, 11, 0.35)"},
                    {"range": [70, 100], "color": "rgba(34, 197, 94, 0.35)"},
                ],
                "threshold": {
                    "line": {"color": "#f8fafc", "width": 4},
                    "thickness": 0.75,
                    "value": score,
                },
            },
            domain={"x": [0, 1], "y": [0, 1]},
        )
    ).update_layout(
        height=360,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=50, r=30, b=10, l=30),
        annotations=[
            dict(
                text=zone,
                x=0.5,
                y=0.08,
                showarrow=False,
                font=dict(size=18, color=color),
            )
        ],
    )


def make_classification_pie(df):
    counts = (
        df["Classification"]
        .value_counts()
        .reindex(CLASSIFICATION_COLORS.keys(), fill_value=0)
        .reset_index()
    )
    counts.columns = ["Classification", "Count"]
    counts = counts[counts["Count"] > 0]

    fig = px.pie(
        counts,
        names="Classification",
        values="Count",
        color="Classification",
        color_discrete_map=CLASSIFICATION_COLORS,
        hole=0.45,
    )
    fig.update_traces(
        texttemplate="%{label}<br>%{percent} (%{value})",
        textposition="inside",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
    )
    fig.update_layout(
        title="Resource Classifications",
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        legend=dict(orientation="h", y=-0.1),
        margin=dict(t=60, r=20, b=50, l=20),
    )
    return fig


def make_cpu_memory_scatter(df):
    fig = px.scatter(
        df,
        x="CPU Usage %",
        y="Memory Usage %",
        color="Classification",
        color_discrete_map=CLASSIFICATION_COLORS,
        size="Efficiency Score",
        size_max=18,
        hover_data={
            "Resource ID": True,
            "Resource Type": True,
            "Efficiency Score": ":.1f",
            "Classification": True,
            "CPU Usage %": ":.1f",
            "Memory Usage %": ":.1f",
        },
    )
    fig.update_layout(
        title="CPU vs Memory Utilization",
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.55)",
        font_color="#e5e7eb",
        xaxis=dict(range=[-2, 100], gridcolor="rgba(148,163,184,0.16)", zeroline=False),
        yaxis=dict(range=[-2, 100], gridcolor="rgba(148,163,184,0.16)", zeroline=False),
        legend=dict(orientation="h", y=-0.18),
        margin=dict(t=60, r=20, b=70, l=20),
    )
    return fig


def style_resource_table(df):
    def highlight_low_efficiency(row):
        score = row["Efficiency Score"]
        if score < 40:
            return ["background-color: rgba(239, 68, 68, 0.22); color: #fee2e2"] * len(row)
        if score < 70:
            return ["background-color: rgba(245, 158, 11, 0.14); color: #fef3c7"] * len(row)
        return [""] * len(row)

    def score_color(value):
        _, color = efficiency_zone(value)
        return f"color: {color}; font-weight: 700"

    return (
        df.style
        .apply(highlight_low_efficiency, axis=1)
        .map(score_color, subset=["Efficiency Score"])
        .format(
            {
                "CPU Usage %": "{:.1f}",
                "Memory Usage %": "{:.1f}",
                "Storage Usage %": "{:.1f}",
                "Efficiency Score": "{:.1f}",
            }
        )
    )


def recommendations_for(row):
    classification = row["Classification"]
    resource_type = row["Resource Type"]
    resource_id = row["Resource ID"]
    score = row["Efficiency Score"]
    storage = row["Storage Usage %"]

    if classification == "Idle":
        if resource_type == "vm":
            return f"Shut down idle VM `{resource_id}` or schedule it outside business hours."
        if "storage" in resource_type:
            return f"Archive unused storage resource `{resource_id}` and review retention policy."
        return f"Decommission or pause idle resource `{resource_id}`."

    if classification == "Overprovisioned":
        return f"Reduce overallocated memory or right-size `{resource_id}`."

    if classification == "Underutilized":
        return f"Right-size `{resource_id}` to a smaller tier based on observed CPU and memory demand."

    if classification == "Overloaded":
        return f"Scale `{resource_id}` or rebalance workload before performance risk increases."

    if score < 70 and storage < 30:
        return f"Review `{resource_id}` for low storage usage and possible consolidation."

    return None


st.markdown(
    """
    <style>
      .stApp {
        background:
          radial-gradient(circle at top left, rgba(14, 165, 233, 0.13), transparent 32rem),
          linear-gradient(135deg, #020617 0%, #0f172a 48%, #111827 100%);
        color: #e5e7eb;
      }
      [data-testid="stSidebar"] {
        background: #020617;
        border-right: 1px solid rgba(148, 163, 184, 0.18);
      }
      div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.76);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 8px;
        padding: 1rem;
      }
      .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
      }
      .dashboard-card {
        background: rgba(15, 23, 42, 0.72);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 8px;
        padding: 1rem;
      }
      h1, h2, h3 {
        color: #f8fafc;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


try:
    df, summary = load_dashboard_data()
except Exception as exc:
    st.error(f"Unable to load Resource Efficiency Engine data: {exc}")
    st.stop()


st.sidebar.title("Filters")
resource_types = sorted(df["Resource Type"].unique())
classifications = sorted(df["Classification"].unique())

selected_types = st.sidebar.multiselect(
    "Resource type",
    options=resource_types,
    default=resource_types,
)
selected_classifications = st.sidebar.multiselect(
    "Classification",
    options=classifications,
    default=classifications,
)
minimum_score = st.sidebar.slider(
    "Minimum efficiency score",
    min_value=0,
    max_value=100,
    value=0,
    step=5,
)

filtered_df = df[
    df["Resource Type"].isin(selected_types)
    & df["Classification"].isin(selected_classifications)
    & (df["Efficiency Score"] >= minimum_score)
].copy()


st.title("Resource Efficiency Engine")
st.caption("Cloud optimization dashboard powered by the Python backend analysis engine")

metric_cols = st.columns(4)
metric_cols[0].metric("Total Resources", summary["total_resources"])
metric_cols[1].metric("Idle Resources", summary["idle_resources"])
metric_cols[2].metric("Overprovisioned", summary["overprovisioned_resources"])
metric_cols[3].metric("Visible After Filters", len(filtered_df))


st.plotly_chart(
    make_efficiency_gauge(summary["average_efficiency_score"]),
    use_container_width=True,
    config={"displayModeBar": False},
)


left_col, right_col = st.columns(2)
with left_col:
    st.plotly_chart(
        make_classification_pie(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with right_col:
    st.plotly_chart(
        make_cpu_memory_scatter(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )


st.subheader("Resource Details")
search_query = st.text_input(
    "Search resources",
    placeholder="Search by resource ID, type, activity level, or classification",
)

table_df = filtered_df.copy()
if search_query:
    query = search_query.strip().lower()
    table_df = table_df[
        table_df.astype(str).apply(
            lambda column: column.str.lower().str.contains(query, regex=False)
        ).any(axis=1)
    ]

display_columns = [
    "Resource ID",
    "Resource Type",
    "CPU Usage %",
    "Memory Usage %",
    "Storage Usage %",
    "Activity Level",
    "Classification",
    "Efficiency Score",
]

st.dataframe(
    style_resource_table(table_df[display_columns]),
    use_container_width=True,
    height=520,
    column_config={
        "Efficiency Score": st.column_config.ProgressColumn(
            "Efficiency Score",
            help="Weighted CPU, memory, storage, and activity score",
            min_value=0,
            max_value=100,
            format="%.1f",
        )
    },
)


st.subheader("Optimization Recommendations")
recommendation_rows = table_df.sort_values("Efficiency Score").head(12)
recommendations = [
    recommendation
    for _, row in recommendation_rows.iterrows()
    if (recommendation := recommendations_for(row)) is not None
]

if recommendations:
    for recommendation in recommendations:
        st.warning(recommendation)
else:
    st.success("No urgent optimization recommendations for the current filter set.")


st.caption(
    f"Loaded `{DATA_FILE.name}` and analyzed it with `ResourceEfficiencyEngine.analyze_resources()`."
)
