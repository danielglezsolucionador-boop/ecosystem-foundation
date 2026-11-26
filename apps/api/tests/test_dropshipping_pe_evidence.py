import sqlite3
import pytest
from app.services.dropshipping_pe_evidence import EvidenceStore, playbook, PLAYBOOKS

@pytest.fixture
def store(tmp_path):
    db = sqlite3.connect(tmp_path / 'demo.db')
    db.row_factory = sqlite3.Row
    s = EvidenceStore(db)
    s.initialize()
    yield s
    db.close()


def submit(s, **kw):
    args = dict(candidate='PE-019', provider='Dropi', kind='stock', reference='DEMO-1', actor='operator-1', role='OPERATOR')
    return s.submit(**{**args, **kw})


def test_persistence_and_review(store):
    eid = submit(store)
    store.review(eid, 'accepted_demo', 'ceo-1', 'CEO')
    store.db.commit()
    path = store.db.execute('PRAGMA database_list').fetchone()[2]
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        out = EvidenceStore(db).snapshot()
        assert out['items'][0]['decision'] == 'accepted_demo'
        assert out['items'][0]['reviewed_by'] == 'ceo-1'
        assert not out['approved_for_sale'] and not out['real_evidence_verified']


def test_duplicate_and_immutable_review(store):
    eid = submit(store)
    with pytest.raises(ValueError): submit(store)
    store.review(eid, 'rejected_demo', 'ceo-1', 'CEO')
    with pytest.raises(ValueError): store.review(eid, 'accepted_demo', 'ceo-1', 'CEO')


def test_role_gate(store):
    with pytest.raises(PermissionError): submit(store, role='AUDITOR')
    eid = submit(store)
    with pytest.raises(PermissionError): store.review(eid, 'accepted_demo', 'operator-1', 'OPERATOR')


@pytest.mark.parametrize('patch', [{'candidate':'PE-031'}, {'provider':'Other'}, {'kind':'live'}, {'reference':'secret-token'}])
def test_invalid_evidence(store, patch):
    with pytest.raises(ValueError): submit(store, **patch)


@pytest.mark.parametrize('intent', list(PLAYBOOKS))
def test_playbook_no_effect(intent):
    out = playbook(intent)
    assert not out['sent'] and not out['live_enabled'] and not out['llm_called']
    assert out['reviewer'] in {'operator', 'CEO'}
