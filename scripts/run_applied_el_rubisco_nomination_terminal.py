#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Finish an already successful nomination operation without repeating science.

The new inquiry records the prepared dossier's scope. Its authenticated admission
retains the earlier human ACT and conditional-cycle OUTCOME lineage. Import and
--help have no effects; this controller never authors or executes a wave.
"""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import traceback

from run_applied_el_broad_programme import SelectedProgramme, add_custody_location_arguments, census, unique_product


def run(programme, args):
    from empirical_lawhood.adapters.methods.rubisco_cycle_constraints.contracts import CycleUseProduct
    from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import NominationDossier
    from empirical_lawhood.adapters.methods.rubisco_nomination_preparation import science
    from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.science import SourceAudit
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import read_recursive_wave
    from empirical_lawhood.api.recursive_inquiry import (
        _read, _validate_human_fork, _validate_intent_draft, read_inquiry_decision,
    )
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.recursive_inquiry import identity
    from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigins
    from empirical_lawhood.runtime.recursive_inquiry import InquirySuccessorAdmission

    this_name = 'scripts/run_applied_el_rubisco_nomination_terminal.py'
    archived = {row['path']: row for row in programme.preflight['members']}
    if archived.get(this_name, {}).get('sha256') != sha256(Path(__file__).read_bytes()).hexdigest():
        raise ValueError('terminal controller differs from its selected source archive')
    prior_raw = args.prior_report.read_bytes()
    if sha256(prior_raw).hexdigest() != args.prior_report_sha256:
        raise ValueError('original adverse controller report changed')
    prior = json.loads(prior_raw)
    prior_cost_raw = args.prior_report.with_name('invocation-cost.json').read_bytes()
    if sha256(prior_cost_raw).hexdigest() != args.prior_cost_sha256:
        raise ValueError('original controller invocation cost changed')
    if (prior['status'] != 'RETAINED_ADVERSE_ATTEMPT'
            or prior.get('exception', {}).get('message') != 'cycle inquiry changes original conditional model endpoint scope'
            or prior['actual_registered_operations'] != 1
            or prior['native_contacts'] != 0):
        raise ValueError('continuation requires the exact completed nomination and retained scope refusal')
    original_wave = prior['waves']['nomination-preparation']
    if original_wave['report']['status'] != 'SUCCEEDED' or len(original_wave['operational_census']) != 1:
        raise ValueError('the prior registered preparation operation did not actually succeed')
    expected = prior['custody_members']

    def retain_history():
        if census(args.prior_root) != expected:
            raise ValueError('original custody differs from its complete retained census')
        shutil.copytree(args.prior_root, programme.root, dirs_exist_ok=True)
        if census(args.prior_root) != expected or census(programme.root) != expected:
            raise ValueError('terminal continuation lost original custody bytes')
        return {'member_count': len(expected), 'bytes': sum(row['bytes'] for row in expected.values()),
                'prior_report_sha256': args.prior_report_sha256,
                'original_storage_root_id': programme.plane.root.contract.storage_root_id,
                'original_relative_paths_and_bytes_preserved': True,
                'new_independent_evidence': False, 'new_registered_operations': 0}

    programme.report['historical_custody'] = programme.measured('historical-exact-custody-copy', retain_history)
    programme.report['completed_prior_nomination_wave'] = original_wave
    programme.report['scientific_producing_source'] = prior['producing_source']
    programme.report['scientific_source_archive'] = prior['source_archive']
    programme.report['scientific_source_archive_sha256'] = prior['source_archive_sha256']
    programme.report['prior_controller_disposition'] = prior['exception']
    programme.report['prior_nomination_controller_attempt'] = {
        'report_path': str(args.prior_report), 'report_sha256': args.prior_report_sha256,
        'cost_sha256': args.prior_cost_sha256, 'cost': json.loads(prior_cost_raw),
        'status': prior['status'], 'exception': prior['exception'],
        'scientific_operation_succeeded': True, 'controller_terminal_commit_succeeded': False,
    }
    programme.report['original_broad_history_summary'] = prior['historical_custody']
    programme.report['prior_completed_nomination_operations'] = 1
    programme.report['new_registered_operations'] = 0
    directory = programme.root / 'nomination-preparation'

    def authenticate_lineage():
        admission = _read(programme.plane, 'nomination-preparation/inquiry-admission.json', InquirySuccessorAdmission)
        packet, records = read_inquiry_decision(directory=programme.root / admission.decision_relative_path,
                                              artifact_writer=programme.plane)
        authored, draft, source, payloads = load_authored_wave(directory=directory, artifact_writer=programme.plane)
        intent = records.get('intent.json')
        if (intent is None or admission.decision_packet != identity(packet, packet.packet_id)
                or admission.intent != identity(intent, intent.intent_id)
                or admission.authored_wave != identity(authored, authored.packet_id)
                or source != records['implementation.json']
                or source.to_document() != prior['producing_source']):
            raise ValueError('actual admission substitutes the persisted ACT, intent, wave or scientific source')
        origins = decode_canonical_bytes(payloads['origins.json'], RecursiveInputOrigins, maximum_bytes=None)
        origins.validate_draft(draft)
        _validate_intent_draft(intent, draft, origins)
        _validate_human_fork(draft=draft, records=records, supplier_directory=programme.root / 'cycle-use',
            contribution_dir=programme.root / 'cycle-use-contribution', origins=origins,
            artifact_writer=programme.plane)
        return {'admission': admission.to_document(), 'act_packet': packet.to_document(),
                'act_decision': records['decision.json'].to_document(), 'intent': intent.to_document(),
                'contribution_parents': [parent.to_document() for parent in draft.contribution_parents],
                'origins': origins.to_document(), 'new_native_contacts': 0, 'scheduler_entered': False}

    programme.report['authenticated_prior_lineage'] = programme.measured('actual-admission-act-parent-authenticate', authenticate_lineage)

    def recover_completed_preparation():
        before = census(programme.root)
        actual_report, products, _, _ = read_recursive_wave(directory=directory, artifact_writer=programme.plane,
                                                          include_products=True)
        actual_document = json.loads(json.dumps(actual_report))
        actual_census_document = json.loads(json.dumps(products['operational_census']))
        if (actual_document != original_wave['report'] or actual_report['status'] != 'SUCCEEDED'
                or actual_census_document != original_wave['operational_census']):
            raise ValueError('actual completed wave differs from its retained report and attempt denominator')
        dossier = unique_product(products, NominationDossier)
        _, historical_products, _, _ = read_recursive_wave(directory=programme.root / 'cycle-use',
            artifact_writer=programme.plane, include_products=True)
        outcome = unique_product(historical_products, CycleUseProduct)
        macro = decode_canonical_bytes((programme.root / 'macro-source.json').read_bytes(), SourceAudit,
                                      maximum_bytes=None)
        science.validate_dossier(dossier, macro, outcome)
        if dossier.to_document() != prior['nomination_dossier'] or census(programme.root) != before:
            raise ValueError('read-only scientific recovery changed the dossier or original custody')
        return dossier

    dossier = programme.measured('completed-scientific-recovery-and-validation', recover_completed_preparation)
    programme.report['nomination_dossier'] = dossier.to_document()
    programme.report['selected_primary_candidate'] = 'gp.i95m'
    programme.report['target_biology'] = 'UNEVALUABLE'
    programme.report['actual_assays'] = 0
    programme.report['external_submission'] = 'NOT_ENTERED'
    programme.report['terminal_state_scope'] = (
        'One actually completed nomination wave; earlier cycle evidence is authenticated through its '
        'admission, ACT and OUTCOME parent, not reprojected as a same-scope predecessor inquiry.')
    programme.report['cost_attribution'] = (
        'The terminal state retains the prior operation measured_invocation once. That historic cost '
        'is not new execution and is not additive to this continuation invocation window.')
    terminal_result = deepcopy(original_wave)
    programme.decision('nomination-preparation-terminal', directory, terminal_result, endpoint=dossier.scope,
        question='The exploratory Gp I95M test nomination dossier is prepared. Material realization, paired biological assays, prize qualification and external submission remain unentered.',
        previous=None)
    programme.report['terminal_inquiry'] = terminal_result['committed_inquiry']
    if programme.report['waves'] or programme.report['native_contacts'] != 0:
        raise ValueError('terminal-only continuation unexpectedly entered a new scientific operation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--complete-selected-nomination-terminal', action='store_true')
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--source-preflight', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--prior-root', type=Path, required=True)
    parser.add_argument('--prior-report', type=Path, required=True)
    parser.add_argument('--prior-report-sha256', required=True)
    parser.add_argument('--prior-cost-sha256', required=True)
    parser.add_argument('--storage-root-id', required=True)
    add_custody_location_arguments(parser)
    args = parser.parse_args()
    if not args.complete_selected_nomination_terminal:
        parser.error('terminal continuation requires explicit selection')
    if any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.label):
        parser.error('select a fresh lowercase operational label')
    args.domain = 'rubisco-nomination-preparation-terminal'
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
