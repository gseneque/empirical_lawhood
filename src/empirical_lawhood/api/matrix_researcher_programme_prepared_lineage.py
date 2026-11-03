# SPDX-License-Identifier: MPL-2.0
"""Current produced DEV and account joins, with original C kept immutable."""
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes


def _development_record_identity(record):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_results import MatrixRevisionProgrammeAssessment
    if type(record) is MatrixRevisionProgrammeAssessment:
        return ObjectIdentity.from_record(record.record_id, record)
    return record.identity


def retained_development_product(context, phase, kind, *, locator_type):
    return retained_development_products(context, phase, (kind,), locator_type=locator_type)[0]


def retained_development_products(context, phase, kinds, *, locator_type):
    """Join complete original DEV custody to all requested producer locators.

    This read establishes receipt/byte correspondence, not another scientific
    result. The phase observation and consumers retain their owning scientific
    validations; E5 nomination also joins its full assessment and receipt.
    """
    from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_retained_roots
    kinds = tuple(kinds)
    if not kinds or len({kind.SCHEMA for kind in kinds}) != len(kinds):
        raise ValueError('programme DEV needs a nonempty distinct product schema roster')
    directory = context.child_directory(phase)
    if phase == 'e4.revision':
        from empirical_lawhood.api.selected_e4_revision_programme import COMPONENT_DIRECTORY
        directory = directory / COMPONENT_DIRECTORY
    with context.writer.read_context() as writer:
        result, roots = _read_recursive_wave_with_retained_roots(directory=directory,
            artifact_writer=writer, include_products=True, terminal_product_format='compact',
            _scientific_consumer=lambda **_: None)
        report, products, draft, plan = result
        packet, original, _, run, actual_plan, _ = roots
        observed = context.report(phase)
        if (draft != original or plan != actual_plan
                or observed.get('run_id') != run.run_plan_id
                or observed.get('execution_plan_sha256') != plan.fingerprint()
                or report.get('run_id') != run.run_plan_id):
            raise PermissionError('programme DEV product substitutes its original authored instance/run/plan')
        return tuple(_retained_development_locator(context, writer, directory, kind, locator_type,
            packet, run, plan, products) for kind in kinds)


def _retained_development_locator(context, writer, directory, kind, locator_type, packet, run, plan, products):
    from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4DevelopmentProduct
    rows = tuple(row for row in products['product_index'] if row['schema'] == kind.SCHEMA)
    if len(rows) != 1:
        raise ValueError('programme DEV needs one exact original ' + kind.SCHEMA)
    row, = rows
    receipt = products['receipts'].get(row['task_id'])
    if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED:
        raise PermissionError('programme DEV product lacks its actual successful producing receipt')
    logical, = (value for value in receipt.output_logical_artifacts
        if value.logical_artifact_id == row['logical_artifact_id'])
    material, = (value for value in receipt.output_materializations
        if value.logical_artifact_id == logical.logical_artifact_id)
    manifest = writer.read_manifest(material.relative_path)
    writer.verify_manifest(manifest)
    if (manifest.logical, manifest.materialization) != (logical, material):
        raise PermissionError('programme DEV substitutes original product publication custody')
    raw = read_bounded_bytes(writer.root.resolve(material.relative_path, for_write=False),
        maximum_bytes=context.plan.specification.operations.metadata_budget.source_scan_bytes)
    record = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    if record.canonical_bytes() != raw or record.fingerprint() != logical.content_sha256:
        raise PermissionError('programme DEV substitutes original canonical product bytes')
    publication = _publication_from_manifest(writer, manifest)
    pin = _development_record_identity(record)
    relative = directory.relative_to(writer.root.contract.canonical_path).as_posix()
    plan_pin = ObjectIdentity.from_record(plan.execution_plan_id, plan)
    receipt_pin = ObjectIdentity.from_record(receipt.receipt_id, receipt)
    if locator_type is SelectedE4DevelopmentProduct:
        return locator_type(pin, relative, run.run_plan_id, plan_pin, row['task_id'], receipt_pin, publication)
    return locator_type('binding.programme.' + record.fingerprint(), relative,
        ObjectIdentity.from_record(packet.packet_id, packet), ObjectIdentity.from_record(run.run_plan_id, run),
        plan_pin, run.run_plan_id, row['task_id'], receipt_pin, logical.logical_artifact_id, pin, publication)


def programme_development_product(context, phase):
    if phase != 'e5.development':
        raise ValueError('prepared development locator requires the actual selected E5 DEV phase')
    if context.design.downstream_account == 'ORIGINAL_E3':
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.science import MatrixPreparationNomination
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_development_product import MatrixSelectedDevelopmentProduct
        return retained_development_product(context, phase, MatrixPreparationNomination,
            locator_type=MatrixSelectedDevelopmentProduct)
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_results import MatrixRevisionProgrammeAssessment
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_development_product import MatrixRevisionDevelopmentProduct
    return retained_development_product(context, phase, MatrixRevisionProgrammeAssessment,
        locator_type=MatrixRevisionDevelopmentProduct)


def programme_development_nomination(context):
    """Read the complete original assessment without requiring a favourable result.

    The ordinary DEV scientific reader replays every assigned input and terminal
    reduction. Join that typed read to the original receipted publication before
    projecting either a nominee or conditional scientific nonentry.
    """
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.science import MatrixPreparationNomination
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_results import MatrixRevisionProgrammeAssessment
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
    from .matrix_programme_decisions import development_assessment
    science = development_assessment(context)
    account = context.design.downstream_account
    if account not in ('ORIGINAL_E3', 'REVISION'):
        raise ValueError('programme nomination changes its frozen D account')
    kind = MatrixPreparationNomination if account == 'ORIGINAL_E3' else MatrixRevisionProgrammeAssessment
    raw = canonical_json_document_bytes(science['assessment'])
    result = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    locator = programme_development_product(context, 'e5.development')
    functional = result if account == 'ORIGINAL_E3' else result.functional
    expected_custody = {'receipt': locator.receipt.to_document(),
        'logical_artifact': locator.publication.logical.to_document(),
        'materialization': locator.publication.materialization.to_document()}
    custody = science.get('custody')
    if (type(functional) is not MatrixPreparationNomination or _development_record_identity(result) != locator.record
            or science.get('nomination_disposition') != functional.disposition
            or type(science.get('assigned_groups')) is not int or type(science.get('assigned_cases')) is not int
            or science.get('assigned_groups') != len(functional.development_unit_ids)
            or len(functional.development_unit_ids) != context.design.e5_development.expected_groups
            or science.get('assigned_cases') != len(functional.cases)
            or not isinstance(custody, dict) or custody.get('assessment') != expected_custody):
        raise PermissionError('programme nomination substitutes its original assessment, complete census or receipt custody')
    return functional.disposition


def require_current_account(context, phase, specification, inputs):
    """No revision/original fallback and no alternate original C are accepted."""
    if phase.startswith(('e5.', 'e6')):
        account = context.design.downstream_account
        if phase in ('e5.development', 'e5.confirmation', 'e6') and specification.account != account:
            raise PermissionError('programme prepared phase changes the original D account')
        # Initialization and source-computability records are different
        # current contracts, with no scientific account field. Their actual
        # prepared programme and original-C operands carry that join instead.
        if phase in ('e5.source', 'e6.source'):
            from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import MatrixRevisionPreparedProgramme
            programme = inputs.prepared_programme
            if (type(programme) is MatrixRevisionPreparedProgramme) != (account == 'REVISION'):
                raise PermissionError('programme prepared source changes the original D account')
        request = getattr(inputs, 'request', None)
        if phase in ('e5.initialize-development', 'e5.initialize-confirmation', 'e6.initialize'):
            request, _ = inputs
        if request is None:
            selection = getattr(inputs, 'selection', None)
            request = None if selection is None else selection.request
        if phase in ('e5.source', 'e6.source') and request is not None:
            if request.input_commitments != context.plan.specification.input_commitments:
                raise PermissionError('programme prepared source changes the original C publication')
        if request is not None and hasattr(request, 'original_commitments'):
            if request.original_commitments.input_commitments != context.plan.specification.input_commitments:
                raise PermissionError('programme prepared phase changes the original C publication')
            if hasattr(request, 'revision') and (request.revision is None) != (account == 'ORIGINAL_E3'):
                raise PermissionError('programme prepared operands mix original and revision accounts')
