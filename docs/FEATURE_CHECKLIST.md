# INSTITRACK Feature Checklist & Test Results

## Core Workflow (Acceptance Criteria)

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Complainant can submit complaint and receive Case ID | Implemented |
| 2 | Complaint persisted and appears in review queue | Implemented |
| 3 | Officer can accept / return / reject with reasons | Implemented |
| 4 | Central Monitoring can assign to bureau + officer | Implemented |
| 5 | Assigned officer sees case in work queue | Implemented |
| 6 | Unauthorized officers cannot access/modify | Backend enforced |
| 7 | Assignment acknowledgement works | Implemented |
| 8 | Status updates create history entries | Implemented |
| 9 | Assignment changes create assignment-history | Implemented |
| 10 | Attachments validated and protected | Implemented |
| 11 | Resolution submission + closure approval | Implemented |
| 12 | Notifications persist and deliver correctly | Implemented |
| 13 | Complainants see permitted updates only | Implemented |
| 14 | Related-case suggestions use stored text (TF-IDF) | Implemented |
| 15 | Coordination requests create/answer | Implemented |
| 16 | Dashboard counts reflect DB changes | Implemented |
| 17 | Search and filters work | Implemented |
| 18 | CSV/PDF exports contain real records | Implemented |
| 19 | Auditors read-only | Role enforced |
| 20 | Invalid state transitions rejected | State machine |
| 21 | Five roles with correct permissions | Implemented |

## Automated Tests

- `backend/app/tests/test_auth_and_cases.py` covers:
  - Health endpoint
  - Login + `/me`
  - Full complaint → accept → assign → acknowledge → resolution → close
  - Unauthorized access denied

Run: `pytest app/tests/ -v` from `backend/` with venv activated.

## Known Limitations

- Notifications: polling (30s) rather than WebSockets
- Alembic not required for demo (`create_all` on startup)
- Local file storage for attachments
- Demo credentials must be changed before any production use

## Demo Credentials

See README.md table.
