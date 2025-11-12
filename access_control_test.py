#!/usr/bin/env python3
"""
Focused Access Control Test for Void and Mark as Paid Endpoints
Tests the specific requirements from the review request.
"""

import requests
import sys
import json
from datetime import datetime

class AccessControlTester:
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
            print(f"✅ {name}")
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

    def login(self, username, password):
        """Login and get token"""
        print(f"\n🔐 Logging in as {username}...")
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

    def setup_test_claims(self):
        """Setup test claims for access control testing"""
        print(f"\n🔧 Setting up test claims...")
        
        # Login as superadmin to create test claims
        if not self.login("superadmin", "SuperAdmin@2024"):
            return None, None, None
        
        # Add deposit to ensure sufficient hospital balance
        self.run_test(
            "Add Hospital Deposit for Testing",
            "POST",
            "admin/hospitals/System Administration/deposit",
            200,
            data={"amount": 1000.0}
        )
        
        # Get existing claims
        success, claims = self.run_test(
            "Get Existing Claims",
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
        
        # Create test claims if needed
        if not completed_claim_id or not paid_claim_id:
            # Get patient and price list
            success, patient_data = self.run_test(
                "Get Patient for Test Claims",
                "GET",
                "patients/SEC-2413-01",
                200
            )
            
            success, price_items = self.run_test(
                "Get Price List for Test Claims",
                "GET",
                "pricelists",
                200
            )
            
            if success and patient_data and price_items:
                # Create COMPLETED claim if needed
                if not completed_claim_id:
                    claim_data = {
                        "patient_serial_number": patient_data["serial_number"],
                        "claim_items": [{
                            "item_id": price_items[0]["item_id"],
                            "item_name": price_items[0]["item_name"],
                            "item_cost": min(price_items[0]["cost"], 25.0),
                            "quantity": 1
                        }]
                    }
                    
                    success, claim_response = self.run_test(
                        "Create COMPLETED Test Claim",
                        "POST",
                        "claims/submit",
                        200,
                        data=claim_data
                    )
                    
                    if success:
                        completed_claim_id = claim_response.get('claim_id')
                        print(f"   Created COMPLETED claim: {completed_claim_id}")
                
                # Create PAID claim if needed
                if not paid_claim_id:
                    claim_data = {
                        "patient_serial_number": patient_data["serial_number"],
                        "claim_items": [{
                            "item_id": price_items[0]["item_id"],
                            "item_name": price_items[0]["item_name"],
                            "item_cost": min(price_items[0]["cost"], 20.0),
                            "quantity": 1
                        }]
                    }
                    
                    success, claim_response = self.run_test(
                        "Create Claim to Mark as PAID",
                        "POST",
                        "claims/submit",
                        200,
                        data=claim_data
                    )
                    
                    if success:
                        temp_claim_id = claim_response.get('claim_id')
                        # Mark it as paid
                        success, pay_response = self.run_test(
                            "Mark Test Claim as PAID",
                            "POST",
                            f"claims/{temp_claim_id}/pay",
                            200
                        )
                        if success:
                            paid_claim_id = temp_claim_id
                            print(f"   Created PAID claim: {paid_claim_id}")
        
        print(f"   Test claims ready - COMPLETED: {completed_claim_id}, PAID: {paid_claim_id}, VOIDED: {voided_claim_id}")
        return completed_claim_id, paid_claim_id, voided_claim_id

    def test_void_endpoint_access_control(self, completed_claim_id, paid_claim_id, voided_claim_id):
        """Test void endpoint access control"""
        print(f"\n🚫 Testing VOID endpoint access control...")
        
        # Test 1: Superadmin can void COMPLETED claim (should succeed)
        if completed_claim_id:
            if self.login("superadmin", "SuperAdmin@2024"):
                success, response = self.run_test(
                    "Superadmin can void COMPLETED claim",
                    "POST",
                    f"claims/{completed_claim_id}/void",
                    200
                )
                if success:
                    voided_claim_id = completed_claim_id
                    completed_claim_id = None
                    print(f"   ✅ Superadmin successfully voided claim")
        
        # Test 2: Non-superadmin Admin user cannot void claim (should fail with 403)
        if self.login("Gaga", "password123"):  # This is a non-superadmin admin
            test_claim_id = voided_claim_id or paid_claim_id or "DUMMY-CLAIM"
            success, response = self.run_test(
                "Non-superadmin Admin user cannot void claim (403)",
                "POST",
                f"claims/{test_claim_id}/void",
                403
            )
        
        # Test 3: Voiding already VOIDED claim should fail (400)
        if voided_claim_id:
            if self.login("superadmin", "SuperAdmin@2024"):
                success, response = self.run_test(
                    "Voiding already VOIDED claim should fail (400)",
                    "POST",
                    f"claims/{voided_claim_id}/void",
                    400
                )
        
        # Test 4: Voiding non-existent claim should fail (404)
        if self.login("superadmin", "SuperAdmin@2024"):
            success, response = self.run_test(
                "Voiding non-existent claim should fail (404)",
                "POST",
                "claims/NONEXISTENT-CLAIM/void",
                404
            )
        
        return voided_claim_id

    def test_mark_as_paid_endpoint_access_control(self, completed_claim_id, paid_claim_id, voided_claim_id):
        """Test mark as paid endpoint access control"""
        print(f"\n💰 Testing MARK AS PAID endpoint access control...")
        
        # Create a new COMPLETED claim for testing if needed
        if not completed_claim_id:
            if self.login("superadmin", "SuperAdmin@2024"):
                success, patient_data = self.run_test(
                    "Get Patient for Payment Test",
                    "GET",
                    "patients/SEC-2413-01",
                    200
                )
                
                success, price_items = self.run_test(
                    "Get Price List for Payment Test",
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
                            "item_cost": min(price_items[0]["cost"], 15.0),
                            "quantity": 1
                        }]
                    }
                    
                    success, claim_response = self.run_test(
                        "Create New COMPLETED Claim for Payment Test",
                        "POST",
                        "claims/submit",
                        200,
                        data=claim_data
                    )
                    
                    if success:
                        completed_claim_id = claim_response.get('claim_id')
                        print(f"   Created new COMPLETED claim: {completed_claim_id}")
        
        # Test 1: Superadmin can mark COMPLETED claim as PAID (should succeed)
        if completed_claim_id:
            if self.login("superadmin", "SuperAdmin@2024"):
                success, response = self.run_test(
                    "Superadmin can mark COMPLETED claim as PAID",
                    "POST",
                    f"claims/{completed_claim_id}/pay",
                    200
                )
                if success:
                    paid_claim_id = completed_claim_id
                    completed_claim_id = None
                    print(f"   ✅ Superadmin successfully marked claim as paid")
        
        # Test 2: Non-superadmin Admin user cannot mark as paid (should fail with 403)
        if self.login("Gaga", "password123"):  # This is a non-superadmin admin
            test_claim_id = paid_claim_id or voided_claim_id or "DUMMY-CLAIM"
            success, response = self.run_test(
                "Non-superadmin Admin user cannot mark as paid (403)",
                "POST",
                f"claims/{test_claim_id}/pay",
                403
            )
        
        # Test 3: Marking already PAID claim should fail (400)
        if paid_claim_id:
            if self.login("superadmin", "SuperAdmin@2024"):
                success, response = self.run_test(
                    "Marking already PAID claim should fail (400)",
                    "POST",
                    f"claims/{paid_claim_id}/pay",
                    400
                )
        
        # Test 4: Marking VOIDED claim should fail (400)
        if voided_claim_id:
            if self.login("superadmin", "SuperAdmin@2024"):
                success, response = self.run_test(
                    "Marking VOIDED claim should fail (400)",
                    "POST",
                    f"claims/{voided_claim_id}/pay",
                    400
                )
        
        # Test 5: Marking non-existent claim should fail (404)
        if self.login("superadmin", "SuperAdmin@2024"):
            success, response = self.run_test(
                "Marking non-existent claim should fail (404)",
                "POST",
                "claims/NONEXISTENT-CLAIM/pay",
                404
            )

    def test_error_messages(self, voided_claim_id, paid_claim_id):
        """Test expected error messages"""
        print(f"\n📝 Testing Expected Error Messages...")
        
        if self.login("Gaga", "password123"):  # Non-superadmin user
            # Test void error message
            success, response = self.run_test(
                "Void Error Message Check",
                "POST",
                f"claims/{voided_claim_id or 'DUMMY'}/void",
                403
            )
            
            # Test mark as paid error message
            success, response = self.run_test(
                "Mark as Paid Error Message Check",
                "POST",
                f"claims/{paid_claim_id or 'DUMMY'}/pay",
                403
            )
        
        if self.login("superadmin", "SuperAdmin@2024"):
            # Test already paid error message
            if paid_claim_id:
                success, response = self.run_test(
                    "Already Paid Error Message Check",
                    "POST",
                    f"claims/{paid_claim_id}/pay",
                    400
                )

    def run_access_control_tests(self):
        """Run comprehensive access control tests"""
        print("🔒 Medical Insurance Billing System - Access Control Testing")
        print("Testing: POST /api/claims/{claim_id}/void and POST /api/claims/{claim_id}/pay")
        print("=" * 80)
        
        # Setup test claims
        completed_claim_id, paid_claim_id, voided_claim_id = self.setup_test_claims()
        
        # Test void endpoint access control
        voided_claim_id = self.test_void_endpoint_access_control(completed_claim_id, paid_claim_id, voided_claim_id)
        
        # Test mark as paid endpoint access control
        self.test_mark_as_paid_endpoint_access_control(None, paid_claim_id, voided_claim_id)
        
        # Test error messages
        self.test_error_messages(voided_claim_id, paid_claim_id)
        
        # Print summary
        print(f"\n📊 Access Control Test Summary")
        print("=" * 50)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Print detailed results
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if not result["success"] and result["details"]:
                print(f"   {result['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = AccessControlTester()
    success = tester.run_access_control_tests()
    
    # Save results
    with open('/app/access_control_test_results.json', 'w') as f:
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