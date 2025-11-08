"""
Migration script to add 'status' field to existing families and members
"""
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def migrate():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Update families without status field
    result_families = await db.families.update_many(
        {"status": {"$exists": False}},
        {"$set": {"status": "Active"}}
    )
    print(f"Updated {result_families.modified_count} families with status='Active'")
    
    # Update members without status field
    result_members = await db.members.update_many(
        {"status": {"$exists": False}},
        {"$set": {"status": "Active"}}
    )
    print(f"Updated {result_members.modified_count} members with status='Active'")
    
    # Check counts
    total_families = await db.families.count_documents({})
    total_members = await db.members.count_documents({})
    print(f"\nTotal families in database: {total_families}")
    print(f"Total members in database: {total_members}")
    
    client.close()
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate())
