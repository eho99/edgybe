#!/bin/bash
# Quick test commands for Referrals System

echo "==================================="
echo "Referrals System - Test Commands"
echo "==================================="

# Backend Tests
echo ""
echo "1. Running Backend Unit Tests..."
echo "-----------------------------------"
cd backend

echo "Installing dependencies..."
pip install -q resend weasyprint jinja2

echo ""
echo "Running all referral tests..."
pytest tests/test_referral_endpoints.py tests/test_referral_services.py -v --tb=short

echo ""
echo "==================================="
echo "Test Summary:"
echo "- Check output above for PASSED/FAILED"
echo "- All tests should pass"
echo "- Some warnings about WeasyPrint/Resend are OK"
echo "==================================="

echo ""
echo "Next steps:"
echo "1. Review test output above"
echo "2. If tests pass, proceed to frontend testing"
echo "3. Run: cd ../frontend && npm run dev"
echo "4. Navigate to: http://localhost:3000/dashboard/organizations/{YOUR_ORG_ID}/referrals"
echo ""

