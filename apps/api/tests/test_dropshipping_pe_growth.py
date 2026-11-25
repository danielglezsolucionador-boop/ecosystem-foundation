import pytest
from pydantic import ValidationError
from app.services.dropshipping_pe_growth import CampaignScenario, CreativeChecklist, creative_plan, evaluate_campaign, evaluate_creative


def scenario(**kw):
    return CampaignScenario(**{**dict(spend_cents=12000, budget_cap_cents=30000, orders=15,
        delivered_paid=12, failed_or_refunded=3, pending=0, net_sales_ex_vat_cents=90000,
        non_ad_costs_cents=50000), **kw})


@pytest.mark.parametrize('candidate', ['PE-013','PE-019','PE-023'])
@pytest.mark.parametrize('platform', ['facebook','instagram','tiktok'])
def test_drafts(candidate, platform):
    out = creative_plan(candidate, platform)
    assert len(out['scripts']) == 3 and not out['published']
    assert all(not x['approved_for_publication'] for x in out['scripts'])


def test_unknown_candidate():
    with pytest.raises(ValueError): creative_plan('PE-999','tiktok')


def test_creative_gate():
    out = evaluate_creative(CreativeChecklist())
    assert len(out['blockers']) == 5 and not out['review_ready']
    out = evaluate_creative(CreativeChecklist(**dict.fromkeys(CreativeChecklist.model_fields, True)))
    assert out['review_ready'] and not out['approved_for_publication']


def test_healthy_campaign():
    out = evaluate_campaign(scenario())
    assert out['decision'] == 'review_scaling_with_ceo'
    assert out['cpa_order_pen'] == '8.00' and out['cpa_delivered_pen'] == '10.00'
    assert out['contribution_cents'] == 28000 and out['contribution_per_delivery_pen'] == '23.33'
    assert out['ceo_approval_required'] and not out['spend_executed']


@pytest.mark.parametrize('patch,decision', [({'spend_cents':30000},'pause_budget_cap'),
    ({'pending':3,'failed_or_refunded':0},'wait_for_settlement'),
    ({'min_deliveries':13},'insufficient_sample'),
    ({'non_ad_costs_cents':90000},'pause_loss'),
    ({'non_ad_costs_cents':70000},'revise_campaign')])
def test_decisions(patch, decision):
    assert evaluate_campaign(scenario(**patch))['decision'] == decision


def test_zero_denominators():
    out = evaluate_campaign(scenario(spend_cents=0, orders=0, delivered_paid=0, failed_or_refunded=0, net_sales_ex_vat_cents=0, non_ad_costs_cents=0))
    assert out['net_sales_roas'] is None and out['cpa_delivered_pen'] is None


@pytest.mark.parametrize('patch',[{'orders':14},{'spend_cents':-1},{'spend_cents':True},{'live':True},{'delivered_paid':0,'failed_or_refunded':15}])
def test_reject_inconsistent_input(patch):
    with pytest.raises(ValidationError): scenario(**patch)
