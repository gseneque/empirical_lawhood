#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Execute an explicitly selected, source-bound RUBISCO in silico question.

The completed nomination is an authenticated OUTCOME parent. Each invocation
retains its exact history and commits a new human-directed ACT before export
and scientific entry. Import and --help perform no computation or construction.
"""
import argparse
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import shutil
import traceback

from run_applied_el_broad_programme import SelectedProgramme, census, unique_product


def archived_bytes(programme, path):
    path = path.resolve(strict=True)
    relative = path.relative_to(programme.project).as_posix()
    raw = path.read_bytes()
    members = {row['path']: row for row in programme.preflight['members']}
    if members.get(relative) != {'path': relative, 'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}:
        raise ValueError('selected source or launcher differs from producing archive: ' + relative)
    return raw


def prior_documents(args):
    raw, cost_raw = args.prior_report.read_bytes(), args.prior_cost.read_bytes()
    if sha256(raw).hexdigest() != args.prior_report_sha256 or sha256(cost_raw).hexdigest() != args.prior_cost_sha256:
        raise ValueError('selected completed nomination report or cost differs')
    report, cost = json.loads(raw), json.loads(cost_raw)
    if (report['status'] != 'SELECTED_TEST_NOMINATION_PACKET_PREPARED'
            or report['domain'] != 'rubisco-nomination-preparation-terminal'
            or report['prior_completed_nomination_operations'] != 1
            or report['new_registered_operations'] != 0 or report['native_contacts'] != 0
            or cost['native_contacts'] != 0 or cost['full_durable_copy_exact'] is not True):
        raise ValueError('entry requires the authentic completed nomination and verified custody')
    expected = report['custody_members']
    if (cost['operational_member_count'] != len(expected)
            or cost['operational_retained_bytes'] != sum(row['bytes'] for row in expected.values())):
        raise ValueError('selected nomination cost belongs to different custody')
    for field in ('cpu_seconds', 'wall_seconds'):
        value, before = cost[field], report['measured_through_pre_copy'][field]
        if (type(value) not in (int, float) or type(before) not in (int, float)
                or not isfinite(value) or not isfinite(before) or before < 0 or value < before):
            raise ValueError('completed nomination cost omits its measured ' + field)
    return report, cost


def retain_history(programme, args, prior):
    expected = prior['custody_members']
    if census(args.prior_root) != expected or census(programme.root):
        raise ValueError('complete original nomination custody or fresh selected root differs')
    shutil.copytree(args.prior_root, programme.root, dirs_exist_ok=True)
    if census(args.prior_root) != expected or census(programme.root) != expected:
        raise ValueError('historical relocation changed original bytes or full denominator')
    return {'member_count': len(expected), 'bytes': sum(row['bytes'] for row in expected.values()),
        'original_storage_root_id': programme.plane.root.contract.storage_root_id,
        'original_relative_paths_preserved': True, 'new_scientific_operations': 0,
        'new_independent_evidence': False, 'new_native_contacts': 0}


def authenticate_nomination(programme, prior):
    from empirical_lawhood.adapters.methods.rubisco_cycle_constraints.contracts import CycleUseProduct
    from empirical_lawhood.adapters.methods.rubisco_nomination_preparation import science, recursive_translation
    from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import NominationDossier
    from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.science import SourceAudit
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import read_recursive_wave
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.provenance import ObjectIdentity

    directory = programme.root / 'nomination-preparation'
    actual_report, products, _, _ = read_recursive_wave(directory=directory, artifact_writer=programme.plane,
        include_products=True, terminal_product_format='references')
    original = prior['completed_prior_nomination_wave']
    if (actual_report['status'] != 'SUCCEEDED' or len(products['operational_census']) != 1
            or json.loads(json.dumps(products['operational_census'])) != original['operational_census']):
        raise ValueError('nomination parent is not the actual successful scientific operation')
    for key in ('run_id', 'packet_sha256', 'draft_sha256', 'execution_plan_sha256', 'producing_code_sha256'):
        if actual_report[key] != original['report'][key]:
            raise ValueError('nomination report substitutes its actual authenticated ' + key)
    identities = {attempt: ObjectIdentity.from_record(receipt.receipt_id, receipt).to_document()
                  for attempt, receipt in products['attempt_receipts'].items()}
    if identities != original['receipt_identities']:
        raise ValueError('nomination report substitutes its actual completion receipt')
    dossier = unique_product(products, NominationDossier)
    if (dossier.fingerprint() != '8121b9e941cbc66d0634dbc9f3047c6e22232fb1a783f2a313a17bf5f63f35fa'
            or dossier.to_document() != prior['nomination_dossier']):
        raise ValueError('nomination parent substitutes the selected prepared candidate')
    _, cycle_products, _, _ = read_recursive_wave(directory=programme.root / 'cycle-use',
        artifact_writer=programme.plane, include_products=True, terminal_product_format='references')
    cycle = unique_product(cycle_products, CycleUseProduct)
    macro = decode_canonical_bytes((programme.root / 'macro-source.json').read_bytes(), SourceAudit,
        maximum_bytes=None)
    science.validate_dossier(dossier, macro, cycle)
    _, draft, _, _ = load_authored_wave(directory=directory, artifact_writer=programme.plane)
    described = recursive_translation.describe_contributions(draft, products)
    if len(described) != 1:
        raise ValueError('nomination has no unique actual OUTCOME contribution')
    return directory, dossier, macro, described[0]


def selected_question(programme, args, dossier, macro, parent):
    """Select installed scientific owners; the controller supplies no analysis."""
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    raw = archived_bytes(programme, args.source_selection)
    if args.check == 'mechanism':
        from empirical_lawhood.adapters.methods.rubisco_insilico_mechanism.contracts import MechanismSource
        from empirical_lawhood.adapters.methods.rubisco_insilico_mechanism import recursive_translation
        source = decode_canonical_bytes(raw, MechanismSource, maximum_bytes=None)
        draft = recursive_translation.challenge_draft(source, macro, dossier, parent=parent)
        records = (source, macro)
    elif args.check == 'structure-inventory':
        from empirical_lawhood.adapters.methods.rubisco_insilico_structure.contracts import StructuralSource
        from empirical_lawhood.adapters.methods.rubisco_insilico_structure import recursive_translation
        source = decode_canonical_bytes(raw, StructuralSource, maximum_bytes=None)
        draft = recursive_translation.source_mapping_draft(source, dossier, parent=parent)
        records = (source,)
    else:
        raise ValueError('selected scientific question has no settled installed owner')
    if source.nomination.object_fingerprint != dossier.fingerprint():
        raise ValueError('selected new question substitutes its actual nomination outcome')
    destination = programme.root / 'insilico-selected-source.json'
    with destination.open('xb') as stream:
        stream.write(raw)
    if destination.read_bytes() != source.canonical_bytes():
        raise ValueError('selected source is not exact canonical input')
    programme.report['scientific_source'] = source.to_document()
    return source, draft, records


def run(programme, args):
    from empirical_lawhood.adapters.methods.rubisco_insilico_mechanism.contracts import MechanismAssessment
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure.contracts import StructuralAssessment
    archived_bytes(programme, Path(__file__))
    prior, cost = prior_documents(args)
    programme.report['prior_nomination'] = {'report_path': str(args.prior_report),
        'report_sha256': args.prior_report_sha256, 'cost_sha256': args.prior_cost_sha256,
        'cost': cost, 'scope_stop_preserved': True, 'prior_operations_not_new_execution': 1}
    programme.report['historical_custody'] = programme.measured('historical-exact-custody-copy',
        lambda: retain_history(programme, args, prior))
    directory, dossier, macro, parent = programme.measured('authenticate-actual-nomination',
        lambda: authenticate_nomination(programme, prior))
    source, draft, records = programme.measured('selected-question-source-intake',
        lambda: selected_question(programme, args, dossier, macro, parent))
    historic_result = prior['completed_prior_nomination_wave'].copy()
    decision = programme.decision('insilico-human-fork', directory, historic_result,
        endpoint=dossier.scope,
        question='Execute the newly selected in silico question from the authentic Gp I95M nomination; retain unknown biology and the historical terminal STOP.',
        next_draft=draft, next_manifest=parent, previous=None, human_choice='use')
    contribution, exported = programme.contribution('insilico-nomination-contribution', directory)
    if exported != parent:
        raise ValueError('exported nomination substitutes the ACT-designated OUTCOME parent')
    actual_directory, products, result = programme.wave('insilico-' + args.check, draft, records,
        parent=parent, contribution=contribution, decision=decision,
        supplier_directory=directory, human_fork=True)
    assessment_type = MechanismAssessment if args.check == 'mechanism' else StructuralAssessment
    assessment = unique_product(products, assessment_type)
    programme.report['assessment'] = assessment.to_document()
    programme.report['target_biology'] = 'UNEVALUABLE'
    programme.report['external_submission'] = 'NOT_ENTERED'
    programme.report['check_completion_scope'] = ('COMPLETE_MECHANISM_QUESTION' if args.check == 'mechanism'
        else 'OBSERVED_STRUCTURE_INVENTORY_SUBSTEP_ONLY_MUTANT_COMPARISON_PENDING')
    programme.decision('insilico-' + args.check + '-terminal', actual_directory, result,
        endpoint=assessment.scope if hasattr(assessment, 'scope') else source_scope(source, args.check),
        question='Retain the actual selected in silico assessment and its negative or unevaluable findings; biology and external submission remain unentered.',
        previous=None)


def source_scope(source, check):
    if check == 'mechanism':
        from empirical_lawhood.adapters.methods.rubisco_insilico_mechanism.contracts import scope
    else:
        from empirical_lawhood.adapters.methods.rubisco_insilico_structure.contracts import scope
    return scope(source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-selected-insilico-question', action='store_true')
    parser.add_argument('--check', choices=('mechanism', 'structure-inventory'), required=True)
    for name in ('project-root', 'source-preflight', 'source-selection', 'prior-root', 'prior-report', 'prior-cost',
                 'working-root', 'logs-root', 'durable-root', 'custody-mount'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('label', 'prior-report-sha256', 'prior-cost-sha256', 'storage-root-id',
                 'custody-filesystem', 'custody-profile'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    if not args.run_selected_insilico_question:
        parser.error('scientific entry requires --run-selected-insilico-question')
    if not args.label or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.label):
        parser.error('select a fresh lowercase operational label')
    args.domain = 'rubisco-insilico-' + args.check
    args.terminal_product_format = 'references'
    programme = SelectedProgramme(args)
    try:
        run(programme, args)
        programme.report['status'] = 'SELECTED_INSILICO_QUESTION_COMPLETED'
    except BaseException as error:
        programme.report['status'] = 'RETAINED_ADVERSE_ATTEMPT'
        programme.report['exception'] = {'type': type(error).__name__, 'message': str(error),
            'traceback': traceback.format_exc()}
        programme.finish()
        raise
    programme.finish()


if __name__ == '__main__':
    main()
