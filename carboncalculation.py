"""ConstructGuard AI - Carbon Emission Calculation Module."""


def add_carbon_emissions(data: dict, resources: list) -> list:
    """Calculates monthly carbon emissions (in kg CO2) for each cloud resource

    based on its regional grid intensity and updates the dataset.
    """
    intensity_map = data.get("regionCarbonIntensity_gPerKWh", {})

    for resource in resources:
        region = resource.get("region")
        energy_kwh = resource.get("energy_kwh_month", 0)
        intensity = intensity_map.get(region, 0)

        # Carbon (kg) = Energy (kWh) * (Intensity (g) / 1000)
        carbon_kg = energy_kwh * (intensity / 1000)

        resource["carbon_intensity_g_per_kwh"] = intensity
        resource["carbon_kg_month"] = round(carbon_kg, 2)

    return resources


def calculate_total_carbon(resources: list) -> float:
    """Aggregates total monthly carbon emissions across all active cloud assets."""
    total_carbon = sum(resource["carbon_kg_month"] for resource in resources)
    return round(total_carbon, 2)


def get_top_carbon_emitters(resources: list, top_n: int = 5) -> list:
    """Identifies the top N assets with the highest carbon footprint."""
    sorted_emitters = sorted(
        resources, key=lambda x: x["carbon_kg_month"], reverse=True
    )
    return sorted_emitters[:top_n]


def print_carbon_table(resources: list, title: str):
    """Prints a neatly formatted, aligned terminal table for carbon accounting."""
    print("\n" + "=" * 105)
    print(f" {title.upper()} ".center(105, "="))
    print("=" * 105)

    header_format = "{:<20} | {:<20} | {:<15} | {:>12} | {:>13} | {:>12}"
    row_format = "{:<20} | {:<20} | {:<15} | {:>12} | {:>13} | {:>12}"

    print(
        header_format.format(
            "ID", "Name", "Region", "Energy (kWh)", "Intensity (g)", "Carbon (kg)"
        )
    )
    print("-" * 105)

    for res in resources:
        print(
            row_format.format(
                str(res["id"]),
                str(res["name"]),
                str(res["region"]),
                res["energy_kwh_month"],
                res["carbon_intensity_g_per_kwh"],
                res["carbon_kg_month"],
            )
        )
    print("=" * 105)