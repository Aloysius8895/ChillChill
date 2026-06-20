import json


def load_json_file(file_path: str) -> dict:
    """Loads a JSON file and returns its content as a dictionary."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        print(f"Successfully loaded data from {file_path}")
        return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return {}
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON. Please check file formatting.")
        return {}


def extract_energy_data(data: dict) -> list:
    """Extracts required resource fields from the cloud data, handles missing

    energy entries, and returns a list of dictionaries.
    """
    resources_list = data.get("resources", [])
    extracted_resources = []

    for resource in resources_list:
        # If estimatedKwhMonth is missing, default it to 0
        energy_kwh = resource.get("estimatedKwhMonth", 0)

        resource_data = {
            "id": resource.get("id"),
            "name": resource.get("name"),
            "type": resource.get("type"),
            "service": resource.get("service"),
            "region": resource.get("region"),
            "energy_kwh_month": energy_kwh,  # Renamed attribute
            "monthlyCostUsd": resource.get("monthlyCostUsd"),
            "cpuUtilizationPct": resource.get("cpuUtilizationPct"),
            "idleDays": resource.get("idleDays"),
            "regionFlexible": resource.get("regionFlexible"),
        }
        extracted_resources.append(resource_data)

    return extracted_resources


def calculate_total_energy(resources: list) -> float:
    """Calculates the sum of all monthly energy usage across all resources."""
    total_energy = sum(resource["energy_kwh_month"] for resource in resources)
    return total_energy


def get_top_energy_resources(resources: list, top_n: int = 5) -> list:
    """Identifies the top N highest energy-consuming resources using sorting."""
    # Sort the list of dictionaries by 'energy_kwh_month' in descending order
    sorted_resources = sorted(
        resources, key=lambda x: x["energy_kwh_month"], reverse=True
    )
    return sorted_resources[:top_n]


def print_resource_table(resources: list, title: str):
    """Helper function to print a beautifully formatted table using pure Python."""
    print("\n" + "=" * 95)
    print(f" {title.upper()} ".center(95, "="))
    print("=" * 95)

    # Define standard column widths for clean alignment
    # < means left-aligned, > means right-aligned
    header_format = (
        "{:<20} | {:<20} | {:<15} | {:<10} | {:<15} | {:>10}"
    )
    row_format = "{:<20} | {:<20} | {:<15} | {:<10} | {:<15} | {:>10}"

    # Print Header
    print(
        header_format.format(
            "ID", "Name", "Type", "Service", "Region", "Energy (kWh)"
        )
    )
    print("-" * 95)

    # Print Rows
    for res in resources:
        print(
            row_format.format(
                str(res["id"]),
                str(res["name"]),
                str(res["type"]),
                str(res["service"]),
                str(res["region"]),
                res["energy_kwh_month"],
            )
        )
    print("=" * 95)


# --- Main Execution Pipeline ---
if __name__ == "__main__":
    # Define the file name containing your Hilti cloud dataset
    FILE_NAME = "hilti-cloud-data (2).json"

    # Step 1: Load the raw JSON file
    cloud_data = load_json_file(FILE_NAME)

    if cloud_data:
        # Step 2: Extract data into a list of dictionaries
        resources_data = extract_energy_data(cloud_data)

        # Step 3: Print the main inventory table
        print_resource_table(
            resources_data, title="ConstructGuard AI: Resource Energy Summary"
        )

        # Step 4: Calculate Metrics
        total_monthly_energy = calculate_total_energy(resources_data)
        top_5_consumers = get_top_energy_resources(resources_data, top_n=5)

        # Step 5: Print Insights Summary
        print(f"\n⚡ Total Estimated Monthly Energy Usage: {total_monthly_energy} kWh")

        # Step 6: Print Top Consumers Table
        print_resource_table(
            top_5_consumers, title="Top 5 Highest Energy-Consuming Resources"
        )