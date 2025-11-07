import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_database():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Clear existing data
    await db.users.delete_many({})
    await db.families.delete_many({})
    await db.members.delete_many({})
    await db.pricelists.delete_many({})
    await db.bills_header.delete_many({})
    await db.bills_details.delete_many({})
    
    # Seed Users (Hospital Staff)
    users = [
        {
            "username": "superadmin",
            "password": pwd_context.hash("SuperAdmin@2024"),
            "hospital_name": "System Administration",
            "role": "Admin",
            "first_login": False
        },
        {
            "username": "general_admin",
            "password": pwd_context.hash("temp_password_123"),
            "hospital_name": "General Hospital",
            "role": "Admin",
            "first_login": True
        },
        {
            "username": "general_clerk",
            "password": pwd_context.hash("password123"),
            "hospital_name": "General Hospital",
            "role": "Billing Clerk",
            "first_login": False
        },
        {
            "username": "city_admin",
            "password": pwd_context.hash("temp_password_123"),
            "hospital_name": "City Medical Center",
            "role": "Admin",
            "first_login": True
        },
        {
            "username": "city_clerk",
            "password": pwd_context.hash("password123"),
            "hospital_name": "City Medical Center",
            "role": "Billing Clerk",
            "first_login": False
        },
        {
            "username": "mercy_admin",
            "password": pwd_context.hash("temp_password_123"),
            "hospital_name": "Mercy Hospital",
            "role": "Admin",
            "first_login": True
        }
    ]
    await db.users.insert_many(users)
    
    # Seed Families
    families = [
        {
            "family_id": "SEC-2413",
            "principle_member_name": "John Smith",
            "total_allotment": 5000.00,
            "remaining_balance": 4250.00
        },
        {
            "family_id": "SEC-2414",
            "principle_member_name": "Sarah Johnson",
            "total_allotment": 7500.00,
            "remaining_balance": 7500.00
        },
        {
            "family_id": "SEC-2415",
            "principle_member_name": "Michael Brown",
            "total_allotment": 3000.00,
            "remaining_balance": 850.00
        },
        {
            "family_id": "SEC-2416",
            "principle_member_name": "Emily Davis",
            "total_allotment": 6000.00,
            "remaining_balance": 5200.00
        }
    ]
    await db.families.insert_many(families)
    
    # Seed Members
    members = [
        # Smith Family
        {
            "serial_number": "SEC-2413-00",
            "family_id": "SEC-2413",
            "first_name": "John",
            "middle_name": "Robert",
            "last_name": "Smith",
            "dob": "1985-03-15",
            "sex": "Male",
            "relationship": "Principle"
        },
        {
            "serial_number": "SEC-2413-01",
            "family_id": "SEC-2413",
            "first_name": "Mary",
            "middle_name": "Ann",
            "last_name": "Smith",
            "dob": "1987-07-22",
            "sex": "Female",
            "relationship": "Spouse"
        },
        {
            "serial_number": "SEC-2413-02",
            "family_id": "SEC-2413",
            "first_name": "Emma",
            "middle_name": "",
            "last_name": "Smith",
            "dob": "2015-11-08",
            "sex": "Female",
            "relationship": "Child"
        },
        # Johnson Family
        {
            "serial_number": "SEC-2414-00",
            "family_id": "SEC-2414",
            "first_name": "Sarah",
            "middle_name": "Elizabeth",
            "last_name": "Johnson",
            "dob": "1990-05-10",
            "sex": "Female",
            "relationship": "Principle"
        },
        {
            "serial_number": "SEC-2414-01",
            "family_id": "SEC-2414",
            "first_name": "David",
            "middle_name": "Lee",
            "last_name": "Johnson",
            "dob": "1988-09-18",
            "sex": "Male",
            "relationship": "Spouse"
        },
        # Brown Family
        {
            "serial_number": "SEC-2415-00",
            "family_id": "SEC-2415",
            "first_name": "Michael",
            "middle_name": "James",
            "last_name": "Brown",
            "dob": "1975-12-03",
            "sex": "Male",
            "relationship": "Principle"
        },
        {
            "serial_number": "SEC-2415-01",
            "family_id": "SEC-2415",
            "first_name": "Linda",
            "middle_name": "Marie",
            "last_name": "Brown",
            "dob": "1978-06-25",
            "sex": "Female",
            "relationship": "Spouse"
        },
        {
            "serial_number": "SEC-2415-02",
            "family_id": "SEC-2415",
            "first_name": "James",
            "middle_name": "",
            "last_name": "Brown",
            "dob": "2010-02-14",
            "sex": "Male",
            "relationship": "Child"
        },
        {
            "serial_number": "SEC-2415-03",
            "family_id": "SEC-2415",
            "first_name": "Robert",
            "middle_name": "Sr",
            "last_name": "Brown",
            "dob": "1950-03-20",
            "sex": "Male",
            "relationship": "Father"
        },
        # Davis Family
        {
            "serial_number": "SEC-2416-00",
            "family_id": "SEC-2416",
            "first_name": "Emily",
            "middle_name": "Grace",
            "last_name": "Davis",
            "dob": "1992-08-30",
            "sex": "Female",
            "relationship": "Principle"
        },
        {
            "serial_number": "SEC-2416-01",
            "family_id": "SEC-2416",
            "first_name": "Robert",
            "middle_name": "William",
            "last_name": "Davis",
            "dob": "1991-04-12",
            "sex": "Male",
            "relationship": "Spouse"
        },
        {
            "serial_number": "SEC-2416-02",
            "family_id": "SEC-2416",
            "first_name": "Margaret",
            "middle_name": "",
            "last_name": "Davis",
            "dob": "1965-11-15",
            "sex": "Female",
            "relationship": "Mother"
        },
        {
            "serial_number": "SEC-2416-03",
            "family_id": "SEC-2416",
            "first_name": "Sarah",
            "middle_name": "Jane",
            "last_name": "Thompson",
            "dob": "1988-06-22",
            "sex": "Female",
            "relationship": "Dependent"
        }
    ]
    await db.members.insert_many(members)
    
    # Seed Price Lists
    pricelists = [
        # General Hospital
        {"hospital_name": "General Hospital", "item_id": "SERV-001", "item_name": "Doctor Consultation", "item_type": "Service", "cost": 75.00},
        {"hospital_name": "General Hospital", "item_id": "SERV-002", "item_name": "Specialist Consultation", "item_type": "Service", "cost": 150.00},
        {"hospital_name": "General Hospital", "item_id": "SERV-003", "item_name": "X-Ray", "item_type": "Service", "cost": 120.00},
        {"hospital_name": "General Hospital", "item_id": "SERV-004", "item_name": "Blood Test (Basic)", "item_type": "Service", "cost": 50.00},
        {"hospital_name": "General Hospital", "item_id": "SERV-005", "item_name": "Ultrasound", "item_type": "Service", "cost": 200.00},
        {"hospital_name": "General Hospital", "item_id": "DRUG-001", "item_name": "Paracetamol 500mg (10 tablets)", "item_type": "Drug", "cost": 5.00},
        {"hospital_name": "General Hospital", "item_id": "DRUG-002", "item_name": "Amoxicillin 500mg (20 capsules)", "item_type": "Drug", "cost": 15.00},
        {"hospital_name": "General Hospital", "item_id": "DRUG-003", "item_name": "Ibuprofen 400mg (30 tablets)", "item_type": "Drug", "cost": 8.00},
        {"hospital_name": "General Hospital", "item_id": "DRUG-004", "item_name": "Cough Syrup 100ml", "item_type": "Drug", "cost": 12.00},
        
        # City Medical Center
        {"hospital_name": "City Medical Center", "item_id": "SERV-001", "item_name": "Doctor Consultation", "item_type": "Service", "cost": 85.00},
        {"hospital_name": "City Medical Center", "item_id": "SERV-002", "item_name": "Specialist Consultation", "item_type": "Service", "cost": 175.00},
        {"hospital_name": "City Medical Center", "item_id": "SERV-003", "item_name": "X-Ray", "item_type": "Service", "cost": 135.00},
        {"hospital_name": "City Medical Center", "item_id": "SERV-004", "item_name": "Blood Test (Basic)", "item_type": "Service", "cost": 60.00},
        {"hospital_name": "City Medical Center", "item_id": "SERV-005", "item_name": "CT Scan", "item_type": "Service", "cost": 450.00},
        {"hospital_name": "City Medical Center", "item_id": "DRUG-001", "item_name": "Paracetamol 500mg (10 tablets)", "item_type": "Drug", "cost": 6.00},
        {"hospital_name": "City Medical Center", "item_id": "DRUG-002", "item_name": "Amoxicillin 500mg (20 capsules)", "item_type": "Drug", "cost": 18.00},
        {"hospital_name": "City Medical Center", "item_id": "DRUG-003", "item_name": "Insulin (1 vial)", "item_type": "Drug", "cost": 95.00},
        
        # Mercy Hospital
        {"hospital_name": "Mercy Hospital", "item_id": "SERV-001", "item_name": "Doctor Consultation", "item_type": "Service", "cost": 70.00},
        {"hospital_name": "Mercy Hospital", "item_id": "SERV-002", "item_name": "Specialist Consultation", "item_type": "Service", "cost": 140.00},
        {"hospital_name": "Mercy Hospital", "item_id": "SERV-003", "item_name": "X-Ray", "item_type": "Service", "cost": 110.00},
        {"hospital_name": "Mercy Hospital", "item_id": "SERV-004", "item_name": "Blood Test (Comprehensive)", "item_type": "Service", "cost": 80.00},
        {"hospital_name": "Mercy Hospital", "item_id": "SERV-005", "item_name": "MRI Scan", "item_type": "Service", "cost": 850.00},
        {"hospital_name": "Mercy Hospital", "item_id": "DRUG-001", "item_name": "Paracetamol 500mg (10 tablets)", "item_type": "Drug", "cost": 4.50},
        {"hospital_name": "Mercy Hospital", "item_id": "DRUG-002", "item_name": "Amoxicillin 500mg (20 capsules)", "item_type": "Drug", "cost": 14.00},
        {"hospital_name": "Mercy Hospital", "item_id": "DRUG-003", "item_name": "Aspirin 100mg (30 tablets)", "item_type": "Drug", "cost": 7.00}
    ]
    await db.pricelists.insert_many(pricelists)
    
    print("✅ Database seeded successfully!")
    print("\n🔐 Login Credentials:")
    print("\n** SUPER ADMIN **")
    print("  Username: superadmin")
    print("  Password: SuperAdmin@2024")
    print("  Access: Full system administration\n")
    
    print("** Hospital Admins (First Login Required) **")
    print("Hospital: General Hospital")
    print("  Username: general_admin")
    print("  Temp Password: temp_password_123")
    print("  (Will be prompted to set new password on first login)\n")
    
    print("Hospital: City Medical Center")
    print("  Username: city_admin")
    print("  Temp Password: temp_password_123")
    print("  (Will be prompted to set new password on first login)\n")
    
    print("Hospital: Mercy Hospital")
    print("  Username: mercy_admin")
    print("  Temp Password: temp_password_123")
    print("  (Will be prompted to set new password on first login)\n")
    
    print("** Billing Clerks (Demo accounts) **")
    print("  general_clerk / password123")
    print("  city_clerk / password123\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())