"""
Seed currencies and update existing hospitals with currency_code
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def seed_currencies():
    # Connect to MongoDB
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "medical_insurance_db")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("Starting currency seeding...")
    
    # Check if USD already exists
    usd_exists = await db.currencies.find_one({"code": "USD"})
    
    if not usd_exists:
        # Create USD as base currency
        usd_currency = {
            "code": "USD",
            "name": "US Dollar",
            "symbol": "$",
            "rate_to_usd": 1.0,
            "decimal_places": 2
        }
        await db.currencies.insert_one(usd_currency)
        print("✅ Created USD base currency")
    else:
        print("ℹ️  USD currency already exists")
    
    # Add some common currencies for quick setup
    common_currencies = [
        {
            "code": "KSH",
            "name": "Kenyan Shilling",
            "symbol": "KSh",
            "rate_to_usd": 150.0,  # Example rate: 150 KSH = 1 USD
            "decimal_places": 2
        },
        {
            "code": "UGX",
            "name": "Ugandan Shilling",
            "symbol": "USh",
            "rate_to_usd": 3700.0,  # Example rate: 3700 UGX = 1 USD
            "decimal_places": 0  # Uganda typically doesn't use decimals
        },
        {
            "code": "TZS",
            "name": "Tanzanian Shilling",
            "symbol": "TSh",
            "rate_to_usd": 2500.0,  # Example rate
            "decimal_places": 0
        }
    ]
    
    for currency in common_currencies:
        existing = await db.currencies.find_one({"code": currency["code"]})
        if not existing:
            await db.currencies.insert_one(currency)
            print(f"✅ Created {currency['code']} - {currency['name']}")
        else:
            print(f"ℹ️  {currency['code']} already exists")
    
    # Update existing hospitals to have currency_code = USD if not set
    hospitals = await db.hospitals.find({}).to_list(1000)
    updated_count = 0
    
    for hospital in hospitals:
        if "currency_code" not in hospital:
            await db.hospitals.update_one(
                {"hospital_name": hospital["hospital_name"]},
                {"$set": {"currency_code": "USD"}}
            )
            updated_count += 1
            print(f"✅ Updated {hospital['hospital_name']} to use USD")
    
    if updated_count == 0:
        print("ℹ️  All hospitals already have currency_code set")
    else:
        print(f"✅ Updated {updated_count} hospitals to use USD")
    
    print("\n✅ Currency seeding complete!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_currencies())
