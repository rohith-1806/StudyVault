import os
import re
import time
import json
import logging
import threading
import requests
from typing import Optional, Dict, Any, List

try:
    import sib_api_v3_sdk
    from sib_api_v3_sdk.rest import ApiException
except ImportError:
    sib_api_v3_sdk = None
    ApiException = Exception

logger = logging.getLogger('studyvault.email')
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [Brevo] %(message)s')

BREVO_API_BASE_URL = "https://api.brevo.com/v3"
BREVO_USER_AGENT = "StudyVault-Brevo-Client/1.0"
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


class EmailService:
    def __init__(self, api_key: Optional[str] = None, sender_email: Optional[str] = None, 
                 sender_name: Optional[str] = None, frontend_url: Optional[str] = None,
                 db_service = None):
        self.api_key = api_key or os.environ.get('BREVO_API_KEY', '')
        self.sender_email = sender_email or os.environ.get('BREVO_SENDER_EMAIL', '')
        self.sender_name = sender_name or os.environ.get('BREVO_SENDER_NAME', 'StudyVault')
        self.frontend_url = (frontend_url or os.environ.get('FRONTEND_URL', 'http://localhost:5173')).rstrip('/')
        self.db_service = db_service
        self._mock_send_handler = None  # Hook for test injection

    def set_mock_send_handler(self, handler):
        """Allows injecting a mock email sender for tests without hitting Brevo network."""
        self._mock_send_handler = handler

    def is_configured(self) -> bool:
        """Checks if Brevo credentials are configured with valid non-placeholder values."""
        if not self.api_key or not self.sender_email:
            return False
        placeholders = [
            'replace_with_your_new_brevo_api_key',
            'your_verified_sender_email',
            'your-api-key',
            'test-key'
        ]
        if self.api_key.strip() in placeholders or 'replace' in self.api_key.lower():
            return False
        if self.sender_email.strip() in placeholders or 'your_' in self.sender_email.lower():
            return False
        return True

    def validate_recipient_email(self, email: str) -> bool:
        """Validates recipient email address syntax."""
        if not email or not isinstance(email, str):
            return False
        return bool(re.match(EMAIL_REGEX, email.strip()))

    def _get_api_client(self):
        """Constructs an authenticated Brevo API client."""
        if not sib_api_v3_sdk:
            raise RuntimeError("sib-api-v3-sdk package is not installed.")
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = self.api_key.strip()
        api_client = sib_api_v3_sdk.ApiClient(configuration)
        return sib_api_v3_sdk.TransactionalEmailsApi(api_client)

    def _send_brevo_transactional_email(
        self, 
        recipient_email: str, 
        recipient_name: str, 
        subject: str, 
        html_content: str, 
        text_content: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Sends an email using Brevo's Transactional Email REST API with controlled retries and exponential backoff.
        Ensures Cloudflare compatibility with custom User-Agent.
        Never logs secrets. Returns structured delivery status.
        """
        cleaned_email = recipient_email.strip().lower()
        if not self.validate_recipient_email(cleaned_email):
            logger.warning("[Brevo] Rejected: Invalid recipient email address format: '%s'", cleaned_email)
            return {"success": False, "status": "invalid_recipient", "error": "Invalid recipient email address format."}

        # Check mock handler (used for test suites)
        if self._mock_send_handler:
            return self._mock_send_handler({
                "recipient_email": cleaned_email,
                "recipient_name": recipient_name,
                "subject": subject,
                "html_content": html_content,
                "text_content": text_content,
                "sender_email": self.sender_email,
                "sender_name": self.sender_name
            })

        if not self.is_configured():
            logger.warning(
                "[Brevo] Email dispatch skipped: BREVO_API_KEY or BREVO_SENDER_EMAIL "
                "is not configured or set to placeholder in backend/.env."
            )
            return {
                "success": False, 
                "status": "unconfigured", 
                "error": "Brevo API key or verified sender email is not configured in backend/.env."
            }

        headers = {
            "api-key": self.api_key.strip(),
            "accept": "application/json",
            "content-type": "application/json",
            "User-Agent": BREVO_USER_AGENT
        }

        payload = {
            "sender": {
                "name": self.sender_name.strip(),
                "email": self.sender_email.strip()
            },
            "to": [
                {
                    "email": cleaned_email,
                    "name": recipient_name or cleaned_email.split('@')[0]
                }
            ],
            "subject": subject,
            "htmlContent": html_content,
            "textContent": text_content
        }

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    "[Brevo] Attempting transactional dispatch (attempt %d/%d) for subject '%s' to recipient domain @%s", 
                    attempt, max_retries, subject, cleaned_email.split('@')[-1]
                )

                response = requests.post(
                    f"{BREVO_API_BASE_URL}/smtp/email",
                    headers=headers,
                    json=payload,
                    timeout=15
                )

                if response.status_code == 201:
                    data = response.json()
                    message_id = data.get('messageId')
                    logger.info("[Brevo] Accepted by Brevo API (HTTP 201 Created). Message-ID: %s", message_id)
                    return {
                        "success": True,
                        "status": "accepted",
                        "message_id": str(message_id) if message_id else "accepted",
                        "http_status": 201
                    }

                # Parse rejection details from Brevo
                err_data = {}
                try:
                    err_data = response.json()
                except Exception:
                    err_data = {"message": response.text}

                error_msg = err_data.get('message', f"HTTP {response.status_code}")
                error_code = err_data.get('code', f"status_{response.status_code}")
                last_error = f"Brevo HTTP {response.status_code} ({error_code}): {error_msg}"
                logger.error("[Brevo] API rejected dispatch: HTTP %d (%s) - %s", response.status_code, error_code, error_msg)

                # Retry on rate limit (429) or transient 5xx server errors
                if response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    backoff = 2 ** attempt
                    time.sleep(backoff)
                    continue
                break

            except requests.exceptions.RequestException as e:
                last_error = f"Network communication failure connecting to Brevo: {str(e)}"
                logger.error("[Brevo] Network connection error: %s", str(e))
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                break
            except Exception as e:
                last_error = f"Unexpected execution error: {str(e)}"
                logger.error("[Brevo] Unexpected error during dispatch: %s", str(e))
                break

        return {
            "success": False,
            "status": "failed",
            "error": last_error or "Unknown delivery error"
        }

    # --- DIAGNOSTIC & VERIFICATION METHODS ---

    def verify_credentials(self) -> Dict[str, Any]:
        """
        Validates Brevo API Key against Brevo /account and /senders endpoints.
        Returns detailed diagnostics without exposing secret keys.
        """
        if not self.is_configured():
            return {
                "valid": False,
                "error": "Credentials missing or placeholder text detected in backend/.env.",
                "details": {
                    "api_key_set": bool(self.api_key),
                    "api_key_is_placeholder": "replace" in self.api_key.lower(),
                    "sender_email_set": bool(self.sender_email),
                    "sender_is_placeholder": "your_" in self.sender_email.lower()
                }
            }

        headers = {
            "api-key": self.api_key.strip(),
            "accept": "application/json",
            "User-Agent": BREVO_USER_AGENT
        }

        try:
            acc_res = requests.get(f"{BREVO_API_BASE_URL}/account", headers=headers, timeout=10)
            if acc_res.status_code != 200:
                err_data = acc_res.json() if 'application/json' in acc_res.headers.get('content-type', '') else {}
                return {
                    "valid": False,
                    "http_status": acc_res.status_code,
                    "error": err_data.get('message', f"HTTP {acc_res.status_code}"),
                    "code": err_data.get('code', 'account_check_failed')
                }

            acc_data = acc_res.json()

            senders_res = requests.get(f"{BREVO_API_BASE_URL}/senders", headers=headers, timeout=10)
            verified_senders = []
            sender_is_verified = False
            if senders_res.status_code == 200:
                senders_data = senders_res.json().get('senders', [])
                verified_senders = [s.get('email', '').lower() for s in senders_data if s.get('active', True)]
                sender_is_verified = self.sender_email.strip().lower() in verified_senders

            return {
                "valid": True,
                "account_email": acc_data.get('email'),
                "company_name": acc_data.get('companyName'),
                "configured_sender": self.sender_email,
                "sender_verified": sender_is_verified,
                "available_verified_senders": verified_senders
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to connect to Brevo API: {str(e)}"
            }

    def check_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """
        Inspects the delivery status and events for a specific message ID from Brevo.
        """
        if not self.is_configured() or not message_id or message_id in ('mock', 'cached'):
            return {"status": "unknown", "error": "Not an active Brevo message ID."}

        headers = {
            "api-key": self.api_key.strip(),
            "accept": "application/json",
            "User-Agent": BREVO_USER_AGENT
        }
        try:
            res = requests.get(f"{BREVO_API_BASE_URL}/smtp/emails/{message_id}", headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"http_status": res.status_code, "error": res.text}
        except Exception as e:
            return {"error": str(e)}

    def send_test_email(self, recipient_email: str) -> Dict[str, Any]:
        """
        Diagnostic method: Sends a safe diagnostic test email to confirm Brevo deliverability.
        """
        cleaned = recipient_email.strip().lower()
        subject = "StudyVault — Brevo Transactional Email Diagnostic Test"
        preheader = "Brevo diagnostic test email confirming API key and sender deliverability."
        body_html = f"""
        <h1 style="color: #ffffff; font-size: 20px; font-weight: 800; margin: 0 0 16px 0;">
          &#9989; Brevo Diagnostic Test Succeeded!
        </h1>
        <p style="margin: 0 0 14px 0;">
          This email confirms that your <strong>Brevo API key</strong> and <strong>verified sender email</strong> (<code>{self.sender_email}</code>) are functioning properly in StudyVault.
        </p>
        <div style="background-color: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 14px 18px; margin: 16px 0; font-family: monospace; font-size: 13px;">
          <div>Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}</div>
          <div>Recipient: {cleaned}</div>
          <div>Sender: {self.sender_name} &lt;{self.sender_email}&gt;</div>
        </div>
        """
        text_content = f"Brevo Diagnostic Test Succeeded!\n\nThis email confirms that your Brevo API key and verified sender email ({self.sender_email}) are working properly in StudyVault.\n\nTimestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
        html_content = self._render_base_template(
            title=subject,
            preheader=preheader,
            body_html=body_html,
            cta_url=self.frontend_url,
            cta_text="Visit StudyVault"
        )
        return self._send_brevo_transactional_email(
            recipient_email=cleaned,
            recipient_name="StudyVault Developer",
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

    # --- HTML / TEXT TEMPLATE GENERATORS ---

    def _render_base_template(self, title: str, preheader: str, body_html: str, cta_url: str, cta_text: str) -> str:
        """
        Generates a premium, responsive glassmorphism/slate themed email HTML template.
        """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <!--[if mso]>
  <style type="text/css">
    body, table, td {{font-family: Arial, Helvetica, sans-serif !important;}}
  </style>
  <![endif]-->
  <style>
    body {{
      margin: 0;
      padding: 0;
      background-color: #0b0f19;
      color: #e2e8f0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      -webkit-font-smoothing: antialiased;
    }}
    table {{ border-collapse: separate; }}
    a {{ color: #818cf8; text-decoration: none; }}
    .btn:hover {{ background-color: #4f46e5 !important; }}
    @media only screen and (max-width: 620px) {{
      .wrapper {{ width: 100% !important; padding: 12px !important; }}
      .content-box {{ padding: 24px 18px !important; }}
      .btn {{ display: block !important; width: 100% !important; text-align: center !important; }}
    }}
  </style>
</head>
<body style="background-color: #0b0f19; margin: 0; padding: 24px 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <span style="display:none;font-size:1px;color:#0b0f19;line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;">
    {preheader}
  </span>
  <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">
    <tr>
      <td align="center">
        <table role="presentation" class="wrapper" width="600" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; width: 100%;">
          
          <!-- BRAND HEADER -->
          <tr>
            <td align="center" style="padding: 20px 0 24px 0;">
              <table role="presentation" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td align="center">
                    <div style="background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); width: 44px; height: 44px; border-radius: 12px; line-height: 44px; text-align: center; color: #ffffff; font-size: 22px; font-weight: 900; margin: 0 auto 12px auto; box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.4);">
                      SV
                    </div>
                    <div style="font-size: 22px; font-weight: 800; letter-spacing: -0.5px; color: #ffffff;">
                      Study<span style="color: #818cf8;">Vault</span>
                    </div>
                    <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #94a3b8; margin-top: 2px;">
                      Student Digital Library
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- MAIN CARD -->
          <tr>
            <td>
              <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" class="content-box" style="background-color: #131b2e; border: 1px solid #1e293b; border-radius: 20px; padding: 36px 32px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);">
                <tr>
                  <td style="color: #cbd5e1; font-size: 15px; line-height: 1.6;">
                    {body_html}

                    <!-- CALL TO ACTION -->
                    {f'''
                    <div style="margin: 32px 0 24px 0; text-align: center;">
                      <a href="{cta_url}" class="btn" style="background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: #ffffff; padding: 14px 32px; font-size: 14px; font-weight: 700; border-radius: 12px; display: inline-block; text-align: center; box-shadow: 0 10px 20px -3px rgba(99, 102, 241, 0.4); text-decoration: none;">
                        {cta_text} &rarr;
                      </a>
                    </div>
                    ''' if cta_url and cta_text else ''}

                    <!-- SIGN-OFF -->
                    <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #1e293b; color: #94a3b8; font-size: 13px; line-height: 1.5;">
                      Thanks and regards,<br>
                      <strong style="color: #f1f5f9;">Team StudyVault</strong>
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td align="center" style="padding: 24px 12px; color: #64748b; font-size: 11px; line-height: 1.6;">
              <p style="margin: 0 0 6px 0;">You received this transactional email from StudyVault.</p>
              <p style="margin: 0;">&copy; {time.strftime('%Y')} StudyVault Digital Library. Empowering collaborative student education.</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    # --- EMAIL FLOW 1: WELCOME EMAIL ---

    def send_welcome_email(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a welcome email to a student after successfully registering on StudyVault.
        Idempotent: Avoids duplicate sends if already logged.
        """
        user_id = str(user.get('id', ''))
        recipient_email = user.get('email', '').strip()
        recipient_name = user.get('full_name', '').strip() or 'Student'

        if self.db_service and self.db_service.has_email_been_sent('welcome', user_id):
            logger.info("Welcome email already sent to user %s. Skipping.", user_id)
            return {"success": True, "status": "already_sent", "message_id": "cached"}

        subject = "Welcome to StudyVault — Unlock a World of Knowledge"
        preheader = "Welcome to StudyVault! Explore, download, and share peer-verified educational resources."

        body_html = f"""
        <h1 style="color: #ffffff; font-size: 22px; font-weight: 800; margin: 0 0 16px 0; letter-spacing: -0.5px;">
          Welcome to StudyVault, {recipient_name}! &#127891;
        </h1>
        <p style="margin: 0 0 16px 0;">
          Thank you for joining <strong>StudyVault</strong> — the student-driven digital library designed to help you excel in your academic journey.
        </p>
        <p style="margin: 0 0 20px 0;">
          Through StudyVault, you can explore and access high-quality learning resources including semester notes, engineering lab manuals, coding guides, interview preparation kits, and previous exam question papers shared by fellow students.
        </p>

        <div style="background-color: #0f172a; border: 1px solid #1e293b; border-radius: 14px; padding: 18px 20px; margin: 20px 0;">
          <div style="font-size: 13px; font-weight: 700; color: #a5b4fc; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
            How StudyVault Works
          </div>
          <ul style="margin: 0; padding-left: 20px; color: #cbd5e1; font-size: 13.5px; line-height: 1.7;">
            <li><strong>Explore & Preview:</strong> Search thousands of categorized subjects and preview PDF notes directly in your browser.</li>
            <li><strong>Give & Take Community:</strong> Upload a valid study document (notes, syllabus, PYQ) to instantly unlock <strong>24 hours of unlimited downloads</strong>.</li>
            <li><strong>Safe & Verified:</strong> Every document is analyzed for authenticity and zero duplicates.</li>
          </ul>
        </div>

        <p style="margin: 0;">
          Ready to dive in? Start browsing today and discover resources for your courses.
        </p>
        """

        text_content = f"""Welcome to StudyVault, {recipient_name}!

Thank you for joining StudyVault — the student-driven digital library designed to help you excel in your academic journey.

Through StudyVault, you can explore and access high-quality learning resources including semester notes, engineering lab manuals, coding guides, interview preparation kits, and previous exam question papers shared by fellow students.

How StudyVault Works:
- Explore & Preview: Search thousands of categorized subjects and preview PDF notes directly in your browser.
- Give & Take Community: Upload a valid study document to instantly unlock 24 hours of unlimited downloads.
- Safe & Verified: Every document is analyzed for authenticity and zero duplicates.

Start exploring now: {self.frontend_url}

Thanks and regards,
Team StudyVault
"""

        html_content = self._render_base_template(
            title=subject,
            preheader=preheader,
            body_html=body_html,
            cta_url=self.frontend_url,
            cta_text="Explore Learning Resources"
        )

        result = self._send_brevo_transactional_email(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

        if self.db_service:
            self.db_service.log_email(
                user_id=user_id,
                email_type='welcome',
                recipient=recipient_email,
                reference_id=user_id,
                status='sent' if result.get('success') else 'failed',
                message_id=result.get('message_id'),
                error_message=result.get('error')
            )

        return result

    # --- EMAIL FLOW 2: RESOURCE UPLOAD CONFIRMATION ---

    def send_upload_confirmation_email(
        self, 
        user: Dict[str, Any], 
        document: Dict[str, Any], 
        reward_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sends an upload confirmation email when a user's uploaded resource passes validation
        and is accepted, granting 24 hours of unlimited download access.
        """
        user_id = str(user.get('id', ''))
        doc_id = str(document.get('id', ''))
        recipient_email = user.get('email', '').strip()
        recipient_name = user.get('full_name', '').strip() or 'Student'
        doc_title = document.get('title', 'Study Document')

        if self.db_service and self.db_service.has_email_been_sent('upload_confirmation', doc_id):
            logger.info("Upload confirmation already sent for document %s. Skipping.", doc_id)
            return {"success": True, "status": "already_sent", "message_id": "cached"}

        subject = f"Resource Uploaded Successfully — 24 Hours Unlimited Access Unlocked!"
        preheader = f"Your document '{doc_title}' has been accepted. You have unlocked 24 hours of unlimited downloads on StudyVault!"

        body_html = f"""
        <div style="background-color: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 12px 16px; margin-bottom: 20px; display: inline-block;">
          <span style="color: #34d399; font-weight: 800; font-size: 13px;">&#10004; Verified & Approved</span>
        </div>

        <h1 style="color: #ffffff; font-size: 22px; font-weight: 800; margin: 0 0 16px 0; letter-spacing: -0.5px;">
          Great job, {recipient_name}!
        </h1>
        <p style="margin: 0 0 16px 0;">
          Your educational resource <strong>"{doc_title}"</strong> has passed verification and has been added to the StudyVault digital library.
        </p>

        <!-- REWARD NOTICE BOX -->
        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(99, 102, 241, 0.15) 100%); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 16px; padding: 22px 24px; margin: 24px 0; text-align: left;">
          <div style="font-size: 12px; font-weight: 800; color: #34d399; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">
            Access Reward Activated
          </div>
          <div style="font-size: 19px; font-weight: 800; color: #ffffff; margin-bottom: 8px;">
            24 Hours of Unlimited Downloads
          </div>
          <p style="margin: 0; color: #cbd5e1; font-size: 13.5px; line-height: 1.6;">
            As a reward for contributing to the community, your account has been unlocked with full unlimited download privileges for the next <strong>24 hours</strong>. You can now download study guides, interview sets, and previous question papers without restrictions.
          </p>
        </div>

        <p style="margin: 0 0 12px 0;">
          Thank you for supporting your fellow learners. By sharing verified study materials, you're making education more accessible to everyone.
        </p>
        """

        text_content = f"""Great job, {recipient_name}!

Your educational resource "{doc_title}" has passed verification and has been added to the StudyVault digital library.

ACCESS REWARD ACTIVATED: 24 Hours of Unlimited Downloads
As a reward for contributing to the community, your account has been unlocked with full unlimited download privileges for the next 24 hours. You can now download study guides, interview sets, and previous question papers without restrictions.

Explore and download resources now: {self.frontend_url}

Thanks and regards,
Team StudyVault
"""

        html_content = self._render_base_template(
            title=subject,
            preheader=preheader,
            body_html=body_html,
            cta_url=f"{self.frontend_url}",
            cta_text="Download Study Resources"
        )

        result = self._send_brevo_transactional_email(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

        if self.db_service:
            self.db_service.log_email(
                user_id=user_id,
                email_type='upload_confirmation',
                recipient=recipient_email,
                reference_id=doc_id,
                status='sent' if result.get('success') else 'failed',
                message_id=result.get('message_id'),
                error_message=result.get('error')
            )

        return result

    # --- EMAIL FLOW 3: 10-HOUR ACCESS REMAINING REMINDER ---

    def send_access_reminder_email(self, user: Dict[str, Any], remaining_seconds: int = 36000) -> Dict[str, Any]:
        """
        Sends an automatic reminder email when a student's 24-hour access period has
        approximately 10 hours remaining.
        """
        user_id = str(user.get('id', ''))
        recipient_email = user.get('email', '').strip()
        recipient_name = user.get('full_name', '').strip() or 'Student'
        current_expiry = user.get('download_access_expires_at', '')

        # Calculate approximate remaining hours for friendly copy
        remaining_hours = max(1, round(remaining_seconds / 3600))

        subject = f"Reminder: {remaining_hours} Hours of Unlimited Access Remaining — StudyVault"
        preheader = f"You have {remaining_hours} hours left of unlimited download access on StudyVault. Download your needed resources or upload to extend."

        body_html = f"""
        <div style="background-color: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 12px; padding: 10px 16px; margin-bottom: 20px; display: inline-block;">
          <span style="color: #fbbf24; font-weight: 800; font-size: 13px;">&#9200; {remaining_hours} Hours Remaining</span>
        </div>

        <h1 style="color: #ffffff; font-size: 22px; font-weight: 800; margin: 0 0 16px 0; letter-spacing: -0.5px;">
          Time is ticking, {recipient_name}!
        </h1>
        <p style="margin: 0 0 16px 0;">
          This is a friendly reminder that your 24-hour unlimited download access on <strong>StudyVault</strong> will expire in approximately <strong>{remaining_hours} hours</strong>.
        </p>

        <!-- HIGHLIGHT CARD -->
        <div style="background-color: #0f172a; border: 1px solid #1e293b; border-radius: 16px; padding: 22px 24px; margin: 24px 0;">
          <div style="font-size: 14px; font-weight: 700; color: #ffffff; margin-bottom: 10px;">
            Make the most of your remaining time:
          </div>
          <ul style="margin: 0; padding-left: 20px; color: #cbd5e1; font-size: 13.5px; line-height: 1.8;">
            <li><strong>Download your course materials:</strong> Grab any lecture slides, revision summaries, and question papers you need for upcoming exams.</li>
            <li><strong>Want to extend for another 24 hours?</strong> Simply upload another valid study document (notes, syllabus, interview sheet) and your unlimited download access will be refreshed!</li>
          </ul>
        </div>

        <p style="margin: 0;">
          Don't wait until your access runs out — grab what you need now or contribute a resource to keep your access active.
        </p>
        """

        text_content = f"""Time is ticking, {recipient_name}!

This is a friendly reminder that your 24-hour unlimited download access on StudyVault will expire in approximately {remaining_hours} hours.

Make the most of your remaining time:
1. Download your course materials: Grab any lecture slides, revision summaries, and question papers you need.
2. Extend for another 24 hours: Simply upload another valid study document (notes, syllabus, interview sheet) to refresh your access!

Explore and download: {self.frontend_url}
Contribute a document: {self.frontend_url}/upload

Thanks and regards,
Team StudyVault
"""

        html_content = self._render_base_template(
            title=subject,
            preheader=preheader,
            body_html=body_html,
            cta_url=f"{self.frontend_url}",
            cta_text="Download Materials Now"
        )

        result = self._send_brevo_transactional_email(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

        if self.db_service:
            ref_id = f"{user_id}:{current_expiry}"
            self.db_service.log_email(
                user_id=user_id,
                email_type='access_reminder_10h',
                recipient=recipient_email,
                reference_id=ref_id,
                status='sent' if result.get('success') else 'failed',
                message_id=result.get('message_id'),
                error_message=result.get('error')
            )

        return result

    # --- ASYNC DISPATCH HELPER ---

    def dispatch_async(self, target_func, *args, **kwargs):
        """
        Dispatches an email function in a background daemon thread so user requests
        (e.g. registration, document upload) are returned instantly without waiting for network I/O.
        """
        def _runner():
            try:
                target_func(*args, **kwargs)
            except Exception as e:
                logger.error("Error in asynchronous email dispatch: %s", str(e))

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()
        return thread
