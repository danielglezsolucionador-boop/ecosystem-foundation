"""Cross-module rehearsal, deliberately independent of full app/auth wiring."""
from decimal import Decimal

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dropshipping_storefront import router
from app.services.dropshipping_pe_catalog import catalog
from app.services.dropshipping_pe_evidence import playbook
from app.services.dropshipping_pe_growth import CampaignScenario, evaluate_campaign
from app.services.dropshipping_pe_offline import LaunchEvidence
from app.services.dropshipping_pe_pipeline import PipelineScenario, simulate_pipeline


def test_demo_catalog_is_consistent_with_research():
    app = FastAPI()
    app.include_router(router)
    items = TestClient(app).get('/api/v1/dropshipping-demo/catalog').json()['items']
    finalists = {p['id'] for p in catalog() if p['stage'] == 'quote_candidate'}
    assert {p['id'] for p in items} == finalists
    assert all(not p['approved_for_sale'] for p in items)


def test_checkout_to_settlement_to_growth_is_simulated():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    cart = {'lines': [{'product_id': 'PE-019', 'pack': 1, 'quantity': 1}], 'region': 'lima'}
    checkout = client.post('/api/v1/dropshipping-demo/checkout', json={
        **cart, 'payment': 'contra_entrega_demo', 'acknowledge_demo': True}).json()
    assert checkout['total_cents'] == 10100
    pipeline = simulate_pipeline(PipelineScenario(
        provider='Dropi', cart=cart,
        events=[{'event_id': f'DEMO-{i}', 'code': 'DEMO_DROPI_' + state}
                for i, state in enumerate(('CONFIRMED', 'DISPATCHED', 'DELIVERED'), 1)],
        product_cost_cents=2000, logistics_cost_cents=1500, advertising_cost_cents=1200,
        provider_fee_cents=500, observed_remittance_cents=9600))
    assert pipeline['gross_cod_cents'] == checkout['total_cents']
    assert pipeline['reconciliation'] == 'matched'
    # Illustrative VAT-exclusive sales and variable costs for 10 identical deliveries.
    campaign = evaluate_campaign(CampaignScenario(spend_cents=12000, budget_cap_cents=30000,
        orders=10, delivered_paid=10, failed_or_refunded=0, pending=0,
        net_sales_ex_vat_cents=85590, non_ad_costs_cents=40000))
    assert campaign['decision'] == 'review_scaling_with_ceo'
    assert campaign['ceo_approval_required']
    assert not any(x['live_enabled'] for x in (checkout, pipeline, campaign))
    assert not playbook('ad_campaign')['sent']
    assert not LaunchEvidence().ready_for_live(Decimal('100'))


def test_settlement_discrepancy_is_escalated_not_executed():
    result = playbook('settlement_difference')
    assert result['reviewer'] == 'CEO'
    assert not result['sent'] and not result['llm_called']
