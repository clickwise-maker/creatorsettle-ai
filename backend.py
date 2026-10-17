"""
CreatorSettle AI — Simple local backend.
Binds to 127.0.0.1 by default. Subscription capture requires a separate approval.
"""
import hashlib
from decimal import Decimal, InvalidOperation

from flask import Flask, jsonify, request, send_from_directory

from creatorsettle_reader import fetch_failed_transactions, get_access_token
from creatorsettle_decision import decide
from creatorsettle_approval import propose, decide as approval_decide, get_status, get_record, _load
from creatorsettle_execution import execute_action
from creatorsettle_recovery import _validate_capture

app = Flask(__name__, static_folder=".")


@app.route("/")
def index():
    return send_from_directory(".", "dashboard.html")


@app.route("/api/transactions")
def api_transactions():
    token = get_access_token()
    txns = fetch_failed_transactions(token)
    result = []
    for txn in txns:
        action, conf, msg, exec_type = decide(txn)
        status = get_status(txn["id"])
        result.append({
            "id": txn["id"],
            "amount": txn["amount"],
            "currency": txn["currency"],
            "status": txn.get("status") or txn.get("decline_code"),
            "source": txn.get("source"),
            "proposed_action": action,
            "message": msg,
            "execution_type": exec_type,
            "approval_status": status or "NOT_PROPOSED",
        })
    return jsonify(result)


@app.route("/api/propose/<txn_id>", methods=["POST"])
def api_propose(txn_id):
    data = request.get_json(silent=True) or {}
    action = data.get("action", "HOLD")
    message = data.get("message", "")
    status = propose(txn_id, action, message)
    return jsonify({"txn_id": txn_id, "status": status})


@app.route("/api/approve/<txn_id>", methods=["POST"])
def api_approve(txn_id):
    if not get_record(txn_id):
        return jsonify({"error": "no approval record"}), 400
    status = approval_decide(txn_id, "APPROVE")
    return jsonify({"txn_id": txn_id, "status": status})


@app.route("/api/reject/<txn_id>", methods=["POST"])
def api_reject(txn_id):
    if not get_record(txn_id):
        return jsonify({"error": "no approval record"}), 400
    status = approval_decide(txn_id, "REJECT")
    return jsonify({"txn_id": txn_id, "status": status})


@app.route("/api/subscription-capture/propose", methods=["POST"])
def api_subscription_capture_propose():
    data = request.get_json(silent=True) or {}
    subscription_id = data.get("subscription_id", "")
    amount = data.get("amount", "")
    currency = data.get("currency", "USD")
    invalid = _validate_capture(subscription_id, amount, currency)
    if invalid:
        return jsonify({"error": invalid, "status": "BLOCKED"}), 400
    try:
        normalized_amount = format(Decimal(str(amount)), ".2f")
    except (InvalidOperation, ValueError, TypeError):
        return jsonify({"error": "invalid_amount", "status": "BLOCKED"}), 400

    # Stable request key blocks duplicate approval/execution for the same subscription+amount.
    key_source = f"{subscription_id}|{normalized_amount}|{currency}"
    request_id = "SUBCAP-" + hashlib.sha256(key_source.encode("utf-8")).hexdigest()[:24]
    status = propose(
        request_id,
        "CAPTURE_SUBSCRIPTION_BALANCE",
        f"Request outstanding balance capture of {currency} {normalized_amount} for subscription {subscription_id}",
        metadata={
            "subscription_id": subscription_id,
            "amount": normalized_amount,
            "currency": currency,
        },
    )
    return jsonify({
        "request_id": request_id,
        "status": status,
        "subscription_id": subscription_id,
        "amount": normalized_amount,
        "currency": currency,
        "requires_explicit_approval": True,
    })


@app.route("/api/subscription-capture/approve/<request_id>", methods=["POST"])
def api_subscription_capture_approve(request_id):
    record = get_record(request_id)
    if not record or record.get("action") != "CAPTURE_SUBSCRIPTION_BALANCE":
        return jsonify({"error": "no subscription capture approval request"}), 400
    status = approval_decide(request_id, "APPROVE")
    return jsonify({"request_id": request_id, "status": status})


@app.route("/api/subscription-capture/reject/<request_id>", methods=["POST"])
def api_subscription_capture_reject(request_id):
    record = get_record(request_id)
    if not record or record.get("action") != "CAPTURE_SUBSCRIPTION_BALANCE":
        return jsonify({"error": "no subscription capture approval request"}), 400
    status = approval_decide(request_id, "REJECT")
    return jsonify({"request_id": request_id, "status": status})


@app.route("/api/subscription-capture/execute/<request_id>", methods=["POST"])
def api_subscription_capture_execute(request_id):
    record = get_record(request_id)
    if not record or record.get("action") != "CAPTURE_SUBSCRIPTION_BALANCE":
        return jsonify({"error": "no subscription capture approval request", "state": "BLOCKED"}), 400
    result = execute_action(request_id)
    code = 200 if result.get("state") != "BLOCKED" else 409
    return jsonify(result), code


@app.route("/api/execute/<txn_id>", methods=["POST"])
def api_execute(txn_id):
    # Ignore client action/type; use stored record.
    token = get_access_token()
    return jsonify(execute_action(txn_id, access_token=token))


@app.route("/api/approvals")
def api_approvals():
    return jsonify(_load())


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
