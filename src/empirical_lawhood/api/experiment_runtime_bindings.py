# SPDX-License-Identifier: MPL-2.0
"""Static API compositions for declared prospective runtime requirements."""

from empirical_lawhood.runtime.experiment_preparation import ExperimentProtocolDeclaration, ExperimentRuntimeBinding
from types import MappingProxyType


_installed_bindings_index = None


def _binding_index(bindings):
    """Index one exact immutable installed declaration tuple; never authority."""
    global _installed_bindings_index
    validator = ExperimentRuntimeBinding.__post_init__
    cached = _installed_bindings_index
    if cached is not None and cached[0] is bindings and cached[1] is validator:
        return cached[2]
    if (type(bindings) is not tuple or any(type(row) is not ExperimentRuntimeBinding for row in bindings)
            or len({row.protocol_id for row in bindings}) != len(bindings)):
        raise ValueError("installed experiment runtime bindings have inconsistent owning declarations")
    for row in bindings:
        row.__post_init__()
    index = MappingProxyType({row.protocol_id: row for row in bindings})
    _installed_bindings_index = bindings, validator, index
    return index


def experiment_runtime_binding(protocol):
    from empirical_lawhood.api.generated_experiment_runtime_bindings import EXPERIMENT_RUNTIME_BINDINGS

    if type(protocol) is not ExperimentProtocolDeclaration:
        raise TypeError("experiment runtime selection requires its exact installed protocol declaration")
    protocol.__post_init__()
    selected = _binding_index(EXPERIMENT_RUNTIME_BINDINGS).get(protocol.protocol_id)
    if selected is None:
        if protocol.requires_prospective_runtime_binding or protocol.requires_development_runtime_binding or protocol.programme_record_type is not None:
            raise ValueError("SOFTWARE: experiment lacks its installed runtime composition")
        return None
    return _validate_selected_pair(protocol, selected)


def validate_experiment_runtime_binding(protocol, binding):
    """One static generator/runtime contract; callbacks grant no lifecycle."""
    if type(protocol) is not ExperimentProtocolDeclaration or type(binding) is not ExperimentRuntimeBinding:
        raise TypeError('experiment API composition requires exact installed declarations')
    protocol.__post_init__()
    binding.__post_init__()
    return _validate_selected_pair(protocol, binding)


def _validate_selected_pair(protocol, binding):
    """Contextual lifecycle requirements are checked at every selection."""
    if binding.protocol_id != protocol.protocol_id:
        raise ValueError('experiment API composition changes its owning protocol')
    required = (protocol.requires_prospective_runtime_binding or protocol.requires_development_runtime_binding
        or protocol.programme_record_type is not None)
    if not required and (any(value is not None for value in (binding.bind_handoff, binding.bind_development_runtime,
            binding.prepare_authoring, binding.read_result, binding.programme_service_factory))
            or not any(callable(value) for value in (binding.derive_inputs, binding.export_products, binding.read_development_result))):
        raise ValueError('ordinary API composition cannot select a different lifecycle')
    if (protocol.requires_prospective_runtime_binding and not callable(binding.bind_handoff)
            or protocol.requires_development_runtime_binding and not callable(binding.bind_development_runtime)
            or protocol.programme_record_type is not None and not callable(binding.programme_service_factory)
            or protocol.programme_record_type is None and binding.programme_service_factory is not None):
        raise ValueError("SOFTWARE: experiment runtime composition does not support its declared lifecycle")
    if any(value is not None for value in (binding.read_development_result, binding.complete_development_result,
            binding.validate_development_read_access, binding.validate_authoring_read_access,
            binding.bootstrap_development_input_access)) and (
            protocol.requires_prospective_runtime_binding or protocol.programme_record_type is not None):
        raise ValueError("development scientific read requires an ordinary development lifecycle")
    if (binding.bootstrap_authoring_input_access is not None
            and protocol.requires_prospective_runtime_binding
            and binding.bootstrap_prospective_input_access is None):
        raise ValueError('prospective authoring access requires its exact prospective bootstrap owner')
    if binding.derive_prospective_design_inputs is not None and not protocol.requires_prospective_runtime_binding:
        raise ValueError('prospective design derivation requires its declared prospective lifecycle')
    if binding.bootstrap_prospective_input_access is not None and not protocol.requires_prospective_runtime_binding:
        raise ValueError('prospective bootstrap cannot select a development or composite lifecycle')
    if any(kind not in protocol.input_record_types for kind in binding.prospective_bootstrap_record_types):
        raise ValueError('prospective bootstrap locator codec differs from its declared input owner')
    if any(kind not in protocol.input_record_types for kind in binding.development_bootstrap_record_types):
        raise ValueError('development bootstrap locator codec differs from its exact declared input owner')
    if binding.specification_schema is not None and binding.specification_schema != protocol.specification_type.SCHEMA:
        raise ValueError("scientific read schema differs from its exact owning protocol")
    return binding


def bootstrap_selected_experiment_inputs(*, declaration, specification, selection,
        read_record, artifact_writer, read_access=None, selection_path=None):
    """Read only selected locator metadata before the ordinary input loader.

    The installed domain owns the exact locator joins and current permission.
    A selected path, declared identity or returned guard creates no authority.
    """
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputSelection

    if type(specification) is not declaration.specification_type:
        raise TypeError('selected input bootstrap changes its exact installed specification owner')
    if type(selection) not in (ExperimentInputSelection, ExperimentFileInputSelection):
        raise TypeError('selected input bootstrap requires its exact closed source selector')
    selection.__post_init__()
    if selection.protocol_id != declaration.protocol_id:
        raise ValueError('selected input bootstrap changes its installed protocol')
    binding = experiment_runtime_binding(declaration)
    callback = None if binding is None else binding.bootstrap_selected_input_access
    if callback is None:
        if read_access is not None:
            raise ValueError('selected experiment has no current-access bootstrap for copied inputs')
        return None
    locator_types = (binding.prospective_bootstrap_record_types
        if declaration.requires_prospective_runtime_binding else binding.development_bootstrap_record_types)
    locator_codecs = {(kind.SCHEMA, kind.VERSION) for kind in locator_types}
    if artifact_writer is None and (getattr(selection, 'files', ()) or any(
            (row.identity.object_schema, row.identity.object_version) not in locator_codecs
            for row in selection.bindings)):
        raise PermissionError('protected copied inputs require their actual selected artifact writer')
    selected = {row.key: row for row in selection.bindings}

    def read_locator(key, reference, kind):
        if artifact_writer is None:
            raise PermissionError('protected copied inputs require their actual selected artifact writer')
        row = selected.get(key)
        if (row is None or type(reference) is not ObjectIdentity or row.identity != reference
                or kind not in locator_types
                or (reference.object_schema, reference.object_version) != (kind.SCHEMA, kind.VERSION)):
            raise PermissionError('selected input bootstrap refuses an undeclared locator key, identity or codec')
        return read_record(row, kind)

    guard = callback(specification=specification, selection=selection, read_locator=read_locator,
        artifact_writer=artifact_writer, read_access=read_access, selection_path=selection_path)
    if not callable(guard):
        raise TypeError('selected input bootstrap requires its code-owned current-access guard')
    if guard() is not None:
        raise ValueError('selected input access guard must return None or raise on refusal')
    return guard


def authenticate_experiment_instance(*, declaration, specification, allocation,
        draft, source_records, artifact_writer):
    """Validate the actual instance with its code-owned scientific/custody owner.

    A shared immutable scientific operand may live in an authenticated external
    publication. Its API composition resolves that publication within this
    invocation; inward declarations never gain a filesystem resolver.
    """
    if declaration.validate_instance is None:
        raise ValueError("authored experiment lacks its registered scientific instance validator")
    binding = experiment_runtime_binding(declaration)
    callback = None if binding is None else binding.authenticate_instance
    arguments = dict(specification=specification, allocation=allocation,
        draft=draft, source_records=source_records)
    if callback is None:
        result = declaration.validate_instance(**arguments)
    else:
        if artifact_writer is None:
            raise ValueError("experiment instance requires its actual publication custody")
        result = callback(**arguments, artifact_writer=artifact_writer)
    if result is not None:
        raise ValueError("experiment instance validator must return None or raise on refusal")


def bootstrap_authored_development_inputs(*, directory, artifact_writer, packet, read_record, read_access=None):
    """Select a closed locator owner before opening protected authored bodies.

    Only packet/instance pins and an installed specification type select code.
    The supplied reader authenticates one exact packet member; the domain gets
    a narrower reader limited to its declared locator-only input codecs.
    """
    from empirical_lawhood.api.experiment_preparation import experiment_protocols
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
    from empirical_lawhood.runtime.prospective_experiment import source_filename

    names = {value.filename for value in packet.members}
    required = {'experiment-instance.json', 'experiment-specification.json'}
    if not names.intersection(required):
        return None
    if not required.issubset(names):
        raise ValueError('authored development bootstrap omits its exact experiment companion')
    instance = read_record('experiment-instance.json', ExperimentInstanceBinding)
    if instance.draft != packet.draft:
        raise PermissionError('development bootstrap substitutes its exact packet-bound draft')
    declarations = tuple(value for value in experiment_protocols()
        if (value.specification_type.SCHEMA, value.specification_type.VERSION) == (
            instance.specification.object_schema, instance.specification.object_version))
    if len(declarations) != 1:
        raise ValueError('development bootstrap lacks one exact installed specification owner')
    declaration, = declarations
    binding = experiment_runtime_binding(declaration)
    if binding is None or binding.bootstrap_development_input_access is None:
        return None
    specification = read_record('experiment-specification.json', declaration.specification_type)
    if specification.identity != instance.specification:
        raise PermissionError('development bootstrap changes its actual instance-bound specification')

    def read_member(reference, kind):
        if (type(reference) is not ObjectIdentity or reference not in instance.sources
                or kind not in binding.development_bootstrap_record_types
                or (reference.object_schema, reference.object_version) != (kind.SCHEMA, kind.VERSION)):
            raise PermissionError('development bootstrap refuses an undeclared locator member')
        record = read_record(source_filename(reference), kind)
        if ObjectIdentity.from_record(reference.object_id, record) != reference:
            raise PermissionError('development bootstrap changes its exact original locator identity')
        return record

    access = binding.bootstrap_development_input_access(directory=directory, artifact_writer=artifact_writer,
        specification=specification, instance=instance, packet=packet, read_member=read_member,
        read_access=read_access)
    if (access is None or type(getattr(access, 'parents', None)) is not tuple
            or not callable(getattr(access, 'require_current', None))
            or not callable(getattr(access, 'require_member', None))
            or not callable(getattr(access, 'record_parents', None))):
        raise TypeError('development bootstrap requires its code-owned original input access context')
    if access.require_current() is not None:
        raise ValueError('original input access guard must return None or raise on refusal')
    return access


def original_input_record_publication(*, record, original_input_access, inherited_parents=()):
    """Exact input ancestry and ordinary inherited labels; no authority inference."""
    from empirical_lawhood.runtime.artifacts import derived_outcome_access, inherited_visibility
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    parents = (() if original_input_access is None else original_input_access.record_parents(record))
    if inherited_parents:
        parents = inherited_parents
    # Model-bearing immutable inputs preserve SEALED ancestry under the
    # existing derivation policy. Intrinsic locator metadata stays blind.
    declared_access = OutcomeAccess.DEVELOPMENT_VISIBLE if parents else OutcomeAccess.OUTCOME_BLIND
    declared_visibility = VisibilityCeiling.DEVELOPMENT_ONLY if parents else VisibilityCeiling.PROSPECTIVE
    access = derived_outcome_access(declared_access, *(value.outcome_access for value in parents))
    visibility = inherited_visibility((declared_visibility,
        *(value.visibility_ceiling for value in parents)), access)
    return parents, access, visibility
