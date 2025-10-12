#!/usr/bin/env python3
"""
Script to create a dummy cars table with 1000 records for testing SQL generation.
"""

import random
import json
import os
from dotenv import load_dotenv
from database.postgres_connection import get_db_connection

# Load environment variables
load_dotenv()

# Car data templates
CAR_BRANDS = [
    "Toyota", "Honda", "Ford", "Chevrolet", "BMW", "Mercedes-Benz", "Audi", "Nissan", 
    "Hyundai", "Kia", "Volkswagen", "Mazda", "Subaru", "Lexus", "Acura", "Infiniti",
    "Genesis", "Volvo", "Jaguar", "Land Rover", "Porsche", "Ferrari", "Lamborghini",
    "Maserati", "Bentley", "Rolls-Royce", "Tesla", "Rivian", "Lucid"
]

CAR_MODELS = {
    "Toyota": ["Camry", "Corolla", "RAV4", "Highlander", "Prius", "Avalon", "Sienna", "Tacoma", "Tundra", "4Runner"],
    "Honda": ["Civic", "Accord", "CR-V", "Pilot", "Fit", "HR-V", "Passport", "Ridgeline", "Insight", "Odyssey"],
    "Ford": ["F-150", "Escape", "Explorer", "Mustang", "Focus", "Edge", "Expedition", "Ranger", "Bronco", "Transit"],
    "BMW": ["3 Series", "5 Series", "7 Series", "X3", "X5", "X7", "Z4", "i3", "i8", "M3"],
    "Mercedes-Benz": ["C-Class", "E-Class", "S-Class", "GLC", "GLE", "GLS", "A-Class", "CLA", "G-Class", "AMG GT"],
    "Tesla": ["Model S", "Model 3", "Model X", "Model Y", "Roadster", "Cybertruck", "Semi"],
    "Audi": ["A3", "A4", "A6", "A8", "Q3", "Q5", "Q7", "Q8", "TT", "R8"],
    "Nissan": ["Altima", "Sentra", "Rogue", "Murano", "Pathfinder", "Frontier", "Titan", "370Z", "GT-R", "Leaf"],
    "Hyundai": ["Elantra", "Sonata", "Tucson", "Santa Fe", "Palisade", "Kona", "Veloster", "Genesis", "Ioniq", "Nexo"],
    "Kia": ["Forte", "Optima", "Sorento", "Telluride", "Soul", "Niro", "Stinger", "Cadenza", "Sedona", "Sportage"]
}

ENGINE_TYPES = ["V6", "V8", "I4", "I6", "Electric", "Hybrid", "Turbo I4", "V12", "Rotary", "Diesel"]
TRANSMISSION_TYPES = ["Automatic", "Manual", "CVT", "Semi-Automatic", "Dual-Clutch"]
FUEL_TYPES = ["Gasoline", "Diesel", "Electric", "Hybrid", "Plug-in Hybrid", "E85", "CNG"]
DRIVE_TYPES = ["FWD", "RWD", "AWD", "4WD"]

COLORS = [
    "White", "Black", "Silver", "Gray", "Red", "Blue", "Green", "Brown", "Gold", "Orange",
    "Yellow", "Purple", "Pink", "Beige", "Champagne", "Pearl White", "Metallic Black"
]

def generate_car_data():
    """Generate a single car record with realistic data."""
    brand = random.choice(CAR_BRANDS)
    model = random.choice(CAR_MODELS.get(brand, ["Unknown"]))
    
    # Generate realistic year (2015-2024)
    year = random.randint(2015, 2024)
    
    # Generate realistic price based on brand and year
    base_price = random.randint(15000, 80000)
    if brand in ["Ferrari", "Lamborghini", "Rolls-Royce", "Bentley"]:
        base_price = random.randint(200000, 500000)
    elif brand in ["BMW", "Mercedes-Benz", "Audi", "Porsche", "Tesla"]:
        base_price = random.randint(40000, 150000)
    
    # Adjust price based on year
    year_factor = 1 + (year - 2015) * 0.05
    price = int(base_price * year_factor)
    
    # Generate mileage (lower for newer cars)
    if year >= 2022:
        mileage = random.randint(0, 15000)
    elif year >= 2020:
        mileage = random.randint(5000, 50000)
    else:
        mileage = random.randint(10000, 120000)
    
    # Generate engine size
    if brand in ["Tesla", "Rivian", "Lucid"]:
        engine_size = random.choice([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # Electric cars
    else:
        engine_size = round(random.uniform(1.5, 6.5), 1)
    
    # Generate horsepower
    if brand in ["Tesla", "Rivian", "Lucid"]:
        horsepower = random.randint(300, 1000)  # Electric cars have high HP
    else:
        horsepower = random.randint(100, 700)
    
    # Generate fuel efficiency
    if brand in ["Tesla", "Rivian", "Lucid"]:
        mpg = 0  # Electric cars don't use MPG
    else:
        mpg = random.randint(15, 45)
    
    return {
        "id": None,  # Will be auto-generated
        "brand": brand,
        "model": model,
        "year": year,
        "price": price,
        "mileage": mileage,
        "engine_type": random.choice(ENGINE_TYPES),
        "engine_size": engine_size,
        "horsepower": horsepower,
        "transmission": random.choice(TRANSMISSION_TYPES),
        "fuel_type": random.choice(FUEL_TYPES),
        "mpg": mpg,
        "drive_type": random.choice(DRIVE_TYPES),
        "color": random.choice(COLORS),
        "condition": random.choice(["Excellent", "Good", "Fair", "Poor"]),
        "accidents": random.randint(0, 3),
        "owners": random.randint(1, 4),
        "warranty": random.choice([True, False]),
        "features": json.dumps(random.sample([
            "Leather Seats", "Sunroof", "Navigation", "Bluetooth", "Backup Camera",
            "Heated Seats", "Cooled Seats", "Premium Sound", "Keyless Entry",
            "Remote Start", "Lane Assist", "Adaptive Cruise", "Blind Spot Monitor",
            "Parking Sensors", "LED Headlights", "Alloy Wheels", "Tinted Windows"
        ], random.randint(3, 8))),
        "description": f"Beautiful {year} {brand} {model} in {random.choice(COLORS).lower()} with {random.choice(ENGINE_TYPES).lower()} engine. {random.choice(['Well maintained', 'Single owner', 'Garage kept', 'Recent service', 'Low miles'])}."
    }

def create_cars_table():
    """Create the cars table with proper schema."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS cars (
        id SERIAL PRIMARY KEY,
        brand VARCHAR(50) NOT NULL,
        model VARCHAR(50) NOT NULL,
        year INTEGER NOT NULL,
        price INTEGER NOT NULL,
        mileage INTEGER NOT NULL,
        engine_type VARCHAR(20) NOT NULL,
        engine_size DECIMAL(3,1),
        horsepower INTEGER NOT NULL,
        transmission VARCHAR(20) NOT NULL,
        fuel_type VARCHAR(20) NOT NULL,
        mpg INTEGER,
        drive_type VARCHAR(10) NOT NULL,
        color VARCHAR(30) NOT NULL,
        condition VARCHAR(20) NOT NULL,
        accidents INTEGER DEFAULT 0,
        owners INTEGER DEFAULT 1,
        warranty BOOLEAN DEFAULT FALSE,
        features TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_cars_brand ON cars(brand);
    CREATE INDEX IF NOT EXISTS idx_cars_model ON cars(model);
    CREATE INDEX IF NOT EXISTS idx_cars_year ON cars(year);
    CREATE INDEX IF NOT EXISTS idx_cars_price ON cars(price);
    CREATE INDEX IF NOT EXISTS idx_cars_fuel_type ON cars(fuel_type);
    CREATE INDEX IF NOT EXISTS idx_cars_condition ON cars(condition);
    """
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(create_table_sql)
            conn.commit()
            print("Cars table created successfully")

def insert_cars_data(num_cars=1000):
    """Insert dummy car data into the cars table."""
    print(f"Generating {num_cars} car records...")
    
    cars_data = []
    for i in range(num_cars):
        car = generate_car_data()
        cars_data.append(car)
        
        if (i + 1) % 100 == 0:
            print(f"Generated {i + 1} cars...")
    
    # Prepare insert statement
    insert_sql = """
    INSERT INTO cars (brand, model, year, price, mileage, engine_type, engine_size, 
                     horsepower, transmission, fuel_type, mpg, drive_type, color, 
                     condition, accidents, owners, warranty, features, description)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Clear existing data
            cursor.execute("DELETE FROM cars")
            print("Cleared existing cars data")
            
            # Insert new data in batches
            batch_size = 100
            for i in range(0, len(cars_data), batch_size):
                batch = cars_data[i:i + batch_size]
                batch_values = []
                
                for car in batch:
                    batch_values.append((
                        car["brand"], car["model"], car["year"], car["price"], car["mileage"],
                        car["engine_type"], car["engine_size"], car["horsepower"], car["transmission"],
                        car["fuel_type"], car["mpg"], car["drive_type"], car["color"], car["condition"],
                        car["accidents"], car["owners"], car["warranty"], car["features"], car["description"]
                    ))
                
                cursor.executemany(insert_sql, batch_values)
                print(f"Inserted batch {i//batch_size + 1}/{(len(cars_data) + batch_size - 1)//batch_size}")
            
            conn.commit()
            print(f"Successfully inserted {len(cars_data)} car records")

def verify_data():
    """Verify the inserted data."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Count total records
            cursor.execute("SELECT COUNT(*) FROM cars")
            count = cursor.fetchone()[0]
            print(f"Total cars in database: {count}")
            
            # Show some sample data
            cursor.execute("SELECT brand, model, year, price, engine_type, fuel_type FROM cars LIMIT 5")
            samples = cursor.fetchall()
            print("\nSample records:")
            for sample in samples:
                print(f"  {sample[0]} {sample[1]} {sample[2]} - ${sample[3]:,} - {sample[4]} {sample[5]}")
            
            # Show statistics
            cursor.execute("SELECT brand, COUNT(*) as count FROM cars GROUP BY brand ORDER BY count DESC LIMIT 10")
            brands = cursor.fetchall()
            print("\nTop brands by count:")
            for brand, count in brands:
                print(f"  {brand}: {count}")
            
            cursor.execute("SELECT MIN(price), MAX(price), AVG(price) FROM cars")
            price_stats = cursor.fetchone()
            print(f"\nPrice range: ${price_stats[0]:,} - ${price_stats[1]:,} (avg: ${price_stats[2]:,.0f})")
            
            cursor.execute("SELECT MIN(year), MAX(year) FROM cars")
            year_range = cursor.fetchone()
            print(f"Year range: {year_range[0]} - {year_range[1]}")

if __name__ == "__main__":
    print("Creating dummy cars database...")
    
    try:
        # Create table
        create_cars_table()
        
        # Insert data
        insert_cars_data(1000)
        
        # Verify data
        verify_data()
        
        print("\nDummy cars database created successfully!")
        print("\nYou can now test SQL generation with queries like:")
        print("- 'Show me all BMW cars'")
        print("- 'Find cars under $30,000'")
        print("- 'List all electric vehicles'")
        print("- 'Show me cars with V8 engines'")
        print("- 'Find red cars from 2020 or newer'")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
