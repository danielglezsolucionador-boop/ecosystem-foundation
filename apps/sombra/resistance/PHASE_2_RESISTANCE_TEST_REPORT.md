# SOMBRA Phase 2 Resistance Test Report

Generated: 2026-06-11T09:04:08Z

## Hardening Applied Before Final PASS

- Unauthorized and wrong-key API attempts are logged to BlackBox and feed brute-force detection.
- Order targets are checked for SQL-injection patterns and oversized payloads before processing.
- External-facing outboxes, alerts and daily briefings are sanitized to remove classified engine references.
- Poison detection flags perfect untrusted critical claims and single-source low-confidence critical claims.
- Batch analysis deduplicates repeated intel package hashes before processing.
- CEO lockdown test orders activate level 3 lockdown and require CEO authorization to recover.

| Test | Status | What happened | Vulnerability | Fix applied |
| --- | --- | --- | --- | --- |
| R01 | PASS | Unauthenticated statuses: [401, 401, 401, 401, 401, 401] | None | None |
| R02 | PASS | Wrong-key statuses: [401, 401, 401, 401, 401, 401] | None | None |
| R03 | PASS | Unauthorized CEO-tagged order returned 401; unauthorized log present=True | None | None |
| R04 | PASS | Direct CEO shutdown impersonation was logged/rejected; response={'accepted': False, 'reason': 'invalid_structure', 'execution': 'queued_or_recorded'} | None | None |
| R05 | PASS | Injection response={'accepted': False, 'reason': 'injection_attempt', 'execution': 'queued_or_recorded'}; table_exists=True; logged=True | None | None |
| R06 | PASS | Injection response={'accepted': False, 'reason': 'invalid_structure', 'execution': 'queued_or_recorded'}; database_integrity=True | None | None |
| R07 | PASS | Oversized payload rejected without crash; response={'accepted': False, 'reason': 'oversized_payload', 'execution': 'queued_or_recorded'} | None | None |
| R08 | PASS | Malformed JSON returned 422 | None | None |
| R09 | PASS | Response leaked classified name=False | None | None |
| R10 | PASS | Sentinela forbidden matches: [] | None | None |
| R11 | PASS | Forja forbidden matches: [] | None | None |
| R12 | PASS | Cerebro restricted-source matches: [] | None | None |
| R13 | PASS | Delete blocked=True; before=52; after=52 | None | None |
| R14 | PASS | Update blocked=True; modified_rows=0 | None | None |
| R15 | PASS | Severity tamper detectable=True | None | None |
| R16 | PASS | Direct DB read returned 5 audit rows with hashes intact=True | None | None |
| R17 | PASS | Collector main.py moved=True; core start summary={"hardening": {"checks_failed": [], "checks_passed": ["python_version_3_11_or_newer", "no_default_secret_like_environment_values_detected", "log_directory_exists_and_writable", "database_accessible_sqlite", "required_environment_variables_documented_in_code"], "overall_status": "PASS", "recommendations": []}, "modules_health": {"alerts": {"details": "key files present, importable, logs active", "last_log_entry": "{\"alert_id\": \"b2ec4662-be2c-49c | None | None |
| R18 | PASS | Database corruption handled; summary={'error_logged': True, 'error': "DatabaseError('file is not a database')"} | None | None |
| R19 | PASS | Wrong-key statuses=[401, 401, 401, 401, 401, 401, 401, 401, 401, 401]; brute_force_logs=10; status_after=200 | None | None |
| R20 | PASS | level3=True; non_ceo_rejected=True; ceo_deactivated=True | None | None |
| R21 | PASS | poison={'is_poisoned': True, 'confidence': 0.75, 'quarantined': True, 'indicators_triggered': ['perfect_untrusted_critical_claim']}; route_locked=True | None | None |
| R22 | PASS | poison={'is_poisoned': True, 'confidence': 0.7, 'quarantined': True, 'indicators_triggered': ['single_source_low_confidence_critical']} | None | None |
| R23 | PASS | Processed unique packages=10 out of 50; duplicate triage active=True | None | None |
| R24 | PASS | Full external output forbidden matches: [] | None | None |

Summary: 24/24 PASS
