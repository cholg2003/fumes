#!/usr/bin/env python3
"""
Focused test for the Medical Insurance Billing System Suspension Features
Tests the family/member suspension system as requested in the review.
"""

import requests
import json
import sys
from datetime import datetime

class SuspensionSystemTester:
    def __init__(self, base_url="https://insuratrack-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.superadmin_token = None
        self.regular_user_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def make_request(self, method, endpoint, token=None, data=None, expected_status=200):
        """Make API request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', 'Unknown error')
                except:
                    error_msg = response.text[:100]
                return False, {"error": f"Status {response.status_code}: {error_msg}"}

        except Exception as e:
            return False, {"error": f"Exception: {str(e)}"}

    def login(self, username, password):
        """Login and get token"""
        success, response = self.make_request(
            "POST", 
            "auth/login", 
            data={"username": username, "password": password}
        )
        
        if success and 'access_token' in response:
            return response['access_token']
        return None

    def test_authentication(self):
        """Test authentication for both superadmin and regular user"""
        print("\n🔐 Testing Authentication...")
        
        # Test superadmin login
        self.superadmin_token = self.login("superadmin", "SuperAdmin@2024")
        if self.superadmin_token:
            self.log_test("Superadmin Login", True)
        else:
            self.log_test("Superadmin Login", False, "Could not authenticate superadmin")
            return False
        
        # Test regular user login
        self.regular_user_token = self.login("test_user", "TestPass123")
        if self.regular_user_token:
            self.log_test("Regular User Login", True)
        else:
            self.log_test("Regular User Login", False, "Could not authenticate regular user")
        
        return True

    def test_family_suspension(self):
        """Test family suspension endpoints"""
        print("\n👨‍👩‍👧‍👦 Testing Family Suspension...")
        
        # Get families first
        success, families = self.make_request("GET", "admin/families", self.superadmin_token)
        if not success or not families:
            self.log_test("Get Families for Testing", False, "No families available")
            return False
        
        test_family_id = families[0]["family_id"]
        print(f"   Using family: {test_family_id}")
        
        # Test 1: Suspend family as superadmin (should succeed)
        success, response = self.make_request(
            "POST", 
            f"admin/families/{test_family_id}/suspend", 
            self.superadmin_token
        )
        self.log_test("Suspend Family - Superadmin Access", success, 
                     response.get("error", "") if not success else "")
        
        # Test 2: Try to suspend family as regular user (should fail with 403)
        if self.regular_user_token:
            success, response = self.make_request(
                "POST", 
                f"admin/families/{test_family_id}/suspend", 
                self.regular_user_token,
                expected_status=403
            )
            self.log_test("Suspend Family - Regular User Denied", success,
                         "Regular user should not be able to suspend families")
        
        # Test 3: Verify all members in family are suspended
        success, members = self.make_request("GET", "admin/members", self.superadmin_token)
        if success:
            family_members = [m for m in members if m["family_id"] == test_family_id]
            suspended_members = [m for m in family_members if m.get("status") == "Suspended"]
            
            if len(suspended_members) == len(family_members):
                self.log_test("Family Suspension Cascades to Members", True,
                             f"All {len(family_members)} members suspended")
            else:
                self.log_test("Family Suspension Cascades to Members", False,
                             f"Only {len(suspended_members)}/{len(family_members)} members suspended")
        
        # Test 4: Unsuspend family
        success, response = self.make_request(
            "POST", 
            f"admin/families/{test_family_id}/unsuspend", 
            self.superadmin_token
        )
        self.log_test("Unsuspend Family - Superadmin Access", success,
                     response.get("error", "") if not success else "")
        
        # Test 5: Try to unsuspend family as regular user (should fail with 403)
        if self.regular_user_token:
            success, response = self.make_request(
                "POST", 
                f"admin/families/{test_family_id}/unsuspend", 
                self.regular_user_token,
                expected_status=403
            )
            self.log_test("Unsuspend Family - Regular User Denied", success,
                         "Regular user should not be able to unsuspend families")
        
        return test_family_id

    def test_member_suspension(self, test_family_id):
        """Test member suspension endpoints"""
        print("\n👤 Testing Member Suspension...")
        
        # Get members of the test family
        success, members = self.make_request("GET", "admin/members", self.superadmin_token)
        if not success:
            self.log_test("Get Members for Testing", False, "Could not get members")
            return None
        
        family_members = [m for m in members if m["family_id"] == test_family_id]
        if not family_members:
            self.log_test("Find Family Members", False, f"No members found for family {test_family_id}")
            return None
        
        test_member_serial = family_members[0]["serial_number"]
        print(f"   Using member: {test_member_serial}")
        
        # Test 1: Suspend member as superadmin (should succeed)
        success, response = self.make_request(
            "POST", 
            f"admin/members/{test_member_serial}/suspend", 
            self.superadmin_token
        )
        self.log_test("Suspend Member - Superadmin Access", success,
                     response.get("error", "") if not success else "")
        
        # Test 2: Try to suspend member as regular user (should fail with 403)
        if self.regular_user_token:
            success, response = self.make_request(
                "POST", 
                f"admin/members/{test_member_serial}/suspend", 
                self.regular_user_token,
                expected_status=403
            )
            self.log_test("Suspend Member - Regular User Denied", success,
                         "Regular user should not be able to suspend members")
        
        # Test 3: Unsuspend member
        success, response = self.make_request(
            "POST", 
            f"admin/members/{test_member_serial}/unsuspend", 
            self.superadmin_token
        )
        self.log_test("Unsuspend Member - Superadmin Access", success,
                     response.get("error", "") if not success else "")
        
        # Test 4: Try to unsuspend member as regular user (should fail with 403)
        if self.regular_user_token:
            success, response = self.make_request(
                "POST", 
                f"admin/members/{test_member_serial}/unsuspend", 
                self.regular_user_token,
                expected_status=403
            )
            self.log_test("Unsuspend Member - Regular User Denied", success,
                         "Regular user should not be able to unsuspend members")
        
        return test_member_serial

    def test_search_filtering(self, test_family_id, test_member_serial):
        """Test search filtering for suspended records"""
        print("\n🔍 Testing Search Filtering...")
        
        # First suspend the family
        self.make_request("POST", f"admin/families/{test_family_id}/suspend", self.superadmin_token)
        
        # Test 1: Search for suspended family as regular user (should not return results)
        if self.regular_user_token:
            success, response = self.make_request(
                "GET", 
                f"patients/search?query={test_family_id}", 
                self.regular_user_token
            )
            
            if success:
                family_found = response.get("family") is not None
                if not family_found:
                    self.log_test("Suspended Family Hidden from Regular User", True)
                else:
                    self.log_test("Suspended Family Hidden from Regular User", False,
                                 "Suspended family visible to regular user")
        
        # Test 2: Search for suspended family as superadmin (should return results)
        success, response = self.make_request(
            "GET", 
            f"patients/search?query={test_family_id}", 
            self.superadmin_token
        )
        
        if success:
            family_found = response.get("family") is not None
            if family_found:
                self.log_test("Suspended Family Visible to Superadmin", True)
            else:
                self.log_test("Suspended Family Visible to Superadmin", False,
                             "Suspended family not visible to superadmin")
        
        # Test 3: Search for suspended member as regular user (should not return results)
        if self.regular_user_token:
            success, response = self.make_request(
                "GET", 
                f"patients/search?query={test_member_serial}", 
                self.regular_user_token
            )
            
            if success:
                results = response.get("results", [])
                member_found = any(r.get("serial_number") == test_member_serial for r in results)
                if not member_found:
                    self.log_test("Suspended Member Hidden from Regular User", True)
                else:
                    self.log_test("Suspended Member Hidden from Regular User", False,
                                 "Suspended member visible to regular user")
        
        # Test 4: Search for suspended member as superadmin (should return results)
        success, response = self.make_request(
            "GET", 
            f"patients/search?query={test_member_serial}", 
            self.superadmin_token
        )
        
        if success:
            results = response.get("results", [])
            member_found = any(r.get("serial_number") == test_member_serial for r in results)
            if member_found:
                self.log_test("Suspended Member Visible to Superadmin", True)
            else:
                self.log_test("Suspended Member Visible to Superadmin", False,
                             "Suspended member not visible to superadmin")
        
        # Unsuspend for next tests
        self.make_request("POST", f"admin/families/{test_family_id}/unsuspend", self.superadmin_token)

    def test_bill_submission_prevention(self, test_member_serial):
        """Test bill submission prevention for suspended members/families"""
        print("\n💰 Testing Bill Submission Prevention...")
        
        # Get price list
        success, price_items = self.make_request("GET", "pricelists", self.superadmin_token)
        if not success or not price_items:
            self.log_test("Get Price List for Bill Test", False, "No price items available")
            return
        
        # Suspend the member first
        self.make_request("POST", f"admin/members/{test_member_serial}/suspend", self.superadmin_token)
        
        # Test 1: Try to create bill for suspended member (should fail with 403)
        bill_data = {
            "patient_serial_number": test_member_serial,
            "bill_items": [{
                "item_id": price_items[0]["item_id"],
                "item_name": price_items[0]["item_name"],
                "item_cost": price_items[0]["cost"]
            }]
        }
        
        success, response = self.make_request(
            "POST", 
            "bills/submit", 
            self.superadmin_token,
            data=bill_data,
            expected_status=403
        )
        self.log_test("Bill Submission Blocked for Suspended Member", success,
                     "Should not be able to create bill for suspended member")
        
        # Unsuspend member and suspend family instead
        self.make_request("POST", f"admin/members/{test_member_serial}/unsuspend", self.superadmin_token)
        
        # Get member's family ID
        success, member_data = self.make_request("GET", f"patients/{test_member_serial}", self.superadmin_token)
        if success:
            family_id = member_data.get("family_id")
            if family_id:
                # Suspend the family
                self.make_request("POST", f"admin/families/{family_id}/suspend", self.superadmin_token)
                
                # Test 2: Try to create bill for member whose family is suspended (should fail with 403)
                success, response = self.make_request(
                    "POST", 
                    "bills/submit", 
                    self.superadmin_token,
                    data=bill_data,
                    expected_status=403
                )
                self.log_test("Bill Submission Blocked for Suspended Family", success,
                             "Should not be able to create bill for member of suspended family")
                
                # Unsuspend family
                self.make_request("POST", f"admin/families/{family_id}/unsuspend", self.superadmin_token)
                
                # Test 3: Create bill for active member (should succeed)
                success, response = self.make_request(
                    "POST", 
                    "bills/submit", 
                    self.superadmin_token,
                    data=bill_data
                )
                self.log_test("Bill Submission Allowed for Active Member", success,
                             response.get("error", "") if not success else "")

    def test_data_verification(self):
        """Test that all families and members have status fields"""
        print("\n📊 Testing Data Verification...")
        
        # Test 1: Verify all families have status field
        success, families = self.make_request("GET", "admin/families", self.superadmin_token)
        if success:
            families_with_status = [f for f in families if "status" in f and f["status"] in ["Active", "Suspended"]]
            if len(families_with_status) == len(families):
                self.log_test("All Families Have Valid Status Field", True,
                             f"All {len(families)} families have status field")
            else:
                self.log_test("All Families Have Valid Status Field", False,
                             f"Only {len(families_with_status)}/{len(families)} families have valid status")
        
        # Test 2: Verify all members have status field
        success, members = self.make_request("GET", "admin/members", self.superadmin_token)
        if success:
            members_with_status = [m for m in members if "status" in m and m["status"] in ["Active", "Suspended"]]
            if len(members_with_status) == len(members):
                self.log_test("All Members Have Valid Status Field", True,
                             f"All {len(members)} members have status field")
            else:
                self.log_test("All Members Have Valid Status Field", False,
                             f"Only {len(members_with_status)}/{len(members)} members have valid status")

    def run_all_tests(self):
        """Run all suspension system tests"""
        print("🏥 Medical Insurance Billing System - Suspension System Testing")
        print("=" * 70)
        
        # Test authentication
        if not self.test_authentication():
            print("\n❌ Authentication failed. Cannot proceed with testing.")
            return False
        
        # Test family suspension
        test_family_id = self.test_family_suspension()
        if not test_family_id:
            print("\n❌ Family suspension tests failed.")
            return False
        
        # Test member suspension
        test_member_serial = self.test_member_suspension(test_family_id)
        if not test_member_serial:
            print("\n❌ Member suspension tests failed.")
            return False
        
        # Test search filtering
        self.test_search_filtering(test_family_id, test_member_serial)
        
        # Test bill submission prevention
        self.test_bill_submission_prevention(test_member_serial)
        
        # Test data verification
        self.test_data_verification()
        
        # Print summary
        print(f"\n📊 Test Summary")
        print("=" * 40)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Save results
        with open('/app/suspension_test_results.json', 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_tests": self.tests_run,
                "passed_tests": self.tests_passed,
                "success_rate": (self.tests_passed/self.tests_run*100) if self.tests_run > 0 else 0,
                "results": self.test_results
            }, f, indent=2)
        
        return self.tests_passed == self.tests_run

def main():
    tester = SuspensionSystemTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())