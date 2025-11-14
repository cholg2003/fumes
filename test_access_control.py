#!/usr/bin/env python3

import requests
import json
from datetime import datetime

class AccessControlTester:
    def __init__(self):
        self.base_url = "https://global-currency-6.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
    
    def login(self, username, password):
        """Login and return token"""
        response = requests.post(f"{self.api_url}/auth/login", 
                               json={"username": username, "password": password})
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    
    def test_endpoint(self, name, method, endpoint, token, expected_status, data=None):
        """Test an endpoint with expected status"""
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        url = f"{self.api_url}/{endpoint}"
        
        try:
            if method == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            elif method == "GET":
                response = requests.get(url, headers=headers)
            
            success = response.status_code == expected_status
            if success:
                self.log_test(name, True)
                return True, response.json() if response.content else {}
            else:
                error_msg = f"Status: {response.status_code} (Expected: {expected_status})"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    pass
                self.log_test(name, False, error_msg)
                return False, {}
        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}
    
    def run_access_control_tests(self):
        """Run comprehensive access control tests"""
        print("🔒 Testing Access Control for Families, Members, and Price Lists")
        print("=" * 70)
        
        # Get tokens
        superadmin_token = self.login("superadmin", "SuperAdmin@2024")
        hospital_admin_token = self.login("test_hospital_admin", "TempAdmin@2024")
        
        if not superadmin_token:
            print("❌ Failed to login as superadmin")
            return False
            
        if not hospital_admin_token:
            print("❌ Failed to login as hospital admin")
            return False
        
        print("✅ Both users logged in successfully")
        
        # Test data
        timestamp = datetime.now().strftime('%H%M%S')
        test_family = {
            "family_id": f"TEST-FAM-{timestamp}",
            "principle_member_name": "Test Family Principal",
            "total_allotment": 5000.0,
            "remaining_balance": 5000.0,
            "status": "Active"
        }
        
        test_member = {
            "serial_number": f"{test_family['family_id']}-01",
            "family_id": test_family['family_id'],
            "first_name": "Test",
            "last_name": "Member",
            "dob": "1990-01-01",
            "sex": "Male",
            "relationship": "Principle",
            "status": "Active"
        }
        
        test_pricelist = {
            "hospital_name": "System Administration",
            "item_id": f"TEST-ITEM-{timestamp}",
            "item_name": "Test Access Control Item",
            "item_type": "Service",
            "cost": 99.99
        }
        
        print(f"\n🟢 SUPERADMIN TESTS (Should all SUCCEED)")
        print("-" * 50)
        
        # Superadmin Family CRUD
        family_created, _ = self.test_endpoint(
            "Superadmin - Create Family", "POST", "admin/families", 
            superadmin_token, 200, test_family
        )
        
        if family_created:
            self.test_endpoint(
                "Superadmin - Update Family", "PUT", f"admin/families/{test_family['family_id']}", 
                superadmin_token, 200, {"principle_member_name": "Updated Name"}
            )
        
        # Superadmin Member CRUD
        member_created, _ = self.test_endpoint(
            "Superadmin - Create Member", "POST", "admin/members", 
            superadmin_token, 200, test_member
        )
        
        if member_created:
            self.test_endpoint(
                "Superadmin - Update Member", "PUT", f"admin/members/{test_member['serial_number']}", 
                superadmin_token, 200, {"first_name": "Updated Test"}
            )
        
        # Superadmin Price List CRUD
        pricelist_created, _ = self.test_endpoint(
            "Superadmin - Create Price List Item", "POST", "admin/pricelists", 
            superadmin_token, 200, test_pricelist
        )
        
        if pricelist_created:
            self.test_endpoint(
                "Superadmin - Update Price List Item", "PUT", 
                f"admin/pricelists/{test_pricelist['hospital_name']}/{test_pricelist['item_id']}", 
                superadmin_token, 200, {"cost": 149.99}
            )
        
        # Superadmin Bulk Operations
        bulk_family = {
            "family_id": f"BULK-FAM-{timestamp}",
            "principle_member_name": "Bulk Test Family",
            "total_allotment": 3000.0,
            "remaining_balance": 3000.0,
            "members": [{"first_name": "Bulk", "last_name": "Member1", "dob": "1985-01-01", "sex": "Male", "relationship": "Principle"}]
        }
        
        self.test_endpoint(
            "Superadmin - Bulk Create Family", "POST", "admin/families/bulk", 
            superadmin_token, 200, bulk_family
        )
        
        bulk_pricelist = {
            "hospital_name": "System Administration",
            "items": [{"item_id": f"BULK-ITEM-{timestamp}", "item_name": "Bulk Test Item", "item_type": "Service", "cost": 75.00}]
        }
        
        self.test_endpoint(
            "Superadmin - Bulk Create Price List", "POST", "admin/pricelists/bulk", 
            superadmin_token, 200, bulk_pricelist
        )
        
        print(f"\n🔴 HOSPITAL ADMIN TESTS (Should all FAIL with 403)")
        print("-" * 50)
        
        # Hospital Admin Family CRUD (should all fail)
        test_family2 = {
            "family_id": f"ADMIN-FAM-{timestamp}",
            "principle_member_name": "Admin Test Family",
            "total_allotment": 2000.0,
            "remaining_balance": 2000.0,
            "status": "Active"
        }
        
        self.test_endpoint(
            "Hospital Admin - Create Family (Should Fail)", "POST", "admin/families", 
            hospital_admin_token, 403, test_family2
        )
        
        if family_created:
            self.test_endpoint(
                "Hospital Admin - Update Family (Should Fail)", "PUT", f"admin/families/{test_family['family_id']}", 
                hospital_admin_token, 403, {"principle_member_name": "Admin Updated"}
            )
            
            self.test_endpoint(
                "Hospital Admin - Delete Family (Should Fail)", "DELETE", f"admin/families/{test_family['family_id']}", 
                hospital_admin_token, 403
            )
        
        # Hospital Admin Member CRUD (should all fail)
        test_member2 = {
            "serial_number": f"{test_family2['family_id']}-01",
            "family_id": test_family2['family_id'],
            "first_name": "Admin", "last_name": "Member", "dob": "1990-01-01", "sex": "Female", "relationship": "Principle", "status": "Active"
        }
        
        self.test_endpoint(
            "Hospital Admin - Create Member (Should Fail)", "POST", "admin/members", 
            hospital_admin_token, 403, test_member2
        )
        
        if member_created:
            self.test_endpoint(
                "Hospital Admin - Update Member (Should Fail)", "PUT", f"admin/members/{test_member['serial_number']}", 
                hospital_admin_token, 403, {"first_name": "Admin Updated"}
            )
            
            self.test_endpoint(
                "Hospital Admin - Delete Member (Should Fail)", "DELETE", f"admin/members/{test_member['serial_number']}", 
                hospital_admin_token, 403
            )
        
        # Hospital Admin Price List CRUD (should all fail)
        test_pricelist2 = {
            "hospital_name": "System Administration",
            "item_id": f"ADMIN-ITEM-{timestamp}",
            "item_name": "Admin Test Item", "item_type": "Service", "cost": 199.99
        }
        
        self.test_endpoint(
            "Hospital Admin - Create Price List Item (Should Fail)", "POST", "admin/pricelists", 
            hospital_admin_token, 403, test_pricelist2
        )
        
        if pricelist_created:
            self.test_endpoint(
                "Hospital Admin - Update Price List Item (Should Fail)", "PUT", 
                f"admin/pricelists/{test_pricelist['hospital_name']}/{test_pricelist['item_id']}", 
                hospital_admin_token, 403, {"cost": 299.99}
            )
            
            self.test_endpoint(
                "Hospital Admin - Delete Price List Item (Should Fail)", "DELETE", 
                f"admin/pricelists/{test_pricelist['hospital_name']}/{test_pricelist['item_id']}", 
                hospital_admin_token, 403
            )
        
        # Hospital Admin Bulk Operations (should fail)
        self.test_endpoint(
            "Hospital Admin - Bulk Create Family (Should Fail)", "POST", "admin/families/bulk", 
            hospital_admin_token, 403, bulk_family
        )
        
        self.test_endpoint(
            "Hospital Admin - Bulk Create Price List (Should Fail)", "POST", "admin/pricelists/bulk", 
            hospital_admin_token, 403, bulk_pricelist
        )
        
        print(f"\n🟡 HOSPITAL ADMIN READ ACCESS (Should SUCCEED)")
        print("-" * 50)
        
        # Hospital Admin should still be able to VIEW
        self.test_endpoint(
            "Hospital Admin - View Families (Should Succeed)", "GET", "admin/families", 
            hospital_admin_token, 200
        )
        
        self.test_endpoint(
            "Hospital Admin - View Members (Should Succeed)", "GET", "admin/members", 
            hospital_admin_token, 200
        )
        
        self.test_endpoint(
            "Hospital Admin - View Price Lists (Should Succeed)", "GET", "admin/pricelists/all", 
            hospital_admin_token, 200
        )
        
        # Hospital Admin should still be able to do other operations
        self.test_endpoint(
            "Hospital Admin - View Claims (Should Succeed)", "GET", "claims", 
            hospital_admin_token, 200
        )
        
        self.test_endpoint(
            "Hospital Admin - View Hospital Balance (Should Succeed)", "GET", "hospital/balance", 
            hospital_admin_token, 200
        )
        
        print(f"\n🧹 CLEANUP")
        print("-" * 50)
        
        # Cleanup - Delete test entities
        if member_created:
            self.test_endpoint(
                "Cleanup - Delete Test Member", "DELETE", f"admin/members/{test_member['serial_number']}", 
                superadmin_token, 200
            )
        
        if family_created:
            self.test_endpoint(
                "Cleanup - Delete Test Family", "DELETE", f"admin/families/{test_family['family_id']}", 
                superadmin_token, 200
            )
        
        if pricelist_created:
            self.test_endpoint(
                "Cleanup - Delete Test Price List Item", "DELETE", 
                f"admin/pricelists/{test_pricelist['hospital_name']}/{test_pricelist['item_id']}", 
                superadmin_token, 200
            )
        
        # Print summary
        print(f"\n📊 TEST SUMMARY")
        print("=" * 40)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = AccessControlTester()
    success = tester.run_access_control_tests()
    exit(0 if success else 1)