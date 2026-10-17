"""
PayPal recovery unit tests. All network interactions are mocked; no real payment is made.
"""
from unittest.mock import patch
from creatorsettle_recovery import capture_outstanding_balance


def fake_response(status_code, payload):
    class FakeResp:
        def __init__(self):
            self.status_code = status_code
        def json(self):
            return payload
    return FakeResp()


def test_no_token():
    with patch("creatorsettle_recovery.get_access_token", return_value=None):
        result = capture_outstanding_balance("I-TEST12345", "20.00")
    assert result["success"] is False
    assert result["reason"] == "no_oauth_token"


def test_invalid_inputs_do_not_call_paypal():
    cases = [
        ("bad id", "20.00", "USD", "invalid_subscription_id"),
        ("I-TEST12345", "-1.00", "USD", "invalid_amount"),
        ("I-TEST12345", "0.00", "USD", "invalid_amount"),
        ("I-TEST12345", "1.234", "USD", "invalid_amount"),
        ("I-TEST12345", "10.00", "us", "invalid_currency"),
    ]
    with patch("creatorsettle_recovery.get_access_token") as token_mock:
        for subscription_id, amount, currency, expected in cases:
            result = capture_outstanding_balance(subscription_id, amount, currency)
            assert result["success"] is False
            assert result["reason"] == expected
        token_mock.assert_not_called()


def test_confirmed_capture_mock():
    with patch("creatorsettle_recovery.get_access_token", return_value="fake"):
        with patch("creatorsettle_recovery.requests.post", return_value=fake_response(201, {"status": "COMPLETED", "id": "CAP-1"})) as post:
            result = capture_outstanding_balance("I-TEST12345", "20.00")
    assert result["success"] is True
    assert result["state"] == "CAPTURE_CONFIRMED"
    assert post.call_args.kwargs["json"]["amount"]["value"] == "20.00"


def test_accepted_is_not_confirmed():
    with patch("creatorsettle_recovery.get_access_token", return_value="fake"):
        with patch("creatorsettle_recovery.requests.post", return_value=fake_response(202, {"status": "PENDING"})):
            result = capture_outstanding_balance("I-TEST12345", "20.00")
    assert result["success"] is True
    assert result["state"] == "REQUEST_ACCEPTED"
    assert result["state"] != "CAPTURE_CONFIRMED"


def test_api_error_mock():
    with patch("creatorsettle_recovery.get_access_token", return_value="fake"):
        with patch("creatorsettle_recovery.requests.post", return_value=fake_response(422, {"name": "UNPROCESSABLE_ENTITY"})):
            result = capture_outstanding_balance("I-TEST12345", "20.00")
    assert result["success"] is False
    assert result["state"] == "FAILED"
    assert result["reason"] == "api_error"


if __name__ == "__main__":
    for test in (
        test_no_token,
        test_invalid_inputs_do_not_call_paypal,
        test_confirmed_capture_mock,
        test_accepted_is_not_confirmed,
        test_api_error_mock,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All mocked recovery tests passed; no live PayPal calls were made.")
