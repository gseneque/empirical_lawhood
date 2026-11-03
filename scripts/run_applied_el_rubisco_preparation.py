#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Prepare the selected full24 molecular roster from two authentic parents.

The nomination is OUTCOME; observed coordinates/inventory are HISTORY. Entry
requires an archived exact selection, complete historical custody and registered
code-owned scientific validation. Import and --help construct no native model.
"""

import argparse
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import shutil
from types import SimpleNamespace
import traceback

from run_applied_el_broad_programme import SelectedProgramme, census, unique_product
from run_applied_el_rubisco_insilico import (
    archived_bytes,
    authenticate_nomination,
    prior_documents as nomination_documents,
)


def structure_documents(args):
    raw, cost_raw = args.prior_report.read_bytes(), args.prior_cost.read_bytes()
    if (sha256(raw).hexdigest() != args.prior_report_sha256
            or sha256(cost_raw).hexdigest() != args.prior_cost_sha256):
        raise ValueError('selected actual structural report/cost changed')
    report, cost = json.loads(raw), json.loads(cost_raw)
    wave = report['waves']['insilico-structure-inventory']
    expected = report['custody_members']
    if (report['status'] != 'RETAINED_ADVERSE_ATTEMPT'
            or report['exception']['message'] != 'aggregate invocation cost cannot identify several attempt costs'
            or report['actual_registered_operations'] != 2 or report['native_contacts'] != 0
            or wave['report']['status'] != 'SUCCEEDED'
            or len(wave['operational_census']) != 2
            or any(row['operational_status'] != 'SUCCEEDED' for row in wave['operational_census'])
            or cost['native_contacts'] != 0 or cost['full_durable_copy_exact'] is not True
            or cost['operational_member_count'] != len(expected)
            or cost['operational_retained_bytes'] != sum(row['bytes'] for row in expected.values())):
        raise ValueError('entry requires actual completed structural science and its retained adverse controller')
    for field in ('cpu_seconds', 'wall_seconds'):
        if (type(cost[field]) not in (int, float) or not isfinite(cost[field])
                or cost[field] < 0 or cost[field] < report['measured_through_pre_copy'][field]):
            raise ValueError('original structural aggregate cost omits measured work')
    return report, cost


def retain_history(programme, args, prior):
    expected = prior['custody_members']
    if census(args.prior_root) != expected or census(programme.root):
        raise ValueError('full original structural custody or fresh preparation root differs')
    shutil.copytree(args.prior_root, programme.root, dirs_exist_ok=True)
    if census(args.prior_root) != expected or census(programme.root) != expected:
        raise ValueError('historical relocation changed original bytes or full denominator')
    return {'member_count': len(expected), 'bytes': sum(row['bytes'] for row in expected.values()),
            'original_relative_paths_and_bytes_preserved': True,
            'new_scientific_operations': 0, 'new_native_contacts': 0,
            'new_independent_evidence': False}


def authenticate_structure(programme, prior):
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure import contracts as c, recursive_translation as rt
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import read_recursive_wave
    from empirical_lawhood.kernel.provenance import ObjectIdentity

    directory = programme.root / 'insilico-structure-inventory'
    original = prior['waves']['insilico-structure-inventory']
    report, products, _, _ = read_recursive_wave(directory=directory, artifact_writer=programme.plane,
        include_products=True, terminal_product_format='references')
    if (json.loads(json.dumps(report)) != original['report']
            or json.loads(json.dumps(products['operational_census'])) != original['operational_census']):
        raise ValueError('structural parent changes actual completed report/attempt census')
    receipts = {attempt: ObjectIdentity.from_record(receipt.receipt_id, receipt).to_document()
                for attempt, receipt in products['attempt_receipts'].items()}
    if receipts != original['receipt_identities']:
        raise ValueError('structural parent changes actual completion receipts')
    inventory = unique_product(products, c.StructuralInventory)
    coordinates = unique_product(products, c.AssemblyCoordinates)
    assessment = unique_product(products, c.StructuralAssessment)
    if assessment.to_document() != prior['assessment']:
        raise ValueError('structural parent changes actual scientific assessment')
    _, draft, _, payloads = load_authored_wave(directory=directory, artifact_writer=programme.plane)
    # Preserve the independent reconstruction guard before any native entry.
    rt.inquiry_evidence_projector(draft, payloads, products)
    described = rt.describe_contributions(draft, products)
    if len(described) != 1:
        raise ValueError('structure has no unique authentic HISTORY contribution')
    return directory, inventory, coordinates, described[0]


def selected_preparation(programme, args, dossier, inventory, coordinates, parents):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as c, recursive_translation as rt, science
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes

    raw = archived_bytes(programme, args.source_selection)
    source = decode_canonical_bytes(raw, c.PreparationSelection, maximum_bytes=None)
    science.validate_source(source, dossier, inventory, coordinates)
    selected_native = programme.root / 'insilico-preparation' / 'native-preparation'
    if source.native_workdir != str(selected_native) or selected_native.exists():
        raise ValueError('native preparation must be fresh inside its portable authored-wave custody')
    draft = rt.preparation_draft(source, dossier, inventory, coordinates,
        nomination_parent=parents[0], structure_parent=parents[1])
    with (programme.root / 'insilico-selected-preparation.json').open('xb') as stream:
        stream.write(raw)
    programme.report['scientific_source'] = source.to_document()
    return source, draft


def run(programme, args):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.contracts import PreparationAssessment

    archived_bytes(programme, Path(__file__))
    archived_bytes(programme, programme.project / 'scripts/run_applied_el_rubisco_insilico.py')
    prior, cost = structure_documents(args)
    nominal_args = SimpleNamespace(prior_report=args.nomination_report, prior_cost=args.nomination_cost,
        prior_report_sha256=args.nomination_report_sha256, prior_cost_sha256=args.nomination_cost_sha256)
    nominal, nominal_cost = nomination_documents(nominal_args)
    programme.report['original_structure_controller'] = {'report_sha256': args.prior_report_sha256,
        'cost_sha256': args.prior_cost_sha256, 'aggregate_cost': cost,
        'status': prior['status'], 'exception': prior['exception'],
        'aggregate_invocation_reallocated': False, 'original_scientific_operations_not_new': 2}
    programme.report['original_nomination_controller'] = {'report_sha256': args.nomination_report_sha256,
        'cost_sha256': args.nomination_cost_sha256, 'aggregate_cost': nominal_cost,
        'original_scientific_operations_not_new': 1, 'historical_stop_preserved': True}
    programme.report['historical_custody'] = programme.measured('historical-exact-custody-copy',
        lambda: retain_history(programme, args, prior))
    history = programme.root / 'preparation-controller-history'
    history.mkdir()
    for name, path in (('structure-report.json', args.prior_report), ('structure-cost.json', args.prior_cost),
                       ('nomination-report.json', args.nomination_report), ('nomination-cost.json', args.nomination_cost)):
        with (history / name).open('xb') as stream:
            stream.write(path.read_bytes())
    nomination_dir, dossier, _, nomination_parent = programme.measured('authenticate-actual-nomination',
        lambda: authenticate_nomination(programme, nominal))
    structure_dir, inventory, coordinates, structure_parent = programme.measured('authenticate-actual-structure',
        lambda: authenticate_structure(programme, prior))
    parents = (nomination_parent, structure_parent)
    source, draft = programme.measured('selected-preparation-source-intake',
        lambda: selected_preparation(programme, args, dossier, inventory, coordinates, parents))
    historical_result = nominal['completed_prior_nomination_wave'].copy()
    decision = programme.decision('insilico-preparation-human-fork', nomination_dir, historical_result,
        endpoint=dossier.scope,
        question='Prepare and independently assess the complete controlled24-model roster from authentic nomination OUTCOME and observed structural HISTORY; retain unknown dynamics and biology.',
        next_draft=draft, next_manifests=parents, previous=None, human_choice='use',
        existing_measured_event_paths=())
    contributions = []
    for name, directory, expected in (('insilico-preparation-nomination-contribution', nomination_dir, nomination_parent),
                                      ('insilico-preparation-structure-contribution', structure_dir, structure_parent)):
        contribution, actual = programme.contribution(name, directory)
        if actual != expected:
            raise ValueError('export changes an ACT-designated authentic parent')
        contributions.append(contribution)
    directory, products, result = programme.wave('insilico-preparation', draft, (source,),
        parents=parents, contributions=tuple(contributions), decision=decision,
        supplier_directory=nomination_dir, human_fork=True)
    assessment = unique_product(products, PreparationAssessment)
    programme.report['assessment'] = assessment.to_document()
    programme.report['check_completion_scope'] = 'ACTUAL_MODEL_PREPARATION_SUBSTEP_DYNAMICS_PENDING'
    programme.report['target_biology'] = 'UNEVALUABLE'
    programme.report['external_submission'] = 'NOT_ENTERED'
    programme.decision('insilico-preparation-terminal', directory, result, endpoint=dossier.scope,
        question='Retain the actual complete24-model preparation dispositions, all assigned parameter/atom origin records and adverse outcomes; dynamics, reactive sampling and biology remain unentered.',
        previous=None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-selected-preparation', action='store_true')
    for name in ('project-root', 'source-preflight', 'source-selection', 'prior-root', 'prior-report', 'prior-cost',
                 'nomination-report', 'nomination-cost', 'working-root', 'logs-root', 'durable-root', 'custody-mount'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('label', 'prior-report-sha256', 'prior-cost-sha256', 'nomination-report-sha256',
                 'nomination-cost-sha256', 'storage-root-id', 'custody-filesystem', 'custody-profile'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    if not args.run_selected_preparation:
        parser.error('scientific entry requires --run-selected-preparation')
    if not args.label or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.label):
        parser.error('select a fresh lowercase operational label')
    args.domain = 'rubisco-insilico-model-preparation'
    args.terminal_product_format = 'references'
    programme = SelectedProgramme(args)
    try:
        run(programme, args)
        programme.report['status'] = 'SELECTED_MODEL_PREPARATION_COMPLETED'
    except BaseException as error:
        programme.report['status'] = 'RETAINED_ADVERSE_ATTEMPT'
        programme.report['exception'] = {'type': type(error).__name__, 'message': str(error),
            'traceback': traceback.format_exc()}
        programme.finish()
        raise
    programme.finish()


if __name__ == '__main__':
    main()
