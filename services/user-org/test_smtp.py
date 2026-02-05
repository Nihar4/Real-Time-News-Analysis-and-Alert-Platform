#!/usr/bin/env python3
"""Test SMTP connection to verify credentials"""
import smtplib
import os

# Test configuration
smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
smtp_user = os.getenv("SMTP_USER", "futurefeedalerts@gmail.com")
smtp_password = os.getenv("SMTP_PASSWORD", "").replace(" ", "")

print(f"Testing SMTP connection...")
print(f"Host: {smtp_host}")
print(f"Port: {smtp_port}")
print(f"User: {smtp_user}")
print(f"Password length: {len(smtp_password)}")
print(f"Password (with spaces removed): '{smtp_password}'")
print(f"Raw password from env: '{os.getenv('SMTP_PASSWORD', '')}'")

try:
    print("\nConnecting to SMTP server...")
    server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
    server.set_debuglevel(1)  # Enable verbose output
    
    print("\nStarting TLS...")
    server.starttls()
    
    print("\nAttempting login...")
    server.login(smtp_user, smtp_password)
    
    print("\n✅ SUCCESS! SMTP authentication worked!")
    server.quit()
    
except Exception as e:
    print(f"\n❌ FAILED: {str(e)}")
    print("\nPossible issues:")
    print("1. App Password may be incorrect or revoked")
    print("2. 2-Step Verification may not be enabled")
    print("3. 'Less secure app access' may be blocking (deprecated)")
    print("\nTo fix:")
    print("1. Go to https://myaccount.google.com/security")
    print("2. Enable 2-Step Verification")
    print("3. Generate a new App Password at https://myaccount.google.com/apppasswords")
    print("4. Update SMTP_PASSWORD in .env file")
