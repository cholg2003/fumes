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

class PasswordReset(BaseModel):
    temporary_password: str

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
    status: str = "Active"  # Active or Suspended

class Family(BaseModel):
    model_config = ConfigDict(extra="ignore")
    family_id: str
    principle_member_name: str
    total_allotment: float
    remaining_balance: float
    status: str = "Active"  # Active or Suspended

class PriceListItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    hospital_name: str
    item_id: str
    item_name: str
    item_type: str
    cost: float

class ClaimItem(BaseModel):
    item_id: str
    item_name: str
    item_cost: float
    quantity: int = 1

class ClaimSubmission(BaseModel):
    patient_serial_number: str
    claim_items: List[ClaimItem]

class ClaimHeader(BaseModel):
    model_config = ConfigDict(extra="ignore")
    claim_id: str
    timestamp: str
    hospital_name: str
    patient_serial_number: str
    patient_name: str
    family_id: str
    total_claim_amount: float
    status: str

class ClaimDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    claim_detail_id: str
    claim_id: str
    item_id: str
    item_name: str
    item_cost: float
    quantity: int = 1

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
    status: str = "Active"

class MemberCreate(BaseModel):
    serial_number: str
    family_id: str
    first_name: str
    middle_name: Optional[str] = ""
    last_name: str
    dob: str
    sex: str
    relationship: str  # Principle, Spouse, Father, Mother, Child, Dependent
    status: str = "Active"

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
    deposit_balance: float = 0.0

class DepositRequest(BaseModel):
    amount: float

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
    status: Optional[str] = None

class MemberUpdate(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    sex: Optional[str] = None
    relationship: Optional[str] = None
    status: Optional[str] = None

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
    # Check if user is superadmin
    is_superadmin = current_user["username"] == "superadmin"
    
    # Check if query is a Family ID (e.g., SEC-2413 without the member number)
    is_family_id = query and '-' in query and len(query.split('-')) == 2
    
    if is_family_id:
        # Search by Family ID
        family_filter = {"family_id": query}
        # Hide suspended families from non-superadmin users
        if not is_superadmin:
            family_filter["status"] = {"$ne": "Suspended"}
        
        family = await db.families.find_one(family_filter, {"_id": 0})
        if not family:
            return {"type": "family", "family": None, "members": []}
        
        # Get members
        member_filter = {"family_id": query}
        # Hide suspended members from non-superadmin users
        if not is_superadmin:
            member_filter["status"] = {"$ne": "Suspended"}
        
        members = await db.members.find(member_filter, {"_id": 0}).to_list(100)
        
        return {
            "type": "family",
            "family": family,
            "members": members
        }
    else:
        # Search by serial number or name (individual search)
        search_filter = {
            "$or": [
                {"serial_number": {"$regex": query, "$options": "i"}},
                {"first_name": {"$regex": query, "$options": "i"}},
                {"last_name": {"$regex": query, "$options": "i"}}
            ]
        }
        
        # Hide suspended members from non-superadmin users
        if not is_superadmin:
            search_filter["status"] = {"$ne": "Suspended"}
        
        patients = await db.members.find(search_filter, {"_id": 0}).to_list(10)
        
        # Get family balance for each patient
        results = []
        for patient in patients:
            family_filter = {"family_id": patient["family_id"]}
            # Hide suspended families from non-superadmin users
            if not is_superadmin:
                family_filter["status"] = {"$ne": "Suspended"}
            
            family = await db.families.find_one(family_filter, {"_id": 0})
            if family:
                results.append({
                    **patient,
                    "remaining_balance": family["remaining_balance"]
                })
        
        return {"type": "individual", "results": results}

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

@api_router.post("/claims/submit")
async def submit_claim(claim_submission: ClaimSubmission, current_user: dict = Depends(get_current_user)):
    # Get patient details
    patient = await db.members.find_one(
        {"serial_number": claim_submission.patient_serial_number},
        {"_id": 0}
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Check if member is suspended
    if patient.get("status") == "Suspended":
        raise HTTPException(status_code=403, detail="Cannot create claim for suspended member")
    
    # Get family balance
    family = await db.families.find_one({"family_id": patient["family_id"]}, {"_id": 0})
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    
    # Check if family is suspended
    if family.get("status") == "Suspended":
        raise HTTPException(status_code=403, detail="Cannot create claim for suspended family")
    
    # Calculate total (cost * quantity for each item)
    total_amount = sum(item.item_cost * item.quantity for item in claim_submission.claim_items)
    
    # Check balance
    if total_amount > family["remaining_balance"]:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient funds. Available balance: ${family['remaining_balance']:.2f}, Claim amount: ${total_amount:.2f}"
        )
    
    # Create claim
    claim_id = f"CLAIM-{str(uuid.uuid4())[:8].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Insert claim header
    claim_header = {
        "claim_id": claim_id,
        "timestamp": timestamp,
        "hospital_name": current_user["hospital_name"],
        "patient_serial_number": patient["serial_number"],
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "family_id": patient["family_id"],
        "total_claim_amount": total_amount,
        "status": "PENDING"
    }
    await db.claims_header.insert_one(claim_header)
    
    # Insert claim details
    for item in claim_submission.claim_items:
        claim_detail = {
            "claim_detail_id": str(uuid.uuid4()),
            "claim_id": claim_id,
            "item_id": item.item_id,
            "item_name": item.item_name,
            "item_cost": item.item_cost,
            "quantity": item.quantity
        }
        await db.claims_details.insert_one(claim_detail)
    
    # Update family balance
    new_balance = family["remaining_balance"] - total_amount
    await db.families.update_one(
        {"family_id": patient["family_id"]},
        {"$set": {"remaining_balance": new_balance}}
    )
    
    return {
        "success": True,
        "claim_id": claim_id,
        "total_amount": total_amount,
        "new_balance": new_balance
    }

@api_router.get("/claims")
async def get_claims_list(current_user: dict = Depends(get_current_user)):
    hospital_name = current_user["hospital_name"]
    claims = await db.claims_header.find(
        {"hospital_name": hospital_name},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    return claims

@api_router.get("/claims/monthly-stats")
async def get_monthly_claims_stats(current_user: dict = Depends(get_current_user)):
    # Get current month's bills
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Aggregate claims by hospital for current month
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
                "total_amount": {"$sum": "$total_claim_amount"},
                "claim_count": {"$sum": 1}
            }
        }
    ]
    
    results = await db.claims_header.aggregate(pipeline).to_list(100)
    
    stats = {}
    for result in results:
        stats[result["_id"]] = {
            "total": result["total_amount"],
            "count": result["claim_count"]
        }
    
    return stats

@api_router.get("/claims/hospital-stats")
async def get_hospital_claims_stats(current_user: dict = Depends(get_current_user)):
    """Get overall claims statistics per hospital (for superadmin) or current hospital"""
    
    # Aggregate all claims by hospital
    pipeline = [
        {
            "$group": {
                "_id": "$hospital_name",
                "total_pending": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "PENDING"]}, "$total_claim_amount", 0]
                    }
                },
                "total_paid": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "PAID"]}, "$total_claim_amount", 0]
                    }
                },
                "pending_count": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "PENDING"]}, 1, 0]
                    }
                },
                "paid_count": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "PAID"]}, 1, 0]
                    }
                }
            }
        }
    ]
    
    results = await db.claims_header.aggregate(pipeline).to_list(100)
    
    stats = {}
    for result in results:
        hospital = result["_id"]
        total_pending = result["total_pending"]
        total_paid = result["total_paid"]
        outstanding = total_pending  # Outstanding is what's still PENDING (not yet paid)
        
        stats[hospital] = {
            "total_pending": total_pending,
            "total_paid": total_paid,
            "outstanding": outstanding,
            "pending_count": result["pending_count"],
            "paid_count": result["paid_count"]
        }
    
    return stats


@api_router.get("/claims")
async def get_claims(current_user: dict = Depends(get_current_user)):
    # Get claims for current user's hospital
    hospital_name = current_user["hospital_name"]
    
    # Superadmin sees all claims
    if current_user["username"] == "superadmin":
        claims = await db.claims_header.find({}, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    else:
        # Regular users see only their hospital's claims
        claims = await db.claims_header.find({"hospital_name": hospital_name}, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    
    return claims

@api_router.get("/claims/{claim_id}")
async def get_claim_details(claim_id: str, current_user: dict = Depends(get_current_user)):
    claim_header = await db.claims_header.find_one({"claim_id": claim_id}, {"_id": 0})
    if not claim_header:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Check if user has access to this bill
    if current_user["role"] != "Admin" or current_user["hospital_name"] != "System Administration":
        # Regular hospital users can only see their own bills
        if claim_header["hospital_name"] != current_user["hospital_name"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    claim_details = await db.claims_details.find({"claim_id": claim_id}, {"_id": 0}).to_list(100)
    
    return {
        "header": claim_header,
        "details": claim_details
    }

@api_router.get("/admin/claims/all")
async def get_all_claims_admin(admin_user: dict = Depends(get_admin_user)):
    # Get all claims for admin (not filtered by hospital)
    claims = await db.claims_header.find({}, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    return claims

@api_router.post("/claims/{claim_id}/void")
async def void_claim(claim_id: str, current_user: dict = Depends(get_current_user)):
    # Only superadmin can void claims
    if current_user["username"] != "superadmin":
        raise HTTPException(status_code=403, detail="Only superadmin can void claims")
    
    claim = await db.claims_header.find_one({"claim_id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if claim["status"] == "VOIDED":
        raise HTTPException(status_code=400, detail="Claim already voided")
    
    # Refund the amount to family
    await db.families.update_one(
        {"family_id": claim["family_id"]},
        {"$inc": {"remaining_balance": claim["total_claim_amount"]}}
    )
    
    # Mark claim as voided
    await db.claims_header.update_one(
        {"claim_id": claim_id},
        {"$set": {"status": "VOIDED"}}
    )
    
    return {"success": True, "message": "Claim voided successfully"}

@api_router.delete("/admin/claims/{claim_id}")
async def delete_claim(claim_id: str, admin_user: dict = Depends(get_admin_user)):
    # Get claim to check if it needs refund
    claim = await db.claims_header.find_one({"claim_id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # If claim is completed, refund the amount
    if claim["status"] == "COMPLETED":
        await db.families.update_one(
            {"family_id": claim["family_id"]},
            {"$inc": {"remaining_balance": claim["total_claim_amount"]}}
        )
    
    # Delete claim details
    await db.claims_details.delete_many({"claim_id": claim_id})
    
    # Delete claim header
    await db.claims_header.delete_one({"claim_id": claim_id})
    
    return {"success": True, "message": "Claim deleted successfully"}

@api_router.put("/admin/claims/{claim_id}")
async def update_claim(claim_id: str, claim_submission: ClaimSubmission, admin_user: dict = Depends(get_admin_user)):
    # Get original claim
    original_claim = await db.claims_header.find_one({"claim_id": claim_id}, {"_id": 0})
    if not original_claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Get new patient details
    new_patient = await db.members.find_one(
        {"serial_number": claim_submission.patient_serial_number},
        {"_id": 0}
    )
    if not new_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Check if new member is suspended
    if new_patient.get("status") == "Suspended":
        raise HTTPException(status_code=403, detail="Cannot update claim for suspended member")
    
    # Get new family balance
    new_family = await db.families.find_one({"family_id": new_patient["family_id"]}, {"_id": 0})
    if not new_family:
        raise HTTPException(status_code=404, detail="Family not found")
    
    # Check if new family is suspended
    if new_family.get("status") == "Suspended":
        raise HTTPException(status_code=403, detail="Cannot update claim for suspended family")
    
    # Calculate new total
    new_total = sum(item.item_cost * item.quantity for item in claim_submission.claim_items)
    
    # Refund original family
    if original_claim["status"] == "COMPLETED":
        await db.families.update_one(
            {"family_id": original_claim["family_id"]},
            {"$inc": {"remaining_balance": original_claim["total_claim_amount"]}}
        )
    
    # Check if new family has sufficient balance
    # If same family, add back the refunded amount for the check
    available_balance = new_family["remaining_balance"]
    if original_claim["family_id"] == new_family["family_id"] and original_claim["status"] == "COMPLETED":
        available_balance += original_claim["total_claim_amount"]
    
    if new_total > available_balance:
        # Rollback the refund
        if original_claim["status"] == "COMPLETED":
            await db.families.update_one(
                {"family_id": original_claim["family_id"]},
                {"$inc": {"remaining_balance": -original_claim["total_claim_amount"]}}
            )
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient funds. Available balance: ${available_balance:.2f}, New claim amount: ${new_total:.2f}"
        )
    
    # Charge new family
    await db.families.update_one(
        {"family_id": new_patient["family_id"]},
        {"$inc": {"remaining_balance": -new_total}}
    )
    
    # Update claim header
    await db.claims_header.update_one(
        {"claim_id": claim_id},
        {"$set": {
            "patient_serial_number": new_patient["serial_number"],
            "patient_name": f"{new_patient['first_name']} {new_patient['last_name']}",
            "family_id": new_patient["family_id"],
            "total_claim_amount": new_total,
            "status": "COMPLETED"
        }}
    )
    
    # Delete old claim details
    await db.claims_details.delete_many({"claim_id": claim_id})
    
    # Insert new claim details
    for item in claim_submission.claim_items:
        claim_detail = {
            "claim_detail_id": str(uuid.uuid4()),
            "claim_id": claim_id,
            "item_id": item.item_id,
            "item_name": item.item_name,
            "item_cost": item.item_cost,
            "quantity": item.quantity
        }
        await db.claims_details.insert_one(claim_detail)
    
    # Get updated family balance
    updated_family = await db.families.find_one({"family_id": new_patient["family_id"]}, {"_id": 0})
    
    return {
        "success": True,
        "message": "Claim updated successfully",
        "claim_id": claim_id,
        "new_total": new_total,
        "new_balance": updated_family["remaining_balance"]
    }

@api_router.post("/claims/{claim_id}/pay")
async def mark_claim_as_paid(claim_id: str, current_user: dict = Depends(get_current_user)):
    # Only superadmin can mark claims as paid
    if current_user["username"] != "superadmin":
        raise HTTPException(status_code=403, detail="Only superadmin can mark claims as paid")
    
    # Get claim
    claim = await db.claims_header.find_one({"claim_id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Check if claim is completed
    if claim["status"] != "COMPLETED":
        raise HTTPException(status_code=400, detail="Only completed claims can be marked as paid")
    
    # Get hospital
    hospital = await db.hospitals.find_one({"hospital_name": current_user["hospital_name"]})
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    # Get current balance
    current_balance = hospital.get("deposit_balance", 0.0)
    claim_amount = claim["total_claim_amount"]
    
    # Check if hospital has sufficient balance
    if current_balance < claim_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient hospital balance. Available: ${current_balance:.2f}, Required: ${claim_amount:.2f}"
        )
    
    # Deduct from hospital balance
    new_balance = current_balance - claim_amount
    await db.hospitals.update_one(
        {"hospital_name": current_user["hospital_name"]},
        {"$set": {"deposit_balance": new_balance}}
    )
    
    # Update claim status to PAID
    await db.claims_header.update_one(
        {"claim_id": claim_id},
        {"$set": {"status": "PAID"}}
    )
    
    return {
        "success": True,
        "message": f"Claim marked as paid. Amount deducted: ${claim_amount:.2f}",
        "new_hospital_balance": new_balance
    }


@api_router.get("/hospital/balance")
async def get_hospital_balance(current_user: dict = Depends(get_current_user)):
    # Get hospital
    hospital = await db.hospitals.find_one({"hospital_name": current_user["hospital_name"]})
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    return {
        "hospital_name": current_user["hospital_name"],
        "deposit_balance": hospital.get("deposit_balance", 0.0)
    }


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
    
    # Check if family has claims
    claims = await db.claims_header.find_one({"family_id": family_id})
    if claims:
        raise HTTPException(status_code=400, detail="Cannot delete family with existing claims.")
    
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
        "remaining_balance": family_data.remaining_balance,
        "status": "Active"
    }
    await db.families.insert_one(family_doc)
    
    # Create members with provided or auto-generated serial numbers
    members_created = []
    for index, member_data in enumerate(family_data.members):
        # Use serial number from CSV if provided, otherwise auto-generate
        if "serial_number" in member_data and member_data["serial_number"]:
            serial_number = member_data["serial_number"]
        else:
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
            "relationship": member_data["relationship"],
            "status": "Active"
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
    # Check if member has claims
    claims = await db.claims_header.find_one({"patient_serial_number": serial_number})
    if claims:
        raise HTTPException(status_code=400, detail="Cannot delete member with existing claims.")
    
    result = await db.members.delete_one({"serial_number": serial_number})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    
    return {"success": True, "message": "Member deleted successfully"}

@api_router.post("/admin/families/{family_id}/suspend")
async def suspend_family(family_id: str, current_user: dict = Depends(get_current_user)):
    # Only superadmin can suspend families
    if current_user["username"] != "superadmin":
        raise HTTPException(status_code=403, detail="Only Super Admin can suspend families")
    
    # Check if family exists
    family = await db.families.find_one({"family_id": family_id})
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    
    # Update family status
    await db.families.update_one({"family_id": family_id}, {"$set": {"status": "Suspended"}})
    
    # Suspend all members in the family
    await db.members.update_many({"family_id": family_id}, {"$set": {"status": "Suspended"}})
    
    return {"success": True, "message": "Family and all members suspended successfully"}

@api_router.post("/admin/families/{family_id}/unsuspend")
async def unsuspend_family(family_id: str, current_user: dict = Depends(get_current_user)):
    # Only superadmin can unsuspend families
    if current_user["username"] != "superadmin":
        raise HTTPException(status_code=403, detail="Only Super Admin can unsuspend families")
    
    # Check if family exists
    family = await db.families.find_one({"family_id": family_id})
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    
    # Update family status
    await db.families.update_one({"family_id": family_id}, {"$set": {"status": "Active"}})
    
    # Unsuspend all members in the family
    await db.members.update_many({"family_id": family_id}, {"$set": {"status": "Active"}})
    
    return {"success": True, "message": "Family and all members unsuspended successfully"}

@api_router.post("/admin/members/{serial_number}/suspend")
async def suspend_member(serial_number: str, current_user: dict = Depends(get_current_user)):
    # Only superadmin can suspend members
    if current_user["username"] != "superadmin":
        raise HTTPException(status_code=403, detail="Only Super Admin can suspend members")
    
    # Check if member exists
    member = await db.members.find_one({"serial_number": serial_number})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Update member status
    await db.members.update_one({"serial_number": serial_number}, {"$set": {"status": "Suspended"}})
    
    return {"success": True, "message": "Member suspended successfully"}

@api_router.post("/admin/members/{serial_number}/unsuspend")
async def unsuspend_member(serial_number: str, current_user: dict = Depends(get_current_user)):
    # Only superadmin can unsuspend members
    if current_user["username"] != "superadmin":
        raise HTTPException(status_code=403, detail="Only Super Admin can unsuspend members")
    
    # Check if member exists
    member = await db.members.find_one({"serial_number": serial_number})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Update member status
    await db.members.update_one({"serial_number": serial_number}, {"$set": {"status": "Active"}})
    
    return {"success": True, "message": "Member unsuspended successfully"}

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

@api_router.post("/admin/hospitals/{hospital_name}/deposit")
async def add_deposit(hospital_name: str, deposit: DepositRequest, admin_user: dict = Depends(get_admin_user)):
    # Check if hospital exists
    hospital = await db.hospitals.find_one({"hospital_name": hospital_name})
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    if deposit.amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be positive")
    
    # Get current balance
    current_balance = hospital.get("deposit_balance", 0.0)
    new_balance = current_balance + deposit.amount
    
    # Update hospital balance
    await db.hospitals.update_one(
        {"hospital_name": hospital_name},
        {"$set": {"deposit_balance": new_balance}}
    )
    
    return {
        "success": True,
        "message": f"Deposit of ${deposit.amount:.2f} added successfully",
        "new_balance": new_balance
    }


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

@api_router.post("/admin/users/{username}/reset-password")
async def reset_user_password(username: str, password_reset: PasswordReset, current_user: dict = Depends(get_current_user)):
    # Only superadmin can reset passwords
    if current_user["username"] != "superadmin":
        raise HTTPException(status_code=403, detail="Only superadmin can reset passwords")
    
    # Prevent resetting superadmin password via this endpoint
    if username == "superadmin":
        raise HTTPException(status_code=400, detail="Cannot reset superadmin password via this endpoint")
    
    # Check if user exists
    user = await db.users.find_one({"username": username}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash the temporary password
    hashed_password = pwd_context.hash(password_reset.temporary_password)
    
    # Update user password and set first_login to true
    await db.users.update_one(
        {"username": username},
        {"$set": {
            "password": hashed_password,
            "first_login": True
        }}
    )
    
    return {
        "success": True,
        "message": f"Password reset for user '{username}'. User must change password on next login."
    }

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