"""Generate the explicit static backbone-extension aggregate module."""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from typing import Sequence

from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, compose_extension_bundle_aggregate
from empirical_lawhood.execution.experiment_preparation import ExperimentProtocolDeclaration, ExperimentRuntimeBinding
from empirical_lawhood.execution.workflow_descriptors import WorkflowDeclaration
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration, EnvironmentDeclaration
from empirical_lawhood.execution.installation_descriptors import WorkflowInstallationDeclaration

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
OUTPUT = PACKAGE_ROOT / "execution/generated_extension_bundles.py"
PROTOCOL_OUTPUT = PACKAGE_ROOT / "api/generated_experiment_protocols.py"
DESCRIPTOR_NAME = "extension.py"
SYMBOL_NAME = "EXTENSION_BUNDLE_CONTRIBUTION"
API_BINDING_ROOT = PACKAGE_ROOT / "api/domain_composition"
API_BINDING_OUTPUT = PACKAGE_ROOT / "api/generated_experiment_runtime_bindings.py"
APPLICATION_PRESENTATION_OUTPUT = PACKAGE_ROOT / "api/generated_application_presentations.py"
WORKFLOW_OUTPUT = PACKAGE_ROOT / "adapters/composition/generated_workflows.py"
PUBLIC_FACET_OUTPUT = PACKAGE_ROOT / "adapters/composition/generated_public_facets.py"


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


def discover_public_facets() -> tuple[Path, ...]:
    """Legacy and shared owners can declare facts without inventing a capability."""
    paths = _discover_descriptors(package_root=PACKAGE_ROOT,
        roots=(PACKAGE_ROOT / "adapters", PACKAGE_ROOT / "methods", PACKAGE_ROOT / "domains", API_BINDING_ROOT),
        name="*public_facets.py", kind="public discovery facet")
    return tuple(path for path in paths if path != PUBLIC_FACET_OUTPUT)


def load_contributions(
    paths: tuple[Path, ...],
) -> tuple[ExtensionBundleContribution, ...]:
    contributions = []
    for path in paths:
        module = importlib.import_module(_module_name(path))
        contribution = descriptor_projection(module, SYMBOL_NAME)
        if not isinstance(contribution, ExtensionBundleContribution):
            raise ValueError(f"extension descriptor omits {SYMBOL_NAME}: {path}")
        contributions.append(contribution)
    ordered = tuple(sorted(contributions, key=lambda value: value.contribution_id))
    compose_extension_bundle_aggregate(ordered)
    return ordered


def render_generated_module(paths: tuple[Path, ...]) -> str:
    """Freeze validated descriptor data without importing executable owners on read.

    The authoritative EXTENSION declarations are still loaded and validated by
    this generator. Runtime decodes exact canonical records and checks the same
    aggregate fingerprint; it does not build unrelated provider factories.
    """
    contributions = load_contributions(paths)
    aggregate = compose_extension_bundle_aggregate(contributions)
    rows = ["    decode_canonical_bytes(" + repr(value.canonical_bytes())
            + ", ExtensionBundleContribution, maximum_bytes="
            + str(len(value.canonical_bytes())) + ")," for value in contributions]
    return "\n".join((
        '"""Generated static descriptor data; regenerate from the authoritative EXTENSION declarations."""',
        "from empirical_lawhood.science.records.decoding import decode_canonical_bytes",
        "from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, compose_extension_bundle_aggregate",
        "", "EXTENSION_BUNDLE_CONTRIBUTIONS = (", *rows, ")", "",
        "GENERATED_EXTENSION_BUNDLE_AGGREGATE = compose_extension_bundle_aggregate(EXTENSION_BUNDLE_CONTRIBUTIONS)",
        f"EXPECTED_AGGREGATE_FINGERPRINT = {aggregate.fingerprint()!r}",
        "if GENERATED_EXTENSION_BUNDLE_AGGREGATE.fingerprint() != EXPECTED_AGGREGATE_FINGERPRINT:",
        '    raise RuntimeError("generated extension aggregate fingerprint drifted")',
        "", "__all__ = ['EXTENSION_BUNDLE_CONTRIBUTIONS', 'GENERATED_EXTENSION_BUNDLE_AGGREGATE', 'EXPECTED_AGGREGATE_FINGERPRINT']", ""))


def render_protocol_module(paths: tuple[Path, ...]) -> str:
    """Bind typed protocol owners only when authoring or scientific reading needs them."""
    imports, aliases, protocols = [], [], []
    for index, path in enumerate(paths):
        module = importlib.import_module(_module_name(path))
        declarations = descriptor_projection(module, "EXPERIMENT_PROTOCOL_DECLARATIONS", ())
        if (type(declarations) is not tuple
                or any(type(value) is not ExperimentProtocolDeclaration for value in declarations)):
            raise TypeError("experiment protocols require exact static code-owned declarations")
        if declarations:
            alias = f"_protocols_{index:03d}"
            imports.extend(projection_expression(module, "EXPERIMENT_PROTOCOL_DECLARATIONS", alias))
            aliases.append("*" + alias)
            protocols.extend(declarations)
    for attribute in ("protocol_id", "consumer_id"):
        values = [getattr(protocol, attribute) for protocol in protocols]
        if len(values) != len(set(values)):
            raise ValueError("installed experiment protocol declarations conflict")
    schemas = [(value.specification_type.SCHEMA, value.specification_type.VERSION) for value in protocols]
    if len(schemas) != len(set(schemas)):
        raise ValueError("installed experiment specifications require unique registered schema/revision pairs")
    return "\n".join((
        '"""Generated by scripts/generate_extension_bundle_aggregate.py; do not edit."""',
        *imports, "", "EXPERIMENT_PROTOCOL_DECLARATIONS = tuple(sorted((",
        "    " + ",\n    ".join(aliases) + ("," if aliases else ""),
        "), key=lambda declaration: declaration.protocol_id))", ""))


def load_public_facets(paths: tuple[Path, ...]):
    """Validate all code-owned facets before publishing any projection."""
    contracts = {
        "WORKFLOW_DECLARATIONS": (WorkflowDeclaration, lambda row: row.workflow.workflow_id),
        "ENVIRONMENT_DECLARATIONS": (EnvironmentDeclaration, lambda row: row.route_id),
        "CONFIGURATION_DECLARATIONS": (ConfigurationDeclaration, lambda row: row.consumer),
        "WORKFLOW_INSTALLATIONS": (WorkflowInstallationDeclaration, lambda row: (row.workflow_id, row.profile_id)),
    }
    values = {symbol: [] for symbol in contracts}
    owners = {symbol: {} for symbol in contracts}
    errors = []
    for path in paths:
        module_name_ = _module_name(path)
        module = importlib.import_module(module_name_)
        present = False
        for symbol, (record_type, identifier) in contracts.items():
            rows = descriptor_projection(module, symbol, ())
            if type(rows) is not tuple or any(type(row) is not record_type for row in rows):
                errors.append(f"{module_name_}: {symbol} requires exact immutable static declarations")
                continue
            present = present or bool(rows)
            for row in rows:
                try:
                    row.__post_init__()
                except (TypeError, ValueError) as error:
                    errors.append(f"{module_name_}: invalid {symbol}: {error}")
                    continue
                key = identifier(row)
                if key in owners[symbol]:
                    errors.append(f"{symbol} duplicate owners for {key}: {owners[symbol][key]}, {module_name_}")
                else:
                    owners[symbol][key] = module_name_
                values[symbol].append(row)
        if str(path).endswith("public_facets.py") and not present:
            errors.append(f"{module_name_}: public descriptor omits every required facet")
    installations = values["WORKFLOW_INSTALLATIONS"]
    if installations:
        workflow_ids = {row.workflow.workflow_id for row in values["WORKFLOW_DECLARATIONS"]}
        environment_ids = {row.route_id for row in values["ENVIRONMENT_DECLARATIONS"]}
        standards = {row.workflow_id for row in installations if row.profile_id == "standard"}
        if standards != workflow_ids:
            errors.append(f"workflow standard installation facets differ: missing={sorted(workflow_ids - standards)}, extra={sorted(standards - workflow_ids)}")
        for row in installations:
            required = {row.controller_environment, *(worker.environment_id for worker in row.workers)}
            if row.workflow_id not in workflow_ids or not required <= environment_ids:
                errors.append(f"{row.workflow_id}/{row.profile_id}: installation references an undeclared workflow or environment")
    if errors:
        raise ValueError("public discovery facets are invalid:\n" + "\n".join(errors))
    return {symbol: tuple(sorted(rows, key=(
        (lambda row: (row.catalogue_order, row.workflow.workflow_id))
        if symbol == "WORKFLOW_DECLARATIONS" else contracts[symbol][1])))
        for symbol, rows in values.items()}, owners


def render_workflow_declarations(paths: tuple[Path, ...]) -> str:
    """Emit only inert constructor data, without descriptor imports at discovery."""
    facets, _ = load_public_facets(paths)
    return _render_workflow_facets(facets)


def _render_workflow_facets(facets) -> str:
    from pprint import pformat

    return ('"""Generated by scripts/generate_extension_bundle_aggregate.py; do not edit."""\n\n'
        'from empirical_lawhood.execution.workflow_descriptors import (  # noqa: F401\n'
        '    RetainedManifestInput, Workflow, WorkflowDeclaration, WorkflowInput, WorkflowOperation,\n)\n\n'
        'WORKFLOW_DECLARATIONS = ' + pformat(facets["WORKFLOW_DECLARATIONS"], width=110, sort_dicts=True) + '\n')


def render_public_facets(paths: tuple[Path, ...]) -> str:
    facets, owners = load_public_facets(paths)
    return _render_public_facets(facets, owners)


def _render_public_facets(facets, owners) -> str:
    from pprint import pformat

    return ('"""Generated by scripts/generate_extension_bundle_aggregate.py; do not edit."""\n\n'
        'from empirical_lawhood.execution.discovery_descriptors import (\n'
        '    ConfigurationDeclaration, EnvironmentDeclaration,\n)\n\n'
        'from empirical_lawhood.execution.installation_descriptors import (  # noqa: F401\n'
        '    ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration,\n)\n\n'
        'ENVIRONMENT_DECLARATIONS = ' + pformat(facets["ENVIRONMENT_DECLARATIONS"], width=110) + '\n\n'
        'CONFIGURATION_DECLARATIONS = ' + pformat(facets["CONFIGURATION_DECLARATIONS"], width=110) + '\n\n'
        'WORKFLOW_INSTALLATIONS = ' + pformat(facets["WORKFLOW_INSTALLATIONS"], width=110) + '\n\n'
        'PUBLIC_FACET_OWNERS = ' + pformat(tuple((symbol, key, owner)
            for symbol in sorted(owners) for key, owner in sorted(owners[symbol].items())), width=110) + '\n')


def render_runtime_bindings() -> str:
    paths = _discover_descriptors(package_root=PACKAGE_ROOT, roots=(API_BINDING_ROOT,),
        name="experiment_binding.py", kind="experiment API binding")
    imports, aliases, protocols = [], [], set()
    for index, path in enumerate(paths):
        module = _module_name(path)
        binding = getattr(importlib.import_module(module), "EXPERIMENT_RUNTIME_BINDING", None)
        if type(binding) is not ExperimentRuntimeBinding:
            raise TypeError("experiment API descriptor requires its exact runtime binding")
        binding.__post_init__()
        if binding.protocol_id in protocols:
            raise ValueError("experiment API bindings repeat one protocol")
        protocols.add(binding.protocol_id)
        alias = f"_runtime_binding_{index:03d}"
        aliases.append(alias)
        imports.append(f"from {module} import EXPERIMENT_RUNTIME_BINDING as {alias}")
    declarations = {row.protocol_id: row for path in discover_descriptors()
        for row in descriptor_projection(importlib.import_module(_module_name(path)), "EXPERIMENT_PROTOCOL_DECLARATIONS", ())}
    required = {key for key,row in declarations.items() if (row.requires_prospective_runtime_binding
        or row.requires_development_runtime_binding or row.programme_record_type is not None)}
    if not required <= protocols or not protocols <= set(declarations):
        raise ValueError("experiment API bindings differ from declared protocols/runtime requirements")
    from empirical_lawhood.api.experiment_runtime_bindings import validate_experiment_runtime_binding
    for path in paths:
        binding = getattr(importlib.import_module(_module_name(path)), "EXPERIMENT_RUNTIME_BINDING")
        validate_experiment_runtime_binding(declarations[binding.protocol_id], binding)
        if not set(binding.derivation_target_protocol_ids)<=set(declarations):
            raise ValueError('experiment preprocessing target lacks its installed declared protocol')
    return "\n".join(('"""Generated by scripts/generate_extension_bundle_aggregate.py; do not edit."""',
        "", *imports, "", "EXPERIMENT_RUNTIME_BINDINGS = (",
        *("    " + alias + "," for alias in aliases), ")", "",
        "EXPERIMENT_SPECIFICATION_PROTOCOLS = (",
        *("    " + repr((row.specification_type.SCHEMA, row.specification_type.VERSION, row.protocol_id)) + ","
            for row in sorted(declarations.values(), key=lambda row: row.protocol_id)), ")", ""))


def render_application_presentations() -> str:
    from empirical_lawhood.api.application_presentations import validate_presentations
    paths = _discover_descriptors(package_root=PACKAGE_ROOT, roots=(API_BINDING_ROOT,),
        name="application_presentation.py", kind="application presentation")
    rows = tuple(getattr(importlib.import_module(_module_name(path)), "APPLICATION_PRESENTATION", None) for path in paths)
    validate_presentations(rows)
    return "\n".join(('"""Generated by scripts/generate_extension_bundle_aggregate.py; do not edit."""', "",
        *(f"from {_module_name(path)} import APPLICATION_PRESENTATION as _presentation_{index:03d}"
            for index, path in enumerate(paths)), "", "APPLICATION_PRESENTATIONS = (",
        *(f"    _presentation_{index:03d}," for index in range(len(rows))), ")", "",
        "APPLICATION_PRESENTATION_MODULES = (",
        *(f"    {_module_name(path)!r}," for path in paths), ")", ""))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated output drifts")
    arguments = parser.parse_args(argv)
    paths = discover_descriptors()
    projections, errors = {}, []
    for path, render in ((OUTPUT, lambda: render_generated_module(paths)),
                         (PROTOCOL_OUTPUT, lambda: render_protocol_module(paths)),
                         (API_BINDING_OUTPUT, render_runtime_bindings),
                         (APPLICATION_PRESENTATION_OUTPUT, render_application_presentations)):
        try:
            projections[path] = render().encode("utf-8")
        except (TypeError, ValueError, ImportError) as error:
            errors.append(f"{path}: {error}")
    try:
        facets, owners = load_public_facets((*paths, *discover_public_facets()))
        projections[WORKFLOW_OUTPUT] = _render_workflow_facets(facets).encode("utf-8")
        projections[PUBLIC_FACET_OUTPUT] = _render_public_facets(facets, owners).encode("utf-8")
    except (TypeError, ValueError, ImportError) as error:
        errors.append(str(error))
    for path, payload in projections.items():
        require_safe_output(path, package_root=PACKAGE_ROOT)
        if arguments.check:
            if not path.is_file() or path.read_bytes() != payload:
                errors.append(f"generated projection is missing or stale: {path}")
    if errors:
        raise SystemExit("extension/API/public projection diagnostics:\n" + "\n".join(errors))
    if not arguments.check:
        for path, payload in projections.items():
            path.write_bytes(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
