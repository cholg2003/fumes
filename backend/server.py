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
    relationship: str

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
        role=user["role"]
    )

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

@api_router.get("/bills/{bill_id}")
async def get_bill_details(bill_id: str, current_user: dict = Depends(get_current_user)):
    bill_header = await db.bills_header.find_one({"bill_id": bill_id}, {"_id": 0})
    if not bill_header:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    bill_details = await db.bills_details.find({"bill_id": bill_id}, {"_id": 0}).to_list(100)
    
    return {
        "header": bill_header,
        "details": bill_details
    }

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
    # Get unique hospital names from users collection
    users = await db.users.find({}, {"_id": 0, "hospital_name": 1}).to_list(1000)
    hospitals = list(set([u["hospital_name"] for u in users]))
    return hospitals

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