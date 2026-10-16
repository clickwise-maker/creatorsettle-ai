# CreatorSettle AI

**Self-healing PayPal settlement agent prototype for creators.**

An agent that reads failed PayPal transactions, decides the next recovery action, requires creator approval, and logs decisions in a hash-chain audit log.

**This is a working prototype.** Approval is in-memory. Recovery execution is simulated except for one real Sandbox order creation. Audit is a hash-chain integrity check, not a full tamper-proof system.

Built for the PayPal AI Hackathon 2026.

---

## Quick Start

```bash
git clone https://github.com/clickwise-maker/creatorsettle-ai.git
cd creatorsettle-ai
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your PayPal Sandbox Client ID and Secret
python creatorsettle_demo.py
```

## Modes

- **With credentials**: Real OAuth + attempt at Transaction Search + real test order creation.
- **Without credentials**: Clear mock mode with labeled mock transactions.

## Modules

| File | Purpose |
|------|---------|
| `creatorsettle_reader.py` | OAuth + transaction fetch (real or mock) + test order |
| `creatorsettle_decision.py` | Decision engine |
| `creatorsettle_approval.py` | In-memory approval layer |
| `creatorsettle_audit.py` | Hash-chain audit logger |
| `creatorsettle_demo.py` | End-to-end demo |

## Notes for Judges

- Meaningful use of PayPal Sandbox (OAuth + Orders API).
- Clear separation of real vs simulated behavior.
- Decision logic is deterministic and testable.

## License

MIT
