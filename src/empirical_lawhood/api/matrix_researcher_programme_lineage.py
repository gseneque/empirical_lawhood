# SPDX-License-Identifier: MPL-2.0
"""Exact original C/phase/package joins for the current result-derived runner."""
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixProgrammePhaseBinding, MatrixProgrammeRunBinding
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity


def read_published_record(writer, relative, kind, maximum_bytes):
    from .retained_e3_evidence import current_e3_evidence, retained_e3_reader
    writer = retained_e3_reader(writer)
    manifest = writer.read_manifest(relative)
    if manifest.logical.payload_schema != kind.SCHEMA or manifest.materialization.compression != 'none':
        raise PermissionError('Matrix programme changes exact retained canonical publication custody')
    retained = current_e3_evidence(writer)
    if retained is not None and writer is retained.writer:
        # The original owner verifies this manifest and its complete current
        # closure on every read; only immutable typed construction is shared.
        return retained.reader.read_control(manifest, kind, maximum_bytes)
    from empirical_lawhood.infrastructure.canonical_record_read import read_verified_canonical_record
    return read_verified_canonical_record(writer, manifest, kind, maximum_bytes=maximum_bytes)


def authenticate_phase_binding(context, binding):
    from empirical_lawhood.api.experiment_preparation import load_experiment_specification, _protocol
    from empirical_lawhood.infrastructure.publication_metadata import consume_published_materializations
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection
    if (type(binding) is not MatrixProgrammePhaseBinding or binding.programme != context.plan.identity):
        raise PermissionError('Matrix phase substitutes its actual original programme')
    binding.__post_init__()
    writer = context.writer

    def consume(members):
        # One authenticated complete roster preserves every original handle.
        # A singular check per handle would reopen all atomic siblings each time.
        for publication in binding.publications:
            manifest = members[publication.materialization.relative_path]
            if (manifest.logical, manifest.materialization) != (publication.logical, publication.materialization):
                raise PermissionError('Matrix phase substitutes an original derivation publication')
        path = writer.root.resolve(binding.specification.relative_path, for_write=False)
        raw = read_bounded_bytes(path, maximum_bytes=binding.specification.maximum_bytes)
        specification = load_experiment_specification(path)
        if (specification.identity != binding.specification.identity or specification.canonical_bytes() != raw
                or _protocol(specification).protocol_id != binding.protocol_id):
            raise PermissionError('Matrix phase substitutes its actual current target specification')
        sources = writer.root.resolve(binding.sources.relative_path, for_write=False)
        raw = read_bounded_bytes(sources, maximum_bytes=binding.sources.maximum_bytes)
        selector = decode_canonical_bytes(raw, ExperimentFileInputSelection, maximum_bytes=binding.sources.maximum_bytes)
        if (raw != selector.canonical_bytes() or selector.protocol_id != binding.protocol_id
                or ObjectIdentity.from_record(selector.selection_id, selector) != binding.sources.identity):
            raise PermissionError('Matrix phase substitutes its actual current source selector')
        return path, specification

    # The closed publication owner rechecks bytes, sidecars, markers, paths and
    # current access after selector consumption, before any result can escape.
    return consume_published_materializations(writer, binding.publications, consume=consume)


def run_binding_relative(context, phase, component_id=None):
    name = phase + '.' + (component_id or 'main') + '.json'
    return (context.directory / 'runs' / name).relative_to(context.writer.root.contract.canonical_path).as_posix()


def retained_run_binding(context, phase, component_id=None):
    relative = run_binding_relative(context, phase, component_id)
    path = context.writer.root.resolve(relative, for_write=False)
    if not path.exists() and not path.is_symlink():
        return None
    value = read_published_record(context.writer, relative, MatrixProgrammeRunBinding, 1024**2)
    if (value.programme != context.plan.identity or value.phase != phase
            or value.component_id != (component_id or 'main')):
        raise PermissionError('Matrix run locator changes the exact retained phase/component')
    return value


def select_programme_authority(context, phase, *, component_id=None):
    """Match explicit real packages by the actual authored child candidate.

    Selection is not execution permission. The ordinary child still performs
    current issue, execution, source, resource, parent and reveal validation.
    """
    from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammePrerequisite
    directory = context.child_directory(phase)
    if component_id is not None:
        directory = directory / 'components' / component_id
    selected, api = context.service._prospective_context(directory, maximum_parallel_tasks=context.plan.workers,
        lifecycle='read')
    retained = retained_run_binding(context, phase, component_id)
    authorities = () if context.operation is None else context.operation.authorities
    if retained is not None and not any(row.package_path == retained.authority.package_path for row in authorities):
        authorities = (*authorities, retained.authority)
    matches = []
    for authority in authorities:
        package, run, plan = api._compile_path(context.writer.root.resolve(authority.package_path, for_write=False))
        candidate = ObjectIdentity.from_record(package.issued_study.candidate.candidate_id, package.issued_study.candidate)
        if candidate == selected.association.candidate:
            matches.append((authority, package, run, plan))
    if not matches:
        raise MatrixProgrammePrerequisite(phase, 'ISSUED_PACKAGE_AND_CURRENT_REVEAL_REQUIRED',
            'Select the actual issued child package and genuine reveal authority for ' + phase
            + ('' if component_id is None else '/' + component_id))
    if len(matches) != 1:
        raise PermissionError('Matrix operation ambiguously selects multiple issued runs for one original child')
    authority, package, run, plan = matches[0]
    if retained is not None and (retained.run_id != run.run_plan_id
            or retained.package != ObjectIdentity.from_record(package.package_id, package)
            or retained.specification != selected.instance.specification):
        raise PermissionError('Matrix operation cannot replace an original selected run/package or replay native work')
    return selected, api, authority, package, run, plan


def programme_original_product(context, phase, schema):
    """Use the ordinary source reader's actual authenticated prior locators."""
    if phase in ('e4.calibration', 'e4.confirmation'):
        return _issued_e4_product(context, phase, schema)
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
    from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
    report = context.report(phase)
    science = report.get('scientific_result', report)
    rows = tuple(decode_canonical_bytes(canonical_json_document_bytes(row), RecursivePriorExecutionBinding,
        maximum_bytes=1024**2) for row in science.get('prior_executions', ()))
    values = tuple(row for row in rows if row.record.object_schema == schema)
    if len(values) != 1:
        raise ValueError('Matrix phase lacks its unique original authenticated producer: ' + phase + '/' + schema)
    selected, _, _, package, run, plan = context.authority(phase)
    value, = values
    if (value.run_id != run.run_plan_id or value.execution_plan != ObjectIdentity.from_record(plan.execution_plan_id, plan)
            or value.package != ObjectIdentity.from_record(package.package_id, package)
            or selected.instance.specification != context.binding(phase).specification.identity):
        raise PermissionError('Matrix prior producer changes its actual selected source phase/run/plan')
    return value


def _issued_e4_product(context, phase, schema):
    """Capture an exact CAL/CONF product inside its ordinary live tail reader."""
    return _issued_e4_record(context, phase, schema)[1]


def _issued_e4_record(context, phase, schema):
    """Read the actual typed product and its original locator in one live scope."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as methods
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_preparation import ASSESSMENT_COMPONENT_ID
    from empirical_lawhood.api.selected_e4_native_read import _read_selected_e4_component
    from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
    allowed = {'e4.calibration': methods.SelectedE4Calibration,
        'e4.confirmation': methods.SelectedE4DownstreamNomination}
    kind = allowed[phase]
    if schema != kind.SCHEMA:
        raise ValueError('Matrix issued product changes its actual selected CAL/CONF scientific role')
    selected, _, authority, _, run, _ = context.authority(phase, ASSESSMENT_COMPONENT_ID)
    def consume(*, writer, package, plan, entry, receipts, products, reveal):
        rows = tuple((value, receipt, logical) for value, receipt, logical in products if type(value) is kind)
        if len(rows) != 1:
            raise PermissionError('Matrix issued phase lacks its unique actual original scientific product')
        record, receipt, logical = rows[0]
        prior = RecursivePriorExecutionBinding('binding.programme.' + record.fingerprint(),
            ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study),
            ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority),
            ObjectIdentity.from_record(package.package_id, package),
            ObjectIdentity.from_record(plan.execution_plan_id, plan), run.run_plan_id, receipt.task_id,
            ObjectIdentity.from_record(receipt.receipt_id, receipt), logical.logical_artifact_id, record.identity,
            record_id_field='record_id')
        return record, MatrixSelectedOriginalProduct(prior, ObjectIdentity.from_record(reveal.authority_id, reveal))
    return _read_selected_e4_component(selected=selected, artifact_writer=context.writer,
        run_id=run.run_plan_id, reveal_authority_id=authority.reveal_authority_id, consume_tail=consume)
