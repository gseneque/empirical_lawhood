#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Explicit human-directed preparation from one authentic historic OUTCOME.

This prepares a test nomination. It constructs no protein, performs no assay and
submits nothing externally. Import and --help enter no scientific operation.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import traceback

from run_applied_el_broad_programme import SelectedProgramme, add_custody_location_arguments, census, unique_product


def run(programme, args):
    from empirical_lawhood.adapters.methods.rubisco_cycle_constraints.contracts import CycleUseProduct
    from empirical_lawhood.adapters.methods.rubisco_cycle_constraints import recursive_translation as cycle_drafts
    from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry import science as portfolio
    from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.source_manifest import (
        INITIAL_CANDIDATE_IDS, SOURCE_MANIFEST,
    )
    from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import (
        AssayPreparationProposal, NominationDossier, NominationSourceMember,
    )
    from empirical_lawhood.adapters.methods.rubisco_nomination_preparation import science, recursive_translation
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_contributions import authenticate_recursive_contribution
    from empirical_lawhood.api.recursive_execution import read_recursive_wave
    from empirical_lawhood.kernel.decoding import decode_canonical_record

    archive_members = {row['path']: row for row in programme.preflight['members']}
    this_name = 'scripts/run_applied_el_rubisco_nomination.py'
    if archive_members.get(this_name, {}).get('sha256') != sha256(Path(__file__).read_bytes()).hexdigest():
        raise ValueError('nomination launcher differs from its producing archive')
    factory_raw = args.factory.read_bytes()
    if sha256(factory_raw).hexdigest() != args.factory_sha256:
        raise ValueError('selected prospective factory changed before entry')
    factory = json.loads(factory_raw)
    prior_raw = args.prior_report.read_bytes()
    if sha256(prior_raw).hexdigest() != args.prior_report_sha256:
        raise ValueError('historic actual report changed before fork')
    prior = json.loads(prior_raw)
    expected_members = prior['custody_members']

    def retain_history():
        if census(args.prior_root) != expected_members:
            raise ValueError('historic source root differs from its complete actual report census')
        shutil.copytree(args.prior_root, programme.root, dirs_exist_ok=True)
        if census(args.prior_root) != expected_members or census(programme.root) != expected_members:
            raise ValueError('historic custody copy lost original bytes or complete denominator')
        return {'member_count': len(expected_members),
                'bytes': sum(row['bytes'] for row in expected_members.values()),
                'new_operations': 0, 'native_contacts': 0,
                'prior_report_sha256': args.prior_report_sha256,
                'original_registered_operations': prior['actual_registered_operations']}

    programme.report['historical_custody'] = programme.measured('historical-exact-custody-copy', retain_history)
    programme.report['historical_custody']['relocation'] = {
        'original_storage_root_id': programme.plane.root.contract.storage_root_id,
        'selected_canonical_root': str(programme.root),
        'original_relative_paths_and_bytes_preserved': True,
        'new_independent_evidence': False,
    }
    supplier_directory = programme.root / 'cycle-use'
    _, products, _, _ = programme.measured('historical-authentic-wave-read', lambda: read_recursive_wave(
        directory=supplier_directory, artifact_writer=programme.plane, include_products=True))
    outcome = unique_product(products, CycleUseProduct)
    _, historic_draft, _, _ = load_authored_wave(directory=supplier_directory, artifact_writer=programme.plane)
    parent = cycle_drafts.describe_contributions(historic_draft, products)[0]
    contribution = programme.root / 'cycle-use-contribution'
    authenticated = programme.measured('historical-portable-parent-authenticate', lambda:
        authenticate_recursive_contribution(directory=contribution, artifact_writer=programme.plane))[2]
    if authenticated != parent:
        raise ValueError('historic portable parent substitutes actual cycle-use outcome')

    def intake():
        source_root = args.factory.parent / 'retained-originals'
        original_sources = {sid: (source_root / (sid + '--' + name)).read_bytes()
                            for sid, name, _, _ in SOURCE_MANIFEST}
        macro = portfolio.source_audit_from_bytes(original_sources, candidate_ids=INITIAL_CANDIDATE_IDS)
        assay = decode_canonical_record(factory['assay'], AssayPreparationProposal)
        members = tuple(decode_canonical_record(row, NominationSourceMember) for row in factory['source_members'])
        preparation = science.preparation_from_source(macro, outcome,
            proposed_material_id=factory['proposed_material_id'], source_ssu_view=factory['source_ssu_view'],
            source_members=members, assay=assay, conditional_rationale=factory['conditional_rationale'],
            adverse_rationale=factory['adverse_rationale'], decision_provenance=factory['decision_provenance'],
            input_id=factory['input_id'])
        for name, record in (('macro-source.json', macro), ('preparation-source.json', preparation)):
            with (programme.root / name).open('xb') as stream:
                stream.write(record.canonical_bytes())
        with (programme.root / 'selected-factory-original.json').open('xb') as stream:
            stream.write(factory_raw)
        return macro, preparation

    macro, preparation = programme.measured('nomination-prospective-source-intake', intake)
    draft = recursive_translation.preparation_draft(preparation, macro, outcome, parent=parent)
    original_result = prior['waves']['cycle-use']
    decision = programme.decision('nomination-human-fork', supplier_directory, original_result,
        endpoint=outcome.scope,
        question='Prepare the explicitly selected high-risk Gp I95M test nominee from the authentic conditional-cycle outcome; preserve unknown target biology.',
        next_draft=draft, next_manifest=parent, human_choice='use')
    programme.report['human_fork_inquiry'] = original_result['committed_inquiry']
    directory, outputs, result = programme.wave('nomination-preparation', draft, (preparation, macro),
        parent=parent, contribution=contribution, decision=decision,
        supplier_directory=supplier_directory, human_fork=True)
    dossier = unique_product(outputs, NominationDossier)
    science.validate_dossier(dossier, macro, outcome)
    programme.report['nomination_dossier'] = dossier.to_document()
    programme.report['selected_primary_candidate'] = 'gp.i95m'
    programme.report['target_biology'] = 'UNEVALUABLE'
    programme.report['actual_assays'] = 0
    programme.report['external_submission'] = 'NOT_ENTERED'
    programme.decision('nomination-preparation', directory, result, endpoint=dossier.scope,
        question='The selected exploratory test dossier is prepared. Exact material realization, paired biochemical assays and external submission remain unentered.',
        previous=None)
    if programme.report['native_contacts'] != 0:
        raise ValueError('pure nomination unexpectedly contacted a native provider')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-selected-test-nomination', action='store_true')
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--source-preflight', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--factory', type=Path, required=True)
    parser.add_argument('--factory-sha256', required=True)
    parser.add_argument('--prior-root', type=Path, required=True)
    parser.add_argument('--prior-report', type=Path, required=True)
    parser.add_argument('--prior-report-sha256', required=True)
    parser.add_argument('--storage-root-id', required=True,
                        help='authentic original storage identity retained by the explicit whole-custody relocation')
    add_custody_location_arguments(parser)
    args = parser.parse_args()
    if not args.prepare_selected_test_nomination:
        parser.error('scientific entry requires explicit preparation selection')
    if any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.label):
        parser.error('select a fresh lowercase operational label')
    args.domain = 'rubisco-nomination-preparation'
    programme = SelectedProgramme(args)
    try:
        run(programme, args)
        programme.report['status'] = 'SELECTED_TEST_NOMINATION_PACKET_PREPARED'
    except BaseException as error:
        programme.report['status'] = 'RETAINED_ADVERSE_ATTEMPT'
        programme.report['exception'] = {'type': type(error).__name__, 'message': str(error),
                                        'traceback': traceback.format_exc()}
        programme.finish()
        raise
    programme.finish()


if __name__ == '__main__':
    main()
