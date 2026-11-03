#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Explicit full-roster qualification and two receipt-ordered later uses.

The numerical selection must already be frozen in the selected source archive.
Import and --help do not select numerics, import PyBaMM or enter science.
"""
import argparse
from hashlib import sha256
from importlib.metadata import distribution
import json
from math import isfinite
from pathlib import Path
import shutil
import traceback

from run_applied_el_broad_programme import SelectedProgramme, add_custody_location_arguments, census, unique_product, write_json


def archived_bytes(programme, path):
    path = path.resolve(strict=True)
    relative = path.relative_to(programme.project).as_posix()
    members = {row['path']: row for row in programme.preflight['members']}
    raw = path.read_bytes()
    if members.get(relative) != {'path': relative, 'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}:
        raise ValueError('selected input or launcher differs from complete producing archive: ' + relative)
    return raw


def prior_documents(args):
    raw = args.prior_report.read_bytes()
    if sha256(raw).hexdigest() != args.prior_report_sha256:
        raise ValueError('actual diagnostic report differs from selected digest')
    report = json.loads(raw)
    raw_cost = args.prior_cost.read_bytes()
    if sha256(raw_cost).hexdigest() != args.prior_cost_sha256:
        raise ValueError('actual diagnostic invocation cost differs from selected digest')
    cost = json.loads(raw_cost)
    required_status = 'RETAINED_ADVERSE_ATTEMPT' if getattr(args,'prior_history_kind','diagnostic-result') == 'operational-obstruction' else 'SELECTED_COMPONENT_PRECISION_DIAGNOSTIC_COMPLETED'
    if (report['status'] != required_status
            or report['domain'] != 'battery-dfn-precision-diagnostic'
            or cost['full_durable_copy_exact'] is not True):
        raise ValueError('refined entry requires a completed actual diagnostic and exact durable custody')
    expected = report['custody_members']
    if (cost['operational_member_count'] != len(expected)
            or cost['operational_retained_bytes'] != sum(row['bytes'] for row in expected.values())
            or cost['native_contacts'] != report['native_contacts']):
        raise ValueError('selected diagnostic cost belongs to a different custody or native invocation')
    for field in ('cpu_seconds', 'wall_seconds'):
        value, before_copy = cost[field], report['measured_through_pre_copy'][field]
        if (type(value) not in (int, float) or type(before_copy) not in (int, float)
                or not isfinite(value) or not isfinite(before_copy) or before_copy < 0 or value < before_copy):
            raise ValueError('diagnostic cost must retain finite nonnegative complete measured ' + field)
    return report, cost


def retain_prior(programme, args, report):
    expected = report['custody_members']
    if census(args.prior_root) != expected or census(programme.root):
        raise ValueError('prior complete custody or fresh selected root differs before relocation')
    shutil.copytree(args.prior_root, programme.root, dirs_exist_ok=True)
    if census(args.prior_root) != expected or census(programme.root) != expected:
        raise ValueError('diagnostic custody relocation changes original bytes or paths')
    return {'members': len(expected), 'bytes': sum(row['bytes'] for row in expected.values()),
        'original_storage_root_id': programme.plane.root.contract.storage_root_id,
        'selected_canonical_root': str(programme.root), 'original_relative_paths_preserved': True,
        'new_independent_evidence': False, 'new_native_contacts': 0}


def validate_prior_census(report, cost, actual_report, products, plan, plane):
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    previous = report['waves']['precision-diagnostic']
    expected = report['custody_members']
    if (report['native_contacts'] != 1 or cost['native_contacts'] != 1
            or cost['operational_member_count'] != len(expected)
            or cost['operational_retained_bytes'] != sum(row['bytes'] for row in expected.values())
            or len(plan.tasks) != 1 or len(products['receipts']) != 1
            or len(products['operational_census']) != 1
            or products['operational_census'][0]['operational_status'] != 'SUCCEEDED'
            or json.loads(json.dumps(products['operational_census'])) != previous['operational_census']):
        raise ValueError('diagnostic report/cost differs from actual successful operation or complete custody census')
    for key in ('run_id', 'status', 'packet_sha256', 'draft_sha256', 'execution_plan_sha256', 'producing_code_sha256'):
        if actual_report[key] != previous['report'][key]:
            raise ValueError('diagnostic report substitutes actual authenticated wave: ' + key)
    task = plan.tasks[0]
    receipt = products['receipts'][task.task_id]
    store = ExternalNativeEffectContactStore(plane=plane,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    contact = store.read(actual_report['run_id'], task.task_id)
    if (contact is None or contact.execution_task != ObjectIdentity.from_record(task.task_id, task)
            or contact.attempt_id != receipt.attempt_id or contact.run_id != receipt.run_id
            or contact.input_materialization_ids != receipt.input_materialization_ids):
        raise ValueError('diagnostic actual native contact does not join its plan, attempt and completion receipt')
    identities = {attempt: ObjectIdentity.from_record(value.receipt_id, value).to_document()
                  for attempt, value in products['attempt_receipts'].items()}
    if identities != previous['receipt_identities']:
        raise ValueError('diagnostic report substitutes actual retained attempt receipt identities')


def source_intake(programme, source, selection_path, diagnostic):
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import SOURCE_VERSION
    target = programme.root / 'refined-source-originals'
    target.mkdir()
    retained = []

    def retain(path, name, digest):
        if path.is_symlink() or not path.is_file():
            raise ValueError('selected source is missing or linked: ' + str(path))
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != digest:
            raise ValueError('selected original source bytes differ: ' + name)
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(raw)
        if destination.read_bytes() != raw:
            raise ValueError('retained source copy differs: ' + name)
        retained.append({'path': name, 'bytes': len(raw), 'sha256': digest, 'original_path': str(path)})

    retain(selection_path, 'numerical-selection.json', source.protocol_sha256)
    for name, digest in (('battery-thermal-inquiry-selection.json', source.original.protocol_sha256),
                         ('battery-dfn-precision-diagnostic-selection.json', diagnostic.source.diagnostic_source.protocol_sha256 if hasattr(diagnostic.source,'diagnostic_source') else diagnostic.source.protocol_sha256)):
        path = programme.project / 'programmes/energy/battery-charging/records' / name
        archived_bytes(programme, path)
        retain(path, name, digest)
    retain(programme.root / 'battery-source-originals/m50-original.pdf',
           'm50-original.pdf', source.original.manufacturer_document_sha256)
    installed = distribution('pybamm')
    if installed.version != SOURCE_VERSION:
        raise ValueError('installed native source version differs before any import')
    native_root = Path(installed.locate_file('pybamm')).resolve(strict=True)
    for name, digest in source.source_members:
        retain(native_root / name, 'pybamm/' + name, digest)
    register = {'members': retained, 'source_sha256': source.fingerprint(),
        'installed_native_source_members': len(source.source_members), 'native_imports_or_contacts': 0,
        'manufacturer_current_oem_approval': False}
    write_json(target / 'source-intake-register.json', register)
    return register


def current_traces(products, source, phase):
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c
    rows = {}
    for outputs in products['records'].values():
        for record in outputs.values():
            if type(record) is c.Trace and record.config.phase == phase and record.config.source == source:
                previous = rows.setdefault(record.trace_id, record)
                if previous != record:
                    raise ValueError('one trace identity exposes conflicting current bytes')
    return tuple(rows[key] for key in sorted(rows))


def assessed_product(products, phase):
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c
    records = [record for outputs in products['records'].values() for record in outputs.values()
               if type(record) is c.AssessedInstance and record.assessment.instance.phase == phase]
    if len(records) != 1:
        raise ValueError('actual current phase has no unique assessed instance')
    return records[0]


def retain_current_summary(programme, products, source, phase):
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c
    from empirical_lawhood.adapters.methods.battery_refined_inquiry.recipient_bindings import ComparatorAssessment
    traces = current_traces(products, source, phase)
    counts = programme.report.setdefault('current_native_ledgers', {})
    counts[phase] = {'returned_trace_ledger_rows': len(traces),
        'charging_forecast_provider_attempts': sum(row.native_provider_attempts for row in traces),
        'charging_solve_step_subcalls': sum(row.backend_solve_calls for row in traces),
        'charging_scope': 'MAIN_CHARGING_SUBSOLVES_ONLY',
        'initial_soc_soh_solve_calls': sum(len(row.initializer_attempts) for row in traces),
        'initializer_scope': 'INITIAL_SOC_SOH_SOLVE_CALLS',
        'native_tier_transitions': sum(len(row.transitions) for row in traces),
        'cpu_seconds': str(sum((row.cpu_seconds for row in traces), c.D(0))),
        'wall_seconds': str(sum((row.wall_seconds for row in traces), c.D(0))),
        'charging_and_initializer_expenses_are_nonadditive_subwindows': True,
        'historical_relay_rows_excluded': True}
    comparators = [record for outputs in products['records'].values() for record in outputs.values()
                   if type(record) is ComparatorAssessment]
    if comparators:
        programme.report.setdefault('actual_comparator_assessments', {})[phase] = {
            row.choice.arm_id: row.to_document() for row in comparators}


def contact_paths(root):
    return {path.relative_to(root).as_posix() for path in root.glob('runs/*/native-contacts/*.json')
            if not path.name.endswith('.manifest.json')}


def reconcile_contacts(programme, inherited):
    """Retain actual new entry even when a worker returns no scientific ledger."""
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.native_effects import NativeEffectContact
    contacts = []
    for relative in sorted(contact_paths(programme.root) - inherited):
        raw = programme.plane.root.resolve(relative, for_write=False).read_bytes()
        contact = decode_canonical_bytes(raw, NativeEffectContact, maximum_bytes=None)
        store = ExternalNativeEffectContactStore(plane=programme.plane, execution_plan=contact.execution_plan,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
        if store.read(contact.run_id, contact.task_id) != contact:
            raise ValueError('new native entry marker differs from guarded custody')
        contacts.append(contact.to_document())
    programme.report['new_native_contact_markers'] = contacts
    programme.report['native_contacts'] = len(contacts)


def obstruction_history_intake(programme,args,prior_report,prior_cost,actual_report,products,prior_draft,plan):
    """Read the failed original once; a fresh PURE operation assesses its history.

    This never submits the obstructed native wave to the scheduler. Original
    absent forecast/subcall completion remains unknown after successful intake.
    """
    from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction import contracts as oc,science as os,recursive_translation as ot
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry import contracts as bc,recursive_translation as original_translation
    from empirical_lawhood.api.recursive_execution import read_recursive_wave
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
    source=decode_canonical_bytes(archived_bytes(programme,args.obstruction_source),oc.ObstructionSource,maximum_bytes=None)
    os.validate_source(source)
    previous=prior_report['waves']['precision-diagnostic']
    expected=prior_report['custody_members']
    actual_source_census={row.relative_path:{'bytes':row.size_bytes,'sha256':row.sha256} for row in source.complete_custody}
    if (source.invocation_report_sha256 != args.prior_report_sha256 or sha256(source.invocation_cost_raw_utf8.encode()).hexdigest()!=args.prior_cost_sha256
            or actual_source_census!=expected or actual_report['status']!='BLOCKED' or products['receipts'] or products['records']
            or len(plan.tasks)!=1 or len(products['operational_census'])!=1
            or json.loads(json.dumps(products['operational_census'])) != previous['operational_census']):
        raise ValueError('adverse history intake substitutes final original report/cost/full census or invents completed scientific products')
    for key in ('run_id','status','packet_sha256','draft_sha256','execution_plan_sha256','producing_code_sha256'):
        if actual_report[key]!=previous['report'][key]:raise ValueError('adverse history substitutes actual guarded wave: '+key)
    source_records=os.validate_source(source)
    if source_records['plan']!=plan or source_records['index'].run_id!=actual_report['run_id']:
        raise ValueError('adverse source plan/run differs from the authenticated failed wave')
    for row in source.records:
        if (programme.plane.root.resolve(row.relative_path,for_write=False).read_bytes()!=row.raw_utf8.encode()
                or programme.plane.root.resolve(row.relative_path+'.manifest.json',for_write=False).read_bytes()!=row.manifest_raw_utf8.encode()):
            raise ValueError('archived obstruction source substitutes actual original record/manifest bytes')
    for manifest in source.input_manifests:programme.plane.verify_manifest(manifest)
    supplier_directory=programme.root/'battery-supply'
    prior_wave,prior_products,supplier_draft,_=read_recursive_wave(directory=supplier_directory,artifact_writer=programme.plane,include_products=True,terminal_product_format='references')
    supplier=unique_product(prior_products,bc.BatteryInquirySupply)
    if supplier.disposition is not A.UNEVALUABLE or oc.identity(supplier)!=source.prior_supply:
        raise ValueError('obstruction changes authentic original negative numerical procedure')
    parents=original_translation.describe_contributions(supplier_draft,prior_products)
    if len(parents)!=1:raise ValueError('original negative supply has an ambiguous authentic MODEL contribution')
    parent=parents[0]
    draft=ot.obstruction_draft(source,supplier,parent=parent)
    # The diagnostic invocation report describes only its own wave. Original
    # supply and its exact measured event are authenticated relocated custody,
    # not a missing entry in that later invocation's presentation report.
    original_result={'report':prior_wave,'operational_census':prior_products['operational_census']}
    original_cost_path='battery-supply-measured-attempt/measured-attempt-cost.json'
    if original_cost_path not in expected:
        raise ValueError('adverse custody omits original supply measured event')
    decision=programme.decision('obstruction-history-human-fork',supplier_directory,original_result,endpoint=supplier.scope,
        question=oc.QUESTION,next_draft=draft,next_manifest=parent,previous=None,human_choice='use',act_outcomes=('unresolved',),
        existing_measured_event_paths=(original_cost_path,))
    contribution,authenticated=programme.contribution('original-negative-obstruction-parent',supplier_directory)
    if authenticated!=parent:raise ValueError('obstruction export differs from persisted human ACT')
    directory,history_products,result=programme.wave('obstruction-history',draft,(source,),parent=parent,contribution=contribution,
        decision=decision,supplier_directory=supplier_directory,human_fork=True)
    history=unique_product(history_products,oc.ObstructionAssessment)
    os.validate_assessment(history)
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    _,history_draft,_,_=load_authored_wave(directory=directory,artifact_writer=programme.plane)
    programme.report['authentic_adverse_diagnostic_history']={'source_sha256':source.fingerprint(),
        'history':history.to_document(),'actual_new_registered_pure_operations':1,'new_native_contacts':0,
        'prior_diagnostic_native_operations':1,'prior_selected_forecast_roster':12,'prior_forecast_completions':None,
        'prior_charging_subcalls':None,'prior_initial_soc_soh_subcalls':None,'returned_prior_trace_rows':0,
        'original_native_wave_reentered':False,'numerical_adequacy':'NOT_ASSESSED'}
    return directory,history_products,history_draft,history,result


def run(programme, args):
    from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic import contracts as dc, science as ds
    from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic import recursive_translation as prior_translation
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import scope as original_scope
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, science, recursive_translation as drafts
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import read_recursive_wave
    from empirical_lawhood.api.recursive_inquiry import preview_inquiry_successor
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A

    archived_bytes(programme, Path(__file__))
    selection_bytes = archived_bytes(programme, args.numerical_selection)
    selection = decode_canonical_bytes(selection_bytes, c.NumericalSelection, maximum_bytes=None)
    prior_report, prior_cost = prior_documents(args)
    programme.report['historical_diagnostic_invocation'] = {'report_sha256': args.prior_report_sha256,
        'cost_sha256': args.prior_cost_sha256, 'cost': prior_cost, 'nonadditive_with_current_invocation': True,
        'new_independent_evidence': False}
    programme.report['inherited_native_marker_paths'] = sorted(relative for relative in prior_report['custody_members']
        if relative.startswith('runs/') and '/native-contacts/' in relative and relative.endswith('.json')
        and not relative.endswith('.manifest.json'))
    programme.report['historical_custody'] = programme.measured('prior-exact-custody-relocation', lambda:
        retain_prior(programme, args, prior_report))
    inherited = contact_paths(programme.root)
    programme.report['inherited_native_marker_paths'] = sorted(inherited)
    directory = programme.root / 'precision-diagnostic'
    actual_report, products, prior_draft, plan = programme.measured('actual-diagnostic-read', lambda: read_recursive_wave(
        directory=directory, artifact_writer=programme.plane, include_products=True, terminal_product_format='references'))
    if getattr(args,'prior_history_kind','diagnostic-result') == 'operational-obstruction':
        directory,products,prior_draft,diagnostic,original_result = programme.measured('actual-obstruction-history-intake',lambda:
            obstruction_history_intake(programme,args,prior_report,prior_cost,actual_report,products,prior_draft,plan))
        from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction import recursive_translation as prior_translation
    else:
        programme.measured('actual-diagnostic-census-join', lambda:
            validate_prior_census(prior_report, prior_cost, actual_report, products, plan, programme.plane))
        diagnostic = unique_product(products, dc.DiagnosticResult)
        ds.validate_result(diagnostic)
        original_result = prior_report['waves']['precision-diagnostic']
    if selection.diagnostic != c.identity(diagnostic):
        raise ValueError('archived numerical selection substitutes the actual diagnostic')
    policy = c.NumericalPolicy(selection.policy_id, selection.diagnostic, selection.fingerprint(), selection.views,
        selection.development_preparations, selection.later_preparations, selection.tolerance_probe)
    source = c.RefinedSource(args.source_id, diagnostic.source.original, c.identity(policy), c.identity(diagnostic),
        selection.fingerprint(), tuple(sorted((*c.SOURCE_MEMBERS, *c.ADDITIONAL_SOURCE_MEMBERS))))
    if source.source_id == source.original.source_id:
        raise ValueError('refined source requires a distinct explicit new source identity')
    science.validate_source_policy(source, policy, diagnostic=diagnostic, protocol_bytes=selection_bytes)
    programme.report['refined_source_intake'] = programme.measured('refined-source-intake', lambda:
        source_intake(programme, source, args.numerical_selection, diagnostic))
    parents = prior_translation.describe_contributions(prior_draft, products)
    if len(parents) != 1:
        raise ValueError('actual diagnostic has an ambiguous retained-analysis parent')
    parent = parents[0]
    draft = drafts.qualification_draft(diagnostic, source, policy, selection, parent=parent)
    decision = programme.decision('refined-human-fork', directory, original_result,
        endpoint=original_scope(diagnostic.source.original), question=drafts.QUESTION,
        next_draft=draft, next_manifest=parent, previous=None, human_choice='use',
        act_outcomes=('scoped-failure', 'unresolved', 'useful-supply'))
    programme.report['human_fork_inquiry'] = original_result['committed_inquiry']
    contribution, authenticated = programme.contribution('diagnostic-history-contribution', directory)
    if authenticated != parent:
        raise ValueError('diagnostic export changes the history selected by the committed ACT')
    directory, products, result = programme.wave('refined-qualification', draft, (source, policy, selection),
        parent=parent, contribution=contribution, decision=decision, supplier_directory=directory, human_fork=True)
    supplier = unique_product(products, c.Supply)
    programme.report['actual_qualification'] = supplier.qualification.to_document()
    previous = None  # The original diagnostic endpoint is a different question.
    for phase, following in (('qualification', 'refined-use'), ('use', 'refined-reuse'), ('reuse', None)):
        retain_current_summary(programme, products, source, phase)
        admitted = supplier.disposition is A.SATISFIED
        successor = parent = None
        if following is not None and admitted:
            _, retained_draft, _, _ = load_authored_wave(directory=directory, artifact_writer=programme.plane)
            manifests = drafts.describe_contributions(retained_draft, products)
            if len(manifests) != 1:
                raise ValueError('current full-custody scientific product has an ambiguous successor parent')
            parent = manifests[0]
            successor = programme.measured(following + '.preview', lambda: preview_inquiry_successor(
                supplier_directory=directory, artifact_writer=programme.plane))
            if successor is None:
                raise ValueError('qualified supplier or entered first use lacks its exact declared successor')
        decision = programme.decision(directory.name, directory, result, endpoint=c.scope(source), question=drafts.QUESTION,
            next_draft=successor, next_manifest=parent, previous=previous,
            human_choice='use' if phase == 'use' and successor is not None else None,
            act_outcomes=('scoped-failure', 'unresolved', 'useful-supply') if phase == 'use' and successor is not None
                         else ('useful-supply',))
        if successor is None:
            programme.report['refined_terminal'] = {'phase': phase, 'action': 'STOP',
                'supplier_disposition': supplier.disposition.value,
                'current_disposition': supplier.disposition.value if phase == 'qualification'
                                       else assessed_product(products, phase).assessment.disposition.value,
                'remaining_selected_phases': ['use', 'reuse'] if phase == 'qualification' else [],
                'remaining_phases_status': 'NONATTEMPT' if phase == 'qualification' else 'COMPLETE'}
            break
        contribution, authenticated = programme.contribution(directory.name + '-contribution', directory)
        if authenticated != parent:
            raise ValueError('portable successor parent differs from actual persisted ACT')
        previous, supplier_directory = decision, directory
        # All inherited raw traces, source-admission and supplier/prior-use
        # products come through authenticated HISTORY/MODEL/OUTCOME ports.
        instance = science.compatible_instance(supplier, 'use') if phase == 'qualification' else science.compatible_instance(
            supplier, 'reuse', prior_use=assessed_product(products, 'use'))
        directory, products, result = programme.wave(following, successor, (source, policy, selection, instance),
            parent=parent, contribution=contribution, decision=decision, supplier_directory=supplier_directory)
        assessed = assessed_product(products, instance.phase)
        if assessed.supplier != supplier or assessed.assessment.instance != instance:
            raise ValueError('later assessed instance changes exact original supplier or selected prior-use lineage')
        programme.report.setdefault('actual_instance_assessments', {})[instance.phase] = assessed.assessment.to_document()
    reconcile_contacts(programme, inherited)
    programme.report['scientific_limits'] = {'physical_independent_units': 0, 'biological_independent_units': 0,
        'whole_time_physical_plating_degradation_qualification': 'UNEVALUABLE',
        'matched_complete_total_cost_superiority': 'UNEVALUABLE', 'shared_allocations_are_independent_trials': False,
        'comparator_expenses_are_shared_complete_experiment_windows_not_matched_standalone_arm_costs': True,
        'current_and_historical_measured_windows_are_nonadditive': True,
        'missing_returned_ledgers_do_not_establish_zero_underlying_subcalls': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-selected-refined-programme', action='store_true')
    parser.add_argument('--prior-history-kind',choices=('diagnostic-result','operational-obstruction'),default='diagnostic-result')
    parser.add_argument('--obstruction-source',type=Path)
    for name in ('project-root', 'source-preflight', 'prior-root', 'prior-report', 'prior-cost', 'numerical-selection'):
        parser.add_argument('--' + name, required=True, type=Path)
    for name in ('label', 'prior-report-sha256', 'prior-cost-sha256', 'storage-root-id', 'source-id'):
        parser.add_argument('--' + name, required=True)
    add_custody_location_arguments(parser)
    args = parser.parse_args()
    if not args.run_selected_refined_programme:
        parser.error('native entry requires --run-selected-refined-programme')
    if (args.prior_history_kind == 'operational-obstruction') != (args.obstruction_source is not None):
        parser.error('operational obstruction intake requires its explicit archived --obstruction-source; result intake forbids it')
    if not args.label or any(char not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for char in args.label):
        parser.error('select a fresh lowercase operational label')
    args.domain, args.terminal_product_format = 'battery-refined-inquiry', 'references'
    programme = SelectedProgramme(args)
    inherited = contact_paths(programme.root)
    try:
        run(programme, args)
        programme.report['status'] = 'SELECTED_REFINED_INQUIRY_COMPLETED'
    except BaseException as error:
        programme.report['status'] = 'RETAINED_ADVERSE_ATTEMPT'
        programme.report['exception'] = {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}
        inherited = set(programme.report.get('inherited_native_marker_paths', inherited))
        reconcile_contacts(programme, inherited)
        programme.report['unreturned_execution_ledgers'] = {'charging_subcalls': 'UNKNOWN', 'initial_soc_soh_subcalls': 'UNKNOWN'}
        programme.finish()
        raise
    programme.finish()


if __name__ == '__main__':
    main()
