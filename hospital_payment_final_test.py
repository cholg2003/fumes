import requests
import sys
import json
from datetime import datetime

class HospitalPaymentFinalTester:
    def __init__(self, base_url="https://global-currency-6.preview.emergentagent.com"):
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

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

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
        success, response = self.run_test(
            f"Login as {username}",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.hospital_name = response.get('hospital_name')
            self.username = response.get('username')
            return True
        return False

    def run_comprehensive_test(self):
        """Run comprehensive Hospital Payment and Deposit System tests"""
        print("🏥 Hospital Payment and Deposit System - Final Testing")
        print("=" * 60)
        
        # Login as superadmin
        if not self.test_login("superadmin", "SuperAdmin@2024"):
            print("❌ Cannot proceed without superadmin login")
            return False
        
        print(f"\n💰 TESTING DEPOSIT ENDPOINTS")
        print("-" * 40)
        
        hospital_name = "System Administration"
        
        # Test 1: Valid deposit (positive amount)
        success, response = self.run_test(
            "Add valid deposit ($300)",
            "POST",
            f"admin/hospitals/{hospital_name}/deposit",
            200,
            data={"amount": 300.0}
        )
        
        # Test 2: Negative amount (should fail)
        success, response = self.run_test(
            "Reject negative deposit (-$50)",
            "POST",
            f"admin/hospitals/{hospital_name}/deposit",
            400,
            data={"amount": -50.0}
        )
        
        # Test 3: Zero amount (should fail)
        success, response = self.run_test(
            "Reject zero deposit ($0)",
            "POST",
            f"admin/hospitals/{hospital_name}/deposit",
            400,
            data={"amount": 0.0}
        )
        
        # Test 4: Non-existent hospital (should fail)
        success, response = self.run_test(
            "Reject deposit to non-existent hospital",
            "POST",
            "admin/hospitals/NonExistentHospital/deposit",
            404,
            data={"amount": 100.0}
        )
        
        print(f"\n💳 TESTING BALANCE ENDPOINT")
        print("-" * 40)
        
        # Test 5: Get hospital balance
        success, response = self.run_test(
            "Get hospital balance",
            "GET",
            "hospital/balance",
            200
        )
        
        initial_balance = 0
        if success:
            initial_balance = response.get('deposit_balance', 0)
            print(f"   Current balance: ${initial_balance:.2f}")
        
        print(f"\n💸 TESTING CLAIM PAYMENT ENDPOINTS")
        print("-" * 40)
        
        # Create a new COMPLETED claim for testing
        success, patient_data = self.run_test(
            "Get patient data for new claim",
            "GET",
            "patients/SEC-2413-01",
            200
        )
        
        success, price_items = self.run_test(
            "Get price list for new claim",
            "GET",
            "pricelists",
            200
        )
        
        new_claim_id = None
        if success and patient_data and price_items:
            # Create a new claim
            claim_data = {
                "patient_serial_number": "SEC-2413-01",
                "claim_items": [{
                    "item_id": "TEST-001",
                    "item_name": "Test Service",
                    "item_cost": 100.0,
                    "quantity": 1
                }]
            }
            
            success, claim_response = self.run_test(
                "Create new COMPLETED claim for testing",
                "POST",
                "claims/submit",
                200,
                data=claim_data
            )
            
            if success:
                new_claim_id = claim_response.get('claim_id')
                print(f"   Created claim: {new_claim_id}")
        
        # Test 6: Mark COMPLETED claim as PAID (should succeed and deduct)
        if new_claim_id:
            success, response = self.run_test(
                f"Mark COMPLETED claim as PAID ({new_claim_id})",
                "POST",
                f"claims/{new_claim_id}/pay",
                200
            )
            
            if success:
                new_balance = response.get('new_hospital_balance', 0)
                print(f"   New balance after payment: ${new_balance:.2f}")
        
        # Test 7: Try to mark already PAID claim again (should fail)
        success, claims = self.run_test(
            "Get existing claims",
            "GET",
            "claims",
            200
        )
        
        paid_claim_id = None
        if success and claims:
            for claim in claims:
                if claim.get("status") == "PAID":
                    paid_claim_id = claim.get("claim_id")
                    break
        
        if paid_claim_id:
            success, response = self.run_test(
                f"Reject payment of already PAID claim ({paid_claim_id})",
                "POST",
                f"claims/{paid_claim_id}/pay",
                400
            )
        
        # Test 8: Try to mark non-existent claim (should fail)
        success, response = self.run_test(
            "Reject payment of non-existent claim",
            "POST",
            "claims/NONEXISTENT-CLAIM/pay",
            404
        )
        
        # Test 9: Test insufficient balance scenario
        print(f"\n⚠️  TESTING INSUFFICIENT BALANCE SCENARIO")
        print("-" * 40)
        
        # Get current balance
        success, balance_response = self.run_test(
            "Check current balance for insufficient funds test",
            "GET",
            "hospital/balance",
            200
        )
        
        if success:
            current_balance = balance_response.get('deposit_balance', 0)
            print(f"   Current balance: ${current_balance:.2f}")
            
            # Create a claim with amount higher than hospital balance
            high_amount = current_balance + 500
            
            claim_data = {
                "patient_serial_number": "SEC-2413-01",
                "claim_items": [{
                    "item_id": "TEST-001",
                    "item_name": "Test Service",
                    "item_cost": high_amount,
                    "quantity": 1
                }]
            }
            
            # This should fail due to insufficient family balance
            success, claim_response = self.run_test(
                f"Reject high-value claim (${high_amount:.2f}) - insufficient family balance",
                "POST",
                "claims/submit",
                400
            )
        
        # Test 10: Verify final balance
        print(f"\n🔍 FINAL VERIFICATION")
        print("-" * 40)
        
        success, final_balance_response = self.run_test(
            "Verify final hospital balance",
            "GET",
            "hospital/balance",
            200
        )
        
        if success:
            final_balance = final_balance_response.get('deposit_balance', 0)
            print(f"   Final balance: ${final_balance:.2f}")
            
            if final_balance < initial_balance:
                self.log_test("Balance correctly deducted after payment", True, f"${initial_balance:.2f} → ${final_balance:.2f}")
            else:
                self.log_test("Balance deduction verification", False, f"Balance not deducted: ${initial_balance:.2f} → ${final_balance:.2f}")
        
        # Print summary
        print(f"\n📊 TEST SUMMARY")
        print("=" * 40)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Print failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        else:
            print(f"\n🎉 ALL TESTS PASSED!")
        
        return len(failed_tests) == 0

def main():
    tester = HospitalPaymentFinalTester()
    success = tester.run_comprehensive_test()
    
    # Save results
    with open('/app/hospital_payment_final_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
            "all_passed": tester.tests_passed == tester.tests_run,
            "results": tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())