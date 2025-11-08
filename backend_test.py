import requests
import sys
import json
from datetime import datetime

class MedicalBillingAPITester:
    def __init__(self, base_url="https://insuratrack-2.preview.emergentagent.com"):
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

    def run_comprehensive_test(self):
        """Run all tests including suspension system"""
        print("🏥 Medical Insurance Billing System - Suspension System Testing")
        print("=" * 70)
        
        # Test suspension system first (most important for this review)
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