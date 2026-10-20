import os
import re
import time
import secrets
import hashlib
import hmac
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

# Load local environment variables from .env file if it exists
load_dotenv()

app = Flask(__name__)

# Security configuration
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://uhreznoytbvlommykqpe.supabase.co").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# SMTP Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
MAIL_FROM = os.getenv("MAIL_FROM", f"Kartik Bhor Portfolio <{SMTP_USERNAME}>" if SMTP_USERNAME else "noreply@kartikbhor.dev")
CONTACT_INBOX = os.getenv("CONTACT_INBOX", SMTP_USERNAME or "kartikbhor619@gmail.com").strip()

# Salt used for internal OTP HMAC/hashing
INTERNAL_SALT = app.config["SECRET_KEY"]

# Startup time for health check
START_TIME = time.time()

# ------------------------------------------------------------------------------
# IN-MEMORY SESSION & RATE-LIMIT STORE
# Structure of otp_sessions[session_token]:
# {
#   "email": str,
#   "name": str,
#   "subject": str,
#   "message": str,
#   "otp_hash": str,
#   "created_at": float (timestamp),
#   "expires_at": float (timestamp),
#   "last_sent_at": float (timestamp),
#   "attempts": int,
#   "verified": bool,
#   "ip": str
# }
# ------------------------------------------------------------------------------
otp_sessions = {}

# Rate limiting data:
# ip_history[ip] = [timestamp1, timestamp2, ...]
ip_history = {}
# email_history[email] = last_sent_timestamp
email_history = {}

# Local verified messages store (Used when Supabase credentials are in setup/mock mode)
local_messages_store = []


# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------
def hash_otp(email: str, session_token: str, otp: str) -> str:
    """Generates a keyed SHA-256 digest of the OTP and session token."""
    raw = f"{INTERNAL_SALT}:{session_token.strip()}:{email.strip().lower()}:{otp.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_rate_limited(ip: str, email: str) -> tuple[bool, str]:
    """Checks rate limits per IP and email to prevent abuse."""
    now = time.time()
    
    # Check cooldown for email (at least 45 seconds between sends)
    last_sent = email_history.get(email.lower())
    if last_sent and (now - last_sent) < 45:
        remaining = int(45 - (now - last_sent))
        return True, f"Please wait {remaining} seconds before requesting another verification code."

    # Check IP hourly quota (max 10 OTP requests per hour)
    history = ip_history.get(ip, [])
    # Filter timestamps within the last 3600 seconds
    valid_history = [t for t in history if now - t < 3600]
    ip_history[ip] = valid_history

    if len(valid_history) >= 10:
        return True, "Too many verification requests from this network. Please try again in an hour."

    return False, ""


def record_request(ip: str, email: str):
    """Records an OTP send event for rate limiting."""
    now = time.time()
    ip_history.setdefault(ip, []).append(now)
    email_history[email.lower()] = now


def validate_contact_payload(data: dict) -> tuple[bool, str, dict]:
    """Validates user contact submission."""
    if not isinstance(data, dict):
        return False, "Invalid payload format.", {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    subject = str(data.get("subject", "")).strip()
    message = str(data.get("message", "")).strip()

    if not name or len(name) < 2 or len(name) > 100:
        return False, "Please provide a valid name between 2 and 100 characters.", {}

    email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not email or len(email) > 255 or not re.match(email_regex, email):
        return False, "Please provide a valid email address.", {}

    if not subject or len(subject) < 2 or len(subject) > 200:
        return False, "Please provide a subject between 2 and 200 characters.", {}

    if not message or len(message) < 10 or len(message) > 4000:
        return False, "Message must be between 10 and 4000 characters.", {}

    return True, "", {
        "name": name,
        "email": email,
        "subject": subject,
        "message": message
    }


def get_smtp_credentials():
    """Dynamically reloads and returns sanitized SMTP credentials."""
    load_dotenv(override=True)
    host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "").strip()
    raw_pwd = os.getenv("SMTP_PASSWORD", "")
    password = raw_pwd.strip().replace(" ", "")
    mail_from = os.getenv("MAIL_FROM", f"Kartik Bhor Portfolio <{username}>" if username else "noreply@kartikbhor.dev")
    inbox = os.getenv("CONTACT_INBOX", username or "kartikbhor619@gmail.com").strip()
    return host, port, username, password, mail_from, inbox


def is_smtp_configured() -> bool:
    """Returns True if real SMTP credentials have been provided in .env."""
    host, port, username, password, _, _ = get_smtp_credentials()
    is_placeholder = (
        not password
        or password.startswith("your_")
        or "16_character" in password
        or username.startswith("your_")
        or "@" not in username
    )
    return bool(host and port and username and not is_placeholder)


def send_otp_email(to_email: str, recipient_name: str, otp_code: str) -> tuple[bool, str]:
    """Sends OTP verification email via SMTP directly to the visitor's real email address."""
    host, port, username, password, mail_from, _ = get_smtp_credentials()

    if not is_smtp_configured():
        return False, "Email service is not configured. Please set SMTP_PASSWORD in your environment variables."

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{otp_code} is your Kartik Bhor Portfolio Verification Code"
        msg["From"] = mail_from
        msg["To"] = to_email

        plain_text = (
            f"Hello {recipient_name},\n\n"
            f"Your verification code for Kartik Bhor's developer portfolio is: {otp_code}\n\n"
            f"This code will expire in 5 minutes.\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"Best regards,\nKartik Bhor"
        )

        html_text = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:24px;background-color:#121214;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#e1e1e6;">
          <div style="max-width:520px;margin:0 auto;background:#1a1a1e;border:1px solid #2e2e36;border-radius:12px;padding:32px;box-shadow:0 10px 30px rgba(0,0,0,0.5);">
            <div style="text-align:center;margin-bottom:24px;">
              <span style="display:inline-block;padding:6px 14px;background:rgba(181,101,255,0.15);border:1px solid #b565ff;border-radius:20px;color:#b565ff;font-weight:700;font-size:12px;letter-spacing:1px;">
                SECURITY VERIFICATION
              </span>
              <h2 style="color:#ffffff;margin:16px 0 6px 0;font-size:22px;">Confirm Your Contact Request</h2>
              <p style="color:#a4a4ad;font-size:14px;margin:0;">Hi {recipient_name}, enter this 6-digit code to verify your email and deliver your message.</p>
            </div>
            
            <div style="background:#141416;border:1px dashed #b565ff;border-radius:10px;padding:20px;text-align:center;margin:24px 0;">
              <span style="font-size:36px;font-weight:800;letter-spacing:8px;color:#b565ff;font-family:monospace;">
                {otp_code}
              </span>
            </div>

            <p style="color:#8f8f9d;font-size:13px;line-height:1.5;margin:16px 0 0 0;text-align:center;">
              ⏰ This code is valid for <strong>5 minutes</strong> and can only be used once.<br>
              If you did not initiate this request, you can safely ignore this email.
            </p>

            <hr style="border:none;border-top:1px solid #2a2a32;margin:28px 0 20px 0;">
            <div style="text-align:center;color:#6b6b76;font-size:12px;">
              Kartik Bhor — Full Stack Developer & AI Engineer<br>
              <a href="https://github.com/kartikbhor413-hash" style="color:#9b6fd6;text-decoration:none;">github.com/kartikbhor413-hash</a>
            </div>
          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_text, "html"))

        # Primary attempt: Port 587 (STARTTLS)
        try:
            server = smtplib.SMTP(host, port, timeout=12)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.send_message(msg)
            server.quit()
        except (smtplib.SMTPServerDisconnected, TimeoutError, OSError):
            # Automatic fallback: Port 465 (Direct SSL)
            server = smtplib.SMTP_SSL(host, 465, timeout=12)
            server.login(username, password)
            server.send_message(msg)
            server.quit()

        return True, f"A 6-digit verification code has been sent to {to_email}. Please check your inbox."
    except smtplib.SMTPAuthenticationError as e:
        print(f"[SMTP AUTH ERROR] Gmail login rejected: {e}")
        return False, "Gmail authentication failed. Please verify your 16-character App Password."
    except Exception as e:
        print(f"[SMTP ERROR] {type(e).__name__}: {e}")
        return False, f"Failed to send email to {to_email}: {e}"


def notify_portfolio_owner(message_record: dict):
    """Notifies Kartik Bhor's inbox of the new verified contact message."""
    host, port, username, password, mail_from, inbox = get_smtp_credentials()

    if not is_smtp_configured():
        print(f"[NOTIFICATION LOG] Verified contact received from {message_record.get('email')} -> {inbox}")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚀 New Verified Message: {message_record.get('subject')} (from {message_record.get('name')})"
        msg["From"] = mail_from
        msg["To"] = inbox

        body = f"""
        New verified message submitted on Kartik Bhor Portfolio:
        
        Name: {message_record.get('name')}
        Email: {message_record.get('email')}
        Subject: {message_record.get('subject')}
        Timestamp: {datetime.now(timezone.utc).isoformat()}
        
        Message:
        ------------------------------------------------------------
        {message_record.get('message')}
        ------------------------------------------------------------
        """
        msg.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP(host, port, timeout=12)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.send_message(msg)
            server.quit()
        except (smtplib.SMTPServerDisconnected, TimeoutError, OSError):
            server = smtplib.SMTP_SSL(host, 465, timeout=12)
            server.login(username, password)
            server.send_message(msg)
            server.quit()

    except Exception as e:
        print(f"[NOTIFICATION ERROR] Failed to notify owner inbox: {e}")


def persist_verified_message(record: dict) -> tuple[bool, str]:
    """Saves the verified message to Supabase PostgreSQL or local fallback."""
    # Check if real Supabase credentials are configured
    is_supabase_ready = bool(
        SUPABASE_URL 
        and SUPABASE_KEY 
        and not SUPABASE_KEY.startswith("your_")
    )

    if is_supabase_ready:
        endpoint = f"{SUPABASE_URL}/rest/v1/contact_messages"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        payload = {
            "name": record["name"],
            "email": record["email"],
            "subject": record["subject"],
            "message": record["message"],
            "verified_at": datetime.now(timezone.utc).isoformat()
        }
        try:
            res = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            if res.status_code in (200, 201):
                return True, "Message saved to Supabase PostgreSQL."
            else:
                print(f"[SUPABASE ERROR] Status {res.status_code}: {res.text}")
                # Fallback to local store so data is not lost
                local_messages_store.append(record)
                return True, "Saved locally (Supabase returned non-200 code)."
        except Exception as e:
            print(f"[SUPABASE EXCEPTION] {e}")
            local_messages_store.append(record)
            return True, "Saved locally (Supabase request failed)."
    else:
        # Development mode without Supabase key
        local_messages_store.append(record)
        print(f"[LOCAL STORE] Contact message recorded locally for {record['email']} (Configure SUPABASE_KEY in .env)")
        return True, "Message saved to local dev store (Supabase credentials pending in .env)."


# ------------------------------------------------------------------------------
# FLASK ROUTES
# ------------------------------------------------------------------------------
@app.route("/")
def index():
    """Renders Kartik Bhor's developer portfolio."""
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint without exposing secrets."""
    is_supabase_configured = bool(SUPABASE_URL and SUPABASE_KEY and not SUPABASE_KEY.startswith("your_"))
    smtp_ready = is_smtp_configured()

    return jsonify({
        "status": "healthy",
        "service": "Kartik Bhor Portfolio API",
        "uptime_seconds": int(time.time() - START_TIME),
        "database": {
            "configured": is_supabase_configured,
            "provider": "Supabase PostgreSQL",
            "target": SUPABASE_URL
        },
        "email_service": {
            "configured": smtp_ready,
            "host": SMTP_HOST if smtp_ready else "Local Console Fallback"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


@app.route("/api/send-otp", methods=["POST"])
def send_otp():
    """Step 1 & 2: Validates contact form data and sends 6-digit OTP."""
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()
    data = request.get_json(silent=True) or {}

    # Validate form input
    is_valid, err_msg, validated = validate_contact_payload(data)
    if not is_valid:
        return jsonify({"success": False, "error": err_msg}), 400

    # Rate limit check
    rate_limited, limit_msg = is_rate_limited(client_ip, validated["email"])
    if rate_limited:
        return jsonify({"success": False, "error": limit_msg}), 429

    # Generate cryptographically secure 6-digit OTP
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    session_token = secrets.token_urlsafe(32)
    otp_digest = hash_otp(validated["email"], session_token, otp_code)

    now = time.time()
    expires_at = now + 300  # 5 minutes expiry

    # Store verification session in memory
    otp_sessions[session_token] = {
        "email": validated["email"],
        "name": validated["name"],
        "subject": validated["subject"],
        "message": validated["message"],
        "otp_hash": otp_digest,
        "created_at": now,
        "expires_at": expires_at,
        "last_sent_at": now,
        "attempts": 0,
        "verified": False,
        "ip": client_ip
    }

    # Record send for rate limits
    record_request(client_ip, validated["email"])

    # Send OTP email
    sent, status_msg = send_otp_email(validated["email"], validated["name"], otp_code)
    if not sent:
        return jsonify({
            "success": False, 
            "error": status_msg
        }), 500

    return jsonify({
        "success": True,
        "message": status_msg,
        "session_token": session_token,
        "expires_in": 300,
        "email": validated["email"]
    }), 200


@app.route("/api/resend-otp", methods=["POST"])
def resend_otp():
    """Resends OTP if cooldown period has passed."""
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()
    data = request.get_json(silent=True) or {}
    session_token = str(data.get("session_token", "")).strip()

    if not session_token or session_token not in otp_sessions:
        return jsonify({"success": False, "error": "Invalid or expired verification session. Please submit the form again."}), 400

    session = otp_sessions[session_token]
    if session.get("verified"):
        return jsonify({"success": False, "error": "This contact request has already been verified."}), 400

    # Check 45-second cooldown
    now = time.time()
    time_since_last = now - session.get("last_sent_at", 0)
    if time_since_last < 45:
        remaining = int(45 - time_since_last)
        return jsonify({"success": False, "error": f"Please wait {remaining} seconds before requesting a new code."}), 429

    # Generate fresh OTP
    new_otp = f"{secrets.randbelow(900000) + 100000}"
    session["otp_hash"] = hash_otp(session["email"], session_token, new_otp)
    session["expires_at"] = now + 300
    session["last_sent_at"] = now
    session["attempts"] = 0  # Reset attempts for new code

    # Record for rate limits
    record_request(client_ip, session["email"])

    sent, status_msg = send_otp_email(session["email"], session["name"], new_otp)
    if not sent:
        return jsonify({"success": False, "error": status_msg}), 500

    return jsonify({
        "success": True,
        "message": status_msg,
        "expires_in": 300
    }), 200


@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    """Step 4 & 5: Verifies the entered OTP and saves message to Supabase."""
    data = request.get_json(silent=True) or {}
    session_token = str(data.get("session_token", "")).strip()
    user_otp = str(data.get("otp", "")).strip()

    if not session_token or session_token not in otp_sessions:
        return jsonify({
            "success": False, 
            "error": "Verification session not found or expired. Please submit the form again."
        }), 400

    session = otp_sessions[session_token]

    if session.get("verified"):
        return jsonify({
            "success": False, 
            "error": "This message has already been verified and delivered."
        }), 400

    now = time.time()
    # Check expiration (5 minutes)
    if now > session.get("expires_at", 0):
        del otp_sessions[session_token]
        return jsonify({
            "success": False, 
            "error": "Verification code has expired. Please request a new code."
        }), 400

    # Check attempt limit (max 5)
    if session.get("attempts", 0) >= 5:
        del otp_sessions[session_token]
        return jsonify({
            "success": False, 
            "error": "Maximum verification attempts exceeded. Please submit your message again."
        }), 429

    # Verify OTP using constant-time comparison
    expected_hash = session["otp_hash"]
    computed_hash = hash_otp(session["email"], session_token, user_otp)

    if not hmac.compare_digest(expected_hash, computed_hash):
        session["attempts"] += 1
        remaining_attempts = 5 - session["attempts"]
        if remaining_attempts <= 0:
            del otp_sessions[session_token]
            return jsonify({
                "success": False, 
                "error": "Incorrect code. Maximum attempts reached. Please submit the form again."
            }), 429
        return jsonify({
            "success": False, 
            "error": f"Invalid verification code. {remaining_attempts} attempt(s) remaining."
        }), 400

    # Mark as verified
    session["verified"] = True

    # Persist message to Supabase PostgreSQL
    record = {
        "name": session["name"],
        "email": session["email"],
        "subject": session["subject"],
        "message": session["message"]
    }
    saved, db_status = persist_verified_message(record)

    # Invalidate session token to prevent any replay attacks
    del otp_sessions[session_token]

    # Notify portfolio owner (Kartik Bhor)
    notify_portfolio_owner(record)

    return jsonify({
        "success": True,
        "message": "Thank you! Your email has been verified and your message has been delivered to Kartik Bhor.",
        "db_status": db_status
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_ENV", "development") == "development"
    print(f"🚀 Kartik Bhor Portfolio server starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
