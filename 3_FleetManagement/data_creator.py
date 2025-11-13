
#!/usr/bin/env python3
"""
generate_data.py

Synthetic logistics data generator.

Creates CSVs:
 - {output_prefix}_vehicles.csv
 - {output_prefix}_facilities.csv
 - {output_prefix}_shipments.csv

Features:
 - Vehicles: VehicleID, Manufacturer, ModelYear, GrossWeight
 - Facilities: FacilityID, FacilityName, Address, City, Region, Country, Latitude, Longitude
 - Shipments: ShipmentID, VehicleID, SourceFacilityID, ReceiverFacilityID,
              ShipmentDateTime, PickupTime, DeliveryTime, Status, Cost, TransitTimeDays, DistanceKm, RouteType, RouteKey

Usage:
    python generate_data.py --vehicles 200 --facilities 50 --shipments 100000 --years 7 --output-prefix logistics_7y

Defaults chosen to cover 7 years of realistic shipment history. Adjust counts via CLI flags.
"""

import argparse
import random
import math
from datetime import datetime, timedelta
import csv
import os
from faker import Faker
import pandas as pd
import numpy as np

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

MANUFACTURERS = [
    "Volvo", "Scania", "Mercedes-Benz", "MAN", "DAF", "Ford", "Tesla", "Isuzu", "Iveco", "Renault"
]

STATUS_WEIGHTS = {
    "Delivered": 0.80,
    "In Transit": 0.10,
    "Delayed": 0.08,
    "Cancelled": 0.02
}

ROUTE_TYPES = ["Domestic", "International"]

def haversine_km(lat1, lon1, lat2, lon2):
    # returns distance in kilometers between two lat/lon points
    R = 6371.0  # Earth radius km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def weighted_choice(choices_dict):
    items = list(choices_dict.items())
    keys = [k for k, _ in items]
    weights = [w for _, w in items]
    return random.choices(keys, weights=weights, k=1)[0]

def generate_vehicles(num_vehicles, start_year_offset=15):
    vehicles = []
    current_year = datetime.now().year
    for i in range(1, num_vehicles + 1):
        manuf = random.choice(MANUFACTURERS)
        model_year = random.randint(current_year - start_year_offset, current_year)
        gross_weight = round(random.uniform(3000, 40000), 2)  # kg
        vehicles.append({
            "VehicleID": i,
            "Manufacturer": manuf,
            "ModelYear": model_year,
            "GrossWeight": gross_weight
        })
    return pd.DataFrame(vehicles)

def generate_facilities(num_facilities):
    facilities = []
    for i in range(1, num_facilities + 1):
        city = fake.city()
        region = fake.state()
        country = fake.country()
        facility_name = f"{fake.company()} Logistics Center"
        address = fake.address().replace('\n', ', ')
        # generate plausible lat/lon (Faker lat/long are global)
        latitude = float(fake.latitude())
        longitude = float(fake.longitude())
        facilities.append({
            "FacilityID": i,
            "FacilityName": facility_name,
            "Address": address,
            "City": city,
            "Region": region,
            "Country": country,
            "Latitude": round(latitude, 6),
            "Longitude": round(longitude, 6)
        })
    return pd.DataFrame(facilities)

def generate_shipments(num_shipments, vehicles_df, facilities_df, years=7, start_date=None):
    shipments = []
    start = start_date or (datetime.now() - timedelta(days=365*years))
    end = datetime.now()
    facility_ids = facilities_df["FacilityID"].tolist()
    vehicle_ids = vehicles_df["VehicleID"].tolist()

    # Precompute facility coords and countries for quick lookup
    facility_coords = facilities_df.set_index("FacilityID")[["Latitude", "Longitude"]].to_dict('index')
    facility_country = facilities_df.set_index("FacilityID")["Country"].to_dict()

    # Cost model params
    base_rate_per_km = 1.2  # currency units per km baseline
    weight_rate_factor = 0.00005  # extra per kg
    fixed_handling = 10.0

    for i in range(1, num_shipments + 1):
        vehicle_id = random.choice(vehicle_ids)
        # ensure source != receiver
        source, receiver = random.sample(facility_ids, 2)
        src = facility_coords[source]
        dst = facility_coords[receiver]
        distance_km = haversine_km(src["Latitude"], src["Longitude"], dst["Latitude"], dst["Longitude"])
        # shipment datetime uniformly distributed across the window
        total_seconds = int((end - start).total_seconds())
        offset_seconds = random.randint(0, total_seconds)
        shipment_dt = start + timedelta(seconds=offset_seconds)
        # status
        status = weighted_choice(STATUS_WEIGHTS)
        # route type
        route_type = "Domestic" if facility_country[source] == facility_country[receiver] else "International"
        # transit time model (days): base speed dependent on route type + random noise + small impact from weight
        # average speeds: domestic 60 km/day (truck), international (with intermodal) 800 km/day for air, but we'll simulate realistic truck inter-country slower
        if route_type == "Domestic":
            avg_speed_km_per_day = random.normalvariate(600, 100) / 10.0  # around 60 km/day with some variance
        else:
            # international shipments often travel longer distances and may use faster legs; set higher avg speed
            avg_speed_km_per_day = random.normalvariate(900, 200) / 10.0  # around 90 km/day

        # vehicle weight impacts speed slightly
        vehicle_weight = float(vehicles_df.loc[vehicles_df["VehicleID"] == vehicle_id, "GrossWeight"].iloc[0])
        weight_impact = 1 + ((vehicle_weight - 10000) / 100000.0)  # small factor
        expected_days = max(0.1, distance_km / max(1, avg_speed_km_per_day) * weight_impact)
        # add randomness and business rules
        transit_days = round(random.gauss(expected_days, max(0.5, expected_days * 0.15)), 2)
        # ensure non-negative
        transit_days = max(0.0, transit_days)

        # Pickup and delivery times
        pickup_time = shipment_dt
        delivery_time = None
        if status in ("Delivered", "Delayed"):
            delivery_time = pickup_time + timedelta(days=transit_days) + timedelta(hours=random.randint(0,23), minutes=random.randint(0,59))
        elif status == "Cancelled":
            delivery_time = None
        else:  # In Transit
            # if shipment_dt + transit_days < now, we may set delivery if it's in the past; else leave None
            est_delivery = pickup_time + timedelta(days=transit_days)
            if est_delivery <= datetime.now():
                delivery_time = est_delivery + timedelta(hours=random.randint(0,23))
            else:
                delivery_time = None

        # cost model (currency units)
        cost = round(
            fixed_handling +
            (base_rate_per_km * distance_km) +
            (weight_rate_factor * vehicle_weight * distance_km) +
            random.uniform(-5.0, 15.0), 2
        )
        # route key
        route_key = f"{min(source, receiver)}_{max(source, receiver)}"

        shipments.append({
            "ShipmentID": i,
            "VehicleID": vehicle_id,
            "SourceFacilityID": source,
            "ReceiverFacilityID": receiver,
            "ShipmentDateTime": shipment_dt.isoformat(sep=' '),
            "PickupTime": pickup_time.isoformat(sep=' '),
            "DeliveryTime": delivery_time.isoformat(sep=' ') if delivery_time is not None else None,
            "Status": status,
            "Cost": cost,
            "TransitTimeDays": transit_days if delivery_time is not None else None,
            "DistanceKm": round(distance_km, 3),
            "RouteType": route_type,
            "RouteKey": route_key
        })

        # progress print for very large datasets (every 100k)
        if i % 100000 == 0:
            print(f"Generated {i} shipments...")

    return pd.DataFrame(shipments)

def save_csv(df, path):
    df.to_csv(path, index=False)
    print(f"Wrote {len(df)} rows to {path}")

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic logistics data (vehicles, facilities, shipments).")
    parser.add_argument("--vehicles", type=int, default=200, help="Number of vehicles to generate.")
    parser.add_argument("--facilities", type=int, default=50, help="Number of facilities to generate.")
    parser.add_argument("--shipments", type=int, default=100000, help="Number of shipments to generate.")
    parser.add_argument("--years", type=int, default=7, help="Number of years to span (default 7).")
    parser.add_argument("--output-prefix", type=str, default="logistics_7y", help="Output file prefix.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--csv-only", action="store_true", help="Only output CSV files (default).")
    args = parser.parse_args()

    # set seeds
    random.seed(args.seed)
    np.random.seed(args.seed)
    Faker.seed(args.seed)

    print("Generating vehicles...")
    vehicles_df = generate_vehicles(args.vehicles)
    print("Generating facilities...")
    facilities_df = generate_facilities(args.facilities)
    print(f"Generating {args.shipments} shipments across {args.years} years (this may take a while)...")
    shipments_df = generate_shipments(args.shipments, vehicles_df, facilities_df, years=args.years)

    out_prefix = args.output_prefix
    out_dir = os.getcwd()
    vehicles_path = os.path.join(out_dir, f"./data/{out_prefix}_vehicles.csv")
    facilities_path = os.path.join(
        out_dir, f"./data/{out_prefix}_facilities.csv")
    shipments_path = os.path.join(
        out_dir, f"./data/{out_prefix}_shipments.csv")

    save_csv(vehicles_df, vehicles_path)
    save_csv(facilities_df, facilities_path)
    save_csv(shipments_df, shipments_path)

    print("\nDone. Files created:")
    print(f" - {vehicles_path}")
    print(f" - {facilities_path}")
    print(f" - {shipments_path}")
    print("\nYou can modify counts with CLI flags. Example:")
    print("  python generate_data.py --vehicles 500 --facilities 200 --shipments 500000 --years 7 --output-prefix mydata")

if __name__ == '__main__':
    main()
