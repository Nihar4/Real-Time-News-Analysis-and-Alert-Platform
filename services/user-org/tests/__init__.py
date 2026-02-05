"""
FutureFeed User-Org Service - Test Package
==========================================

This test suite contains standalone tests that verify core functionality
without requiring the full FastAPI application dependencies.

Run tests:
    cd services/user-org
    python -m pytest tests/ -v

Test files:
    - test_standalone.py: Core utility tests (21 tests)
    - test_auth.py: Authentication tests (requires FastAPI)
    - test_api.py: API endpoint tests (requires FastAPI)
    - test_email.py: Email service tests (requires smtplib)
"""
