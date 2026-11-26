"""Compare complete pytest JUnit reports without hiding inherited failures."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def summarize(report):
    root = ET.parse(report).getroot()
    rows = {}
    for case in root.iter('testcase'):
        key = case.attrib['classname'] + '::' + case.attrib['name']
        if key in rows:
            raise ValueError('Duplicate test ID: ' + key)
        rows[key] = next((state for state in ('error', 'failure', 'skipped')
                          if case.find(state) is not None), 'passed')
    if not rows:
        raise ValueError('Empty report')
    return rows


def compare(baseline, current):
    if not baseline or not current:
        raise ValueError('Empty test inventory')
    absent = sorted(baseline.keys() - current.keys())
    inherited = sorted(k for k, v in current.items()
                       if v == 'failure' and baseline.get(k) == 'failure')
    regressions = sorted(k for k, v in current.items()
                         if v != 'passed' and k not in inherited
                         and not (v == 'skipped' and baseline.get(k) == 'skipped'))
    return {'baseline_count': len(baseline), 'current_count': len(current),
            'missing_tests': absent, 'new_nonpasses': regressions,
            'inherited_failures': inherited, 'passed': not absent and not regressions}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    extract = sub.add_parser('extract')
    extract.add_argument('xml', type=Path)
    extract.add_argument('output', type=Path)
    check = sub.add_parser('compare')
    check.add_argument('baseline', type=Path)
    check.add_argument('current', type=Path)
    args = parser.parse_args()
    if args.command == 'extract':
        args.output.write_text(json.dumps(summarize(args.xml), indent=2), encoding='utf-8')
        return 0
    result = compare(json.loads(args.baseline.read_text()), json.loads(args.current.read_text()))
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
