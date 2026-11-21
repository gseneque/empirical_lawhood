# SPDX-License-Identifier: MPL-2.0
"""SCI02 input selection and receipt-authenticated scientific readout.

The API composes existing bounded I/O and custody. Domain code derives the
scientific graph and equations; this file never enters a native instrument.
"""
from decimal import Decimal
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from statistics import median
from types import SimpleNamespace
import secrets

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_bindings as binding
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_read as reader
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_experiment import Sci02Specification
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import METHODS, POLICY_METHODS, RECIPES, PROTOCOL_ID, NATIVE_PHASES, Sci02Design, Sci02NativeCheckpoint, Sci02Product, Sci02Selection
from empirical_lawhood.domains.matrix.matrix_factor_response.exposure import MatrixFactorExposureCensus, load_mandatory_exposure_floor
from empirical_lawhood.domains.matrix.matrix_researcher_programme.scientific_design import MatrixProgrammeScientificDesign
from empirical_lawhood.domains.matrix.matrix_scheduled_history.selected_streams import SelectedE4StreamRecipe, STREAM_RULE
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.adapters.matrix_storage.matrix_array_io import NPZMemberSelection, decode_matrix_arrays
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes, validate_stable_id
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.design.campaigns import CampaignSpec
from empirical_lawhood.design.experiment_inputs import ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding


def reconcile_exposure_from_programme(*, commitment, artifact_reader, output_directory, maximum_source_bytes):
    """Conservatively exclude every actual reserved root, including nonentry.

    The existing complete input reader authenticates original publications and
    child reservations. This is factual exclusion metadata, not a new scientific
    allocation, source qualification or outcome-access grant.
    """
    from empirical_lawhood.adapters.matrix_storage.matrix_programme_inputs import authenticated_programme_inputs
    from empirical_lawhood.domains.matrix.matrix_factor_response.exposure import MatrixScheduledPhysicalExclusion
    destination = Path(output_directory).absolute()
    if destination.exists(): raise FileExistsError('SCI02 exposure audit requires a new explicit destination')
    with authenticated_programme_inputs(writer=artifact_reader, commitment=commitment,
            maximum_source_bytes=maximum_source_bytes) as original:
        census = original.exposure_census
        seeds, groups = set(census.effective_seed_exclusions), set(census.exposed_independent_groups)
        regimes, physical = set(census.exposed_regimes), set(census.scheduled_physical_exclusions)
        rows = []
        for phase in original.phases:
            allocation = phase.reservation.allocation
            phase_groups, phase_seeds = set(), set()
            for root in allocation.roots:
                phase_groups.add(root.root.independent_group_id)
                regimes.add(root.root.regime_id)
                phase_seeds.update(s.effective_seed for s in root.streams)
            if phase.responses is not None:
                for group, panels in phase.responses.panels:
                    phase_groups.add(group)
                    for panel in panels: phase_seeds.update(s.effective_seed for s in panel.streams)
            physical.update(MatrixScheduledPhysicalExclusion.from_coordinate(c) for c in allocation.coordinates)
            groups.update(phase_groups); seeds.update(phase_seeds)
            rows.append({'role': phase.role, 'independent_groups': len(phase_groups), 'effective_seeds': len(phase_seeds),
                'reservation': original.commitments.phases[len(rows)].reservation.record})
        raw = original.commitments.canonical_bytes()
        source = ArtifactIdentity('sci02.exclusion-source.' + original.commitments.fingerprint(),
            'factual-original-reservation-census', original.commitments.SCHEMA, sha256(raw).hexdigest(), 'application/json', len(raw))
        reconciled = replace(census, census_id='census.sci02.complete-reservations.' + original.commitments.fingerprint(),
            effective_seed_exclusions=tuple(sorted(seeds)), exposed_independent_groups=tuple(sorted(groups)),
            exposed_regimes=tuple(sorted(regimes)), scheduled_physical_exclusions=tuple(sorted(physical, key=lambda v: v.fingerprint())),
            exposed_artifact_sha256s=tuple(sorted({*census.exposed_artifact_sha256s, source.sha256})),
            factual_provenance=tuple(sorted((*census.factual_provenance, source), key=lambda v: v.artifact_id)))
        audit = {'original_commitment': commitment, 'original_exposure_census': census.identity,
            'exclusion_union': reconciled.identity, 'phase_census': tuple(rows),
            'previous_effective_seeds': len(census.effective_seed_exclusions), 'excluded_effective_seeds': len(seeds),
            'previous_groups': len(census.exposed_independent_groups), 'excluded_groups': len(groups),
            'rule': 'EXCLUDE_ALL_ORIGINAL_RESERVATIONS_INCLUDING_NONENTRY_NO_FRESHNESS_OR_AUTHORITY_CLAIM',
            'new_native_contact_count': 0}
        destination.mkdir(parents=True)
        payloads = {'exposure-census.json': reconciled.canonical_bytes(), 'audit.json': canonical_json_bytes(audit),
            'commitment.original.json': raw, 'commitment-publication.original.json': commitment.canonical_bytes()}
        for name, payload in payloads.items():
            with (destination / name).open('xb') as stream: stream.write(payload)
    return {'exposure_census': str(destination / 'exposure-census.json'), 'audit': str(destination / 'audit.json'),
        'excluded_effective_seeds': len(seeds), 'excluded_groups': len(groups), 'new_native_contact_count': 0}


def create_inputs(*, original_design_path, templates_path, exposure_census_path, campaign_path,
        protocol_path, project_root, output_directory, namespace, molecular_requirement):
    """Derive one committed DEV16/held32 bank and the supported DEV8 inputs.

    The caller supplies original source files, their factual exposure census,
    the selected source installation, and a new explicit destination. The
    random material generated here allocates streams; no trajectory is drawn.
    """
    validate_stable_id(namespace)
    destination = Path(output_directory).absolute()
    if destination.exists(): raise FileExistsError('SCI02 inputs require a new explicit destination')
    read = lambda p, kind: decode_canonical_bytes(read_bounded_bytes(Path(p), maximum_bytes=128 * 1024**2), kind, maximum_bytes=128 * 1024**2)
    original = read(original_design_path, MatrixProgrammeScientificDesign)
    exposure = read(exposure_census_path, MatrixFactorExposureCensus)
    floor = load_mandatory_exposure_floor()
    if exposure.mandatory_floor != floor.identity:
        raise ValueError('SCI02 exposure census changes the independently pinned mandatory floor')
    campaign = read(campaign_path, CampaignSpec)
    coordinate, = (c for c in original.e1_coordinates if c.family_id == 'matrix-history.joint-decreasing-coupling')
    raw = read_bounded_bytes(Path(templates_path), maximum_bytes=original.prepared_assay.template_artifact.size_bytes)
    decode_matrix_arrays(raw, NPZMemberSelection(original.prepared_assay.template_artifact, original.prepared_assay.template_members))
    protocol = read_bounded_bytes(Path(protocol_path), maximum_bytes=1024**2)
    design = Sci02Design('design.' + namespace, original.identity, coordinate, original.prepared_assay, original.e1_factor_rule,
        molecular_requirement, sha256(protocol).hexdigest())
    material = SelectedE4StreamRecipe('streams.' + namespace, secrets.token_hex(32), secrets.token_hex(32), STREAM_RULE)
    selection = Sci02Selection('selection.' + namespace, design, material, exposure.identity)
    roots = tuple(selection.root(bank, index) for bank, count in (('DEV', 16), ('HOLDOUT', 32)) for index in range(count))
    seeds, groups = [], []
    for root in roots:
        groups.append(root.group_id)
        for panel in (0, 1):
            seeds.extend(s.effective_seed for s in material.streams(root.group_id, future=bool(panel)))
    if len(set(seeds)) != len(seeds) or set(seeds).intersection(exposure.effective_seed_exclusions) or set(groups).intersection(exposure.exposed_independent_groups):
        raise ValueError('SCI02 reserved roots collide with each other or an original exposed stream/group')
    from empirical_lawhood.storage.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    provenance = capture_numerical_provenance(project_root=project_root)
    source = implementation_binding(project_root)
    specification = Sci02Specification('specification.' + namespace + '.dev8', selection.identity, provenance.identity,
        ObjectIdentity.from_record(campaign.campaign_id, campaign))
    records = {'selection': selection, 'provenance': provenance, 'campaign': campaign}
    sources = ExperimentFileInputSelection('inputs.' + namespace + '.dev8', PROTOCOL_ID,
        tuple(ExperimentInputBinding(key, specification.selection if key == 'selection' else specification.provenance if key == 'provenance'
            else specification.campaign, key + '.json', len(record.canonical_bytes())) for key, record in sorted(records.items())),
        (ExperimentFileInputBinding('templates', design.assay.template_artifact, '1.0.0', 'templates.original.npz', len(raw)),))
    payloads = {key + '.json': record.canonical_bytes() for key, record in records.items()}
    payloads.update({'specification.json': specification.canonical_bytes(), 'sources.json': sources.canonical_bytes(),
        'source-snapshot.json': source.canonical_bytes(), 'templates.original.npz': raw, 'protocol.original.md': protocol,
        'inherited-design.original.json': read_bounded_bytes(Path(original_design_path), maximum_bytes=128 * 1024**2),
        'exposure-census.original.json': read_bounded_bytes(Path(exposure_census_path), maximum_bytes=128 * 1024**2),
        'reservation.json': canonical_json_bytes({'selection': selection.identity, 'roots': roots,
            'assigned_development_roots': 16, 'assigned_holdout_roots': 32, 'assigned_response_package_cap': 144,
            'reserved_effective_seed_count': len(seeds), 'mandatory_exposure_floor': floor.identity,
            'exposure_census': exposure.identity, 'native_contact_count': 0})})
    destination.mkdir(parents=True)
    for name, payload in sorted(payloads.items()):
        with (destination / name).open('xb') as stream: stream.write(payload)
    return {'specification': str(destination / 'specification.json'), 'sources': str(destination / 'sources.json'),
        'source_snapshot': str(destination / 'source-snapshot.json'), 'selection': selection.identity.to_document(),
        'development_roots': 8, 'reserved_response_package_cap': 144, 'native_contact_count': 0,
        'scope': design.scope, 'qualification': 'NOT_ESTABLISHED'}


def refresh_execution_inputs(*, original_input_directory, project_root, output_directory):
    """Rebind the same reservation after repair without resetting its exposure."""
    from empirical_lawhood.storage.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_experiment import bind_inputs
    original, destination = Path(original_input_directory).absolute(), Path(output_directory).absolute()
    if destination.exists(): raise FileExistsError('SCI02 execution revision requires a new explicit destination')
    def read(name, kind):
        raw = read_bounded_bytes(original / name, maximum_bytes=128 * 1024**2)
        return raw, decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    spec_raw, previous = read('specification.json', Sci02Specification)
    sources_raw, sources = read('sources.json', ExperimentFileInputSelection)
    kinds = {'selection': Sci02Selection, 'provenance': NumericalProducingProvenance, 'campaign': CampaignSpec}
    records, payloads = {}, {}
    if sources.protocol_id != PROTOCOL_ID or {b.key for b in sources.bindings} != set(kinds):
        raise ValueError('SCI02 execution revision changes its original source census')
    for source in sources.bindings:
        raw = read_bounded_bytes(original / source.relative_path, maximum_bytes=source.maximum_bytes)
        record = decode_canonical_bytes(raw, kinds[source.key], maximum_bytes=len(raw))
        if record.canonical_bytes() != raw or ObjectIdentity.from_record(source.identity.object_id, record) != source.identity:
            raise ValueError('SCI02 execution revision substitutes an original input')
        records[source.key], payloads[source.key + '.json'] = record, raw
    bind_inputs(previous, records)
    template, = sources.files
    if template.key != 'templates' or template.identity != records['selection'].design.assay.template_artifact:
        raise ValueError('SCI02 execution revision substitutes its physical instrument')
    raw = read_bounded_bytes(original / template.relative_path, maximum_bytes=template.maximum_bytes)
    decode_matrix_arrays(raw, NPZMemberSelection(template.identity, records['selection'].design.assay.template_members))
    payloads['templates.original.npz'] = raw
    for name in ('protocol.original.md', 'inherited-design.original.json', 'exposure-census.original.json', 'reservation.json'):
        payloads[name] = read_bounded_bytes(original / name, maximum_bytes=128 * 1024**2)
    if sha256(payloads['protocol.original.md']).hexdigest() != records['selection'].design.protocol_document_sha256:
        raise ValueError('SCI02 execution revision changes its original scientific protocol')
    provenance, implementation = capture_numerical_provenance(project_root=project_root), implementation_binding(project_root)
    specification = replace(previous, specification_id='specification.sci02.execution.' + previous.fingerprint()[:24]
        + '.' + provenance.fingerprint()[:24], provenance=provenance.identity)
    revised_sources = replace(sources, selection_id='inputs.' + specification.fingerprint(), bindings=tuple(
        replace(source, identity=provenance.identity, relative_path='provenance.json', maximum_bytes=len(provenance.canonical_bytes()))
        if source.key == 'provenance' else replace(source, relative_path=source.key + '.json') for source in sources.bindings),
        files=(replace(template, relative_path='templates.original.npz'),))
    payloads.update({'predecessor.specification.json': spec_raw, 'predecessor.sources.json': sources_raw,
        'predecessor.provenance.json': payloads['provenance.json'], 'provenance.json': provenance.canonical_bytes(),
        'specification.json': specification.canonical_bytes(), 'sources.json': revised_sources.canonical_bytes(),
        'source-snapshot.json': implementation.canonical_bytes()})
    destination.mkdir(parents=True)
    for name, payload in sorted(payloads.items()):
        with (destination / name).open('xb') as stream: stream.write(payload)
    return {'specification': str(destination / 'specification.json'), 'sources': str(destination / 'sources.json'),
        'source_snapshot': str(destination / 'source-snapshot.json'), 'selection': records['selection'].identity.to_document(),
        'native_contact_count': 0, 'exposure_reset': False}


def _source_record(payloads, pin, kind):
    name = 'experiment-source-' + sha256(pin.object_id.encode()).hexdigest() + '.json'
    raw = payloads[name]
    result = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    if ObjectIdentity.from_record(pin.object_id, result) != pin or result.canonical_bytes() != raw:
        raise PermissionError('SCI02 read substitutes its original canonical source')
    return result


def _values(writer, products, tasks, product, *, label="arrays"):
    from empirical_lawhood.api.matrix_native_read_custody import _array
    from empirical_lawhood.storage.recursive_custody import read_exposed_recursive_payload
    _array(products, tasks, product.config.node_id, product.arrays, label=label)
    publication = products['outputs'][product.arrays.array_artifact.artifact_id]
    manifest = writer.read_manifest(publication.materialization.relative_path)
    if (manifest.logical, manifest.materialization) != (publication.logical, publication.materialization):
        raise PermissionError('SCI02 read substitutes an original array publication')
    raw = read_exposed_recursive_payload(writer, manifest, maximum_bytes=product.arrays.array_artifact.size_bytes)
    return dict(decode_matrix_arrays(raw, product.arrays))


def _native_custody(writer, products, tasks, plan, config, provenance, product):
    from empirical_lawhood.api.matrix_native_read_custody import _expected_contact
    from empirical_lawhood.api.matrix_native_acquisition_replay import inspect_native
    from empirical_lawhood.storage.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.storage.native_subwork import ExternalNativeSubworkStore
    contacts = ExternalNativeEffectContactStore(plane=writer, execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=binding.VISIBILITY, outcome_access=binding.ACCESS)
    store = ExternalNativeSubworkStore(plane=writer, parent_contacts=contacts)
    receipt = products['receipts'][config.node_id]
    parent = _expected_contact(task=tasks[config.node_id], plan=plan, run_id=receipt.run_id,
        attempt_id=receipt.attempt_id, products=products)
    if contacts.read(receipt.run_id, config.node_id) != parent:
        raise PermissionError('SCI02 original parent contact does not match its actual consumed operands')
    context = SimpleNamespace(input_ports=tuple(SimpleNamespace(materialization_id=v) for v in parent.input_materialization_ids))
    definition, = binding.native_work(context, config, provenance, parent).definitions
    event = product.native[0] if product.native else None
    if event is not None and event.definition != definition:
        raise PermissionError('SCI02 native event substitutes its original definition or stream scope')
    inspect_native(store=store, definition=definition, event=event, require_nonentry=event is None)
    if event is not None:
        checkpoint = decode_canonical_bytes(b''.join(store.iter_completed_output(definition, 'checkpoint')),
            Sci02NativeCheckpoint, maximum_bytes=binding.MAX_RECORD)
        if (checkpoint.config, checkpoint.arrays, checkpoint.generators, checkpoint.measurements) != (
                config.identity, product.arrays, product.generators, product.measurements):
            raise PermissionError('SCI02 product changes its receipted native continuation checkpoint')


def _summary(rows):
    values = [float(v) for v in rows if v is not None]
    return None if not values else {'minimum': min(values), 'median': median(values), 'maximum': max(values), 'finite_count': len(values)}


def summarize(root_rows, costs):
    """Assigned-denominator comparisons; no fit or qualification inference."""
    table, contrasts, forecasts, policies = [], [], [], []
    for recipe in RECIPES:
        for method in METHODS:
            prefix = recipe + '.' + method + '.'
            table.append({'recipe': recipe, 'method': method, 'assigned_roots': len(root_rows),
                'available_roots': sum(row.get(prefix + 'available') == 1 for row in root_rows),
                'joint_successes': sum(row.get(prefix + 'joint_success') == 1 for row in root_rows),
                'error': _summary(row.get(prefix + 'error') for row in root_rows),
                'view_difference': _summary(row.get(prefix + 'view_difference') for row in root_rows),
                'factor_momentum_signal64': _summary(row.get(recipe + '.signal.factor_momentum64') for row in root_rows)})
            forecasts.append({'recipe': recipe, 'method': method,
                'forecast_absolute_miss': _summary(row.get(prefix + 'forecast_absolute_miss') for row in root_rows),
                'predicted_admissions': sum(row.get(prefix + 'forecast_admit') == 1 for row in root_rows),
                'false_predicted_admissions': sum(row.get(prefix + 'forecast_admit') == 1 and row.get(prefix + 'joint_success') != 1 for row in root_rows)})
    for method in METHODS:
        for recipe in ('EARLY', 'DELAYED'):
            paired = [(row.get(recipe + '.' + method + '.error'), row.get('ORIGINAL.' + method + '.error')) for row in root_rows]
            difference = [a - b for a, b in paired if a is not None and b is not None]
            contrasts.append({'method': method, 'recipe_minus_original': recipe, 'assigned_roots': len(root_rows),
                'complete_pairs': len(difference), 'error_difference': _summary(difference),
                'improved_roots': sum(v < 0 for v in difference), 'worsened_roots': sum(v > 0 for v in difference)})
    for method in POLICY_METHODS:
        selected = []
        for row in root_rows:
            eligible = [recipe for recipe in RECIPES if row.get(recipe + '.' + method + '.forecast_signal', Decimal(0)) >= Decimal('.10')
                and row.get(recipe + '.' + method + '.forecast_error') is not None]
            recipe = min(eligible, key=lambda r: (row[r + '.' + method + '.forecast_error'], RECIPES.index(r))) if eligible else None
            admitted = recipe is not None and row.get(recipe + '.' + method + '.forecast_admit') == 1
            selected.append({'recipe': recipe, 'admitted': admitted,
                'observed_joint_success': None if recipe is None else row.get(recipe + '.' + method + '.joint_success') == 1,
                'disposition': 'REDUCED_ADMISSION' if admitted else 'NATIVE_FALLBACK_REQUIRED' if recipe else 'NO_RECOMMENDATION'})
        policies.append({'method': method, 'scope': 'DEVELOPMENT_DIAGNOSTIC_NOT_HELDOUT_POLICY_VALUE', 'assigned_roots': len(root_rows),
            'selections': selected, 'admissions': sum(v['admitted'] for v in selected),
            'false_admissions': sum(v['admitted'] and not v['observed_joint_success'] for v in selected),
            'no_recommendation': sum(v['recipe'] is None for v in selected),
            'fallback_required': sum(v['disposition'] == 'NATIVE_FALLBACK_REQUIRED' for v in selected)})
    return {'method_table': table, 'preparation_contrasts': contrasts, 'forecast_accuracy': forecasts,
        'selector_diagnostics': policies, 'measured_costs': costs,
        'independent_units': len(root_rows), 'assigned_response_packages': 3 * len(root_rows),
        'qualification': 'NOT_ESTABLISHED', 'molecular_shortcut_requirement': 'OPEN',
        'finite_reuse_saving': 'NOT_ESTABLISHED_BY_ACCURACY_OR_STUDY_COMPLETION',
        'precision_limit': 'Eight DEV roots are not a held-out policy test or a 95/95 reliability demonstration.'}


def read_development_result(*, directory, artifact_writer, specification, instance, payloads, report, products, draft, plan, allow_partial=False):
    if type(specification) is not Sci02Specification or instance.specification != specification.identity:
        raise PermissionError('SCI02 read changes its exact public instance')
    if allow_partial or report.get('typed_product_validation') == 'DEFERRED':
        return {'scientific_completion': 'DEFERRED', 'assigned_roots': 8, 'assigned_response_packages': 24,
            'reason': 'Partial custody does not establish an independently read scientific result.', 'qualification': 'NOT_ESTABLISHED'}
    selection = _source_record(payloads, specification.selection, Sci02Selection)
    provenance = _source_record(payloads, specification.provenance, NumericalProducingProvenance)
    template_input = 'external.templates.' + selection.design.assay.template_artifact.sha256
    template_filename = 'external-' + sha256(template_input.encode()).hexdigest()[:24] + '.npz'
    templates = dict(decode_matrix_arrays(payloads[template_filename],
        NPZMemberSelection(selection.design.assay.template_artifact, selection.design.assay.template_members)))
    configs = {c.node_id: c for i in range(8) for c in binding.configs(selection.design, selection.root('DEV', i), provenance.identity)}
    tasks = {t.task_id: t for t in plan.tasks}
    if set(tasks) != set(configs) or draft.selected_operation_ids != tuple(sorted(configs)):
        raise PermissionError('SCI02 read changes the complete original DEV8 operation census')
    run_id = plan.source_plan.object_id
    if report.get('run_id') != run_id: raise PermissionError('SCI02 read substitutes an original execution')
    from empirical_lawhood.api.matrix_native_read_custody import _record
    rows, costs, retained = [], {}, []
    for index in range(8):
        root = selection.root('DEV', index)
        root_configs = binding.configs(selection.design, root, provenance.identity)
        records, arrays = {}, {}
        for config in root_configs:
            receipt = products['receipts'].get(config.node_id)
            if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED: continue
            product = _record(products, tasks, run_id, config.node_id, Sci02Product)
            if product.config != config: raise PermissionError('SCI02 read changes its original operation configuration')
            records[config.node_id] = product
            arrays[config.node_id] = _values(artifact_writer, products, tasks, product)
            if config.phase in NATIVE_PHASES:
                _native_custody(artifact_writer, products, tasks, plan, config, provenance, product)
            for key, value in product.measurements:
                if config.phase == 'reduce' and not key.startswith('runtime.'): continue
                if key.startswith('runtime.') or key.endswith('_cpu_seconds'):
                    cost_key = config.phase + '.' + key
                    costs[cost_key] = costs.get(cost_key, Decimal(0)) + value
            for native in product.native:
                for key in ('cpu_seconds', 'wall_seconds'):
                    value = getattr(native.completion.cost, key)
                    if value is not None:
                        cost_key = config.phase + '.native_child.' + key
                        costs[cost_key] = costs.get(cost_key, Decimal(0)) + value
        for config in root_configs:
            product = records.get(config.node_id)
            if product is None: continue
            expected_parents = tuple(sorted((records[binding.config_for(config, key).node_id].identity
                for key in binding.DEPENDENCIES[config.phase]), key=lambda p: p.object_id))
            if product.predecessors != expected_parents:
                raise PermissionError('SCI02 read substitutes actual original causal predecessors')
            if config.phase in ('source-state', 'handoff', 'observation'):
                key, = binding.DEPENDENCIES[config.phase]
                source = arrays[binding.config_for(config, key).node_id]
                recomputed = binding.compute(config, {}, {key: source})
                if set(arrays[config.node_id]) != set(recomputed.arrays):
                    raise PermissionError('SCI02 causal projection changes its exact permitted member census')
                for name, value in recomputed.arrays.items(): reader.same(arrays[config.node_id][name], value, 'causal state projection')
            if config.phase == 'assess':
                parents = {k: records[binding.config_for(config, k).node_id] for k in binding.DEPENDENCIES['assess']}
                operands = {k: arrays[p.config.node_id] for k, p in parents.items()}
                reader.instrument_checks(config.design, operands['source-state'], operands['shadow'], templates)
                result = binding.compute(config, parents, operands)
                actual = arrays[config.node_id]
                if set(actual) != set(result.arrays): raise PermissionError('SCI02 read changes complete assessment arrays')
                for name, value in result.arrays.items(): reader.same(actual[name], value, 'independent assessment ' + name)
                scientific = tuple((k, v) for k, v in product.measurements if not k.startswith('runtime.'))
                if (product.disposition, product.reasons, scientific) != (result.disposition, result.reasons, result.measurements):
                    raise PermissionError('SCI02 read changes original independently recomputed criteria')
        base = root_configs[0]
        reduction_config = binding.config_for(base, 'reduce')
        reduction = records.get(reduction_config.node_id)
        if reduction is None:
            rows.append({})
            retained.append({'root': root.record_id, 'state': 'INCOMPLETE', 'missing_operations': 28 - len(records)})
        else:
            assessment_records = tuple(records[binding.config_for(reduction_config, r + '.assess').node_id] for r in RECIPES)
            expected = reader.reduce_root(assessment_records,
                {r: arrays[binding.config_for(reduction_config, r + '.assess').node_id] for r in RECIPES})
            if set(arrays[reduction_config.node_id]) != set(expected.arrays):
                raise PermissionError('SCI02 read changes complete signed finite-pair arrays')
            for name, value in expected.arrays.items():
                reader.same(arrays[reduction_config.node_id][name], value, 'signed finite-pair ' + name)
            actual = tuple((k, v) for k, v in reduction.measurements if not k.startswith('runtime.'))
            if actual != expected.measurements: raise PermissionError('SCI02 whole-root reduction changes assigned arm outcomes')
            rows.append(dict(actual))
            retained.append({'root': root.record_id, 'state': 'ASSESSED', 'product': reduction.identity.to_document()})
    return {'scientific_completion': 'COMPLETE_DEV8_ASSESSMENT' if all(r['state'] == 'ASSESSED' for r in retained) else 'INCOMPLETE_DEV8_ASSESSMENT',
        'state': 'SCI02_RETAINED_RESULT', 'scope': selection.design.scope, 'root_census': retained,
        **summarize(rows, {k: str(v) for k, v in sorted(costs.items())}), 'new_native_contact_count': 0}
