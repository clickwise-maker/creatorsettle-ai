"""
CreatorSettle AI — Simple Backend
Binds to 127.0.0.1 by default. Server-side validation.
"""

from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path

from creatorsettle_reader import fetch_failed_transactions, get_access_token
from creatorsettle_decision import decide
from creatorsettle_approval import propose, decide as approval_decide, get_status, get_record, _load
from creatorsettle_execution import execute_action

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
    data = request.get_json() or {}
    action = data.get("action", "HOLD")
    message = data.get("message", "")
    status = propose(txn_id, action, message)
    return jsonify({"txn_id": txn_id, "status": status})

@app.route("/api/approve/<txn_id>", methods=["POST"])
def api_approve(txn_id):
    record = get_record(txn_id)
    if not record:
        return jsonify({"error": "no approval record"}), 400
    status = approval_decide(txn_id, "APPROVE")
    return jsonify({"txn_id": txn_id, "status": status})

@app.route("/api/reject/<txn_id>", methods=["POST"])
def api_reject(txn_id):
    record = get_record(txn_id)
    if not record:
        return jsonify({"error": "no approval record"}), 400
    status = approval_decide(txn_id, "REJECT")
    return jsonify({"txn_id": txn_id, "status": status})

@app.route("/api/execute/<txn_id>", methods=["POST"])
def api_execute(txn_id):
    # Ignore client action/type; use stored record
    token = get_access_token()
    result = execute_action(txn_id, access_token=token)
    return jsonify(result)

@app.route("/api/approvals")
def api_approvals():
    return jsonify(_load())

if __name__ == "__main__":
    # Local only by default
    app.run(host="127.0.0.1", port=5000, debug=False)
