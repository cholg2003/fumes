#!/usr/bin/env python3
"""
SSP Currency Claim Submission Test
Test claim submission for Test Hospital using SSP currency
"""

import sys
import os
sys.path.append('/app')

from backend_test import MedicalBillingAPITester

def main():
    """Run SSP currency claim submission test"""
    print("🚀 Starting SSP Currency Claim Submission Test...")
    
    tester = MedicalBillingAPITester()
    success = tester.run_ssp_currency_test()
    
    if success:
        print("\n✅ SSP Currency test completed successfully!")
    else:
        print("\n❌ SSP Currency test failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())