"""Generate the explicit static executable-binding and codec aggregate module."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib
import json
from pathlib import Path
from typing import Sequence

from empirical_lawhood.execution.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE
from empirical_lawhood.science.records.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.execution.study_issue import StudyExtensionDecoderRegistration
from empirical_lawhood.execution.executable_bindings import ExecutableBindingContribution, ExecutableCapabilityProviderFactoryRegistry, GeneratedExecutableBindingAggregate, compose_executable_binding_aggregate
from empirical_lawhood.execution.static_codecs import CanonicalRecordCodecRegistration, CanonicalRecordCodecRegistry

from empirical_lawhood.execution.extensions import descriptor_projection, projection_expression


try:
    from ._descriptor_discovery import (
        discover_descriptors as _discover_descriptors,
        module_name,
        require_safe_output,
    )
except ImportError:  # Explicit script invocation outside the checkout.
    from _descriptor_discovery import (
        discover_descriptors as _discover_descriptors,
        module_name,
        require_safe_output,
    )


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "src/empirical_lawhood"
ALLOWLISTED_ROOTS = (
    PACKAGE_ROOT / "methods",
    PACKAGE_ROOT / "domains",
    PACKAGE_ROOT / "adapters",
)
OUTPUT = PACKAGE_ROOT / "adapters/composition/generated_executable_bindings.py"
DECLARATIONS_OUTPUT = PACKAGE_ROOT / "execution/generated_executable_declarations.py"
RECURSIVE_OUTPUT = PACKAGE_ROOT / "adapters/composition/generated_recursive_operations.py"
DESCRIPTOR_NAME = "extension.py"
CONTRIBUTION_SYMBOL = "EXECUTABLE_BINDING_CONTRIBUTION"
FACTORIES_SYMBOL = "EXECUTABLE_BINDING_FACTORIES"
RECORD_TYPES_SYMBOL = "EXECUTABLE_RECORD_TYPES"


@dataclass(frozen=True, slots=True)
class LoadedExecutableDescriptor:
    path: Path
    module_name: str
    contribution: ExecutableBindingContribution
    factories: tuple[object, ...]
    record_types: tuple[type[CanonicalRecord], ...]


def _module_name(path: Path) -> str:
    return module_name(path, package_root=PACKAGE_ROOT)


def discover_descriptors() -> tuple[Path, ...]:
    """Discover one static owner per extension without a registration census."""
    paths = tuple(path for name in (DESCRIPTOR_NAME,)
        for path in _discover_descriptors(package_root=PACKAGE_ROOT,
            roots=ALLOWLISTED_ROOTS, name=name, kind="extension"))
    parents = [path.parent for path in paths]
    if len(parents) != len(set(parents)):
        raise ValueError("one extension cannot declare both unified and explicit projections")
    return tuple(sorted(paths))


def load_descriptors(paths: tuple[Path, ...]) -> tuple[LoadedExecutableDescriptor, ...]:
    loaded: list[LoadedExecutableDescriptor] = []
    for path in paths:
        module_name = _module_name(path)
        module = importlib.import_module(module_name)
        contribution = descriptor_projection(module, CONTRIBUTION_SYMBOL)
        factories = descriptor_projection(module, FACTORIES_SYMBOL)
        record_types = descriptor_projection(module, RECORD_TYPES_SYMBOL)
        if contribution is None and not factories and not record_types:
            continue  # A declaration may own only static scientific profiles.
        if not isinstance(contribution, ExecutableBindingContribution):
            raise ValueError(f"executable descriptor omits {CONTRIBUTION_SYMBOL}: {path}")
        if not isinstance(factories, tuple):
            raise ValueError(f"executable descriptor omits {FACTORIES_SYMBOL}: {path}")
        if not isinstance(record_types, tuple) or any(
            not isinstance(value, type) or not issubclass(value, CanonicalRecord)
            for value in record_types
        ):
            raise ValueError(f"executable descriptor omits {RECORD_TYPES_SYMBOL}: {path}")
        loaded.append(
            LoadedExecutableDescriptor(
                path=path,
                module_name=module_name,
                contribution=contribution,
                factories=factories,
                record_types=record_types,
            )
        )
    ordered = tuple(sorted(loaded, key=lambda value: value.contribution.contribution_id))
    contribution_ids = tuple(value.contribution.contribution_id for value in ordered)
    if tuple(sorted(set(contribution_ids))) != contribution_ids:
        raise ValueError("executable descriptors contain duplicate contribution IDs")
    return ordered


def _codec_registrations(
    descriptors: tuple[LoadedExecutableDescriptor, ...],
    aggregate: GeneratedExecutableBindingAggregate,
) -> tuple[
    tuple[CanonicalRecordCodecRegistration, ...],
    tuple[CanonicalRecordCodecRegistration, ...],
    tuple[type[CanonicalRecord], ...],
]:
    record_types = tuple(
        sorted(
            (record_type for descriptor in descriptors for record_type in descriptor.record_types),
            key=lambda value: (value.SCHEMA, value.VERSION),
        )
    )
    record_keys = tuple((value.SCHEMA, value.VERSION) for value in record_types)
    if tuple(sorted(set(record_keys))) != record_keys:
        raise ValueError("executable descriptors duplicate an exact canonical record schema/revision owner")
    all_decoders = tuple(
        sorted(
            (
                registration
                for binding in aggregate.bindings
                for registration in binding.issued_decoder_registrations
            ),
            key=lambda value: (value.payload_schema, value.payload_version, value.decoder_key, value.decoder_version),
        )
    )
    by_decoder_key: dict[tuple[str, str], StudyExtensionDecoderRegistration] = {}
    for decoder in all_decoders:
        previous = by_decoder_key.setdefault((decoder.decoder_key, decoder.decoder_version), decoder)
        if previous != decoder:
            raise ValueError("executable bindings conflict on an exact issued decoder key/version")
    if set(record_keys) != {(value.payload_schema, value.payload_version) for value in by_decoder_key.values()}:
        raise ValueError("executable record types differ from issued decoder schema/revisions")
    by_record = {(value.SCHEMA, value.VERSION): value for value in record_types}
    primary_decoders = {}
    for descriptor in descriptors:
        for record_type in descriptor.record_types:
            owned = {(decoder.decoder_key, decoder.decoder_version): decoder
                for binding in descriptor.contribution.bindings
                for decoder in binding.issued_decoder_registrations
                if (decoder.payload_schema, decoder.payload_version) == (record_type.SCHEMA, record_type.VERSION)}
            if len(owned) != 1:
                raise ValueError("canonical record owner lacks its unique issued decoder registration")
            primary_decoders[record_type.SCHEMA, record_type.VERSION] = next(iter(owned.values()))

    def registration(decoder, *, primary):
        codec_id = "executable-canonical-json." + decoder.payload_schema.replace("/", ".").replace("_", "-")
        if decoder.payload_version != '1.0.0':
            codec_id += '.revision-' + decoder.payload_version
        if not primary:
            codec_id += ".decoder-" + decoder.fingerprint()
        return CanonicalRecordCodecRegistration(
            codec_id=codec_id,
            record_schema=decoder.payload_schema,
            record_version=decoder.payload_version,
            maximum_bytes=decoder.maximum_payload_bytes,
            decoder_key=decoder.decoder_key,
            decoder_version=decoder.decoder_version,
            decoder_implementation_sha256=decoder.implementation_sha256,
        )
    registrations = tuple(registration(primary_decoders[key], primary=True) for key in record_keys)
    additional = tuple(sorted(
        (registration(decoder, primary=False) for decoder in by_decoder_key.values()
            if decoder != primary_decoders[decoder.payload_schema, decoder.payload_version]),
        key=lambda value: value.codec_id,
    ))
    for value in (*registrations, *additional):
        record_type = by_record[value.record_schema, value.record_version]
        if record_type.VERSION != value.record_version:
            raise ValueError("executable codec record version differs from its decoder")
    CanonicalRecordCodecRegistry(
        registry_id="canonical-codecs.generated-executable-bindings",
        registrations=registrations,
        record_types=by_record,
        additional_registrations=additional,
    )
    return registrations, additional, record_types


def compose_loaded_descriptors(
    descriptors: tuple[LoadedExecutableDescriptor, ...],
) -> tuple[
    GeneratedExecutableBindingAggregate,
    ExecutableCapabilityProviderFactoryRegistry,
    tuple[CanonicalRecordCodecRegistration, ...],
    tuple[type[CanonicalRecord], ...],
]:
    contributions = tuple(value.contribution for value in descriptors)
    aggregate = compose_executable_binding_aggregate(
        contributions,
        discovery_aggregate=GENERATED_EXTENSION_BUNDLE_AGGREGATE,
    )
    factories = tuple(
        sorted(
            (factory for descriptor in descriptors for factory in descriptor.factories),
            key=lambda value: value.binding.binding_id,  # type: ignore[attr-defined]
        )
    )
    factory_registry = ExecutableCapabilityProviderFactoryRegistry(
        aggregate=aggregate,
        factories=factories,  # type: ignore[arg-type]
    )
    codec_registrations, _additional, record_types = _codec_registrations(descriptors, aggregate)
    return aggregate, factory_registry, codec_registrations, record_types


def _render_codec_registration(value: CanonicalRecordCodecRegistration) -> str:
    return "\n".join(
        (
            "    CanonicalRecordCodecRegistration(",
            f"        codec_id={json.dumps(value.codec_id)},",
            f"        record_schema={json.dumps(value.record_schema)},",
            f"        record_version={json.dumps(value.record_version)},",
            f"        maximum_bytes={value.maximum_bytes},",
            f"        decoder_key={json.dumps(value.decoder_key)},",
            f"        decoder_version={json.dumps(value.decoder_version)},",
            "        decoder_implementation_sha256="
            f"{json.dumps(value.decoder_implementation_sha256)},",
            "    ),",
        )
    )


def render_executable_modules(paths: tuple[Path, ...]) -> tuple[str, str]:
    """Generate one static binding aggregate and bind its executable owners to the same contributions."""
    descriptors = load_descriptors(paths)
    aggregate, _factories, codec_registrations, _record_types = compose_loaded_descriptors(
        descriptors
    )
    _primary, additional_registrations, _types = _codec_registrations(descriptors, aggregate)
    aliases = {
        value.contribution.contribution_id: f"_descriptor_{index:03d}"
        for index, value in enumerate(descriptors)
    }
    imports: list[str] = []
    for descriptor in descriptors:
        alias = aliases[descriptor.contribution.contribution_id]
        module = importlib.import_module(descriptor.module_name)
        for symbol, suffix in ((CONTRIBUTION_SYMBOL, "contribution"),
                               (FACTORIES_SYMBOL, "factories"),
                               (RECORD_TYPES_SYMBOL, "record_types")):
            imports.extend(projection_expression(module, symbol, alias + "_" + suffix))
    contribution_values = ",\n".join(
        f"    {aliases[value.contribution.contribution_id]}_contribution" for value in descriptors
    )
    factory_values = ",\n".join(
        f"                *{aliases[value.contribution.contribution_id]}_factories"
        for value in descriptors
    )
    record_type_values = ",\n".join(
        f"            *{aliases[value.contribution.contribution_id]}_record_types"
        for value in descriptors
    )
    codec_values = "\n".join(_render_codec_registration(value) for value in codec_registrations)
    additional_codec_values = "\n".join(_render_codec_registration(value) for value in additional_registrations)
    codec_fingerprint = hashlib.sha256(canonical_json_bytes(codec_registrations)).hexdigest()
    additional_codec_fingerprint = hashlib.sha256(canonical_json_bytes(additional_registrations)).hexdigest()
    static_rows = []
    for descriptor in descriptors:
        payload = descriptor.contribution.canonical_bytes()
        static_rows.append(f"    decode_canonical_bytes({payload!r}, ExecutableBindingContribution, maximum_bytes={len(payload)}),")
    declarations = "\n".join((
        '"""Generated executable declaration data for static discovery."""',
        "from empirical_lawhood.execution.executable_bindings import ExecutableBindingContribution, compose_executable_binding_aggregate",
        "from empirical_lawhood.execution.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE",
        "from empirical_lawhood.science.records.decoding import decode_canonical_bytes",
        "", "EXECUTABLE_BINDING_CONTRIBUTIONS = (", *static_rows, ")", "",
        "GENERATED_EXECUTABLE_BINDING_AGGREGATE = compose_executable_binding_aggregate(",
        "    EXECUTABLE_BINDING_CONTRIBUTIONS, discovery_aggregate=GENERATED_EXTENSION_BUNDLE_AGGREGATE,",
        ")", "",
        f'EXPECTED_AGGREGATE_FINGERPRINT = "{aggregate.fingerprint()}"',
        "if GENERATED_EXECUTABLE_BINDING_AGGREGATE.fingerprint() != EXPECTED_AGGREGATE_FINGERPRINT:",
        '    raise RuntimeError("generated executable aggregate fingerprint drifted")', "",
    ))
    executable = "\n".join(
        (
            '"""Generated by scripts/generate_executable_binding_aggregate.py; do not edit."""',
            "",
            "import hashlib",
            "from typing import cast",
            "",
            "from empirical_lawhood.execution.generated_executable_declarations import (",
            "    EXECUTABLE_BINDING_CONTRIBUTIONS as _STATIC_CONTRIBUTIONS,",
            "    EXPECTED_AGGREGATE_FINGERPRINT,",
            "    GENERATED_EXECUTABLE_BINDING_AGGREGATE,",
            ")",
            "from empirical_lawhood.science.records.serialization import canonical_json_bytes",
            "from empirical_lawhood.execution.executable_bindings import (",
            "    ExecutableCapabilityProviderFactoryRegistry,",
            "    ExecutableFactory,",
            ")",
            "from empirical_lawhood.execution.static_codecs import (",
            "    CanonicalRecordCodecRegistration,",
            "    CanonicalRecordCodecRegistry,",
            ")",
            *imports,
            "",
            "EXECUTABLE_BINDING_CONTRIBUTIONS = (",
            f"{contribution_values},",
            ")",
            "",
            "if EXECUTABLE_BINDING_CONTRIBUTIONS != _STATIC_CONTRIBUTIONS:",
            '    raise RuntimeError("installed executable declarations differ from static discovery")',
            "_EXECUTABLE_FACTORIES: tuple[ExecutableFactory, ...] = tuple(",
            "    sorted(",
            "        cast(",
            "            tuple[ExecutableFactory, ...],",
            "            (",
            f"{factory_values},",
            "            ),",
            "        ),",
            "        key=lambda value: value.binding.binding_id,",
            "    )",
            ")",
            "EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY = ExecutableCapabilityProviderFactoryRegistry(",
            "    aggregate=GENERATED_EXECUTABLE_BINDING_AGGREGATE,",
            "    factories=_EXECUTABLE_FACTORIES,",
            ")",
            "",
            "EXECUTABLE_RECORD_TYPES = tuple(",
            "    sorted(",
            "        (",
            f"{record_type_values},",
            "        ),",
            "        key=lambda value: (value.SCHEMA, value.VERSION),",
            "    )",
            ")",
            "_EXECUTABLE_CODEC_REGISTRATIONS = (",
            f"{codec_values}",
            ")",
            "_EXECUTABLE_ADDITIONAL_CODEC_REGISTRATIONS = (",
            f"{additional_codec_values}",
            ")",
            "EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY = CanonicalRecordCodecRegistry(",
            '    registry_id="canonical-codecs.generated-executable-bindings",',
            "    registrations=_EXECUTABLE_CODEC_REGISTRATIONS,",
            "    record_types={(value.SCHEMA, value.VERSION): value for value in EXECUTABLE_RECORD_TYPES},",
            "    additional_registrations=_EXECUTABLE_ADDITIONAL_CODEC_REGISTRATIONS,",
            ")",
            "",
            "EXPECTED_CODEC_REGISTRY_FINGERPRINT = (",
            f'    "{codec_fingerprint}"',
            ")",
            "EXPECTED_ADDITIONAL_CODEC_REGISTRY_FINGERPRINT = (",
            f'    "{additional_codec_fingerprint}"',
            ")",
            "if (",
            "    hashlib.sha256(canonical_json_bytes(_EXECUTABLE_CODEC_REGISTRATIONS)).hexdigest()",
            "    != EXPECTED_CODEC_REGISTRY_FINGERPRINT",
            "):",
            '    raise RuntimeError("generated executable codec registry fingerprint drifted")',
            "if (",
            "    hashlib.sha256(canonical_json_bytes(_EXECUTABLE_ADDITIONAL_CODEC_REGISTRATIONS)).hexdigest()",
            "    != EXPECTED_ADDITIONAL_CODEC_REGISTRY_FINGERPRINT",
            "):",
            '    raise RuntimeError("generated additional executable codec registry fingerprint drifted")',
            "",
            "__all__ = [",
            '    "EXECUTABLE_BINDING_CONTRIBUTIONS",',
            '    "EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY",',
            '    "EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY",',
            '    "EXECUTABLE_RECORD_TYPES",',
            '    "EXPECTED_AGGREGATE_FINGERPRINT",',
            '    "EXPECTED_CODEC_REGISTRY_FINGERPRINT",',
            '    "EXPECTED_ADDITIONAL_CODEC_REGISTRY_FINGERPRINT",',
            '    "GENERATED_EXECUTABLE_BINDING_AGGREGATE",',
            "]",
            "",
        )
    )
    return declarations, executable


def _symbol_location(value):
    module, name = value.__module__, value.__qualname__
    if not module.startswith('empirical_lawhood.') or any(not part.isidentifier() for part in name.split('.')):
        raise ValueError('generated recursive selections require importable code-owned symbols')
    actual = importlib.import_module(module)
    for part in name.split('.'):
        actual = getattr(actual, part)
    if actual is not value:
        raise ValueError('generated recursive symbol differs from its actual module owner')
    return module, name


def render_recursive_index(paths: tuple[Path, ...]) -> str:
    """Project the existing validated owners without constructing runners/providers."""
    from empirical_lawhood.execution.capabilities import CapabilityRegistry
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
    from empirical_lawhood.execution.recursive_provider import RecursiveOperationProviderFactory
    from empirical_lawhood.storage.contracts.recursive_record_codecs import input_record_type_census
    from empirical_lawhood.storage.contracts.recursive_storage_codecs import storage_codec_census
    descriptors = load_descriptors(paths)
    compose_loaded_descriptors(descriptors)
    operations, factories, codecs, output_selections = [], [], {}, []
    for descriptor in descriptors:
        for factory in descriptor.factories:
            if not isinstance(factory, RecursiveOperationProviderFactory):
                continue
            factories.append(factory)
            operations.append((factory.registration.selection.selection_id, descriptor.module_name,
                factory.binding.binding_id, factory.binding.fingerprint(), factory.manifest.fingerprint()))
            for schema, kind in factory.output_codecs.items():
                if schema != kind.SCHEMA or codecs.setdefault((schema, kind.VERSION), kind) is not kind:
                    raise ValueError('registered recursive factories disagree on a strict output codec for an exact schema/revision')
            selection = factory.registration.selection
            output_selections.extend((selection.capability_key, selection.capability_version,
                selection.implementation_sha256, output.payload_schema, factory.output_codecs[output.payload_schema].VERSION)
                for output in factory.registration.outputs if output.profile is ArtifactProfile.CANONICAL_JSON)
    operations.sort()
    if len({row[0] for row in operations}) != len(operations):
        raise ValueError('generated recursive operations repeat an exact selection')
    registrations = tuple(factory.registration for factory in factories)
    inputs = input_record_type_census(registrations, legacy_codecs=codecs)
    storage = storage_codec_census(registrations)
    registry = CapabilityRegistry('recursive-inquiry.registered-operations',
        tuple(sorted((factory.manifest for factory in factories), key=lambda row: row.registry_id)))
    output_rows = tuple((schema, version, *_symbol_location(kind)) for (schema, version), kind in sorted(codecs.items()))
    input_rows = tuple((kind.SCHEMA, kind.VERSION, *_symbol_location(kind)) for kind in inputs)
    storage_rows = tuple((codec.codec_id, codec.payload_schema, codec.record_version, codec.profile.value,
        codec.media_type, codec.filename_suffix, *_symbol_location(codec.validate_stream),
        codec.maximum_bytes, codec.allow_empty)
        for codec in storage)
    lines = ['"""Generated by scripts/generate_executable_binding_aggregate.py; do not edit."""', '',
        '# Static keys and exact manifests only; no domain modules are imported here.',
        f'REGISTRY_BYTES = {registry.canonical_bytes()!r}', f'REGISTRY_SHA256 = {registry.fingerprint()!r}', '']
    for name, rows in (('OPERATIONS', tuple(operations)), ('OUTPUT_RECORD_TYPES', output_rows),
                       ('OUTPUT_CODEC_SELECTIONS', tuple(sorted(set(output_selections)))),
                       ('INPUT_RECORD_TYPES', input_rows), ('STORAGE_CODECS', storage_rows)):
        lines.extend((name + ' = (', *(f'    {row!r},' for row in rows), ')', ''))
    return '\n'.join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated output drifts")
    arguments = parser.parse_args(argv)
    paths = discover_descriptors()
    declarations, executable = render_executable_modules(paths)
    outputs = ((DECLARATIONS_OUTPUT, declarations.encode("utf-8")),
        (OUTPUT, executable.encode("utf-8")),
        (RECURSIVE_OUTPUT, render_recursive_index(paths).encode("utf-8")))
    for path, expected in outputs:
        require_safe_output(path, package_root=PACKAGE_ROOT)
        if arguments.check:
            if not path.is_file() or path.read_bytes() != expected:
                raise SystemExit("generated executable binding aggregate or recursive index is missing or stale")
        else:
            path.write_bytes(expected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
