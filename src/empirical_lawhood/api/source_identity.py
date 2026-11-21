# SPDX-License-Identifier: MPL-2.0
"""Compare existing source observations and declarations without admission."""

from dataclasses import dataclass
import json
from pathlib import Path

from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.numerical_provenance import authenticate_recorded_numerical_provenance, capture_numerical_provenance
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import validate_semantic_version, validate_stable_id
from empirical_lawhood.execution.executable_bindings import GeneratedExecutableBindingAggregate
from empirical_lawhood.execution.extension_bundles import GeneratedExtensionBundleAggregate


MAXIMUM_SELECTED_CAPABILITIES = 32
_MEMBERS = (
    ('provenance.json', NumericalProducingProvenance),
    ('discovery.json', GeneratedExtensionBundleAggregate),
    ('executables.json', GeneratedExecutableBindingAggregate),
)


@dataclass(frozen=True, slots=True)
class SourceIdentityObservation:
    """Diagnostic grouping of existing records; no custody or execution grant."""

    provenance: NumericalProducingProvenance
    discovery: GeneratedExtensionBundleAggregate | None = None
    executables: GeneratedExecutableBindingAggregate | None = None

    def __post_init__(self):
        authenticate_recorded_numerical_provenance(self.provenance)
        for record, expected in ((self.discovery, GeneratedExtensionBundleAggregate),
                (self.executables, GeneratedExecutableBindingAggregate)):
            if record is not None:
                if type(record) is not expected:
                    raise TypeError('identity observation requires exact static aggregate types')
                record.__post_init__()
        if self.discovery is not None and self.executables is not None:
            expected = ObjectIdentity.from_record(self.discovery.aggregate_id, self.discovery)
            if self.executables.discovery_aggregate != expected:
                raise ValueError('identity observation substitutes the executable discovery aggregate')

    def members(self):
        """Return existing canonical members for an explicitly selected directory."""
        result = []
        for (name, _), record in zip(_MEMBERS,
                (self.provenance, self.discovery, self.executables), strict=True):
            if record is not None:
                raw = record.canonical_bytes()
                result.append((name, raw))
        return tuple(result)


def observe_source_identity(*, project_root=None):
    """Reuse actual source observation and static declarations; build no provider."""
    from empirical_lawhood.adapters.composition.generated_executable_bindings import GENERATED_EXECUTABLE_BINDING_AGGREGATE
    from empirical_lawhood.execution.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE

    return SourceIdentityObservation(capture_numerical_provenance(project_root=project_root),
        GENERATED_EXTENSION_BUNDLE_AGGREGATE, GENERATED_EXECUTABLE_BINDING_AGGREGATE)


def read_source_identity(directory):
    """Decode bounded diagnostic copies, without claiming original-result custody."""
    records = []
    for name, record_type in _MEMBERS:
        path = Path(directory) / name
        if path.is_symlink():
            raise ValueError('identity observation refuses symbolic links')
        if not path.exists() and name != 'provenance.json':
            records.append(None)
            continue
        raw = read_bounded_bytes(path, maximum_bytes=None)
        records.append(decode_canonical_bytes(raw, record_type, maximum_bytes=None))
    return SourceIdentityObservation(*records)


def _change(before, after, *, observed=True):
    if not observed:
        status = 'UNKNOWN'
    elif before is None and after is None:
        status = 'ABSENT'
    elif before is None:
        status = 'ADDED'
    elif after is None:
        status = 'REMOVED'
    else:
        status = 'UNCHANGED' if before == after else 'CHANGED'
    return dict(status=status, before=before, after=after)


def _record_change(before, after, *, observed, details=False):
    result = _change(None if before is None else before.fingerprint(),
        None if after is None else after.fingerprint(), observed=observed)
    if details:
        result['declarations'] = dict(before=None if before is None else before.to_document(),
            after=None if after is None else after.to_document())
    return result


def _selected(snapshot, key):
    discovery = snapshot.discovery
    manifest = binding = executable = None
    if discovery is not None:
        try:
            manifest = discovery.capability_registry.resolve(*key)
        except KeyError:
            pass
        binding = discovery.binding(*key)
    if snapshot.executables is not None:
        executable = snapshot.executables.binding(*key)
    return manifest, binding, executable


def compare_source_identities(before, after, *, selected_capabilities=()):
    """Explain exact observed changes; never authorize execution, reads or science."""
    for snapshot in (before, after):
        if type(snapshot) is not SourceIdentityObservation:
            raise TypeError('identity comparison requires exact observations')
        snapshot.__post_init__()
    if (type(selected_capabilities) is not tuple or len(selected_capabilities) > MAXIMUM_SELECTED_CAPABILITIES
            or any(type(key) is not tuple or len(key) != 2 for key in selected_capabilities)):
        raise ValueError('identity comparison requires at most 32 distinct capability/version pairs')
    for key, version in selected_capabilities:
        validate_stable_id(key, field_name='selected capability')
        validate_semantic_version(version)
    if len(set(selected_capabilities)) != len(selected_capabilities):
        raise ValueError('identity comparison repeats a selected capability/version pair')
    old, new = before.provenance, after.provenance
    old_rows, new_rows = dict(old.package_sources), dict(new.package_sources)
    paths = tuple(sorted(old_rows.keys() | new_rows.keys()))
    changed_members = tuple(dict(path=path, **_change(old_rows.get(path), new_rows.get(path)))
        for path in paths if old_rows.get(path) != new_rows.get(path))
    old_runtime, new_runtime = json.loads(old.runtime_observation_json), json.loads(new.runtime_observation_json)
    runtime = {key: _change(old_runtime.get(key), new_runtime.get(key))
        for key in sorted(old_runtime.keys() | new_runtime.keys())}
    for key in runtime:
        if key not in old_runtime:
            runtime[key]['status'] = 'ADDED'
        elif key not in new_runtime:
            runtime[key]['status'] = 'REMOVED'
    selections = []
    for key in sorted(selected_capabilities):
        old_selected, new_selected = _selected(before, key), _selected(after, key)
        row = dict(capability_key=key[0], capability_version=key[1])
        for index, name in enumerate(('manifest', 'bundle_binding', 'executable')):
            observed = (before.executables is not None and after.executables is not None) if index == 2 else (
                before.discovery is not None and after.discovery is not None)
            row[name] = _record_change(old_selected[index], new_selected[index], observed=observed, details=True)
        selections.append(row)
    same_source = (old.code_sources_sha256, old.dependency_lock_sha256, old.observed_git_head,
        old.runtime_observation_json) == (new.code_sources_sha256, new.dependency_lock_sha256,
        new.observed_git_head, new.runtime_observation_json)
    static_complete = all(value is not None for value in (
        before.discovery, after.discovery, before.executables, after.executables))
    static_changed = any(left is not None and right is not None and left.fingerprint() != right.fingerprint()
        for left, right in ((before.discovery, after.discovery), (before.executables, after.executables)))
    pending = ('OBSERVED_CHANGE_KEEP_ORIGINAL_COMPATIBLE_INSTALLATION' if not same_source or static_changed else
        'ORDINARY_CURRENT_ADMISSION_REQUIRED' if static_complete else
        'INCOMPLETE_OBSERVATION_ORDINARY_CURRENT_ADMISSION_REQUIRED')
    return dict(report_kind='source-identity-comparison', report_version='1',
        authority='NONE', custody_authenticated=False, execution_admitted=False, qualification='NOT_ESTABLISHED',
        provenance=_record_change(old, new, observed=True),
        package=dict(**_change(old.code_sources_sha256, new.code_sources_sha256),
            before_member_count=len(old_rows), after_member_count=len(new_rows), changed_members=changed_members),
        dependency_lock=_change(old.dependency_lock_sha256, new.dependency_lock_sha256),
        source_commit=_change(old.observed_git_head, new.observed_git_head),
        checkout_clean_observation=_change(old.observed_checkout_clean, new.observed_checkout_clean),
        runtime=runtime,
        discovery_aggregate=_record_change(before.discovery, after.discovery,
            observed=before.discovery is not None and after.discovery is not None),
        executable_aggregate=_record_change(before.executables, after.executables,
            observed=before.executables is not None and after.executables is not None),
        selected_capabilities=tuple(selections),
        consequences=dict(new_execution='ORDINARY_CURRENT_SOURCE_AND_OPERAND_ADMISSION_REQUIRED',
            pending_execution=pending,
            retained_read='ORIGINAL_CUSTODY_SUPPORTED_REVISION_AND_CURRENT_ACCESS_REQUIRED',
            scientific_requalification='SEPARATE_PROTOCOL_EXPOSURE_UNCERTAINTY_AND_APPLICABILITY_REQUIRED'))
