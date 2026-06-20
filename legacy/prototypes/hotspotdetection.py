"""ConstructGuard AI - Carbon Hotspot Detection Module."""


def detect_carbon_hotspots(resources: list) -> list:
    """Evaluates each resource's carbon emissions and assigns a severity hotspot level

    (Critical, High, Medium, Low), then returns the list sorted by emissions.
    """
    for resource in resources:
        carbon = resource.get("carbon_kg_month", 0)

        # 1. Determine the hotspot severity level based on carbon thresholds
        if carbon > 100:
            level = "Critical"
        elif 50 <= carbon <= 100:
            level = "High"
        elif 20 <= carbon < 50:
            level = "Medium"
        else:
            level = "Low"

        # 2. Inject the new field into the resource dictionary
        resource["hotspot_level"] = level

    # 3. Sort resources by carbon_kg_month in descending order (highest emitter first)
    sorted_resources = sorted(
        resources, key=lambda x: x.get("carbon_kg_month", 0), reverse=True
    )

    return sorted_resources


def get_top_carbon_hotspots(resources: list, top_n: int = 5) -> list:
    """Identifies and returns the top N highest carbon-emitting resources."""
    # Since detect_carbon_hotspots already handles the sorting,
    # we can safely slice the first top_n resources from the list.
    return resources[:top_n]


def print_hotspot_table(resources: list, title: str):
    """Prints a beautifully aligned terminal table showing tracked hot-zones."""
    print("\n" + "=" * 90)
    print(f" {title.upper()} ".center(90, "="))
    print("=" * 90)

    # < means left-aligned, > means right-aligned text formatting blocks
    header_format = "{:<20} | {:<20} | {:<15} | {:<15} | {:>12} | {:^15}"
    row_format = "{:<20} | {:<20} | {:<15} | {:<15} | {:>12} | {:^15}"

    # Print Table Header
    print(
        header_format.format(
            "ID", "Name", "Type", "Region", "Carbon (kg)", "Hotspot Level"
        )
    )
    print("-" * 90)

    # Print Data Rows
    for res in resources:
        print(
            row_format.format(
                str(res.get("id")),
                str(res.get("name")),
                str(res.get("type")),
                str(res.get("region")),
                res.get("carbon_kg_month", 0),
                res.get("hotspot_level", "Unknown"),
            )
        )
    print("=" * 90)