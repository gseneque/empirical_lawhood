# SPDX-License-Identifier: MPL-2.0
"""Prepare or read one paired response stage through the existing EL APIs.

The request supplies operational paths returned by earlier stages. Scientific
rosters, products, predictions and decisions remain with their existing owners.
This checkout recipe supplies explicit selections and paths. Shared services
own authoring, decisions, contributions and original result reading. Use the
ordinary recursive-inquiry CLI for execution and recovery.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import sys

from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationError, MAX_REQUEST_BYTES, MAX_TEXT_BYTES, absolute_path, exact_mapping, identifier, load_application_json
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.api.application_context import application_storage
from empirical_lawhood.api.recursive_authoring import author_recursive_wave, load_authored_wave
from empirical_lawhood.api.recursive_contributions import authenticate_recursive_contribution, export_recursive_contribution
from empirical_lawhood.api import recursive_inquiry as inquiry
from empirical_lawhood.api.domain_composition.rubisco_response.preparation_inquiry import project_preparation_inquiry
from empirical_lawhood.api.domain_composition.rubisco_response.active_preparation import prepare_response_prefix_from_files, prepare_prefix_continuation, retain_preparation_prefix_inputs, validate_prefix_file_selection
from empirical_lawhood.api.domain_composition.rubisco_response.preparation_response import freeze_response_predictions, prepare_preparation_response_stage, retain_response_inputs, prepare_environmental_response_design_from_files
from empirical_lawhood.api.domain_composition.rubisco_response.preparation_response_analysis import native_result_reader, prepare_response_analysis, read_preparation_stage, read_response_analysis, read_response_stage, retain_response_analysis_inputs
from empirical_lawhood.api.domain_composition.rubisco_response.preparation_supply import prepare_preparation_supply, read_preparation_supply
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_supply_policy import supply_design, supply_owners
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff


def json_default(value):
    if hasattr(value, 'to_document'):
        return value.to_document()
    if isinstance(value, (Path, Decimal)):
        return str(value)
    raise TypeError('Do not replace complete original operands with an implicit serialization')


def retain(path, value, *, plane):
    raw = value.canonical_bytes() if hasattr(value, 'canonical_bytes') else (
        json.dumps(value, default=json_default, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    relative = path.relative_to(plane.root.contract.canonical_path).as_posix()
    selected = plane.root.resolve(relative, for_write=True, operation_minimum_free_bytes=len(raw))
    selected.parent.mkdir(parents=True, exist_ok=True)
    selected = plane.root.resolve(relative, for_write=True, operation_minimum_free_bytes=len(raw))
    with selected.open('xb') as stream:
        stream.write(raw)
    plane.root.resolve(relative, for_write=False)


def validate_request(operation, request):
    """Reject invalid selections before reading any scientific custody."""
    authoring = ('prepare-prefix', 'continue-prefix', 'fork-prefix', 'admit', 'assess', 'prepare-response')
    common = ('root_directory', 'supplier_directory', 'previous_decision_directories',
        'completed_supplier_directories', 'contribution_directories', 'cutoff_id',
        'actor_id', 'human_choice', 'human_reason') if operation in authoring else ()
    fields = {
        'prepare-environment-design': (('design_file', 'model_files'), ('region', 'residue_keys', 'coordinate_tolerance_angstrom')),
        'prepare-prefix': (('design_file', 'plan_file', 'model_files', 'native_work_directory'), ()),
        'continue-prefix': (('prefix_directory', 'prefix_contribution', 'native_work_directory'), ()),
        'fork-prefix': (('prospective_directory', 'input_bindings'), ()),
        'admit': (('prefix_directory',), ('response_analysis_directory',)),
        'assess': (('prefix_directory', 'response_directories'), ()),
        'prepare-response': (('prefix_directory', 'prefix_contribution', 'stage', 'native_work_directory'),
            ('diagnostic_directory', 'diagnostic_contribution')),
        'read-prefix': (('prefix_directory',), ()),
        'read-response': (('directory',), ()),
        'read-analysis': (('directory',), ()),
        'read-admission': (('directory',), ()),
        'export': (('directory',), ()),
    }
    if operation not in fields:
        raise ApplicationError('UNSUPPORTED_OPERATION', 'Select a supported preparation operation.')
    required, optional = fields[operation]
    required = ('output_directory', *common, *required)
    exact_mapping(request, (*required, *optional), required=required)
    for name, value in request.items():
        if name.endswith('_directories'):
            if type(value) not in (list, tuple):
                raise ApplicationError('INVALID_PATHS', 'Select an array of original paths.', field=name)
            paths = tuple(absolute_path(path, name) for path in value)
            if len(set(paths)) != len(paths) or (not paths and name in (
                    'previous_decision_directories', 'contribution_directories')):
                raise ApplicationError('INVALID_PATHS', 'Preserve distinct required original paths.', field=name)
        elif name.endswith(('_directory', '_contribution', '_file')):
            if value is None and name in optional:
                continue
            absolute_path(value, name)
    if operation in authoring:
        for name in ('actor_id', 'cutoff_id'):
            identifier(request[name], name)
        if request['human_choice'] not in ('acquire', 'hold'):
            raise ApplicationError('INVALID_CHOICE', 'Select acquire or hold.', field='human_choice')
        reason = request['human_reason']
        if type(reason) is not str or not reason.strip() or len(reason.encode()) > MAX_TEXT_BYTES:
            raise ApplicationError('INVALID_REASON', 'Supply a bounded explicit selection reason.', field='human_reason')
    if operation == 'prepare-environment-design':
        from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import MODELS
        from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import REGIONS
        roles = ('preparation', 'prototype', 'representation')
        exact_mapping(request['model_files'], MODELS, required=MODELS)
        for name in MODELS:
            exact_mapping(request['model_files'][name], (*roles, 'topology', 'coordinates'), required=roles)
            for role, path in request['model_files'][name].items():
                absolute_path(path, 'model_files.' + name + '.' + role)
        region = request.get('region', REGIONS[0])
        residues = request.get('residue_keys', ())
        if region not in REGIONS or type(residues) not in (list, tuple):
            raise ApplicationError('INVALID_ENVIRONMENT', 'Select a prospective supported protein region.')
        keys = []
        for row in residues:
            if (type(row) not in (list, tuple) or len(row) != 2 or type(row[1]) is not int or row[1] <= 0):
                raise ApplicationError('INVALID_ENVIRONMENT', 'Select chain and positive sequence-position pairs.')
            identifier(row[0], 'residue_keys')
            keys.append(tuple(row))
        if (keys != sorted(set(keys)) or (region == REGIONS[1] and not keys)
                or (region == REGIONS[0] and keys)):
            raise ApplicationError('INVALID_ENVIRONMENT', 'Use a distinct sorted residue census only for the selected-residues region.')
        if 'coordinate_tolerance_angstrom' in request:
            value = request['coordinate_tolerance_angstrom']
            try:
                tolerance = Decimal(value) if type(value) is str else None
            except ArithmeticError:
                tolerance = None
            if tolerance is None or not tolerance.is_finite() or not Decimal(0) < tolerance <= Decimal('0.0001'):
                raise ApplicationError('INVALID_ENVIRONMENT', 'Use an exact decimal string for a positive coordinate tolerance no larger than 0.0001 angstrom.')
    if operation == 'prepare-prefix':
        validate_prefix_file_selection(model_files=request['model_files'], native_work_directory=request['native_work_directory'])
        if (len(request['contribution_directories']) != 1
                or Path(request['supplier_directory']) != Path(request['root_directory'])):
            raise ApplicationError('INVALID_PARENTS', 'Select the original root supplier and its one original contribution.')
    if operation == 'fork-prefix':
        bindings = request['input_bindings']
        if type(bindings) not in (list, tuple) or not bindings:
            raise ApplicationError('INVALID_BINDINGS', 'Use the complete returned input bindings.', field='input_bindings')
        seen = set()
        for binding in bindings:
            if type(binding) not in (list, tuple) or len(binding) != 2:
                raise ApplicationError('INVALID_BINDINGS', 'Select input identifier and path pairs.', field='input_bindings')
            key = identifier(binding[0], 'input_bindings')
            absolute_path(binding[1], 'input_bindings')
            if key in seen:
                raise ApplicationError('INVALID_BINDINGS', 'Input identifiers must not repeat.', field='input_bindings')
            seen.add(key)
    if operation == 'continue-prefix':
        if (len(request['contribution_directories']) != 2
                or Path(request['prefix_contribution']) not in {Path(p) for p in request['contribution_directories']}
                or Path(request['supplier_directory']) != Path(request['prefix_directory'])
                or Path(request['prefix_directory']) not in {Path(p) for p in request['completed_supplier_directories']}):
            raise ApplicationError('INVALID_PARENTS', 'Select the original prefix supplier, its completed history, and the root and prefix contributions.')
    if operation == 'prepare-response':
        stage = request['stage']
        if stage not in ('diagnostic', 'initial-primary', 'environment-diagnostic', 'challenge', 'additional-refinement'):
            raise ApplicationError('INVALID_STAGE', 'Select a supported response stage.', field='stage')
        diagnosis = tuple(request.get(name) is not None for name in ('diagnostic_directory', 'diagnostic_contribution'))
        if diagnosis != ((False, False) if stage in ('diagnostic', 'initial-primary') else (True, True)):
            raise ApplicationError('INVALID_DIAGNOSTIC', 'Later stages require both original diagnostic selections.')
        expected = (Path(request['prefix_contribution']),)
        if stage not in ('diagnostic', 'initial-primary'):
            expected += (Path(request['diagnostic_contribution']),)
        selected = tuple(Path(path) for path in request['contribution_directories'])
        if len(set(expected)) != len(expected) or set(selected) != set(expected):
            raise ApplicationError('INVALID_PARENTS', 'Match direct contributions to the selected prefix and diagnostic.')
    return request


def original_parent(path, plane):
    return authenticate_recursive_contribution(directory=Path(path), artifact_writer=plane)[2]


def prefix_case(request, plane):
    return read_preparation_stage(directory=Path(request['prefix_directory']), artifact_writer=plane)


def author_prepared_supplier(request, context, plane, prepared, bindings, parents, *, prospective=None):
    root = context.project_root
    destination = Path(request['output_directory'])
    draft = prepared['draft']
    from empirical_lawhood.api.recursive_operations import inquiry_selection_scope
    with inquiry_selection_scope(draft):
        _, _, _, origins_for = supply_owners(draft)
        design = supply_design(draft)
        if 'design' in prepared and prepared['design'] != design:
            raise ValueError('supplier selection changes its frozen scientific design')
        origins = origins_for(draft)
    if prospective is None:
        prospective = destination / 'prospective'
        author_recursive_wave(draft=draft, project_root=root, artifact_writer=plane, output_dir=prospective,
            input_bindings=bindings, contribution_dirs=parents, origins=origins)
    from empirical_lawhood.api.recursive_inquiry_read import inquiry_authoring_read
    with inquiry_authoring_read(plane) as reader:
        return _commit_prepared_supplier(request=request, root=root, destination=destination,
            draft=draft, design=design, origins=origins, prospective=prospective,
            bindings=bindings, parents=parents, plane=plane, reader=reader)


def _commit_prepared_supplier(*, request, root, destination, draft, design, origins,
        prospective, bindings, parents, plane, reader):
    # The reader shares immutable history within this invocation. Current
    # products/access/costs are reprojected; new packages use the ordinary writer.
    with reader.read_context() as reader:
        selected = project_preparation_inquiry(root_directory=Path(request['root_directory']),
            prospective_directory=prospective, design=design,
            previous_decision_directories=tuple(Path(p) for p in request['previous_decision_directories']),
            completed_supplier_directories=tuple(Path(p) for p in request['completed_supplier_directories']),
            information_cutoff=InformationCutoff(request['cutoff_id'], 'clock.rubisco.declared-rate-closure',
                CausalPhase.POST_OUTCOME, None), artifact_writer=reader)
        decision_path = destination / 'decision'
        arguments = dict(specification=selected.specification, state=selected.state, sources=selected.sources,
            menu=selected.menu, policy=selected.policy, campaign=selected.campaign,
            right=selected.campaign.decision_rights[0], actor_id=request['actor_id'],
            project_root=root, artifact_writer=reader, output_dir=decision_path,
            human_choice=request['human_choice'], human_reason=request['human_reason'])
    arguments['artifact_writer'] = plane
    # Commitment owns its current preview and validation. There is no separate
    # review pause in this caller that would justify another complete preview.
    packet, records = inquiry.commit_inquiry_decision(**arguments)
    result = dict(decision_directory=str(decision_path), decision_packet_sha256=packet.fingerprint(),
        decision=records['decision.json'].to_document(), selected_directory=None, new_native_calls=0)
    if request['human_choice'] != 'hold':
        wave = destination / 'selected'
        authored = inquiry.author_inquiry_successor(decision_directory=decision_path,
            supplier_directory=Path(request['supplier_directory']), human_fork_draft=draft, origins=origins,
            input_bindings=bindings, contribution_dirs=parents, project_root=root, artifact_writer=plane,
            output_dir=wave, expected_decision_packet_sha256=packet.fingerprint())
        with reader.read_context() as reader:
            inquiry.read_inquiry_successor(directory=wave, artifact_writer=reader)
        result.update(selected_directory=str(wave), authoring=authored)
    else:
        # ACT authoring reads the decision itself; HOLD has no successor owner
        # to perform that read, so retain its independent readback here.
        with reader.read_context() as reader:
            inquiry.read_inquiry_decision(directory=decision_path, artifact_writer=reader)
    return result, selected, records


def operate(operation, request, context, plane):
    request = validate_request(operation, request)
    destination = Path(request['output_directory'])
    if destination.exists() or destination.is_symlink():
        raise ValueError('Select a new output directory; preserve the preceding attempt')
    relative = destination.relative_to(plane.root.contract.canonical_path).as_posix()
    plane.root.resolve(relative, for_write=True)
    if operation == 'prepare-environment-design':
        design = prepare_environmental_response_design_from_files(design_file=Path(request['design_file']),
            model_files=request['model_files'], region=request.get('region', 'COMMON_PROTEIN_OUTSIDE_SELECTED_SITE_CORE'),
            residue_keys=tuple(tuple(row) for row in request.get('residue_keys', ())),
            coordinate_tolerance_angstrom=Decimal(request.get('coordinate_tolerance_angstrom', '0.000001')))
        path = destination / 'environment-design.json'
        retain(path, design, plane=plane)
        environment = design.environment
        return dict(design_file=str(path), design=design.identity.to_document(),
            environment=environment.identity.to_document(), region=environment.region,
            residue_keys=environment.residue_keys, eligible_common_atoms=len(environment.atom_pairs),
            excluded_atom_counts={name: len(rows) for name, rows in environment.excluded_atom_indices},
            physical_atom_counts=dict(environment.physical_atom_counts),
            coordinate_tolerance_angstrom=str(environment.coordinate_tolerance_angstrom),
            direction_status='NOT_YET_NOMINATED_REQUIRES_INITIAL_WT_PRIMARY_ACTION',
            native_return_allowance=dict(preparation_up_to=10, response_core=24, optional_refinement=4),
            new_native_calls=0)
    if operation == 'prepare-prefix':
        parents = tuple(Path(p) for p in request['contribution_directories'])
        prepared = prepare_response_prefix_from_files(design_file=Path(request['design_file']),
            plan_file=Path(request['plan_file']), model_files=request['model_files'],
            native_work_directory=Path(request['native_work_directory']),
            root_directory=Path(request['root_directory']), root_contribution=parents[0],
            project_root=context.project_root, artifact_writer=plane)
        bindings = retain_preparation_prefix_inputs(prepared=prepared, artifact_writer=plane, output_dir=destination / 'inputs')
        return author_prepared_supplier(request, context, plane, prepared, bindings, parents)[0]
    if operation == 'fork-prefix':
        prospective = Path(request['prospective_directory'])
        _, draft, _, _ = load_authored_wave(directory=prospective, artifact_writer=plane, lazy_payloads=True)
        bindings = tuple((key, Path(path)) for key, path in request['input_bindings'])
        parents = tuple(Path(p) for p in request['contribution_directories'])
        return author_prepared_supplier(request, context, plane, dict(draft=draft), bindings, parents, prospective=prospective)[0]
    if operation == 'continue-prefix':
        parents = tuple(Path(p) for p in request['contribution_directories'])
        prepared = prepare_prefix_continuation(prefix_directory=Path(request['prefix_directory']),
            prefix_contribution=Path(request['prefix_contribution']),
            native_work_directory=Path(request['native_work_directory']),
            project_root=context.project_root, artifact_writer=plane)
        bindings = retain_preparation_prefix_inputs(prepared=prepared, artifact_writer=plane, output_dir=destination / 'inputs')
        return author_prepared_supplier(request, context, plane, prepared, bindings, parents)[0]
    if operation == 'export':
        return export_recursive_contribution(directory=Path(request['directory']), output_dir=destination / 'contribution',
            project_root=context.project_root, artifact_writer=plane)
    if operation == 'read-prefix':
        original = prefix_case(request, plane)
        checkpoints = original['checkpoints']
        for name, readout in checkpoints['original_readouts'].items():
            retain(destination / (name + '-readout.json'), readout, plane=plane)
        return dict(status=checkpoints['checkpoint_status'], report=original['report'],
            readouts={name: row.identity.to_document() for name, row in checkpoints['original_readouts'].items()},
            original_selected_positions=4, available_positions=len(checkpoints['centers']), new_native_calls=0)
    if operation == 'read-response':
        original = read_response_stage(directory=Path(request['directory']), artifact_writer=plane)
        for index, readout in enumerate(original['readouts']):
            retain(destination / f'original-readout-{index:03d}.json', readout, plane=plane)
        return dict(report=original['report'], selected_effects=len(original['configs']),
            original_readouts=len(original['readouts']), new_native_calls=0)
    if operation == 'read-analysis':
        original = read_response_analysis(directory=Path(request['directory']), artifact_writer=plane)
        retain(destination / 'assessment.json', original['assessment'], plane=plane)
        return dict(report=original['report'], assessment=original['assessment'].to_document(), new_native_calls=0)
    if operation == 'read-admission':
        original = read_preparation_supply(directory=Path(request['directory']), artifact_writer=plane)
        retain(destination / 'assessment.json', original['assessment'], plane=plane)
        return dict(report=original['report'], assessment=original['assessment'].to_document(),
            connections=[row.to_document() for row in original['connection_assessments']], new_native_calls=0)
    original = prefix_case(request, plane)
    checkpoints = original['checkpoints']
    parents = tuple(Path(p) for p in request['contribution_directories'])
    manifests = tuple(original_parent(p, plane) for p in parents)
    parent_by_path = dict(zip(parents, manifests, strict=True))
    if operation == 'admit':
        assessment = None
        if request.get('response_analysis_directory') is not None:
            assessment = read_response_analysis(directory=Path(request['response_analysis_directory']), artifact_writer=plane)['assessment']
        prepared = prepare_preparation_supply(design=checkpoints['design'],
            original_prefixes=tuple(checkpoints['original_readouts'][n] for n in ('m1-i95m', 'm1-wt')),
            parents=manifests, original_response=assessment)
        return author_prepared_supplier(request, context, plane, prepared, (), parents)[0]
    if operation == 'assess':
        stages = tuple(read_response_stage(directory=Path(p), artifact_writer=plane) for p in request['response_directories'])
        prepared = prepare_response_analysis(checkpoints=checkpoints,
            stages=tuple((stage['configs'], stage['readouts']) for stage in stages),
            representations=original['representations'], parents=manifests, project_root=context.project_root,
            native_subwork_for_result=lambda result: native_result_reader(plane, result))
        bindings = retain_response_analysis_inputs(prepared=prepared, artifact_writer=plane, output_dir=destination / 'inputs')
        return author_prepared_supplier(request, context, plane, prepared, bindings, parents)[0]
    if operation == 'prepare-response':
        stage = request['stage']
        configs = {c.original.model_name: c for c in original['configs']}
        models = tuple((name, configs[name].original.prototype, original['representations'][name],
            original['model_sources'][name].topology_utf8.encode('ascii'),
            original['model_sources'][name].coordinates_utf8.encode('ascii'),
            Path(request['native_work_directory']) / name) for name in ('m1-i95m', 'm1-wt'))
        diagnostic = None
        diagnostic_parent = None
        predictions = ()
        if request.get('diagnostic_directory') is not None:
            diagnostic = read_response_analysis(directory=Path(request['diagnostic_directory']), artifact_writer=plane)['assessment']
            diagnostic_parent = parent_by_path[Path(request['diagnostic_contribution'])]
        if stage == 'challenge':
            predictions = freeze_response_predictions(assessment=diagnostic, centers=checkpoints['centers'], frames=checkpoints['frames'])
        preparation_parent = parent_by_path[Path(request['prefix_contribution'])]
        prepared = prepare_preparation_response_stage(checkpoints=checkpoints, stage=stage, models=models,
            project_root=context.project_root, preparation_parent=preparation_parent,
            predictions=predictions, diagnostic=diagnostic, diagnostic_parent=diagnostic_parent)
        bindings = retain_response_inputs(prepared=prepared, artifact_writer=plane, output_dir=destination / 'inputs')
        return author_prepared_supplier(request, context, plane, prepared, bindings, parents)[0]
    raise ValueError('Unsupported stage operation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('prepare-environment-design', 'prepare-prefix', 'continue-prefix', 'fork-prefix', 'export', 'read-prefix',
        'read-response', 'read-analysis', 'read-admission', 'admit', 'assess', 'prepare-response'))
    parser.add_argument('--context', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--operator-profile', type=Path, required=True)
    args = parser.parse_args()
    context = ApplicationContext.from_document(load_application_json(read_bounded_bytes(args.context, maximum_bytes=MAX_REQUEST_BYTES)))
    if args.operator_profile != context.operator_profile:
        raise ValueError('Select the same absolute operator profile as the application context')
    if context.python_executable != Path(sys.executable).absolute():
        raise ValueError('Invoke the selected installed interpreter')
    request = load_application_json(read_bounded_bytes(args.request, maximum_bytes=MAX_REQUEST_BYTES))
    validate_request(args.operation, request)
    _, _, plane = application_storage(context, for_write=True)
    result = operate(args.operation, request, context, plane)
    destination = Path(request['output_directory'])
    retain(destination / 'operation-return.json', dict(operation=args.operation,
        completed_at_utc=datetime.now(timezone.utc).isoformat(), result=result,
        context_sha256=context.fingerprint()), plane=plane)
    print(json.dumps(dict(operation=args.operation, status=result.get('status'),
        output=str(destination / 'operation-return.json')), sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
