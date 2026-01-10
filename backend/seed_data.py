#!/usr/bin/env python3
"""
Database Seeding Script
Loads sample data from CSV files in data/ folder into the database.
"""
import csv
import json
import os
import random
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from automotive_service.models.customer import Customer
from automotive_service.models.service_center import ServiceCenter, Technician


def load_customers(csv_path):
    """Load customers from CSV file"""
    count = 0
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip if customer already exists
            if Customer.query.get(row['cid']):
                continue
            
            customer = Customer(
                id=row['cid'],
                name=row['name'],
                phone=row['phone'],
                address=row['address'],
                location_human=row['location_human'],
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                vehicle_brand=row['vehicle_brand'],
                vehicle_model=row['vehicle_model'],
                fuel_type=row['fuel_type'],
                car_number=row['car_number'],
                vin=row['vin'],
                warranty_years_remaining=int(row['warranty_years_remaining'])
            )
            db.session.add(customer)
            count += 1
    
    db.session.commit()
    return count


def load_service_centers(csv_path):
    """Load service centers from CSV file"""
    count = 0
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip if service center already exists
            if ServiceCenter.query.get(row['scid']):
                continue
            
            service_center = ServiceCenter(
                id=row['scid'],
                name=row['name'],
                location_human=row['location_human'],
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
            )
            db.session.add(service_center)
            count += 1
    
    db.session.commit()
    return count


def generate_technicians():
    """Generate technicians for each service center"""
    specializations = [
        ['Oil Change', 'General Maintenance'],
        ['AC', 'Heating'],
        ['Tires', 'Alignment'],
        ['Body Work', 'Paint'],
        ['Engine', 'Transmission'],
        ['Brakes', 'Suspension'],
        ['Electrical', 'Diagnostics'],
        ['Exhaust', 'Emissions'],
    ]
    
    first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emily', 'Robert', 'Maria', 'James', 'Anna']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Martinez', 'Wilson']
    
    count = 0
    service_centers = ServiceCenter.query.all()
    
    for sc in service_centers:
        # Check if technicians already exist for this service center
        existing = Technician.query.filter_by(service_center_id=sc.id).count()
        if existing > 0:
            continue
        
        # Generate 1-3 technicians per service center
        num_techs = random.randint(1, 3)
        for i in range(num_techs):
            tech_id = f"TECH-{str(count + 1).zfill(4)}"
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            specs = random.choice(specializations)
            
            technician = Technician(
                employee_id=tech_id,
                service_center_id=sc.id,
                name=name,
                specializations=json.dumps(specs),
                availability_status='AVAILABLE',
                current_workload=0,
                max_workload=3
            )
            db.session.add(technician)
            count += 1
    
    db.session.commit()
    return count


def main():
    """Main seeding function"""
    print("=" * 60)
    print("Database Seeding Script")
    print("=" * 60)
    
    base_path = os.path.join(os.path.dirname(__file__), 'data')
    customers_csv = os.path.join(base_path, 'customers.csv')
    service_centers_csv = os.path.join(base_path, 'service_centres.csv')
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        print(f"\n[1/3] Loading customers from {customers_csv}...")
        customer_count = load_customers(customers_csv)
        print(f"      ✓ Loaded {customer_count} customers")
        
        print(f"\n[2/3] Loading service centers from {service_centers_csv}...")
        sc_count = load_service_centers(service_centers_csv)
        print(f"      ✓ Loaded {sc_count} service centers")
        
        print("\n[3/3] Generating technicians...")
        tech_count = generate_technicians()
        print(f"      ✓ Generated {tech_count} technicians")
        
        print("\n" + "=" * 60)
        print("Database seeding complete!")
        print(f"  - Customers: {Customer.query.count()}")
        print(f"  - Service Centers: {ServiceCenter.query.count()}")
        print(f"  - Technicians: {Technician.query.count()}")
        print("=" * 60)


if __name__ == '__main__':
    main()

