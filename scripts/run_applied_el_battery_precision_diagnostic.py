#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Explicit receipt-backed precision question from an actual failed procedure.

Import and --help perform no native entry. The finite component experiment
preserves original negative results and supplies no model/use qualification.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import traceback

from run_applied_el_broad_programme import SelectedProgramme, add_custody_location_arguments, census, unique_product


def run(programme, args):
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import BatteryInquirySupply, scope
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry import recursive_translation as prior_translation
    from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic import contracts, science, recursive_translation
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import read_recursive_wave

    members = {row['path']: row for row in programme.preflight['members']}
    if members.get('scripts/run_applied_el_battery_precision_diagnostic.py', {}).get('sha256') != sha256(Path(__file__).read_bytes()).hexdigest():
        raise ValueError('diagnostic launcher differs from its producing archive')
    raw_report = args.prior_report.read_bytes()
    if sha256(raw_report).hexdigest() != args.prior_report_sha256:
        raise ValueError('actual prior report changed before the new scientific question')
    prior_report = json.loads(raw_report)
    expected = prior_report['custody_members']

    def retain_prior():
        if census(args.prior_root) != expected:
            raise ValueError('prior complete custody differs from its retained report')
        shutil.copytree(args.prior_root, programme.root, dirs_exist_ok=True)
        if census(args.prior_root) != expected or census(programme.root) != expected:
            raise ValueError('prior custody relocation changes original bytes or paths')
        return {'members': len(expected), 'bytes': sum(x['bytes'] for x in expected.values()),
                'original_storage_root_id': programme.plane.root.contract.storage_root_id,
                'selected_canonical_root': str(programme.root), 'original_relative_paths_preserved': True,
                'new_independent_evidence': False, 'new_native_contacts': 0}

    programme.report['historical_custody'] = programme.measured('prior-exact-custody-relocation', retain_prior)
    supplier_directory = programme.root / 'battery-supply'
    _, products, _, _ = programme.measured('actual-prior-negative-procedure-read', lambda:
        read_recursive_wave(directory=supplier_directory, artifact_writer=programme.plane, include_products=True))
    prior = unique_product(products, BatteryInquirySupply)
    source = contracts.DiagnosticSource()
    science.validate_prior(source, prior)
    protocol_path = programme.project / 'programmes/energy/battery-charging/records/battery-dfn-precision-diagnostic-selection.json'
    if sha256(protocol_path.read_bytes()).hexdigest() != source.protocol_sha256:
        raise ValueError('selected prospective precision protocol changed before entry')
    _, prior_draft, _, _ = load_authored_wave(directory=supplier_directory, artifact_writer=programme.plane)
    parents = prior_translation.describe_contributions(prior_draft, products)
    if len(parents) != 1:
        raise ValueError('actual failed procedure has an ambiguous portable parent')
    parent = parents[0]
    draft = recursive_translation.diagnostic_draft(prior, source, parent=parent)
    original_result = prior_report['waves']['battery-supply']
    decision = programme.decision('precision-diagnostic-human-fork', supplier_directory, original_result,
        endpoint=scope(prior.source), question=contracts.QUESTION,
        next_draft=draft, next_manifest=parent, human_choice='use', act_outcomes=('unresolved',))
    programme.report['human_fork_inquiry'] = original_result['committed_inquiry']
    contribution, exported_parent = programme.contribution('prior-negative-procedure-contribution', supplier_directory)
    if exported_parent != parent:
        raise ValueError('export substitutes the procedure parent selected by the committed ACT')
    directory, outputs, result = programme.wave('precision-diagnostic', draft, (source,),
        parent=parent, contribution=contribution, decision=decision,
        supplier_directory=supplier_directory, human_fork=True)
    diagnosis = unique_product(outputs, contracts.DiagnosticResult)
    science.validate_result(diagnosis)
    programme.report['precision_diagnostic'] = diagnosis.to_document()
    programme.report['logical_forecast_count'] = len(diagnosis.traces)
    programme.report['charging_backend_subsolve_calls'] = sum(x.backend_solve_calls for x in diagnosis.traces)
    programme.report['initializer_solver_attempts'] = sum(len(x.initializer_attempts) for x in diagnosis.traces)
    programme.report['numerical_model_or_use_qualification'] = False
    programme.decision('precision-diagnostic', directory, result,
        endpoint=scope(source.original), question='Retain the component diagnosis; full reference qualification and later instance use require a separately assessed numerical procedure.',
        previous=decision)
    if programme.report['native_contacts'] != 1:
        raise ValueError('diagnostic framework contact census differs from its actual singleton operation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-selected-precision-diagnostic', action='store_true')
    parser.add_argument('--project-root', required=True, type=Path)
    parser.add_argument('--source-preflight', required=True, type=Path)
    parser.add_argument('--label', required=True)
    parser.add_argument('--prior-root', required=True, type=Path)
    parser.add_argument('--prior-report', required=True, type=Path)
    parser.add_argument('--prior-report-sha256', required=True)
    parser.add_argument('--storage-root-id', required=True)
    add_custody_location_arguments(parser)
    args = parser.parse_args()
    if not args.run_selected_precision_diagnostic:
        parser.error('native entry requires the explicit finite scientific selection')
    if not args.label or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.label):
        parser.error('select a fresh lowercase operational label')
    args.domain = 'battery-dfn-precision-diagnostic'
    programme = SelectedProgramme(args)
    try:
        run(programme, args)
        programme.report['status'] = 'SELECTED_COMPONENT_PRECISION_DIAGNOSTIC_COMPLETED'
    except BaseException as error:
        programme.report['status'] = 'RETAINED_ADVERSE_ATTEMPT'
        programme.report['exception'] = {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}
        programme.finish()
        raise
    programme.finish()


if __name__ == '__main__':
    main()
