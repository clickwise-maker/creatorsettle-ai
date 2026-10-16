# CreatorSettle AI

Self-healing PayPal settlement agent for creators, freelancers, and small online stores.

## Problem
Creators frequently face failed or delayed PayPal settlements (declines, holds, currency issues). Manual retries waste time and money. There is no autonomous agent that monitors, diagnoses, and recovers these automatically with a full audit trail.

## Solution
An AI-powered agent that:
- Reads failed/pending transactions via PayPal Sandbox APIs
- Uses a decision engine to choose RETRY / ROUTE / ALERT / HOLD
- Requires one-tap creator approval before execution
- Logs every decision in a tamper-proof hash-chain audit log

## Status
Prototype modules (Reader, Decision Engine, Approval Layer, Audit Logger) + end-to-end demo.

## Built for
PayPal AI Hackathon 2026  
Deadline: 12 November 2026  
Target: Best Use of Agentic Commerce + Best Overall

## License
MIT
