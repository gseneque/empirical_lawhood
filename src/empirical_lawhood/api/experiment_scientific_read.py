# SPDX-License-Identifier: MPL-2.0
"""Dispatch retained scientific reads without compiling current domain source."""

from empirical_lawhood.api.experiment_runtime_bindings import _binding_index

def read_prepared_experiment_science(*, selected, artifact_writer, run_id, reveal_authority_id=None, allow_partial=False,
        assess_incomplete=False, read_access=None):
    """Use a code-owned read projection selected by the original retained schema.

    The retained experiment loader owns authentication of the original companion.
    A domain reader owns current outcome authority, receipts and scientific bytes.
    Static dispatch performs no current operation discovery or source compilation.
    """
    from empirical_lawhood.api.generated_experiment_runtime_bindings import (
        EXPERIMENT_RUNTIME_BINDINGS, EXPERIMENT_SPECIFICATION_PROTOCOLS,
    )
    if type(assess_incomplete) is not bool or allow_partial and assess_incomplete:
        raise ValueError('incomplete assessment and metadata-only partial inspection are distinct selections')

    bindings = _binding_index(EXPERIMENT_RUNTIME_BINDINGS)
    pin = selected.instance.specification
    protocols = tuple(protocol for schema, version, protocol in EXPERIMENT_SPECIFICATION_PROTOCOLS
        if (schema, version) == (pin.object_schema, pin.object_version))
    if len(protocols) != 1:
        raise ValueError("retained experiment lacks one exact installed specification revision")
    reader = bindings.get(protocols[0])
    if reader is None or reader.specification_schema != pin.object_schema or not callable(reader.read_result):
        if assess_incomplete:
            raise ValueError('selected scientific reader does not support incomplete assessment')
        return None
    options = {}
    original_access = getattr(selected, "original_input_access", None)
    if read_access is not None and original_access is None:
        raise ValueError("prospective scientific read lacks its registered original-access scope")
    if original_access is not None:
        if original_access.require_current() is not None:
            raise ValueError("original input access must return None or raise")
        if read_access is not None:
            options["read_access"] = read_access
    if assess_incomplete:
        if not reader.supports_incomplete_assessment:
            raise ValueError('selected scientific reader does not support incomplete assessment')
        options['assess_incomplete'] = True

    result = reader.read_result(selected=selected, artifact_writer=artifact_writer,
        run_id=run_id, reveal_authority_id=reveal_authority_id, allow_partial=allow_partial, **options)
    if original_access is not None and original_access.require_current() is not None:
        raise ValueError("original input access must return None or raise")
    return result


def read_prepared_development_science(*, directory, artifact_writer, payloads, report,
        products, draft, plan, allow_partial=False, read_access=None):
    """Dispatch once over the common owner's actual authenticated DEV context.

    The authored loader already validates the complete companion, source roster
    and scientific projection. This seam decodes only the small original
    instance/specification required to select an exact installed reader. It
    never calls domain preparation, recompiles or reloads a packet/plan, reads
    products, or substitutes partial access for the caller's explicit choice.
    """
    if type(allow_partial) is not bool:
        raise TypeError("development scientific read requires an explicit partial-custody selection")
    original_input_access = getattr(payloads, 'original_input_access', None)
    if original_input_access is not None:
        original_input_access.require_current()
    selected = _development_runtime_context(payloads=payloads, draft=draft,
        callback_name="read_development_result")
    if selected is None:
        if read_access is not None:
            raise ValueError("development access selection requires its declared scientific read owner")
        return None
    binding, specification, instance = selected
    options = {}
    if read_access is not None:
        if not callable(binding.validate_development_read_access):
            raise ValueError("selected development reader does not support an operational access selection")
        options["read_access"] = read_access
    result = binding.read_development_result(directory=directory, artifact_writer=artifact_writer,
        specification=specification, instance=instance, payloads=payloads, report=report,
        products=products, draft=draft, plan=plan, allow_partial=allow_partial, **options)
    if original_input_access is not None:
        original_input_access.require_current()
    return result


def validate_prepared_development_read_access(*, directory, artifact_writer, payloads, draft, plan, read_access):
    """Check an explicit current access selection before opening scientific inputs.

    The exact installed owner authenticates current permission. No verdict or
    authority object escapes this operation-local preflight.
    """
    original_input_access = getattr(payloads, 'original_input_access', None)
    if read_access is None and original_input_access is None:
        return
    if original_input_access is not None:
        original_input_access.require_current()
    selected = _development_runtime_context(payloads=payloads, draft=draft,
        callback_name="read_development_result")
    if selected is None or not callable(selected[0].validate_development_read_access):
        raise ValueError("selected development reader does not support an operational access selection")
    binding, specification, instance = selected
    result = binding.validate_development_read_access(directory=directory, artifact_writer=artifact_writer,
        specification=specification, instance=instance, payloads=payloads, draft=draft, plan=plan,
        read_access=read_access)
    if result is not None:
        raise ValueError("development access validator must return None or raise on refusal")


def complete_prepared_development_science(*, directory, artifact_writer, project_root,
        maximum_parallel_tasks, payloads, draft, plan, scheduler_result, read_access=None):
    """Produce declared PURE results after actual acquisition, before full read.

    The existing execution owner supplies its original authenticated context.
    The callback authenticates actual terminal custody and creates no new native
    entry, issue, qualification or outcome-access authority.
    """
    original_input_access = getattr(payloads, 'original_input_access', None)
    if original_input_access is not None:
        original_input_access.require_current()
    selected = _development_runtime_context(payloads=payloads, draft=draft,
        callback_name="complete_development_result")
    if selected is None:
        return None
    binding, specification, instance = selected
    options = {}
    if read_access is not None:
        if not callable(binding.validate_development_read_access):
            raise ValueError("selected development completion does not support an operational access selection")
        options["read_access"] = read_access
    result = binding.complete_development_result(directory=directory, artifact_writer=artifact_writer,
        project_root=project_root, maximum_parallel_tasks=maximum_parallel_tasks,
        specification=specification, instance=instance, payloads=payloads, draft=draft, plan=plan,
        scheduler_result=scheduler_result, **options)
    if original_input_access is not None:
        original_input_access.require_current()
    return result


def _development_runtime_context(*, payloads, draft, callback_name):
    """Select one exact ordinary owner from the original public companion."""
    from empirical_lawhood.adapters.composition.generated_extension_bundles import EXPERIMENT_PROTOCOL_DECLARATIONS
    from empirical_lawhood.api.generated_experiment_runtime_bindings import (
        EXPERIMENT_RUNTIME_BINDINGS, EXPERIMENT_SPECIFICATION_PROTOCOLS,
    )
    from empirical_lawhood.api.experiment_runtime_bindings import validate_experiment_runtime_binding
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding, ExperimentProtocolDeclaration

    required = {"experiment-specification.json", "experiment-instance.json"}
    present = required.intersection(payloads)
    if not present:
        return None
    if present != required:
        raise ValueError("development scientific read omits an original experiment companion")
    raw = payloads["experiment-instance.json"]
    instance = decode_canonical_bytes(raw, ExperimentInstanceBinding, maximum_bytes=len(raw))
    pin = instance.specification
    protocols = tuple(protocol for schema, version, protocol in EXPERIMENT_SPECIFICATION_PROTOCOLS
        if (schema, version) == (pin.object_schema, pin.object_version))
    if len(protocols) != 1:
        raise ValueError("retained experiment lacks one exact installed specification revision")
    reader = _binding_index(EXPERIMENT_RUNTIME_BINDINGS).get(protocols[0])
    if reader is None or reader.specification_schema != pin.object_schema or not callable(getattr(reader, callback_name)):
        return None
    if (type(EXPERIMENT_PROTOCOL_DECLARATIONS) is not tuple
            or any(type(row) is not ExperimentProtocolDeclaration for row in EXPERIMENT_PROTOCOL_DECLARATIONS)):
        raise ValueError("installed development specification codecs have inconsistent owning declarations")
    declarations = tuple(row for row in EXPERIMENT_PROTOCOL_DECLARATIONS if row.protocol_id == protocols[0]
        and (row.specification_type.SCHEMA, row.specification_type.VERSION) == (pin.object_schema, pin.object_version))
    if len(declarations) != 1:
        raise ValueError("retained experiment lacks one exact installed development specification codec")
    declaration, = declarations
    binding = validate_experiment_runtime_binding(declaration, reader)

    raw = payloads["experiment-specification.json"]
    specification = decode_canonical_bytes(raw, declaration.specification_type, maximum_bytes=len(raw))
    if (specification.identity != pin or instance.draft != ObjectIdentity.from_record(draft.draft_id, draft)
            or instance.campaign != ObjectIdentity.from_record(draft.campaign.campaign_id, draft.campaign)):
        raise ValueError("development scientific read changes its original specification/draft/campaign association")
    return binding, specification, instance
