from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class UserLogin(BaseModel):
    username: str
    password: str

class PasswordSetup(BaseModel):
    username: str
    temporary_password: str
    new_password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    hospital_name: str
    username: str
    role: str
    first_login: bool

class Member(BaseModel):
    model_config = ConfigDict(extra="ignore")
    serial_number: str
    family_id: str
    first_name: str
    middle_name: Optional[str] = ""
    last_name: str
    dob: str
    sex: str
    relationship: str

class Family(BaseModel):
    model_config = ConfigDict(extra="ignore")
    family_id: str
    principle_member_name: str
    total_allotment: float
    remaining_balance: float

class PriceListItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    hospital_name: str
    item_id: str
    item_name: str
    item_type: str
    cost: float

class BillItem(BaseModel):
    item_id: str
    item_name: str
    item_cost: float

class BillSubmission(BaseModel):
    patient_serial_number: str
    bill_items: List[BillItem]

class BillHeader(BaseModel):
    model_config = ConfigDict(extra="ignore")
    bill_id: str
    timestamp: str
    hospital_name: str
    patient_serial_number: str
    patient_name: str
    family_id: str
    total_bill_amount: float
    status: str

class BillDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    bill_detail_id: str
    bill_id: str
    item_id: str
    item_name: str
    item_cost: float

class PatientSearchResult(BaseModel):
    serial_number: str
    family_id: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    dob: str
    sex: str
    relationship: str
    remaining_balance: float

class FamilyCreate(BaseModel):
    family_id: str
    principle_member_name: str
    total_allotment: float
    remaining_balance: float

class MemberCreate(BaseModel):
    serial_number: str
    family_id: str
    first_name: str
    middle_name: Optional[str] = ""
    last_name: str
    dob: str
    sex: str
    relationship: str  # Principle, Spouse, Father, Mother, Child, Dependent

class FamilyWithMembers(BaseModel):
    family_id: str
    principle_member_name: str
    total_allotment: float
    remaining_balance: float
    members: List[dict]  # List of member details without serial numbers

class BulkPriceList(BaseModel):
    hospital_name: str
    items: List[dict]  # List of {item_id, item_name, item_type, cost}

class HospitalCreate(BaseModel):
    hospital_name: str
    address: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""

class UserCreate(BaseModel):
    username: str
    hospital_name: str
    role: str
    temporary_password: str
    first_login: bool = True

class FamilyUpdate(BaseModel):
    principle_member_name: Optional[str] = None
    total_allotment: Optional[float] = None
    remaining_balance: Optional[float] = None

class MemberUpdate(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    sex: Optional[str] = None
    relationship: Optional[str] = None

class PriceListUpdate(BaseModel):
    item_name: Optional[str] = None
    item_type: Optional[str] = None
    cost: Optional[float] = None

class UserUpdate(BaseModel):
    hospital_name: Optional[str] = None
    role: Optional[str] = None

class PriceListCreate(BaseModel):
    hospital_name: str
    item_id: str
    item_name: str
    item_type: str
    cost: float

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        hospital_name: str = payload.get("hospital_name")
        role: str = payload.get("role")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return {"username": username, "hospital_name": hospital_name, "role": role}
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Routes
@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_login: UserLogin):
    user = await db.users.find_one({"username": user_login.username}, {"_id": 0})
    if not user or not verify_password(user_login.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "hospital_name": user["hospital_name"],
            "role": user["role"]
        }
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        hospital_name=user["hospital_name"],
        username=user["username"],
        role=user["role"],
        first_login=user.get("first_login", False)
    )

@api_router.post("/auth/setup-password")
async def setup_password(password_setup: PasswordSetup):
    user = await db.users.find_one({"username": password_setup.username}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.get("first_login", False):
        raise HTTPException(status_code=400, detail="Password already set")
    
    if not verify_password(password_setup.temporary_password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid temporary password")
    
    # Update password and mark as not first login
    new_hashed_password = pwd_context.hash(password_setup.new_password)
    await db.users.update_one(
        {"username": password_setup.username},
        {"$set": {"password": new_hashed_password, "first_login": False}}
    )
    
    return {"success": True, "message": "Password set successfully"}

@api_router.get("/patients/search")
async def search_patient(query: str, current_user: dict = Depends(get_current_user)):
    # Search by serial number or name
    search_filter = {
        "$or": [
            {"serial_number": {"$regex": query, "$options": "i"}},
            {"first_name": {"$regex": query, "$options": "i"}},
            {"last_name": {"$regex": query, "$options": "i"}}
        ]
    }
    
    patients = await db.members.find(search_filter, {"_id": 0}).to_list(10)
    
    # Get family balance for each patient
    results = []
    for patient in patients:
        family = await db.families.find_one({"family_id": patient["family_id"]}, {"_id": 0})
        if family:
            results.append({
                **patient,
                "remaining_balance": family["remaining_balance"]
            })
    
    return results

@api_router.get("/patients/{serial_number}")
async def get_patient(serial_number: str, current_user: dict = Depends(get_current_user)):
    patient = await db.members.find_one({"serial_number": serial_number}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    family = await db.families.find_one({"family_id": patient["family_id"]}, {"_id": 0})
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    
    return {
        **patient,
        "remaining_balance": family["remaining_balance"]
    }

@api_router.get("/pricelists")
async def get_price_list(current_user: dict = Depends(get_current_user)):
    hospital_name = current_user["hospital_name"]
    items = await db.pricelists.find({"hospital_name": hospital_name}, {"_id": 0}).to_list(1000)
    return items

@api_router.post("/bills/submit")
async def submit_bill(bill_submission: BillSubmission, current_user: dict = Depends(get_current_user)):
    # Get patient details
    patient = await db.members.find_one(
        {"serial_number": bill_submission.patient_serial_number},
        {"_id": 0}
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get family balance
    family = await db.families.find_one({"family_id": patient["family_id"]}, {"_id": 0})
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    
    # Calculate total
    total_amount = sum(item.item_cost for item in bill_submission.bill_items)
    
    # Check balance
    if total_amount > family["remaining_balance"]:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient funds. Available balance: ${family['remaining_balance']:.2f}, Bill amount: ${total_amount:.2f}"
        )
    
    # Create bill
    bill_id = f"BILL-{str(uuid.uuid4())[:8].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Insert bill header
    bill_header = {
        "bill_id": bill_id,
        "timestamp": timestamp,
        "hospital_name": current_user["hospital_name"],
        "patient_serial_number": patient["serial_number"],
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "family_id": patient["family_id"],
        "total_bill_amount": total_amount,
        "status": "COMPLETED"
    }
    await db.bills_header.insert_one(bill_header)
    
    # Insert bill details
    for item in bill_submission.bill_items:
        bill_detail = {
            "bill_detail_id": str(uuid.uuid4()),
            "bill_id": bill_id,
            "item_id": item.item_id,
            "item_name": item.item_name,
            "item_cost": item.item_cost
        }
        await db.bills_details.insert_one(bill_detail)
    
    # Update family balance
    new_balance = family["remaining_balance"] - total_amount
    await db.families.update_one(
        {"family_id": patient["family_id"]},
        {"$set": {"remaining_balance": new_balance}}
    )
    
    return {
        "success": True,
        "bill_id": bill_id,
        "total_amount": total_amount,
        "new_balance": new_balance
    }

@api_router.get("/bills")
async def get_bills(current_user: dict = Depends(get_current_user)):
    hospital_name = current_user["hospital_name"]
    bills = await db.bills_header.find(
        {"hospital_name": hospital_name},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    return bills

@api_router.get("/bills/monthly-stats")
async def get_monthly_billing_stats(current_user: dict = Depends(get_current_user)):
    # Get current month's bills
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Aggregate bills by hospital for current month
    pipeline = [
        {
            "$match": {
                "timestamp": {"$gte": start_of_month.isoformat()},
                "status": "COMPLETED"
            }
        },
        {
            "$group": {
                "_id": "$hospital_name",
                "total_amount": {"$sum": "$total_bill_amount"},
                "bill_count": {"$sum": 1}
            }
        }
    ]
    
    results = await db.bills_header.aggregate(pipeline).to_list(100)
    
    stats = {}
    for result in results:
        stats[result["_id"]] = {
            "total": result["total_amount"],
            "count": result["bill_count"]
        }
    
    return stats

@api_router.get("/bills/{bill_id}")
async def get_bill_details(bill_id: str, current_user: dict = Depends(get_current_user)):
    bill_header = await db.bills_header.find_one({"bill_id": bill_id}, {"_id": 0})
    if not bill_header:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    # Check if user has access to this bill
    if current_user["role"] != "Admin" or current_user["hospital_name"] != "System Administration":
        # Regular hospital users can only see their own bills
        if bill_header["hospital_name"] != current_user["hospital_name"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    bill_details = await db.bills_details.find({" bill_id": bill_id}, {"_id": 0}).to_list(100)
    
    return {
        "header": bill_header,
        "details": bill_details
    }

@api_router.get("/admin/bills/all")
async def get_all_bills_admin(admin_user: dict = Depends(get_admin_user)):
    # Get all bills for admin (not filtered by hospital)
    bills = await db.bills_header.find({}, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    return bills

@api_router.post("/bills/{bill_id}/void")
async def void_bill(bill_id: str, current_user: dict = Depends(get_current_user)):
    bill = await db.bills_header.find_one({"bill_id": bill_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    if bill["status"] == "VOIDED":
        raise HTTPException(status_code=400, detail="Bill already voided")
    
    # Refund the amount to family
    await db.families.update_one(
        {"family_id": bill["family_id"]},
        {"$inc": {"remaining_balance": bill["total_bill_amount"]}}
    )
    
    # Mark bill as voided
    await db.bills_header.update_one(
        {"bill_id": bill_id},
        {"$set": {"status": "VOIDED"}}
    )
    
    return {"success": True, "message": "Bill voided successfully"}

@api_router.delete("/admin/bills/{bill_id}")
async def delete_bill(bill_id: str, admin_user: dict = Depends(get_admin_user)):
    # Get bill to check if it needs refund
    bill = await db.bills_header.find_one({"bill_id": bill_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    # If bill is completed, refund the amount
    if bill["status"] == "COMPLETED":
        await db.families.update_one(
            {"family_id": bill["family_id"]},
            {"$inc": {"remaining_balance": bill["total_bill_amount"]}}
        )
    
    # Delete bill details
    await db.bills_details.delete_many({"bill_id": bill_id})
    
    # Delete bill header
    await db.bills_header.delete_one({"bill_id": bill_id})
    
    return {"success": True, "message": "Bill deleted successfully"}

# Admin Routes
@api_router.get("/admin/families")
async def get_all_families(admin_user: dict = Depends(get_admin_user)):
    families = await db.families.find({}, {"_id": 0}).to_list(1000)
    return families

@api_router.post("/admin/families")
async def create_family(family: FamilyCreate, admin_user: dict = Depends(get_admin_user)):
    # Check if family_id already exists
    existing = await db.families.find_one({"family_id": family.family_id})
    if existing:
        raise HTTPException(status_code=400, detail="Family ID already exists")
    
    family_doc = family.model_dump()
    await db.families.insert_one(family_doc)
    return {"success": True, "message": "Family created successfully"}

@api_router.put("/admin/families/{family_id}")
async def update_family(family_id: str, family_update: FamilyUpdate, admin_user: dict = Depends(get_admin_user)):
    # Check if family exists
    existing = await db.families.find_one({"family_id": family_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Family not found")
    
    # Build update document
    update_doc = {k: v for k, v in family_update.model_dump().items() if v is not None}
    if not update_doc:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    await db.families.update_one({"family_id": family_id}, {"$set": update_doc})
    return {"success": True, "message": "Family updated successfully"}

@api_router.delete("/admin/families/{family_id}")
async def delete_family(family_id: str, admin_user: dict = Depends(get_admin_user)):
    # Check if family has members
    members = await db.members.find_one({"family_id": family_id})
    if members:
        raise HTTPException(status_code=400, detail="Cannot delete family with existing members. Delete members first.")
    
    # Check if family has bills
    bills = await db.bills_header.find_one({"family_id": family_id})
    if bills:
        raise HTTPException(status_code=400, detail="Cannot delete family with existing bills.")
    
    result = await db.families.delete_one({"family_id": family_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Family not found")
    
    return {"success": True, "message": "Family deleted successfully"}

@api_router.post("/admin/families/bulk")
async def create_family_with_members(family_data: FamilyWithMembers, admin_user: dict = Depends(get_admin_user)):
    # Check if family_id already exists
    existing = await db.families.find_one({"family_id": family_data.family_id})
    if existing:
        raise HTTPException(status_code=400, detail="Family ID already exists")
    
    # Create family
    family_doc = {
        "family_id": family_data.family_id,
        "principle_member_name": family_data.principle_member_name,
        "total_allotment": family_data.total_allotment,
        "remaining_balance": family_data.remaining_balance
    }
    await db.families.insert_one(family_doc)
    
    # Create members with auto-generated serial numbers
    members_created = []
    for index, member_data in enumerate(family_data.members):
        serial_number = f"{family_data.family_id}-{index:02d}"
        
        # Check if serial number already exists
        existing_member = await db.members.find_one({"serial_number": serial_number})
        if existing_member:
            raise HTTPException(status_code=400, detail=f"Serial number {serial_number} already exists")
        
        member_doc = {
            "serial_number": serial_number,
            "family_id": family_data.family_id,
            "first_name": member_data["first_name"],
            "middle_name": member_data.get("middle_name", ""),
            "last_name": member_data["last_name"],
            "dob": member_data["dob"],
            "sex": member_data["sex"],
            "relationship": member_data["relationship"]
        }
        await db.members.insert_one(member_doc)
        members_created.append(serial_number)
    
    return {
        "success": True,
        "message": f"Family and {len(members_created)} members created successfully",
        "family_id": family_data.family_id,
        "members": members_created
    }

@api_router.get("/admin/members")
async def get_all_members(admin_user: dict = Depends(get_admin_user)):
    members = await db.members.find({}, {"_id": 0}).to_list(1000)
    return members

@api_router.post("/admin/members")
async def create_member(member: MemberCreate, admin_user: dict = Depends(get_admin_user)):
    # Check if serial_number already exists
    existing = await db.members.find_one({"serial_number": member.serial_number})
    if existing:
        raise HTTPException(status_code=400, detail="Serial number already exists")
    
    # Check if family exists
    family = await db.families.find_one({"family_id": member.family_id})
    if not family:
        raise HTTPException(status_code=404, detail="Family ID not found")
    
    member_doc = member.model_dump()
    await db.members.insert_one(member_doc)
    return {"success": True, "message": "Member added successfully"}

@api_router.put("/admin/members/{serial_number}")
async def update_member(serial_number: str, member_update: MemberUpdate, admin_user: dict = Depends(get_admin_user)):
    # Check if member exists
    existing = await db.members.find_one({"serial_number": serial_number})
    if not existing:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Build update document
    update_doc = {k: v for k, v in member_update.model_dump().items() if v is not None}
    if not update_doc:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    await db.members.update_one({"serial_number": serial_number}, {"$set": update_doc})
    return {"success": True, "message": "Member updated successfully"}

@api_router.delete("/admin/members/{serial_number}")
async def delete_member(serial_number: str, admin_user: dict = Depends(get_admin_user)):
    # Check if member has bills
    bills = await db.bills_header.find_one({"patient_serial_number": serial_number})
    if bills:
        raise HTTPException(status_code=400, detail="Cannot delete member with existing bills.")
    
    result = await db.members.delete_one({"serial_number": serial_number})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    
    return {"success": True, "message": "Member deleted successfully"}

@api_router.get("/admin/pricelists/all")
async def get_all_pricelists(admin_user: dict = Depends(get_admin_user)):
    pricelists = await db.pricelists.find({}, {"_id": 0}).to_list(1000)
    return pricelists

@api_router.post("/admin/pricelists")
async def create_pricelist_item(item: PriceListCreate, admin_user: dict = Depends(get_admin_user)):
    # Check if item_id already exists for this hospital
    existing = await db.pricelists.find_one({
        "hospital_name": item.hospital_name,
        "item_id": item.item_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Item ID already exists for this hospital")
    
    item_doc = item.model_dump()
    await db.pricelists.insert_one(item_doc)
    return {"success": True, "message": "Price list item created successfully"}

@api_router.post("/admin/pricelists/bulk")
async def bulk_create_pricelists(bulk_data: BulkPriceList, admin_user: dict = Depends(get_admin_user)):
    items_created = []
    items_skipped = []
    
    for item_data in bulk_data.items:
        # Check if item_id already exists for this hospital
        existing = await db.pricelists.find_one({
            "hospital_name": bulk_data.hospital_name,
            "item_id": item_data["item_id"]
        })
        
        if existing:
            items_skipped.append(item_data["item_id"])
            continue
        
        item_doc = {
            "hospital_name": bulk_data.hospital_name,
            "item_id": item_data["item_id"],
            "item_name": item_data["item_name"],
            "item_type": item_data["item_type"],
            "cost": float(item_data["cost"])
        }
        await db.pricelists.insert_one(item_doc)
        items_created.append(item_data["item_id"])
    
    return {
        "success": True,
        "message": f"Created {len(items_created)} items, skipped {len(items_skipped)} duplicates",
        "created": items_created,
        "skipped": items_skipped
    }

@api_router.put("/admin/pricelists/{hospital_name}/{item_id}")
async def update_pricelist_item(hospital_name: str, item_id: str, item_update: PriceListUpdate, admin_user: dict = Depends(get_admin_user)):
    # Check if item exists
    existing = await db.pricelists.find_one({"hospital_name": hospital_name, "item_id": item_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Price list item not found")
    
    # Build update document
    update_doc = {k: v for k, v in item_update.model_dump().items() if v is not None}
    if not update_doc:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    await db.pricelists.update_one(
        {"hospital_name": hospital_name, "item_id": item_id},
        {"$set": update_doc}
    )
    return {"success": True, "message": "Price list item updated successfully"}

@api_router.delete("/admin/pricelists/{hospital_name}/{item_id}")
async def delete_pricelist_item(hospital_name: str, item_id: str, admin_user: dict = Depends(get_admin_user)):
    result = await db.pricelists.delete_one({
        "hospital_name": hospital_name,
        "item_id": item_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Price list item not found")
    
    return {"success": True, "message": "Price list item deleted successfully"}

@api_router.get("/admin/hospitals")
async def get_hospitals(admin_user: dict = Depends(get_admin_user)):
    # Get unique hospital names from hospitals collection
    hospitals = await db.hospitals.find({}, {"_id": 0}).to_list(1000)
    return hospitals

@api_router.post("/admin/hospitals")
async def create_hospital(hospital: HospitalCreate, admin_user: dict = Depends(get_admin_user)):
    # Check if hospital already exists
    existing = await db.hospitals.find_one({"hospital_name": hospital.hospital_name})
    if existing:
        raise HTTPException(status_code=400, detail="Hospital already exists")
    
    hospital_doc = hospital.model_dump()
    await db.hospitals.insert_one(hospital_doc)
    return {"success": True, "message": "Hospital created successfully"}

@api_router.put("/admin/hospitals/{hospital_name}")
async def update_hospital(hospital_name: str, hospital_update: HospitalCreate, admin_user: dict = Depends(get_admin_user)):
    # Check if hospital exists
    existing = await db.hospitals.find_one({"hospital_name": hospital_name})
    if not existing:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    update_doc = hospital_update.model_dump()
    await db.hospitals.update_one({"hospital_name": hospital_name}, {"$set": update_doc})
    return {"success": True, "message": "Hospital updated successfully"}

@api_router.delete("/admin/hospitals/{hospital_name}")
async def delete_hospital(hospital_name: str, admin_user: dict = Depends(get_admin_user)):
    # Check if hospital has users
    users = await db.users.find_one({"hospital_name": hospital_name})
    if users:
        raise HTTPException(status_code=400, detail="Cannot delete hospital with existing users.")
    
    # Check if hospital has price lists
    pricelists = await db.pricelists.find_one({"hospital_name": hospital_name})
    if pricelists:
        raise HTTPException(status_code=400, detail="Cannot delete hospital with existing price lists.")
    
    result = await db.hospitals.delete_one({"hospital_name": hospital_name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    return {"success": True, "message": "Hospital deleted successfully"}

@api_router.post("/admin/users")
async def create_user(user_data: UserCreate, admin_user: dict = Depends(get_admin_user)):
    # Check if username exists
    existing = await db.users.find_one({"username": user_data.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create user with first_login flag
    user_doc = {
        "username": user_data.username,
        "password": pwd_context.hash(user_data.temporary_password),
        "hospital_name": user_data.hospital_name,
        "role": user_data.role,
        "first_login": user_data.first_login
    }
    await db.users.insert_one(user_doc)
    return {"success": True, "message": "User created successfully"}

@api_router.get("/admin/users")
async def get_all_users(admin_user: dict = Depends(get_admin_user)):
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users

@api_router.put("/admin/users/{username}")
async def update_user(username: str, user_update: UserUpdate, admin_user: dict = Depends(get_admin_user)):
    # Check if user exists
    existing = await db.users.find_one({"username": username})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build update document
    update_doc = {k: v for k, v in user_update.model_dump().items() if v is not None}
    if not update_doc:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    await db.users.update_one({"username": username}, {"$set": update_doc})
    return {"success": True, "message": "User updated successfully"}

@api_router.delete("/admin/users/{username}")
async def delete_user(username: str, admin_user: dict = Depends(get_admin_user)):
    # Prevent deleting superadmin
    if username == "superadmin":
        raise HTTPException(status_code=400, detail="Cannot delete superadmin account")
    
    result = await db.users.delete_one({"username": username})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"success": True, "message": "User deleted successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()