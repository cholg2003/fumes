import requests
import sys
import json
from datetime import datetime

class MedicalBillingAPITester:
    def __init__(self, base_url="https://care-billing.preview.emergentagent.com"):
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

    def run_comprehensive_test(self):
        """Run all tests"""
        print("🏥 Medical Insurance Billing System - API Testing")
        print("=" * 60)
        
        # Test different user credentials
        test_users = [
            ("general_clerk", "password123"),
            ("city_clerk", "password123"),
            ("mercy_admin", "password123")
        ]
        
        successful_login = False
        patient_data = None
        price_items = None
        bill_id = None
        
        # Try to login with each user
        for username, password in test_users:
            if self.test_login(username, password):
                successful_login = True
                break
        
        if not successful_login:
            print("\n❌ All login attempts failed. Cannot proceed with testing.")
            return False
        
        # Test patient search
        self.test_patient_search()
        
        # Get patient details
        success, patient_data = self.test_get_patient_details()
        
        # Get price list
        success, price_items = self.test_price_list()
        
        # Test balance validation (should fail)
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