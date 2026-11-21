# SPDX-License-Identifier: MPL-2.0
"""SCI02-C source selection and authenticated reuse through shared EL custody."""
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_bindings as original
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_experiment import Sci02Specification
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Arrays, Sci02Selection
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import Sci02CRetainedCase
from empirical_lawhood.adapters.matrix_storage.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity


def export_original_development(*, directory, artifact_writer, output_directory):
    """Authenticate complete DEV8, then retain bounded deterministic operands.

    This source projection acquires no trajectory and creates no qualification.
    Its exact original product/receipt census survives in each retained case.
    """
    from empirical_lawhood.api.experiment_scientific_read import read_prepared_development_science
    from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_retained_roots
    from empirical_lawhood.api.matrix_sci02 import _source_record, _values
    destination = Path(output_directory).absolute()
    if destination.exists():
        raise FileExistsError('SCI02-C retained export requires a new explicit destination')
    pending = {}

    def consume(**kwargs):
        summary = read_prepared_development_science(**kwargs)
        if summary is None or summary.get('scientific_completion') != 'COMPLETE_DEV8_ASSESSMENT':
            raise ValueError('SCI02-C requires the complete original independently read DEV8')
        payloads, products, plan = kwargs['payloads'], kwargs['products'], kwargs['plan']
        specification = decode_canonical_bytes(payloads['experiment-specification.json'], Sci02Specification, maximum_bytes=4 * 1024**2)
        selection = _source_record(payloads, specification.selection, Sci02Selection)
        summary_raw = json.dumps(summary, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        tasks = {t.task_id: t for t in plan.tasks}
        for index in range(8):
            root = selection.root('DEV', index)
            configs = original.configs(selection.design, root, specification.provenance)
            source = {}
            for config in configs:
                outputs = products['records'].get(config.node_id, {})
                if len(outputs) != 1:
                    raise ValueError('SCI02-C retained export omits an original completed product')
                product, = outputs.values()
                if product.config != config:
                    raise ValueError('SCI02-C retained export substitutes an original operation')
                source[(config.recipe, config.phase)] = product
            arrays = {}
            instrument = source['COMMON', 'shadow']
            values = _values(kwargs['artifact_writer'], products, tasks, instrument)
            for name in ('forces', 'receivers', 'source_frame', 'source_spectrum', 'source_low',
                    'complement_spectrum', 'complement_vectors', 'source_factor_admitted'):
                if name in values:
                    arrays['instrument.' + name] = values[name]
            for recipe in original.RECIPES:
                for phase in ('handoff', 'observation', 'assess'):
                    product = source[recipe, phase]
                    values = _values(kwargs['artifact_writer'], products, tasks, product)
                    for name, value in values.items():
                        selected = phase in ('handoff', 'observation') or phase == 'assess' and name.endswith('.native')
                        if selected:
                            arrays[recipe.lower() + '.' + phase + '.' + ('h32.' if phase == 'observation' else '') + name] = value
                prefix = source[recipe, 'response-prefix']
                native_prefix = _values(kwargs['artifact_writer'], products, tasks, prefix)
                for view, mult in (('primary', 1), ('fine', 2)):
                    for panel in (0, 1):
                        for name in ('positions', 'momenta', 'alpha_tilde', 'ticks'):
                            value = native_prefix[f'branch.{view}.p{panel}.a0.hold.' + name]
                            arrays[f'{recipe.lower()}.observation.h16.{view}.p{panel}.' + name] = value[[16 * mult]].copy()
            raw, members = encode_matrix_arrays(arrays)
            artifact = ArtifactIdentity('arrays.sci02c.retained.' + root.fingerprint(), 'retained-scientific-input',
                original.MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), 'application/x-npz', len(raw))
            record = Sci02CRetainedCase('retained.sci02c.' + root.fingerprint(), root, selection.design,
                ObjectIdentity.from_record(plan.execution_plan_id, plan),
                tuple(sorted((p.identity for p in source.values()), key=lambda p: p.object_id)),
                tuple(sorted((ObjectIdentity.from_record(products['receipts'][c.node_id].receipt_id,
                    products['receipts'][c.node_id]) for c in configs), key=lambda p: p.object_id)),
                Sci02Arrays('arrays.sci02c.retained.' + root.fingerprint(), artifact, members), sha256(summary_raw).hexdigest())
            pending[f'root-{index:02d}.json'] = record.canonical_bytes()
            pending[f'root-{index:02d}.npz'] = raw
        pending['original-selection.json'] = selection.canonical_bytes()
        pending['original-read.json'] = summary_raw
        return summary

    _read_recursive_wave_with_retained_roots(directory=directory, artifact_writer=artifact_writer,
        terminal_product_format='references', _scientific_consumer=consume)
    destination.mkdir(parents=True)
    for name, raw in sorted(pending.items()):
        with (destination / name).open('xb') as stream:
            stream.write(raw)
    audit = {'source_directory': str(Path(directory).absolute()), 'independent_roots': 8, 'new_native_contacts': 0,
        'exposure': 'ORIGINAL_SCI02_DEV8_EXPOSED',
        'members': {name: {'sha256': sha256(raw).hexdigest(), 'size_bytes': len(raw)} for name, raw in sorted(pending.items())}}
    (destination / 'export-audit.json').write_text(json.dumps(audit, sort_keys=True, indent=2) + '\n')
    return {'directory': str(destination), 'audit': str(destination / 'export-audit.json'), 'independent_roots': 8, 'new_native_contacts': 0}


def _write_inputs(*, study, selection, campaign, cases, frozen, calibrated, files, protocol, project_root, output_directory, audit):
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_experiment import Sci02CSpecification
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import PROTOCOL_ID
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.storage.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.design.experiment_inputs import ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding
    destination = Path(output_directory).absolute()
    if destination.exists(): raise FileExistsError('SCI02-C inputs require a new explicit destination')
    provenance, implementation = capture_numerical_provenance(project_root=project_root), implementation_binding(project_root)
    tranche = 'TRAINING' if frozen is None else 'CALIBRATION' if calibrated is None else 'CONFIRMATION'
    specification = Sci02CSpecification('specification.sci02c.' + tranche.lower() + '.' + study.fingerprint() + '.' + provenance.fingerprint()[:16],
        study.identity, selection.identity, provenance.identity, ObjectIdentity.from_record(campaign.campaign_id, campaign), tranche,
        tuple(c.identity for c in cases), None if frozen is None else frozen.identity, None if calibrated is None else calibrated.identity)
    records = {'study': study, 'selection': selection, 'provenance': provenance, 'campaign': campaign,
        **{f'root{i:02d}': c for i, c in enumerate(cases)}, **({} if frozen is None else {'frozen': frozen}),
        **({} if calibrated is None else {'calibrated': calibrated})}
    sources = ExperimentFileInputSelection('inputs.sci02c.' + specification.fingerprint(), PROTOCOL_ID,
        tuple(ExperimentInputBinding(key, ObjectIdentity.from_record(campaign.campaign_id, value) if key == 'campaign' else value.identity,
            key + '.json', len(value.canonical_bytes())) for key, value in sorted(records.items())),
        tuple(ExperimentFileInputBinding(key, artifact, '1.0.0', name, len(raw)) for key, artifact, name, raw in sorted(files)))
    payloads = {key + '.json': value.canonical_bytes() for key, value in records.items()}
    payloads.update({name: raw for _, _, name, raw in files})
    payloads.update({'specification.json': specification.canonical_bytes(), 'sources.json': sources.canonical_bytes(),
        'source-snapshot.json': implementation.canonical_bytes(), 'protocol.original.md': protocol,
        'input-custody-audit.json': json.dumps(audit, indent=2, sort_keys=True).encode()})
    destination.mkdir(parents=True)
    for name, value in sorted(payloads.items()):
        with (destination / name).open('xb') as stream: stream.write(value)
    return {'directory': str(destination), 'specification': str(destination / 'specification.json'), 'sources': str(destination / 'sources.json'),
        'source_snapshot': str(destination / 'source-snapshot.json'), 'tranche': tranche,
        'independent_roots': 32 if tranche == 'CONFIRMATION' else 8,
        'operations': 9 if tranche == 'TRAINING' else 929 if tranche == 'CONFIRMATION' else 233,
        'new_native_contact_cap': 0 if tranche == 'TRAINING' else 320 if tranche == 'CONFIRMATION' else 80,
        'audit_ordinals': list(study.audit_ordinals)}


def create_training_inputs(*, retained_directory, campaign_path, protocol_path, project_root, output_directory):
    """Bind all exposed original DEV8 histories, without acquiring a new root."""
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import Sci02CDesign
    from empirical_lawhood.storage.bounded_io import read_bounded_bytes
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
    from empirical_lawhood.design.campaigns import CampaignSpec
    source = Path(retained_directory).absolute()
    read = lambda p, bound=128 * 1024**2: read_bounded_bytes(Path(p), maximum_bytes=bound)
    audit = json.loads(read(source / 'export-audit.json', 1024**2))
    names = {'original-selection.json', 'original-read.json', *(f'root-{i:02d}.{s}' for i in range(8) for s in ('json', 'npz'))}
    if (audit.get('independent_roots'), audit.get('new_native_contacts'), audit.get('exposure')) != (8, 0, 'ORIGINAL_SCI02_DEV8_EXPOSED') or set(audit['members']) != names:
        raise ValueError('SCI02-C retained export changes original exposed development census')
    bodies = {}
    for name in sorted(names):
        raw = read(source / name)
        if audit['members'][name] != {'sha256': sha256(raw).hexdigest(), 'size_bytes': len(raw)}:
            raise ValueError('SCI02-C retained export changes exact original member bytes')
        bodies[name] = raw
    selection = decode_canonical_bytes(bodies['original-selection.json'], Sci02Selection, maximum_bytes=4 * 1024**2)
    cases = tuple(decode_canonical_bytes(bodies[f'root-{i:02d}.json'], Sci02CRetainedCase, maximum_bytes=4 * 1024**2) for i in range(8))
    for i, c in enumerate(cases):
        if (c.root != selection.root('DEV', i) or c.design != selection.design
                or c.original_read_sha256 != sha256(bodies['original-read.json']).hexdigest()):
            raise ValueError('SCI02-C training substitutes an original root or independent read')
        decode_matrix_arrays(bodies[f'root-{i:02d}.npz'], c.arrays)
    protocol = read(protocol_path, 1024**2)
    study = Sci02CDesign('design.sci02c.' + selection.fingerprint()[:24] + '.' + sha256(protocol).hexdigest()[:24],
        selection.identity, selection.design, sha256(protocol).hexdigest())
    campaign = decode_canonical_bytes(read(campaign_path, 4 * 1024**2), CampaignSpec, maximum_bytes=4 * 1024**2)
    return _write_inputs(study=study, selection=selection, campaign=campaign, cases=cases, frozen=None, calibrated=None,
        files=tuple((f'root{i:02d}-arrays', c.arrays.array_artifact, f'root-{i:02d}.npz', bodies[f'root-{i:02d}.npz']) for i, c in enumerate(cases)),
        protocol=protocol, project_root=project_root, output_directory=output_directory, audit=audit)


def create_continuation_inputs(*, directory, artifact_writer, templates_path, protocol_path, project_root, output_directory):
    """Derive the next original tranche only from an authenticated complete read."""
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_experiment import Sci02CSpecification
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import Sci02CDesign, Sci02CProduct
    from empirical_lawhood.api.experiment_scientific_read import read_prepared_development_science
    from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_retained_roots
    from empirical_lawhood.api.matrix_sci02 import _source_record
    from empirical_lawhood.storage.bounded_io import read_bounded_bytes
    from empirical_lawhood.design.campaigns import CampaignSpec
    captured = {}

    def consume(**kwargs):
        summary = read_prepared_development_science(**kwargs)
        if summary is None or summary.get('scientific_completion') != 'COMPLETE_SCI02C_ASSESSMENT':
            raise ValueError('SCI02-C continuation requires a complete independently read predecessor')
        payloads = kwargs['payloads']
        spec = decode_canonical_bytes(payloads['experiment-specification.json'], Sci02CSpecification, maximum_bytes=4 * 1024**2)
        if spec.tranche not in ('TRAINING', 'CALIBRATION'):
            raise ValueError('SCI02-C finite confirmation has no further native successor')
        pooled = [v for values in kwargs['products']['records'].values() for v in values.values()
            if type(v) is Sci02CProduct and v.config.phase == ('fit' if spec.tranche == 'TRAINING' else 'calibrate')]
        if len(pooled) != 1: raise ValueError('SCI02-C continuation lacks the original pooled product')
        result = pooled[0]
        frozen = result if spec.tranche == 'TRAINING' else _source_record(payloads, spec.frozen, Sci02CProduct)
        if frozen.frozen_description is None: raise ValueError('SCI02-C source diagnosis did not supply a frozen account')
        captured.update(study=_source_record(payloads, spec.study, Sci02CDesign), selection=_source_record(payloads, spec.selection, Sci02Selection),
            campaign=_source_record(payloads, spec.campaign, CampaignSpec), frozen=frozen,
            calibrated=None if spec.tranche == 'TRAINING' else result,
            audit={'predecessor_directory': str(Path(directory).absolute()), 'predecessor_product': result.identity.to_document(),
                'predecessor_receipt': kwargs['products']['receipts'][result.config.node_id].to_document(),
                'readout_sha256': sha256(json.dumps(summary, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
                'new_native_contacts_during_derivation': 0})
        return summary

    _read_recursive_wave_with_retained_roots(directory=directory, artifact_writer=artifact_writer,
        terminal_product_format='references', _scientific_consumer=consume)
    protocol = read_bounded_bytes(Path(protocol_path), maximum_bytes=1024**2)
    if sha256(protocol).hexdigest() != captured['study'].protocol_document_sha256:
        raise ValueError('SCI02-C continuation changes its frozen original scientific protocol')
    artifact = captured['selection'].design.assay.template_artifact
    templates = read_bounded_bytes(Path(templates_path), maximum_bytes=artifact.size_bytes)
    if len(templates) != artifact.size_bytes or sha256(templates).hexdigest() != artifact.sha256:
        raise ValueError('SCI02-C continuation substitutes original fixed instrument bytes')
    return _write_inputs(**captured, cases=(), files=(('templates', artifact, 'templates.npz', templates),),
        protocol=protocol, project_root=project_root, output_directory=output_directory)


def _native_custody(writer, products, tasks, plan, config, provenance, product):
    from types import SimpleNamespace
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_bindings as binding
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_native import native_work
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import Sci02CNativeCheckpoint
    from empirical_lawhood.api.matrix_native_read_custody import _expected_contact
    from empirical_lawhood.api.matrix_native_acquisition_replay import inspect_native
    from empirical_lawhood.storage.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.storage.native_subwork import ExternalNativeSubworkStore
    contacts = ExternalNativeEffectContactStore(plane=writer, execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=binding.VISIBILITY, outcome_access=binding.ACCESS)
    store = ExternalNativeSubworkStore(plane=writer, parent_contacts=contacts)
    receipt = products['receipts'][config.node_id]
    parent = _expected_contact(task=tasks[config.node_id], plan=plan, run_id=receipt.run_id, attempt_id=receipt.attempt_id, products=products)
    if contacts.read(receipt.run_id, config.node_id) != parent:
        raise PermissionError('SCI02-C parent native contact changes actual consumed operands')
    context = SimpleNamespace(input_ports=tuple(SimpleNamespace(materialization_id=v) for v in parent.input_materialization_ids))
    definition, = native_work(context, config, provenance, parent).definitions
    event = product.native[0] if product.native else None
    if event is not None and event.definition != definition:
        raise PermissionError('SCI02-C native event changes original source, stream or predecessor custody')
    inspect_native(store=store, definition=definition, event=event, require_nonentry=event is None)
    if event is not None:
        checkpoint = decode_canonical_bytes(b''.join(store.iter_completed_output(definition, 'checkpoint')),
            Sci02CNativeCheckpoint, maximum_bytes=binding.MAX_RECORD)
        if (checkpoint.config, checkpoint.arrays, checkpoint.generators, checkpoint.measurements) != (
                config.identity, product.arrays, product.generators, product.measurements):
            raise PermissionError('SCI02-C product changes its original receipted native checkpoint')


def _check_result(product, actual, expected):
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_read import same
    if set(actual) != set(expected.arrays): raise PermissionError('SCI02-C read changes complete scientific output members')
    for name, value in expected.arrays.items(): same(actual[name], value, 'SCI02-C independently read ' + name)
    measurements = tuple((k, v) for k, v in product.measurements if not k.startswith('runtime.'))
    if (product.disposition, product.reasons, measurements) != (expected.disposition, expected.reasons, expected.measurements):
        raise PermissionError('SCI02-C read substitutes the original scientific result')


def read_result(*, directory, artifact_writer, specification, instance, payloads, report, products, draft, plan, allow_partial=False):
    """Read one original tranche in bounded whole-root scopes, with no acquisition."""
    from decimal import Decimal
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_bindings as binding
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_science as science
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_read as reader
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_read as old_reader
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_experiment import Sci02CSpecification, roots_for
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import Sci02CDesign, Sci02CProduct, NATIVE_PHASES, POOLED
    from empirical_lawhood.api.matrix_native_read_custody import _record
    from empirical_lawhood.api.matrix_sci02 import _source_record, _values
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import NPZMemberSelection, decode_matrix_arrays
    from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
    from empirical_lawhood.science.records.status import OperationalStatus
    if type(specification) is not Sci02CSpecification or instance.specification != specification.identity:
        raise PermissionError('SCI02-C read substitutes its exact public instance')
    count = 32 if specification.tranche == 'CONFIRMATION' else 8
    if allow_partial or report.get('typed_product_validation') == 'DEFERRED':
        return {'scientific_completion': 'DEFERRED', 'assigned_roots': count, 'qualification': 'NOT_ESTABLISHED'}
    study = _source_record(payloads, specification.study, Sci02CDesign)
    selection = _source_record(payloads, specification.selection, Sci02Selection)
    provenance = _source_record(payloads, specification.provenance, NumericalProducingProvenance)
    cases = tuple(_source_record(payloads, p, Sci02CRetainedCase) for p in specification.cases)
    frozen = None if specification.frozen is None else _source_record(payloads, specification.frozen, Sci02CProduct)
    calibrated = None if specification.calibrated is None else _source_record(payloads, specification.calibrated, Sci02CProduct)
    roots = roots_for(selection, specification.tranche)
    configs = binding.configs(study, roots, provenance.identity, specification.cases,
        None if frozen is None else frozen.frozen_description, None if calibrated is None else calibrated.calibration_result)
    tasks = {t.task_id: t for t in plan.tasks}
    if set(tasks) != {c.node_id for c in configs} or draft.selected_operation_ids != tuple(c.node_id for c in configs):
        raise PermissionError('SCI02-C read changes its complete original operation census')
    run_id = plan.source_plan.object_id
    if report.get('run_id') != run_id: raise PermissionError('SCI02-C read changes original execution identity')
    records, costs, operation_costs = {}, {}, []
    for config in configs:
        receipt = products['receipts'].get(config.node_id)
        if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED: continue
        product = _record(products, tasks, run_id, config.node_id, Sci02CProduct)
        if product.config != config: raise PermissionError('SCI02-C read substitutes an exact producing configuration')
        records[config.node_id] = product
        own_cost = {}
        for key, value in product.measurements:
            if value is not None and (key.startswith('runtime.') or key.endswith('_cpu_seconds') or key.endswith('hvp_columns')):
                costs[config.phase + '.' + key] = costs.get(config.phase + '.' + key, Decimal(0)) + value
                own_cost[key] = str(value)
        for native in product.native:
            for key in ('cpu_seconds', 'wall_seconds'):
                value = getattr(native.completion.cost, key)
                if value is not None:
                    label = 'native_child.' + key
                    costs[config.phase + '.' + label] = costs.get(config.phase + '.' + label, Decimal(0)) + value
                    own_cost[label] = str(value)
        operation_costs.append({'node': config.node_id, 'phase': config.phase, 'recipe': config.recipe,
            'root_ordinal': None if config.phase in POOLED else config.root.ordinal, 'components': own_cost})
    for config in configs:
        product = records.get(config.node_id)
        if product is None: continue
        parents = binding.parents_for(config)
        if any(c.node_id not in records for c in parents.values()):
            raise PermissionError('SCI02-C completed product lacks original causal predecessor receipts')
        if product.predecessors != tuple(sorted((records[c.node_id].identity for c in parents.values()), key=lambda p: p.object_id)):
            raise PermissionError('SCI02-C product substitutes its sealed original predecessors')
    templates = None
    if specification.tranche != 'TRAINING':
        artifact = study.physical.assay.template_artifact
        filename = 'external-' + sha256(('external.templates.' + artifact.sha256).encode()).hexdigest()[:24] + '.npz'
        templates = dict(decode_matrix_arrays(payloads[filename], NPZMemberSelection(artifact, study.physical.assay.template_members)))
    rows, pooled_inputs, pooled_arrays = [], {}, {}
    for root in roots:
        selected = tuple(c for c in configs if c.phase not in POOLED and c.roots == (root,))
        if any(c.node_id not in records for c in selected):
            rows.append({'root': root.record_id, 'ordinal': root.ordinal, 'state': 'UNKNOWN',
                'missing_operations': sum(c.node_id not in records for c in selected)})
            continue
        arrays = {c.node_id: _values(artifact_writer, products, tasks, records[c.node_id]) for c in selected}
        for config in selected:
            product, actual = records[config.node_id], arrays[config.node_id]
            parents = {k: records[c.node_id] for k, c in binding.parents_for(config).items()}
            operands = {k: arrays[p.config.node_id] for k, p in parents.items()}
            if config.phase in NATIVE_PHASES:
                _native_custody(artifact_writer, products, tasks, plan, config, provenance, product)
            if config.phase == 'diagnose':
                case = cases[root.ordinal]
                filename = 'external-' + sha256(('external.' + case.arrays.array_artifact.artifact_id).encode()).hexdigest()[:24] + '.npz'
                retained = dict(decode_matrix_arrays(payloads[filename], case.arrays))
                reader.check_diagnosis(config, case, retained, product, actual)
            elif config.phase in ('source-state', 'handoff', 'observation', 'history-observation'):
                result, _, _ = binding.compute(config, parents, operands, None)
                _check_result(product, actual, result)
            elif config.phase == 'instrument':
                old_reader.instrument_checks(config.design, operands['source-state'], actual, templates)
            elif config.phase in ('request', 'decision', 'assess', 'reduce'):
                result, _, _ = binding.compute(config, parents, operands, None)
                _check_result(product, actual, result)
        final, = (c for c in selected if c.phase == ('diagnose' if specification.tranche == 'TRAINING' else 'reduce'))
        product, values = records[final.node_id], arrays[final.node_id]
        pooled_inputs[final.node_id], pooled_arrays[final.node_id] = product, values
        row = {'root': root.record_id, 'ordinal': root.ordinal, 'state': 'ASSESSED', 'disposition': product.disposition,
            'product': product.identity.to_document(), 'measurements': {k: None if v is None else str(v) for k, v in product.measurements}}
        for key in ('features', 'model_q', 'frozen_q', 'native_q', 'native_endpoints', 'predictions', 'widths', 'selected_route', 'request_history'):
            if key in values: row[key] = values[key].tolist()
        rows.append(row)
    pooled, = (c for c in configs if c.phase in POOLED)
    result = records.get(pooled.node_id)
    complete = result is not None and len(records) == len(configs) and len(pooled_inputs) == count
    summary = {}
    if complete:
        actual = _values(artifact_writer, products, tasks, result)
        if pooled.phase == 'fit': reader.check_fit(pooled, pooled_inputs, pooled_arrays, result, actual)
        elif pooled.phase == 'calibrate':
            expected, calibration = science.calibrate(pooled, pooled_inputs, pooled_arrays)
            _check_result(result, actual, expected)
            if result.calibration_result != calibration: raise PermissionError('SCI02-C read substitutes its exact calibration rank')
        else: _check_result(result, actual, reader.confirm(pooled, pooled_inputs, pooled_arrays))
        summary['pooled_product'] = result.identity.to_document()
        summary['pooled_measurements'] = {k: None if v is None else str(v) for k, v in result.measurements}
        if result.frozen_description is not None: summary['frozen_description'] = result.frozen_description.to_document()
        if result.calibration_result is not None: summary['calibration'] = result.calibration_result.to_document()
        if 'aggregate' in actual:
            summary['aggregate'] = dict(zip(('reference_mean', 'surrogate_mean', 'audit_only_mean', 'corrected_mean', 'residual_standard_error'), actual['aggregate'].tolist(), strict=True))
    return {'scientific_completion': 'COMPLETE_SCI02C_ASSESSMENT' if complete else 'INCOMPLETE_SCI02C_ASSESSMENT',
        'state': 'FROZEN_ACCOUNT_AVAILABLE' if complete and result.frozen_description is not None else 'FINITE_TRANCHE_ASSESSED' if complete else 'INCOMPLETE',
        'scope': study.scope, 'tranche': specification.tranche, 'assigned_roots': count, 'assigned_response_packages': 3 * count,
        'root_findings': rows, 'cost_components': {k: str(v) for k, v in sorted(costs.items())}, 'operation_costs': operation_costs,
        'audit_ordinals': list(study.audit_ordinals), 'new_native_contact_count': 0,
        'original_completed_native_contacts': sum(len(p.native) for p in records.values()),
        'sealed_decision_reference_dependencies_verified': sum(c.phase == 'reference' and c.node_id in records for c in configs),
        'molecular_requirement': {'status': 'OPEN', 'requirement': study.physical.molecular_requirement},
        'qualification': 'NOT_ESTABLISHED', **summary}
