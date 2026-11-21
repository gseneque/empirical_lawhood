# SPDX-License-Identifier: MPL-2.0
"""Prepare an explicit conformance fixture from a retained certificate report.

This command writes only the selected new developer fixture. The separate
bounded runner verifies original custody and assessment without execution.
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.storage.bounded_io import read_bounded_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--operator-profile', type=Path, required=True)
    parser.add_argument('--expected-report', type=Path, required=True)
    parser.add_argument('--output-fixture', type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)
    profile = args.operator_profile.resolve(strict=True)
    original = read_bounded_bytes(args.expected_report, maximum_bytes=128 * 1024)
    expected = json.loads(original)
    if (expected.get('status') != 'VERIFIED_ORIGINAL_ASSESSMENT'
            or not expected.get('certificate_identity') or not expected.get('directory')):
        raise ValueError('select an original complete certificate verification report')
    # The selected identity makes this byte-identity status explicit. Original
    # scientific and authority fields retain their complete expected values.
    expected['byte_identity'] = 'MATCHES_SELECTED_IDENTITY'
    for key in ('independent_unit_ids', 'nested_view_ids', 'original_evidence', 'remaining_requirements'):
        expected[key] = tuple(expected[key])
    text = '''# SPDX-License-Identifier: MPL-2.0
# Explicit retained read; no producer, worker or new scientific calculation.
from dataclasses import replace
from pathlib import Path
import sys
from empirical_lawhood.api.application_context import application_storage
from empirical_lawhood.api.application_contracts import ApplicationContext
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.knowledge_certificates import KnowledgeAssessmentCertificate
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.execution.extension_conformance import ConformanceCall, ConformanceCase, ConformanceProfile, ExtensionConformanceSelection
'''
    text += 'EXPECTED_REPORT_SOURCE_SHA256 = ' + repr(sha256(original).hexdigest()) + '\n'
    text += 'expected = ' + repr(expected) + '\n'
    text += 'project_root = Path(' + repr(str(root)) + ')\n'
    text += 'operator_profile = Path(' + repr(str(profile)) + ')\n'
    text += '''_, _, plane = application_storage(ApplicationContext(context_id='knowledge.conformance',
    label='Original assessment read conformance', python_executable=Path(sys.executable),
    project_root=project_root, operator_profile=operator_profile), for_write=False)
identity = decode_canonical_bytes(canonical_json_bytes(expected['certificate_identity']), ObjectIdentity, maximum_bytes=4096)
arguments = dict(directory=Path(expected['directory']), artifact_writer=plane, expected_certificate=identity)
changed = replace(identity, object_fingerprint=('f' if identity.object_fingerprint != 'f' * 64 else 'e') * 64)
CONFORMANCE_SELECTION = ExtensionConformanceSelection('knowledge', 'empirical-lawhood/knowledge/', (),
    imported_record_types=(KnowledgeAssessmentCertificate,), profile=ConformanceProfile.PORTABLE_CERTIFICATE_READ,
    cases=(ConformanceCase('knowledge.original-assessment', ConformanceCall.CERTIFICATE_READ, arguments, expected),
        ConformanceCase('knowledge.substituted-identity', ConformanceCall.CERTIFICATE_READ,
            {**arguments, 'expected_certificate': changed}, 'ValueError', 'substitutes its exact original record')))
'''
    if len(text.encode()) > 256 * 1024:
        raise ValueError('prepared conformance fixture exceeds the existing byte bound')
    target = args.output_fixture.absolute()
    if target.resolve().is_relative_to(root):
        raise ValueError('select a new external developer fixture path')
    with target.open('x') as stream:
        stream.write(text)
    print(json.dumps({'fixture': str(target), 'fixture_sha256': sha256(text.encode()).hexdigest(),
                      'scientific_authority': 'NONE', 'expected_report_sha256': sha256(original).hexdigest()}))


if __name__ == '__main__':
    main()
