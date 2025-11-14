#!/usr/bin/env python3
"""
generate_data.py
Synthetic logistics data generator for Vehicles, Facilities, and Shipments.
Covers 7 years by default and supports scalable parameters.

Author: OpenAI GPT-5
Date: 2025-11-13
"""

import pandas as pd
import numpy as np
import random
import argparse
from faker import Faker
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, asin
import os

fake = Faker()

# -------------------------------------------------------
# Utility: haversine distance (km)
# -------------------------------------------------------


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

# -------------------------------------------------------
# Main generation function
# -------------------------------------------------------


def generate_data(
    num_vehicles=300,
    num_facilities=80,
    num_shipments=600000,
    years=7,
    output_prefix="logistics"
):
    Faker.seed(42)
    random.seed(42)
    np.random.seed(42)

    start_date = datetime.now() - timedelta(days=years * 365)
    end_date = datetime.now()

    # ---------------------------------------------------
    # 1. Generate Vehicles
    # ---------------------------------------------------
    manufacturers = ["Volvo", "Mercedes",
                     "Scania", "MAN", "DAF", "Iveco", "Renault"]
    vehicles = []
    for i in range(1, num_vehicles + 1):
        vehicles.append({
            "VehicleID": i,
            "Manufacturer": random.choice(manufacturers),
            "ModelYear": random.randint(2010, 2025),
            "GrossWeight": round(random.uniform(8000, 40000), 2)
        })
    df_vehicles = pd.DataFrame(vehicles)

    # ---------------------------------------------------
    # 2. Generate Facilities (with City, Region, Country)
    # ---------------------------------------------------
    countries = ["USA", "Canada", "Germany", "France", "UK",
                 "Italy", "Spain", "Netherlands", "Poland", "Sweden"]
    facilities = []
    for i in range(1, num_facilities + 1):
        country = random.choice(countries)
        city = fake.city()
        region = fake.state()
        facilities.append({
            "FacilityID": i,
            "FacilityName": f"{city} Logistics Hub",
            "Address": fake.address().replace("\n", ", "),
            "City": city,
            "Region": region,
            "Country": country,
            "Latitude": round(random.uniform(-60, 75), 6),
            "Longitude": round(random.uniform(-150, 150), 6)
        })
    df_facilities = pd.DataFrame(facilities)

    # ---------------------------------------------------
    # 3. Generate Shipments
    # ---------------------------------------------------
    shipments = []
    for i in range(1, num_shipments + 1):
        vehicle = random.choice(df_vehicles["VehicleID"].tolist())

        # Enforce source ≠ receiver
        src, dst = random.sample(df_facilities["FacilityID"].tolist(), 2)

        source = df_facilities.loc[df_facilities["FacilityID"] == src].iloc[0]
        receiver = df_facilities.loc[df_facilities["FacilityID"]
                                     == dst].iloc[0]

        distance_km = haversine(
            source["Latitude"], source["Longitude"],
            receiver["Latitude"], receiver["Longitude"]
        )

        # Random shipment datetime in the range
        ship_datetime = fake.date_time_between(
            start_date=start_date, end_date=end_date)
        pickup_time = ship_datetime + timedelta(hours=random.randint(1, 6))
        transit_days = max(0.2, np.random.normal(distance_km / 500, 0.5))
        delivery_time = pickup_time + timedelta(days=transit_days)

        status = random.choices(
            ["Delivered", "In Transit", "Delayed", "Cancelled"],
            weights=[0.7, 0.15, 0.1, 0.05],
            k=1
        )[0]

        # If cancelled, remove delivery time
        if status == "Cancelled":
            delivery_time = None

        cost = round(distance_km * random.uniform(0.8, 1.8) +
                     random.uniform(100, 1000), 2)

        route_type = "Domestic" if source["Country"] == receiver["Country"] else "International"
        route_key = f"{source['FacilityID']}_{receiver['FacilityID']}"

        shipments.append({
            "ShipmentID": i,
            "VehicleID": vehicle,
            "SourceFacilityID": source["FacilityID"],
            "ReceiverFacilityID": receiver["FacilityID"],
            "ShipmentDateTime": ship_datetime,
            "PickupTime": pickup_time,
            "DeliveryTime": delivery_time,
            "Status": status,
            "Cost": cost,
            "TransitTimeDays": round(transit_days, 2),
            "DistanceKm": round(distance_km, 3),
            "RouteType": route_type,
            "RouteKey": route_key
        })

    df_shipments = pd.DataFrame(shipments)

    # ---------------------------------------------------
    # 4. Save to CSVs
    # ---------------------------------------------------
    os.makedirs("data", exist_ok=True)
    vehicles_path = f"data/{output_prefix}_vehicles.csv"
    facilities_path = f"data/{output_prefix}_facilities.csv"
    shipments_path = f"data/{output_prefix}_shipments.csv"

    df_vehicles.to_csv(vehicles_path, index=False)
    df_facilities.to_csv(facilities_path, index=False)
    df_shipments.to_csv(shipments_path, index=False)

    print(f"✅ Data generated successfully!")
    print(f"Vehicles:   {vehicles_path} ({len(df_vehicles)} rows)")
    print(f"Facilities: {facilities_path} ({len(df_facilities)} rows)")
    print(f"Shipments:  {shipments_path} ({len(df_shipments)} rows)")


# -------------------------------------------------------
# CLI entrypoint
# -------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate synthetic logistics data for analysis.")
    parser.add_argument("--vehicles", type=int, default=300,
                        help="Number of vehicles to generate")
    parser.add_argument("--facilities", type=int, default=80,
                        help="Number of facilities to generate")
    parser.add_argument("--shipments", type=int, default=600000,
                        help="Number of shipments to generate")
    parser.add_argument("--years", type=int, default=7,
                        help="Number of years of historical data")
    parser.add_argument("--output-prefix", type=str,
                        default="logistics", help="Prefix for output files")
    args = parser.parse_args()

    generate_data(
        num_vehicles=args.vehicles,
        num_facilities=args.facilities,
        num_shipments=args.shipments,
        years=args.years,
        output_prefix=args.output_prefix
    )