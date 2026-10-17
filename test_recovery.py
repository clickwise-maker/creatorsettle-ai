"""
CreatorSettle AI — Recovery Tests
Mocks network so tests do not depend on live PayPal.
"""

from unittest.mock import patch
from creatorsettle_recovery import capture_outstanding_balance

def test_no_token():
    print("=== No token ===")
    with patch("creatorsettle_recovery.get_access_token", return_value=None):
        r = capture_outstanding_balance("I-TEST", "20.00")
        assert r["success"] is False
        assert r["reason"] == "no_oauth_token"
    print("PASS")

def test_success_mock():
    print("\n=== Success mock ===")
    class FakeResp:
        status_code = 201
        def json(self):
            return {"status": "COMPLETED", "id": "CAP-1"}
    with patch("creatorsettle_recovery.get_access_token", return_value="fake"):
        with patch("creatorsettle_recovery.requests.post", return_value=FakeResp()):
            r = capture_outstanding_balance("I-TEST", "20.00")
            assert r["success"] is True
            assert r["reason"] == "captured"
    print("PASS")

def test_api_error_mock():
    print("\n=== API error mock ===")
    class FakeResp:
        status_code = 422
        def json(self):
            return {"name": "UNPROCESSABLE_ENTITY"}
    with patch("creatorsettle_recovery.get_access_token", return_value="fake"):
        with patch("creatorsettle_recovery.requests.post", return_value=FakeResp()):
            r = capture_outstanding_balance("I-TEST", "20.00")
            assert r["success"] is False
            assert r["reason"] == "api_error"
    print("PASS")

if __name__ == "__main__":
    test_no_token()
    test_success_mock()
    test_api_error_mock()
    print("\n=== Recovery tests passed ===")
