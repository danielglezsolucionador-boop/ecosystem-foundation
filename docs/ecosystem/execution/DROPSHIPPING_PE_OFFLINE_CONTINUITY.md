# Dropshipping PE 001 — continuity register
Mode: offline development. No account creation, trials, purchases, ads, deployment or real orders.
Public repository: no credentials, customer data or private business figures.
Existing authenticated ecommerce-readiness router extended; no new external dependencies.
Routes under /api/v1/ecommerce-readiness/dropshipping-pe:
- GET /status: simulated readiness; external connection and stock unverified.
- POST /financial-scenario: illustrative contribution per delivered order in PEN; target S/15 provisional, excludes fixed costs and income tax.
- POST /order-simulation: stateless lifecycle (confirmation, dispatch, delivery, rejection, cancellation and return). No persistence or actual side effects.
Finance assumes supplier product cost incurred only for delivered orders; add unrecovered product cost to failed_shipping or reserve as applicable. All input VAT treatment subject to accounting approval.
Next: authenticated control center UI, catalog with evidence, provider sandbox adapters, storefront and local checkout simulations, security review. Do not declare live status until authentic stock, cost, logistics, sample, legal review, checkout and owner approval are verified.
External accounts and trials deferred until offline work passes validation. Five-day launch objective conditional on third-party lead times and evidence.
Tests added: service and API tests; full suite must run before merge. No production change authorized.
