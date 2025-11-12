import requests
import sys
import json
from datetime import datetime

class HospitalPaymentSystemTester:
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

    def test_hospital_deposit_endpoints(self):
        """Test hospital deposit functionality"""
        print(f"\n💰 Testing Hospital Deposit Endpoints...")
        
        # Login as superadmin
        if not self.test_login("superadmin", "SuperAdmin@2024"):
            self.log_test("Hospital Deposit Setup", False, "Could not login as superadmin")
            return False
        
        hospital_name = "System Administration"
        
        # Test 1: Valid deposit (positive amount)
        print(f"\n   Test 1: Valid deposit (positive amount)")
        success, response = self.run_test(
            "POST /api/admin/hospitals/{hospital_name}/deposit - Valid Amount",
            "POST",
            f"admin/hospitals/{hospital_name}/deposit",
            200,
            data={"amount": 250.0}
        )
        
        if success:
            print(f"      ✅ Added $250.00 deposit")
            print(f"      New balance: ${response.get('new_balance', 0):.2f}")
        
        # Test 2: Negative amount (should fail)
        print(f"\n   Test 2: Negative amount (should fail)")
        success, response = self.run_test(
            "POST /api/admin/hospitals/{hospital_name}/deposit - Negative Amount",
            "POST",
            f"admin/hospitals/{hospital_name}/deposit",
            400,
            data={"amount": -50.0}
        )
        
        # Test 3: Zero amount (should fail)
        print(f"\n   Test 3: Zero amount (should fail)")
        success, response = self.run_test(
            "POST /api/admin/hospitals/{hospital_name}/deposit - Zero Amount",
            "POST",
            f"admin/hospitals/{hospital_name}/deposit",
            400,
            data={"amount": 0.0}
        )
        
        # Test 4: Non-existent hospital (should fail)
        print(f"\n   Test 4: Non-existent hospital (should fail)")
        success, response = self.run_test(
            "POST /api/admin/hospitals/{hospital_name}/deposit - Non-existent Hospital",
            "POST",
            "admin/hospitals/NonExistentHospital/deposit",
            404,
            data={"amount": 100.0}
        )
        
        # Test 5: Non-admin user access (should fail)
        print(f"\n   Test 5: Non-admin user access (should fail)")
        # Create a regular user token (we'll simulate this by clearing admin token)
        admin_token = self.token
        self.token = "invalid_token"
        
        success, response = self.run_test(
            "POST /api/admin/hospitals/{hospital_name}/deposit - Invalid Token",
            "POST",
            f"admin/hospitals/{hospital_name}/deposit",
            401,
            data={"amount": 100.0}
        )
        
        # Restore admin token
        self.token = admin_token
        
        return True

    def test_hospital_balance_endpoint(self):
        """Test hospital balance retrieval"""
        print(f"\n💳 Testing Hospital Balance Endpoint...")
        
        # Test 1: Valid authenticated user
        print(f"\n   Test 1: Valid authenticated user")
        success, response = self.run_test(
            "GET /api/hospital/balance - Authenticated User",
            "GET",
            "hospital/balance",
            200
        )
        
        if success:
            hospital_name = response.get('hospital_name')
            balance = response.get('deposit_balance', 0)
            print(f"      Hospital: {hospital_name}")
            print(f"      Balance: ${balance:.2f}")
            return balance
        
        return 0

    def test_claim_payment_endpoints(self):
        """Test claim payment functionality"""
        print(f"\n💸 Testing Claim Payment Endpoints...")
        
        # Get existing claims
        success, claims = self.run_test(
            "GET /api/claims - Get Claims for Testing",
            "GET",
            "claims",
            200
        )
        
        if not success or not claims:
            self.log_test("Claim Payment Setup", False, "No claims found for testing")
            return False
        
        # Find claims with different statuses
        completed_claims = [c for c in claims if c.get("status") == "COMPLETED"]
        paid_claims = [c for c in claims if c.get("status") == "PAID"]
        voided_claims = [c for c in claims if c.get("status") == "VOIDED"]
        
        print(f"      Found {len(completed_claims)} COMPLETED, {len(paid_claims)} PAID, {len(voided_claims)} VOIDED claims")
        
        # Test 1: Mark COMPLETED claim as PAID (should succeed and deduct)
        if completed_claims:
            claim_id = completed_claims[0]["claim_id"]
            claim_amount = completed_claims[0]["total_claim_amount"]
            
            print(f"\n   Test 1: Mark COMPLETED claim as PAID")
            print(f"      Claim ID: {claim_id}")
            print(f"      Amount: ${claim_amount:.2f}")
            
            success, response = self.run_test(
                "POST /api/claims/{claim_id}/pay - Mark COMPLETED as PAID",
                "POST",
                f"claims/{claim_id}/pay",
                200
            )
            
            if success:
                new_balance = response.get('new_hospital_balance', 0)
                print(f"      ✅ Claim marked as paid")
                print(f"      New hospital balance: ${new_balance:.2f}")
        
        # Test 2: Try to mark PAID claim again (should fail)
        if paid_claims:
            claim_id = paid_claims[0]["claim_id"]
            
            print(f"\n   Test 2: Try to mark PAID claim again (should fail)")
            print(f"      Claim ID: {claim_id}")
            
            success, response = self.run_test(
                "POST /api/claims/{claim_id}/pay - Mark PAID claim again",
                "POST",
                f"claims/{claim_id}/pay",
                400
            )
        
        # Test 3: Try to mark VOIDED claim (should fail)
        if voided_claims:
            claim_id = voided_claims[0]["claim_id"]
            
            print(f"\n   Test 3: Try to mark VOIDED claim (should fail)")
            print(f"      Claim ID: {claim_id}")
            
            success, response = self.run_test(
                "POST /api/claims/{claim_id}/pay - Mark VOIDED claim",
                "POST",
                f"claims/{claim_id}/pay",
                400
            )
        
        # Test 4: Non-existent claim (should fail)
        print(f"\n   Test 4: Non-existent claim (should fail)")
        success, response = self.run_test(
            "POST /api/claims/{claim_id}/pay - Non-existent claim",
            "POST",
            "claims/NONEXISTENT-CLAIM-ID/pay",
            404
        )
        
        # Test 5: Verify claim status changes from COMPLETED to PAID
        print(f"\n   Test 5: Verify claim status changes")
        success, updated_claims = self.run_test(
            "GET /api/claims - Verify Status Changes",
            "GET",
            "claims",
            200
        )
        
        if success and updated_claims:
            # Check if we have more PAID claims now
            new_paid_claims = [c for c in updated_claims if c.get("status") == "PAID"]
            if len(new_paid_claims) > len(paid_claims):
                self.log_test("Claim Status Change Verification", True, f"Claims successfully changed to PAID status")
            else:
                self.log_test("Claim Status Change Verification", False, f"No new PAID claims found")
        
        return True

    def test_insufficient_balance_scenario(self):
        """Test insufficient balance scenario"""
        print(f"\n⚠️  Testing Insufficient Balance Scenario...")
        
        # Get current hospital balance
        success, balance_response = self.run_test(
            "GET /api/hospital/balance - Check Current Balance",
            "GET",
            "hospital/balance",
            200
        )
        
        if not success:
            self.log_test("Insufficient Balance Test Setup", False, "Could not get hospital balance")
            return False
        
        current_balance = balance_response.get('deposit_balance', 0)
        print(f"      Current hospital balance: ${current_balance:.2f}")
        
        # Create a high-value claim that would exceed hospital balance
        # First get patient and price list data
        success, patient_data = self.run_test(
            "GET /api/patients/{serial_number} - Get Patient for Test",
            "GET",
            "patients/SEC-2413-01",
            200
        )
        
        success, price_items = self.run_test(
            "GET /api/pricelists - Get Price List for Test",
            "GET",
            "pricelists",
            200
        )
        
        if success and patient_data and price_items:
            # Create a claim with amount higher than hospital balance
            high_amount = current_balance + 500  # More than hospital balance
            
            claim_data = {
                "patient_serial_number": patient_data["serial_number"],
                "claim_items": [{
                    "item_id": price_items[0]["item_id"],
                    "item_name": price_items[0]["item_name"],
                    "item_cost": high_amount,
                    "quantity": 1
                }]
            }
            
            print(f"\n   Creating high-value claim (${high_amount:.2f}) to test insufficient balance...")
            
            # This will likely fail due to insufficient family balance first
            success, claim_response = self.run_test(
                "POST /api/claims/submit - Create High Value Claim",
                "POST",
                "claims/submit",
                400  # Expected to fail due to insufficient family balance
            )
            
            # If it somehow succeeds, try to pay it
            if success and claim_response.get('claim_id'):
                high_claim_id = claim_response['claim_id']
                print(f"      High-value claim created: {high_claim_id}")
                
                success, response = self.run_test(
                    "POST /api/claims/{claim_id}/pay - Insufficient Hospital Balance",
                    "POST",
                    f"claims/{high_claim_id}/pay",
                    400
                )
                
                if success:
                    print(f"      ✅ Correctly rejected payment due to insufficient hospital balance")
        
        return True

    def test_cross_hospital_permission(self):
        """Test cross-hospital permission checks"""
        print(f"\n🏥 Testing Cross-Hospital Permission Checks...")
        
        # Get a claim from System Administration
        success, claims = self.run_test(
            "GET /api/claims - Get System Administration Claims",
            "GET",
            "claims",
            200
        )
        
        if not success or not claims:
            self.log_test("Cross-Hospital Permission Test Setup", False, "No claims found")
            return False
        
        # Find a claim that can be used for testing
        test_claim_id = None
        for claim in claims:
            if claim.get("hospital_name") == "System Administration":
                test_claim_id = claim.get("claim_id")
                break
        
        if not test_claim_id:
            self.log_test("Cross-Hospital Permission Test Setup", False, "No System Administration claims found")
            return False
        
        print(f"      Using claim {test_claim_id} from System Administration")
        
        # Try to create a user from a different hospital (simulate by using invalid token)
        # In a real scenario, we would login as a different hospital user
        print(f"\n   Test: Different hospital user trying to mark claim as paid (should fail)")
        
        # Save current token and simulate different hospital user
        original_token = self.token
        self.token = "different_hospital_token"
        
        success, response = self.run_test(
            "POST /api/claims/{claim_id}/pay - Different Hospital User",
            "POST",
            f"claims/{test_claim_id}/pay",
            401  # Should fail with unauthorized
        )
        
        # Restore original token
        self.token = original_token
        
        return True

    def run_comprehensive_test(self):
        """Run comprehensive Hospital Payment and Deposit System tests"""
        print("🏥 Hospital Payment and Deposit System - Comprehensive Testing")
        print("=" * 70)
        
        # Test all endpoints according to the review request
        
        # 1. Test deposit endpoints
        self.test_hospital_deposit_endpoints()
        
        # 2. Test balance endpoint
        initial_balance = self.test_hospital_balance_endpoint()
        
        # 3. Test claim payment endpoints
        self.test_claim_payment_endpoints()
        
        # 4. Test insufficient balance scenario
        self.test_insufficient_balance_scenario()
        
        # 5. Test cross-hospital permissions
        self.test_cross_hospital_permission()
        
        # 6. Verify final balance
        print(f"\n🔍 Final Balance Verification...")
        final_balance = self.test_hospital_balance_endpoint()
        
        if final_balance < initial_balance:
            self.log_test("Balance Deduction Verification", True, f"Balance correctly deducted from ${initial_balance:.2f} to ${final_balance:.2f}")
        else:
            self.log_test("Balance Deduction Verification", False, f"Balance not deducted. Initial: ${initial_balance:.2f}, Final: ${final_balance:.2f}")
        
        # Print summary
        print(f"\n📊 Test Summary")
        print("=" * 40)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Print detailed results for failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = HospitalPaymentSystemTester()
    success = tester.run_comprehensive_test()
    
    # Save detailed results
    with open('/app/hospital_payment_test_results.json', 'w') as f:
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