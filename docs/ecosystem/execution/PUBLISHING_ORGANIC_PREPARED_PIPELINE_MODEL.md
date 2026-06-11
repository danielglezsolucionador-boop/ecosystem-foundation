# Publishing Organic Prepared Pipeline Model

Date: 2026-06-10
Block: S3
Status: prepared_local

## Purpose

This model defines how PLUMA, LENTE, MARKETING, MARCA PERSONAL, E-COMMERCE, SNIFF AMAZON and CEREBRO prepare organic content without real publication.

## Rules

- Organic content can be prepared without CEO approval.
- Real publication requires an official connected account.
- Unknown or not connected accounts keep `publication_status="prepared"`.
- Paid campaigns are out of this block.
- No views, reach, leads, sales or conversion numbers are invented.
- External publication is blocked by default.

## Pipeline

1. CEREBRO selects a content objective.
2. PLUMA prepares text, scripts, newsletters or authority content.
3. LENTE prepares visuals, short videos or thumbnails.
4. MARKETING checks the commercial angle.
5. MARCA PERSONAL stays prepared until official accounts are confirmed.
6. CEREBRO reports missing evidence and blocked actions.

## Safe States

- `publication_status=prepared`
- `account_status=unknown`
- `account_status=not_connected`
- `real_publication_enabled=false`
- `external_connection_enabled=false`
- `metrics_invented=false`

## Endpoints

- `GET /api/v1/publishing-prepared/status`
- `GET /api/v1/publishing-prepared/calendar`
- `GET /api/v1/publishing-prepared/content`
- `GET /api/v1/publishing-prepared/blocked`

## Closure Criteria

The block is complete when the cabina can show prepared content, blocked real publication, missing metrics, and the next CEO/account decision without claiming real publication.
