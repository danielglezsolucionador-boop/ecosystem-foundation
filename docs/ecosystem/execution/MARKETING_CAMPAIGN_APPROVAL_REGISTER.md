# Marketing Campaign Approval Register

Date: 2026-06-10
Block: S4

| ID | Product | Type | Status | ROI | CEO Approval | Launched |
| --- | --- | --- | --- | --- | --- | --- |
| s4_dcft_paid_validation | DCFT | paid | approval_needed | missing | required | false |
| s4_sentinela_paid_validation | SENTINELA | paid | approval_needed | missing | required | false |
| s4_organic_content_support | ecosystem | organic | prepared | not_required_for_prepared_organic | not_required | false |

## Blocked Risk Register

| ID | Risk | Severity | Control |
| --- | --- | --- | --- |
| s4_paid_without_roi | paid_campaign_without_roi | high | requires_ceo_approval=true |
| s4_external_accounts_unknown | external_account_unknown | medium | external_account_connected=false |

## CEO Decision Later

CEO must approve paid spend only after ROI and account ownership are validated.
