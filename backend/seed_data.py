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
    await db.claims_header.delete_many({})
    await db.claims_details.delete_many({})
    await db.hospitals.delete_many({})
    
    # Seed ONLY Super Admin - hospitals and users will be created via admin panel
    users = [
        {
            "username": "superadmin",
            "password": pwd_context.hash("SuperAdmin@2024"),
            "hospital_name": "System Administration",
            "role": "Admin",
            "first_login": False
        }
    ]
    await db.users.insert_many(users)
    
    # Seed sample hospitals (can be created via admin panel later)
    hospitals = [
        {
            "hospital_name": "System Administration",
            "address": "N/A",
            "phone": "N/A",
            "email": "superadmin@system.com"
        }
    ]
    await db.hospitals.insert_many(hospitals)
    
    # Seed Families
    families = [
        {
            "family_id": "SEC-2413",
            "principle_member_name": "John Smith",
            "total_allotment": 5000.00,
            "remaining_balance": 5000.00
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
            "remaining_balance": 3000.00
        },
        {
            "family_id": "SEC-2416",
            "principle_member_name": "Emily Davis",
            "total_allotment": 6000.00,
            "remaining_balance": 6000.00
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
    
    # Seed Price Lists - Empty, will be added via admin panel per hospital
    pricelists = []
    # await db.pricelists.insert_many(pricelists)
    
    print("✅ Database seeded successfully!")
    print("\n🔐 SUPER ADMIN CREDENTIALS:")
    print("  Username: superadmin")
    print("  Password: SuperAdmin@2024")
    print("  Access: Full system administration")
    print("\n📋 NEXT STEPS:")
    print("  1. Login as superadmin")
    print("  2. Go to Admin Panel → Manage All Data (CRUD)")
    print("  3. Create hospitals in 'Hospitals' tab")
    print("  4. Create users for each hospital in 'Users' tab:")
    print("     - 1 Admin per hospital")
    print("     - 1 Finance per hospital")
    print("     - 1 Reception per hospital")
    print("  5. Add price lists for each hospital")
    print("\n✨ Sample families have been created for testing")
    print("   You can search for: SEC-2413, SEC-2414, SEC-2415, SEC-2416\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())