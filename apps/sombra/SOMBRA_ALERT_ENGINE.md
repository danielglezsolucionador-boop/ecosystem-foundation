# SOMBRA :: ALERT ENGINE SYSTEM :: BLOCK T7

CLASSIFICATION: THREAT TRANSMISSION UNIT
VERSION: 1.0 DOCUMENTARY SAFE
CLEARANCE: CEREBRO / CEO ONLY
OVERRIDE: NOT PERMITTED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Alert Doctrine

An alert that cries wolf is worse than no alert at all.

Every SOMBRA alert must answer four questions:

- What is the threat?
- Who is at risk?
- When does it materialize?
- What must be done right now?

If these four questions cannot be answered, the alert is not ready. It remains under analysis until it can be classified, supported, routed, and paired with a recommended action.

No noise.
No vague guidance.
No customer-facing SOMBRA attribution.
Signal only.

This file is documentation only. It does not implement alert engines, dataclasses, AI prompts, queues, automation, APIs, notifications, or runtime behavior.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Section T7.1 — Alert Classification System

Alert severity is driven by score, time window, confidence, client impact, and action urgency.

### Critical

Score reference: 75+.

Time window: 0-2 hours.

Transmission rule:

- Immediate CEREBRO route.
- SENTINELA defensive route when client defense is required.
- CEO awareness only through CEREBRO unless emergency rules apply.
- FORJA route when a defensive capability must be built or updated.

Example categories:

- Active credential exposure affecting an ecosystem client.
- Active ransomware targeting client sector or client asset.
- Weaponized exploit with client exposure.
- Executive exposure with active abuse risk.
- Active attack campaign.

### High

Score reference: 50+.

Time window: 2-24 hours.

Transmission rule:

- Urgent CEREBRO route.
- SENTINELA defensive route when client defense is required.
- FORJA route when build/update is required.

Example categories:

- New exploit circulating with credible risk.
- Client domain appearing in threat discussion.
- Inactive but confirmed credential exposure.
- Phishing campaign being assembled.
- Lookalike domain registration.

### Medium

Score reference: 25+.

Time window: 24-72 hours.

Transmission rule:

- Standard CEREBRO route.
- SENTINELA route when defensive tracking is required.

Example categories:

- New CVE affecting client technology stack.
- Sector threat trend emerging.
- Suspicious domain registration.
- Threat actor method change.

### Low

Score reference: 10+.

Time window: 72+ hours.

Transmission rule:

- Daily or batched CEREBRO intelligence summary.

Example categories:

- General threat landscape shift.
- Emerging attack technique.
- Sector discussion increase.
- Historical pattern recurrence.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Section T7.2 — Alert Package Structure

Every future alert must follow a consistent structure.

Required fields:

- `alert_id`: immutable unique reference.
- `timestamp_utc`: UTC timestamp.
- `mission_id`: originating mission or proactive detection reference.
- `order_origin`: proactive / CEO / CEREBRO.
- `severity`: CRITICAL / HIGH / MEDIUM / LOW.
- `threat_score`: 0-100 score.
- `confidence_level`: confidence score.
- `threat_type`: classifier category.
- `target_client`: specific client or ecosystem-wide.
- `target_assets`: affected domains, emails, systems, executives, or assets within authorized scope.
- `blast_radius`: single client / multi-client / sector-wide / ecosystem-wide.
- `findings`: sanitized intelligence content.
- `evidence_summary`: what was detected, without exposing classified source details.
- `time_window`: relevance or materialization window.
- `historical_context`: pattern history and prior impact.
- `recommended_action`: exact action, owner, and deadline.
- `route_to`: SENTINELA / FORJA / CEREBRO / CEO.
- `forja_construction_needed`: yes/no.
- `forja_specification`: defensive capability summary when needed.
- `source`: always classified for restricted origin.
- `sombra_version`: active version reference.
- `integrity_reference`: hash or future integrity proof.
- `audit_logged`: true in any future implementation.

Forbidden:

- Raw classified source details.
- Customer-facing SOMBRA attribution.
- Unverified critical claims.
- Alerts without recommended action.
- Alerts without confidence/data basis.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Section T7.3 — Alert Generation Requirements

Alert generation is conceptual only.

Future generation must:

- Consume only classified and validated intelligence.
- Include prediction output when available.
- Include historical context.
- Sanitize source details before SENTINELA/client routes.
- Define exact owner and deadline.
- Identify whether FORJA construction is required.
- Log the full generation event.

Recommended action quality bar:

- Specific.
- Assigned.
- Time-bound.
- Evidence-backed.
- No vague language.
- No unsupported speculation.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Section T7.4 — Proactive Alert Protocol

SOMBRA does not wait for orders when a critical or high-severity threat is detected within authorized monitoring scope.

Proactive transmission can be triggered by:

- Score threshold crossing.
- Active client-impacting credential exposure.
- Active attack campaign.
- Weaponized exploit affecting client scope.
- Executive exposure with active risk.
- Client risk score spike.

Proactive route:

1. Generate validated alert.
2. Route to CEREBRO.
3. Route defensive summary to SENTINELA when applicable.
4. Route construction signal to FORJA when required.
5. Audit the event.
6. Write memory update.

Rules:

- No public/customer-facing source exposure.
- No direct customer report from SOMBRA.
- CEO awareness goes through CEREBRO unless emergency doctrine applies.
- Legal review blockers override proactive routing.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Section T7.5 — Daily Intelligence Briefing

SOMBRA may prepare a daily intelligence briefing for CEREBRO.

CEREBRO is responsible for translating any CEO-facing report.

Briefing sections:

- Executive summary for CEREBRO.
- Threat landscape update.
- Client status matrix.
- Active critical/high threats.
- Predictions for the next 7 days.
- FORJA recommendations.
- Operational status summary without sensitive method details.

Rules:

- No client-facing SOMBRA attribution.
- No sensitive source details.
- No operational identity details.
- No customer report directly from SOMBRA.
- CEREBRO owns CEO language.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[END BLOCK T7 — DOCUMENTARY SAFE VERSION]

## Cross-References

- `SOMBRA_SYSTEM.md`
- `SOMBRA_ARCHITECTURE.md`
- `SOMBRA_COMMUNICATION_SYSTEM.md`
- `SOMBRA_MEMORY.md`
- `SOMBRA_RULES.md`
- `SOMBRA_SOURCES.md`
- `heart/03_COMMUNICATION_PROTOCOL.md`
- `heart/04_MEMORY_AND_LEARNING.md`
- `heart/05_CODE_OF_CONDUCT.md`
- `heart/06_RESILIENCE_AND_INTEGRITY.md`
