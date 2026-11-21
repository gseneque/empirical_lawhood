# SPDX-License-Identifier: MPL-2.0
"""Original wave reading, analysis preparation and independent six-question reuse."""

from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.api.recursive_inquiry_read import inquiry_projection_read
from empirical_lawhood.storage.recursive_control_read import decode_authored_control
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactStreamWriteRequest
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis import PreparationResponseAnalysis, action_bytes, assess_analysis, available_capture, binary_operands, read_action_bytes
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_operation import capability_for, config_type, external_id, input_selections
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_translation import response_analysis_draft
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import MODELS, POSITIONS, is_environmental, primary_response_frame


@contextmanager
def native_result_reader(artifact_writer, result):
    """Keep original native custody verified through one complete consumer read."""
    with artifact_writer.read_context() as reader:
        yield _native_result_reader(reader, result)


def _native_result_reader(artifact_writer, result):
    """Bind a completed-only store to the caller's live verification scope."""
    from empirical_lawhood.storage.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.storage.native_subwork import ExternalNativeSubworkStore
    definition = result.unit.definition if hasattr(result, 'unit') else result.definition
    parent = definition.parent_contact
    contacts = ExternalNativeEffectContactStore(plane=artifact_writer, execution_plan=parent.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    return ExternalNativeSubworkStore(plane=artifact_writer, parent_contacts=contacts, parent_contact=parent, completed_only=True)


def _input(payloads, external, kind):
    record = decode_authored_control(payloads,
        'external-' + sha256(external.input_id.encode()).hexdigest()[:24] + '.json', kind,
        maximum_bytes=external.maximum_size_bytes)
    if (record.canonical_size_bytes() != external.maximum_size_bytes
            or record.fingerprint() != external.expected_content_sha256):
        raise ValueError('preparation reader substitutes its complete original authored input')
    return record


def read_preparation_stage(*, directory, artifact_writer):
    """Independently reopen the actual paired prefix and retain unavailable states."""
    with artifact_writer.read_context() as writer, inquiry_projection_read(writer) as reading:
        return _read_preparation_stage(directory=directory, artifact_writer=reading.writer, reading=reading)


def _read_preparation_stage(*, directory, artifact_writer, reading):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_inquiry import actual_products
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import node_id
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_translation import external_id as source_id, selected_configs
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_operation import checked_coordinates
    from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import PeriodicProbeRawSources
    from empirical_lawhood.api.domain_composition.rubisco_response.preparation_response import prepare_response_checkpoints
    def preflight(*, packet, draft, source):
        if selected_configs(draft)[0].scientific_context is None:
            raise ValueError('research preparation reading requires its actual original root context')
    original = reading.wave(directory=directory, include_products=True, validate_authored=preflight)
    packet, draft, source, payloads = original.packet, original.draft, original.implementation, original.payloads
    report, products = original.report, original.products
    configs = selected_configs(draft)
    if len(actual_products(draft, products)) != 4:
        raise ValueError('paired preparation lacks complete original result/readout publications; preserve its operational census')
    external = {row.input_id: row for row in draft.external_inputs}
    prefixes, representations, model_sources = [], {}, {}
    for config in configs:
        name = config.original.model_name
        model = _input(payloads, external[source_id(config, 'native-model')], MolecularRepresentation)
        preparation = _input(payloads, external[source_id(config, 'native-preparation')], ActiveModelPreparation)
        raw = _input(payloads, external[source_id(config, 'native-source')], PeriodicProbeRawSources)
        coordinates = checked_coordinates(config.original, model, preparation, raw)
        records = products['records'][node_id(config)]
        result = records[node_id(config) + '.product']
        prefixes.append((name, config, model, preparation, coordinates, result, _native_result_reader(artifact_writer, result)))
        representations[name], model_sources[name] = model, raw
    checkpoints = prepare_response_checkpoints(design=configs[0].scientific_context.design, prefixes=tuple(prefixes))
    for config in configs:
        if checkpoints['original_readouts'][config.original.model_name] != products['records'][node_id(config)][node_id(config) + '.assessment']:
            raise ValueError('preparation reader disagrees with its original independently published readout')
    return dict(packet=packet, draft=draft, source=source, report=report, products=products, configs=configs,
        checkpoints=checkpoints, representations=representations, model_sources=model_sources)


def read_response_stage(*, directory, artifact_writer):
    with artifact_writer.read_context() as writer, inquiry_projection_read(writer) as reading:
        return _read_response_stage(directory=directory, reading=reading)


def _read_response_stage(*, directory, reading):
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_inquiry import actual_products
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import node_id
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_translation import selected_configs
    original = reading.wave(directory=directory, include_products=True)
    packet, draft, source = original.packet, original.draft, original.implementation
    report, products = original.report, original.products
    configs = selected_configs(draft)
    actual_products(draft, products)
    readouts = tuple(products['records'][node_id(c)][node_id(c) + '.assessment'] for c in configs
        if node_id(c) + '.assessment' in products['records'].get(node_id(c), {}))
    return dict(packet=packet, draft=draft, source=source, report=report, products=products, configs=configs, readouts=readouts)


def prepare_response_analysis(*, checkpoints, stages, representations, parents, project_root, native_subwork_for_result):
    """Retain original raw captures and derive an ordinary non-native supplier.

    Each stage supplies its original configs and original published readouts.
    Both completed and unavailable returns retain the full selected denominator.
    The native reader factory supplies a context spanning reconstruction and
    raw capture, with its final custody check before any analysis is returned.
    """
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import node_id
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_read import read_response_point
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_translation import validate_configs
    design = checkpoints['design']
    points, readouts, raw_operands = {}, {}, {}
    frames = dict(checkpoints['frames'])
    for configs, original_readouts in stages:
        base = validate_configs(configs)
        if base.protocol != design:
            raise ValueError('response analysis changes its original scientific design')
        by_config = {c.identity: c for c in configs}
        for config in configs:
            if is_environmental(design):
                name = config.frame.model_name
                if primary_response_frame(config.frame) != primary_response_frame(checkpoints['frames'][name]):
                    raise ValueError('environment response analysis changes its original initial primary frame')
                if config.frame.additional is not None:
                    if frames[name].additional is not None and frames[name] != config.frame:
                        raise ValueError('environment response analysis changes its one frozen direction')
                    frames[name] = config.frame
            key = config.point.effect.effect_id
            if key in points:
                raise ValueError('response analysis repeats a selected stage')
            points[key] = config.point
        for original in original_readouts:
            config = by_config.get(original.configuration)
            if config is None:
                raise ValueError('response analysis adds a readout from an unselected configuration')
            result = original.original.original_result
            key = config.point.effect.effect_id
            with native_subwork_for_result(result) as store:
                actual = read_response_point(config=config, representation=representations[config.center.model_name],
                    center_bytes=checkpoints['center_bytes'][config.center.model_name, config.center.position],
                    original_result=result, native_subwork=store,
                    assessor_source=ObjectIdentity.from_record('source.response-assessor.' +
                        config.original.implementation.code_sources_sha256, config.original.implementation),
                    readout_id=node_id(config) + '.assessment')
                if actual != original or key in readouts:
                    raise ValueError('response analysis disagrees with or repeats its original point readout')
                readouts[key] = original
                captures = available_capture(actual)
                if captures is not None:
                    for name in ('energy', 'gradient'):
                        capture = getattr(captures, name)
                        raw = b''.join(store.iter_completed_output(result.definition, 'raw.' + name, maximum_chunk_bytes=2**20))
                        if len(raw) != capture.artifact_manifest.materialization.size_bytes:
                            raise ValueError('response analysis exceeds its original bounded complete capture')
                        raw_operands['native-array.' + key + '.' + name] = raw
    available = set(checkpoints['centers']) == set(POSITIONS)
    if not available and stages:
        raise ValueError('response analysis cannot conceal unavailable paired preparation with a selected subset')
    prefixes = tuple(checkpoints['original_readouts'][name] for name in MODELS)
    provisional = PreparationResponseAnalysis('analysis.preparation-response.pending', design, prefixes,
        tuple(checkpoints['centers'][key] for key in POSITIONS) if available else (),
        tuple(frames[name] for name in MODELS) if available else (),
        tuple(points[key] for key in sorted(points)), tuple(readouts[key] for key in sorted(readouts)),
        tuple(sorted(parents, key=lambda p: p.contribution_id)))
    analysis = replace(provisional, analysis_id='analysis.preparation-response.' + provisional.fingerprint())
    for center in analysis.centers:
        raw_operands['center.' + center.model_name + '.' + center.position] = checkpoints['center_bytes'][center.model_name, center.position]
    config = config_type(design)('config.response-assessment.' + analysis.fingerprint(), analysis, implementation_binding(project_root))
    # This is an explicit preliminary analysis of already exposed diagnostic
    # returns. No withheld native challenge is run or revealed here.
    assessment, _ = assess_analysis(analysis, raw_operands, assessor_source=config.assessor_source,
        assessment_id=capability_for(config) + '.assessment.' + analysis.fingerprint())
    return dict(config=config, draft=response_analysis_draft(config), binary=raw_operands, preliminary_assessment=assessment)


def retain_response_analysis_inputs(*, prepared, artifact_writer, output_dir):
    destination = Path(output_dir)
    if not destination.is_absolute() or destination.exists() or destination.is_symlink():
        raise ValueError('response assessment inputs need fresh absolute external custody')
    root = Path(artifact_writer.root.contract.canonical_path)
    relative = destination.relative_to(root).as_posix()
    config, binary = prepared['config'], prepared['binary']
    bindings = []
    for name, pin, media, size in binary_operands(config.analysis):
        raw = binary[name]
        if len(raw) != size or sha256(raw).hexdigest() != pin.object_fingerprint:
            raise ValueError('response analysis input changed before retention')
        key = external_id(config, name)
        path = relative + '/' + sha256(key.encode()).hexdigest() + ('.gz' if media == 'application/gzip' else '.bin')
        artifact_writer.write_stream(ArtifactStreamWriteRequest(pin.object_id, path, pin.object_schema,
            ArtifactProfile.RAW_SOURCE_BYTES, media, 'response-analysis.inputs.' + config.analysis.fingerprint(), relative,
            (raw[offset:offset + 2**20] for offset in range(0, size, 2**20)), maximum_bytes=size,
            maximum_chunk_bytes=min(size, 2**20), expected_size_bytes=size, expected_physical_sha256=pin.object_fingerprint,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
        bindings.append((key, root / path))
    return tuple(bindings)


def read_response_analysis(*, directory, artifact_writer):
    """Reconstruct the original assessment and every action without native work."""
    with artifact_writer.read_context() as writer, inquiry_projection_read(writer) as reading:
        return _read_response_analysis(directory=directory, artifact_writer=reading.writer, reading=reading)


def _read_response_analysis(*, directory, artifact_writer, reading):
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_inquiry import actual_products
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis_translation import selected_config
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_analysis import ACTION_SCHEMA
    from empirical_lawhood.storage.bounded_io import read_bounded_bytes
    def preflight(*, packet, draft, source):
        if selected_config(draft).implementation != source:
            raise ValueError('response assessment changes its original producing implementation')
    original = reading.wave(directory=directory, include_products=True, validate_authored=preflight)
    packet, draft, source, payloads = original.packet, original.draft, original.implementation, original.payloads
    config = selected_config(draft)
    report, products = original.report, original.products
    rows = actual_products(draft, products)
    if len(rows) != 1:
        raise ValueError('response assessment has no complete original publication')
    assessment = rows[0][2]
    binary = {}
    for name, pin, media, size, _, record in input_selections(config):
        suffix = '.json' if media == 'application/json' else '.gz' if media == 'application/gzip' else '.bin'
        key = external_id(config, name)
        raw = payloads['external-' + sha256(key.encode()).hexdigest()[:24] + suffix]
        if len(raw) != size or sha256(raw).hexdigest() != pin.object_fingerprint:
            raise ValueError('response assessment substitutes original complete direct inputs')
        if record is None:
            binary[name] = raw
        elif raw != record.canonical_bytes():
            raise ValueError('response assessment changes its original contributed readout')
    independently_assessed, arrays = assess_analysis(config.analysis, binary, assessor_source=config.assessor_source,
        assessment_id=assessment.assessment_id)
    if independently_assessed != assessment:
        raise ValueError('response assessment disagrees with independent original-array reconstruction')
    manifest, = [m for m in products['outputs'].values() if m.logical.payload_schema == ACTION_SCHEMA]
    artifact_writer.verify_manifest(manifest)
    raw = read_bounded_bytes(artifact_writer.root.resolve(manifest.materialization.relative_path, for_write=False),
        maximum_bytes=manifest.materialization.size_bytes)
    if sha256(raw).hexdigest() != manifest.materialization.physical_sha256 or raw != action_bytes(arrays):
        raise ValueError('response assessment substitutes its original complete action arrays')
    read_action_bytes(assessment, raw)
    return dict(packet=packet, draft=draft, source=source, config=config, report=report, products=products,
        assessment=assessment, action_arrays=arrays, action_manifest=manifest)
