# SPDX-License-Identifier: MPL-2.0
"""Registered programme composition over existing component execution services."""

from pathlib import Path

from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experiment_programme import (
    MAX_PROGRAMME_DESCRIPTOR_BYTES, PROGRAMME_DESCRIPTOR_FILENAME, ExperimentProgrammeDescriptor,
)

from .experiment_runtime_bindings import experiment_runtime_binding


def _descriptor_path(service, directory, *, for_write):
    directory = Path(directory)
    if not directory.is_absolute() or any(value.is_symlink() for value in (directory, *directory.parents)):
        raise ValueError("Programme directory requires an absolute path without symbolic links")
    root = Path(service.artifact_writer.root.contract.canonical_path)
    relative = (directory / PROGRAMME_DESCRIPTOR_FILENAME).relative_to(root).as_posix()
    return service.artifact_writer.root.resolve(relative, for_write=for_write)


def write_experiment_programme_descriptor(*, service, directory, descriptor):
    """Publish a new public selector outside every component's closed package."""
    from empirical_lawhood.api.configuration import _write_new_file

    if type(descriptor) is not ExperimentProgrammeDescriptor:
        raise TypeError("Programme selection requires its exact public descriptor")
    descriptor.__post_init__()
    _protocol_for_descriptor(descriptor)
    path = _descriptor_path(service, directory, for_write=True)
    _write_new_file(path, descriptor.canonical_bytes())


def _programme_factory(declaration):

    binding = experiment_runtime_binding(declaration)
    factory = None if binding is None else binding.programme_service_factory
    if not callable(factory):
        raise ValueError("Programme lacks its exact installed API composition")
    return factory


def _protocol_for_descriptor(descriptor):
    from .experiment_preparation import experiment_protocols

    declarations = tuple(value for value in experiment_protocols() if value.protocol_id == descriptor.protocol_id)
    if len(declarations) != 1:
        raise ValueError("Programme descriptor lacks one installed owning protocol")
    declaration, = declarations
    if (declaration.programme_record_type is None
            or (descriptor.specification.object_schema, descriptor.specification.object_version) !=
                (declaration.specification_type.SCHEMA, declaration.specification_type.VERSION)
            or (descriptor.programme.object_schema, descriptor.programme.object_version) !=
                (declaration.programme_record_type.SCHEMA, declaration.programme_record_type.VERSION)):
        raise ValueError("Programme descriptor changes its exact registered selection revisions")
    _programme_factory(declaration)
    return declaration


def selected_composite_programme_service(*, service, directory=None, preparation=None):
    """Resolve code-owned composition only; the owner authenticates its full state."""
    if directory is None and preparation is None:
        return None
    if directory is not None and preparation is not None:
        raise TypeError("Select one preparation or retained programme directory")
    descriptor = None
    if preparation is not None:
        from .experiment_preparation import _protocol

        preparation.__post_init__()
        if preparation.programme is None:
            return None
        declaration = _protocol(preparation.specification_record)
        if (declaration.programme_record_type is None
                or type(preparation.programme) is not declaration.programme_record_type):
            raise ValueError("Prepared programme substitutes its exact installed composition owner")
    else:
        # Absence selects the existing single-run route. A present malformed or
        # linked descriptor refuses; it must never fall back to another route.
        candidate = Path(directory) / PROGRAMME_DESCRIPTOR_FILENAME
        if not candidate.exists() and not candidate.is_symlink():
            return None
        path = _descriptor_path(service, directory, for_write=False)
        raw = read_bounded_bytes(path, maximum_bytes=MAX_PROGRAMME_DESCRIPTOR_BYTES)
        descriptor = decode_canonical_bytes(raw, ExperimentProgrammeDescriptor, maximum_bytes=MAX_PROGRAMME_DESCRIPTOR_BYTES)
        if raw != descriptor.canonical_bytes():
            raise ValueError("Programme descriptor requires exact canonical bytes")
        declaration = _protocol_for_descriptor(descriptor)
    selected = _programme_factory(declaration)(service=service, descriptor=descriptor)
    if any(not callable(getattr(selected, name, None)) for name in ("author", "run", "read", "recover")):
        raise TypeError("Registered programme factory lacks the complete public component lifecycle")
    return selected


def require_programme_source(project_root, snapshot, *, _admitted_source=None):
    """Authenticate operational parent selection; no issue or closure authority."""
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
    if (type(snapshot) is not ObjectIdentity or (snapshot.object_schema, snapshot.object_version) !=
            (RecursiveImplementationBinding.SCHEMA, RecursiveImplementationBinding.VERSION)):
        raise ValueError("new prospective component authoring requires its current operational implementation binding; retained common closures remain read-only")
    current = (implementation_binding(project_root) if _admitted_source is None else
        implementation_binding(project_root, _admitted_source=_admitted_source))
    if snapshot != ObjectIdentity.from_record("recursive-member.implementation", current):
        raise PermissionError("programme changes its selected current implementation")
    return current


def preflight_programme_source(project_root, snapshot):
    """Refuse inadmissible selected source before any new programme publication."""
    from empirical_lawhood.infrastructure.source_closure import (
        capture_admitted_target_source, require_admitted_target_source_current,
    )
    admitted = capture_admitted_target_source(Path(project_root))
    parent = require_programme_source(project_root, snapshot, _admitted_source=admitted)
    require_admitted_target_source_current(Path(project_root), admitted)
    require_programme_source(project_root, snapshot, _admitted_source=admitted)
    if admitted.implementation_commit != parent.observed_git_head:
        raise PermissionError("programme source changed before publication")
    return admitted


def component_source_snapshot(project_root, snapshot, prospective_spec_id, *, _admitted_source=None):
    """Capture the exact child closure expected by the existing prospective owner."""
    from empirical_lawhood.infrastructure.source_closure import (
        capture_admitted_target_source, capture_target_closure, require_admitted_target_source_current,
    )
    if _admitted_source is None:
        admitted = capture_admitted_target_source(Path(project_root))
    else:
        admitted = _admitted_source
        require_admitted_target_source_current(Path(project_root), admitted)
    parent = require_programme_source(project_root, snapshot, _admitted_source=admitted)
    captured = capture_target_closure(Path(project_root), prospective_spec_id + ".source-closure",
        _admitted_source=admitted)
    require_admitted_target_source_current(Path(project_root), admitted)
    require_programme_source(project_root, snapshot, _admitted_source=admitted)
    if captured.source.implementation_commit != parent.observed_git_head:
        raise PermissionError("prospective component source differs from its selected parent implementation")
    return ObjectIdentity.from_record("recursive-member.implementation", captured.closure)


def prepared_component_source_snapshot(project_root, preparation):
    """Use the actual prospective design owner; never infer its ID from a phase."""
    from .experiment_preparation import _protocol
    from empirical_lawhood.runtime.experiment_preparation import ExperimentPreparation
    from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs

    if type(preparation) is not ExperimentPreparation:
        raise TypeError("component source requires its exact typed preparation")
    preparation.__post_init__()
    if preparation.specification_record is None or preparation.execution is None:
        raise ValueError("component source requires its original specification and execution selection")
    declaration = _protocol(preparation.specification_record)
    if not declaration.requires_prospective_runtime_binding:
        raise ValueError("component source requires its declared prospective lifecycle")
    if preparation.prospective_spec is not None:
        design = RecursiveProspectiveDesignInputs.from_spec(preparation.prospective_spec)
    else:
        binding = experiment_runtime_binding(declaration)
        derive = None if binding is None else binding.derive_prospective_design_inputs
        if not callable(derive):
            raise ValueError("component source requires its installed prospective design owner")
        design = derive(preparation)
    if type(design) is not RecursiveProspectiveDesignInputs:
        raise TypeError("component source requires the exact prospective design inputs")
    design.__post_init__()
    if design.draft != preparation.draft:
        raise ValueError("component source design changes its original prepared scientific draft")
    return component_source_snapshot(project_root, preparation.execution.source_snapshot, design.spec_id)
