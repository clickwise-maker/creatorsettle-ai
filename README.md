# CreatorSettle AI

**Self-healing PayPal settlement agent for creators, freelancers, and small businesses.**

An AI-powered agent that monitors failed/declined PayPal settlements, decides the best recovery action (RETRY / ROUTE / ALERT / HOLD), requires one-tap creator approval, and logs every decision in a tamper-proof hash-chain audit log.

Built for the **PayPal AI Hackathon 2026**.

---

## Problem

Creators and freelancers lose money and time when PayPal settlements fail due to:
- Insufficient funds
- Expired cards
- Fraud filters
- Currency or hold issues

There is no autonomous system that diagnoses the failure, chooses a recovery path, and keeps a full audit trail.

## Solution

CreatorSettle AI is an **agentic** system that:
1. Reads failed/pending transactions (PayPal Sandbox)
2. Uses a decision engine to choose the safest next action
3. Asks the creator for one-tap approval before any execution
4. Writes every decision into an immutable hash-chain audit log

## Architecture

```
PayPal Sandbox
     │
     ▼
┌─────────────┐
│   Reader    │  ← OAuth2 + Transaction fetch
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Decision   │  ← RETRY / ROUTE / ALERT / HOLD
│   Engine    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Approval   │  ← One-tap creator approve/reject
│   Layer     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Audit     │  ← Tamper-proof hash chain
│   Logger    │
└─────────────┘
```

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/clickwise-maker/creatorsettle-ai.git
cd creatorsettle-ai
pip install -r requirements.txt
```

### 2. PayPal Sandbox Credentials

1. Go to https://developer.paypal.com and log in
2. Apps & Credentials → Sandbox → Create App
3. Copy **Client ID** and **Secret**

Create a `.env` file:

```env
PAYPAL_CLIENT_ID=your_client_id
PAYPAL_SECRET=your_secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
```

### 3. Run the Demo

```bash
python creatorsettle_demo.py
```

You should see decisions for 5 mock failed transactions + audit chain verification.

### 4. Test OAuth Only

```bash
python creatorsettle_reader.py
```

## Modules

| File | Purpose |
|------|---------|
| `creatorsettle_reader.py` | PayPal OAuth + transaction fetch |
| `creatorsettle_decision.py` | Decision engine (RETRY/ROUTE/ALERT/HOLD) |
| `creatorsettle_approval.py` | One-tap approval layer |
| `creatorsettle_audit.py` | Tamper-proof hash-chain logger |
| `creatorsettle_demo.py` | End-to-end demo |

## Demo Video

A 3-minute demo video will be linked here before final submission.

## License

MIT

## Hackathon

- **Event**: PayPal AI Hackathon 2026
- **Deadline**: 12 November 2026, 12:00 PM PT
- **Target Categories**: Best Use of Agentic Commerce, Best Use of PayPal + AI
