import pytest
from compare_dropshipping_regressions import compare, summarize


def test_inherited_failure_remains_visible():
    result = compare({'a': 'passed', 'b': 'failure'}, {'a': 'passed', 'b': 'failure', 'c': 'passed'})
    assert result['passed'] and result['inherited_failures'] == ['b']


@pytest.mark.parametrize('current', [{'a': 'failure', 'b': 'failure'}, {'b': 'failure'}, {'a': 'passed', 'b': 'skipped'}, {'a': 'passed', 'b': 'error'}, {'a': 'passed', 'b': 'failure', 'c': 'skipped'}])
def test_regression_or_missing_test_blocks(current):
    assert not compare({'a': 'passed', 'b': 'failure'}, current)['passed']


def test_parse_and_duplicate(tmp_path):
    report = tmp_path / 'report.xml'
    report.write_text('<testsuites><testsuite><testcase classname="a" name="b"><failure/></testcase><testcase classname="a" name="c"/></testsuite></testsuites>')
    assert summarize(report) == {'a::b': 'failure', 'a::c': 'passed'}
    report.write_text('<testsuite><testcase classname="a" name="b"/><testcase classname="a" name="b"/></testsuite>')
    with pytest.raises(ValueError):
        summarize(report)
