import requests
import sys
import json
from datetime import datetime

class MedicalBillingAPITester:
    def __init__(self, base_url="https://medfinanceflow.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.hospital_name = None
        self.username = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected: {expected_status})"
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f" - {response.text[:100]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_login(self, username, password):
        """Test login and get token"""
        print(f"\n🔐 Testing login for {username}...")
        success, response = self.run_test(
            f"Login - {username}",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.hospital_name = response.get('hospital_name')
            self.username = response.get('username')
            print(f"   Hospital: {self.hospital_name}")
            print(f"   Role: {response.get('role')}")
            return True
        return False

    def test_patient_search(self):
        """Test patient search functionality"""
        print(f"\n👤 Testing patient search...")
        
        # Test search by serial number
        success, response = self.run_test(
            "Patient Search - By Serial Number",
            "GET",
            "patients/search?query=SEC-2413-01",
            200
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            patient = response[0]
            print(f"   Found patient: {patient.get('first_name')} {patient.get('last_name')}")
            print(f"   Balance: ${patient.get('remaining_balance', 0):.2f}")
        
        # Test search by name
        success, response = self.run_test(
            "Patient Search - By Name",
            "GET",
            "patients/search?query=John",
            200
        )
        
        return success

    def test_get_patient_details(self):
        """Test getting specific patient details"""
        print(f"\n📋 Testing patient details...")
        success, response = self.run_test(
            "Get Patient Details",
            "GET",
            "patients/SEC-2413-01",
            200
        )
        
        if success:
            print(f"   Patient: {response.get('first_name')} {response.get('last_name')}")
            print(f"   Family ID: {response.get('family_id')}")
            print(f"   Balance: ${response.get('remaining_balance', 0):.2f}")
        
        return success, response

    def test_price_list(self):
        """Test price list loading"""
        print(f"\n💰 Testing price list...")
        success, response = self.run_test(
            "Get Price List",
            "GET",
            "pricelists",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} items in price list")
            if len(response) > 0:
                item = response[0]
                print(f"   Sample item: {item.get('item_name')} - ${item.get('cost', 0):.2f}")
        
        return success, response

    def test_bill_submission(self, patient_data, price_items):
        """Test bill submission"""
        print(f"\n📄 Testing bill submission...")
        
        if not patient_data or not price_items:
            self.log_test("Bill Submission", False, "Missing patient data or price items")
            return False, {}
        
        # Create a small bill with first available item
        bill_items = [{
            "item_id": price_items[0]["item_id"],
            "item_name": price_items[0]["item_name"],
            "item_cost": price_items[0]["cost"]
        }]
        
        bill_data = {
            "patient_serial_number": patient_data["serial_number"],
            "bill_items": bill_items
        }
        
        success, response = self.run_test(
            "Submit Bill",
            "POST",
            "bills/submit",
            200,
            data=bill_data
        )
        
        if success:
            print(f"   Bill ID: {response.get('bill_id')}")
            print(f"   Total: ${response.get('total_amount', 0):.2f}")
            print(f"   New Balance: ${response.get('new_balance', 0):.2f}")
        
        return success, response

    def test_bill_history(self):
        """Test bill history"""
        print(f"\n📚 Testing bill history...")
        success, response = self.run_test(
            "Get Bill History",
            "GET",
            "bills",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} bills")
            if len(response) > 0:
                bill = response[0]
                print(f"   Latest bill: {bill.get('bill_id')} - ${bill.get('total_bill_amount', 0):.2f}")
        
        return success, response

    def test_bill_details(self, bill_id):
        """Test getting bill details"""
        print(f"\n🔍 Testing bill details...")
        success, response = self.run_test(
            "Get Bill Details",
            "GET",
            f"bills/{bill_id}",
            200
        )
        
        if success:
            header = response.get('header', {})
            details = response.get('details', [])
            print(f"   Bill: {header.get('bill_id')}")
            print(f"   Patient: {header.get('patient_name')}")
            print(f"   Items: {len(details)}")
        
        return success, response

    def test_void_bill(self, bill_id):
        """Test voiding a bill"""
        print(f"\n🚫 Testing bill void...")
        success, response = self.run_test(
            "Void Bill",
            "POST",
            f"bills/{bill_id}/void",
            200
        )
        
        if success:
            print(f"   Bill {bill_id} voided successfully")
        
        return success

    def test_balance_validation(self, patient_data, price_items):
        """Test balance validation (insufficient funds)"""
        print(f"\n⚠️  Testing balance validation...")
        
        if not patient_data or not price_items:
            self.log_test("Balance Validation", False, "Missing test data")
            return False
        
        # Create a bill that exceeds balance
        expensive_items = [item for item in price_items if item["cost"] > patient_data.get("remaining_balance", 0)]
        
        if not expensive_items:
            # Create artificial expensive item
            bill_items = [{
                "item_id": price_items[0]["item_id"],
                "item_name": price_items[0]["item_name"],
                "item_cost": patient_data.get("remaining_balance", 0) + 100  # Exceed balance
            }]
        else:
            bill_items = [{
                "item_id": expensive_items[0]["item_id"],
                "item_name": expensive_items[0]["item_name"],
                "item_cost": expensive_items[0]["cost"]
            }]
        
        bill_data = {
            "patient_serial_number": patient_data["serial_number"],
            "bill_items": bill_items
        }
        
        success, response = self.run_test(
            "Balance Validation - Insufficient Funds",
            "POST",
            "bills/submit",
            400,  # Should fail with 400
            data=bill_data
        )
        
        return success

    def test_admin_endpoints_access_control(self):
        """Test admin endpoints access control"""
        print(f"\n🔒 Testing admin access control...")
        
        # Test non-admin access (should get 403)
        non_admin_users = [("general_clerk", "password123"), ("city_clerk", "password123")]
        
        for username, password in non_admin_users:
            print(f"\n   Testing {username} access to admin endpoints...")
            if self.test_login(username, password):
                # Try to access admin endpoints - should fail with 403
                self.run_test(
                    f"Admin Access Control - {username} - Get Families",
                    "GET",
                    "admin/families",
                    403
                )
                
                self.run_test(
                    f"Admin Access Control - {username} - Get Members",
                    "GET",
                    "admin/members",
                    403
                )
                
                self.run_test(
                    f"Admin Access Control - {username} - Get All Pricelists",
                    "GET",
                    "admin/pricelists/all",
                    403
                )

    def test_admin_families_management(self):
        """Test admin family management"""
        print(f"\n👨‍👩‍👧‍👦 Testing admin family management...")
        
        # Get all families
        success, families = self.run_test(
            "Admin - Get All Families",
            "GET",
            "admin/families",
            200
        )
        
        if success:
            print(f"   Found {len(families)} families")
        
        # Create a new family
        test_family = {
            "family_id": f"TEST-{datetime.now().strftime('%H%M%S')}",
            "principle_member_name": "Test Family Principal",
            "total_allotment": 5000.0,
            "remaining_balance": 5000.0
        }
        
        success, response = self.run_test(
            "Admin - Create Family",
            "POST",
            "admin/families",
            200,
            data=test_family
        )
        
        if success:
            print(f"   Created family: {test_family['family_id']}")
        
        return success, test_family

    def test_admin_members_management(self, test_family):
        """Test admin member management"""
        print(f"\n👤 Testing admin member management...")
        
        # Get all members
        success, members = self.run_test(
            "Admin - Get All Members",
            "GET",
            "admin/members",
            200
        )
        
        if success:
            print(f"   Found {len(members)} members")
        
        # Create a new member
        test_member = {
            "serial_number": f"{test_family['family_id']}-01",
            "family_id": test_family['family_id'],
            "first_name": "Test",
            "middle_name": "Admin",
            "last_name": "Member",
            "dob": "1990-01-01",
            "sex": "Male",
            "relationship": "Principle"
        }
        
        success, response = self.run_test(
            "Admin - Create Member",
            "POST",
            "admin/members",
            200,
            data=test_member
        )
        
        if success:
            print(f"   Created member: {test_member['serial_number']}")
        
        return success, test_member

    def test_admin_pricelists_management(self):
        """Test admin pricelist management"""
        print(f"\n💰 Testing admin pricelist management...")
        
        # Get all pricelists
        success, pricelists = self.run_test(
            "Admin - Get All Pricelists",
            "GET",
            "admin/pricelists/all",
            200
        )
        
        if success:
            print(f"   Found {len(pricelists)} pricelist items across all hospitals")
        
        # Get hospitals
        success, hospitals = self.run_test(
            "Admin - Get Hospitals",
            "GET",
            "admin/hospitals",
            200
        )
        
        if success and hospitals:
            print(f"   Found {len(hospitals)} hospitals: {', '.join(hospitals)}")
            
            # Create a new pricelist item
            test_item = {
                "hospital_name": hospitals[0],
                "item_id": f"TEST-{datetime.now().strftime('%H%M%S')}",
                "item_name": "Test Admin Item",
                "item_type": "Service",
                "cost": 99.99
            }
            
            success, response = self.run_test(
                "Admin - Create Pricelist Item",
                "POST",
                "admin/pricelists",
                200,
                data=test_item
            )
            
            if success:
                print(f"   Created pricelist item: {test_item['item_id']}")
                
                # Test delete pricelist item
                delete_success, delete_response = self.run_test(
                    "Admin - Delete Pricelist Item",
                    "DELETE",
                    f"admin/pricelists/{test_item['hospital_name']}/{test_item['item_id']}",
                    200
                )
                
                if delete_success:
                    print(f"   Deleted pricelist item: {test_item['item_id']}")
        
        return success

    def test_cross_hospital_billing(self, test_member):
        """Test cross-hospital billing affecting same family balance"""
        print(f"\n🏥 Testing cross-hospital billing...")
        
        # First, get the current balance
        success, patient_data = self.run_test(
            "Get Test Patient Details",
            "GET",
            f"patients/{test_member['serial_number']}",
            200
        )
        
        if not success:
            self.log_test("Cross-Hospital Billing", False, "Could not get patient details")
            return False
        
        initial_balance = patient_data.get('remaining_balance', 0)
        print(f"   Initial family balance: ${initial_balance:.2f}")
        
        # Get price list for current hospital
        success, price_items = self.run_test(
            "Get Price List for Billing",
            "GET",
            "pricelists",
            200
        )
        
        if success and price_items:
            # Create a bill
            bill_items = [{
                "item_id": price_items[0]["item_id"],
                "item_name": price_items[0]["item_name"],
                "item_cost": price_items[0]["cost"]
            }]
            
            bill_data = {
                "patient_serial_number": test_member["serial_number"],
                "bill_items": bill_items
            }
            
            success, bill_response = self.run_test(
                "Cross-Hospital Bill Submission",
                "POST",
                "bills/submit",
                200,
                data=bill_data
            )
            
            if success:
                new_balance = bill_response.get('new_balance', 0)
                bill_amount = bill_response.get('total_amount', 0)
                print(f"   Bill amount: ${bill_amount:.2f}")
                print(f"   New balance: ${new_balance:.2f}")
                print(f"   Balance reduction: ${initial_balance - new_balance:.2f}")
                
                # Verify balance was correctly deducted
                expected_balance = initial_balance - bill_amount
                if abs(new_balance - expected_balance) < 0.01:
                    print("   ✅ Cross-hospital billing correctly affected family balance")
                    return True
                else:
                    self.log_test("Cross-Hospital Billing", False, f"Balance calculation error. Expected: {expected_balance}, Got: {new_balance}")
        
        return False

    def test_suspension_system(self):
        """Test the family/member suspension system"""
        print(f"\n🚫 Testing Suspension System...")
        
        # First login as superadmin
        if not self.test_login("superadmin", "SuperAdmin@2024"):
            self.log_test("Suspension System Setup", False, "Could not login as superadmin")
            return False
        
        # Get existing families and members for testing
        success, families = self.run_test(
            "Get Families for Suspension Test",
            "GET",
            "admin/families",
            200
        )
        
        if not success or not families:
            self.log_test("Suspension System Setup", False, "No families found for testing")
            return False
        
        # Use first family for testing
        test_family_id = families[0]["family_id"]
        print(f"   Using family {test_family_id} for suspension tests")
        
        # Get members of this family
        success, members = self.run_test(
            "Get Members for Suspension Test",
            "GET",
            "admin/members",
            200
        )
        
        family_members = [m for m in members if m["family_id"] == test_family_id]
        if not family_members:
            self.log_test("Suspension System Setup", False, f"No members found for family {test_family_id}")
            return False
        
        test_member_serial = family_members[0]["serial_number"]
        print(f"   Using member {test_member_serial} for suspension tests")
        
        # Test 1: Suspend Family (superadmin only)
        success, response = self.run_test(
            "Suspend Family - Superadmin",
            "POST",
            f"admin/families/{test_family_id}/suspend",
            200
        )
        
        if success:
            print(f"   ✅ Family {test_family_id} suspended successfully")
        
        # Test 2: Verify all members in family are suspended
        success, updated_members = self.run_test(
            "Verify Members Auto-Suspended",
            "GET",
            "admin/members",
            200
        )
        
        if success:
            suspended_members = [m for m in updated_members if m["family_id"] == test_family_id and m.get("status") == "Suspended"]
            if len(suspended_members) == len(family_members):
                self.log_test("Family Suspension Cascade", True, f"All {len(family_members)} members suspended")
            else:
                self.log_test("Family Suspension Cascade", False, f"Only {len(suspended_members)}/{len(family_members)} members suspended")
        
        # Test 3: Search for suspended family as non-superadmin (should not return results)
        # Login as regular user first
        regular_user_token = self.token  # Save superadmin token
        if self.test_login("general_clerk", "password123"):  # Try regular user
            success, search_response = self.run_test(
                "Search Suspended Family - Regular User",
                "GET",
                f"patients/search?query={test_family_id}",
                200
            )
            
            if success:
                if search_response.get("type") == "family" and not search_response.get("family"):
                    self.log_test("Suspended Family Hidden from Regular User", True, "Suspended family not visible to regular user")
                else:
                    self.log_test("Suspended Family Hidden from Regular User", False, "Suspended family visible to regular user")
        
        # Restore superadmin token
        self.token = regular_user_token
        
        # Test 4: Search for suspended family as superadmin (should return results)
        success, search_response = self.run_test(
            "Search Suspended Family - Superadmin",
            "GET",
            f"patients/search?query={test_family_id}",
            200
        )
        
        if success and search_response.get("type") == "family" and search_response.get("family"):
            self.log_test("Suspended Family Visible to Superadmin", True, "Suspended family visible to superadmin")
        else:
            self.log_test("Suspended Family Visible to Superadmin", False, "Suspended family not visible to superadmin")
        
        # Test 5: Try to create bill for suspended member (should fail with 403)
        # Get price list first
        success, price_items = self.run_test(
            "Get Price List for Suspension Test",
            "GET",
            "pricelists",
            200
        )
        
        if success and price_items:
            bill_data = {
                "patient_serial_number": test_member_serial,
                "bill_items": [{
                    "item_id": price_items[0]["item_id"],
                    "item_name": price_items[0]["item_name"],
                    "item_cost": price_items[0]["cost"]
                }]
            }
            
            success, response = self.run_test(
                "Bill Submission for Suspended Member",
                "POST",
                "bills/submit",
                403,  # Should fail
                data=bill_data
            )
        
        # Test 6: Unsuspend Family
        success, response = self.run_test(
            "Unsuspend Family - Superadmin",
            "POST",
            f"admin/families/{test_family_id}/unsuspend",
            200
        )
        
        if success:
            print(f"   ✅ Family {test_family_id} unsuspended successfully")
        
        # Test 7: Verify all members in family are unsuspended
        success, updated_members = self.run_test(
            "Verify Members Auto-Unsuspended",
            "GET",
            "admin/members",
            200
        )
        
        if success:
            active_members = [m for m in updated_members if m["family_id"] == test_family_id and m.get("status") == "Active"]
            if len(active_members) == len(family_members):
                self.log_test("Family Unsuspension Cascade", True, f"All {len(family_members)} members unsuspended")
            else:
                self.log_test("Family Unsuspension Cascade", False, f"Only {len(active_members)}/{len(family_members)} members unsuspended")
        
        # Test 8: Individual Member Suspension
        success, response = self.run_test(
            "Suspend Individual Member - Superadmin",
            "POST",
            f"admin/members/{test_member_serial}/suspend",
            200
        )
        
        # Test 9: Search for suspended member as regular user (should not return results)
        if self.test_login("general_clerk", "password123"):
            success, search_response = self.run_test(
                "Search Suspended Member - Regular User",
                "GET",
                f"patients/search?query={test_member_serial}",
                200
            )
            
            if success:
                results = search_response.get("results", [])
                suspended_member_found = any(r.get("serial_number") == test_member_serial for r in results)
                if not suspended_member_found:
                    self.log_test("Suspended Member Hidden from Regular User", True, "Suspended member not visible to regular user")
                else:
                    self.log_test("Suspended Member Hidden from Regular User", False, "Suspended member visible to regular user")
        
        # Restore superadmin token
        self.token = regular_user_token
        
        # Test 10: Unsuspend Individual Member
        success, response = self.run_test(
            "Unsuspend Individual Member - Superadmin",
            "POST",
            f"admin/members/{test_member_serial}/unsuspend",
            200
        )
        
        # Test 11: Test non-superadmin access to suspension endpoints (should fail with 403)
        if self.test_login("general_clerk", "password123"):
            self.run_test(
                "Suspend Family - Non-Superadmin (Should Fail)",
                "POST",
                f"admin/families/{test_family_id}/suspend",
                403
            )
            
            self.run_test(
                "Suspend Member - Non-Superadmin (Should Fail)",
                "POST",
                f"admin/members/{test_member_serial}/suspend",
                403
            )
        
        # Test 12: Verify status fields exist in all families and members
        success, all_families = self.run_test(
            "Verify Family Status Fields",
            "GET",
            "admin/families",
            200
        )
        
        if success:
            families_with_status = [f for f in all_families if "status" in f]
            if len(families_with_status) == len(all_families):
                self.log_test("Family Status Field Verification", True, f"All {len(all_families)} families have status field")
            else:
                self.log_test("Family Status Field Verification", False, f"Only {len(families_with_status)}/{len(all_families)} families have status field")
        
        success, all_members = self.run_test(
            "Verify Member Status Fields",
            "GET",
            "admin/members",
            200
        )
        
        if success:
            members_with_status = [m for m in all_members if "status" in m]
            if len(members_with_status) == len(all_members):
                self.log_test("Member Status Field Verification", True, f"All {len(all_members)} members have status field")
            else:
                self.log_test("Member Status Field Verification", False, f"Only {len(members_with_status)}/{len(all_members)} members have status field")
        
        return True

    def test_hospital_stats_endpoint(self):
        """Test the NEW Hospital Statistics endpoint"""
        print(f"\n📊 Testing Hospital Statistics Endpoint...")
        
        # Test 1: Login as superadmin to test hospital stats
        if not self.test_login("superadmin", "SuperAdmin@2024"):
            self.log_test("Hospital Stats Setup", False, "Could not login as superadmin")
            return False
        
        # Test 2: Get hospital statistics (new endpoint)
        success, stats_response = self.run_test(
            "Get Hospital Statistics - All Hospitals",
            "GET",
            "claims/hospital-stats",
            200
        )
        
        if success and isinstance(stats_response, dict):
            print(f"   Found statistics for {len(stats_response)} hospitals")
            
            # Verify structure for each hospital
            for hospital_name, stats in stats_response.items():
                print(f"   Hospital: {hospital_name}")
                
                # Check required fields
                required_fields = ['total_completed', 'total_paid', 'outstanding', 'completed_count', 'paid_count']
                missing_fields = [field for field in required_fields if field not in stats]
                
                if not missing_fields:
                    self.log_test(f"Hospital Stats Structure - {hospital_name}", True, "All required fields present")
                    
                    # Verify outstanding equals total_completed (key requirement)
                    total_completed = stats.get('total_completed', 0)
                    outstanding = stats.get('outstanding', 0)
                    
                    if total_completed == outstanding:
                        self.log_test(f"Outstanding Calculation - {hospital_name}", True, f"Outstanding (${outstanding}) equals total_completed (${total_completed})")
                    else:
                        self.log_test(f"Outstanding Calculation - {hospital_name}", False, f"Outstanding (${outstanding}) != total_completed (${total_completed})")
                    
                    # Print detailed stats
                    print(f"     Total Completed: ${stats.get('total_completed', 0)}")
                    print(f"     Total Paid: ${stats.get('total_paid', 0)}")
                    print(f"     Outstanding: ${stats.get('outstanding', 0)}")
                    print(f"     Completed Count: {stats.get('completed_count', 0)}")
                    print(f"     Paid Count: {stats.get('paid_count', 0)}")
                    
                else:
                    self.log_test(f"Hospital Stats Structure - {hospital_name}", False, f"Missing fields: {missing_fields}")
        
        # Test 3: Login as hospital admin and test access
        if self.test_login("mercy_admin", "password123"):
            success, hospital_stats = self.run_test(
                "Get Hospital Statistics - Hospital Admin",
                "GET",
                "claims/hospital-stats",
                200
            )
            
            if success:
                print(f"   Hospital admin can access stats for {len(hospital_stats)} hospitals")
        
        # Test 4: Verify calculations by cross-checking with claims data
        if self.test_login("superadmin", "SuperAdmin@2024"):
            # Get all claims to verify calculations
            success, all_claims = self.run_test(
                "Get All Claims for Verification",
                "GET",
                "claims",
                200
            )
            
            if success and all_claims:
                # Calculate expected stats manually
                expected_stats = {}
                for claim in all_claims:
                    hospital = claim.get('hospital_name')
                    status = claim.get('status')
                    amount = claim.get('total_claim_amount', 0)
                    
                    if hospital not in expected_stats:
                        expected_stats[hospital] = {
                            'total_completed': 0,
                            'total_paid': 0,
                            'completed_count': 0,
                            'paid_count': 0
                        }
                    
                    if status == 'COMPLETED':
                        expected_stats[hospital]['total_completed'] += amount
                        expected_stats[hospital]['completed_count'] += 1
                    elif status == 'PAID':
                        expected_stats[hospital]['total_paid'] += amount
                        expected_stats[hospital]['paid_count'] += 1
                
                # Compare with API response
                success, api_stats = self.run_test(
                    "Get Hospital Stats for Calculation Verification",
                    "GET",
                    "claims/hospital-stats",
                    200
                )
                
                if success:
                    for hospital, expected in expected_stats.items():
                        if hospital in api_stats:
                            api_data = api_stats[hospital]
                            
                            # Verify completed amounts
                            if abs(api_data.get('total_completed', 0) - expected['total_completed']) < 0.01:
                                self.log_test(f"Calculation Verification - {hospital} Completed Amount", True, f"${expected['total_completed']}")
                            else:
                                self.log_test(f"Calculation Verification - {hospital} Completed Amount", False, f"Expected: ${expected['total_completed']}, Got: ${api_data.get('total_completed', 0)}")
                            
                            # Verify paid amounts
                            if abs(api_data.get('total_paid', 0) - expected['total_paid']) < 0.01:
                                self.log_test(f"Calculation Verification - {hospital} Paid Amount", True, f"${expected['total_paid']}")
                            else:
                                self.log_test(f"Calculation Verification - {hospital} Paid Amount", False, f"Expected: ${expected['total_paid']}, Got: ${api_data.get('total_paid', 0)}")
                            
                            # Verify counts
                            if api_data.get('completed_count', 0) == expected['completed_count']:
                                self.log_test(f"Calculation Verification - {hospital} Completed Count", True, f"{expected['completed_count']}")
                            else:
                                self.log_test(f"Calculation Verification - {hospital} Completed Count", False, f"Expected: {expected['completed_count']}, Got: {api_data.get('completed_count', 0)}")
                            
                            if api_data.get('paid_count', 0) == expected['paid_count']:
                                self.log_test(f"Calculation Verification - {hospital} Paid Count", True, f"{expected['paid_count']}")
                            else:
                                self.log_test(f"Calculation Verification - {hospital} Paid Count", False, f"Expected: {expected['paid_count']}, Got: {api_data.get('paid_count', 0)}")
        
        return True

    def test_access_control_void_and_pay_endpoints(self):
        """Test access control for void and mark as paid endpoints - SUPERADMIN ONLY"""
        print(f"\n🔒 Testing Access Control for Void and Mark as Paid Endpoints...")
        
        # First, ensure we have test data - create a claim if needed
        if not self.test_login("superadmin", "SuperAdmin@2024"):
            self.log_test("Access Control Test Setup", False, "Could not login as superadmin")
            return False
        
        # Get existing claims to work with
        success, claims = self.run_test(
            "Get Claims for Access Control Testing",
            "GET",
            "claims",
            200
        )
        
        completed_claim_id = None
        paid_claim_id = None
        voided_claim_id = None
        
        if success and claims:
            for claim in claims:
                if claim.get("status") == "COMPLETED" and not completed_claim_id:
                    completed_claim_id = claim.get("claim_id")
                elif claim.get("status") == "PAID" and not paid_claim_id:
                    paid_claim_id = claim.get("claim_id")
                elif claim.get("status") == "VOIDED" and not voided_claim_id:
                    voided_claim_id = claim.get("claim_id")
        
        # If no COMPLETED claim exists, create one for testing
        if not completed_claim_id:
            # Get patient and price list to create a test claim
            success, patient_data = self.run_test(
                "Get Patient for Test Claim Creation",
                "GET",
                "patients/SEC-2413-01",
                200
            )
            
            success, price_items = self.run_test(
                "Get Price List for Test Claim Creation",
                "GET",
                "pricelists",
                200
            )
            
            if success and patient_data and price_items:
                claim_data = {
                    "patient_serial_number": patient_data["serial_number"],
                    "claim_items": [{
                        "item_id": price_items[0]["item_id"],
                        "item_name": price_items[0]["item_name"],
                        "item_cost": min(price_items[0]["cost"], 50.0),  # Use small amount
                        "quantity": 1
                    }]
                }
                
                success, claim_response = self.run_test(
                    "Create Test Claim for Access Control Testing",
                    "POST",
                    "claims/submit",
                    200,
                    data=claim_data
                )
                
                if success:
                    completed_claim_id = claim_response.get('claim_id')
                    print(f"   Created test claim: {completed_claim_id}")
        
        print(f"   Test claims - COMPLETED: {completed_claim_id}, PAID: {paid_claim_id}, VOIDED: {voided_claim_id}")
        
        # Test different user roles
        test_users = [
            ("mercy_admin", "password123", "Admin"),
            ("general_clerk", "password123", "Finance"),  # Assuming this is Finance role
            ("city_clerk", "password123", "Reception")    # Assuming this is Reception role
        ]
        
        # === VOID CLAIM ENDPOINT TESTS ===
        print(f"\n   🚫 Testing VOID endpoint access control...")
        
        # Test 1: Superadmin can void COMPLETED claim (should succeed)
        if completed_claim_id:
            success, response = self.run_test(
                "Void Claim - Superadmin (Should Succeed)",
                "POST",
                f"claims/{completed_claim_id}/void",
                200
            )
            
            if success:
                print(f"   ✅ Superadmin successfully voided claim {completed_claim_id}")
                voided_claim_id = completed_claim_id  # Now this claim is voided
                completed_claim_id = None  # No longer completed
        
        # Test 2-4: Non-superadmin users cannot void claims (should fail with 403)
        for username, password, role in test_users:
            if self.test_login(username, password):
                # Try to void a claim (use any claim ID, should fail regardless)
                test_claim_id = voided_claim_id or paid_claim_id or "DUMMY-CLAIM"
                success, response = self.run_test(
                    f"Void Claim - {role} User (Should Fail with 403)",
                    "POST",
                    f"claims/{test_claim_id}/void",
                    403
                )
        
        # Test 5: Voiding already VOIDED claim should fail (400)
        if voided_claim_id:
            if self.test_login("superadmin", "SuperAdmin@2024"):
                success, response = self.run_test(
                    "Void Already Voided Claim (Should Fail with 400)",
                    "POST",
                    f"claims/{voided_claim_id}/void",
                    400
                )
        
        # Test 6: Voiding non-existent claim should fail (404)
        if self.test_login("superadmin", "SuperAdmin@2024"):
            success, response = self.run_test(
                "Void Non-existent Claim (Should Fail with 404)",
                "POST",
                "claims/NONEXISTENT-CLAIM-ID/void",
                404
            )
        
        # === MARK AS PAID ENDPOINT TESTS ===
        print(f"\n   💰 Testing MARK AS PAID endpoint access control...")
        
        # Create another COMPLETED claim for payment testing if needed
        if not completed_claim_id:
            if self.test_login("superadmin", "SuperAdmin@2024"):
                success, patient_data = self.run_test(
                    "Get Patient for Payment Test Claim",
                    "GET",
                    "patients/SEC-2413-01",
                    200
                )
                
                success, price_items = self.run_test(
                    "Get Price List for Payment Test Claim",
                    "GET",
                    "pricelists",
                    200
                )
                
                if success and patient_data and price_items:
                    claim_data = {
                        "patient_serial_number": patient_data["serial_number"],
                        "claim_items": [{
                            "item_id": price_items[0]["item_id"],
                            "item_name": price_items[0]["item_name"],
                            "item_cost": min(price_items[0]["cost"], 30.0),
                            "quantity": 1
                        }]
                    }
                    
                    success, claim_response = self.run_test(
                        "Create Test Claim for Payment Testing",
                        "POST",
                        "claims/submit",
                        200,
                        data=claim_data
                    )
                    
                    if success:
                        completed_claim_id = claim_response.get('claim_id')
                        print(f"   Created test claim for payment: {completed_claim_id}")
        
        # Ensure hospital has sufficient balance for payment tests
        if self.test_login("superadmin", "SuperAdmin@2024"):
            success, response = self.run_test(
                "Add Deposit for Payment Testing",
                "POST",
                "admin/hospitals/System Administration/deposit",
                200,
                data={"amount": 1000.0}
            )
        
        # Test 1: Superadmin can mark COMPLETED claim as PAID (should succeed)
        if completed_claim_id:
            if self.test_login("superadmin", "SuperAdmin@2024"):
                success, response = self.run_test(
                    "Mark Claim as Paid - Superadmin (Should Succeed)",
                    "POST",
                    f"claims/{completed_claim_id}/pay",
                    200
                )
                
                if success:
                    print(f"   ✅ Superadmin successfully marked claim {completed_claim_id} as paid")
                    paid_claim_id = completed_claim_id  # Now this claim is paid
                    completed_claim_id = None  # No longer completed
        
        # Test 2-4: Non-superadmin users cannot mark claims as paid (should fail with 403)
        for username, password, role in test_users:
            if self.test_login(username, password):
                # Try to mark a claim as paid (use any claim ID, should fail regardless)
                test_claim_id = paid_claim_id or voided_claim_id or "DUMMY-CLAIM"
                success, response = self.run_test(
                    f"Mark Claim as Paid - {role} User (Should Fail with 403)",
                    "POST",
                    f"claims/{test_claim_id}/pay",
                    403
                )
        
        # Test 5: Marking already PAID claim should fail (400)
        if paid_claim_id:
            if self.test_login("superadmin", "SuperAdmin@2024"):
                success, response = self.run_test(
                    "Mark Already Paid Claim as Paid (Should Fail with 400)",
                    "POST",
                    f"claims/{paid_claim_id}/pay",
                    400
                )
        
        # Test 6: Marking VOIDED claim should fail (400)
        if voided_claim_id:
            if self.test_login("superadmin", "SuperAdmin@2024"):
                success, response = self.run_test(
                    "Mark Voided Claim as Paid (Should Fail with 400)",
                    "POST",
                    f"claims/{voided_claim_id}/pay",
                    400
                )
        
        # Test 7: Marking non-existent claim should fail (404)
        if self.test_login("superadmin", "SuperAdmin@2024"):
            success, response = self.run_test(
                "Mark Non-existent Claim as Paid (Should Fail with 404)",
                "POST",
                "claims/NONEXISTENT-CLAIM-ID/pay",
                404
            )
        
        # Test 8: Marking with insufficient balance should fail (400)
        # First, reduce hospital balance to very low amount
        if self.test_login("superadmin", "SuperAdmin@2024"):
            # Get current balance
            success, balance_response = self.run_test(
                "Get Current Balance for Insufficient Funds Test",
                "GET",
                "hospital/balance",
                200
            )
            
            if success:
                current_balance = balance_response.get('deposit_balance', 0)
                
                # Create a high-value claim if we have sufficient family balance
                success, patient_data = self.run_test(
                    "Get Patient for High Value Claim",
                    "GET",
                    "patients/SEC-2413-01",
                    200
                )
                
                if success and patient_data and patient_data.get('remaining_balance', 0) > current_balance + 100:
                    success, price_items = self.run_test(
                        "Get Price List for High Value Claim",
                        "GET",
                        "pricelists",
                        200
                    )
                    
                    if success and price_items:
                        high_amount = current_balance + 100  # More than hospital balance
                        
                        claim_data = {
                            "patient_serial_number": patient_data["serial_number"],
                            "claim_items": [{
                                "item_id": price_items[0]["item_id"],
                                "item_name": price_items[0]["item_name"],
                                "item_cost": high_amount,
                                "quantity": 1
                            }]
                        }
                        
                        success, claim_response = self.run_test(
                            "Create High Value Claim for Insufficient Balance Test",
                            "POST",
                            "claims/submit",
                            200,
                            data=claim_data
                        )
                        
                        if success:
                            high_claim_id = claim_response.get('claim_id')
                            success, response = self.run_test(
                                "Mark High Value Claim as Paid - Insufficient Hospital Balance (Should Fail with 400)",
                                "POST",
                                f"claims/{high_claim_id}/pay",
                                400
                            )
        
        print(f"   ✅ Access control testing completed for void and mark as paid endpoints")
        return True

    def test_hospital_payment_deposit_system(self):
        """Test the Hospital Payment and Deposit System feature"""
        print(f"\n💰 Testing Hospital Payment and Deposit System...")
        
        # First login as superadmin for deposit operations
        if not self.test_login("superadmin", "SuperAdmin@2024"):
            self.log_test("Hospital Payment System Setup", False, "Could not login as superadmin")
            return False
        
        # Test 1: Add deposit to hospital (positive amount)
        test_hospital = "System Administration"
        deposit_amount = 500.0
        
        success, response = self.run_test(
            "Add Hospital Deposit - Valid Amount",
            "POST",
            f"admin/hospitals/{test_hospital}/deposit",
            200,
            data={"amount": deposit_amount}
        )
        
        if success:
            print(f"   ✅ Added ${deposit_amount} deposit to {test_hospital}")
            print(f"   New balance: ${response.get('new_balance', 0):.2f}")
        
        # Test 2: Try to add negative deposit (should fail)
        success, response = self.run_test(
            "Add Hospital Deposit - Negative Amount (Should Fail)",
            "POST",
            f"admin/hospitals/{test_hospital}/deposit",
            400,
            data={"amount": -100.0}
        )
        
        # Test 3: Try to add zero deposit (should fail)
        success, response = self.run_test(
            "Add Hospital Deposit - Zero Amount (Should Fail)",
            "POST",
            f"admin/hospitals/{test_hospital}/deposit",
            400,
            data={"amount": 0.0}
        )
        
        # Test 4: Try to add deposit to non-existent hospital (should fail)
        success, response = self.run_test(
            "Add Hospital Deposit - Non-existent Hospital (Should Fail)",
            "POST",
            "admin/hospitals/NonExistentHospital/deposit",
            404,
            data={"amount": 100.0}
        )
        
        # Test 5: Try to add deposit as non-admin user (should fail)
        # Login as regular user
        regular_user_token = self.token  # Save superadmin token
        if self.test_login("general_clerk", "password123"):
            success, response = self.run_test(
                "Add Hospital Deposit - Non-Admin User (Should Fail)",
                "POST",
                f"admin/hospitals/{test_hospital}/deposit",
                403,
                data={"amount": 100.0}
            )
        
        # Restore superadmin token
        self.token = regular_user_token
        
        # Test 6: Get hospital balance as authenticated user
        # Login as System Administration user to test balance endpoint
        if self.test_login("superadmin", "SuperAdmin@2024"):  # Superadmin belongs to System Administration
            success, response = self.run_test(
                "Get Hospital Balance - Authenticated User",
                "GET",
                "hospital/balance",
                200
            )
            
            if success:
                hospital_name = response.get('hospital_name')
                balance = response.get('deposit_balance', 0)
                print(f"   Hospital: {hospital_name}")
                print(f"   Current balance: ${balance:.2f}")
                
                # Store balance for payment tests
                initial_balance = balance
        
        # Test 7: Get existing claims to test payment functionality
        success, claims = self.run_test(
            "Get Claims for Payment Testing",
            "GET",
            "claims",
            200
        )
        
        completed_claim_id = None
        paid_claim_id = None
        voided_claim_id = None
        
        if success and claims:
            # Find claims with different statuses
            for claim in claims:
                if claim.get("status") == "COMPLETED" and not completed_claim_id:
                    completed_claim_id = claim.get("claim_id")
                elif claim.get("status") == "PAID" and not paid_claim_id:
                    paid_claim_id = claim.get("claim_id")
                elif claim.get("status") == "VOIDED" and not voided_claim_id:
                    voided_claim_id = claim.get("claim_id")
            
            print(f"   Found claims - COMPLETED: {completed_claim_id}, PAID: {paid_claim_id}, VOIDED: {voided_claim_id}")
        
        # Test 8: Mark completed claim as paid (should succeed)
        if completed_claim_id:
            success, response = self.run_test(
                "Mark Completed Claim as Paid",
                "POST",
                f"claims/{completed_claim_id}/pay",
                200
            )
            
            if success:
                deducted_amount = response.get('message', '').split('$')[1].split('.')[0] if '$' in response.get('message', '') else 'Unknown'
                new_balance = response.get('new_hospital_balance', 0)
                print(f"   ✅ Claim {completed_claim_id} marked as paid")
                print(f"   Amount deducted: ${deducted_amount}")
                print(f"   New hospital balance: ${new_balance:.2f}")
        
        # Test 9: Try to mark already paid claim as paid again (should fail)
        if paid_claim_id:
            success, response = self.run_test(
                "Mark Already Paid Claim as Paid (Should Fail)",
                "POST",
                f"claims/{paid_claim_id}/pay",
                400
            )
        
        # Test 10: Try to mark voided claim as paid (should fail)
        if voided_claim_id:
            success, response = self.run_test(
                "Mark Voided Claim as Paid (Should Fail)",
                "POST",
                f"claims/{voided_claim_id}/pay",
                400
            )
        
        # Test 11: Try to mark non-existent claim as paid (should fail)
        success, response = self.run_test(
            "Mark Non-existent Claim as Paid (Should Fail)",
            "POST",
            "claims/NONEXISTENT-CLAIM/pay",
            404
        )
        
        # Test 12: Create a scenario with insufficient balance
        # First, get current balance
        success, balance_response = self.run_test(
            "Get Current Balance for Insufficient Funds Test",
            "GET",
            "hospital/balance",
            200
        )
        
        if success:
            current_balance = balance_response.get('deposit_balance', 0)
            
            # Create a test claim with amount higher than balance
            # First get a patient and price list
            success, patient_data = self.run_test(
                "Get Patient for High Amount Claim",
                "GET",
                "patients/SEC-2413-01",
                200
            )
            
            success, price_items = self.run_test(
                "Get Price List for High Amount Claim",
                "GET",
                "pricelists",
                200
            )
            
            if success and patient_data and price_items:
                # Create a claim with high amount
                high_amount = current_balance + 1000  # More than current balance
                
                claim_data = {
                    "patient_serial_number": patient_data["serial_number"],
                    "claim_items": [{
                        "item_id": price_items[0]["item_id"],
                        "item_name": price_items[0]["item_name"],
                        "item_cost": high_amount,
                        "quantity": 1
                    }]
                }
                
                # This should fail due to insufficient family balance, but let's try
                success, claim_response = self.run_test(
                    "Create High Amount Claim",
                    "POST",
                    "claims/submit",
                    400  # Should fail due to insufficient family balance
                )
                
                # If somehow it succeeds, try to pay it (should fail due to insufficient hospital balance)
                if success and claim_response.get('claim_id'):
                    high_claim_id = claim_response['claim_id']
                    success, response = self.run_test(
                        "Mark High Amount Claim as Paid - Insufficient Hospital Balance (Should Fail)",
                        "POST",
                        f"claims/{high_claim_id}/pay",
                        400
                    )
        
        # Test 13: Test claim from different hospital (permission check)
        # Login as a different hospital user
        if self.test_login("mercy_admin", "password123"):  # Different hospital
            # Try to mark a System Administration claim as paid
            if completed_claim_id:
                success, response = self.run_test(
                    "Mark Claim from Different Hospital as Paid (Should Fail)",
                    "POST",
                    f"claims/{completed_claim_id}/pay",
                    403
                )
        
        # Test 14: Verify claim status changes from COMPLETED to PAID
        # Login back as System Administration user
        if self.test_login("superadmin", "SuperAdmin@2024"):
            # Get updated claims list to verify status changes
            success, updated_claims = self.run_test(
                "Verify Claim Status Changes",
                "GET",
                "claims",
                200
            )
            
            if success and updated_claims:
                # Check if our completed claim is now marked as PAID
                for claim in updated_claims:
                    if claim.get("claim_id") == completed_claim_id:
                        if claim.get("status") == "PAID":
                            self.log_test("Claim Status Change Verification", True, f"Claim {completed_claim_id} status changed to PAID")
                        else:
                            self.log_test("Claim Status Change Verification", False, f"Claim {completed_claim_id} status is {claim.get('status')}, expected PAID")
                        break
        
        # Test 15: Verify hospital balance is correctly deducted
        success, final_balance_response = self.run_test(
            "Verify Final Hospital Balance",
            "GET",
            "hospital/balance",
            200
        )
        
        if success:
            final_balance = final_balance_response.get('deposit_balance', 0)
            print(f"   Final hospital balance: ${final_balance:.2f}")
            
            # The balance should be less than initial balance if we successfully paid claims
            if final_balance < initial_balance:
                self.log_test("Hospital Balance Deduction Verification", True, f"Balance correctly deducted from ${initial_balance:.2f} to ${final_balance:.2f}")
            else:
                self.log_test("Hospital Balance Deduction Verification", False, f"Balance not deducted properly. Initial: ${initial_balance:.2f}, Final: ${final_balance:.2f}")
        
        return True

    def test_superadmin_only_access_control(self):
        """Test that only Superadmin can perform CRUD operations on Families, Members, and Price Lists"""
        print(f"\n🔒 Testing Superadmin-Only Access Control for Families, Members, and Price Lists...")
        
        # Test data for creating entities
        test_family_data = {
            "family_id": f"TEST-FAM-{datetime.now().strftime('%H%M%S')}",
            "principle_member_name": "Test Family Principal",
            "total_allotment": 5000.0,
            "remaining_balance": 5000.0,
            "status": "Active"
        }
        
        test_member_data = {
            "serial_number": f"{test_family_data['family_id']}-01",
            "family_id": test_family_data['family_id'],
            "first_name": "Test",
            "middle_name": "Access",
            "last_name": "Member",
            "dob": "1990-01-01",
            "sex": "Male",
            "relationship": "Principle",
            "status": "Active"
        }
        
        test_pricelist_data = {
            "hospital_name": "System Administration",
            "item_id": f"TEST-ITEM-{datetime.now().strftime('%H%M%S')}",
            "item_name": "Test Access Control Item",
            "item_type": "Service",
            "cost": 99.99
        }
        
        # === SUPERADMIN ACCESS TESTS (Should all SUCCEED) ===
        print(f"\n   ✅ Testing Superadmin Access (Should all SUCCEED)...")
        
        if not self.test_login("superadmin", "SuperAdmin@2024"):
            self.log_test("Superadmin Access Control Setup", False, "Could not login as superadmin")
            return False
        
        # Test Family CRUD - Superadmin
        success, response = self.run_test(
            "Superadmin - Create Family",
            "POST",
            "admin/families",
            200,
            data=test_family_data
        )
        family_created = success
        
        if family_created:
            # Update family
            success, response = self.run_test(
                "Superadmin - Update Family",
                "PUT",
                f"admin/families/{test_family_data['family_id']}",
                200,
                data={"principle_member_name": "Updated Family Principal"}
            )
        
        # Test Member CRUD - Superadmin
        if family_created:
            success, response = self.run_test(
                "Superadmin - Create Member",
                "POST",
                "admin/members",
                200,
                data=test_member_data
            )
            member_created = success
            
            if member_created:
                # Update member
                success, response = self.run_test(
                    "Superadmin - Update Member",
                    "PUT",
                    f"admin/members/{test_member_data['serial_number']}",
                    200,
                    data={"first_name": "Updated Test"}
                )
        
        # Test Price List CRUD - Superadmin
        success, response = self.run_test(
            "Superadmin - Create Price List Item",
            "POST",
            "admin/pricelists",
            200,
            data=test_pricelist_data
        )
        pricelist_created = success
        
        if pricelist_created:
            # Update price list item
            success, response = self.run_test(
                "Superadmin - Update Price List Item",
                "PUT",
                f"admin/pricelists/{test_pricelist_data['hospital_name']}/{test_pricelist_data['item_id']}",
                200,
                data={"cost": 149.99}
            )
        
        # Test Bulk operations - Superadmin
        bulk_family_data = {
            "family_id": f"BULK-FAM-{datetime.now().strftime('%H%M%S')}",
            "principle_member_name": "Bulk Test Family",
            "total_allotment": 3000.0,
            "remaining_balance": 3000.0,
            "members": [
                {
                    "first_name": "Bulk",
                    "last_name": "Member1",
                    "dob": "1985-01-01",
                    "sex": "Male",
                    "relationship": "Principle"
                }
            ]
        }
        
        success, response = self.run_test(
            "Superadmin - Bulk Create Family with Members",
            "POST",
            "admin/families/bulk",
            200,
            data=bulk_family_data
        )
        
        bulk_pricelist_data = {
            "hospital_name": "System Administration",
            "items": [
                {
                    "item_id": f"BULK-ITEM-{datetime.now().strftime('%H%M%S')}",
                    "item_name": "Bulk Test Item",
                    "item_type": "Service",
                    "cost": 75.00
                }
            ]
        }
        
        success, response = self.run_test(
            "Superadmin - Bulk Create Price List Items",
            "POST",
            "admin/pricelists/bulk",
            200,
            data=bulk_pricelist_data
        )
        
        # === HOSPITAL ADMIN ACCESS TESTS (Should all FAIL with 403) ===
        print(f"\n   ❌ Testing Hospital Admin Access (Should all FAIL with 403)...")
        
        # Create a test hospital admin user if needed, or use existing one
        hospital_admin_users = [
            ("mercy_admin", "password123"),
            ("general_clerk", "password123"),  # Try different admin users
        ]
        
        hospital_admin_logged_in = False
        for username, password in hospital_admin_users:
            if self.test_login(username, password):
                hospital_admin_logged_in = True
                print(f"   Using hospital admin: {username}")
                break
        
        if not hospital_admin_logged_in:
            self.log_test("Hospital Admin Access Control Setup", False, "Could not login as hospital admin")
            return False
        
        # Test Family CRUD - Hospital Admin (should all fail with 403)
        test_family_data2 = {
            "family_id": f"ADMIN-FAM-{datetime.now().strftime('%H%M%S')}",
            "principle_member_name": "Admin Test Family",
            "total_allotment": 2000.0,
            "remaining_balance": 2000.0,
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Hospital Admin - Create Family (Should Fail)",
            "POST",
            "admin/families",
            403,
            data=test_family_data2
        )
        
        # Try to update existing family
        if family_created:
            success, response = self.run_test(
                "Hospital Admin - Update Family (Should Fail)",
                "PUT",
                f"admin/families/{test_family_data['family_id']}",
                403,
                data={"principle_member_name": "Admin Updated Name"}
            )
            
            success, response = self.run_test(
                "Hospital Admin - Delete Family (Should Fail)",
                "DELETE",
                f"admin/families/{test_family_data['family_id']}",
                403
            )
        
        # Test Member CRUD - Hospital Admin (should all fail with 403)
        test_member_data2 = {
            "serial_number": f"{test_family_data2['family_id']}-01",
            "family_id": test_family_data2['family_id'],
            "first_name": "Admin",
            "last_name": "Member",
            "dob": "1990-01-01",
            "sex": "Female",
            "relationship": "Principle",
            "status": "Active"
        }
        
        success, response = self.run_test(
            "Hospital Admin - Create Member (Should Fail)",
            "POST",
            "admin/members",
            403,
            data=test_member_data2
        )
        
        # Try to update existing member
        if member_created:
            success, response = self.run_test(
                "Hospital Admin - Update Member (Should Fail)",
                "PUT",
                f"admin/members/{test_member_data['serial_number']}",
                403,
                data={"first_name": "Admin Updated"}
            )
            
            success, response = self.run_test(
                "Hospital Admin - Delete Member (Should Fail)",
                "DELETE",
                f"admin/members/{test_member_data['serial_number']}",
                403
            )
        
        # Test Price List CRUD - Hospital Admin (should all fail with 403)
        test_pricelist_data2 = {
            "hospital_name": "System Administration",
            "item_id": f"ADMIN-ITEM-{datetime.now().strftime('%H%M%S')}",
            "item_name": "Admin Test Item",
            "item_type": "Service",
            "cost": 199.99
        }
        
        success, response = self.run_test(
            "Hospital Admin - Create Price List Item (Should Fail)",
            "POST",
            "admin/pricelists",
            403,
            data=test_pricelist_data2
        )
        
        # Try to update existing price list item
        if pricelist_created:
            success, response = self.run_test(
                "Hospital Admin - Update Price List Item (Should Fail)",
                "PUT",
                f"admin/pricelists/{test_pricelist_data['hospital_name']}/{test_pricelist_data['item_id']}",
                403,
                data={"cost": 299.99}
            )
            
            success, response = self.run_test(
                "Hospital Admin - Delete Price List Item (Should Fail)",
                "DELETE",
                f"admin/pricelists/{test_pricelist_data['hospital_name']}/{test_pricelist_data['item_id']}",
                403
            )
        
        # Test Bulk operations - Hospital Admin (should fail with 403)
        success, response = self.run_test(
            "Hospital Admin - Bulk Create Family (Should Fail)",
            "POST",
            "admin/families/bulk",
            403,
            data=bulk_family_data
        )
        
        success, response = self.run_test(
            "Hospital Admin - Bulk Create Price List (Should Fail)",
            "POST",
            "admin/pricelists/bulk",
            403,
            data=bulk_pricelist_data
        )
        
        # === TEST WHAT HOSPITAL ADMIN CAN STILL DO (Should SUCCEED) ===
        print(f"\n   ✅ Testing Hospital Admin READ Access (Should SUCCEED)...")
        
        # Hospital Admin should still be able to VIEW (GET) these entities
        success, response = self.run_test(
            "Hospital Admin - View Families (Should Succeed)",
            "GET",
            "admin/families",
            200
        )
        
        success, response = self.run_test(
            "Hospital Admin - View Members (Should Succeed)",
            "GET",
            "admin/members",
            200
        )
        
        success, response = self.run_test(
            "Hospital Admin - View Price Lists (Should Succeed)",
            "GET",
            "admin/pricelists/all",
            200
        )
        
        # Hospital Admin should still be able to submit claims
        success, patient_data = self.run_test(
            "Hospital Admin - Get Patient for Claim Test",
            "GET",
            "patients/SEC-2413-01",
            200
        )
        
        success, price_items = self.run_test(
            "Hospital Admin - Get Price List for Claim Test",
            "GET",
            "pricelists",
            200
        )
        
        if success and patient_data and price_items:
            claim_data = {
                "patient_serial_number": patient_data["serial_number"],
                "claim_items": [{
                    "item_id": price_items[0]["item_id"],
                    "item_name": price_items[0]["item_name"],
                    "item_cost": min(price_items[0]["cost"], 25.0),
                    "quantity": 1
                }]
            }
            
            success, response = self.run_test(
                "Hospital Admin - Submit Claim (Should Succeed)",
                "POST",
                "claims/submit",
                200,
                data=claim_data
            )
        
        # Hospital Admin should be able to view financial dashboard
        success, response = self.run_test(
            "Hospital Admin - View Hospital Balance (Should Succeed)",
            "GET",
            "hospital/balance",
            200
        )
        
        success, response = self.run_test(
            "Hospital Admin - View Claims (Should Succeed)",
            "GET",
            "claims",
            200
        )
        
        # === CLEANUP - Delete test entities ===
        print(f"\n   🧹 Cleaning up test entities...")
        
        # Login back as superadmin for cleanup
        if self.test_login("superadmin", "SuperAdmin@2024"):
            # Delete test entities created during testing
            if member_created:
                success, response = self.run_test(
                    "Cleanup - Delete Test Member",
                    "DELETE",
                    f"admin/members/{test_member_data['serial_number']}",
                    200
                )
            
            if family_created:
                success, response = self.run_test(
                    "Cleanup - Delete Test Family",
                    "DELETE",
                    f"admin/families/{test_family_data['family_id']}",
                    200
                )
            
            if pricelist_created:
                success, response = self.run_test(
                    "Cleanup - Delete Test Price List Item",
                    "DELETE",
                    f"admin/pricelists/{test_pricelist_data['hospital_name']}/{test_pricelist_data['item_id']}",
                    200
                )
        
        print(f"   ✅ Superadmin-only access control testing completed")
        return True

    def run_comprehensive_test(self):
        """Run all tests including access control for Families, Members, and Price Lists"""
        print("🏥 Medical Insurance Billing System - Access Control Testing for Families, Members, and Price Lists")
        print("=" * 80)
        
        # Test MAIN FOCUS: Superadmin-only access control for Families, Members, and Price Lists
        self.test_superadmin_only_access_control()
        
        # Test ACCESS CONTROL for void and mark as paid endpoints
        self.test_access_control_void_and_pay_endpoints()
        
        # Test NEW hospital statistics endpoint 
        self.test_hospital_stats_endpoint()
        
        # Test hospital payment and deposit system 
        self.test_hospital_payment_deposit_system()
        
        # Test suspension system 
        self.test_suspension_system()
        
        # Test different user credentials for basic functionality
        test_users = [
            ("general_clerk", "password123"),
            ("city_clerk", "password123"),
            ("mercy_admin", "password123")
        ]
        
        successful_login = False
        patient_data = None
        price_items = None
        bill_id = None
        admin_logged_in = False
        test_family = None
        test_member = None
        
        # Test admin access control first (with non-admin users)
        self.test_admin_endpoints_access_control()
        
        # Try to login with admin user for admin tests
        print(f"\n🔐 Testing admin login...")
        if self.test_login("mercy_admin", "password123"):
            admin_logged_in = True
            successful_login = True
            
            # Test admin functionality
            success, test_family = self.test_admin_families_management()
            if success and test_family:
                success, test_member = self.test_admin_members_management(test_family)
            
            self.test_admin_pricelists_management()
            
            # Test cross-hospital billing if we have test member
            if test_member:
                self.test_cross_hospital_billing(test_member)
        
        # If admin login failed, try other users for basic tests
        if not successful_login:
            for username, password in test_users[:2]:  # Skip admin since we already tried
                if self.test_login(username, password):
                    successful_login = True
                    break
        
        if not successful_login:
            print("\n❌ All login attempts failed. Cannot proceed with testing.")
            return False
        
        # Test basic functionality (if not admin, login with regular user)
        if not admin_logged_in:
            self.test_login("general_clerk", "password123")
        
        # Test patient search
        self.test_patient_search()
        
        # Get patient details
        success, patient_data = self.test_get_patient_details()
        
        # Get price list
        success, price_items = self.test_price_list()
        
        # Test balance validation (should fail)
        if patient_data and price_items:
            self.test_balance_validation(patient_data, price_items)
            
            # Test bill submission (should succeed)
            success, bill_response = self.test_bill_submission(patient_data, price_items)
            if success:
                bill_id = bill_response.get('bill_id')
        
        # Test bill history
        self.test_bill_history()
        
        # Test bill details
        if bill_id:
            self.test_bill_details(bill_id)
            
            # Test void bill
            self.test_void_bill(bill_id)
        
        # Print summary
        print(f"\n📊 Test Summary")
        print("=" * 40)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = MedicalBillingAPITester()
    success = tester.run_comprehensive_test()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
            "results": tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())