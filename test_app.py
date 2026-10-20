import json
import time
from unittest.mock import patch
from app import app, otp_sessions, hash_otp

def run_tests():
    print("\n" + "=" * 60)
    print("RUNNING AUTOMATED TEST SUITE FOR KARTIK BHOR PORTFOLIO")
    print("=" * 60 + "\n")

    client = app.test_client()
    passed = 0
    total = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f" [PASS] {name}")
        else:
            print(f" [FAIL] {name} - {details}")

    # Mock send_otp_email for local unit testing so it does not fail when running offline
    with patch("app.send_otp_email", return_value=(True, "A 6-digit code has been sent")):
        # Test 1: Home Page GET
        res = client.get("/")
        assert_test(
            "Home Page (GET /) returns 200",
            res.status_code == 200 and "Kartik Bhor" in res.text and "Smart Attendance System" in res.text,
            f"Status: {res.status_code}"
        )

        # Test 2: Health Check GET
        res = client.get("/health")
        data = res.get_json()
        assert_test(
            "Health Endpoint (GET /health) returns valid JSON",
            res.status_code == 200 and data.get("status") == "healthy" and "database" in data,
            f"Data: {data}"
        )

        # Test 3: Send OTP with empty payload
        res = client.post("/api/send-otp", json={})
        data = res.get_json()
        assert_test(
            "Send OTP with empty payload returns 400",
            res.status_code == 400 and not data.get("success"),
            f"Status: {res.status_code}, Msg: {data}"
        )

        # Test 4: Send OTP with invalid email
        res = client.post("/api/send-otp", json={
            "name": "Kartik Tester",
            "email": "not-an-email",
            "subject": "Inquiry",
            "message": "Testing the message validation length."
        })
        data = res.get_json()
        assert_test(
            "Send OTP with invalid email format returns 400",
            res.status_code == 400 and "valid email" in data.get("error", "").lower(),
            f"Msg: {data.get('error')}"
        )

        # Test 5: Send OTP with short message
        res = client.post("/api/send-otp", json={
            "name": "Kartik Tester",
            "email": "tester@example.com",
            "subject": "Inquiry",
            "message": "Too short"
        })
        data = res.get_json()
        assert_test(
            "Send OTP with message < 10 chars returns 400",
            res.status_code == 400 and "10" in data.get("error", ""),
            f"Msg: {data.get('error')}"
        )

        # Test 6: Send OTP with valid data
        valid_payload = {
            "name": "Alex Developer",
            "email": "alex.test@example.com",
            "subject": "AI Project Collaboration",
            "message": "Hello Kartik, I am interested in collaborating with you on a computer vision project."
        }
        res = client.post("/api/send-otp", json=valid_payload)
        data = res.get_json()
        session_token = data.get("session_token")
        assert_test(
            "Send OTP with valid payload returns 200 & session_token",
            res.status_code == 200 and data.get("success") and session_token is not None,
            f"Data: {data}"
        )

        # Test 7: Verify OTP with wrong code
        res = client.post("/api/verify-otp", json={
            "session_token": session_token,
            "otp": "000000"
        })
        data = res.get_json()
        assert_test(
            "Verify OTP with incorrect code returns 400 with attempts countdown",
            res.status_code == 400 and "attempt" in data.get("error", "").lower(),
            f"Msg: {data.get('error')}"
        )

        # Test 8: Verify OTP with correct code
        session = otp_sessions.get(session_token)
        found_otp = None
        if session:
            for candidate in range(100000, 1000000):
                c_str = str(candidate)
                if hash_otp(session["email"], session_token, c_str) == session["otp_hash"]:
                    found_otp = c_str
                    break

        assert_test(
            "Internal cryptographic digest found valid OTP",
            found_otp is not None,
            "Could not resolve test OTP"
        )

        if found_otp:
            res = client.post("/api/verify-otp", json={
                "session_token": session_token,
                "otp": found_otp
            })
            data = res.get_json()
            assert_test(
                "Verify OTP with valid code succeeds (200 OK)",
                res.status_code == 200 and data.get("success") is True,
                f"Data: {data}"
            )

            # Test 9: Anti-Replay: Re-submitting the same session token fails
            res = client.post("/api/verify-otp", json={
                "session_token": session_token,
                "otp": found_otp
            })
            data = res.get_json()
            assert_test(
                "Anti-Replay protection prevents reusing the same session token",
                res.status_code == 400,
                f"Data: {data}"
            )

        # Test 10: Resend OTP cooldown enforcement
        res = client.post("/api/send-otp", json={
            "name": "Cooldown Tester",
            "email": "cooldown@example.com",
            "subject": "Cooldown Check",
            "message": "Testing the 45-second resend cooldown timer."
        })
        data = res.get_json()
        new_token = data.get("session_token")
        
        # Try resending immediately
        res = client.post("/api/resend-otp", json={"session_token": new_token})
        data = res.get_json()
        assert_test(
            "Resend OTP enforces 45-second cooldown (HTTP 429)",
            res.status_code == 429 and "wait" in data.get("error", "").lower(),
            f"Status: {res.status_code}, Msg: {data.get('error')}"
        )

        # Fast forward cooldown in session
        if new_token in otp_sessions:
            otp_sessions[new_token]["last_sent_at"] -= 50
            res = client.post("/api/resend-otp", json={"session_token": new_token})
            data = res.get_json()
            assert_test(
                "Resend OTP succeeds after cooldown elapses (HTTP 200)",
                res.status_code == 200 and data.get("success") is True,
                f"Status: {res.status_code}, Msg: {data}"
            )

    print("\n" + "-" * 60)
    print(f"RESULTS: {passed}/{total} TESTS PASSED")
    print("-" * 60 + "\n")

    return passed == total

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
