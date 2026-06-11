# Marketing Paid Campaign Approval Gate Model

Date: 2026-06-10
Block: S4
Status: approval_gate_prepared

## Purpose

This model blocks paid marketing execution unless CEO approval and ROI evidence exist.

## Approval Rules

- Organic prepared work does not require CEO approval.
- Paid campaigns require CEO approval.
- Campaigns with missing ROI stay blocked.
- External ad accounts must be confirmed before real launch.
- No spending is allowed from this block.

## Gate States

- `status=approval_needed`
- `requires_ceo_approval=true`
- `roi_status=missing`
- `paid_campaign_launched=false`
- `budget_spent=0`
- `external_connection_enabled=false`

## Endpoints

- `GET /api/v1/marketing-approval/status`
- `GET /api/v1/marketing-approval/campaigns`
- `GET /api/v1/marketing-approval/approval-needed`
- `GET /api/v1/marketing-approval/risks`

## Risks

- Paid campaign without ROI.
- External ad account unknown.
- Budget execution without CEO decision.

## Closure Criteria

The gate is complete when paid campaigns remain blocked and the cabina shows what needs CEO approval before money is spent.
