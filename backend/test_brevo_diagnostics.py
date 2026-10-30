#!/usr/bin/env python3
"""
StudyVault — Brevo Transactional Email Diagnostic CLI Tool

Provides safe, developer-only diagnostics for verifying Brevo API configuration,
account connection, verified senders, direct test email delivery, and message event status.
Never exposes secret keys in console output.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Ensure backend directory is in python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Load environment configuration
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)
load_dotenv(os.path.join(backend_dir, '..', '.env'))
load_dotenv()

from config import Config
from services.db_service import DBService
from services.email_service import EmailService

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('BrevoDiagnostic')

def mask_secret(secret: str) -> str:
    """Safely masks a secret string, revealing only the first 4 and last 4 characters."""
    if not secret:
        return "<EMPTY/NOT_SET>"
    s = secret.strip()
    if len(s) <= 8:
        return f"{s[:2]}***{s[-2:]}"
    return f"{s[:6]}...{s[-4:]} (length: {len(s)})"

def run_diagnostics(args):
    print("=" * 70)
    print(" STUDYVAULT — BREVO TRANSACTIONAL EMAIL DIAGNOSTIC SUITE")
    print("=" * 70)

    # 1. Environment & Configuration Check
    print("\n[1] Environment & Configuration Inspection:")
    print(f"  - Config file path: {env_path} (exists: {os.path.exists(env_path)})")
    
    raw_key = os.environ.get('BREVO_API_KEY', '')
    raw_sender = os.environ.get('BREVO_SENDER_EMAIL', '')
    sender_name = os.environ.get('BREVO_SENDER_NAME', 'StudyVault')
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

    is_key_placeholder = 'replace' in raw_key.lower() or raw_key.strip() == 'your_new_brevo_api_key'
    is_sender_placeholder = 'your_' in raw_sender.lower() or raw_sender.strip() == 'your_verified_sender_email'

    print(f"  - BREVO_API_KEY: {mask_secret(raw_key)}")
    if is_key_placeholder:
        print("    [!] WARNING: BREVO_API_KEY still contains placeholder text ('replace_with_your_new_brevo_api_key').")
        print("    [!] ACTION REQUIRED: Paste your real Brevo API key (starts with 'xkeysib-') in backend/.env.")
    else:
        print("    [OK] API key format is non-placeholder.")

    print(f"  - BREVO_SENDER_EMAIL: {raw_sender if raw_sender else '<EMPTY>'}")
    if is_sender_placeholder:
        print("    [!] WARNING: BREVO_SENDER_EMAIL contains placeholder text ('your_verified_sender_email').")
        print("    [!] ACTION REQUIRED: Set BREVO_SENDER_EMAIL to your verified Brevo sender address.")
    else:
        print("    [OK] Sender email is specified.")

    print(f"  - BREVO_SENDER_NAME: {sender_name}")
    print(f"  - FRONTEND_URL: {frontend_url}")

    db_service = DBService()
    email_service = EmailService(
        api_key=raw_key,
        sender_email=raw_sender,
        sender_name=sender_name,
        frontend_url=frontend_url,
        db_service=db_service
    )

    is_configured = email_service.is_configured()
    print(f"  - Service is_configured() Check: {'PASS' if is_configured else 'FAIL (Unconfigured or placeholder)'}")

    # 2. Live Brevo API Connection Check
    print("\n[2] Live Brevo API Credential & Sender Verification:")
    if not is_configured:
        print("  - [SKIP] Cannot connect to Brevo API because credentials are unconfigured or placeholders.")
        print("  - To fix: Edit backend/.env and replace placeholder values with your real Brevo API key & sender email.")
    else:
        print("  - Connecting to Brevo API (GET /v3/account & GET /v3/senders)...")
        verification = email_service.verify_credentials()
        if verification.get('valid'):
            print("  - [SUCCESS] Brevo API Key Authenticated Successfully!")
            print(f"    - Account Email: {verification.get('account_email')}")
            print(f"    - Company / Account: {verification.get('company_name')}")
            print(f"    - Configured Sender: {verification.get('configured_sender')}")
            
            if verification.get('sender_verified'):
                print("    - Sender Verification Status: [VERIFIED & ACTIVE]")
            else:
                print("    - Sender Verification Status: [!] NOT VERIFIED in this Brevo account!")
                print(f"    - Available verified senders on this Brevo account: {verification.get('available_verified_senders')}")
                print(f"    - Action: In Brevo dashboard, add and verify '{raw_sender}' under Senders.")
        else:
            print("  - [FAIL] Brevo API Verification Failed:")
            print(f"    - Error: {verification.get('error')}")
            print(f"    - HTTP Status: {verification.get('http_status')}")
            if verification.get('http_status') == 401:
                print("    - Reason: Unauthorized. The Brevo API key is invalid, revoked, or mistyped.")
            elif verification.get('http_status') == 403:
                print("    - Reason: Forbidden. Your Brevo account may be pending activation or transactional emails are restricted.")

    # 3. Direct Test Email Send (if requested)
    if args.send_test:
        recipient = args.send_test.strip()
        print(f"\n[3] Sending Direct Test Transactional Email to: {recipient}...")
        test_res = email_service.send_test_email(recipient)
        if test_res.get('success'):
            print(f"  - [SUCCESS] Test email accepted by Brevo!")
            print(f"  - Brevo Message-ID: {test_res.get('message_id')}")
            print(f"  - Status: {test_res.get('status')} (HTTP {test_res.get('http_status', 201)})")
            print("  - Please check the inbox and spam/junk folder for the test message.")
        else:
            print(f"  - [FAIL] Test email delivery could not be completed.")
            print(f"  - Status: {test_res.get('status')}")
            print(f"  - Reason: {test_res.get('error')}")

    # 4. Resend Welcome Email to an Existing User (if requested)
    if args.resend_welcome:
        target_email = args.resend_welcome.strip().lower()
        print(f"\n[4] Resending Welcome Email to Registered User: {target_email}...")
        user = db_service.get_profile_by_email(target_email)
        if not user:
            print(f"  - [ERROR] No registered user found in StudyVault database for email: {target_email}")
        else:
            print(f"  - User found: '{user.get('full_name')}' (ID: {user.get('id')})")
            res = email_service.send_welcome_email(user)
            if res.get('success'):
                print(f"  - [SUCCESS] Welcome email successfully dispatched via Brevo!")
                print(f"  - Message-ID: {res.get('message_id')}")
                print(f"  - Status: {res.get('status')}")
            else:
                print(f"  - [FAIL] Welcome email dispatch failed: {res.get('error')}")

    # 5. Check Message Delivery Status (if requested)
    if args.check_message:
        msg_id = args.check_message.strip()
        print(f"\n[5] Checking Brevo Delivery Status for Message-ID: {msg_id}...")
        status_info = email_service.check_delivery_status(msg_id)
        print(f"  - Brevo Response: {status_info}")

    # 6. Recent Email Audit Logs from Database
    print("\n[6] Recent Email Audit Logs (from StudyVault database):")
    recent_logs = db_service.get_recent_email_logs(limit=5)
    if not recent_logs:
        print("  - No email logs recorded yet.")
    else:
        for idx, log in enumerate(recent_logs, 1):
            print(f"  {idx}. Type: {log.get('email_type')} | To: {log.get('recipient')} | Status: {log.get('status')} | Message-ID: {log.get('message_id') or '<None>'} | Created: {log.get('created_at')}")
            if log.get('error_message'):
                print(f"     Error Detail: {log.get('error_message')}")

    print("\n" + "=" * 70)
    print(" DIAGNOSTIC COMPLETE")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="StudyVault Brevo Email Diagnostic CLI")
    parser.add_argument('--send-test', type=str, help="Send a single diagnostic test email to the specified recipient address.")
    parser.add_argument('--resend-welcome', type=str, help="Resend the welcome email to an existing registered user.")
    parser.add_argument('--check-message', type=str, help="Query Brevo for delivery events of a specific Brevo Message-ID.")
    cli_args = parser.parse_args()

    run_diagnostics(cli_args)
