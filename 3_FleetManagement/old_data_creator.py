"""
data_generator.py
-----------------
Generates synthetic data for:
 - Vehicles
 - Facilities
 - Shipments

You can specify how many rows per table using CLI args:
    python data_generator.py --vehicles 50 --facilities 10 --shipments 5000

Default values create a realistic dataset over 5 years for analytics and ML modeling.
"""

import argparse
import random
from datetime import datetime, timedelta
import pandas as pd
# Faker is used to generate realistic facility names and addresses
from faker import Faker


fake = Faker()


def generate_vehicles(num_vehicles: int):
    vehicles = []
    for i in range(1, num_vehicles + 1):
        vehicles.append({
            "VehicleID": i,
            "Manufacturer": random.choice(["Volvo", "Scania", "Mercedes", "MAN", "DAF", "Ford", "Tesla"]),
            "ModelYear": random.randint(2010, 2025),
            "GrossWeight": round(random.uniform(5000, 40000), 2)
        })
    return pd.DataFrame(vehicles)


def generate_facilities(num_facilities: int):
    facilities = []
    for i in range(1, num_facilities + 1):
        loc = fake.location_on_land()
        facilities.append({
            "FacilityID": i,
            "FacilityName": f"{fake.company()} Logistics Center",
            "Address": fake.address().replace("\n", ", "),
            "Latitude": float(loc[0]),
            "Longitude": float(loc[1])
        })
    return pd.DataFrame(facilities)


def generate_shipments(num_shipments: int, vehicles_df: pd.DataFrame, facilities_df: pd.DataFrame):
    shipments = []
    start_date = datetime.now() - timedelta(days=5 * 365)  # 5 years ago
    for i in range(1, num_shipments + 1):
        vehicle_id = random.choice(vehicles_df["VehicleID"].tolist())
        source, receiver = random.sample(
            facilities_df["FacilityID"].tolist(), 2)
        shipment_date = start_date + timedelta(days=random.randint(0, 5 * 365))
        shipments.append({
            "ShipmentID": i,
            "VehicleID": vehicle_id,
            "SourceFacilityID": source,
            "ReceiverFacilityID": receiver,
            "ShipmentDate": shipment_date.date().isoformat()
        })
    return pd.DataFrame(shipments)


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic logistics data.")
    parser.add_argument("--vehicles", type=int, default=50,
                        help="Number of vehicles to generate.")
    parser.add_argument("--facilities", type=int, default=15,
                        help="Number of facilities to generate.")
    parser.add_argument("--shipments", type=int, default=10000,
                        help="Number of shipments to generate.")
    parser.add_argument("--output-prefix", type=str,
                        default="logistics_data", help="Output file prefix.")

    args = parser.parse_args()

    # Generate datasets
    print("Generating vehicles...")
    vehicles_df = generate_vehicles(args.vehicles)

    print("Generating facilities...")
    facilities_df = generate_facilities(args.facilities)

    print("Generating shipments...")
    shipments_df = generate_shipments(
        args.shipments, vehicles_df, facilities_df)

    # Save as CSV files
    vehicles_df.to_csv(
        f"./data/{args.output_prefix}_vehicles.csv", index=False)
    facilities_df.to_csv(
        f"./data/{args.output_prefix}_facilities.csv", index=False)
    shipments_df.to_csv(
        f"./data/{args.output_prefix}_shipments.csv", index=False)

    print("\n✅ Data generation complete.")
    print(
        f"Vehicles: {args.output_prefix}_vehicles.csv ({len(vehicles_df)} rows)")
    print(
        f"Facilities: {args.output_prefix}_facilities.csv ({len(facilities_df)} rows)")
    print(
        f"Shipments: {args.output_prefix}_shipments.csv ({len(shipments_df)} rows)")
    print("\nReady for analysis or ML modeling.")


if __name__ == "__main__":
    main()
