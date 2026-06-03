# Control Center Data Contracts

Estado: `BASE_DEFINED`

## 1. Application Status

```json
{
  "app_id": "string",
  "name": "string",
  "environment": "local|staging|production",
  "health": "ok|degraded|failed|unknown",
  "runtime": "operational|degraded|blocked|unknown",
  "version": "string",
  "commit": "string",
  "updated_at": "ISO-8601"
}
```

## 2. Blocker

```json
{
  "blocker_id": "uuid",
  "app_id": "string",
  "severity": "info|warning|degraded|critical|blocked",
  "description": "string",
  "owner": "string",
  "status": "open|in_progress|resolved",
  "created_at": "ISO-8601"
}
```

## 3. Approval

```json
{
  "approval_id": "uuid",
  "action": "string",
  "risk": "low|medium|high|critical",
  "requested_by": "string",
  "status": "pending|approved|rejected",
  "created_at": "ISO-8601"
}
```

## 4. Rule

Todo dato debe incluir fuente y timestamp en la implementacion futura.

