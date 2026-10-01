# Enterprise Data Retention Policy 2026

## 1. Scope and Compliance
This policy governs data archival lifecycles across all production cloud workloads for ISO 27001 compliance.

## 2. Retention Schedules
All non-essential database transactional records are archived to cold storage after 180 days.
Audit trails and access logs must be retained in immutable storage for a minimum of 365 calendar days.

## 3. Account Termination & Anonymization
Customer personal identifiers are cryptographically anonymized within 30 days of formal account closure.
Residual backup snapshots are permanently purged following standard automated retention sweeps.
