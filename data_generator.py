"""
Pharma Sales Data Generator Script
Generates a realistic synthetic dataset representing pharmaceutical sales.
Produces 50,000 transaction records spanning the last 2 years (730 days).
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration Constants
NUM_ROWS = 50000
OUTPUT_FILENAME = "pharma_sales_data.csv"

# Drug catalog containing names, categories, and baseline unit prices
DRUG_CATALOG = [
    {"drug_name": "Paracetamol", "category": "Analgesics", "unit_price": 4.50},
    {"drug_name": "Ibuprofen", "category": "Analgesics", "unit_price": 6.20},
    {"drug_name": "Amoxicillin", "category": "Antibiotics", "unit_price": 18.90},
    {"drug_name": "Atorvastatin", "category": "Statins", "unit_price": 45.00},
    {"drug_name": "Metformin", "category": "Antidiabetics", "unit_price": 12.50},
    {"drug_name": "Omeprazole", "category": "Antacids", "unit_price": 15.00},
    {"drug_name": "Lisinopril", "category": "Cardiovascular", "unit_price": 22.00},
    {"drug_name": "Albuterol", "category": "Respiratory", "unit_price": 35.50},
    {"drug_name": "Amlodipine", "category": "Cardiovascular", "unit_price": 14.80},
    {"drug_name": "Levothyroxine", "category": "Thyroid", "unit_price": 28.00}
]

# Attribute Lists
REGIONS = ["North", "South", "East", "West"]
CUSTOMER_TYPES = ["Pharmacy", "Hospital", "Clinic"]
PAYMENT_METHODS = ["Cash", "Credit Card", "Insurance"]

# Distribution weights for attributes
REGION_WEIGHTS = [0.35, 0.25, 0.20, 0.20]  # North has slightly higher sales volume
CUSTOMER_WEIGHTS = [0.50, 0.30, 0.20]       # Pharmacy is most common
PAYMENT_WEIGHTS = [0.20, 0.50, 0.30]        # Credit Card is most common

def generate_random_dates(start_date, end_date, num_records):
    """
    Generates a list of sorted random datetimes between start_date and end_date.
    Includes weights to simulate business hours (higher density during daytime).
    """
    delta_seconds = int((end_date - start_date).total_seconds())
    dates = []
    
    for _ in range(num_records):
        # Select a random number of seconds from the start
        random_seconds = random.randint(0, delta_seconds)
        random_date = start_date + timedelta(seconds=random_seconds)
        
        # Adjust time of day to simulate realistic business hours (8 AM to 8 PM peak)
        hour = random_date.hour
        # If random hour falls into late night, shift it to daylight business hours with high probability
        if hour < 8 or hour > 20:
            if random.random() < 0.8:
                random_date = random_date.replace(hour=random.randint(9, 18))
                
        dates.append(random_date)
        
    dates.sort()  # Transactions naturally occur chronologically
    return dates

def generate_dataset():
    """
    Generates a DataFrame with 50,000 records of synthetic pharma sales.
    """
    print(f"Generating {NUM_ROWS} synthetic pharma sales records...")
    
    # Time frame: past 730 days up to today
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    # 1. Generate Timestamps
    sale_dates = generate_random_dates(start_date, end_date, NUM_ROWS)
    
    # 2. Pick drugs and fill in drug information
    # We assign different weights to drugs to simulate realistic market demands
    # Paracetamol & Metformin are high-volume, Atorvastatin & Amoxicillin are mid-volume
    drug_weights = [0.22, 0.15, 0.08, 0.10, 0.12, 0.10, 0.08, 0.05, 0.06, 0.04]
    selected_drugs = random.choices(DRUG_CATALOG, weights=drug_weights, k=NUM_ROWS)
    
    data = []
    for i in range(NUM_ROWS):
        drug = selected_drugs[i]
        date = sale_dates[i]
        
        # Determine attributes
        region = random.choices(REGIONS, weights=REGION_WEIGHTS, k=1)[0]
        customer_type = random.choices(CUSTOMER_TYPES, weights=CUSTOMER_WEIGHTS, k=1)[0]
        payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS, k=1)[0]
        
        # Quantity calculation:
        # Hospitals and clinics tend to order in bulk, whereas pharmacies/individuals buy smaller quantities
        if customer_type == "Hospital":
            quantity = random.randint(10, 100)
        elif customer_type == "Clinic":
            quantity = random.randint(5, 40)
        else:  # Pharmacy
            quantity = random.randint(1, 10)
            
        # Seasonal Adjustment: Respiratory and Analgesics sales spike in winter (Nov, Dec, Jan, Feb)
        month = date.month
        if drug["category"] in ["Respiratory", "Analgesics"] and month in [11, 12, 1, 2]:
            # Boost quantity by 30-50% during flu season
            quantity = int(quantity * random.uniform(1.3, 1.5))
            
        # Price fluctuations over time (slight inflation trend over 2 years)
        # Calculate how far along the timeline this date is (from 0 to 1)
        timeline_pct = (date - start_date).total_seconds() / (end_date - start_date).total_seconds()
        # Add up to 8% inflation over 2 years, plus some daily noise (+/- 2%)
        inflation_factor = 1.0 + (timeline_pct * 0.08) + random.uniform(-0.02, 0.02)
        unit_price = round(drug["unit_price"] * inflation_factor, 2)
        
        # Total Revenue calculation
        total_revenue = round(quantity * unit_price, 2)
        
        # Construct the record
        record = {
            "sale_id": i + 1,  # ID starts at 1
            "sale_date": date.strftime("%Y-%m-%d %H:%M:%S"),
            "drug_name": drug["drug_name"],
            "category": drug["category"],
            "quantity": quantity,
            "unit_price": unit_price,
            "total_revenue": total_revenue,
            "region": region,
            "customer_type": customer_type,
            "payment_method": payment_method
        }
        data.append(record)
        
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(OUTPUT_FILENAME, index=False)
    print(f"Dataset successfully generated and saved to '{OUTPUT_FILENAME}'!")
    print(f"File size: {os.path.getsize(OUTPUT_FILENAME) / (1024*1024):.2f} MB")
    print("\nDataset Summary Preview:")
    print(df.head())
    print("\nColumns and Data Types:")
    print(df.dtypes)

if __name__ == "__main__":
    generate_dataset()
