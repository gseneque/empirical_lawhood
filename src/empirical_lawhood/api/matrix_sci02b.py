# SPDX-License-Identifier: MPL-2.0
"""SCI02-B source selection and authenticated reuse through shared EL custody."""
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_bindings as original
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_experiment import Sci02Specification
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Arrays, Sci02Selection
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_records import Sci02BRetainedCase
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
        raise FileExistsError('SCI02-B retained export requires a new explicit destination')
    pending = {}

    def consume(**kwargs):
        summary = read_prepared_development_science(**kwargs)
        if summary is None or summary.get('scientific_completion') != 'COMPLETE_DEV8_ASSESSMENT':
            raise ValueError('SCI02-B requires the complete original independently read DEV8')
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
                    raise ValueError('SCI02-B retained export omits an original completed product')
                product, = outputs.values()
                if product.config != config:
                    raise ValueError('SCI02-B retained export substitutes an original operation')
                source[(config.recipe, config.phase)] = product
            arrays = {}
            instrument = source['COMMON', 'shadow']
            values = _values(kwargs['artifact_writer'], products, tasks, instrument)
            for name in ('forces', 'receivers', 'source_frame', 'source_spectrum', 'source_low',
                    'complement_spectrum', 'complement_vectors', 'source_factor_admitted'):
                if name in values:
                    arrays['instrument.' + name] = values[name]
            for recipe in original.RECIPES:
                for phase in ('handoff', 'observation', 'assess', 'origin'):
                    product = source[recipe, phase]
                    values = _values(kwargs['artifact_writer'], products, tasks, product)
                    for name, value in values.items():
                        selected = phase in ('handoff', 'observation') or phase == 'assess' and name.endswith('.native')
                        selected |= phase == 'origin' and name.endswith('.basis.input_krylov48')
                        if selected:
                            arrays[recipe.lower() + '.' + phase + '.' + name] = value
            raw, members = encode_matrix_arrays(arrays)
            artifact = ArtifactIdentity('arrays.sci02b.retained.' + root.fingerprint(), 'retained-scientific-input',
                original.MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), 'application/x-npz', len(raw))
            record = Sci02BRetainedCase('retained.sci02b.' + root.fingerprint(), root, selection.design,
                ObjectIdentity.from_record(plan.execution_plan_id, plan),
                tuple(sorted((p.identity for p in source.values()), key=lambda p: p.object_id)),
                tuple(sorted((ObjectIdentity.from_record(products['receipts'][c.node_id].receipt_id,
                    products['receipts'][c.node_id]) for c in configs), key=lambda p: p.object_id)),
                Sci02Arrays('arrays.sci02b.retained.' + root.fingerprint(), artifact, members), sha256(summary_raw).hexdigest())
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


def create_development_inputs(*, retained_directory, campaign_path, protocol_path, project_root, output_directory):
    """Bind authenticated exposed operands to the supported complete B0 graph."""
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_experiment import Sci02BSpecification
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_records import PROTOCOL_ID, Sci02BDesign
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.storage.bounded_io import read_bounded_bytes
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
    from empirical_lawhood.storage.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.design.campaigns import CampaignSpec
    from empirical_lawhood.design.experiment_inputs import ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding
    source, destination = Path(retained_directory).absolute(), Path(output_directory).absolute()
    if destination.exists(): raise FileExistsError('SCI02-B development requires a new explicit input destination')
    read = lambda path, limit=128 * 1024**2: read_bounded_bytes(Path(path), maximum_bytes=limit)
    audit = json.loads(read(source / 'export-audit.json', 1024**2))
    if (audit.get('independent_roots') != 8 or audit.get('new_native_contacts') != 0
            or audit.get('exposure') != 'ORIGINAL_SCI02_DEV8_EXPOSED'):
        raise ValueError('SCI02-B retained package omits its original exposed development census')
    original = {}
    expected_names = {'original-selection.json', 'original-read.json', *(f'root-{i:02d}.{s}' for i in range(8) for s in ('json', 'npz'))}
    if set(audit['members']) != expected_names:
        raise ValueError('SCI02-B retained package changes its complete original members')
    for name in sorted(expected_names):
        value = read(source / name)
        if audit['members'][name] != {'sha256': sha256(value).hexdigest(), 'size_bytes': len(value)}:
            raise ValueError('SCI02-B retained package substitutes an authenticated export member')
        original[name] = value
    selection = decode_canonical_bytes(original['original-selection.json'], Sci02Selection, maximum_bytes=len(original['original-selection.json']))
    cases = tuple(decode_canonical_bytes(original[f'root-{i:02d}.json'], Sci02BRetainedCase, maximum_bytes=4 * 1024**2) for i in range(8))
    summary_hash = sha256(original['original-read.json']).hexdigest()
    for index, case in enumerate(cases):
        if case.root != selection.root('DEV', index) or case.original_read_sha256 != summary_hash or case.design != selection.design:
            raise ValueError('SCI02-B export changes original roots, physical operands or independently read summary')
        decode_matrix_arrays(original[f'root-{index:02d}.npz'], case.arrays)
    protocol = read(protocol_path, 1024**2)
    study = Sci02BDesign('design.sci02b.' + selection.fingerprint()[:24] + '.' + sha256(protocol).hexdigest()[:24],
        selection.identity, selection.design, sha256(protocol).hexdigest())
    campaign_raw = read(campaign_path, 4 * 1024**2)
    campaign = decode_canonical_bytes(campaign_raw, CampaignSpec, maximum_bytes=len(campaign_raw))
    provenance, implementation = capture_numerical_provenance(project_root=project_root), implementation_binding(project_root)
    specification = Sci02BSpecification('specification.sci02b.' + study.fingerprint(), study.identity, selection.identity,
        tuple(c.identity for c in cases), provenance.identity, ObjectIdentity.from_record(campaign.campaign_id, campaign))
    records = {'study': study, 'selection': selection, 'provenance': provenance, 'campaign': campaign,
        **{f'root{i:02d}': case for i, case in enumerate(cases)}}
    sources = ExperimentFileInputSelection('inputs.sci02b.' + specification.fingerprint(), PROTOCOL_ID,
        tuple(ExperimentInputBinding(key, ObjectIdentity.from_record(record.campaign_id, record) if key == 'campaign' else record.identity,
            key + '.json', len(record.canonical_bytes())) for key, record in sorted(records.items())),
        tuple(ExperimentFileInputBinding(f'root{i:02d}-arrays', case.arrays.array_artifact, '1.0.0', f'root-{i:02d}.npz',
            case.arrays.array_artifact.size_bytes) for i, case in enumerate(cases)))
    payloads = {key + '.json': record.canonical_bytes() for key, record in records.items()}
    payloads.update({name: value for name, value in original.items() if name.endswith('.npz') or name == 'original-read.json'})
    payloads.update({'specification.json': specification.canonical_bytes(), 'sources.json': sources.canonical_bytes(),
        'source-snapshot.json': implementation.canonical_bytes(), 'protocol.original.md': protocol,
        'original-export-audit.json': read(source / 'export-audit.json', 1024**2)})
    destination.mkdir(parents=True)
    for name, value in sorted(payloads.items()):
        with (destination / name).open('xb') as stream: stream.write(value)
    return {'directory': str(destination), 'specification': str(destination / 'specification.json'),
        'sources': str(destination / 'sources.json'), 'source_snapshot': str(destination / 'source-snapshot.json'),
        'independent_roots': 8, 'operations': 17, 'new_native_contacts': 0, 'exposure': 'ORIGINAL_SCI02_DEV8_EXPOSED'}


def read_development_result(*, directory, artifact_writer, specification, instance, payloads, report, products, draft, plan, allow_partial=False):
    """Independently check original retained operands, models, pairs and decision."""
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_bindings as binding
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_development as development
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_experiment import Sci02BSpecification
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_records import Sci02BDesign, Sci02BProduct
    from empirical_lawhood.api.matrix_native_read_custody import _record
    from empirical_lawhood.api.matrix_sci02 import _source_record, _values
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
    from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
    from empirical_lawhood.science.records.status import OperationalStatus
    if type(specification) is not Sci02BSpecification or instance.specification != specification.identity:
        raise PermissionError('SCI02-B read substitutes the exact original public instance')
    if allow_partial or report.get('typed_product_validation') == 'DEFERRED':
        return {'scientific_completion': 'DEFERRED', 'assigned_roots': 8, 'qualification': 'NOT_ESTABLISHED'}
    study = _source_record(payloads, specification.study, Sci02BDesign)
    selection = _source_record(payloads, specification.selection, Sci02Selection)
    provenance = _source_record(payloads, specification.provenance, NumericalProducingProvenance)
    cases = tuple(_source_record(payloads, p, Sci02BRetainedCase) for p in specification.cases)
    configs = binding.configs(study, tuple(selection.root('DEV', i) for i in range(8)), specification.cases, provenance.identity)
    tasks = {t.task_id: t for t in plan.tasks}
    if set(tasks) != {c.node_id for c in configs} or draft.selected_operation_ids != tuple(c.node_id for c in configs):
        raise PermissionError('SCI02-B read changes its complete original candidate/root census')
    run_id = plan.source_plan.object_id
    if report.get('run_id') != run_id: raise PermissionError('SCI02-B read substitutes its actual original execution')
    records, arrays, rows, costs = {}, {}, [], {}
    for config in configs:
        receipt = products['receipts'].get(config.node_id)
        if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED:
            continue
        product = _record(products, tasks, run_id, config.node_id, Sci02BProduct)
        if product.config != config: raise PermissionError('SCI02-B read changes an exact producing configuration')
        records[config.node_id] = product
        arrays[config.node_id] = _values(artifact_writer, products, tasks, product)
        for key, value in product.measurements:
            if key.startswith('runtime.') or key.endswith('_cpu_seconds'):
                costs[config.phase + '.' + key] = costs.get(config.phase + '.' + key, 0) + value
    for config in configs:
        if config.phase != 'diagnose': continue
        product = records.get(config.node_id)
        if product is None:
            rows.append({'root_ordinal': config.root.ordinal, 'dimension': config.candidate_dimension, 'state': 'UNKNOWN'})
            continue
        case = cases[config.root.ordinal]
        filename = 'external-' + sha256(('external.' + case.arrays.array_artifact.artifact_id).encode()).hexdigest()[:24] + '.npz'
        retained_values = dict(decode_matrix_arrays(payloads[filename], case.arrays))
        if product.predecessors: raise PermissionError('SCI02-B retained diagnosis adds a future predecessor')
        development.verify_diagnosis(config, case, retained_values, product, arrays[config.node_id])
        rows.append({'root_ordinal': config.root.ordinal, 'root': config.root.record_id, 'dimension': config.candidate_dimension,
            'state': 'ASSESSED', 'disposition': product.disposition, 'reasons': list(product.reasons),
            'measurements': {key: None if value is None else str(value) for key, value in product.measurements},
            'product': product.identity.to_document()})
    fitted_config, = (c for c in configs if c.phase == 'fit')
    fitted = records.get(fitted_config.node_id)
    complete = fitted is not None and len(records) == 17
    dimension = None
    if complete:
        diagnoses = {k: p for k, p in records.items() if p.config.phase == 'diagnose'}
        if fitted.predecessors != tuple(sorted((p.identity for p in diagnoses.values()), key=lambda p: p.object_id)):
            raise PermissionError('SCI02-B fit changes its original producing predecessors')
        development.verify_fit(fitted_config, diagnoses, arrays, fitted, arrays[fitted_config.node_id])
        dimension, _ = development.selection(tuple(diagnoses.values()))
    return {'scientific_completion': 'COMPLETE_SCI02B_DEVELOPMENT_ASSESSMENT' if complete else 'INCOMPLETE_SCI02B_DEVELOPMENT',
        'state': 'REPRESENTATION_MENU_CLOSED' if complete and not dimension else 'FROZEN_DESCRIPTION_AVAILABLE' if complete else 'INCOMPLETE',
        'scope': study.scope, 'assigned_roots': 8, 'assigned_candidates': 2, 'retained_response_packages': 24,
        'selected_dimension': dimension, 'new_native_contact_count': 0, 'root_candidate_findings': rows,
        'cost_components_seconds': {k: str(v) for k, v in sorted(costs.items())},
        'calibration_roots_entered': 0, 'confirmation_roots_entered': 0,
        'molecular_requirement': {'status': 'OPEN', 'requirement': study.physical.molecular_requirement},
        'qualification': 'NOT_ESTABLISHED'}
