# SPDX-License-Identifier: MPL-2.0
"""Decode current locator selections through installed, code-owned projections.

Copied locators select no new authority. The owning operation authenticates
their immutable origin and reloads current grants at each access boundary.
"""
from pathlib import Path

from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


def _read_access_owners(protocol_id):
    from .generated_experiment_runtime_bindings import EXPERIMENT_RUNTIME_BINDINGS

    from empirical_lawhood.kernel.serialization import validate_stable_id

    validate_stable_id(protocol_id)
    bindings = EXPERIMENT_RUNTIME_BINDINGS
    if (type(bindings) is not tuple
            or any(type(binding) is not ExperimentRuntimeBinding for binding in bindings)
            or len({binding.protocol_id for binding in bindings}) != len(bindings)):
        raise ValueError('current access requires unambiguous installed protocol owners')
    selected = tuple(binding for binding in bindings if binding.protocol_id == protocol_id)
    if len(selected) != 1:
        raise ValueError('selected protocol has no current locator projection')
    owners = {}
    codecs = {}
    for binding in selected:
        if type(binding) is not ExperimentRuntimeBinding:
            raise TypeError('current access requires exact installed experiment bindings')
        binding.__post_init__()
        if not binding.read_access_record_types:
            continue
        callback = binding.select_read_access
        kinds = binding.read_access_record_types
        # Retaining the callback itself prevents identity reuse and keeps one
        # projection shared by several supported protocols unambiguous.
        previous = owners.get(id(callback))
        if previous is not None and (previous[0] is not callback or previous[1] != kinds):
            raise ValueError('current access projection repeats inconsistent locator codecs')
        owners[id(callback)] = (callback, kinds)
        for kind in kinds:
            key = (kind.SCHEMA, kind.VERSION)
            if key in codecs and codecs[key] is not kind:
                raise ValueError('current access locators disagree on their exact codec owner')
            codecs[key] = kind
    if not owners:
        raise ValueError('selected protocol has no current locator projection')
    return tuple(owners.values()), codecs


def load_experiment_read_access(paths, *, protocol_id):
    """Load one complete homogeneous selection of existing canonical locators.

    The explicit selected protocol owns the closed locator projection.
    The shared closed authoring codec permits edited JSON/YAML copies without
    accepting another root schema, revision, Python import or permission body.
    No artifact or authority store is opened here.
    """
    from .codecs import load_registered_authoring

    if type(paths) not in (tuple, list) or not paths:
        raise ValueError('current access requires an explicit nonempty locator file selection')
    owners, codecs = _read_access_owners(protocol_id)
    selected_paths = tuple(Path(path) for path in paths)
    for path in selected_paths:
        if '..' in path.parts or any(member.is_symlink() for member in (path, *path.parents)):
            raise ValueError('current access locator paths refuse symbolic links and parent traversal')
    if len({path.absolute() for path in selected_paths}) != len(selected_paths):
        raise ValueError('current access repeats a locator file')
    records = tuple(load_registered_authoring(path, root_schemas=codecs) for path in selected_paths)
    matching = tuple(callback for callback, kinds in owners
        if all(type(record) in kinds for record in records))
    if len(matching) != 1:
        raise ValueError('current access locators mix or ambiguously select installed owners')
    selected = matching[0](records)
    if (selected is None or type(selected) in (bool, int, float, str, bytes, tuple, list, dict, set)
            or isinstance(selected, CanonicalRecord)):
        raise TypeError('current access projection must return its operation-local selection, not a permission result')
    return selected


def _protocol_for_specification_pin(pin):
    from empirical_lawhood.api.generated_experiment_runtime_bindings import EXPERIMENT_SPECIFICATION_PROTOCOLS
    from empirical_lawhood.kernel.provenance import ObjectIdentity

    if type(pin) is not ObjectIdentity:
        raise TypeError('current access requires an exact specification identity')
    pin.__post_init__()
    protocols = tuple(protocol for schema, version, protocol in EXPERIMENT_SPECIFICATION_PROTOCOLS
        if (schema, version) == (pin.object_schema, pin.object_version))
    if len(protocols) != 1:
        raise ValueError('current access lacks one exact retained specification owner')
    return protocols[0]


def _require_specification_member(member, intrinsic):
    """Join transport custody to the record's intrinsic scientific identity.

    Recursive packets name this fixed member by its transport role. That
    alias does not replace the specification's intrinsic ID in the instance.
    Protocol selection opens neither the scientific body nor its siblings;
    the lifecycle reader still authenticates the exact member bytes and ID.
    """
    pin = member.identity
    if (pin.object_id not in (intrinsic.object_id, 'recursive-member.experiment-specification')
            or (pin.object_schema, pin.object_version, pin.object_fingerprint) !=
                (intrinsic.object_schema, intrinsic.object_version, intrinsic.object_fingerprint)):
        raise PermissionError('current access substitutes its exact packet-pinned specification')


def experiment_read_access_protocol(*, specification_path=None, directory=None, artifact_writer=None):
    """Select a protocol before locator copies or protected sibling bodies.

    A copied specification is editable input. Retained selection uses only the
    exact intrinsic packet, instance and association metadata and their pins;
    the actual lifecycle still authenticates all scientific bytes and grants.
    """
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
    from empirical_lawhood.runtime.prospective_experiment import (
        ASSOCIATION_FILENAME, INSTANCE_FILENAME, SPECIFICATION_FILENAME,
        ProspectiveExperimentAssociation, instance_identity,
    )
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave

    if (specification_path is None) == (directory is None):
        raise ValueError('current access requires exactly one selected specification or retained directory')
    if specification_path is not None:
        from .experiment_preparation import _protocol, load_experiment_specification
        protocol_id = _protocol(load_experiment_specification(Path(specification_path))).protocol_id
    else:
        if artifact_writer is None:
            raise ValueError('retained current access requires the actual selected artifact plane')
        from .prospective_experiment import _directory, _read_prospective_locator
        from empirical_lawhood.infrastructure.recursive_custody import read_recursive_bootstrap_record

        selected = _directory(directory, artifact_writer)
        association_path = selected / 'experiment' / ASSOCIATION_FILENAME
        packet_path = selected / 'authored-wave.json'
        prospective = association_path.exists() or association_path.is_symlink()
        development = packet_path.exists() or packet_path.is_symlink()
        if prospective == development:
            raise ValueError('current access requires one ordinary retained lifecycle, not a composite or mixed directory')
        if prospective:
            companion = _directory(selected / 'experiment', artifact_writer)
            association = _read_prospective_locator(companion, ASSOCIATION_FILENAME, artifact_writer,
                ProspectiveExperimentAssociation)
            members = {member.filename: member for member in association.members}
            instance = _read_prospective_locator(companion, INSTANCE_FILENAME, artifact_writer,
                ExperimentInstanceBinding, expected=members[INSTANCE_FILENAME])
            if instance_identity(instance) != association.instance:
                raise PermissionError('current access substitutes its exact retained instance/specification association')
            _require_specification_member(members[SPECIFICATION_FILENAME], instance.specification)
            packet = _read_prospective_locator(_directory(selected / 'prospective', artifact_writer),
                'authored-wave.json', artifact_writer, AuthoredRecursiveWave)
            if ObjectIdentity.from_record(packet.packet_id, packet) != association.prospective_wave:
                raise PermissionError('current access substitutes its exact association-pinned packet')
        else:
            root = Path(artifact_writer.root.contract.canonical_path)
            packet = read_recursive_bootstrap_record(artifact_writer,
                packet_path.relative_to(root).as_posix(), AuthoredRecursiveWave)
            members = {member.filename: member for member in packet.members}
            member = members.get(INSTANCE_FILENAME)
            if member is None or SPECIFICATION_FILENAME not in members:
                raise PermissionError('current access omits its exact packet-pinned instance/specification')
            instance = read_recursive_bootstrap_record(artifact_writer,
                (selected / INSTANCE_FILENAME).relative_to(root).as_posix(), ExperimentInstanceBinding,
                maximum_bytes=member.size_bytes, expected=member)
            _require_specification_member(members[SPECIFICATION_FILENAME], instance.specification)
        if packet.draft != instance.draft:
            raise PermissionError('current access substitutes its original packet/instance draft')
        protocol_id = _protocol_for_specification_pin(instance.specification)
    # Unsupported protocol refusal precedes any access-locator body open.
    _read_access_owners(protocol_id)
    return protocol_id
